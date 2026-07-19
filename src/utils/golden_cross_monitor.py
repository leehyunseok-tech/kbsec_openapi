"""골든크로스 매수 모니터 (MonitorBase + IVS11560 매핑)."""

from src.utils.monitor_base import MonitorBase
from src.utils.chart_analysis import get_minute_closes, detect_golden_cross
from src.utils.settings_manager import SettingsManager
from src.utils import trade_logger


class GoldenCrossMonitor(MonitorBase):
    POLL_INTERVAL = 20
    LABEL = "골든크로스"

    def __init__(self, session, execute_command):
        super().__init__(session, execute_fn=execute_command, send_message_fn=None)
        self.last_crossed = {}

    def _has_targets(self) -> bool:
        return bool(SettingsManager.load_settings().get("gdcrs", {}).get("stocks", []))

    def _check_all(self):
        settings = SettingsManager.load_settings()
        gdcrs = settings.get("gdcrs", {})
        stocks = gdcrs.get("stocks", [])
        intv_short, intv_long = gdcrs.get("intv_short", 5), gdcrs.get("intv_long", 20)
        if not stocks:
            return

        for stock in stocks:
            stk_cd, amount = stock.get("code", ""), stock.get("amount", 0)
            if not stk_cd:
                continue

            closes = get_minute_closes(stk_cd, intv_short, self.session.access_token, self.session.host_url, count=max(60, intv_long + 10))
            if not closes:
                continue

            is_crossed = detect_golden_cross(closes, intv_short, intv_long)
            prev_state = self.last_crossed.get(stk_cd, False)

            if is_crossed and not prev_state:
                print(f"[gdcrs] ⭐ {stk_cd} 골든크로스 감지!", flush=True)
                trade_logger.register_order(stk_cd, "골든크로스")
                cmd = f"buy {stk_cd} max {amount}"
                response = self._execute(cmd)
                print(f"[gdcrs] 매수 응답: {str(response)[:100]}", flush=True)

            self.last_crossed[stk_cd] = is_crossed
