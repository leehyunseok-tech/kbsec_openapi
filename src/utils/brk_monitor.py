"""
돌파매수 감시 모니터 (MonitorBase 이용, IVU10140 매핑).

장 중 30초마다 전일종가 대비 상승률을 확인해 기준 이상이면 등록된 명령 자동 실행.
당일 종목당 1회만 실행.
"""

from datetime import datetime

from src.api.price_info import ivu10140
from src.utils.monitor_base import MonitorBase
from src.utils.settings_manager import SettingsManager

_SETTINGS_KEY = "brk_watch_list"
_RATE_KEY = "brk_rate"
_DEFAULT_RATE = 3.0


def _load_list() -> list:
    return SettingsManager.load_settings().get(_SETTINGS_KEY, [])


def _save_list(lst: list):
    settings = SettingsManager.load_settings()
    settings[_SETTINGS_KEY] = lst
    SettingsManager.save_settings(settings)


def _load_rate() -> float:
    return float(SettingsManager.load_settings().get(_RATE_KEY, _DEFAULT_RATE))


def _save_rate(rate: float):
    settings = SettingsManager.load_settings()
    settings[_RATE_KEY] = rate
    SettingsManager.save_settings(settings)


class BrkMonitor(MonitorBase):
    """
    현재가 기준 상승률 돌파매수 감시.

    주의: KB IVU10140에는 "전일종가 대비 등락률"(up_dwn_r_p2)이 이미 있어 이를 그대로 사용한다
    (API가 직접 등락률을 제공하므로 별도 계산 불필요).
    """

    POLL_INTERVAL = 30
    LABEL = "돌파매수"

    def __init__(self, session, execute_fn, send_message_fn):
        super().__init__(session, execute_fn, send_message_fn)
        self._triggered_today: set = set()
        self._last_date: str = ""

    def _has_targets(self) -> bool:
        return bool(_load_list())

    def set_rate(self, rate: float) -> str:
        _save_rate(rate)
        return f"✅ 돌파 기준 상승률: +{rate:.1f}% 로 설정됨"

    def get_rate(self) -> float:
        return _load_rate()

    def add(self, stk_cd: str, command: str) -> str:
        lst = _load_list()
        for item in lst:
            if item["stk_cd"] == stk_cd:
                item["command"] = command
                _save_list(lst)
                return f"✅ ({stk_cd}) 명령 업데이트: `{command}`"
        lst.append({"stk_cd": stk_cd, "command": command})
        _save_list(lst)
        return f"✅ 감시 추가: ({stk_cd}) → `{command}`"

    def remove(self, idx: int) -> str:
        lst = _load_list()
        if idx < 1 or idx > len(lst):
            return f"❌ 번호 {idx}는 없습니다. (1~{len(lst)})"
        removed = lst.pop(idx - 1)
        _save_list(lst)
        return f"✅ 제거: ({removed['stk_cd']})  `{removed['command']}`"

    def get_list_text(self) -> str:
        lst = _load_list()
        rate = _load_rate()
        state = "🟢 실행 중" if self.is_running() else "🔴 중지됨"
        if not lst:
            return f"📋 돌파매수 감시 목록이 비어 있습니다.\n기준 상승률: +{rate:.1f}%  감시: {state}"
        lines = [f"📋 돌파매수 감시 목록  (기준: 전일종가 대비 +{rate:.1f}% 이상)\n"]
        for i, item in enumerate(lst, 1):
            done = " ✅당일완료" if item["stk_cd"] in self._triggered_today else ""
            lines.append(f"{i}. ({item['stk_cd']}) → {item['command']}{done}")
        lines.append(f"\n감시 상태: {state}")
        return "\n".join(lines)

    def _on_start(self):
        self._triggered_today.clear()
        self._last_date = ""

    def _reset_daily(self):
        today = datetime.now().strftime("%Y%m%d")
        if today != self._last_date:
            self._triggered_today.clear()
            self._last_date = today

    def _check_all(self):
        self._reset_daily()
        if not self.session.is_logged_in():
            return
        rate = _load_rate()
        token, host_url = self.session.access_token, self.session.host_url

        for item in _load_list():
            stk_cd, command = item["stk_cd"], item["command"]
            if stk_cd in self._triggered_today:
                continue

            result = ivu10140(excg_clsf="0", shrt_cd=stk_cd, token=token, host_url=host_url)
            if not result["success"]:
                continue
            body = result["body"].get("dataBody", {})
            try:
                flu_rt = float(str(body.get("up_dwn_r_p2", "0")).strip())
                cur_prc = abs(float(str(body.get("now_prc", "0")).strip()))
            except (ValueError, TypeError):
                continue
            stk_nm = body.get("is_nm", stk_cd)

            if flu_rt >= rate:
                self._triggered_today.add(stk_cd)
                print(f"[brk] 돌파 감지 ({stk_cd} {stk_nm}) +{flu_rt:.2f}% → {command}", flush=True)
                self.send_message(
                    f"🚀 돌파매수 신호\n종목: ({stk_cd}) {stk_nm}\n현재가: {cur_prc:,.0f}원\n"
                    f"상승률: +{flu_rt:.2f}%  (기준: +{rate:.1f}%)\n실행: {command}"
                )
                self._execute(command)
