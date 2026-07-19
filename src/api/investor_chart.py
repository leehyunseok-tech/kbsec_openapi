# 자동 생성 파일 — 수동 수정 금지.
# docs/api/generate_api_client.py 재실행으로 갱신하세요.

"""거래원/투자자/프로그램매매

포함 API: IVU10420, IVU10430, IVU10450
"""

from src.api.client import call_business_api


def ivu10420(is_cd, excg_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10420 거래원 — 당일주요외국계거래원
    
    Args:
        is_cd: 종목코드 (필수)
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "excg_clsf": excg_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="거래원",
        api_code="IVU10420",
        endpoint="/api/v1/ivu10420",
        data_body=data_body,
        required=["is_cd"],
        token=token,
        host_url=host_url,
    )


def ivu10430(excg_clsf="", is_cd="", strt_dt="", end_dt="", amt_q_clsf="", trd_clsf="", acml_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10430 투자자 — 
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        is_cd: 종목코드 (선택)
        strt_dt: 시작일자 (선택)
        end_dt: 종료일자 (선택)
        amt_q_clsf: 금액수량구분 (선택) — 1:금액, 2:수량
        trd_clsf: 매매구분 (선택) — 1:순매수, 2:매수, 3:매도
        acml_clsf: 누적구분 (선택) — 0:누적안함, 1:누적
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "is_cd": is_cd,
            "strt_dt": strt_dt,
            "end_dt": end_dt,
            "amt_q_clsf": amt_q_clsf,
            "trd_clsf": trd_clsf,
            "acml_clsf": acml_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="투자자",
        api_code="IVU10430",
        endpoint="/api/v1/ivu10430",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10450(excg_clsf="", is_cd="", amt_q_clsf="", prd_clsf="", inq_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10450 프로그램 — 
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        is_cd: 종목코드 (선택)
        amt_q_clsf: 금액수량구분 (선택) — 금액수량구분 : 1:금액, 2:수량
        prd_clsf: 기간구분 (선택) — 기간구분 : 1:시간별, 2:일별
        inq_cnt: 조회건수 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "is_cd": is_cd,
            "amt_q_clsf": amt_q_clsf,
            "prd_clsf": prd_clsf,
            "inq_cnt": inq_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="프로그램",
        api_code="IVU10450",
        endpoint="/api/v1/ivu10450",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

