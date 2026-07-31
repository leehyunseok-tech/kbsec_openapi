"""
트레일링 스탑 모니터 (WS 실시간 틱 → REST 폴링으로 대체).

설정값(trst 명령): drop_rate(고점 대비 하락율 %), min_profit(최소 발동 수익률 %).
발동 조건: 수익률 >= min_profit AND 고점 대비 하락율 >= drop_rate → 전량 매도.

평가손익은 SSQM2952(잔고현황 조회)의 val_yld를 그대로 사용한다 (KB가 직접 제공 — 계산 불필요).
"""

from datetime import datetime

from src.utils import trade_logger
from src.utils.holdings_valuation import get_holdings_with_profit
from src.utils.monitor_base import MonitorBase
from src.utils.settings_manager import SettingsManager


class TrailingStopMonitor(MonitorBase):
    POLL_INTERVAL = 15
    LABEL = "트레일링스탑"

    def __init__(self, session, execute_command):
        super().__init__(session, execute_fn=execute_command, send_message_fn=None)
        self.peak_prices = {}
        self.sold_today = set()
        self._last_date = ""

    def start(self, require_list: bool = False):
        return super().start(require_list=False)

    def _on_start(self):
        self.peak_prices.clear()
        self.sold_today.clear()

    def _reset_daily(self):
        today = datetime.now().strftime("%Y%m%d")
        if today != self._last_date:
            self.sold_today.clear()
            self._last_date = today

    def _check_all(self):
        self._reset_daily()
        holdings = get_holdings_with_profit(self.session)
        if not holdings:
            return

        settings = SettingsManager.get_trailing_stop_settings()
        drop_rate, min_profit = settings.get("drop_rate", 3.0), settings.get("min_profit", 5.0)

        for h in holdings:
            code = h["code"]
            if code in self.sold_today or h["cur_price"] <= 0:
                continue

            peak = max(self.peak_prices.get(code, 0), h["cur_price"])
            self.peak_prices[code] = peak
            drop_from_peak = (peak - h["cur_price"]) / peak * 100 if peak > 0 else 0
            profit_rate = h["profit_rate"]

            print(
                f"[trst] {code}({h['name']}) 현재={h['cur_price']:,.0f} 수익={profit_rate:+.1f}% 고점대비={drop_from_peak:.1f}%하락",
                flush=True,
            )

            if profit_rate >= min_profit and drop_from_peak >= drop_rate:
                self._trigger_sell(code, h["name"], h["qty"], profit_rate, drop_from_peak)

    def _trigger_sell(self, code, name, qty, profit_rate, drop_from_peak):
        print(
            f"[trst] 🔴 발동! {code}({name}) 수익={profit_rate:+.1f}% 고점대비={drop_from_peak:.1f}%하락 → 전량 매도",
            flush=True,
        )
        self.sold_today.add(code)
        trade_logger.register_order(code, "트레일링스탑")
        try:
            result = self._execute(f"sell {code}")
            print(f"[trst] 매도 결과: {str(result)[:100]}", flush=True)
        except Exception as e:
            print(f"[trst] 매도 오류: {e}", flush=True)
