# 자동 생성 파일 — 수동 수정 금지.
# manage/generate/generate_api_client.py 재실행으로 갱신하세요.

"""각종 상위/순위 조회

포함 API: GSA10150, GSA10170, GSS10180, IVM30010, IVS10910, IVS10920, IVS11190, IVU10020, IVU10210, IVU10240, IVU10270, IVU10280, IVU10550
"""

from src.api.client import call_business_api


def gsa10150(krx_cd="", std_dy="", vlm="", is_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSA10150 거래량상위 — 거래량상위
    
    Args:
        krx_cd: 거래소코드 (선택) — NAS: 나스닥, NYS: 뉴욕거래소, AMX: 아멕스
        std_dy: 기준일 (선택) — 01: 전일,05:5일,10:10일, 20:20일, 60:60일, 90:90일
        vlm: 거래량 (선택)
        is_cnt: 종목건수 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "krx_cd": krx_cd,
            "std_dy": std_dy,
            "vlm": vlm,
            "is_cnt": is_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="거래량상위",
        api_code="GSA10150",
        endpoint="/api/v1/gsa10150",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def gsa10170(krx_cd="", is_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSA10170 시가총액상위 — 시가총액상위
    
    Args:
        krx_cd: 거래소코드 KRX_CD (선택) — NAS: 나스닥, NYS: 뉴욕거래소, AMX: 아멕스
        is_cnt: 종목건수 IS_CNT (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "krx_cd": krx_cd,
            "is_cnt": is_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="시가총액상위",
        api_code="GSA10170",
        endpoint="/api/v1/gsa10170",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def gss10180(krx_cd="", clsf="", clsf2="", std_dy="", vlm="", is_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """GSS10180 신고_신저 — 신고신저
    
    Args:
        krx_cd: 거래소코드 KRX_CD (선택) — NAS: 나스닥, NYS: 뉴욕거래소, AMX: 아멕스
        clsf: 구분 CLSF (1:신고 2:신저) (선택) — 0: 신고 1: 신저
        clsf2: 구분2 CLSF2 (1:일시돌파 2:돌파유지) (선택) — 0: 일시돌파 1: 돌파유지
        std_dy: 기준일 STD_DY (01:전일 05:5일 10:10일) (선택) — 01: 전일,05:5일,10:10일, 20:20일, 60:60일, 90:90일
        vlm: 거래량 VLM (선택)
        is_cnt: 종목건수 IS_CNT (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "krx_cd": krx_cd,
            "clsf": clsf,
            "clsf2": clsf2,
            "std_dy": std_dy,
            "vlm": vlm,
            "is_cnt": is_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="신고_신저",
        api_code="GSS10180",
        endpoint="/api/v1/gss10180",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivm30010(mkt_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVM30010 업종랭킹 — 업종랭킹(MTS)(IVM30010)
    
    Args:
        mkt_clsf: 시장구분 (선택) — 1:코스피 2:코스닥
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "mkt_clsf": mkt_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="업종랭킹",
        api_code="IVM30010",
        endpoint="/api/v1/ivm30010",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivs10910(mkt_clsf="", inq_cnt="", srt_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVS10910 시가대비등락률 상위 — 시가대비등락율상위(IVS10910)
    
    Args:
        mkt_clsf: 시장구분 (선택) — 1:전체, 2:KOSPI, 3:KOSDAQ, 4:KOSPI200, 5:KOSDAQ150
        inq_cnt: 조회건수 (선택)
        srt_clsf: 정렬구분 (선택) — 1:상승, 2:하락
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "mkt_clsf": mkt_clsf,
            "inq_cnt": inq_cnt,
            "srt_clsf": srt_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="시가대비등락률 상위",
        api_code="IVS10910",
        endpoint="/api/v1/ivs10910",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivs10920(inq_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVS10920 시가총액 상위 — 시가총액상위
    
    Args:
        inq_cnt: 조회건수 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "inq_cnt": inq_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="시가총액 상위",
        api_code="IVS10920",
        endpoint="/api/v1/ivs10920",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivs11190(mkt_clsf="", srt_clsf="", thdy_bdy_clsf="", inq_cnt="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVS11190 기간외등락률 순위 — 시간외단일가등락율순위(IVS11190)
    
    Args:
        mkt_clsf: 시장구분 (선택) — 1:전체, 2:거래소, 3:코스닥
        srt_clsf: 정렬구분 (선택) — 1:상승율, 2:하락율
        thdy_bdy_clsf: 당일전일구분 (선택) — 1:당일, 2:전일
        inq_cnt: 조회건수 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "mkt_clsf": mkt_clsf,
            "srt_clsf": srt_clsf,
            "thdy_bdy_clsf": thdy_bdy_clsf,
            "inq_cnt": inq_cnt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="기간외등락률 순위",
        api_code="IVS11190",
        endpoint="/api/v1/ivs11190",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10020(excg_clsf="", mkt_clsf="", invstr_ccd="", prd_clsf="", rnk_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10020 매매 상위 — 외국인기관매매상위
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        mkt_clsf: 시장구분 (선택) — 0:거래소, 1:코스닥, 2:전체
        invstr_ccd: 투자자구분코드 (선택) — 0:외국인 1:기관 2:외국인+기관 3:증권 4:보험 5:투신 6:사모펀드 7:은행 8:종금 9:기금 A:기타 B:국가지자체 C:개인 D:기타외국인
        prd_clsf: 기간구분 (선택) — 0:전일 1:1주 2:1달 3:3달 4:6달 5:1년 6:연초
        rnk_clsf: 순위구분 (선택) — 0:순매수 1:순매도 2:지분증가 3:지분감소 4:연속순매수 5:연속순매도
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "mkt_clsf": mkt_clsf,
            "invstr_ccd": invstr_ccd,
            "prd_clsf": prd_clsf,
            "rnk_clsf": rnk_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매매 상위",
        api_code="IVU10020",
        endpoint="/api/v1/ivu10020",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10210(excg_clsf="", mkt_clsf="", thdy_bdy_clsf="", inq_cnt="", srt_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10210 거래대금 상위 — ATS통합-거래대금상위
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        mkt_clsf: 시장구분 (선택) — 1:전체, 2:KOSPI, 3:KOSDAQ
        thdy_bdy_clsf: 당일전일구분 (선택) — 1:당일, 2:전일
        inq_cnt: 조회건수 (선택)
        srt_clsf: 정렬구분 (선택) — 1:상위, 2:하위
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "mkt_clsf": mkt_clsf,
            "thdy_bdy_clsf": thdy_bdy_clsf,
            "inq_cnt": inq_cnt,
            "srt_clsf": srt_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="거래대금 상위",
        api_code="IVU10210",
        endpoint="/api/v1/ivu10210",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10240(excg_clsf="", mkt_clsf="", inq_cnt="", srt_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10240 등락률 상위 — ATS통합-전일대비등락율상위
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        mkt_clsf: 시장구분 (선택) — 1:전체, 2:KOSPI, 3:KOSDAQ, 4:KOSPI200, 5:KOSDAQ150
        inq_cnt: 조회건수 (선택)
        srt_clsf: 정렬구분 (선택) — 1:상승율, 2:하락율, 3:상승폭, 4:하락폭
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "mkt_clsf": mkt_clsf,
            "inq_cnt": inq_cnt,
            "srt_clsf": srt_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="등락률 상위",
        api_code="IVU10240",
        endpoint="/api/v1/ivu10240",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10270(excg_clsf="", mkt_clsf="", inq_cnt="", up_dwn_ccd="", minute_dy_ccd="", minute_dy_unt="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10270 급등_급락 상위 — ATS통합-가격급등/급락종목
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        mkt_clsf: 시장구분 (선택) — 1:전체, 2:KOSPI, 3:KOSDAQ
        inq_cnt: 조회건수 (선택)
        up_dwn_ccd: 등락구분코드 (선택) — 1:급등, 2:급락
        minute_dy_ccd: MINUTE일구분코드 (선택) — 1:분전, 2:일전
        minute_dy_unt: MINUTE일단위 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "mkt_clsf": mkt_clsf,
            "inq_cnt": inq_cnt,
            "up_dwn_ccd": up_dwn_ccd,
            "minute_dy_ccd": minute_dy_ccd,
            "minute_dy_unt": minute_dy_unt,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="급등_급락 상위",
        api_code="IVU10270",
        endpoint="/api/v1/ivu10270",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10280(excg_clsf="", mkt_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10280 거래량 상위 — ATS통합-당일거래량상위
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        mkt_clsf: 시장구분 (선택) — 시장구분 : 1:전체, 2:KOSPI, 3:KOSDAQ
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "mkt_clsf": mkt_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="거래량 상위",
        api_code="IVU10280",
        endpoint="/api/v1/ivu10280",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ivu10550(excg_clsf="", mkt_clsf="", inq_cnt="", nw_stk_lw_ccd="", std_clsf="", prd_clsf="", excd_clsf="", *, extra: dict | None = None, token, host_url) -> dict:
    """IVU10550 신고_신저 — 신고가/신저가(IVU10550)
    
    Args:
        excg_clsf: 거래소구분 (선택) — 0:통합, 1:KRX, 2:NXT
        mkt_clsf: 시장구분 (선택) — 1:전체, 2:KOSPI, 3:KOSDAQ
        inq_cnt: 조회건수 (선택)
        nw_stk_lw_ccd: 신고저구분코드 (선택) — : 1:신고가, 2:신저가
        std_clsf: 기준구분 (선택) — 1:고저기준, 2:종가기준
        prd_clsf: 기간구분 (선택) — 1:전일 2:5일 3:10일 4:20일 5:60일 6:250일 7:120일
        excd_clsf: 돌파구분 (선택) — 1:일시돌파, 2:돌파유지
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_clsf": excg_clsf,
            "mkt_clsf": mkt_clsf,
            "inq_cnt": inq_cnt,
            "nw_stk_lw_ccd": nw_stk_lw_ccd,
            "std_clsf": std_clsf,
            "prd_clsf": prd_clsf,
            "excd_clsf": excd_clsf,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="신고_신저",
        api_code="IVU10550",
        endpoint="/api/v1/ivu10550",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

