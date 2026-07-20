"""
mst 명령 처리 - 종목마스터 현황 조회.

mst/api/openapi_field_*.mst 파일이 이미 로컬에 있으므로 API 호출이나 파일 생성 없이
로드 현황만 보고한다.
"""

from src.utils.stock_master import load_all


def handle_mst(args, session):
    """mst 명령 처리 - 종목마스터 로드 현황 조회 (API 호출 불필요)"""
    kospi, kosdaq, overseas = load_all()
    return f"""📋 종목마스터 (로컬 파일 기반, API 호출 없음)

코스피: {len(kospi):,}종목
코스닥: {len(kosdaq):,}종목
해외주식: {len(overseas):,}종목

종목명 검색: /종목검색 {{키워드}}
파일 위치: mst/api/"""
