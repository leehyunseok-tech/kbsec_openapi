"""
자연어 변환(Claude) 결과 명령어의 종목코드 자리에 있는 종목명을 로컬 mst 파일로
결정적으로 해석한다.

investor 핸들러는 국내(코스피/코스닥) 6자리 코드만 받아들이므로(KB API에 해외 투자자
매매동향 API가 없어 국내 전용) 국내 종목만 검색한다. buy/sell/srch는 국내 코드로 먼저
검색하고, 국내에서 못 찾으면 해외(미국) 티커로 한 번 더 검색한다 —
buy_command.py/sell_command.py/srch_command.py가 6자리 숫자면 국내(SSAM1801/1802/
IVU10140), 그 외(예: "IONQ")면 mst/api/openapi_field_foren-us.mst에 등록된 해외 티커인지
확인해 해외(SKAM2101/GSS10030)로 분기하기 때문이다.

Claude(ai_command_converter.py)는 사용자가 종목명으로 말한 경우 코드로 추측하지 않고
종목명을 그대로 남겨두도록 지시되어 있다(docs/command_guide.md 참고) — 실제 종목코드
변환은 여기서 mst/api 로컬 파일 검색으로 처리해, AI가 존재하지 않거나 틀린 코드를
만들어내는 위험을 없앤다. rsv에 중첩된 명령(예: "rsv 10:00 buy 005930 5")은 예약 재실행
시 AI/이 리졸버를 거치지 않고 바로 실행되므로 대상에서 제외한다(기존처럼 Claude가
직접 코드로 변환).
"""

from dataclasses import dataclass

from src.utils.stock_master import search_domestic, search_overseas

_STOCK_CODE_COMMANDS = {"buy", "sell", "srch", "investor"}
_OVERSEAS_ELIGIBLE_COMMANDS = {"buy", "sell", "srch"}


@dataclass(frozen=True)
class _Candidate:
    """국내(DomesticStock)/해외(OverseasStock)를 동일한 모양으로 다루기 위한 공용 표현."""

    code: str  # 국내 6자리 코드 또는 해외 티커
    name: str
    market: str  # 'KOSPI'/'KOSDAQ' 또는 거래소코드(NAS 등)


def _is_code(token: str) -> bool:
    return token.isdigit() and len(token) == 6


def _domestic_candidates_for(name: str):
    """이름으로 국내 종목 검색. 정확히 일치하는 종목이 있으면 그것만 우선 반환."""
    matches = search_domestic(name, limit=20)
    exact = [s for s in matches if s.name == name]
    matches = exact or matches
    return [_Candidate(code=s.code, name=s.name, market=s.market) for s in matches]


def _overseas_candidates_for(name: str):
    """이름/티커로 해외 종목 검색. 티커·한글명·영문명이 정확히 일치하면 그것만 우선 반환."""
    matches = search_overseas(name, limit=20)
    name_stripped = name.strip()
    name_upper = name_stripped.upper()
    exact = [
        s
        for s in matches
        if name_upper == s.ticker.upper() or name_stripped in (s.name_kr, s.name_en) or name_upper == s.name_en.upper()
    ]
    matches = exact or matches
    return [_Candidate(code=s.ticker, name=(s.name_kr or s.name_en), market=s.exchange) for s in matches]


def resolve_first_ambiguous(commands):
    """
    commands를 순서대로 검사해 buy/sell/srch/investor의 첫 인자가 종목코드가 아니면
    종목명으로 간주하고 로컬 검색으로 해석한다. ("all"과 이미 6자리 코드인 경우는 통과.)
    buy/sell은 국내 검색이 비어 있으면 해외 티커로 한 번 더 검색한다.

    Returns:
      ("ok", 해석완료된 commands 리스트)
      ("ambiguous", cmd_index, 종목명, candidates)   candidates: list[_Candidate]
      ("not_found", 종목명)
    """
    resolved = list(commands)
    for cmd_index, cmd in enumerate(resolved):
        parts = cmd.split()
        if not parts:
            continue
        name, args = parts[0].lower(), parts[1:]
        if name not in _STOCK_CODE_COMMANDS or not args:
            continue

        token = args[0]
        if _is_code(token) or token.lower() == "all":
            continue

        candidates = _domestic_candidates_for(token)
        if not candidates and name in _OVERSEAS_ELIGIBLE_COMMANDS:
            candidates = _overseas_candidates_for(token)
        if not candidates:
            return "not_found", token
        if len(candidates) > 1:
            return "ambiguous", cmd_index, token, candidates

        args[0] = candidates[0].code
        resolved[cmd_index] = " ".join([parts[0]] + args)

    return "ok", resolved
