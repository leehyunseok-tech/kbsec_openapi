# 자동 생성 파일 — 수동 수정 금지.
# manage/generate/generate_api_client.py 재실행으로 갱신하세요.

"""시장/거시 정보 (세계지수/환율/증시주변자금동향/장운영상태/해외시세분석)

포함 API: GSA10600, IVA10370, IVA60140, IVA60190, SZQM0771
"""

from src.api.client import call_business_api


def gsa10600(frex_clsf="", clsf="", rnk="", is_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSA10600 해외시세분석 — 해외시세분석
    
    Args:
        frex_clsf: 해외거래소구분 — AA:미국전체 AB:나스닥 AC:뉴욕 AD:아멕스
        clsf: 구분 — 1:전일대비 2: 시가총액 3:거래량 4:52주 신고가 5:52주 신저가 6:PER 7:EPS, 8:배당수익률, a:거래대금
        rnk: 순위 — 1:상위 2:하위
        is_cnt: 종목건수
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "frex_clsf": frex_clsf,
            "clsf": clsf,
            "rnk": rnk,
            "is_cnt": is_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="해외시세분석",
        api_code="GSA10600",
        endpoint="/api/v1/gsa10600",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def iva10370(*, extra: dict | None = None, token, host_url) -> dict:
    """IVA10370 증시주변자금동향 — 
    
    Args: (문서화된 요청 파라미터 없음)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="증시주변자금동향",
        api_code="IVA10370",
        endpoint="/api/v1/iva10370",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def iva60140(lnd_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVA60140 세계지수 — 세계지수
    
    Args:
        lnd_clsf: 대륙구분 — S: 아시아, C: 아메라키, E: 유럽
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "lnd_clsf": lnd_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="세계지수",
        api_code="IVA60140",
        endpoint="/api/v1/iva60140",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def iva60190(*, extra: dict | None = None, token, host_url) -> dict:
    """IVA60190 환율종합 — 
    
    Args: (문서화된 요청 파라미터 없음)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="환율종합",
        api_code="IVA60190",
        endpoint="/api/v1/iva60190",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def szqm0771(*, extra: dict | None = None, token, host_url) -> dict:
    """SZQM0771 장운영상태 — 
    
    Args: (문서화된 요청 파라미터 없음)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="장운영상태",
        api_code="SZQM0771",
        endpoint="/api/v1/szqm0771",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

