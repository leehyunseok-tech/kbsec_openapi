"""
main.py(TelegramBot)와 terminal.py(TerminalClient)가 공유하는 명령 처리 파이프라인.

두 클라이언트는 CLAUDE.md의 듀얼 클라이언트 규칙에 따라 동일한 명령 핸들러를
공유하는데, AI 자연어 변환 이후의 처리(종목명/API명 로컬 해석 → 선택/확인 세션
→ 일괄 실행)까지 완전히 같은 로직이 양쪽에 복사되어 있어 한쪽만 고치는 드리프트
버그가 실제로 발생했었다(terminal.py의 ApiCallPending 세션 충돌 등). 이 믹스인이
그 공통 부분의 단일 소스다 — 파이프라인을 수정할 때는 이 파일만 고치면 된다.

믹스인을 쓰는 클래스가 제공해야 하는 것:
  - self.commands: {명령어: 핸들러(args)} 딕셔너리
  - self.session: SessionManager (access_token / host_url)

user_id는 세션 매니저의 키다 — TelegramBot은 텔레그램 chat_id를, TerminalClient는
고정 센티널(CLI_USER_ID)을 넘긴다.
"""

from src.utils.api_spec import execute_api_call, format_api_result
from src.utils.command_executor import (
    ApiCallPending,
    ApiNameSelectionPending,
    StockSelectionPending,
    get_session_manager,
)
from src.utils.api_resolver import resolve_first_api_name
from src.utils.stock_resolver import resolve_first_ambiguous


class CommandPipelineMixin:
    """AI 변환 결과 처리(해석/선택/확인/일괄실행)와 모니터 콜백의 공통 구현."""

    def _execute_monitor_command(self, cmd_str: str):
        """brk/wave/grid 모니터가 감지 시 명령어를 직접 실행할 때 사용."""
        parts = cmd_str.strip().split()
        if not parts:
            return None
        command, args = parts[0].lower(), parts[1:]
        if command in self.commands:
            try:
                return self.commands[command](args)
            except Exception as e:
                return f"⚠️ 명령 실행 오류: {e}"
        return f"⚠️ 알 수 없는 명령어: {command}"

    def _handle_ai_commands(self, commands, user_id):
        """
        AI가 변환한 명령어 목록에서 종목명 → API 한글이름 순서로 로컬 해석한 뒤
        확인 세션을 만든다.

        buy/sell/srch/investor의 첫 인자가 6자리 코드가 아니면 종목명으로 보고
        mst/api 파일에서 검색하고(src/utils/stock_resolver.py), api 명령의 인자가
        코드가 아니면 docs/api/api-list.json에서 한글 API명으로 검색한다
        (src/utils/api_resolver.py). 어느 쪽이든 결과가 여러 건이면 번호 선택
        세션을 만든다.
        """
        session_mgr = get_session_manager()
        status, *rest = resolve_first_ambiguous(commands)
        if status == "ambiguous":
            cmd_index, stock_name, candidates = rest
            session = session_mgr.create_selection_session(user_id, user_id, commands, cmd_index, stock_name, candidates)
            return session.get_selection_message()
        if status == "not_found":
            (stock_name,) = rest
            return f"❌ '{stock_name}' 종목을 찾을 수 없습니다.\n\n/stcd {stock_name} 로 종목명을 확인해보세요."
        (resolved_commands,) = rest

        api_status, *api_rest = resolve_first_api_name(resolved_commands)
        if api_status == "ambiguous":
            cmd_index, api_name, candidates = api_rest
            session = session_mgr.create_api_name_selection_session(user_id, user_id, resolved_commands, cmd_index, api_name, candidates)
            return session.get_selection_message()
        if api_status == "not_found":
            (api_name,) = api_rest
            return f"❌ '{api_name}' API를 찾을 수 없습니다.\n\n/api list {api_name} 로 확인해보세요."
        (resolved_commands,) = api_rest

        session = session_mgr.create_session(user_id, user_id, resolved_commands)
        return session.get_confirmation_message()

    def _handle_session_response(self, response, user_id, session):
        """확인/선택 대기 세션에 대한 사용자 응답 처리."""
        session_mgr = get_session_manager()
        if isinstance(session, StockSelectionPending):
            return self._handle_selection_response(response, user_id, session)
        if isinstance(session, ApiNameSelectionPending):
            return self._handle_api_name_selection_response(response, user_id, session)
        if isinstance(session, ApiCallPending):
            return self._handle_api_selection_response(response, user_id, session)
        if response.strip().lower() in ("y", "yes", "ㅇ"):
            return self._execute_all_commands(session)
        session_mgr.close_session(user_id)
        return "❌ 명령 실행이 취소되었습니다."

    def _handle_selection_response(self, response, user_id, session):
        """종목 번호 선택 세션에 대한 응답 처리 ('1'~'N'이면 확정, 그 외는 취소)."""
        session_mgr = get_session_manager()
        response = response.strip()
        session_mgr.close_session(user_id)
        if not response.isdigit() or not (1 <= int(response) <= len(session.candidates)):
            return "❌ 종목 선택이 취소되었습니다."
        updated_commands = session.resolve_choice(int(response))
        return self._handle_ai_commands(updated_commands, user_id)

    def _handle_api_name_selection_response(self, response, user_id, session):
        """'api {한글이름}' 검색 결과 선택 세션에 대한 응답 처리."""
        session_mgr = get_session_manager()
        response = response.strip()
        session_mgr.close_session(user_id)
        if not response.isdigit() or not (1 <= int(response) <= len(session.candidates)):
            return "❌ API 선택이 취소되었습니다."
        updated_commands = session.resolve_choice(int(response))
        return self._handle_ai_commands(updated_commands, user_id)

    def _handle_api_selection_response(self, response, user_id, session):
        """
        '/api {코드}' 선택 대기 세션에 대한 응답 처리 — 필드 하나씩 순서대로 진행.

        아직 답변할 필드가 남아 있으면 세션을 닫지 않고 다음 필드의 프롬프트를
        반환한다(메신저/터미널 양쪽 다 그 프롬프트를 사용자에게 다시 보여준다).
        모든 필드가 채워지면 세션을 닫고 실제로 API를 호출한다.
        """
        session_mgr = get_session_manager()
        response = response.strip()
        field = session.current_field()
        if not response.isdigit() or not (1 <= int(response) <= len(field.choices)):
            session_mgr.close_session(user_id)
            return "❌ 입력이 올바르지 않아 취소되었습니다."

        done = session.resolve_choice(int(response))
        if not done:
            return session.get_selection_message()

        session_mgr.close_session(user_id)
        result = execute_api_call(session.spec, session.data_body, self.session.access_token, self.session.host_url)
        return format_api_result(session.spec, result)

    def _execute_all_commands(self, session):
        """확인(y)된 명령어들을 순차 실행하고 결과를 모아 반환."""
        session_mgr = get_session_manager()
        results = []
        while not session.is_completed():
            cmd, idx = session.execute_next()
            if cmd is None:
                break
            parts = cmd.split()
            command, args = parts[0], parts[1:]
            try:
                if command in self.commands:
                    result = self.commands[command](args) or "(결과 없음)"
                    session.mark_executed(idx, result)
                    results.append(f"✅ {idx + 1}. `{cmd}`\n{result}")
                else:
                    session.mark_executed(idx, "오류: 알 수 없는 명령어")
                    results.append(f"❌ {idx + 1}. `{cmd}`\n오류: 알 수 없는 명령어")
            except Exception as e:
                session.mark_executed(idx, f"오류: {e}")
                results.append(f"❌ {idx + 1}. `{cmd}`\n오류: {e}")

        session_mgr.close_session(session.user_id)
        return "🎯 명령 실행 완료\n\n" + "\n\n".join(results)
