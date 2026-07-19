"""
분봉 캔들 조회 + 이동평균 골든/데드크로스 판정.

KB IVS11560(통합차트, 국내)을 분봉(chrt_clsf='B')으로 조회해 종가 리스트를 뽑는다.
"""

from src.api.chart import ivs11560
from src.utils.stock_master import find_by_code


def get_minute_closes(stk_cd: str, interval_minutes: int, token: str, host_url: str, count: int = 60):
    """
    분봉 종가 리스트 조회 (과거 → 최신 순).

    Returns:
        list[float] 또는 조회 실패 시 None
    """
    # 2026-07-17 재수출 명세에서 info_ccd(1:원주가)/mkt_clsf(0:KOSPI 1:KOSDAQ)가
    # 필수(Y)로 바뀌어 값을 채운다. 시장구분은 로컬 종목마스터로 판별.
    stock = find_by_code(stk_cd)
    mkt_clsf = "1" if stock is not None and stock.market == "KOSDAQ" else "0"
    result = ivs11560(
        info_ccd="1",
        mkt_clsf=mkt_clsf,
        chrt_clsf="B",
        minute_tck_indx=str(interval_minutes),
        is_cd=stk_cd,
        inq_clsf="2",
        inq_cnt=str(count),
        token=token,
        host_url=host_url,
    )
    if not result["success"]:
        return None

    candles = result["body"].get("dataBody", {}).get("out2", []) or []
    if not candles:
        return None

    def _sort_key(c):
        return f"{c.get('dt', '')}{c.get('tm', '')}"

    candles = sorted(candles, key=_sort_key)
    closes = []
    for c in candles:
        try:
            closes.append(abs(float(str(c.get("cls_prc_p2", "0")).strip())))
        except (ValueError, TypeError):
            continue
    return closes or None


def _moving_average(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def detect_golden_cross(closes, short_period: int, long_period: int) -> bool:
    """직전 봉 대비 이번 봉에서 단기 이평선이 장기 이평선을 상향 돌파했는지."""
    if len(closes) < long_period + 1:
        return False
    short_now = _moving_average(closes, short_period)
    long_now = _moving_average(closes, long_period)
    short_prev = _moving_average(closes[:-1], short_period)
    long_prev = _moving_average(closes[:-1], long_period)
    if None in (short_now, long_now, short_prev, long_prev):
        return False
    return short_prev <= long_prev and short_now > long_now


def detect_dead_cross(closes, short_period: int, long_period: int) -> bool:
    """직전 봉 대비 이번 봉에서 단기 이평선이 장기 이평선을 하향 돌파했는지."""
    if len(closes) < long_period + 1:
        return False
    short_now = _moving_average(closes, short_period)
    long_now = _moving_average(closes, long_period)
    short_prev = _moving_average(closes[:-1], short_period)
    long_prev = _moving_average(closes[:-1], long_period)
    if None in (short_now, long_now, short_prev, long_prev):
        return False
    return short_prev >= long_prev and short_now < long_now
