"""
트리플 클라이언트 명령 등록 정합성 검사.

telegram/terminal/web 세 클라이언트는 `src/commands/*.py`의 **같은 핸들러를 공유**해야
한다(CLAUDE.md 필수 규칙). 과거에 파이프라인 로직이 클라이언트마다 복사돼 있다가
드리프트 버그가 실제로 발생했기 때문에, 명령 집합이 갈라지는 것을 테스트로 못박는다.

이 테스트는 커맨드 레지스트리 리팩터링의 **안전망**이다 — 리팩터링 전후로 동일하게
통과해야 하며, 그래야 "중복만 제거했고 동작은 그대로"임이 보장된다.
"""

import pytest

from src.commands.command_meta import COMMANDS_META
from src.run.telegram import TelegramBot
from src.run.terminal import TerminalClient
from src.web.client import WebClient

# 웹에만 없는 명령과 그 이유.
#   power/종료 — 웹은 여러 사용자가 공유하는 서버라 브라우저에서 프로세스를 죽이면 안 된다.
WEB_ONLY_MISSING = {"power", "종료"}

# 한글 명령이 영문 별칭과 **의도적으로** 다른 핸들러를 쓰는 경우.
#   종료/power — `/종료`는 인자 없이 즉시 종료하고, `/power off`는 오작동 방지를 위해
#   반드시 "off" 인자를 요구한다. 별개 진입점인 것이 설계다.
INTENTIONALLY_DIFFERENT_HANDLERS = {("종료", "power")}


@pytest.fixture(scope="module")
def clients():
    return {
        "telegram": TelegramBot(),
        "terminal": TerminalClient(),
        "web": WebClient(web_session_id="test-session"),
    }


def test_telegram_and_terminal_expose_identical_commands(clients):
    """텔레그램과 터미널은 명령 집합이 완전히 같아야 한다 (제외 대상 없음)."""
    assert set(clients["telegram"].commands) == set(clients["terminal"].commands)


def test_web_differs_only_by_documented_exceptions(clients):
    """웹에 없는 명령은 문서화된 예외뿐이어야 한다 — 그 외 차이는 드리프트다."""
    missing = set(clients["telegram"].commands) - set(clients["web"].commands)
    assert missing == WEB_ONLY_MISSING, (
        f"웹 클라이언트 명령 차이가 예상과 다릅니다. 예상 누락={WEB_ONLY_MISSING}, 실제 누락={missing}"
    )
    # 웹에만 있는 명령이 생기는 것도 드리프트다.
    assert not set(clients["web"].commands) - set(clients["telegram"].commands)


def test_every_command_is_callable(clients):
    for name, client in clients.items():
        for cmd, fn in client.commands.items():
            assert callable(fn), f"{name} 클라이언트의 '{cmd}' 핸들러가 호출 가능하지 않습니다"


def test_korean_aliases_registered_in_all_clients(clients):
    """command_meta의 한글 이름이 세 클라이언트 모두에 별칭으로 등록돼야 한다.

    한글이 기본 명령이고 영문은 숨김 별칭인 체계라, 한글이 빠지면 사용자가 쓰는
    기본 명령이 동작하지 않는다.
    """
    for entry in COMMANDS_META:
        korean = entry["name"]
        for name, client in clients.items():
            if korean in WEB_ONLY_MISSING and name == "web":
                continue
            assert korean in client.commands, f"{name} 클라이언트에 한글 명령 '{korean}'이 등록되지 않았습니다"


def test_korean_alias_maps_to_same_handler_as_english(clients):
    """한글 명령과 영문 별칭은 같은 핸들러를 가리켜야 한다 (한쪽만 바뀌는 드리프트 방지)."""
    for entry in COMMANDS_META:
        korean, aliases = entry["name"], entry["aliases"]
        for name, client in clients.items():
            if korean in WEB_ONLY_MISSING and name == "web":
                continue
            for alias in aliases:
                if alias not in client.commands or (korean, alias) in INTENTIONALLY_DIFFERENT_HANDLERS:
                    continue
                assert client.commands[korean] == client.commands[alias], (
                    f"{name}: '{korean}'과 별칭 '{alias}'이 서로 다른 핸들러를 가리킵니다"
                )


def test_commands_meta_has_no_ghost_entries(clients):
    """COMMANDS_META에만 있고 실제 클라이언트엔 없는 유령 항목이 없어야 한다."""
    registered = set(clients["telegram"].commands)
    for entry in COMMANDS_META:
        assert entry["name"] in registered, f"COMMANDS_META의 '{entry['name']}'이 어느 클라이언트에도 없습니다"
