# 자동 생성 파일 — 수동 수정 금지.
# docs/api/generate_api_client.py 재실행으로 갱신하세요.

"""국내 주식 매매주문 (매도/매수/정정/취소, 소수점 포함)

포함 API: SKAM2101, SKAM2102, SKAM2201, SKAM2202, SSAM1801, SSAM1802, SSAM1805, SSAM1806, SSAM5762, SSAM5763, SSAM5764
"""

from src.api.client import call_business_api


def skam2101(trd_dl_ccd, is_cd, frgn_ordr_typ_cd, frgn_ordr_q, frgn_ordr_prc_p4, *, extra: dict | None = None, token, host_url) -> dict:
    """SKAM2101 매도_매수주문 — 해외주식 매도 또는 매수 주문을 접수합니다.미국, 홍콩, 일본 등 글로벌원마켓 지원 거래소의 주식을 시장가 또는 지정가로 주문할 수 있습니다.
    
    Args:
        trd_dl_ccd: 매매거래구분코드 (필수) — 01:매도, 02:매수
        is_cd: 종목코드 (필수) — ex)TSLA
        frgn_ordr_typ_cd: 해외주문유형코드 (필수) — 1:시장가, 2:지정가, 3:VWAP시장가, 4:TWAP시장가
        frgn_ordr_q: 해외주문수량 (필수)
        frgn_ordr_prc_p4: 해외주문가격P4 (필수)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "trd_dl_ccd": trd_dl_ccd,
            "is_cd": is_cd,
            "frgn_ordr_typ_cd": frgn_ordr_typ_cd,
            "frgn_ordr_q": frgn_ordr_q,
            "frgn_ordr_prc_p4": frgn_ordr_prc_p4,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매도_매수주문",
        api_code="SKAM2101",
        endpoint="/api/v1/skam2101",
        data_body=data_body,
        required=["trd_dl_ccd", "is_cd", "frgn_ordr_typ_cd", "frgn_ordr_q", "frgn_ordr_prc_p4"],
        token=token,
        host_url=host_url,
    )


def skam2102(crct_cncl_clsf, is_cd, orgn_ordr_no, frgn_ordr_prc_p4, *, extra: dict | None = None, token, host_url) -> dict:
    """SKAM2102 정정_취소주문 — 접수된 해외주식 주문을 정정하거나 취소합니다.미체결 상태의 해외주식 주문에 대해 수량·가격 정정 또는 주문 취소를 요청할 수 있습니다.
    
    Args:
        crct_cncl_clsf: 정정취소구분 (필수) — 1:정정, 2:취소
        is_cd: 종목코드 (필수)
        orgn_ordr_no: 원주문번호 (필수)
        frgn_ordr_prc_p4: 해외주문가격P4 (필수)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "crct_cncl_clsf": crct_cncl_clsf,
            "is_cd": is_cd,
            "orgn_ordr_no": orgn_ordr_no,
            "frgn_ordr_prc_p4": frgn_ordr_prc_p4,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="정정_취소주문",
        api_code="SKAM2102",
        endpoint="/api/v1/skam2102",
        data_body=data_body,
        required=["crct_cncl_clsf", "is_cd", "orgn_ordr_no", "frgn_ordr_prc_p4"],
        token=token,
        host_url=host_url,
    )


def skam2201(trd_dl_ccd, is_cd, amt_q_clsf, frgn_ordr_typ_cd, ordr_amt, tv_s_est_f="", crncy_ccd="", dcml_ordr_q_p6="", frgn_ordr_prc_p4="", *, extra: dict | None = None, token, host_url) -> dict:
    """SKAM2201 소수점매도_매수주문 — 해외주식 소수점 단위 매도 또는 매수 주문을 접수합니다.1주 미만의 소수점 단위로 해외주식을 거래할 수 있어 소액으로도 해외 우량주에 투자할 수 있습니다.
    
    Args:
        trd_dl_ccd: 매매거래구분코드 (필수) — 01-매도, 02-매수
        is_cd: 종목코드 (필수)
        amt_q_clsf: 금액수량구분 (필수) — 0-금액, 1-수량
        frgn_ordr_typ_cd: 해외주문유형코드 (필수) — 2-지정가, E-유사시장가
        ordr_amt: 주문금액 (필수)
        tv_s_est_f: 전량매도설정여부 (선택) — 0-일부매도, 1-전량매도
        crncy_ccd: 통화구분코드 (선택) — 0-원화, 1-외화(USD)
        dcml_ordr_q_p6: 소수점주문수량P6 (선택)
        frgn_ordr_prc_p4: 해외주문가격P4 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "trd_dl_ccd": trd_dl_ccd,
            "is_cd": is_cd,
            "amt_q_clsf": amt_q_clsf,
            "frgn_ordr_typ_cd": frgn_ordr_typ_cd,
            "ordr_amt": ordr_amt,
            "tv_s_est_f": tv_s_est_f,
            "crncy_ccd": crncy_ccd,
            "dcml_ordr_q_p6": dcml_ordr_q_p6,
            "frgn_ordr_prc_p4": frgn_ordr_prc_p4,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="소수점매도_매수주문",
        api_code="SKAM2201",
        endpoint="/api/v1/skam2201",
        data_body=data_body,
        required=["trd_dl_ccd", "is_cd", "amt_q_clsf", "frgn_ordr_typ_cd", "ordr_amt"],
        token=token,
        host_url=host_url,
    )


def skam2202(orgn_ordr_no, *, extra: dict | None = None, token, host_url) -> dict:
    """SKAM2202 소수점취소주문 — 접수된 해외주식 소수점 주문을 취소합니다.미체결 상태의 해외주식 소수점 매수·매도 주문의 수량·가격을 변경하거나 취소할 수 있습니다.
    
    Args:
        orgn_ordr_no: 원주문번호 (필수)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "orgn_ordr_no": orgn_ordr_no,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="소수점취소주문",
        api_code="SKAM2202",
        endpoint="/api/v1/skam2202",
        data_body=data_body,
        required=["orgn_ordr_no"],
        token=token,
        host_url=host_url,
    )


def ssam1801(mkt_tm_clsf, is_cd, ordr_q, ordr_uprc, ordr_ccd, sor_ordr_ccd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM1801 매도주문 — 국내주식 현금 매도 주문을 접수합니다.시장가, 지정가 등 다양한 주문 유형을 지원하며, 보유 주식의 전부 또는 일부를 매도할 수 있습니다.
    
    Args:
        mkt_tm_clsf: 시장시간구분 (필수) — 1:정규장,2:장개시전시간외종가,3:장종료후시간외종가,4:장종료후시간외단일가
        is_cd: 종목코드 (필수)
        ordr_q: 주문수량 (필수)
        ordr_uprc: 주문단가 (필수)
        ordr_ccd: 주문구분코드 (필수) — 00:지정가,03:시장가,12:최유리지정가,13:최우선지정가,M3:중간가
        sor_ordr_ccd: SOR주문구분코드 (선택) — K:KRX,N:NXT,S:SOR
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "mkt_tm_clsf": mkt_tm_clsf,
            "is_cd": is_cd,
            "ordr_q": ordr_q,
            "ordr_uprc": ordr_uprc,
            "ordr_ccd": ordr_ccd,
            "sor_ordr_ccd": sor_ordr_ccd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매도주문",
        api_code="SSAM1801",
        endpoint="/api/v1/ssam1801",
        data_body=data_body,
        required=["mkt_tm_clsf", "is_cd", "ordr_q", "ordr_uprc", "ordr_ccd"],
        token=token,
        host_url=host_url,
    )


def ssam1802(mkt_tm_clsf, is_cd, ordr_q, ordr_uprc, ordr_ccd, sor_ordr_ccd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM1802 매수주문 — 국내주식 현금 매수 주문을 접수합니다.시장가, 지정가 등 다양한 주문 유형을 지원합니다. 스톱지정가 주문 시 ordr_ccd 값을 확인하세요.
    
    Args:
        mkt_tm_clsf: 시장시간구분 (필수) — 1:정규장,2:장개시전시간외종가,3:장종료후시간외종가,4:장종료후시간외단일가
        is_cd: 종목코드 (필수)
        ordr_q: 주문수량 (필수)
        ordr_uprc: 주문단가 (필수)
        ordr_ccd: 주문구분코드 (필수) — 00:지정가,03:시장가,12:최유리지정가,13:최우선지정가, M3:중간가
        sor_ordr_ccd: SOR주문구분코드 (선택) — K:KRX,N:NXT,S:SOR
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "mkt_tm_clsf": mkt_tm_clsf,
            "is_cd": is_cd,
            "ordr_q": ordr_q,
            "ordr_uprc": ordr_uprc,
            "ordr_ccd": ordr_ccd,
            "sor_ordr_ccd": sor_ordr_ccd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매수주문",
        api_code="SSAM1802",
        endpoint="/api/v1/ssam1802",
        data_body=data_body,
        required=["mkt_tm_clsf", "is_cd", "ordr_q", "ordr_uprc", "ordr_ccd"],
        token=token,
        host_url=host_url,
    )


def ssam1805(mkt_tm_clsf, is_cd, ordr_q, ordr_uprc, ordr_ccd, crct_clsf, orgn_ordr_no, sor_ordr_ccd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM1805 정정주문 — 미체결 상태의 국내주식 주문을 정정합니다.원주문번호와 정정할 수량·가격을 입력하여 미체결 주문의 내용을 변경할 수 있습니다.
    
    Args:
        mkt_tm_clsf: 시장시간구분 (필수) — 1:정규장,2:장개시전시간외종가,3:장종료후시간외종가,4:장종료후시간외단일가
        is_cd: 종목코드 (필수)
        ordr_q: 주문수량 (필수) — *일부정정시 입력
        ordr_uprc: 주문단가 (필수)
        ordr_ccd: 주문구분코드 (필수) — 00:지정가,03:시장가,05:조건부지정가,12:최유리지정가,13:최우선지정가
        crct_clsf: 정정구분 (필수) — 1:일부정정,2:전부정정
        orgn_ordr_no: 원주문번호 (필수)
        sor_ordr_ccd: SOR주문구분코드 (선택) — K:KRX,N:NXT,S:SOR
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "mkt_tm_clsf": mkt_tm_clsf,
            "is_cd": is_cd,
            "ordr_q": ordr_q,
            "ordr_uprc": ordr_uprc,
            "ordr_ccd": ordr_ccd,
            "crct_clsf": crct_clsf,
            "orgn_ordr_no": orgn_ordr_no,
            "sor_ordr_ccd": sor_ordr_ccd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="정정주문",
        api_code="SSAM1805",
        endpoint="/api/v1/ssam1805",
        data_body=data_body,
        required=["mkt_tm_clsf", "is_cd", "ordr_q", "ordr_uprc", "ordr_ccd", "crct_clsf", "orgn_ordr_no"],
        token=token,
        host_url=host_url,
    )


def ssam1806(is_cd, crct_clsf, orgn_ordr_no, ordr_q="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM1806 취소주문 — 
    
    Args:
        is_cd: 종목코드 (필수)
        crct_clsf: 정정구분 (필수) — 1:일부정정,2:전부정정
        orgn_ordr_no: 원주문번호 (필수)
        ordr_q: 주문수량 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "crct_clsf": crct_clsf,
            "orgn_ordr_no": orgn_ordr_no,
            "ordr_q": ordr_q,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="취소주문",
        api_code="SSAM1806",
        endpoint="/api/v1/ssam1806",
        data_body=data_body,
        required=["is_cd", "crct_clsf", "orgn_ordr_no"],
        token=token,
        host_url=host_url,
    )


def ssam5762(is_cd, ordr_amt, dcml_ordr_std_ccd, tv_s_est_f, ordr_q_p6="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM5762 소수점 매도주문 — 국내주식 소수점 단위 매도 주문을 접수합니다.1주 미만의 소수점 단위로 보유한 주식을 매도할 수 있습니다.
    
    Args:
        is_cd: 종목코드 (필수)
        ordr_amt: 주문금액 (필수)
        dcml_ordr_std_ccd: 소수점주문기준구분코드 (필수) — 1:금액, 2:수량 (전량일때 2번으로)
        tv_s_est_f: 전량매도설정여부 (필수) — 0:일부매도, 1:전량매도
        ordr_q_p6: 주문수량P6 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "ordr_amt": ordr_amt,
            "dcml_ordr_std_ccd": dcml_ordr_std_ccd,
            "tv_s_est_f": tv_s_est_f,
            "ordr_q_p6": ordr_q_p6,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="소수점 매도주문",
        api_code="SSAM5762",
        endpoint="/api/v1/ssam5762",
        data_body=data_body,
        required=["is_cd", "ordr_amt", "dcml_ordr_std_ccd", "tv_s_est_f"],
        token=token,
        host_url=host_url,
    )


def ssam5763(is_cd, ordr_amt, dcml_ordr_std_ccd, ordr_q_p6="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM5763 소수점 매수주문 — 
    
    Args:
        is_cd: 종목코드 (필수)
        ordr_amt: 주문금액 (필수)
        dcml_ordr_std_ccd: 소수점주문기준구분코드 (필수) — 1:금액,2:수량
        ordr_q_p6: 주문수량P6 (선택)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "ordr_amt": ordr_amt,
            "dcml_ordr_std_ccd": dcml_ordr_std_ccd,
            "ordr_q_p6": ordr_q_p6,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="소수점 매수주문",
        api_code="SSAM5763",
        endpoint="/api/v1/ssam5763",
        data_body=data_body,
        required=["is_cd", "ordr_amt", "dcml_ordr_std_ccd"],
        token=token,
        host_url=host_url,
    )


def ssam5764(dmstc_stk_dcml_trd_jb_ccd, ordr_sqc, ordr_dt, bnf_is_cd, trd_dl_ccd, dmstc_stk_dcml_ordr_sq, *, extra: dict | None = None, token, host_url) -> dict:
    """SSAM5764 소수점 주문취소 — 
    
    Args:
        dmstc_stk_dcml_trd_jb_ccd: 국내주식소수점매매업무구분코드 (필수) — 01:일반,02:자기,03:정기매수,04:비상장분할 일괄청산,05:정리매매 일괄청산
        ordr_sqc: 주문회차 (필수)
        ordr_dt: 주문일자 (필수)
        bnf_is_cd: 수익증권종목코드 (필수)
        trd_dl_ccd: 매매거래구분코드 (필수) — 01:매도, 02:매수
        dmstc_stk_dcml_ordr_sq: 국내주식소수점주문일련번호 (필수) — SSQM5765 api 의 acpt_no 값
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "dmstc_stk_dcml_trd_jb_ccd": dmstc_stk_dcml_trd_jb_ccd,
            "ordr_sqc": ordr_sqc,
            "ordr_dt": ordr_dt,
            "bnf_is_cd": bnf_is_cd,
            "trd_dl_ccd": trd_dl_ccd,
            "dmstc_stk_dcml_ordr_sq": dmstc_stk_dcml_ordr_sq,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="소수점 주문취소",
        api_code="SSAM5764",
        endpoint="/api/v1/ssam5764",
        data_body=data_body,
        required=["dmstc_stk_dcml_trd_jb_ccd", "ordr_sqc", "ordr_dt", "bnf_is_cd", "trd_dl_ccd", "dmstc_stk_dcml_ordr_sq"],
        token=token,
        host_url=host_url,
    )

