# 자동 생성 파일 — 수동 수정 금지.
# docs/api/generate_api_client.py 재실행으로 갱신하세요.

"""시세 조회 (현재가/호가/체결/시장종합)

포함 API: GSA10020, GSS10030, GSS10040, IVSA0070, IVU10070, IVU10080, IVU10140
"""

from src.api.client import call_business_api


def gsa10020(krx_cd="", is_cd="", rcrd_c="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSA10020 체결 — 시간대별체결
    
    Args:
        krx_cd: 거래소코드 KRX_CD (선택) — NAS: 나스닥, NYS: 뉴욕거래소, AMX: 아멕스
        is_cd: 종목코드 IS_CD (선택)
        rcrd_c: 레코드수 RCRD_C (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "krx_cd": krx_cd,
            "is_cd": is_cd,
            "rcrd_c": rcrd_c,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="체결",
        api_code="GSA10020",
        endpoint="/api/v1/gsa10020",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def gss10030(krx_cd="", is_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSS10030 현재가 — 현재가
    
    Args:
        krx_cd: 거래소코드 (선택) — NAS: 나스닥, NYS: 뉴욕거래소, AMX: 아멕스
        is_cd: 종목코드 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "krx_cd": krx_cd,
            "is_cd": is_cd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="현재가",
        api_code="GSS10030",
        endpoint="/api/v1/gss10030",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def gss10040(krx_cd="", is_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSS10040 호가 — 호가
    
    Args:
        krx_cd: 거래소코드 (선택) — NAS: 나스닥, NYS: 뉴욕거래소, AMX: 아멕스
        is_cd: 종목코드 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "krx_cd": krx_cd,
            "is_cd": is_cd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="호가",
        api_code="GSS10040",
        endpoint="/api/v1/gss10040",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivsa0070(*, extra: dict | None = None, token, host_url) -> dict:
    """IVSA0070 시장종합 — 시장종합(IVSA0070)
    
    Args: (문서화된 요청 파라미터 없음)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="시장종합",
        api_code="IVSA0070",
        endpoint="/api/v1/ivsa0070",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10070(is_cd="", ovtm_mkt_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10070 호가 — 
    
    Args:
        is_cd: 종목코드 (선택)
        ovtm_mkt_clsf: 시간외장구분 (선택) — 0:정규장, 1:시간외
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "ovtm_mkt_clsf": ovtm_mkt_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="호가",
        api_code="IVU10070",
        endpoint="/api/v1/ivu10070",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10080(excg_clsf="", is_cd="", ovtm_mkt_clsf="", inq_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10080 체결 — 
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        is_cd: 종목코드 (선택)
        ovtm_mkt_clsf: 시간외장구분 (선택) — 0:정규장, 1:시간외
        inq_cnt: 조회건수 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "is_cd": is_cd,
            "ovtm_mkt_clsf": ovtm_mkt_clsf,
            "inq_cnt": inq_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="체결",
        api_code="IVU10080",
        endpoint="/api/v1/ivu10080",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10140(excg_clsf="", shrt_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10140 현재가 — 조회 시점의 주식 현재가를 조회 하는 API
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        shrt_cd: 단축코드 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "shrt_cd": shrt_cd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="현재가",
        api_code="IVU10140",
        endpoint="/api/v1/ivu10140",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

