"""
슬래시 명령어 메타데이터 단일 소스.

한글 기본 명령어의 (이름/사용법/설명/분류/영문별칭)을 한곳에 모아둔다.
  - 웹 "명령 실행" 입력칸의 "/" 자동완성 드롭다운이 GET /api/commands 로 이 목록을
    받아 접두어 매칭에 사용한다(src/web/app.py, src/web/static/js/app.js).
  - 명령어 한글화 체계(한글 기본 + 영문 숨김 별칭)의 참조표 역할도 한다.

명령어를 추가/변경할 때는 CLAUDE.md 필수 규칙과 함께 이 표도 갱신한다.
저수준 개발자 도구(/api /call /info /list)와 login 은 영문 예외라 여기 포함하지 않는다.
74개 자동생성 API 커맨드(/{코드}-{API명})도 코드 기반이라 포함하지 않는다.
"""

# 각 항목: name(한글 기본 명령), aliases(영문 별칭들), usage, desc, category
COMMANDS_META = [
    # ── 인증/상태 ──
    {"name": "상태", "aliases": ["status"], "usage": "/상태", "desc": "로그인 상태·토큰 남은 시간 확인", "category": "인증/상태"},

    # ── 조회 ──
    {"name": "종목정보", "aliases": ["srch"], "usage": "/종목정보 {종목코드}", "desc": "종목 현재가·기본정보 (국내/미국)", "category": "조회"},
    {"name": "순위", "aliases": ["rank"], "usage": "/순위 [1~4]", "desc": "거래대금·등락률·거래량·업종 상위", "category": "조회"},
    {"name": "잔고", "aliases": ["report", "r"], "usage": "/잔고", "desc": "보유종목 + 미체결 주문 조회", "category": "조회"},
    {"name": "종목마스터", "aliases": ["mst"], "usage": "/종목마스터", "desc": "종목마스터(로컬 파일) 로드 현황", "category": "조회"},
    {"name": "종목검색", "aliases": ["stcd"], "usage": "/종목검색 {키워드}", "desc": "종목명/코드 키워드 검색", "category": "조회"},
    {"name": "투자자", "aliases": ["investor"], "usage": "/투자자 {종목코드} {개월수}", "desc": "투자자별 누적 순매수 차트 (국내)", "category": "조회"},

    # ── 매매 ──
    {"name": "매수", "aliases": ["buy"], "usage": "/매수 {종목코드} {수량}", "desc": "종목 매수 (국내/미국)", "category": "매매"},
    {"name": "매도", "aliases": ["sell"], "usage": "/매도 {종목코드} [{수량}]", "desc": "종목 매도 (국내/미국)", "category": "매매"},
    {"name": "취소", "aliases": ["ccl"], "usage": "/취소 pend", "desc": "미체결 주문 전체 취소", "category": "매매"},

    # ── 설정 ──
    {"name": "장시간", "aliases": ["mkhr"], "usage": "/장시간 [{시작} {종료}]", "desc": "장 시간 조회/설정", "category": "설정"},
    {"name": "익절", "aliases": [], "usage": "/익절 [{퍼센티지}]", "desc": "익절 기준 조회/설정", "category": "설정"},
    {"name": "손절", "aliases": [], "usage": "/손절 [{퍼센티지}]", "desc": "손절 기준 조회/설정", "category": "설정"},
    {"name": "타임아웃", "aliases": ["time"], "usage": "/타임아웃 {초} cancel|market", "desc": "미체결 주문 타임아웃", "category": "설정"},
    {"name": "쿨다운", "aliases": ["cooldown"], "usage": "/쿨다운 {시간}", "desc": "매도 후 재매수 금지 시간", "category": "설정"},
    {"name": "금지종목", "aliases": ["blacklist"], "usage": "/금지종목 add|list|remove", "desc": "매매 금지 종목 관리", "category": "설정"},
    {"name": "최대보유", "aliases": ["mxhold"], "usage": "/최대보유 {개수}", "desc": "최대 보유 종목 수", "category": "설정"},
    {"name": "설정", "aliases": ["stts"], "usage": "/설정", "desc": "전체 설정값 한 번에 조회", "category": "설정"},

    # ── 예약/기록 ──
    {"name": "예약", "aliases": ["rsv"], "usage": "/예약 {시간} {명령어}", "desc": "명령 예약 (매일/1회/목록/삭제)", "category": "예약/기록"},
    {"name": "체결기록", "aliases": ["log"], "usage": "/체결기록 [{일수}]", "desc": "체결 내역 CSV 전송", "category": "예약/기록"},
    {"name": "분석", "aliases": ["anss"], "usage": "/분석 [{일수}]", "desc": "체결 내역 AI 분석 (Claude)", "category": "예약/기록"},

    # ── 자동매매 ──
    {"name": "골든크로스", "aliases": ["gdcrs"], "usage": "/골든크로스 add|list|remove|intv|clear", "desc": "골든크로스 자동매수 설정", "category": "자동매매"},
    {"name": "데드크로스", "aliases": ["ddcrs"], "usage": "/데드크로스", "desc": "데드크로스 자동매도 (골든크로스 분봉 공유)", "category": "자동매매"},
    {"name": "트레일링", "aliases": ["trst"], "usage": "/트레일링 [{하락율} {최소수익률}]", "desc": "트레일링 스탑 설정", "category": "자동매매"},
    {"name": "돌파매수", "aliases": ["brk"], "usage": "/돌파매수 rate|add|list|remove", "desc": "돌파매수 감시 설정", "category": "자동매매"},
    {"name": "분할매매", "aliases": ["wave"], "usage": "/분할매매 set|view|add|list|remove", "desc": "분할매매 설정", "category": "자동매매"},
    {"name": "그리드", "aliases": ["grid"], "usage": "/그리드 add|list|remove", "desc": "그리드 트레이딩 설정", "category": "자동매매"},
    {"name": "감시시작", "aliases": ["start"], "usage": "/감시시작 {전략}", "desc": "자동매매 감시 시작", "category": "자동매매"},
    {"name": "감시중단", "aliases": ["stop"], "usage": "/감시중단 {전략}", "desc": "자동매매 감시 중단", "category": "자동매매"},

    # ── 기타 ──
    {"name": "도움말", "aliases": ["help"], "usage": "/도움말", "desc": "전체 명령어 도움말", "category": "기타"},
    {"name": "종료", "aliases": ["power"], "usage": "/종료", "desc": "Agent 프로세스 종료 (터미널/텔레그램)", "category": "기타"},
]

# /감시시작 · /감시중단 사용법 안내에 쓰는 한글 전략명 표시 문자열
AUTOTRADE_FEATURES_KR = "골든크로스, 데드크로스, 트레일링, 돌파매수, 분할매매, 그리드, 손절매, 보유감시"

# 자동매매 전략명: 한글 인자 → 내부 키. /감시시작 골든크로스 = /start gdcrs
AUTOTRADE_FEATURE_ALIASES = {
    "골든크로스": "gdcrs",
    "데드크로스": "ddcrs",
    "트레일링": "trst",
    "돌파매수": "brk",
    "분할매매": "wave",
    "그리드": "grid",
    "손절매": "stls",
    "자동손절": "stls",
    "보유감시": "hold",
    "보유": "hold",
}


def command_aliases() -> dict:
    """한글 기본 명령 → 별칭 목록. (문서/참조용)"""
    return {c["name"]: c["aliases"] for c in COMMANDS_META}


def korean_command_map(commands: dict) -> dict:
    """영문 키가 이미 등록된 commands 딕셔너리를 받아, {한글이름: 같은 핸들러} 매핑을 반환한다.

    각 클라이언트(main/terminal/web)가 `self.commands`를 만든 뒤
    `self.commands.update(korean_command_map(self.commands))` 한 줄로 한글 별칭을
    일괄 등록하기 위한 헬퍼. 이미 한글 키가 있는 명령(익절/손절)은 건너뛰고,
    영문 별칭이 이 클라이언트에 없으면(예: 웹의 power) 해당 한글 키도 만들지 않는다.
    """
    out = {}
    for c in COMMANDS_META:
        if c["name"] in commands:
            continue
        for alias in c["aliases"]:
            if alias in commands:
                out[c["name"]] = commands[alias]
                break
    return out
