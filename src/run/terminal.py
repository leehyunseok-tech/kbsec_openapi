"""
KB증권 API 터미널 클라이언트 (듀얼 클라이언트 아키텍처).

telegram.py(TelegramBot)와 동일한 src/commands/*.py 핸들러를 공유하는
TerminalClient — 텔레그램 없이 터미널에서 봇 명령어를 그대로 테스트할 수 있다.
추가로 API 코드 기반 저수준 직접 호출(call/info/list)도 제공한다.

사용법:
  uv run python -m src.run.terminal   (또는 manage/run/run-terminal.bat / manage/run/run-terminal.sh)

실행하면 배너 출력 → 자동 로그인 → `>>> ` 프롬프트 순서로 시작한다. 자동 로그인은
운영환경(`real`) 고정이다 — KB증권 개발환경(모의투자)이 아직 제공되지 않기 때문
(`docs/features.md` 참고).

'/'로 시작하면 명확한 커맨드로 간주해 AI 없이 곧바로 실행되고, '/' 없이 입력하면
자연어로 간주해 무조건 Claude로 변환 후 확인을 거쳐 실행된다(telegram.py와 동일 규칙).

명령어:
  /login real                  로그인 (토큰 발급)
  /help                        봇 명령어 도움말
  /srch, /rank, /buy, /sell, /ccl, /report, /mst, /stcd ...   봇과 동일한 명령어
  /call <API코드> <json>        저수준 직접 호출 (json은 dataBody 필드)
  /info <API코드>               해당 API의 필수/선택 파라미터 조회
  /list [모듈명]                등록된 API 코드/이름 목록 조회
  /power off / exit / quit     종료

# 참고: 조건검색식 실시간거래(cond/jggs), VI(변동성완화장치) 감시(vi),
# 테마·공매도·대차거래 분석(theme/short/loan)은 KB증권 OpenAPI에 대응 API가 없어
# 지원하지 않는다 (docs/features.md 참고). KB가 추후 실시간/조건검색 API를 제공하면
# 여기에 추가한다.
"""

import json
import sys

from src.utils.console import force_utf8_streams
from src.utils.logging_config import setup_logging

# Windows 콘솔 기본 코드페이지(cp949)는 이모지/일부 한글 조합을 인코딩하지 못해
# UnicodeEncodeError가 나므로, 다른 모듈을 import 하기 전에 표준 스트림을 UTF-8로 강제한다.
force_utf8_streams(include_stdin=True)
setup_logging()

from src.commands.api_command import handle_api
from src.commands.brk_command import set_brk_monitor
from src.commands.command_meta import AUTOTRADE_FEATURE_ALIASES, AUTOTRADE_FEATURES_KR, korean_command_map
from src.commands.grid_command import set_grid_monitor
from src.commands.login_command import handle_login
from src.commands.registry import CommandContext, build_common_commands
from src.commands.wave_command import set_wave_monitor
from src.run.command_pipeline import CommandPipelineMixin
from src.utils import terminal_ui
from src.utils.ai_command_converter import convert_natural_to_commands
from src.utils.api_spec import describe_spec, execute_api_call, full_blank_body, load_api_spec, search_api_entries
from src.utils.brk_monitor import BrkMonitor
from src.utils.command_executor import (
    CommandPendingExecution,
    get_session_manager,
)
from src.utils.dead_cross_monitor import DeadCrossMonitor
from src.utils.direct_api_command import execute_direct_command, resolve_direct_command
from src.utils.golden_cross_monitor import GoldenCrossMonitor
from src.utils.grid_monitor import GridMonitor
from src.utils.holdings_monitor import HoldingsMonitor
from src.utils.session import SessionManager
from src.utils.stoploss_manager import StopLossManager
from src.utils.trailing_stop_monitor import TrailingStopMonitor
from src.utils.wave_monitor import WaveMonitor

CLI_USER_ID = "cli"
_AUTOTRADE_FEATURES = ("stls", "gdcrs", "ddcrs", "trst", "hold", "brk", "wave", "grid")

LOW_LEVEL_HELP = """── 저수준 직접 호출 (API 코드 기반) ──
  /call <API코드> [<json>]  API 호출. 지정한 필드만 값을 채우고 나머지는 전부
                           타입(길이)만큼 공백(" ")으로 자동 채워 요청합니다.
                           예: /call SZQM0771 {}
                           예: /call SSAM1801 {"is_cd":"005930","ordr_q":"1","ordr_uprc":"320000"}
  /info <API코드>           해당 API의 파라미터(타입/길이/필수여부/선택지) 조회 (호출 전 확인용)
  /list [키워드]            등록 API 코드/이름/업무구분 검색 (키워드 생략 시 전체)
"""


class _TerminalContext(CommandContext):
    """터미널 클라이언트가 공용 명령 핸들러에 넘길 의존성.

    터미널에는 파일/사진을 보낼 대상이 없어 document_sender/photo_sender는 기본값(None)을
    그대로 쓴다 — 핸들러들이 None이면 전송을 건너뛰고 경로만 안내한다. 모니터도
    프로세스당 하나뿐이라 전역 싱글턴에 맡긴다(기본 None).
    """

    def __init__(self, client):
        super().__init__(client.session)
        self._client = client

    @property
    def execute_command(self):
        return self._client.process_command_as_text


class TerminalClient(CommandPipelineMixin):
    """telegram.py의 TelegramBot과 동일한 명령 핸들러를 공유하는 터미널 클라이언트.

    AI 자연어 변환 이후의 처리(종목명/API명 해석, 선택/확인 세션, 일괄 실행)는
    telegram.py와 공유하는 CommandPipelineMixin(src/run/command_pipeline.py)에 있다.
    """

    def __init__(self):
        self.session = SessionManager()
        self.running = True

        self.brk_monitor = BrkMonitor(self.session, self._execute_monitor_command, self._notify)
        set_brk_monitor(self.brk_monitor)
        self.wave_monitor = WaveMonitor(self.session, self._execute_monitor_command, self._notify)
        set_wave_monitor(self.wave_monitor)
        self.grid_monitor = GridMonitor(self.session, self._execute_monitor_command, self._notify)
        set_grid_monitor(self.grid_monitor)

        self.gdcrs_monitor = None
        self.ddcrs_monitor = None
        self.trst_monitor = None
        self.stls_monitor = None
        self.hold_monitor = None

        # 공용 명령은 src/commands/registry.py 한 곳에 선언돼 있다 (telegram/web과 공유).
        self.commands = build_common_commands(_TerminalContext(self))
        # 클라이언트마다 동작이 다른 명령만 여기서 직접 등록한다(registry.CLIENT_SPECIFIC).
        self.commands.update(
            {
                "login": self.handle_command_login,
                "help": self.handle_command_help,
                "api": self.handle_command_api,
                "start": self.handle_command_start,
                "stop": self.handle_command_stop,
                "power": self.handle_command_power,
            }
        )
        # 한글 명령 등록: command_meta의 한글 이름을 같은 핸들러로 매핑 (영문 키는 별칭으로 유지)
        self.commands.update(korean_command_map(self.commands))
        self.commands["종료"] = self.handle_command_quit  # /종료 는 인자 없이 즉시 종료 (/power off 와 별개)

    @staticmethod
    def _notify(message):
        """터미널 환경에서는 텔레그램 전송 대신 콘솔에 출력."""
        print(f"\n🔔 [알림] {message}\n", flush=True)

    def handle_command_login(self, args):
        return handle_login(args, self.session)

    def handle_command_help(self, args):
        from src.run.telegram import HELP_TEXT

        return HELP_TEXT.strip() + "\n" + LOW_LEVEL_HELP

    def handle_command_api(self, args, interactive=False):
        """
        interactive=False(기본)는 self.commands["api"](args) 형태로 균일하게
        호출되는 경로(_execute_all_commands의 확정된 명령 일괄 실행, 모니터 콜백 등)에서
        쓰인다 — 이미 확정되어 더 이상 사용자 응답을 받을 수 없는 흐름 안에서 선택
        세션을 새로 만들면, 그 세션이 등록되자마자 바깥 배치 실행이 끝나며 같은
        CLI_USER_ID 키로 close_session을 호출해 방금 만든 세션을 즉시 지워버리는
        충돌이 생긴다. 그래서 이 경로에서는 세션을 만들지 않고(session_mgr=None),
        선택이 필요한 API면 "/api {코드}로 직접 실행하라"는 안내만 반환한다.
        실제 사용자가 '/api ...'를 직접 입력한 최상위 호출(_dispatch_direct)만
        interactive=True로 넘겨 세션 생성을 허용한다.
        """
        session_mgr = get_session_manager() if interactive else None
        chat_id = CLI_USER_ID if interactive else None
        return handle_api(args, self.session, session_mgr, chat_id)

    def handle_command_power(self, args):
        if not args or args[0].lower() != "off":
            return "사용법: /power off  (또는 /종료)"
        self.running = False
        return "👋 프로그램이 종료됩니다."

    def handle_command_quit(self, args):
        """/종료 — 인자 없이 즉시 종료. (오작동 방지 가드가 있는 /power off 와 별개 진입점)"""
        self.running = False
        return "👋 프로그램이 종료됩니다."

    def handle_command_start(self, args):
        if not args:
            return f"❌ 사용법: /감시시작 {{전략}}\n\n전략: {AUTOTRADE_FEATURES_KR}"
        return self._dispatch_monitor(args[0].lower(), "start")

    def handle_command_stop(self, args):
        if not args:
            return f"❌ 사용법: /감시중단 {{전략}}\n\n전략: {AUTOTRADE_FEATURES_KR}"
        return self._dispatch_monitor(args[0].lower(), "stop")

    def _dispatch_monitor(self, feature, action):
        feature = AUTOTRADE_FEATURE_ALIASES.get(feature, feature)  # 한글 전략명(골든크로스 등) → 내부키
        if feature not in _AUTOTRADE_FEATURES:
            return f"❌ 알 수 없는 전략: {feature}\n\n전략: {AUTOTRADE_FEATURES_KR}"

        if feature == "brk":
            monitor = self.brk_monitor
        elif feature == "wave":
            monitor = self.wave_monitor
        elif feature == "grid":
            monitor = self.grid_monitor
        elif feature == "gdcrs":
            if self.gdcrs_monitor is None:
                self.gdcrs_monitor = GoldenCrossMonitor(self.session, self._execute_monitor_command)
            monitor = self.gdcrs_monitor
        elif feature == "ddcrs":
            if self.ddcrs_monitor is None:
                self.ddcrs_monitor = DeadCrossMonitor(self.session, self._execute_monitor_command)
            monitor = self.ddcrs_monitor
        elif feature == "trst":
            if self.trst_monitor is None:
                self.trst_monitor = TrailingStopMonitor(self.session, self._execute_monitor_command)
            monitor = self.trst_monitor
        elif feature == "stls":
            if self.stls_monitor is None:
                self.stls_monitor = StopLossManager(self.session, self._execute_monitor_command)
            monitor = self.stls_monitor
        elif feature == "hold":
            if self.hold_monitor is None:
                self.hold_monitor = HoldingsMonitor(self.session, self._notify)
            monitor = self.hold_monitor
        else:
            return f"❌ 알 수 없는 전략: {feature}"

        return monitor.start() if action == "start" else monitor.stop()

    def process_command_as_text(self, text, chat_id=None):
        """rank의 cmd 서브명령 등에서 텍스트 명령을 실행하기 위한 콜백."""
        return self._dispatch_direct(text.strip().lstrip("/"))

    def _prompt_for_session(self, session):
        """
        활성 세션 타입에 맞는 대화형 프롬프트(Enter 확인 / 화살표+숫자 선택)를
        보여주고, 그 결과를 process_command가 그대로 이해하는 텍스트로 변환해 반환한다.

        세션 해석 로직 자체(_handle_session_response 등, command_pipeline.py)는
        여전히 텍스트("y"/"n" 또는 1-based 번호 문자열) 기반이라 변경하지 않는다 —
        여기서는 그 텍스트를 "어떻게 입력받을지"만 바꾼다.
        """
        print()
        if isinstance(session, CommandPendingExecution):
            print(session.get_confirmation_message())
            ok = terminal_ui.confirm_prompt()
            return "y" if ok else "n"

        # StockSelectionPending / ApiNameSelectionPending / ApiCallPending 공통 —
        # 셋 다 title()/option_labels()를 제공해 동일하게 다룰 수 있다.
        idx = terminal_ui.select_from_list(session.option_labels(), title=session.title())
        return str(idx + 1) if idx is not None else "취소"

    # ── 저수준 직접 호출 (call/info/list, docs/api/md 명세 기반) ──────────────
    def handle_call(self, args):
        """
        지정한 필드만 JSON으로 값을 채우고, 나머지 INPUT 필드는 전부 타입(길이)만큼
        공백으로 자동 채워 요청한다 — 필수 파라미터를 전부 알아야 했던 예전 방식과
        달리, 관심 있는 값만 입력하면 된다(src/utils/api_spec.py의 full_blank_body).
        """
        if len(args) < 1:
            return "사용법: /call <API코드> ['<json>']"
        if not self.session.is_logged_in():
            return "❌ 먼저 /login real 로 로그인하세요."

        code = args[0].upper()
        spec = load_api_spec(code)
        if spec is None:
            return f"❌ 알 수 없는 API 코드: {code} (/list 명령으로 전체 목록 확인)"

        raw_json = " ".join(args[1:]).strip() or "{}"
        try:
            overrides = json.loads(raw_json)
        except json.JSONDecodeError as e:
            return f"❌ JSON 파싱 오류: {e}"
        if not isinstance(overrides, dict):
            return '❌ JSON은 {"필드명":"값"} 형태의 객체여야 합니다.'

        valid_fields = {f.name_en for f in spec.fields}
        unknown = [k for k in overrides if k not in valid_fields]
        if unknown:
            return f"❌ 알 수 없는 파라미터: {', '.join(unknown)} (/info {code} 로 사용 가능한 필드를 확인하세요)"

        data_body = full_blank_body(spec)
        data_body.update({k: str(v) for k, v in overrides.items()})

        result = execute_api_call(spec, data_body, self.session.access_token, self.session.host_url)
        return json.dumps(result, ensure_ascii=False, indent=2)

    def handle_info(self, args):
        if not args:
            return "사용법: /info <API코드>"
        spec = load_api_spec(args[0])
        if spec is None:
            return f"❌ 알 수 없는 API 코드: {args[0]} (/list 명령으로 전체 목록 확인)"
        return describe_spec(spec) + f'\n원하는 필드만 지정해 호출: /call {spec.code} {{"필드명":"값"}}'

    def handle_list(self, args):
        keyword = args[0] if args else None
        entries = search_api_entries(keyword)
        if not entries:
            return f"검색 결과가 없습니다 (키워드: {keyword})" if keyword else "등록된 API가 없습니다."
        lines = [f"{e['code']:<10} {e['name']}  [{e['category']}]" for e in entries]
        lines.append(f"\n총 {len(entries)}건. '/info <API코드>'로 파라미터를 확인하세요.")
        return "\n".join(lines)

    def process_command(self, text):
        """
        구분 기준은 오직 '/' 유무다 — '/'로 시작하면 명확한 커맨드로 간주해 AI 없이
        곧바로 실행하고, '/' 없이 입력되면 자연어로 간주해 무조건 Claude로 변환 후
        확인을 거친다. 명령어와 같은 단어로 시작한다고 해서 직접 실행되지 않는다.
        """
        text = text.strip()
        if not text:
            return None

        session_mgr = get_session_manager()
        if session_mgr.has_active_session(CLI_USER_ID):
            return self._handle_session_response(text, CLI_USER_ID, session_mgr.get_session(CLI_USER_ID))

        if text.startswith("/"):
            return self._dispatch_direct(text[1:])

        commands, error = convert_natural_to_commands(text)
        if commands:
            return self._handle_ai_commands(commands, CLI_USER_ID)
        if error:
            return f"❌ {error}"
        return f"❌ '{text}'를 이해하지 못했습니다. (/help 참고, 또는 자연어로 요청)"

    def _dispatch_direct(self, text):
        """
        '/'가 이미 벗겨진 명령어 문자열을 AI 없이 곧바로 실행한다.

        process_command의 '/' 분기뿐 아니라, rank의 cmd 콜백처럼 이미 완전히
        해석된 문자열을 신뢰하고 즉시 실행해야 하는 내부 호출에서도 사용한다.
        """
        parts = text.split(maxsplit=1)
        if not parts:
            return "❌ 명령어를 입력하세요. /help를 입력하면 도움말을 볼 수 있습니다."
        command = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if command == "call":
            return self.handle_call(_split_call_args(rest))
        if command == "info":
            return self.handle_info(rest.split())
        if command == "list":
            return self.handle_list(rest.split())
        if command == "api":
            return self.handle_command_api(rest.split(), interactive=True)
        if command in self.commands:
            return self.commands[command](rest.split())

        direct_entry = resolve_direct_command(command)
        if direct_entry is not None:
            if not self.session.is_logged_in():
                return "❌ 로그인이 필요합니다. /login real 을 먼저 실행하세요."
            return execute_direct_command(direct_entry, rest.split(), self.session.access_token, self.session.host_url)

        return f"❌ 알 수 없는 명령어: /{command} (/help 참고)"

    def run(self):
        """터미널 클라이언트 실행 (배너 → 자동 로그인 → 명령 입력 루프)."""
        print("=" * 60)
        print("🤖 KB증권 Open API Agent - 터미널 클라이언트")
        print("=" * 60)
        print("/help 를 입력하면 사용 가능한 명령어를 볼 수 있습니다.")
        print("/exit 또는 /power off 로 프로그램을 종료할 수 있습니다.")
        print("=" * 60)
        print()

        # 자동 로그인 — 운영환경(real) 고정. KB증권 개발환경(모의투자)은 아직 미제공.
        print("🔐 운영환경 자동 로그인 중...")
        login_result = self.handle_command_login(["real"])
        print(login_result)
        print()

        session_mgr = get_session_manager()

        while self.running:
            try:
                if session_mgr.has_active_session(CLI_USER_ID):
                    session = session_mgr.get_session(CLI_USER_ID)
                    answer = self._prompt_for_session(session)
                    response = self.process_command(answer)
                    if session_mgr.has_active_session(CLI_USER_ID):
                        # 세션이 아직 남아있으면(예: API 직접호출의 다음 필드) 다음
                        # 루프에서 대화형 프롬프트가 곧바로 다시 그려주므로, 중간
                        # 텍스트 응답은 출력하지 않는다(중복 출력 방지).
                        continue
                    print()
                    print(response)
                    print()
                    continue

                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ("/exit", "exit", "/quit", "quit"):
                    print("👋 프로그램을 종료합니다.")
                    break

                response = self.process_command(user_input)

                if session_mgr.has_active_session(CLI_USER_ID):
                    # 방금 입력으로 확인/선택 세션이 새로 열렸다 — 다음 루프에서
                    # 바로 대화형 프롬프트로 이어지므로 세션 생성 시점 안내 텍스트는
                    # 다시 출력하지 않는다.
                    continue

                print()
                print(response)
                print()

            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {str(e)}\n")


def _split_call_args(rest):
    """`call CODE '<json>'` 에서 CODE와 json 문자열을 분리."""
    rest = rest.strip()
    if not rest:
        return []
    return rest.split(maxsplit=1)


def main():
    client = TerminalClient()
    client.run()


if __name__ == "__main__":
    sys.exit(main())
