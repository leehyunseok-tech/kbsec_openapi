"""그리드 트레이딩 모니터 (MonitorBase + IVU10140 매핑)."""

from src.utils.monitor_base import MonitorBase
from src.utils.price_lookup import get_current_price
from src.utils.settings_manager import SettingsManager

_WATCH_KEY = "grid_watch_list"


def _load_list() -> list:
    return SettingsManager.load_settings().get(_WATCH_KEY, [])


def _save_list(lst: list):
    settings = SettingsManager.load_settings()
    settings[_WATCH_KEY] = lst
    SettingsManager.save_settings(settings)


class GridMonitor(MonitorBase):
    POLL_INTERVAL = 10
    LABEL = "그리드"

    def __init__(self, session, execute_fn, send_message_fn):
        super().__init__(session, execute_fn, send_message_fn)
        self._states: dict = {}

    def _has_targets(self) -> bool:
        return bool(_load_list())

    def _on_start(self):
        self._states.clear()

    def add(self, stk_cd, base_price, interval, order_amount, max_stages) -> str:
        lst = _load_list()
        for item in lst:
            if item["stk_cd"] == stk_cd:
                item.update({"base_price": base_price, "interval": interval, "order_amount": order_amount, "max_stages": max_stages})
                _save_list(lst)
                return f"✅ ({stk_cd}) 그리드 업데이트됨\n기준가 {base_price:,}원 | 간격 {interval}% | 주문금액 {order_amount:,}원 | 최대 {max_stages}단계"
        lst.append({"stk_cd": stk_cd, "base_price": base_price, "interval": interval, "order_amount": order_amount, "max_stages": max_stages})
        _save_list(lst)
        buy_levels = ", ".join(f"{base_price * (1 - (n * interval / 100)):,.0f}" for n in range(1, max_stages + 1))
        sell_levels = ", ".join(f"{base_price * (1 + (n * interval / 100)):,.0f}" for n in range(1, max_stages + 1))
        return (
            f"✅ 그리드 추가: ({stk_cd})\n기준가: {base_price:,}원  간격: {interval}%  주문금액: {order_amount:,}원  최대: {max_stages}단계\n"
            f"매수레벨: {buy_levels}\n매도레벨: {sell_levels}"
        )

    def remove(self, idx: int) -> str:
        lst = _load_list()
        if idx < 1 or idx > len(lst):
            return f"❌ 번호 {idx}는 없습니다. (1~{len(lst)})"
        removed = lst.pop(idx - 1)
        _save_list(lst)
        self._states.pop(removed["stk_cd"], None)
        return f"✅ 제거: ({removed['stk_cd']}) 기준가 {removed['base_price']:,}원"

    def get_list_text(self) -> str:
        lst = _load_list()
        state_str = "🟢 실행 중" if self.is_running() else "🔴 중지됨"
        if not lst:
            return f"📋 그리드 목록이 비어 있습니다.\n감시: {state_str}"
        lines = [f"📋 그리드 목록 ({state_str})\n"]
        for i, item in enumerate(lst, 1):
            st = self._states.get(item["stk_cd"])
            progress = f"매수발동 {len(st['buy_triggered'])}/{item['max_stages']} 매도발동 {len(st['sell_triggered'])}/{item['max_stages']}" if st else "미시작"
            lines.append(f"{i}. ({item['stk_cd']}) 기준가 {item['base_price']:,}원 간격 {item['interval']}% 금액 {item['order_amount']:,}원 {item['max_stages']}단계  [{progress}]")
        return "\n".join(lines)

    def _check_all(self):
        if not self.session.is_logged_in():
            return
        token, host_url = self.session.access_token, self.session.host_url

        for item in _load_list():
            stk_cd = item["stk_cd"]
            info = get_current_price(stk_cd, token, host_url)
            if not info:
                continue
            cur_price = info["price"]

            if stk_cd not in self._states:
                self._states[stk_cd] = {"buy_triggered": set(), "sell_triggered": set(), "stk_nm": info["name"]}
                print(f"[grid] ({stk_cd}) 감시 시작 현재가: {cur_price:,.0f}원", flush=True)

            self._check_levels(stk_cd, cur_price, item, self._states[stk_cd])

    def _check_levels(self, stk_cd, cur_price, item, st):
        base, interval, order_amount, max_stages = item["base_price"], item["interval"], item["order_amount"], item["max_stages"]
        stk_nm = st["stk_nm"]

        for n in range(1, max_stages + 1):
            if n in st["buy_triggered"]:
                continue
            level_price = base * (1 - n * interval / 100)
            if cur_price <= level_price:
                qty = max(1, int(order_amount // cur_price))
                cmd = f"buy {stk_cd} {qty}"
                st["buy_triggered"].add(n)
                print(f"[grid] 매수 레벨{n} ({stk_cd}) {cur_price:,.0f}원 {qty}주 → {cmd}", flush=True)
                self.send_message(f"🔵 그리드 {n}단계 매수\n종목: ({stk_cd}) {stk_nm}\n현재가: {cur_price:,.0f}원  수량: {qty}주\n레벨가: {level_price:,.0f}원  실행: {cmd}")
                self._execute(cmd)

        for n in range(1, max_stages + 1):
            if n in st["sell_triggered"]:
                continue
            level_price = base * (1 + n * interval / 100)
            if cur_price >= level_price:
                qty = max(1, int(order_amount // cur_price))
                cmd = f"sell {stk_cd} {qty}"
                st["sell_triggered"].add(n)
                print(f"[grid] 매도 레벨{n} ({stk_cd}) {cur_price:,.0f}원 {qty}주 → {cmd}", flush=True)
                self.send_message(f"🔴 그리드 {n}단계 매도\n종목: ({stk_cd}) {stk_nm}\n현재가: {cur_price:,.0f}원  수량: {qty}주\n레벨가: {level_price:,.0f}원  실행: {cmd}")
                self._execute(cmd)
