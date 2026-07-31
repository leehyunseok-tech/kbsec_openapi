"""
sell 명령 처리 - 종목 매도주문 (SSAM1801/SSQM1801/SKAM2101 매핑).

해외(SKAM2101) 매도는 KB API 74개 전체에 종목별 해외 보유수량 조회 API가 없어(계좌
잔고 조회는 SPQO2226 등 통화별 예수금뿐, 종목별 해외 보유수량은 미제공) 수량을 반드시
명시해야 한다("전량 매도"/"sell all" 미지원, buy_command.py의 해외 지원과 비대칭 —
API 자체가 없어 해결 불가, docs/features.md 참고). 가격을 생략하면 국내와 동일하게
현재가를 조회해 지정가로 제출한다(시장가처럼 동작). 블랙리스트/쿨다운 가드는 국내·해외
모두 적용된다.
"""

from src.api.account import ssqm1801
from src.api.order import skam2101, ssam1801
from src.utils.cooldown_log import record_sell
from src.utils.formatting import format_number
from src.utils.price_lookup import get_overseas_current_price
from src.utils.settings_manager import SettingsManager
from src.utils.stock_master import find_overseas_by_ticker


def _is_domestic_code(stock_code: str) -> bool:
    return stock_code.isdigit() and len(stock_code) == 6


def _normalize_code(is_no: str) -> str:
    """KB 보유주식 조회의 종목번호("A005930")를 6자리 코드로 정규화."""
    is_no = (is_no or "").strip()
    return is_no[-6:] if len(is_no) >= 6 else is_no


def _get_holdings(session):
    result = ssqm1801(token=session.access_token, host_url=session.host_url)
    if not result["success"]:
        return None, result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
    records = result["body"].get("dataBody", {}).get("Record1", []) or []
    return records, None


def _place_sell(stock_code, quantity, price, session):
    ordr_ccd = "00" if price else "03"
    ordr_uprc = str(price) if price else "0"
    return ssam1801(
        mkt_tm_clsf="1",
        is_cd=stock_code,
        ordr_q=str(quantity),
        ordr_uprc=ordr_uprc,
        ordr_ccd=ordr_ccd,
        token=session.access_token,
        host_url=session.host_url,
    )


# ── 해외주식 매도 (SKAM2101) ──────────────────────────────────────────────────
def _place_overseas_sell(overseas_stock, quantity, price, session):
    """지정가(frgn_ordr_typ_cd=2)로 제출. buy_command.py의 해외 매수와 동일 방식."""
    return skam2101(
        trd_dl_ccd="01",
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


def _handle_overseas_sell(overseas_stock, args, session):
    ticker = overseas_stock.ticker

    if ticker in SettingsManager.get_blacklist():
        return f"❌ {ticker}은(는) 블랙리스트 종목입니다."

    if len(args) < 2:
        return f"❌ 해외 종목은 수량을 반드시 입력해야 합니다.\n사용법: /매도 {ticker} {{수량}} [{{지정가}}]"

    try:
        quantity = int(args[1])
        if quantity <= 0:
            return "❌ 수량은 1 이상이어야 합니다."
    except ValueError:
        return "❌ 수량은 숫자여야 합니다."

    price = None
    if len(args) >= 3:
        try:
            price = float(args[2])
            if price <= 0:
                return "❌ 지정가는 0보다 커야 합니다."
        except ValueError:
            return "❌ 지정가는 숫자여야 합니다."

    was_market = price is None
    if price is None:
        price_info = get_overseas_current_price(overseas_stock.exchange, ticker, session.access_token, session.host_url)
        if price_info is None:
            return "❌ 해외 현재가 조회 실패"
        price = price_info["price"]

    result = _place_overseas_sell(overseas_stock, quantity, price, session)
    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 해외 매도주문 실패\n\n오류: {error_msg}"

    record_sell(ticker)
    body = result["body"].get("dataBody", {})
    order_type = f"시장가(현재가 ${price:.2f} 기준)" if was_market else f"지정가 ${price:.2f}"
    return f"""✅ 해외 매도주문 접수

{ticker}  {order_type}  {quantity}주
주문번호: {body.get("ordr_no", "N/A")}
메시지: {body.get("o_msg", "")}"""


def handle_sell(args: list[str], session) -> str:
    """
    sell 명령 처리 - 종목 매도주문 (국내 6자리 코드 또는 해외 티커)

    사용법:
      /매도 all                        - 보유 전체 종목 시장가 매도 (국내만 해당)
      /매도 {종목코드}                 - 전량 매도 (국내만; 시장가)
      /매도 {종목코드} {수량}          - 시장가 매도 (해외는 현재가 조회 후 지정가로 제출)
      /매도 {종목코드} {수량} {지정가} - 지정가 매도

    해외 종목은 종목코드 자리에 티커(예: IONQ)를 입력하고, 수량을 반드시 명시해야 합니다
    (보유수량 자동조회 미지원 — "sell IONQ" 전량 매도 불가, "sell IONQ 5"처럼 입력).
    """
    if not session.is_logged_in():
        return "❌ 먼저 로그인을 해야 합니다.\n/login real을 입력하세요."

    if not args:
        return (
            "❌ 사용법:\n"
            "/매도 all                        - 보유 전체 종목 시장가 매도 (국내만 해당)\n"
            "/매도 {종목코드}                 - 전량 매도 (국내만)\n"
            "/매도 {종목코드} {수량}          - 시장가 매도\n"
            "/매도 {종목코드} {수량} {지정가} - 지정가 매도"
        )

    if args[0].lower() == "all":
        return _handle_sell_all(session)

    stock_code = args[0]

    if _is_domestic_code(stock_code):
        return _handle_domestic_sell(stock_code, args, session)

    overseas_stock = find_overseas_by_ticker(stock_code)
    if overseas_stock:
        return _handle_overseas_sell(overseas_stock, args, session)

    return f"❌ '{stock_code}'는 국내 6자리 종목코드도, 등록된 해외 티커도 아닙니다.\n/종목검색 {stock_code} 로 종목명을 확인해보세요."


def _handle_domestic_sell(stock_code, args, session):
    if stock_code in SettingsManager.get_blacklist():
        return f"❌ {stock_code}은(는) 블랙리스트 종목입니다."

    quantity, price = None, None
    if len(args) >= 2:
        try:
            quantity = int(args[1])
            if quantity <= 0:
                return "❌ 수량은 1 이상이어야 합니다."
        except ValueError:
            return "❌ 수량은 숫자여야 합니다."
    if len(args) >= 3:
        try:
            price = int(args[2])
            if price <= 0:
                return "❌ 지정가는 1 이상이어야 합니다."
        except ValueError:
            return "❌ 지정가는 숫자여야 합니다."

    if quantity is None:
        records, err = _get_holdings(session)
        if err:
            return f"❌ 보유종목 조회 실패\n\n오류: {err}"
        found = next((r for r in records if _normalize_code(r.get("is_no")) == stock_code), None)
        if not found:
            return f"❌ 종목 {stock_code}을(를) 보유하고 있지 않습니다."
        try:
            quantity = int(str(found.get("ordr_psbl_q", "0")).strip())
        except ValueError:
            quantity = 0
        if quantity <= 0:
            return f"❌ 종목 {stock_code}의 매도 가능수량이 0입니다."

    result = _place_sell(stock_code, quantity, price, session)
    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 매도주문 실패\n\n오류: {error_msg}"

    record_sell(stock_code)
    body = result["body"].get("dataBody", {})
    order_type = f"지정가 {format_number(price)}원" if price else "시장가"
    return f"""✅ 매도주문 접수

{order_type}  {quantity}주
주문번호: {body.get("ordr_no", "N/A")}
메시지: {body.get("o_msg", "")}"""


def _handle_sell_all(session) -> str:
    records, err = _get_holdings(session)
    if err:
        return f"❌ 보유종목 조회 실패\n\n오류: {err}"
    if not records:
        return "✅ 보유 중인 종목이 없습니다."

    blacklist = SettingsManager.get_blacklist()
    success_list, fail_list, skip_list = [], [], []

    for record in records:
        code = _normalize_code(record.get("is_no"))
        name = record.get("is_nm", code)
        if not code:
            continue
        if code in blacklist:
            skip_list.append(f"  ⏭️  {name}({code}) - 블랙리스트 제외")
            continue
        try:
            qty = int(str(record.get("ordr_psbl_q", "0")).strip())
        except ValueError:
            qty = 0
        if qty <= 0:
            continue

        result = _place_sell(code, qty, None, session)
        if result["success"]:
            record_sell(code)
            success_list.append(f"  ✅ {name}({code}) {qty:,}주")
        else:
            msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
                "resultMessage", "알 수 없는 오류"
            )
            fail_list.append(f"  ❌ {name}({code}) {qty:,}주 - {msg}")

    lines = [
        f"전체 매도: 성공 {len(success_list)}건 / 실패 {len(fail_list)}건"
        + (f" / 제외 {len(skip_list)}건" if skip_list else "")
    ]
    if success_list:
        lines.append("\n매도 완료:")
        lines.extend(success_list)
    if fail_list:
        lines.append("\n매도 실패:")
        lines.extend(fail_list)
    if skip_list:
        lines.append("\n제외 (블랙리스트):")
        lines.extend(skip_list)
    return "\n".join(lines)
