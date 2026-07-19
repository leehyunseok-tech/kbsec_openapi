"""
자연어 변환(Claude) 결과 명령어의 'api {한글이름}' 토큰을 docs/api/api-list.json의
API명으로 결정적으로 해석한다 (src/utils/stock_resolver.py와 동일한 패턴).

AI(ai_command_converter.py)는 API 코드를 직접 추측하지 않고 docs/api/md 파일명에 있는
한글 API명을 그대로 사용하도록 지시되어 있다(docs/command_guide_for_ai.md 참고) — 실제 코드
변환은 여기서 docs/api/api-list.json 로컬 조회로 처리해, AI가 존재하지 않거나 틀린
코드를 만들어내는 위험을 없앤다.
"""

import re
from dataclasses import dataclass

from src.utils.api_spec import search_api_entries

_CODE_RE = re.compile(r"^[A-Za-z0-9]{6,}$")
_SUBCOMMANDS = {"list", "info"}


@dataclass(frozen=True)
class ApiCandidate:
    code: str
    name: str
    category: str


def _is_code(token: str) -> bool:
    return bool(_CODE_RE.match(token))


def _normalize(text: str) -> str:
    return text.replace(" ", "").strip().lower()


def _candidates_for(name: str):
    """이름으로 API 검색. 정규화 후 정확히 일치하는 API가 있으면 그것만 우선 반환."""
    norm_target = _normalize(name)
    if not norm_target:
        return []
    entries = search_api_entries(None)
    exact = [e for e in entries if _normalize(e["name"]) == norm_target]
    matches = exact or [e for e in entries if norm_target in _normalize(e["name"])]
    return [ApiCandidate(code=e["code"], name=e["name"], category=e.get("category", "")) for e in matches]


def resolve_first_api_name(commands):
    """
    commands를 순서대로 검사해 'api' 명령의 첫 인자가 이미 코드이거나 list/info
    서브명령이 아니면 한글 API명으로 간주하고 로컬 검색으로 해석한다.

    Returns:
      ("ok", 해석완료된 commands 리스트)
      ("ambiguous", cmd_index, API명, candidates)   candidates: list[ApiCandidate]
      ("not_found", API명)
    """
    resolved = list(commands)
    for cmd_index, cmd in enumerate(resolved):
        parts = cmd.split()
        if not parts:
            continue
        name, args = parts[0].lower(), parts[1:]
        if name != "api" or not args:
            continue
        if args[0].lower() in _SUBCOMMANDS:
            continue
        if len(args) == 1 and _is_code(args[0]):
            continue

        raw_name = " ".join(args)
        if _is_code(raw_name):
            continue

        candidates = _candidates_for(raw_name)
        if not candidates:
            return "not_found", raw_name
        if len(candidates) > 1:
            return "ambiguous", cmd_index, raw_name, candidates

        resolved[cmd_index] = f"api {candidates[0].code}"

    return "ok", resolved
