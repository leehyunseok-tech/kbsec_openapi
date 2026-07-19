# 자동 생성 파일 — 수동 수정 금지.
# manage/generate/generate_api_client.py 재실행으로 갱신하세요.

"""통합차트

포함 API: GSC10060, IVS11560
"""

from src.api.client import call_business_api


def gsc10060(krx_cd="", is_cd="", chrt_clsf="", bndl="", mdfy_stk_prc_use_f="", rcrd_c="", srch_strt_dy="", clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSC10060 통합차트 — 차트
    
    Args:
        krx_cd: 거래소코드 KRX_CD (선택)
        is_cd: 종목코드 IS_CD (선택)
        chrt_clsf: 차트구분 CHRT_CLSF (선택) — 1:틱 2:분 3:일 4:주 5:월 6:년
        bndl: 묶음 BNDL (선택) — 묶음틱 개수
        mdfy_stk_prc_use_f: 수정주가사용여부 MDFY_STK_PRC_USE_F (선택) — 0:수정주가 미사용 1:수정주가사용
        rcrd_c: 레코드수 RCRD_C (선택) — 최대요청개수:5000
        srch_strt_dy: 검색시작일 SRCH_STRT_DY (선택) — 과거일자 검색용
        clsf: 구분 CLSF (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "krx_cd": krx_cd,
            "is_cd": is_cd,
            "chrt_clsf": chrt_clsf,
            "bndl": bndl,
            "mdfy_stk_prc_use_f": mdfy_stk_prc_use_f,
            "rcrd_c": rcrd_c,
            "srch_strt_dy": srch_strt_dy,
            "clsf": clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="통합차트",
        api_code="GSC10060",
        endpoint="/api/v1/gsc10060",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivs11560(info_ccd, mkt_clsf, chrt_clsf, is_cd, inq_clsf, minute_tck_indx="", strt_dy="", inq_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVS11560 통합차트 — 통합차트
    
    Args:
        info_ccd: 정보구분코드 (필수) — 1:원주가 2:수정주가(KOSPI, KOSDAQ 종목만)
        mkt_clsf: 시장구분 (필수) — 0:KOSPI 1:KOSDAQ
        chrt_clsf: 차트구분 (필수) — D:일별 W:주별 M:월별 Y:년별(주식) B:분봉 T:틱
        is_cd: 종목코드 (필수)
        inq_clsf: 조회구분 (필수) — 1:날짜로 조회 2:데이터수로 조회
        minute_tck_indx: MINUTE틱지수 (선택) — 분, 틱, 일 선택시 조회 주기 표시
        strt_dy: 시작일 (선택)
        inq_cnt: 조회건수 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "info_ccd": info_ccd,
            "mkt_clsf": mkt_clsf,
            "chrt_clsf": chrt_clsf,
            "is_cd": is_cd,
            "inq_clsf": inq_clsf,
            "minute_tck_indx": minute_tck_indx,
            "strt_dy": strt_dy,
            "inq_cnt": inq_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="통합차트",
        api_code="IVS11560",
        endpoint="/api/v1/ivs11560",
        data_body=data_body,
        required=["info_ccd", "mkt_clsf", "chrt_clsf", "is_cd", "inq_clsf"],
        token=token,
        host_url=host_url,
    )

