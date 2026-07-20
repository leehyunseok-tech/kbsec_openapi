# 자동 생성 파일 — 수동 수정 금지.
# manage/generate/generate_api_client.py 재실행으로 갱신하세요.

"""계좌/잔고/손익/증거금/예수금 조회

포함 API: SKQM2106, SKQM3350, SPQM2103, SPQM2204, SPQM2205, SPQM2206, SPQM2207, SPQM2226, SPQM3390, SPQN5472, SRQM3051, SSQM0004, SSQM1801, SSQM1802, SSQM2121, SSQM2341, SSQM2392, SSQM2442, SSQM2932, SSQM2952, SSQM5765
"""

from src.api.client import call_business_api


def skqm2106(stnd_is_cd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SKQM2106 주문가능금액조회 — 해외주식 글로벌원마켓 서비스에서 통화별 주문 가능 금액을 조회합니다.해외주식 매수 주문 전 통화별로 사용 가능한 주문 가능 금액을 확인할 수 있습니다.
    
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
        api_name="주문가능금액조회",
        api_code="SKQM2106",
        endpoint="/api/v1/skqm2106",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def skqm3350(*, extra: dict | None = None, token, host_url) -> dict:
    """SKQM3350 주문가능금액현황조회 — 해외주식 글로벌원마켓 서비스에서 통화별 주문 가능 예수금 현황을 조회합니다.
    
    Args: (문서화된 요청 파라미터 없음)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="주문가능금액현황조회",
        api_code="SKQM3350",
        endpoint="/api/v1/skqm3350",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqm2103(ccls_clsf="", ordr_dt="", dl_clsf="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPQM2103 주문체결조회 — 해외주식 주문 체결 내역을 조회합니다.지정된 기간 내 체결된 해외주식 주문의 종목, 매매 구분, 수량, 단가, 수수료 등을 확인할 수 있습니다.
    
    Args:
        ccls_clsf: 체결구분 — 1:전체,2:체결,3:미체결
        ordr_dt: 주문일자
        dl_clsf: 거래구분 — 0.전체 1.일반 2.소수점
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "ccls_clsf": ccls_clsf,
            "ordr_dt": ordr_dt,
            "dl_clsf": dl_clsf,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="주문체결조회",
        api_code="SPQM2103",
        endpoint="/api/v1/spqm2103",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqm2204(strt_ordr_dt="", end_ordr_dt="", ccls_clsf="", trd_clsf="", stnd_is_cd="", dl_clsf="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPQM2204 체결미체결 조회 — 해외주식 주문 체결 현황을 조회합니다.당일 접수한 해외주식 주문의 체결 수량, 미체결 수량, 체결 단가 등 처리 상태를 확인할 수 있습니다.
    
    Args:
        strt_ordr_dt: 시작주문일자
        end_ordr_dt: 종료주문일자
        ccls_clsf: 체결구분 — 0: 전체, 1: 체결, 2: 미체결
        trd_clsf: 매매구분 — 99: 전체, 01: 매도, 02: 매수
        stnd_is_cd: 표준종목코드
        dl_clsf: 거래구분 — 0:전체 ,1:일반거래,2:소수점거래
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "strt_ordr_dt": strt_ordr_dt,
            "end_ordr_dt": end_ordr_dt,
            "ccls_clsf": ccls_clsf,
            "trd_clsf": trd_clsf,
            "stnd_is_cd": stnd_is_cd,
            "dl_clsf": dl_clsf,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="체결미체결 조회",
        api_code="SPQM2204",
        endpoint="/api/v1/spqm2204",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqm2205(strt_ordr_dt="", end_ordr_dt="", trd_clsf="", stnd_is_cd="", krw_unty_mgn_rqst_f="", dl_clsf="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPQM2205 매매정산 현황 — 해외주식 매매가 정산 현황을 조회합니다.체결된 해외주식 거래의 매매 단가 기준 정산 금액과 외화·원화 환산 내역을 확인할 수 있습니다.
    
    Args:
        strt_ordr_dt: 시작주문일자
        end_ordr_dt: 종료주문일자
        trd_clsf: 매매구분 — 99:전체, 01:매도, 02:매수
        stnd_is_cd: 표준종목코드
        krw_unty_mgn_rqst_f: 원화통합증거금신청여부 — 0: 외화기준, 1: 원화기준
        dl_clsf: 거래구분 — 0:전체, 1:일반거래, 2:소수점거래
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "strt_ordr_dt": strt_ordr_dt,
            "end_ordr_dt": end_ordr_dt,
            "trd_clsf": trd_clsf,
            "stnd_is_cd": stnd_is_cd,
            "krw_unty_mgn_rqst_f": krw_unty_mgn_rqst_f,
            "dl_clsf": dl_clsf,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매매정산 현황",
        api_code="SPQM2205",
        endpoint="/api/v1/spqm2205",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqm2206(ordr_dt="", stnd_is_cd="", std_crncy_f="", exch_r_aplc_f="", frgn_stk_mgn_ccd="", dl_clsf="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPQM2206 매매손익 당일 — 당일 해외주식 매매 손익을 조회합니다.오늘 체결된 해외주식 거래에 대한 실현 손익, 수수료, 제세금을 통화별로 확인할 수 있습니다.
    
    Args:
        ordr_dt: 주문일자
        stnd_is_cd: 표준종목코드
        std_crncy_f: 기준통화여부 — 1:외화기준,2:원화기준
        exch_r_aplc_f: 환율적용여부 — 1:환전시매도환율, 2:매매기준율
        frgn_stk_mgn_ccd: 해외주식증거금구분코드 — 1:원화, 2:외화
        dl_clsf: 거래구분 — 0:전체,1:일반거래,2:소수점거래
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "ordr_dt": ordr_dt,
            "stnd_is_cd": stnd_is_cd,
            "std_crncy_f": std_crncy_f,
            "exch_r_aplc_f": exch_r_aplc_f,
            "frgn_stk_mgn_ccd": frgn_stk_mgn_ccd,
            "dl_clsf": dl_clsf,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매매손익 당일",
        api_code="SPQM2206",
        endpoint="/api/v1/spqm2206",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqm2207(stnd_is_cd="", std_crncy_f="", exch_r_aplc_f="", frgn_stk_mgn_ccd="", dl_clsf="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPQM2207 매매손익 기간별 — 지정된 기간 동안의 해외주식 매매 손익을 조회합니다.기간 내 해외주식 거래의 실현 손익, 수수료, 세금을 종목별·통화별로 확인할 수 있습니다.
    
    Args:
        stnd_is_cd: 표준종목코드
        std_crncy_f: 기준통화여부 — 1:외화기준,2:원화기준
        exch_r_aplc_f: 환율적용여부 — 1:환전시매도환율, 2:매매기준율
        frgn_stk_mgn_ccd: 해외주식증거금구분코드 — 1:원화, 2:외화
        dl_clsf: 거래구분
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "stnd_is_cd": stnd_is_cd,
            "std_crncy_f": std_crncy_f,
            "exch_r_aplc_f": exch_r_aplc_f,
            "frgn_stk_mgn_ccd": frgn_stk_mgn_ccd,
            "dl_clsf": dl_clsf,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매매손익 기간별",
        api_code="SPQM2207",
        endpoint="/api/v1/spqm2207",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqm2226(std_crncy_f="", exch_r_aplc_f="", fee_clsf="", cn_f="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SPQM2226 해외주식계좌잔고평가조회 — 해외주식 계좌 잔고 평가를 조회합니다.보유 중인 해외주식의 종목별 수량, 평균 단가, 현재가, 평가금액 및 손익을 확인할 수 있습니다.
    
    Args:
        std_crncy_f: 기준통화여부 — 1: 외화기준, 2: 원화기준
        exch_r_aplc_f: 환율적용여부 — 1:환전시매도환율, 2: 매매기준환율(원화)
        fee_clsf: 수수료구분 — 0: 포함, 1: 미포함
        cn_f: 연속여부
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "std_crncy_f": std_crncy_f,
            "exch_r_aplc_f": exch_r_aplc_f,
            "fee_clsf": fee_clsf,
            "cn_f": cn_f,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="해외주식계좌잔고평가조회",
        api_code="SPQM2226",
        endpoint="/api/v1/spqm2226",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqm3390(*, extra: dict | None = None, token, host_url) -> dict:
    """SPQM3390 계좌증거금조회 — 글로벌원마켓(통합증거금) 서비스에 가입된 계좌의 증거금 사용 현황을 조회합니다.
    
    Args: (문서화된 요청 파라미터 없음)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="계좌증거금조회",
        api_code="SPQM3390",
        endpoint="/api/v1/spqm3390",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def spqn5472(*, extra: dict | None = None, token, host_url) -> dict:
    """SPQN5472 소수점주문가능금액조회 — 해외주식 소수점 매매 시 주문 가능 금액을 조회합니다.소수점 단위로 매수하려는 해외주식 종목과 금액을 입력하면 주문 가능 여부를 확인할 수 있습니다.
    
    Args: (문서화된 요청 파라미터 없음)
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="소수점주문가능금액조회",
        api_code="SPQN5472",
        endpoint="/api/v1/spqn5472",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def srqm3051(strt_dt="", rgt_clsf="", is_cd="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SRQM3051 계좌권리 발생내역 — 계좌에서 발생한 권리 내역을 조회합니다.배당금 지급, 주식 배당, 무상증자 등 보유 종목에서 발생한 권리 행사 내역을 확인할 수 있습니다.
    
    Args:
        strt_dt: 시작일자
        rgt_clsf: 권리구분 — 0:전체, 1:배당, 2:유상증자/BW권리행사, 3:무상증자, 4:매수청구, 5:감자, 6:액면분할/액면병합, 7:피흡수합병
        is_cd: 종목코드
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "strt_dt": strt_dt,
            "rgt_clsf": rgt_clsf,
            "is_cd": is_cd,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="계좌권리 발생내역",
        api_code="SRQM3051",
        endpoint="/api/v1/srqm3051",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm0004(is_no="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM0004 예수금내역 — 
    
    Args:
        is_no: 종목번호
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_no": is_no,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="예수금내역",
        api_code="SSQM0004",
        endpoint="/api/v1/ssqm0004",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm1801(inq_clsf="", is_no="", mkt_tm_ccd="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM1801 보유주식 조회 — 계좌에서 보유 중인 주식 목록과 상세 정보를 조회합니다.
    
    Args:
        inq_clsf: 조회구분 — 0:현금주식매도,1:현금주식예약,2:현금주식일괄매도,3:ELW+현금,4:장외단주매도,5:ELW 전용,6:현금주식매도+코넥스+ETN,7:코넥스전용,8:ETN 전용,9:ELW+현금+ETN
        is_no: 종목번호
        mkt_tm_ccd: 시장시간구분코드 — 1:정규시장,2:장개시전시간외,3:장종료후시간외,4:시간외단일가
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "inq_clsf": inq_clsf,
            "is_no": is_no,
            "mkt_tm_ccd": mkt_tm_ccd,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="보유주식 조회",
        api_code="SSQM1801",
        endpoint="/api/v1/ssqm1801",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm1802(is_no="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM1802 매수주문가능금액 — 특정 종목에 대해 현재 계좌에서 매수 가능한 금액과 수량을 조회합니다.
    
    Args:
        is_no: 종목번호
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_no": is_no,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매수주문가능금액",
        api_code="SSQM1802",
        endpoint="/api/v1/ssqm1802",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm2121(trd_dt="", clsf="", stmt_dt="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM2121 매매정산현황 — 
    
    Args:
        trd_dt: 매매일자
        clsf: 구분 — 1: 단가별, 2: 종목별
        stmt_dt: 결제일자
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "trd_dt": trd_dt,
            "clsf": clsf,
            "stmt_dt": stmt_dt,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매매정산현황",
        api_code="SSQM2121",
        endpoint="/api/v1/ssqm2121",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm2341(ccls_clsf="", ordr_dt="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM2341 체결미체결 조회 — 계좌별 주문 체결 내역을 조회합니다.지정된 기간 내 체결된 주문의 종목, 매매 구분, 체결 수량, 단가, 수수료 등을 확인할 수 있습니다.
    
    Args:
        ccls_clsf: 체결구분 — 0:전체, 1:체결, 2:미체결
        ordr_dt: 주문일자
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "ccls_clsf": ccls_clsf,
            "ordr_dt": ordr_dt,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="체결미체결 조회",
        api_code="SSQM2341",
        endpoint="/api/v1/ssqm2341",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm2392(is_no="", ordr_dt_from="", ordr_dt_to="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM2392 매매손익현황 — 
    
    Args:
        is_no: 종목번호
        ordr_dt_from: 주문일자FROM
        ordr_dt_to: 주문일자TO
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_no": is_no,
            "ordr_dt_from": ordr_dt_from,
            "ordr_dt_to": ordr_dt_to,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="매매손익현황",
        api_code="SSQM2392",
        endpoint="/api/v1/ssqm2392",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm2442(is_cd="", inq_strt_dt="", inq_end_dt="", md_clsf="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM2442 실현손익현황 — 
    
    Args:
        is_cd: 종목코드
        inq_strt_dt: 조회시작일자
        inq_end_dt: 조회종료일자
        md_clsf: 매체구분 — 1:오프라인 2:온라인 3:지점
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "is_cd": is_cd,
            "inq_strt_dt": inq_strt_dt,
            "inq_end_dt": inq_end_dt,
            "md_clsf": md_clsf,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="실현손익현황",
        api_code="SSQM2442",
        endpoint="/api/v1/ssqm2442",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm2932(inq_clsf="", excg_mktpr_ccd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM2932 잔고현황 조회(결제기준) — 종합위탁계좌 및 신연금저축계좌의 잔고 현황을 조회합니다.계좌 유형별 보유 자산 및 평가 금액을 한눈에 확인할 수 있습니다.
    
    Args:
        inq_clsf: 조회구분 — 1:계좌별, 2:상품유형별 (자문/일임)
        excg_mktpr_ccd: 거래소시세구분코드 — A:통합시세,K:KRX시세,N:NXT시세
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "inq_clsf": inq_clsf,
            "excg_mktpr_ccd": excg_mktpr_ccd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="잔고현황 조회(결제기준)",
        api_code="SSQM2932",
        endpoint="/api/v1/ssqm2932",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm2952(excg_mktpr_ccd="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM2952 잔고현황 조회(체결기준) — 
    
    Args:
        excg_mktpr_ccd: 거래소시세구분코드 — A:통합시세, K:KRX시세, N:NXT시세
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "excg_mktpr_ccd": excg_mktpr_ccd,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="잔고현황 조회(체결기준)",
        api_code="SSQM2952",
        endpoint="/api/v1/ssqm2952",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def ssqm5765(trd_clsf="", trd_strt_dt="", trd_end_dt="", is_cd="", nxt_key="", *, extra: dict | None = None, token, host_url) -> dict:
    """SSQM5765 소수점매매 조회 — 국내주식 소수점 매매 전체 내역을 조회합니다.소수점 단위로 매수·매도한 거래 내역, 수량, 금액, 손익을 기간별로 확인할 수 있습니다.
    
    Args:
        trd_clsf: 매매구분 — 0: 전체, 1:매도, 2:매수
        trd_strt_dt: 매매시작일자
        trd_end_dt: 매매종료일자 — * 당일자 조회시에는 빈값
        is_cd: 종목코드
        nxt_key: 다음키
        extra: INPUT 표에 없는 추가 dataBody 필드
        token, host_url: 인증 토큰 및 호스트 URL
    """
    data_body = {
            "trd_clsf": trd_clsf,
            "trd_strt_dt": trd_strt_dt,
            "trd_end_dt": trd_end_dt,
            "is_cd": is_cd,
            "nxt_key": nxt_key,
        }
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="소수점매매 조회",
        api_code="SSQM5765",
        endpoint="/api/v1/ssqm5765",
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )

