"""
command_meta 메타데이터 정합성 검사.

COMMANDS_META는 한글↔영문 별칭 매핑의 단일 소스이자 웹 "/" 자동완성
(GET /api/commands)의 데이터 소스라, 형식이 깨지면 두 기능이 동시에 망가진다.
"""

import pytest

from src.commands.command_meta import COMMANDS_META, korean_command_map

REQUIRED_KEYS = {"name", "aliases", "usage", "desc", "category"}


def test_every_entry_has_required_keys():
    for entry in COMMANDS_META:
        assert REQUIRED_KEYS <= set(entry), f"{entry.get('name')} 항목에 누락된 키: {REQUIRED_KEYS - set(entry)}"


def test_names_are_unique():
    names = [e["name"] for e in COMMANDS_META]
    assert len(names) == len(set(names)), "COMMANDS_META에 중복된 한글 명령이 있습니다"


def test_aliases_are_globally_unique():
    """같은 영문 별칭이 두 한글 명령에 붙으면 나중 등록이 앞선 것을 덮어쓴다."""
    seen = {}
    for entry in COMMANDS_META:
        for alias in entry["aliases"]:
            assert alias not in seen, f"별칭 '{alias}'이 '{seen[alias]}'와 '{entry['name']}'에 중복 등록됐습니다"
            seen[alias] = entry["name"]


def test_names_are_korean_and_usage_starts_with_slash():
    for entry in COMMANDS_META:
        assert entry["usage"].startswith("/"), f"{entry['name']}: usage는 '/'로 시작해야 합니다"
        assert entry["usage"].lstrip("/").startswith(entry["name"]), (
            f"{entry['name']}: usage가 자기 명령 이름으로 시작하지 않습니다 ({entry['usage']})"
        )


def test_aliases_are_ascii():
    """영문 별칭은 AI 변환기가 출력하는 토큰이라 ASCII여야 한다."""
    for entry in COMMANDS_META:
        for alias in entry["aliases"]:
            assert alias.isascii(), f"{entry['name']}의 별칭 '{alias}'이 ASCII가 아닙니다"


def test_korean_command_map_maps_korean_to_existing_handlers():
    english = {"srch": "H_SRCH", "buy": "H_BUY", "sell": "H_SELL"}
    mapped = korean_command_map(english)
    assert mapped["종목정보"] == "H_SRCH"
    assert mapped["매수"] == "H_BUY"
    assert mapped["매도"] == "H_SELL"


def test_korean_command_map_skips_unregistered_commands():
    """클라이언트에 없는 명령은 한글 별칭도 만들지 않아야 한다 (유령 매핑 방지)."""
    mapped = korean_command_map({"srch": "H_SRCH"})
    assert "종목정보" in mapped
    assert "매수" not in mapped


@pytest.mark.parametrize("entry", COMMANDS_META, ids=lambda e: e["name"])
def test_category_is_non_empty(entry):
    assert entry["category"].strip(), f"{entry['name']}: category가 비어 있습니다"
