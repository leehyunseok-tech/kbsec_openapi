"""
보유 종목 변경 모니터 (MonitorBase + SSQM1801/SSQM2341 매핑).

장 시간 중 10초마다 보유 종목을 조회해 이전 조회와 비교, 변경 시 알림 + 체결로그 기록.
"""

import contextlib
from datetime import datetime

from src.api.account import ssqm1801, ssqm2341
from src.utils import trade_logger
from src.utils.logging_config import get_logger
from src.utils.monitor_base import MonitorBase

logger = get_logger(__name__)


def _normalize_code(is_no: str) -> str:
    is_no = (is_no or "").strip()
    return is_no[-6:] if len(is_no) >= 6 else is_no


class HoldingsMonitor(MonitorBase):
    POLL_INTERVAL = 10
    LABEL = "보유종목"

    def __init__(self, session, send_message_fn=None):
        super().__init__(session, execute_fn=None, send_message_fn=send_message_fn)
        self._prev_holdings = {}

    def start(self, require_list: bool = False):
        if self.is_running():
            return "❌ 보유 종목 모니터링이 이미 실행 중입니다."
        if not self.session.is_logged_in():
            return "❌ 먼저 로그인을 해야 합니다."

        snapshot = self._get_snapshot()
        if snapshot is None:
            return "❌ 초기 보유 종목 조회 실패"
        self._prev_holdings = snapshot

        self._stop_event.clear()
        import threading

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        stock_list = ", ".join(f"{info['name']}({code})" for code, info in snapshot.items()) or "없음"
        return (
            f"✅ 보유 종목 모니터링 시작\n\n현재 보유: {stock_list}\n10초마다 갱신 · 변경 시 알림\n\n/stop hold 로 중단"
        )

    def _get_snapshot(self):
        result = ssqm1801(token=self.session.access_token, host_url=self.session.host_url)
        if not result["success"]:
            return None
        records = result["body"].get("dataBody", {}).get("Record1", []) or []
        snapshot = {}
        for r in records:
            code = _normalize_code(r.get("is_no"))
            if not code:
                continue
            try:
                qty = int(str(r.get("ordr_psbl_q", "0")).strip())
            except ValueError:
                qty = 0
            snapshot[code] = {"name": r.get("is_nm", code), "qty": qty}
        return snapshot

    def _check_all(self):
        snapshot = self._get_snapshot()
        if snapshot is None:
            return
        self._compare_and_notify(snapshot)
        self._prev_holdings = snapshot

    def _compare_and_notify(self, new_holdings):
        prev = self._prev_holdings
        messages = []
        changed = []

        for code, info in new_holdings.items():
            name, qty = info["name"], info["qty"]
            if code not in prev:
                messages.append(f"[hold] 📈 매수 감지: {name}({code}) {qty:,}주")
                changed.append((code, name, "매수", qty, qty))
            elif qty != prev[code]["qty"]:
                diff = qty - prev[code]["qty"]
                if diff > 0:
                    messages.append(f"[hold] 📈 추가매수 감지: {name}({code}) +{diff:,}주 (총 {qty:,}주)")
                    changed.append((code, name, "매수", diff, qty))
                else:
                    messages.append(f"[hold] 📉 일부매도 감지: {name}({code}) {diff:,}주 (잔여 {qty:,}주)")
                    changed.append((code, name, "매도", abs(diff), qty))

        for code, info in prev.items():
            if code not in new_holdings:
                messages.append(f"[hold] 📉 전량매도 감지: {info['name']}({code})")
                changed.append((code, info["name"], "매도", info["qty"], 0))

        for code, name, side, qty_diff, remaining in changed:
            self._log_execution(code, name, side, qty_diff, remaining)

        for msg in messages:
            logger.info(msg)
            # 알림 전송 실패(텔레그램 장애 등)로 감시 루프 자체가 죽으면 안 된다.
            with contextlib.suppress(Exception):
                self.send_message(msg)

    def _log_execution(self, code, name, side, qty_diff, remaining):
        """SSQM2341로 당일 체결내역 조회 후 CSV 기록 (매칭 실패 시 가격 0으로 기록)."""
        try:
            today = datetime.now().strftime("%Y%m%d")
            # inq_clsf는 2026-07-17 재수출 명세에서 INPUT에서 빠졌지만 운영 검증된 페이로드 유지를 위해 extra로 전송.
            result = ssqm2341(
                ccls_clsf="1",
                ordr_dt=today,
                extra={"inq_clsf": "9"},
                token=self.session.access_token,
                host_url=self.session.host_url,
            )
            strategy = trade_logger.consume_strategy(code)
            if not result["success"]:
                trade_logger.log_trade(code, name, side, 0, qty_diff, strategy, remaining)
                return

            records = result["body"].get("dataBody", {}).get("Record1", []) or []
            side_name = "매수" if side == "매수" else "매도"
            matched = [
                r
                for r in records
                if _normalize_code(r.get("is_cd") or r.get("stnd_is_cd")) == code
                and side_name in (r.get("trd_dl_ccd_nm") or "")
            ]
            if matched:
                ex = matched[-1]
                price = int(str(ex.get("ccls_uprc", "0")).strip() or 0)
                trade_logger.log_trade(code, ex.get("hngl_shrt_nm") or name, side, price, qty_diff, strategy, remaining)
            else:
                trade_logger.log_trade(code, name, side, 0, qty_diff, strategy, remaining)
        except Exception:
            logger.exception("[hold] 체결 기록 오류")
