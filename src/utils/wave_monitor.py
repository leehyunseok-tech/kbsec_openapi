"""분할매매(wave) 모니터 (MonitorBase + IVU10140 매핑)."""

from src.utils.logging_config import get_logger
from src.utils.monitor_base import MonitorBase
from src.utils.price_lookup import get_current_price
from src.utils.settings_manager import SettingsManager

logger = get_logger(__name__)

_CONFIG_KEY = "wave_config"
_WATCH_KEY = "wave_watch_list"
_DEFAULT_CONFIG = {"buy_a": 3.0, "buy_b": 6.0, "buy_c": 2.0, "sell_d": 3.0, "sell_e": 6.0, "sell_f": 2.0}


def _load_config() -> dict:
    return SettingsManager.load_settings().get(_CONFIG_KEY, dict(_DEFAULT_CONFIG))


def _save_config(cfg: dict):
    settings = SettingsManager.load_settings()
    settings[_CONFIG_KEY] = cfg
    SettingsManager.save_settings(settings)


def _load_list() -> list:
    return SettingsManager.load_settings().get(_WATCH_KEY, [])


def _save_list(lst: list):
    settings = SettingsManager.load_settings()
    settings[_WATCH_KEY] = lst
    SettingsManager.save_settings(settings)


class WaveMonitor(MonitorBase):
    POLL_INTERVAL = 10
    LABEL = "분할매매"

    def __init__(self, session, execute_fn, send_message_fn):
        super().__init__(session, execute_fn, send_message_fn)
        self._states: dict = {}

    def _has_targets(self) -> bool:
        return bool(_load_list())

    def _on_start(self):
        self._states.clear()

    # ── 설정 ──────────────────────────────────────────────────────────────
    def set_config(self, buy_a, buy_b, buy_c, sell_d, sell_e, sell_f) -> str:
        _save_config(
            {"buy_a": buy_a, "buy_b": buy_b, "buy_c": buy_c, "sell_d": sell_d, "sell_e": sell_e, "sell_f": sell_f}
        )
        return f"✅ 분할매매 설정 완료\n\n매수: -{buy_a}% / -{buy_b}% / 최저+{buy_c}%\n매도: +{sell_d}% / +{sell_e}% / 최고-{sell_f}%"

    def get_config_text(self) -> str:
        cfg = _load_config()
        return (
            f"⚙️ 분할매매 설정\n\n"
            f"📉 매수 기준 (기준가 대비)\n  1차: -{cfg.get('buy_a', 3.0)}% 하락 시\n"
            f"  2차: -{cfg.get('buy_b', 6.0)}% 하락 시\n  3차: 최저점 +{cfg.get('buy_c', 2.0)}% 반등 시\n\n"
            f"📈 매도 기준 (기준가 대비)\n  1차: +{cfg.get('sell_d', 3.0)}% 상승 시\n"
            f"  2차: +{cfg.get('sell_e', 6.0)}% 상승 시\n  3차: 최고점 -{cfg.get('sell_f', 2.0)}% 하락 시"
        )

    # ── 감시 목록 ─────────────────────────────────────────────────────────
    def add(self, stk_cd: str, total_amount: int) -> str:
        lst = _load_list()
        for item in lst:
            if item["stk_cd"] == stk_cd:
                item["total_amount"] = total_amount
                _save_list(lst)
                return f"✅ ({stk_cd}) 투자금액 {total_amount:,}원으로 업데이트됨"
        lst.append({"stk_cd": stk_cd, "total_amount": total_amount})
        _save_list(lst)
        return f"✅ 분할매매 추가: ({stk_cd}) 총 {total_amount:,}원 (단계별 {total_amount // 3:,}원)"

    def remove(self, idx: int) -> str:
        lst = _load_list()
        if idx < 1 or idx > len(lst):
            return f"❌ 번호 {idx}는 없습니다. (1~{len(lst)})"
        removed = lst.pop(idx - 1)
        _save_list(lst)
        self._states.pop(removed["stk_cd"], None)
        return f"✅ 제거: ({removed['stk_cd']}) {removed['total_amount']:,}원"

    def get_list_text(self) -> str:
        lst = _load_list()
        cfg = _load_config()
        state_str = "🟢 실행 중" if self.is_running() else "🔴 중지됨"
        if not lst:
            return f"📋 분할매매 목록이 비어 있습니다.\n감시: {state_str}"
        lines = [
            f"📋 분할매매 목록 ({state_str})\n"
            f"매수: -{cfg.get('buy_a', 3)}% / -{cfg.get('buy_b', 6)}% / 최저+{cfg.get('buy_c', 2)}%\n"
            f"매도: +{cfg.get('sell_d', 3)}% / +{cfg.get('sell_e', 6)}% / 최고-{cfg.get('sell_f', 2)}%\n"
        ]
        for i, item in enumerate(lst, 1):
            st = self._states.get(item["stk_cd"])
            progress = (
                f"기준가 {st['ref_price']:,.0f}원 | 매수{st['buy_stage']}/3 매도{st['sell_stage']}/3"
                if st
                else "미시작"
            )
            lines.append(f"{i}. ({item['stk_cd']}) {item['total_amount']:,}원  [{progress}]")
        return "\n".join(lines)

    # ── 폴링 ──────────────────────────────────────────────────────────────
    def _check_all(self):
        if not self.session.is_logged_in():
            return
        token, host_url = self.session.access_token, self.session.host_url

        for item in _load_list():
            stk_cd, total_amount = item["stk_cd"], item["total_amount"]
            per_stage_amt = max(1, total_amount // 3)

            info = get_current_price(stk_cd, token, host_url)
            if not info:
                continue
            cur_price = info["price"]

            if stk_cd not in self._states:
                self._states[stk_cd] = {
                    "ref_price": cur_price,
                    "buy_stage": 0,
                    "sell_stage": 0,
                    "trough_price": cur_price,
                    "peak_price": cur_price,
                    "total_bought_qty": 0,
                    "per_stage_amt": per_stage_amt,
                    "stk_nm": info["name"],
                }
                logger.info(f"[wave] ({stk_cd}) 기준가 설정: {cur_price:,.0f}원")
                continue

            st = self._states[stk_cd]
            st["trough_price"] = min(st["trough_price"], cur_price)
            st["peak_price"] = max(st["peak_price"], cur_price)

            cfg = _load_config()
            self._check_buy(stk_cd, cur_price, per_stage_amt, st, cfg)
            self._check_sell(stk_cd, cur_price, st, cfg)

    def _check_buy(self, stk_cd, cur_price, per_stage_amt, st, cfg):
        ref, stage = st["ref_price"], st["buy_stage"]
        if stage == 0 and cur_price <= ref * (1 - cfg.get("buy_a", 3.0) / 100):
            self._do_buy(stk_cd, 1, cur_price, max(1, int(per_stage_amt // cur_price)), st)
        elif stage == 1 and cur_price <= ref * (1 - cfg.get("buy_b", 6.0) / 100):
            self._do_buy(stk_cd, 2, cur_price, max(1, int(per_stage_amt // cur_price)), st)
        elif stage == 2:
            trough, c = st["trough_price"], cfg.get("buy_c", 2.0)
            if trough < cur_price and cur_price >= trough * (1 + c / 100):
                self._do_buy(stk_cd, 3, cur_price, max(1, int(per_stage_amt // cur_price)), st)

    def _do_buy(self, stk_cd, stage, cur_price, qty, st):
        st["buy_stage"] = stage
        st["total_bought_qty"] += qty
        cmd = f"buy {stk_cd} {qty}"
        logger.info(f"[wave] {stage}차 매수 ({stk_cd}) {cur_price:,.0f}원 × {qty}주 → {cmd}")
        self.send_message(
            f"📊 분할매매 {stage}차 매수\n종목: ({stk_cd}) {st.get('stk_nm', stk_cd)}\n현재가: {cur_price:,.0f}원  수량: {qty}주\n실행: {cmd}"
        )
        self._execute(cmd)

    def _check_sell(self, stk_cd, cur_price, st, cfg):
        ref, stage = st["ref_price"], st["sell_stage"]
        if stage == 0 and cur_price >= ref * (1 + cfg.get("sell_d", 3.0) / 100):
            self._do_sell(stk_cd, 1, cur_price, st)
        elif stage == 1 and cur_price >= ref * (1 + cfg.get("sell_e", 6.0) / 100):
            self._do_sell(stk_cd, 2, cur_price, st)
        elif stage == 2:
            peak, f_val = st["peak_price"], cfg.get("sell_f", 2.0)
            if peak > cur_price and cur_price <= peak * (1 - f_val / 100):
                self._do_sell(stk_cd, 3, cur_price, st)

    def _do_sell(self, stk_cd, stage, cur_price, st):
        st["sell_stage"] = stage
        total_qty, per_stage_amt = st["total_bought_qty"], st.get("per_stage_amt", 0)
        if stage == 3:
            cmd, qty_desc = f"sell {stk_cd}", "전량"
        else:
            qty = (
                max(1, total_qty // 3)
                if total_qty > 0
                else (max(1, int(per_stage_amt // cur_price)) if per_stage_amt > 0 else 1)
            )
            cmd, qty_desc = f"sell {stk_cd} {qty}", f"{qty}주"
        logger.info(f"[wave] {stage}차 매도 ({stk_cd}) {cur_price:,.0f}원 {qty_desc} → {cmd}")
        self.send_message(
            f"📊 분할매매 {stage}차 매도\n종목: ({stk_cd}) {st.get('stk_nm', stk_cd)}\n현재가: {cur_price:,.0f}원  수량: {qty_desc}\n실행: {cmd}"
        )
        self._execute(cmd)
