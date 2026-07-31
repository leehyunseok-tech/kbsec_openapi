"""
자동 손절매/익절 모니터 (REST 폴링 기반).

KB증권 API에는 실시간 웹소켓이 없어, 다른 모니터들과 동일하게 MonitorBase 기반
폴링 클래스로 구현했다.

설정값(익절/손절 명령): take_profit(%), stop_loss(%, 음수).
평가손익은 SSQM2952의 val_yld를 그대로 사용한다.
"""

from datetime import datetime

from src.utils import trade_logger
from src.utils.holdings_valuation import get_holdings_with_profit
from src.utils.logging_config import get_logger
from src.utils.monitor_base import MonitorBase
from src.utils.settings_manager import SettingsManager

logger = get_logger(__name__)


class StopLossManager(MonitorBase):
    POLL_INTERVAL = 15
    LABEL = "자동손절매"

    def __init__(self, session, execute_command):
        super().__init__(session, execute_fn=execute_command, send_message_fn=None)
        self.sold_today = {}
        self._last_date = ""

    def start(self, require_list: bool = False):
        return super().start(require_list=False)

    def _on_start(self):
        self.sold_today.clear()

    def _reset_daily(self):
        today = datetime.now().strftime("%Y%m%d")
        if today != self._last_date:
            self.sold_today.clear()
            self._last_date = today

    def is_enabled(self) -> bool:
        return self.is_running()

    def get_status(self) -> str:
        settings = SettingsManager.get_stop_loss_settings()
        status = "✅ 활성화" if self.is_running() else "⏹️  비활성화"
        sold_lines = (
            "\n".join(
                f"  #{code} {info['name']} - {'익절' if info['reason'] == 'take_profit' else '손절'} ({info['profit_rate']:+.2f}%)"
                for code, info in list(self.sold_today.items())[:10]
            )
            or "  없음"
        )
        return (
            f"{status}\n\n"
            f"익절 기준: +{settings.get('take_profit', 5.0)}%  손절 기준: {settings.get('stop_loss', -5.0)}%\n\n"
            f"오늘 매도:\n{sold_lines}"
        )

    def _check_all(self):
        self._reset_daily()
        holdings = get_holdings_with_profit(self.session)
        if not holdings:
            return

        settings = SettingsManager.get_stop_loss_settings()
        take_profit, stop_loss = settings.get("take_profit", 5.0), settings.get("stop_loss", -5.0)

        for h in holdings:
            code = h["code"]
            if code in self.sold_today:
                continue
            profit_rate = h["profit_rate"]

            if profit_rate >= take_profit:
                self._trigger_sell(code, h["name"], h["qty"], profit_rate, "take_profit")
            elif profit_rate <= stop_loss:
                self._trigger_sell(code, h["name"], h["qty"], profit_rate, "stop_loss")

    def _trigger_sell(self, code, name, qty, profit_rate, reason):
        reason_kr = "익절" if reason == "take_profit" else "손절"
        logger.info(f"[stls] 🎯 {reason_kr} 기준 도달: {code}({name}) {profit_rate:+.2f}% → 전량 매도")
        trade_logger.register_order(code, f"{reason_kr}매")
        try:
            result = self._execute(f"sell {code}")
            self.sold_today[code] = {"name": name, "reason": reason, "profit_rate": profit_rate}
            logger.info(f"[stls] 매도 결과: {str(result)[:100]}")
        except Exception:
            logger.exception("[stls] 손절 매도 오류")
