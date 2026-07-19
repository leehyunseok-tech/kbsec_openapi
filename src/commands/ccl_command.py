"""
ccl 명령 처리 - 주문 취소 (SSQM2341/SSAM1806 매핑).

주의: SSQM2341 응답의 Record1 개별 필드 중 종목코드 키(is_cd/stnd_is_cd)는
명세의 요청/응답 예시가 빈 배열이라 확정하지 못했다. 실전 사용 전
KB 샌드박스에서 실제 응답을 확인해 필요 시 아래 _extract_code를 조정할 것.
"""

from datetime import datetime

from src.api.account import ssqm2341
from src.api.order import ssam1806


def _extract_code(order: dict) -> str:
    raw = order.get("is_cd") or order.get("stnd_is_cd") or ""
    raw = raw.strip()
    return raw[-6:] if len(raw) >= 6 else raw


def handle_ccl(args, session):
    """
    ccl 명령 처리 - 주문 취소

    사용법:
      /ccl pend  - 미체결 주문 전체 취소
    """
    if not session.is_logged_in():
        return "❌ 먼저 로그인을 해야 합니다.\n/login real을 입력하세요."

    if not args or args[0].lower() != "pend":
        return "사용법: /ccl pend - 미체결 주문 전체 취소"

    today = datetime.now().strftime("%Y%m%d")
    # inq_clsf는 2026-07-17 재수출 명세에서 INPUT에서 빠졌지만 운영 검증된 페이로드 유지를 위해 extra로 전송.
    pending_result = ssqm2341(
        ccls_clsf="2", ordr_dt=today, extra={"inq_clsf": "9"}, token=session.access_token, host_url=session.host_url
    )
    if not pending_result["success"]:
        error_msg = pending_result["body"].get("error") or pending_result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return f"❌ 미체결 주문 조회 실패\n\n오류: {error_msg}"

    orders = pending_result["body"].get("dataBody", {}).get("Record1", []) or []
    if not orders:
        return "✅ 취소할 미체결 주문이 없습니다."

    success_list, fail_list = [], []
    for order in orders:
        ord_no = order.get("ordr_no", "")
        code = _extract_code(order)
        name = order.get("hngl_shrt_nm", code)
        qty = str(order.get("nccls_q", "0")).strip()

        result = ssam1806(
            is_cd=code,
            crct_clsf="2",
            orgn_ordr_no=ord_no,
            ordr_q=qty,
            token=session.access_token,
            host_url=session.host_url,
        )
        if result["success"]:
            success_list.append(f"  ✅ {name}({code}) {qty}주")
        else:
            msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get("resultMessage", "알 수 없는 오류")
            fail_list.append(f"  ❌ {name}({code}) {qty}주 - {msg}")

    lines = [f"미체결 일괄 취소: 성공 {len(success_list)}건 / 실패 {len(fail_list)}건\n"]
    if success_list:
        lines.append("취소 완료:")
        lines.extend(success_list)
    if fail_list:
        lines.append("\n취소 실패:")
        lines.extend(fail_list)
    return "\n".join(lines)
