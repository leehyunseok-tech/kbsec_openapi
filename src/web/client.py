"""
웹 인터페이스용 클라이언트 (듀얼 → 트리플 클라이언트 아키텍처의 세 번째 축).

telegram.py(TelegramBot)/terminal.py(TerminalClient)와 동일하게 CommandPipelineMixin을
공유해 명령 처리(AI 변환 이후 종목명/API명 해석 → 확인/선택 세션 → 일괄 실행) 로직이
세 클라이언트 모두 하나의 소스(src/run/command_pipeline.py)를 따르게 한다.

터미널/텔레그램과 결정적으로 다른 점 — 인증 방식:
  터미널/텔레그램은 단일 운영자가 config.py에 자신의 client_key/client_secret을
  넣어두고 그 값으로만 자동 로그인한다(운영자 1명 = 프로세스 1개).
  웹은 다중 사용자가 하나의 서버를 같이 쓸 수 있어야 하므로, config.py의 키를 쓰지
  않는다 — 각 브라우저 세션(쿠키)이 설정 화면에서 자기 자신의 client_key/client_secret을
  직접 입력하고, 그 값은 이 인스턴스(WebClient) 안에서만 메모리로 보관한다. 디스크에
  저장하지 않으므로 서버가 재시작되면 다시 입력해야 한다 — 공개 배포 시 다른 사용자의
  시크릿이 파일로 남지 않게 하려는 의도적인 설계다 (src/web/session_store.py 참고).

브라우저 세션 1개 = WebClient 인스턴스 1개 = SessionManager(토큰) 1개 + 모니터
스레드 세트 1벌. command_executor.py의 확인/선택 세션은 프로세스 전역 싱글턴이라
user_id로 서로 구분해야 하는데(telegram.py는 텔레그램 chat_id, terminal.py는 고정
CLI_USER_ID를 쓰는 것과 동일한 이유), 여기서는 웹 세션 쿠키 값 자체를 user_id로 쓴다.
"""

import threading
from collections import deque

from config import config
from src.api.auth import get_token, revoke_token
from src.commands.anss_command import handle_anss
from src.commands.api_command import handle_api
from src.commands.blacklist_command import handle_blacklist
from src.commands.brk_command import handle_brk
from src.commands.buy_command import handle_buy
from src.commands.ccl_command import handle_ccl
from src.commands.command_meta import AUTOTRADE_FEATURE_ALIASES, AUTOTRADE_FEATURES_KR, korean_command_map
from src.commands.cooldown_command import handle_cooldown
from src.commands.gdcrs_command import handle_gdcrs
from src.commands.grid_command import handle_grid
from src.commands.investor_command import handle_investor
from src.commands.log_command import handle_log
from src.commands.login_command import handle_status
from src.commands.loss_command import handle_loss
from src.commands.mkhr_command import handle_mkhr
from src.commands.mst_command import handle_mst
from src.commands.mxhold_command import handle_mxhold
from src.commands.profit_command import handle_profit
from src.commands.rank_command import handle_rank
from src.commands.report_command import handle_report
from src.commands.rsv_command import handle_rsv
from src.commands.sell_command import handle_sell
from src.commands.srch_command import handle_srch
from src.commands.stcd_command import handle_stcd
from src.commands.stts_command import handle_stts
from src.commands.time_command import handle_time
from src.commands.trst_command import handle_trst
from src.commands.wave_command import handle_wave
from src.msgr.telegram.tel_send import send_document, send_photo
from src.run.command_pipeline import CommandPipelineMixin
from src.utils import api_spec
from src.utils.ai_command_converter import convert_natural_to_commands
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

_AUTOTRADE_FEATURES = ("stls", "gdcrs", "ddcrs", "trst", "hold", "brk", "wave", "grid")

LOW_LEVEL_HELP = """── 저수준 직접 호출 (API 코드 기반) ──
  /call <API코드> [<json>]  API 호출. 지정한 필드만 값을 채우고 나머지는 전부
                           타입(길이)만큼 공백(" ")으로 자동 채워 요청합니다.
                           예: /call SZQM0771 {}
                           예: /call SSAM1801 {"is_cd":"005930","ordr_q":"1","ordr_uprc":"320000"}
  /info <API코드>           해당 API의 파라미터(타입/길이/필수여부/선택지) 조회 (호출 전 확인용)
  /list [키워드]            등록 API 코드/이름/업무구분 검색 (키워드 생략 시 전체)
"""


class WebClient(CommandPipelineMixin):
    """웹 브라우저 세션(쿠키) 하나에 대응하는 클라이언트.

    telegram.py/terminal.py와 동일한 src/commands/*.py 핸들러를 공유한다. 다른 점은
    로그인(login) 방식과, 모니터 알림을 텔레그램 전송/콘솔 출력 대신 이 인스턴스의
    메모리 큐에 쌓아 프론트엔드가 폴링(/api/notifications)해 가져가게 하는 부분뿐이다.
    """

    def __init__(self, web_session_id: str):
        self.user_id = web_session_id  # command_executor 세션 키 (텔레그램 chat_id 역할)
        self.session = SessionManager()

        # 설정 화면에서 선택적으로 입력받는 값 — 미입력 시 None (config.py 전역값으로 폴백하지 않음,
        # 사용자별로 격리되어야 하는 값이라 서버 공용 config.py를 참조하면 다른 사용자와 섞인다).
        self.claude_api_key = None
        self.claude_model = None
        self.telegram_token = None
        self.telegram_chat_id = None

        # 마지막 로그인에 쓴 앱키/시크릿 (메모리 전용 — 토큰 재발급/로그아웃 시 토큰
        # 폐기에 필요). 시크릿 무저장 원칙과 동일하게 이 인스턴스 밖으로 나가지 않는다.
        self._login_env = None
        self._login_client_key = None
        self._login_client_secret = None

        self._notify_lock = threading.Lock()
        self.notifications = deque(maxlen=200)

        # 주의: telegram.py/terminal.py처럼 set_brk_monitor() 등으로 전역 등록하지 않는다 —
        # 웹은 브라우저 세션마다 WebClient가 새로 생기므로, 전역 등록하면 마지막에 접속한
        # 사용자의 모니터가 다른 모든 사용자의 brk/wave/grid 명령을 가로챈다. 대신
        # handle_brk/handle_wave/handle_grid에 monitor 인자로 자기 것을 명시적으로 넘긴다.
        self.brk_monitor = BrkMonitor(self.session, self._execute_monitor_command, self._notify)
        self.wave_monitor = WaveMonitor(self.session, self._execute_monitor_command, self._notify)
        self.grid_monitor = GridMonitor(self.session, self._execute_monitor_command, self._notify)

        self.gdcrs_monitor = None
        self.ddcrs_monitor = None
        self.trst_monitor = None
        self.stls_monitor = None
        self.hold_monitor = None

        self.commands = {
            "login": self.handle_command_login,
            "status": self.handle_command_status,
            "help": self.handle_command_help,
            "srch": self.handle_command_srch,
            "rank": self.handle_command_rank,
            "buy": self.handle_command_buy,
            "sell": self.handle_command_sell,
            "ccl": self.handle_command_ccl,
            "report": self.handle_command_report,
            "r": self.handle_command_report,
            "mst": self.handle_command_mst,
            "stcd": self.handle_command_stcd,
            "mkhr": self.handle_command_mkhr,
            "stts": self.handle_command_stts,
            "time": self.handle_command_time,
            "cooldown": self.handle_command_cooldown,
            "blacklist": self.handle_command_blacklist,
            "mxhold": self.handle_command_mxhold,
            "익절": self.handle_command_profit,
            "손절": self.handle_command_loss,
            "rsv": self.handle_command_rsv,
            "log": self.handle_command_log,
            "anss": self.handle_command_anss,
            "investor": self.handle_command_investor,
            "api": self.handle_command_api,
            "gdcrs": self.handle_command_gdcrs,
            "ddcrs": self.handle_command_ddcrs,
            "trst": self.handle_command_trst,
            "brk": self.handle_command_brk,
            "wave": self.handle_command_wave,
            "grid": self.handle_command_grid,
            "start": self.handle_command_start,
            "stop": self.handle_command_stop,
        }
        # 한글 명령 등록: command_meta의 한글 이름을 같은 핸들러로 매핑 (영문 키는 별칭으로 유지)
        # 웹에는 종료(power)가 없다 — 브라우저에서 서버를 끄면 다른 사용자에게 영향을 주기 때문.
        self.commands.update(korean_command_map(self.commands))

    # ── 알림 큐 (모니터 콜백 → 프론트 폴링) ─────────────────────────────
    def _notify(self, message):
        with self._notify_lock:
            self.notifications.append(message)

    def drain_notifications(self):
        with self._notify_lock:
            msgs = list(self.notifications)
            self.notifications.clear()
        return msgs

    # ── 로그인 (config.py 미사용 — 사용자가 입력한 키로 직접 토큰 발급) ──
    def login(self, env: str, client_key: str, client_secret: str) -> dict:
        if env not in ("real", "dev"):
            return {"success": False, "message": "env는 real 또는 dev여야 합니다."}

        host_url = config.real_host_url if env == "real" else config.dev_host_url
        result = get_token(host_url, client_key, client_secret)

        if result["success"]:
            self.session.set_token(result["access_token"], env, result["expires_in"])
            self._login_env = env
            self._login_client_key = client_key
            self._login_client_secret = client_secret
            return {"success": True, "message": handle_status([], self.session)}

        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get(
            "resultMessage", "알 수 없는 오류"
        )
        return {"success": False, "message": f"로그인 실패: {error_msg}"}

    def reissue_token(self) -> dict:
        """토큰 재발급 — 마지막 로그인에 쓴 앱키/시크릿으로 새 토큰을 발급받는다."""
        if not (self._login_client_key and self._login_client_secret):
            return {"success": False, "message": "재발급에 쓸 앱키가 없습니다. 설정 화면에서 다시 로그인하세요."}
        result = self.login(self._login_env or "real", self._login_client_key, self._login_client_secret)
        if result["success"]:
            result["message"] = "🔑 토큰을 재발급했습니다.\n" + result["message"]
        return result

    def logout(self) -> dict:
        """로그아웃 — KB에 토큰 폐기를 요청하고, 이 세션의 토큰/앱키를 메모리에서 지운다.

        폐기 API가 실패해도 로컬 상태는 반드시 지운다 — 사용자 관점의 로그아웃은
        항상 성공해야 하고, 폐기 실패한 토큰은 만료 시각까지만 유효하다.
        """
        if not self.session.is_logged_in():
            return {"success": False, "message": "로그인 상태가 아닙니다."}

        detail = ""
        if self._login_client_key and self._login_client_secret:
            revoked = revoke_token(
                self.session.host_url,
                self.session.access_token,
                self._login_client_key,
                self._login_client_secret,
            )
            if not revoked["success"]:
                detail = " (KB 토큰 폐기 요청은 실패 — 토큰은 만료 시각까지 유효할 수 있습니다)"

        self.session.clear()
        self._login_env = None
        self._login_client_key = None
        self._login_client_secret = None
        get_session_manager().close_session(self.user_id)  # 열려 있던 확인/선택 세션도 정리
        return {"success": True, "message": "로그아웃되었습니다." + detail}

    def describe_pending_session(self):
        """현재 활성 확인/선택 세션을 프론트엔드가 렌더링할 수 있는 JSON으로 변환.

        CommandPendingExecution은 confirm(예/아니오), 나머지(StockSelectionPending/
        ApiNameSelectionPending/ApiCallPending)는 공통 title()/option_labels()를 쓰는
        select(번호 선택)로 통일해 다룬다 — telegram.py의 _buttons_for_session, terminal.py의
        _prompt_for_session과 같은 분기 구조다.
        """
        session_mgr = get_session_manager()
        if not session_mgr.has_active_session(self.user_id):
            return None
        session = session_mgr.get_session(self.user_id)
        if isinstance(session, CommandPendingExecution):
            return {"kind": "confirm", "message": session.get_confirmation_message()}
        return {"kind": "select", "title": session.title(), "options": session.option_labels()}

    # ── 명령 핸들러 (telegram.py/terminal.py와 동일하게 self.session 위임) ──
    def handle_command_login(self, args):
        return "ℹ️ 웹에서는 우측 상단 '설정' 화면에서 앱키(client_key)/시크릿(client_secret)을 입력하면 자동으로 로그인됩니다."

    def handle_command_status(self, args):
        return handle_status(args, self.session)

    def handle_command_help(self, args):
        from src.run.telegram import HELP_TEXT

        return HELP_TEXT.strip() + "\n" + LOW_LEVEL_HELP

    def handle_command_srch(self, args):
        return handle_srch(args, self.session)

    def handle_command_rank(self, args):
        return handle_rank(args, self.session, self.process_command_as_text)

    def handle_command_buy(self, args):
        return handle_buy(args, self.session)

    def handle_command_sell(self, args):
        return handle_sell(args, self.session)

    def handle_command_ccl(self, args):
        return handle_ccl(args, self.session)

    def handle_command_report(self, args):
        return handle_report(args, self.session)

    def handle_command_mst(self, args):
        return handle_mst(args, self.session)

    def handle_command_stcd(self, args):
        return handle_stcd(args, self.session)

    def handle_command_mkhr(self, args):
        return handle_mkhr(args)

    def handle_command_stts(self, args):
        return handle_stts(args)

    def handle_command_time(self, args):
        return handle_time(args)

    def handle_command_cooldown(self, args):
        return handle_cooldown(args)

    def handle_command_blacklist(self, args):
        return handle_blacklist(args)

    def handle_command_mxhold(self, args):
        return handle_mxhold(args)

    def handle_command_profit(self, args):
        return handle_profit(args)

    def handle_command_loss(self, args):
        return handle_loss(args)

    def handle_command_rsv(self, args):
        return handle_rsv(args)

    def handle_command_log(self, args):
        return handle_log(args, self.session, self._telegram_document_sender())

    def handle_command_anss(self, args):
        return handle_anss(args, self.session)

    def handle_command_investor(self, args):
        return handle_investor(args, self.session, self._telegram_photo_sender())

    def _telegram_document_sender(self):
        """설정 화면에서 telegram_token/telegram_chat_id를 입력했을 때만 실제 전송자를 반환.

        미입력 시 None을 반환하면 log_command.py/investor_command.py가 파일 경로를
        텍스트로 그대로 보여주는 폴백 동작을 그대로 쓴다(terminal.py와 동일한 동작).
        """
        if not (self.telegram_token and self.telegram_chat_id):
            return None
        return lambda path, caption: send_document(
            path, caption, token=self.telegram_token, chat_id=self.telegram_chat_id
        )

    def _telegram_photo_sender(self):
        if not (self.telegram_token and self.telegram_chat_id):
            return None
        return lambda path, caption: send_photo(path, caption, token=self.telegram_token, chat_id=self.telegram_chat_id)

    def handle_command_api(self, args, interactive=False):
        """
        interactive=False(기본)는 _execute_all_commands의 일괄 실행/모니터 콜백처럼
        이미 확정되어 더 이상 사용자 응답을 받을 수 없는 흐름에서 쓰인다 — terminal.py의
        handle_command_api와 동일한 이유로 세션 생성을 막는다(주석 참고).
        실제 사용자가 '/api ...'를 직접 입력한 최상위 호출(_dispatch_direct)만
        interactive=True로 넘겨 선택 세션 생성을 허용한다.
        """
        session_mgr = get_session_manager() if interactive else None
        user_id = self.user_id if interactive else None
        return handle_api(args, self.session, session_mgr, user_id)

    def handle_command_gdcrs(self, args):
        return handle_gdcrs(args, self.session)

    def handle_command_ddcrs(self, args):
        return "ℹ️ ddcrs는 별도 설정 명령이 없습니다. /gdcrs intv 로 분봉 주기를 설정하면 gdcrs·ddcrs 모두에 적용됩니다.\n/start ddcrs 로 감시를 시작하세요."

    def handle_command_trst(self, args):
        return handle_trst(args)

    def handle_command_brk(self, args):
        return handle_brk(args, self.session, monitor=self.brk_monitor)

    def handle_command_wave(self, args):
        return handle_wave(args, self.session, monitor=self.wave_monitor)

    def handle_command_grid(self, args):
        return handle_grid(args, self.session, monitor=self.grid_monitor)

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

    # ── 저수준 직접 호출 (call/info/list, docs/api/md 명세 기반) — terminal.py와 동일 ──
    def handle_call(self, args):
        import json as _json

        if len(args) < 1:
            return "사용법: /call <API코드> ['<json>']"
        if not self.session.is_logged_in():
            return "❌ 먼저 설정 화면에서 로그인하세요."

        code = args[0].upper()
        spec = api_spec.load_api_spec(code)
        if spec is None:
            return f"❌ 알 수 없는 API 코드: {code} (/list 명령으로 전체 목록 확인)"

        raw_json = " ".join(args[1:]).strip() or "{}"
        try:
            overrides = _json.loads(raw_json)
        except _json.JSONDecodeError as e:
            return f"❌ JSON 파싱 오류: {e}"
        if not isinstance(overrides, dict):
            return '❌ JSON은 {"필드명":"값"} 형태의 객체여야 합니다.'

        valid_fields = {f.name_en for f in spec.fields}
        unknown = [k for k in overrides if k not in valid_fields]
        if unknown:
            return f"❌ 알 수 없는 파라미터: {', '.join(unknown)} (/info {code} 로 사용 가능한 필드를 확인하세요)"

        data_body = api_spec.full_blank_body(spec)
        data_body.update({k: str(v) for k, v in overrides.items()})

        result = api_spec.execute_api_call(spec, data_body, self.session.access_token, self.session.host_url)
        return _json.dumps(result, ensure_ascii=False, indent=2)

    def handle_info(self, args):
        if not args:
            return "사용법: /info <API코드>"
        spec = api_spec.load_api_spec(args[0])
        if spec is None:
            return f"❌ 알 수 없는 API 코드: {args[0]} (/list 명령으로 전체 목록 확인)"
        return api_spec.describe_spec(spec) + f'\n원하는 필드만 지정해 호출: /call {spec.code} {{"필드명":"값"}}'

    def handle_list(self, args):
        keyword = args[0] if args else None
        entries = api_spec.search_api_entries(keyword)
        if not entries:
            return f"검색 결과가 없습니다 (키워드: {keyword})" if keyword else "등록된 API가 없습니다."
        lines = [f"{e['code']:<10} {e['name']}  [{e['category']}]" for e in entries]
        lines.append(f"\n총 {len(entries)}건. '/info <API코드>'로 파라미터를 확인하세요.")
        return "\n".join(lines)

    # ── 진입점 ────────────────────────────────────────────────────────
    def process_command(self, text):
        """
        구분 기준은 오직 '/' 유무다 — terminal.py/telegram.py와 동일한 규칙.
        '/'로 시작하면 명확한 커맨드로 간주해 AI 없이 곧바로 실행하고, '/' 없이
        입력되면 자연어로 간주해 무조건 Claude로 변환 후 확인을 거친다.
        """
        text = text.strip()
        if not text:
            return None

        session_mgr = get_session_manager()
        if session_mgr.has_active_session(self.user_id):
            return self._handle_session_response(text, self.user_id, session_mgr.get_session(self.user_id))

        if text.startswith("/"):
            return self._dispatch_direct(text[1:])

        commands, error = convert_natural_to_commands(text, api_key=self.claude_api_key, model=self.claude_model)
        if commands:
            return self._handle_ai_commands(commands, self.user_id)
        if error:
            return f"❌ {error}"
        return f"❌ '{text}'를 이해하지 못했습니다. (/help 참고, 또는 자연어로 요청)"

    def _dispatch_direct(self, text):
        """'/'가 이미 벗겨진 명령어 문자열을 AI 없이 곧바로 실행한다."""
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


def _split_call_args(rest):
    """`call CODE '<json>'` 에서 CODE와 json 문자열을 분리."""
    rest = rest.strip()
    if not rest:
        return []
    return rest.split(maxsplit=1)
