# 자동 생성 파일 — 수동 수정 금지.
# manage/generate/generate_api_client.py 재실행으로 갱신하세요.

"""예약주문 (국내/미국)

포함 API: SPAO2104, SPAO2106, SPQO2105, SSAM0831, SSQM0831, SSQM0834
"""

from src.api.client import call_business_api


def spao2104(is_cd="", trd_dl_ccd="", ordr_typ_cd="", ordr_q="", frgn_ordr_prc_p4="", strt_tm="", end_tm="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPAO2104 주식예약주문미국 — 미국 주식에 대한 예약 주문을 접수합니다.정규 거래 시간 외에도 다음 거래일 시장 개장 시 자동으로 실행될 미국 주식 주문을 사전 접수합니다.
    
    Args:
        is_cd: 종목코드
        trd_dl_ccd: 매매거래구분코드 — 01:매도,02:매수
        ordr_typ_cd: 주문유형코드 — 1:시장가, 2:지정가, 3:VWAP시장가, 4:TWAP시장가
        ordr_q: 주문수량
        frgn_ordr_prc_p4: 해외주문가격P4
        strt_tm: 시작시간
        end_tm: 종료시간
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "trd_dl_ccd": trd_dl_ccd,
            "ordr_typ_cd": ordr_typ_cd,
            "ordr_q": ordr_q,
            "frgn_ordr_prc_p4": frgn_ordr_prc_p4,
            "strt_tm": strt_tm,
            "end_tm": end_tm,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="주식예약주문미국",
        api_code="SPAO2104",
        endpoint="/api/v1/spao2104",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spao2106(is_cd="", trd_clsf="", ordr_typ="", ordr_q="", frgn_ordr_prc_p4="", cncl_ordr_no="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPAO2106 예약주문취소미국 — 접수된 미국 주식 예약 주문을 취소합니다.아직 처리되지 않은 미국 주식 예약 주문을 취소 처리합니다.
    
    Args:
        is_cd: 종목코드
        trd_clsf: 매매구분
        ordr_typ: 주문유형
        ordr_q: 주문수량
        frgn_ordr_prc_p4: 해외주문가격P4
        cncl_ordr_no: 취소주문번호
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "trd_clsf": trd_clsf,
            "ordr_typ": ordr_typ,
            "ordr_q": ordr_q,
            "frgn_ordr_prc_p4": frgn_ordr_prc_p4,
            "cncl_ordr_no": cncl_ordr_no,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="예약주문취소미국",
        api_code="SPAO2106",
        endpoint="/api/v1/spao2106",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqo2105(rsrv_dt="", stnd_is_cd="", trd_clsf="", krw_unty_mgn_rqst_f="", cn_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPQO2105 예약주문조회 — 해외주식 예약주문조회
    
    Args:
        rsrv_dt: 예약일자
        stnd_is_cd: 표준종목코드
        trd_clsf: 매매구분 — 1:시장가,3:지정가
        krw_unty_mgn_rqst_f: 원화통합증거금신청여부 — 0: 외화, 1: 원화
        cn_key: 연속키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "rsrv_dt": rsrv_dt,
            "stnd_is_cd": stnd_is_cd,
            "trd_clsf": trd_clsf,
            "krw_unty_mgn_rqst_f": krw_unty_mgn_rqst_f,
            "cn_key": cn_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="예약주문조회",
        api_code="SPQO2105",
        endpoint="/api/v1/spqo2105",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssam0831(ordr_jb_clsf="", is_cd="", ordr_uprc="", ordr_q="", ordr_ccd="", strt_dt="", end_dt="", mkt_tm_ccd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM0831 예약주문접수 — 
    
    Args:
        ordr_jb_clsf: 주문업무구분 — 1:매도,2:매수
        is_cd: 종목코드
        ordr_uprc: 주문단가
        ordr_q: 주문수량
        ordr_ccd: 주문구분코드 — 00:지정가,03:시장가,12:최유리지정가,13:최우선지정가
        strt_dt: 시작일자
        end_dt: 종료일자
        mkt_tm_ccd: 시장시간구분코드
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "ordr_jb_clsf": ordr_jb_clsf,
            "is_cd": is_cd,
            "ordr_uprc": ordr_uprc,
            "ordr_q": ordr_q,
            "ordr_ccd": ordr_ccd,
            "strt_dt": strt_dt,
            "end_dt": end_dt,
            "mkt_tm_ccd": mkt_tm_ccd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="예약주문접수",
        api_code="SSAM0831",
        endpoint="/api/v1/ssam0831",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm0831(ordr_dt="", nxt_key="", trd_clsf="", hndl_clsf="", tv_rv_ccd="", end_dt="", is_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM0831 예약주문처리 조회 — 
    
    Args:
        ordr_dt: 주문일자
        nxt_key: 다음키
        trd_clsf: 매매구분 — 0:전체,1:매도,2:매수
        hndl_clsf: 처리구분 — 0:전체,S:완료,R:접수,E:거부
        tv_rv_ccd: 전량잔량구분코드 — 0:전체,N:일반,T:기간
        end_dt: 종료일자
        is_cd: 종목코드
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "ordr_dt": ordr_dt,
            "nxt_key": nxt_key,
            "trd_clsf": trd_clsf,
            "hndl_clsf": hndl_clsf,
            "tv_rv_ccd": tv_rv_ccd,
            "end_dt": end_dt,
            "is_cd": is_cd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="예약주문처리 조회",
        api_code="SSQM0831",
        endpoint="/api/v1/ssqm0831",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm0834(nxt_key="", strt_dt="", end_dt="", is_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM0834 예약주문접수 조회 — 접수된 예약 주문 내역을 조회합니다.정규 시장 시간 외에 접수한 예약 주문의 종목, 수량, 단가 등 상세 내역을 확인할 수 있습니다.
    
    Args:
        nxt_key: 다음키
        strt_dt: 시작일자
        end_dt: 종료일자
        is_cd: 종목코드
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "nxt_key": nxt_key,
            "strt_dt": strt_dt,
            "end_dt": end_dt,
            "is_cd": is_cd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="예약주문접수 조회",
        api_code="SSQM0834",
        endpoint="/api/v1/ssqm0834",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

