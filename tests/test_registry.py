"""
커맨드 레지스트리 바인딩 동작 검증.

`build_common_commands()`가 만든 호출 함수가 **어떤 핸들러에 어떤 인자를 넘기는지**를
검사한다. 명령 이름만 맞고 인자가 잘못 전달되면(예: 웹이 자기 모니터 대신 None을 넘기면)
이름 기반 정합성 테스트로는 잡히지 않기 때문이다.
"""

import pytest

from src.commands.registry import (
    COMMON_COMMANDS,
    CommandContext,
    CommandSpec,
    build_common_commands,
)


class FakeContext(CommandContext):
    """호출 인자를 기록만 하는 컨텍스트."""

    def __init__(self):
        super().__init__(session="SESSION")
        self.monitors = {"brk": "BRK_MON", "wave": "WAVE_MON", "grid": "GRID_MON"}

    @property
    def document_sender(self):
        return "DOC_SENDER"

    @property
    def photo_sender(self):
        return "PHOTO_SENDER"

    @property
    def execute_command(self):
        return "EXEC"

    def monitor(self, name):
        return self.monitors.get(name)


def test_session_only_command_passes_session():
    calls = []
    spec = CommandSpec("x", lambda *a, **k: calls.append((a, k)), needs=("session",))
    spec.bind(FakeContext())(["arg1"])
    assert calls == [((["arg1"], "SESSION"), {})]


def test_no_dependency_command_passes_only_args():
    calls = []
    spec = CommandSpec("x", lambda *a, **k: calls.append((a, k)))
    spec.bind(FakeContext())(["arg1"])
    assert calls == [((["arg1"],), {})]


def test_monitor_is_passed_as_keyword():
    """웹 다중 사용자 격리의 핵심 — 자기 모니터가 monitor= 키워드로 전달돼야 한다."""
    calls = []
    spec = CommandSpec("brk", lambda *a, **k: calls.append((a, k)), needs=("session",), monitor_kwarg="brk")
    spec.bind(FakeContext())(["add"])
    assert calls == [((["add"], "SESSION"), {"monitor": "BRK_MON"})]


def test_monitor_defaults_to_none_when_context_has_none():
    """텔레그램/터미널은 monitor=None → 핸들러가 전역 싱글턴을 쓴다 (기존 동작 유지)."""
    calls = []
    ctx = CommandContext(session="S")  # 기본 CommandContext.monitor()는 항상 None
    spec = CommandSpec("brk", lambda *a, **k: calls.append((a, k)), needs=("session",), monitor_kwarg="brk")
    spec.bind(ctx)(["add"])
    assert calls == [((["add"], "S"), {"monitor": None})]


def test_senders_are_passed_positionally_in_declared_order():
    calls = []
    spec = CommandSpec("log", lambda *a, **k: calls.append(a), needs=("session", "document_sender"))
    spec.bind(FakeContext())([])
    assert calls == [([], "SESSION", "DOC_SENDER")]


def test_constant_command_ignores_args_and_returns_text():
    spec = CommandSpec("ddcrs", constant="안내문")
    assert spec.bind(FakeContext())(["아무거나"]) == "안내문"


def test_spec_requires_handler_or_constant():
    with pytest.raises(ValueError, match="handler 또는 constant"):
        CommandSpec("broken")


def test_unknown_dependency_raises():
    spec = CommandSpec("x", lambda *a: None, needs=("존재하지않는의존성",))
    with pytest.raises(KeyError, match="알 수 없는 컨텍스트 의존성"):
        spec.bind(FakeContext())([])


def test_build_registers_every_common_command_and_alias():
    commands = build_common_commands(FakeContext())
    for spec in COMMON_COMMANDS:
        assert spec.name in commands
        for alias in spec.aliases:
            assert commands[alias] is commands[spec.name], f"별칭 {alias}이 다른 함수를 가리킵니다"


def test_common_command_names_are_unique():
    names = [s.name for s in COMMON_COMMANDS]
    assert len(names) == len(set(names))


def test_report_alias_r_is_registered():
    """'/r'은 잔고 조회의 짧은 별칭 — 레지스트리 전환 과정에서 빠지기 쉬운 항목이라 명시 검사."""
    commands = build_common_commands(FakeContext())
    assert "r" in commands and commands["r"] is commands["report"]
