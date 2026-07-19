"""
rank 명령 처리 - 상위 종목 랭킹 조회.

메뉴: 1 거래대금상위(IVU10210), 2 등락률상위(IVU10240), 3 거래량상위(IVU10280),
4 업종랭킹(IVM30010).
"""

from src.api.rank_info import ivu10210, ivu10240, ivu10280, ivm30010
from src.utils.formatting import format_number, compare_sign

RANK_FUNCS = {
    "1": ("거래대금상위", lambda session: ivu10210(inq_cnt="20", token=session.access_token, host_url=session.host_url)),
    "2": ("등락률상위", lambda session: ivu10240(token=session.access_token, host_url=session.host_url)),
    "3": ("거래량상위", lambda session: ivu10280(token=session.access_token, host_url=session.host_url)),
}


def handle_rank(args, session, execute_command=None):
    """
    rank 명령 처리 - 상위 종목 랭킹 조회

    사용법:
      /rank            - 메뉴 표시
      /rank 1          - 거래대금상위 Top 20
      /rank 2          - 등락률상위 Top 20
      /rank 3          - 거래량상위 Top 20
      /rank 4          - 업종랭킹
    """
    if not session.is_logged_in():
        return "❌ 먼저 로그인을 해야 합니다.\n/login real을 입력하세요."

    if not args:
        return _show_menu()

    rank_type = args[0].strip()

    if rank_type == "4":
        return _get_sector_rank(session)

    entry = RANK_FUNCS.get(rank_type)
    if not entry:
        return f"❌ 잘못된 번호입니다.\n\n{_show_menu()}"

    name, func = entry
    result = func(session)
    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get("resultMessage", "알 수 없는 오류")
        return f"❌ {name} 조회 실패\n\n오류: {error_msg}"

    return _format_stock_rank(name, result)


def _show_menu():
    return """📊 종목 랭킹 조회

1️⃣  /rank 1   →  💰 거래대금상위
2️⃣  /rank 2   →  📈 등락률상위
3️⃣  /rank 3   →  📊 거래량상위
4️⃣  /rank 4   →  🏭 업종랭킹"""


def _format_stock_rank(name, result):
    body = result["body"].get("dataBody", {})
    items = body.get("out2", []) or []
    if not items:
        return f"📊 {name}\n\n조회된 종목이 없습니다."

    lines = [f"📊 {name} (Top {len(items[:20])})\n"]
    for i, item in enumerate(items[:20], 1):
        sign = compare_sign(item.get("bdy_cmpr_ccd"))
        vlm = item.get("vlm") or item.get("acml_vlm")
        lines.append(
            f"{i:>2}. {item.get('is_nm', 'N/A')}({item.get('is_cd', '')})  "
            f"{format_number(item.get('now_prc'))}원  {sign}{format_number(item.get('up_dwn_r_p2'))}%  "
            f"거래량 {format_number(vlm)}"
        )
    return "\n".join(lines)


def _get_sector_rank(session):
    result = ivm30010(token=session.access_token, host_url=session.host_url)
    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get("resultMessage", "알 수 없는 오류")
        return f"❌ 업종랭킹 조회 실패\n\n오류: {error_msg}"

    body = result["body"].get("dataBody", {})
    items = body.get("out2", []) or []
    if not items:
        return "🏭 업종랭킹\n\n조회된 업종이 없습니다."

    lines = ["🏭 업종랭킹\n"]
    for i, item in enumerate(items[:20], 1):
        sign = compare_sign(item.get("bdy_cmpr_ccd"))
        lines.append(
            f"{i:>2}. {item.get('indx_nm', 'N/A')}  지수 {format_number(item.get('now_indx_p2'))}  "
            f"{sign}{format_number(item.get('up_dwn_r_p2'))}%"
        )
    return "\n".join(lines)
