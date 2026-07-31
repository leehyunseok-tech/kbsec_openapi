"""
데드크로스 자동매도 모니터 (MonitorBase + IVS11560/SSQM1801 매핑).

보유종목은 api.account.ssqm1801(보유주식 조회)을 직접 호출해 견고하게 조회한다.
"""

from src.api.account import ssqm1801
from src.utils import trade_logger
from src.utils.chart_analysis import detect_dead_cross, get_minute_closes
from src.utils.monitor_base import MonitorBase
from src.utils.settings_manager import SettingsManager


def _normalize_code(is_no: str) -> str:
    is_no = (is_no or "").strip()
    return is_no[-6:] if len(is_no) >= 6 else is_no


class DeadCrossMonitor(MonitorBase):
    POLL_INTERVAL = 20
    LABEL = "데드크로스"

    def __init__(self, session, execute_command):
        super().__init__(session, execute_fn=execute_command, send_message_fn=None)
        self.last_crossed = {}
        self.intv_short = 5
        self.intv_long = 20

    def _has_targets(self) -> bool:
        return True  # 보유 종목 전체를 대상으로 하므로 사전 목록 불필요

    def start(self, require_list: bool = False):
        return super().start(require_list=False)

    def _get_holding_stocks(self):
        result = ssqm1801(token=self.session.access_token, host_url=self.session.host_url)
        if not result["success"]:
            return {}
        records = result["body"].get("dataBody", {}).get("Record1", []) or []
        holdings = {}
        for r in records:
            code = _normalize_code(r.get("is_no"))
            if not code:
                continue
            try:
                qty = int(str(r.get("ordr_psbl_q", "0")).strip())
            except ValueError:
                qty = 0
            if qty > 0:
                holdings[code] = qty
        return holdings

    def _check_all(self):
        settings = SettingsManager.load_settings()
        ddcrs = settings.get("ddcrs", {})
        intv_short = ddcrs.get("intv_short", self.intv_short)
        intv_long = ddcrs.get("intv_long", self.intv_long)

        holdings = self._get_holding_stocks()
        if not holdings:
            return

        for stk_cd, qty in holdings.items():
            closes = get_minute_closes(
                stk_cd, intv_short, self.session.access_token, self.session.host_url, count=max(60, intv_long + 10)
            )
            if not closes:
                continue

            is_crossed = detect_dead_cross(closes, intv_short, intv_long)
            prev_state = self.last_crossed.get(stk_cd, False)

            if is_crossed and not prev_state:
                print(f"[ddcrs] ⚠️  {stk_cd} 데드크로스 감지! {qty}주 매도", flush=True)
                trade_logger.register_order(stk_cd, "데드크로스")
                cmd = f"sell {stk_cd} {qty}"
                response = self._execute(cmd)
                print(f"[ddcrs] 매도 응답: {str(response)[:100]}", flush=True)

            self.last_crossed[stk_cd] = is_crossed
