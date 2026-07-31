"""현재가 조회 헬퍼 (국내 IVU10140 / 해외 GSS10030 기반). 폴링 모니터·매매 명령이 공용으로 사용."""

from src.api.price_info import gss10030, ivu10140


def get_current_price(stock_code: str, token: str, host_url: str):
    """
    국내 종목 현재가 조회.

    Returns:
        dict {'price': float, 'name': str} 또는 실패 시 None
    """
    result = ivu10140(excg_clsf="0", shrt_cd=stock_code, token=token, host_url=host_url)
    if not result["success"]:
        return None
    body = result["body"].get("dataBody", {})
    try:
        price = abs(float(str(body.get("now_prc", "0")).strip()))
    except (ValueError, TypeError):
        return None
    if price <= 0:
        return None
    return {"price": price, "name": body.get("is_nm", stock_code)}


def get_overseas_current_price(exchange: str, ticker: str, token: str, host_url: str):
    """
    해외 종목 현재가 조회 (GSS10030). 시장가처럼 동작하는 주문(현재가로 지정가 제출)에 사용.

    Returns:
        dict {'price': float} 또는 실패 시 None
    """
    result = gss10030(krx_cd=exchange, is_cd=ticker, token=token, host_url=host_url)
    if not result["success"]:
        return None
    body = result["body"].get("dataBody", {})
    try:
        price = abs(float(str(body.get("now_prc_p4", "0")).strip()))
    except (ValueError, TypeError):
        return None
    if price <= 0:
        return None
    return {"price": price}
