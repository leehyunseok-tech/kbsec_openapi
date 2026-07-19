"""report/r 명령 처리 - 계좌 현황 + 미체결 주문 조회 (SSQM1801/SSQM2341 매핑)."""

from datetime import datetime

from src.api.account import ssqm1801, ssqm2341
from src.utils.formatting import format_number


def handle_report(args, session):
    """report/r 명령 처리 - 보유종목 + 체결/미체결 주문 조회"""
    if not session.is_logged_in():
        return "❌ 먼저 로그인을 해야 합니다.\n/login real을 입력하세요."

    holdings_result = ssqm1801(token=session.access_token, host_url=session.host_url)
    if not holdings_result["success"]:
        error_msg = holdings_result["body"].get("error") or holdings_result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 계좌 조회 실패\n\n오류: {error_msg}"

    records = holdings_result["body"].get("dataBody", {}).get("Record1", []) or []
    lines = ["📊 보유 종목"]
    if not records:
        lines.append("  보유 중인 종목이 없습니다.")
    else:
        for r in records:
            name = r.get("is_nm", "N/A")
            code = (r.get("is_no", "") or "").strip()[-6:]
            qty = format_number(r.get("ordr_psbl_q"))
            lines.append(f"  {name}({code})  주문가능수량 {qty}주")

    today = datetime.now().strftime("%Y%m%d")
    # inq_clsf는 2026-07-17 재수출 명세에서 INPUT에서 빠졌지만 운영 검증된 페이로드 유지를 위해 extra로 전송.
    orders_result = ssqm2341(
        ccls_clsf="2", ordr_dt=today, extra={"inq_clsf": "9"}, token=session.access_token, host_url=session.host_url
    )
    lines.append("\n📋 미체결 주문")
    if orders_result["success"]:
        pending = orders_result["body"].get("dataBody", {}).get("Record1", []) or []
        if not pending:
            lines.append("  미체결 주문이 없습니다.")
        else:
            for o in pending:
                lines.append(
                    f"  {o.get('hngl_shrt_nm', 'N/A')}  주문번호 {o.get('ordr_no', 'N/A')}  "
                    f"주문가 {format_number(o.get('ordr_uprc'))}원  미체결 {format_number(o.get('nccls_q'))}주"
                )
    else:
        error_msg = orders_result["body"].get("error") or orders_result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        lines.append(f"  조회 실패: {error_msg}")

    return "\n".join(lines)
