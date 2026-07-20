# 자동 생성 파일 — 수동 수정 금지.
# manage/generate/generate_api_client.py 재실행으로 갱신하세요.

"""종목 기본정보/기업개요

포함 API: IVM10050, SIAM4983, SIQM4900
"""

from src.api.client import call_business_api


def ivm10050(is_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVM10050 기업개요 — 종목의 간략한 기업 정보를 조회하는 API
    
    Args:
        is_cd: 종목코드
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="기업개요",
        api_code="IVM10050",
        endpoint="/api/v1/ivm10050",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def siam4983(Record1="", *, extra: dict | None = None, token, host_url) -> dict:
    """SIAM4983 종목기본정보 — 해외주식 종목 정보를 조회할 수 있는 API 입니다.
    
    Args:
        Record1: Record1
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "Record1": Record1,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="종목기본정보",
        api_code="SIAM4983",
        endpoint="/api/v1/siam4983",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def siqm4900(stnd_is_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SIQM4900 종목기본정보 — 
    
    Args:
        stnd_is_cd: 표준종목코드
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "stnd_is_cd": stnd_is_cd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="종목기본정보",
        api_code="SIQM4900",
        endpoint="/api/v1/siqm4900",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

