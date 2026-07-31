"""
buy 명령 처리 - 종목 매수주문 (SSAM1802/SKAM2101 매핑).

지원 범위: 국내(SSAM1802) 시장가/지정가/금액기반(max) 매수, 해외(SKAM2101)
시장가(현재가 자동 조회 후 지정가 제출)/지정가/금액기반(max) 매수 — 블랙리스트/쿨다운
가드는 국내·해외 모두 적용(settings_manager.py가 6자리 코드/티커 둘 다 저장 가능).
tick 조정 매수, 자동매매 중복매수 가드, 주문 타임아웃 감시는 아직 미지원
(docs/features.md 참고, 개선 예정).
"""

from src.api.order import skam2101, ssam1802
from src.api.price_info import ivu10140
from src.utils.cooldown_log import get_remaining, is_in_cooldown
from src.utils.formatting import format_number
from src.utils.price_lookup import get_overseas_current_price
from src.utils.settings_manager import SettingsManager
from src.utils.stock_master import find_overseas_by_ticker


def _is_domestic_code(stock_code: str) -> bool:
    return stock_code.isdigit() and len(stock_code) == 6


def _check_guards(stock_code: str):
    """블랙리스트·쿨다운 공통 검사 (국내 종목만 대상). 차단 시 에러 메시지, 통과 시 None 반환."""
    if stock_code in SettingsManager.get_blacklist():
        return f"❌ {stock_code}은(는) 블랙리스트 종목입니다. 매수/매도가 금지되어 있습니다."

    cooldown_hours = SettingsManager.get_cooldown_hours()
    if cooldown_hours > 0 and is_in_cooldown(stock_code, cooldown_hours):
        remaining = get_remaining(stock_code, cooldown_hours)
        return f"❌ {stock_code}은(는) 쿨다운 중입니다. 재매수 가능까지: {remaining}"
    return None


def _get_current_price(stock_code, session):
    result = ivu10140(excg_clsf="0", shrt_cd=stock_code, token=session.access_token, host_url=session.host_url)
    if not result["success"]:
        return None, "현재가 조회 실패"
    body = result["body"].get("dataBody", {})
    try:
        price = int(str(body.get("now_prc", "0")).strip())
    except ValueError:
        price = 0
    if price <= 0:
        return None, "현재가 정보를 얻을 수 없습니다"
    return {"price": price, "name": body.get("is_nm", "N/A")}, None


def _place_order(stock_code, quantity, price, session):
    """price=None이면 시장가."""
    ordr_ccd = "00" if price else "03"
    ordr_uprc = str(price) if price else "0"

    return ssam1802(
        mkt_tm_clsf="1",
        is_cd=stock_code,
        ordr_q=str(quantity),
        ordr_uprc=ordr_uprc,
        ordr_ccd=ordr_ccd,
        token=session.access_token,
        host_url=session.host_url,
    )


def _format_result(result, order_type, quantity):
    body = result["body"].get("dataBody", {})
    return f"""✅ 매수주문 접수

{order_type}  {quantity}주
주문번호: {body.get("ordr_no", "N/A")}
메시지: {body.get("o_msg", "")}"""


# ── 해외주식 매수 (SKAM2101) ──────────────────────────────────────────────────
def _resolve_overseas_price(overseas_stock, price, session):
    """price가 None이면 현재가를 조회해 반환(시장가처럼 동작), 아니면 그대로 반환.
    Returns (price, error_msg)."""
    if price is not None:
        return price, None
    price_info = get_overseas_current_price(
        overseas_stock.exchange, overseas_stock.ticker, session.access_token, session.host_url
    )
    if price_info is None:
        return None, "해외 현재가 조회 실패"
    return price_info["price"], None


def _place_overseas_order(overseas_stock, quantity, price, session):
    """지정가(frgn_ordr_typ_cd=2)로 제출. 시장가는 상위에서 현재가를 채운 뒤 호출한다 —
    KB API가 해외 시장가 주문의 가격 필드 처리 방식을 명세에 밝히지 않아, 현재가를
    직접 조회해 지정가로 제출하는 방식으로 시장가를 흉내낸다."""
    return skam2101(
        trd_dl_ccd="02",
        is_cd=overseas_stock.ticker,
        frgn_ordr_typ_cd="2",
        frgn_ordr_q=str(quantity),
        frgn_ordr_prc_p4=f"{price:.2f}",
        # 2026-07-17 재수출 명세에서 frgn_krx_ccd가 INPUT에서 빠졌지만, 이 값을 포함한
        # 요청이 운영에서 검증된 형태라 페이로드를 바꾸지 않기 위해 extra로 유지한다.
        extra={"frgn_krx_ccd": "US"},
        token=session.access_token,
        host_url=session.host_url,
    )


def _format_overseas_result(result, order_type, quantity, ticker):
    body = result["body"].get("dataBody", {})
    return f"""✅ 해외 매수주문 접수

{ticker}  {order_type}  {quantity}주
주문번호: {body.get("ordr_no", "N/A")}
메시지: {body.get("o_msg", "")}"""


def _handle_overseas_buy(overseas_stock, args, session):
    ticker = overseas_stock.ticker
    display_name = overseas_stock.name_kr or overseas_stock.name_en

    guard_msg = _check_guards(ticker)
    if guard_msg:
        return guard_msg

    # ── max 모드: 금액(USD) 기반 시장가 매수 ──────────────────────────────────
    if args[1].lower() == "max":
        try:
            max_amount = float(args[2].strip())
            if max_amount <= 0:
                raise ValueError
        except (ValueError, IndexError):
            return f"❌ 사용법: /매수 {ticker} max {{금액(USD)}}"

        price_info = get_overseas_current_price(overseas_stock.exchange, ticker, session.access_token, session.host_url)
        if price_info is None:
            return "❌ 해외 현재가 조회 실패"

        quantity = int(max_amount / price_info["price"])
        if quantity <= 0:
            return (
                f"❌ 구매 불가능\n종목: {display_name}({ticker})\n"
                f"현재가: ${price_info['price']:.2f}  최대금액: ${max_amount:.2f}\n"
                f"최대 금액이 현재가보다 작아 1주도 구매할 수 없습니다."
            )

        result = _place_overseas_order(overseas_stock, quantity, price_info["price"], session)
        if not result["success"]:
            error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
                "resultMessage", "알 수 없는 오류"
            )
            return f"❌ 해외 금액 기반 매수 실패\n\n오류: {error_msg}"

        actual_amount = quantity * price_info["price"]
        order_type = f"시장가(현재가 ${price_info['price']:.2f} 기준)"
        return (
            f"{_format_overseas_result(result, order_type, quantity, ticker)}\n\n"
            f"📊 상세: {display_name}({ticker})  현재가 ${price_info['price']:.2f}\n"
            f"최대금액 ${max_amount:.2f} → 실제 ${actual_amount:.2f}"
        )

    # ── 기본 수량 모드 ────────────────────────────────────────────────────────
    try:
        quantity = int(args[1].strip())
        if quantity <= 0:
            raise ValueError
    except ValueError:
        return "❌ 수량은 양의 정수여야 합니다."

    price = None
    if len(args) >= 3:
        try:
            price = float(args[2].strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            return "❌ 가격은 양의 숫자여야 합니다."

    was_market = price is None
    price, err = _resolve_overseas_price(overseas_stock, price, session)
    if err:
        return f"❌ {err}"

    result = _place_overseas_order(overseas_stock, quantity, price, session)
    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 해외 매수주문 실패\n\n오류: {error_msg}"

    order_type = f"시장가(현재가 ${price:.2f} 기준)" if was_market else f"지정가 ${price:.2f}"
    return _format_overseas_result(result, order_type, quantity, ticker)


def handle_buy(args: list[str], session) -> str:
    """
    buy 명령 처리 - 종목 매수주문 (국내 6자리 코드 또는 해외 티커)

    사용법:
      /매수 {종목코드} {수량}         - 시장가 매수 (해외는 현재가 조회 후 지정가로 제출)
      /매수 {종목코드} {수량} {지정가} - 지정가 매수
      /매수 {종목코드} max {금액}     - 금액 범위 내 최대 매수 (국내는 원화, 해외는 USD)

    해외 종목은 종목코드 자리에 티커(예: IONQ)를 입력하세요. mst/api/openapi_field_foren-us.mst에
    등록된 티커인지로 국내/해외를 판별한다(자연어 입력 시엔 src/utils/stock_resolver.py가 미리
    종목명을 코드/티커로 해석해 넘겨준다).
    """
    if len(args) < 2:
        return (
            "사용법:\n"
            "/매수 {종목코드} {수량}          - 시장가 매수 (해외는 현재가 조회 후 지정가로 제출)\n"
            "/매수 {종목코드} {수량} {지정가} - 지정가 매수\n"
            "/매수 {종목코드} max {금액}      - 금액 범위 내 최대 매수 (국내: 원화, 해외: USD)"
        )

    if not session.is_logged_in():
        return "❌ 먼저 로그인을 해야 합니다.\n/login real을 입력하세요."

    stock_code = args[0].strip()

    if _is_domestic_code(stock_code):
        return _handle_domestic_buy(stock_code, args, session)

    overseas_stock = find_overseas_by_ticker(stock_code)
    if overseas_stock:
        return _handle_overseas_buy(overseas_stock, args, session)

    return f"❌ '{stock_code}'는 국내 6자리 종목코드도, 등록된 해외 티커도 아닙니다.\n/종목검색 {stock_code} 로 종목명을 확인해보세요."


def _handle_domestic_buy(stock_code, args, session):
    guard_msg = _check_guards(stock_code)
    if guard_msg:
        return guard_msg

    # ── max 모드: 금액 기반 시장가 매수 ─────────────────────────────────────
    if args[1].lower() == "max":
        try:
            max_amount = int(args[2].strip())
            if max_amount <= 0:
                raise ValueError
        except (ValueError, IndexError):
            return "❌ 사용법: /매수 {종목코드} max {금액}"

        price_info, err = _get_current_price(stock_code, session)
        if err:
            return f"❌ {err}"

        quantity = max(int(max_amount / price_info["price"]), 0)
        if quantity <= 0:
            return (
                f"❌ 구매 불가능\n종목: {price_info['name']}({stock_code})\n"
                f"현재가: {format_number(price_info['price'])}원  최대금액: {format_number(max_amount)}원\n"
                f"최대 금액이 현재가보다 작아 1주도 구매할 수 없습니다."
            )

        result = _place_order(stock_code, quantity, None, session)
        if not result["success"]:
            error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
                "resultMessage", "알 수 없는 오류"
            )
            return f"❌ 금액 기반 매수 실패\n\n오류: {error_msg}"

        actual_amount = quantity * price_info["price"]
        return (
            f"{_format_result(result, '시장가', quantity)}\n\n"
            f"📊 상세: {price_info['name']}({stock_code})  현재가 {format_number(price_info['price'])}원\n"
            f"최대금액 {format_number(max_amount)}원 → 실제 {format_number(actual_amount)}원"
        )

    # ── 기본 수량 모드 ────────────────────────────────────────────────────────
    try:
        quantity = int(args[1].strip())
        if quantity <= 0:
            raise ValueError
    except ValueError:
        return "❌ 수량은 양의 정수여야 합니다."

    price = None
    if len(args) >= 3:
        try:
            price = int(args[2].strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            return "❌ 가격은 양의 정수여야 합니다."

    result = _place_order(stock_code, quantity, price, session)
    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 매수주문 실패\n\n오류: {error_msg}"

    order_type = f"지정가 {format_number(price)}원" if price else "시장가"
    return _format_result(result, order_type, quantity)
