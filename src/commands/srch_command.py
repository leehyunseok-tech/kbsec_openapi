"""
srch 명령 처리 - 종목 현재가/기본정보 조회 (IVU10140/GSS10030 매핑).

국내는 IVU10140, 해외(미국)는 GSS10030을 사용한다. 종목코드 자리가 6자리 숫자면 국내,
아니면 mst/api/openapi_field_foren-us.mst에 등록된 티커인지 확인해 해외로 분기한다
(buy_command.py/sell_command.py와 동일한 판별 방식).
"""

from src.api.price_info import gss10030, ivu10140
from src.utils.formatting import compare_sign, format_number
from src.utils.stock_master import find_overseas_by_ticker


def _is_domestic_code(stock_code: str) -> bool:
    return stock_code.isdigit() and len(stock_code) == 6


def handle_srch(args: list[str], session) -> str:
    """
    srch 명령 처리 - 종목 현재가/기본정보 조회 (국내 6자리 코드 또는 해외 티커)

    사용법: /종목정보 {종목코드}  (예: /종목정보 105560, /종목정보 IONQ)
    """
    if not args:
        return "사용법: /종목정보 {종목코드}\n예: /종목정보 105560 (국내)  /종목정보 IONQ (해외)"

    if not session.is_logged_in():
        return "❌ 먼저 로그인을 해야 합니다.\n/login real을 입력하세요."

    stock_code = args[0].strip()

    if _is_domestic_code(stock_code):
        return _handle_domestic_srch(stock_code, session)

    overseas_stock = find_overseas_by_ticker(stock_code)
    if overseas_stock:
        return _handle_overseas_srch(overseas_stock, session)

    return f"""❌ '{stock_code}'는 국내 6자리 종목코드도, 등록된 해외 티커도 아닙니다.

예시:
/종목정보 105560  → KB금융 (국내)
/종목정보 IONQ    → 아이온큐

/종목검색 {stock_code} 로 종목명을 확인해보세요."""


def _handle_domestic_srch(stock_code, session):
    result = ivu10140(excg_clsf="0", shrt_cd=stock_code, token=session.access_token, host_url=session.host_url)

    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 종목정보 조회 실패\n\n오류: {error_msg}\n\n종목코드를 확인해주세요."

    body = result["body"].get("dataBody", {})
    sign = compare_sign(body.get("bdy_cmpr_ccd"))

    return f"""📈 {body.get("is_nm", "N/A")} ({stock_code})

💰 현재 시세
현재가: {format_number(body.get("now_prc"))}원
전일대비: {sign}{format_number(body.get("bdy_cmpr"))}원 ({format_number(body.get("up_dwn_r_p2"))}%)
시가: {format_number(body.get("opn_prc"))}원
고가: {format_number(body.get("hgh_prc"))}원
저가: {format_number(body.get("lw_prc"))}원
상한가: {format_number(body.get("ulmt_prc"))}원
하한가: {format_number(body.get("llmt_prc"))}원

📊 투자지표
시가총액: {format_number(body.get("opn_prc_tl_amt"))}백만원
PER: {format_number(body.get("per_p2"))}
PBR: {format_number(body.get("pbr_p2"))}
EPS: {format_number(body.get("eps_p2"))}

📊 거래 정보
거래량: {format_number(body.get("acml_vlm"))}
전일거래량: {format_number(body.get("bdy_vlm"))}
시장구분: {body.get("mkt_clsf_nm", "N/A")}"""


def _handle_overseas_srch(overseas_stock, session):
    ticker = overseas_stock.ticker
    display_name = overseas_stock.name_kr or overseas_stock.name_en

    result = gss10030(
        krx_cd=overseas_stock.exchange, is_cd=ticker, token=session.access_token, host_url=session.host_url
    )

    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 해외 종목정보 조회 실패\n\n오류: {error_msg}\n\n티커를 확인해주세요."

    body = result["body"].get("dataBody", {})
    sign = compare_sign(body.get("bdy_cmpr_ccd"))
    crncy = body.get("dl_crncy", "USD")

    return f"""📈 {display_name} ({ticker})  [{overseas_stock.exchange}]

💰 현재 시세
현재가: {format_number(body.get("now_prc_p4"))} {crncy}  (₩{format_number(body.get("now_prc_krw_p2"))})
전일대비: {sign}{format_number(body.get("bdy_cmpr_p4"))} {crncy} ({format_number(body.get("up_dwn_r_p2"))}%)
시가: {format_number(body.get("opn_prc_p4"))} {crncy}
고가: {format_number(body.get("hgh_prc_p4"))} {crncy}
저가: {format_number(body.get("lw_prc_p4"))} {crncy}

📊 투자지표
시가총액: {format_number(body.get("opn_prc_tl_amt"))} {crncy}
PER: {format_number(body.get("per_p4"))}
EPS: {format_number(body.get("eps_p4"))}

📊 거래 정보
거래량: {format_number(body.get("vlm"))}
전일거래량: {format_number(body.get("bdy_vlm"))}
52주 최고/최저: {format_number(body.get("wk52_max_prc_p4"))} / {format_number(body.get("wk52_min_prc_p4"))} {crncy}
(시세는 15분 지연일 수 있습니다 — mrkt_prc_clsf 참고)"""
