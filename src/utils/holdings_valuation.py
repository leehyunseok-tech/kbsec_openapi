"""
보유종목 평가손익 조회 (SSQM2952 잔고현황 조회(체결기준) 기반).

KB의 SSQM1801(보유주식 조회)에는 평균매입가가 없다. 대신 SSQM2952에 종목별
`byng_avr_prc`(매입평균가)와 `val_yld`(평가수익율)가 직접 내려오므로 이를 사용한다 —
수익률을 직접 계산하지 않아 더 정확하다.
"""

from src.api.account import ssqm2952


def _to_float(raw) -> float:
    try:
        return float(str(raw).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def get_holdings_with_profit(session):
    """
    보유종목 + 평가손익 조회.

    Returns:
        list[dict] {'code','name','qty','cur_price','avg_price','profit_rate'} 또는 실패 시 None
    """
    result = ssqm2952(excg_mktpr_ccd="A", token=session.access_token, host_url=session.host_url)
    if not result["success"]:
        return None

    records = result["body"].get("dataBody", {}).get("Record1", []) or []
    holdings = []
    for r in records:
        code = (r.get("is_cd") or "").strip()[-6:]
        if not code:
            continue
        qty = int(_to_float(r.get("hld_q")))
        if qty <= 0:
            continue
        holdings.append(
            {
                "code": code,
                "name": r.get("is_nm", code),
                "qty": qty,
                "cur_price": _to_float(r.get("now_prc")),
                "avg_price": _to_float(r.get("byng_avr_prc")),
                "profit_rate": _to_float(r.get("val_yld")),
            }
        )
    return holdings
