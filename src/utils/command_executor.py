"""변환된 명령어들의 실행(확인 후 실행)을 관리하는 모듈 (브로커 무관).

확인/선택 세션은 응답을 "텍스트 한 줄"로 받는다는 점에서 클라이언트 무관하다 —
main.py(텔레그램)는 인라인 버튼 탭의 callback_data를 텍스트로 변환해서,
terminal.py는 화살표 키/Enter 인터랙티브 프롬프트의 결과를 텍스트로 변환해서
넘긴다(둘 다 src/run/command_pipeline.py에서 처리). 세션 클래스 자체는 그
변환된 텍스트("y"/"n" 또는 1-based 번호 문자열)만 알면 된다.
"""

from typing import Dict, List
from datetime import datetime


class CommandPendingExecution:
    """대기 중인 명령어 실행 세션"""

    def __init__(self, user_id, chat_id, commands: List[str]):
        self.user_id = user_id
        self.chat_id = chat_id
        self.commands = commands
        self.created_at = datetime.now()
        self.status = "pending"
        self.current_index = 0
        self.executed_results: Dict[int, str] = {}

    def get_confirmation_message(self) -> str:
        # 명령이 하나뿐이면 번호를 붙이지 않는다 — 세 클라이언트(터미널/텔레그램/웹)
        # 공통 표시 규칙(사용자 요청, 🔍 이모지도 같은 이유로 제거). 여러 개일 때만
        # 순번을 붙여 구분한다.
        if len(self.commands) == 1:
            return f"다음 명령어를 실행할까요?\n\n`{self.commands[0]}`"
        lines = ["다음 명령어를 실행할까요?\n"]
        lines.extend(f"{idx}. `{cmd}`" for idx, cmd in enumerate(self.commands, 1))
        return "\n".join(lines)

    def execute_next(self):
        """다음 명령어로 이동. 반환: (명령어, 인덱스) 또는 (None, -1)"""
        if self.current_index < len(self.commands):
            cmd = self.commands[self.current_index]
            self.current_index += 1
            return cmd, self.current_index - 1
        return None, -1

    def is_completed(self) -> bool:
        return self.current_index >= len(self.commands)

    def mark_executed(self, index: int, result: str):
        self.executed_results[index] = result


class StockSelectionPending:
    """
    자연어 변환 결과에서 종목명이 로컬 mst 검색으로 여러 종목과 매칭될 때,
    사용자가 번호로 하나를 고르도록 대기하는 세션 (src/utils/stock_resolver.py 참고).
    """

    def __init__(self, user_id, chat_id, commands: List[str], cmd_index: int, stock_name: str, candidates: list):
        self.user_id = user_id
        self.chat_id = chat_id
        self.commands = commands  # 전체 명령어 목록. commands[cmd_index]의 첫 인자가 아직 종목명.
        self.cmd_index = cmd_index
        self.stock_name = stock_name
        self.candidates = candidates  # list[stock_resolver._Candidate] (code, name, market) — 국내/해외 공용
        self.created_at = datetime.now()

    def title(self) -> str:
        return f"🔍 '{self.stock_name}' 검색 결과가 여러 건입니다. 번호를 입력하세요."

    def option_labels(self) -> List[str]:
        return [f"{s.name}  {s.code}  [{s.market}]" for s in self.candidates]

    def get_selection_message(self) -> str:
        lines = [self.title() + "\n"]
        lines.extend(f"{idx}. {label}" for idx, label in enumerate(self.option_labels(), 1))
        return "\n".join(lines)

    def resolve_choice(self, choice_idx: int) -> List[str]:
        """1-based 선택 번호로 종목코드를 확정해 대입한 새 commands 리스트 반환."""
        code = self.candidates[choice_idx - 1].code
        parts = self.commands[self.cmd_index].split()
        parts[1] = code
        resolved = list(self.commands)
        resolved[self.cmd_index] = " ".join(parts)
        return resolved


class ApiNameSelectionPending:
    """
    자연어 변환 결과에서 'api {한글이름}'이 로컬 검색으로 여러 API와 매칭될 때,
    사용자가 번호로 하나를 고르도록 대기하는 세션 (src/utils/api_resolver.py 참고).
    """

    def __init__(self, user_id, chat_id, commands: List[str], cmd_index: int, api_name: str, candidates: list):
        self.user_id = user_id
        self.chat_id = chat_id
        self.commands = commands  # 전체 명령어 목록. commands[cmd_index]의 인자가 아직 API 한글이름.
        self.cmd_index = cmd_index
        self.api_name = api_name
        self.candidates = candidates  # list[api_resolver.ApiCandidate] (code, name, category)
        self.created_at = datetime.now()

    def title(self) -> str:
        return f"🔍 '{self.api_name}' API 검색 결과가 여러 건입니다. 번호를 입력하세요."

    def option_labels(self) -> List[str]:
        return [f"{c.name}  {c.code}  [{c.category}]" for c in self.candidates]

    def get_selection_message(self) -> str:
        lines = [self.title() + "\n"]
        lines.extend(f"{idx}. {label}" for idx, label in enumerate(self.option_labels(), 1))
        return "\n".join(lines)

    def resolve_choice(self, choice_idx: int) -> List[str]:
        """1-based 선택 번호로 API 코드를 확정해 대입한 새 commands 리스트 반환."""
        code = self.candidates[choice_idx - 1].code
        resolved = list(self.commands)
        resolved[self.cmd_index] = f"api {code}"
        return resolved


class ApiCallPending:
    """
    "/api {코드}" 직접호출에서 필수(Y)+선택지 있는 INPUT 필드를 사용자가 번호로
    고르도록 대기하는 세션 (src/utils/api_spec.py 참고).

    필드를 한 번에 몰아서 받지 않고 한 번에 하나씩(필드마다 별도 프롬프트) 순서대로
    진행한다 — 터미널의 화살표 메뉴나 텔레그램 인라인 버튼은 한 번의 상호작용으로
    "값 하나"만 고를 수 있어서, 여러 필드를 한 메시지로 동시에 받는 이전 방식(공백
    구분 번호 나열)은 두 UI 모두에서 자연스럽게 표현할 수 없었다.
    """

    def __init__(self, user_id, chat_id, spec, base_data_body: dict, fields: list):
        self.user_id = user_id
        self.chat_id = chat_id
        self.spec = spec  # src.utils.api_spec.ApiSpec
        self.data_body = dict(base_data_body)  # 선택 불필요 필드는 이미 공백으로 채워짐, 선택값은 여기 누적
        self.fields = fields  # list[api_spec.ApiField] — choices 포함, 선택이 필요한 필드 전체
        self.field_index = 0  # 지금 답변을 받아야 하는 필드
        self.created_at = datetime.now()

    def current_field(self):
        return self.fields[self.field_index]

    def title(self) -> str:
        f = self.current_field()
        return f"🔧 {self.spec.code} {self.spec.name} — API 직접호출 ({self.field_index + 1}/{len(self.fields)})\n{f.name_kr}({f.name_en}) 값을 선택하세요."

    def option_labels(self) -> List[str]:
        return [f"{label} ({code})" for code, label in self.current_field().choices]

    def get_selection_message(self) -> str:
        lines = [self.title() + "\n"]
        lines.extend(f"{idx}. {label}" for idx, label in enumerate(self.option_labels(), 1))
        return "\n".join(lines)

    def resolve_choice(self, choice_idx: int) -> bool:
        """1-based 선택을 현재 필드에 적용. 모든 필드가 끝나면 True(완료), 아니면 False(다음 필드 대기)."""
        f = self.current_field()
        self.data_body[f.name_en] = f.choices[choice_idx - 1][0]
        self.field_index += 1
        return self.field_index >= len(self.fields)


class ExecutionSessionManager:
    """사용자별 명령 실행 세션 관리"""

    def __init__(self):
        self.sessions: Dict[str, object] = {}

    def create_session(self, user_id, chat_id, commands: List[str]) -> CommandPendingExecution:
        session = CommandPendingExecution(user_id, chat_id, commands)
        self.sessions[str(user_id)] = session
        return session

    def create_selection_session(self, user_id, chat_id, commands, cmd_index, stock_name, candidates) -> StockSelectionPending:
        session = StockSelectionPending(user_id, chat_id, commands, cmd_index, stock_name, candidates)
        self.sessions[str(user_id)] = session
        return session

    def create_api_name_selection_session(self, user_id, chat_id, commands, cmd_index, api_name, candidates) -> ApiNameSelectionPending:
        session = ApiNameSelectionPending(user_id, chat_id, commands, cmd_index, api_name, candidates)
        self.sessions[str(user_id)] = session
        return session

    def create_api_call_session(self, user_id, chat_id, spec, base_data_body, fields) -> ApiCallPending:
        session = ApiCallPending(user_id, chat_id, spec, base_data_body, fields)
        self.sessions[str(user_id)] = session
        return session

    def get_session(self, user_id):
        return self.sessions.get(str(user_id))

    def close_session(self, user_id):
        self.sessions.pop(str(user_id), None)

    def has_active_session(self, user_id) -> bool:
        return str(user_id) in self.sessions


_session_manager = ExecutionSessionManager()


def get_session_manager() -> ExecutionSessionManager:
    return _session_manager
