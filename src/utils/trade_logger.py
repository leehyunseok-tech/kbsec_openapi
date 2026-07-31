"""
자동매매 체결 내역 CSV 로거 (브로커 무관, thread-safe).

logs/YYYYMMDD.csv 에 실시간 기록
컬럼: 체결시간, 종목코드, 종목명, 매수/매도, 체결가, 수량, 전략, 잔여수량
"""

import csv
import threading
from datetime import datetime
from pathlib import Path

from src.paths import LOGS_DIR as _LOGS_DIR

_CSV_HEADER = ["체결시간", "종목코드", "종목명", "매수/매도", "체결가", "수량", "전략", "잔여수량"]

_lock = threading.Lock()
_pending_strategies: dict = {}
_logged_keys: set = set()


def _today_path() -> Path:
    return _LOGS_DIR / f"{datetime.now().strftime('%Y%m%d')}.csv"


def _ensure_csv() -> Path:
    path = _today_path()
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(_CSV_HEADER)
    return path


def register_order(code: str, strategy: str):
    """매수/매도 실행 직전에 전략명 등록"""
    with _lock:
        _pending_strategies[code.strip()] = strategy


def consume_strategy(code: str) -> str:
    """전략명 조회 후 삭제. 미등록이면 '수동' 반환"""
    with _lock:
        return _pending_strategies.pop(code.strip(), "수동")


def log_trade(
    code: str, name: str, side: str, price: int, qty: int, strategy: str, remaining_qty: int, exec_time: str = ""
) -> bool:
    """체결 내역 CSV 기록 (중복 무시). True면 신규 기록됨."""
    time_str = exec_time or datetime.now().strftime("%H:%M:%S")
    key = (code.strip(), time_str, side, qty)

    with _lock:
        if key in _logged_keys:
            return False
        _logged_keys.add(key)
        path = _ensure_csv()
        with open(path, "a", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow([time_str, code, name, side, price, qty, strategy, remaining_qty])

    print(f"[체결로그] {side} {name}({code}) {qty}주 @{price:,}원 [{strategy}] 잔여{remaining_qty}주", flush=True)
    return True


def generate_summary() -> str:
    """오늘 CSV에서 일일 거래 요약 생성. CSV 하단에 추가 후 텔레그램용 문자열 반환."""
    path = _today_path()
    if not path.exists():
        return "📋 오늘 체결 내역이 없습니다."

    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            t = row.get("체결시간", "")
            if not t or t.startswith("---"):
                continue
            rows.append(row)

    if not rows:
        return "📋 오늘 체결 내역이 없습니다."

    buy_amt = sell_amt = buy_cnt = sell_cnt = 0
    for r in rows:
        try:
            amt = int(r.get("체결가", 0)) * int(r.get("수량", 0))
        except (ValueError, TypeError):
            continue
        side = r.get("매수/매도", "")
        if side == "매수":
            buy_amt += amt
            buy_cnt += 1
        elif side == "매도":
            sell_amt += amt
            sell_cnt += 1

    profit = sell_amt - buy_amt
    profit_rate = (profit / buy_amt * 100) if buy_amt > 0 else 0.0
    sign = "+" if profit >= 0 else ""
    date_str = datetime.now().strftime("%Y-%m-%d")

    summary = (
        f"📊 {date_str} 일일 거래 결과\n\n"
        f"💰 매수: {buy_cnt}건 / {buy_amt:,}원\n"
        f"💸 매도: {sell_cnt}건 / {sell_amt:,}원\n\n"
        f"{'📈' if profit >= 0 else '📉'} 수익금: {sign}{profit:,}원\n"
        f"📊 수익률: {sign}{profit_rate:.2f}%"
    )

    with _lock, open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([])
        w.writerow(["--- 일일 요약 ---"])
        for line in summary.split("\n"):
            if line.strip():
                w.writerow([line.strip()])

    return summary
