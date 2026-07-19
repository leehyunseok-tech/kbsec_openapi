# 자동 생성 파일 — 수동 수정 금지.
# manage/generate/generate_api_client.py 재실행으로 갱신하세요.

"""거래내역/출금가능금액 조회

포함 API: SWQA2301, SWQM2412, SWQN2302
"""

from src.api.client import call_business_api


def swqa2301(inq_clsf, strt_dt="", end_dt="", is_no="", nxt_key="", srt_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """SWQA2301 거래내역 조회 — 
    
    Args:
        inq_clsf: 조회구분 (필수) — 전체
        strt_dt: 시작일자 (선택)
        end_dt: 종료일자 (선택)
        is_no: 종목번호 (선택)
        nxt_key: 다음키 (선택)
        srt_clsf: 정렬구분 (선택) — 1: 과거거래내역순, 2: 최근거래내역순
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "inq_clsf": inq_clsf,
            "strt_dt": strt_dt,
            "end_dt": end_dt,
            "is_no": is_no,
            "nxt_key": nxt_key,
            "srt_clsf": srt_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="거래내역 조회",
        api_code="SWQA2301",
        endpoint="/api/v1/swqa2301",
        data_body=data_body,
        required=["inq_clsf"],
        token=token,
        host_url=host_url,
    )


def swqm2412(inq_dt, dl_sq="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SWQM2412 거래내역 조회 상세 — 
    
    Args:
        inq_dt: 조회일자 (필수)
        dl_sq: 거래일련번호 (선택)
        nxt_key: 다음키 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "inq_dt": inq_dt,
            "dl_sq": dl_sq,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="거래내역 조회 상세",
        api_code="SWQM2412",
        endpoint="/api/v1/swqm2412",
        data_body=data_body,
        required=["inq_dt"],
        token=token,
        host_url=host_url,
    )


def swqn2302(ccd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SWQN2302 출금가능금액 조회 — D+1(익일), D+2(익익일) 출금 가능 금액을 조회합니다.
    
    Args:
        ccd: 구분코드 (선택) — 1:익일예수금/익익일예수금 포함
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "ccd": ccd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="출금가능금액 조회",
        api_code="SWQN2302",
        endpoint="/api/v1/swqn2302",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

