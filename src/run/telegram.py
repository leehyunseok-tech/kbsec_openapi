"""
KB증권 API 텔레그램 봇.

운영: 텔레그램 폴링 기반 봇. 개발/테스트는 src/run/terminal.py를 사용하세요.

사용법:
  uv run python -m src.run.telegram   (또는 manage/run/run-telegram.bat / manage/run/run-telegram.sh)
"""

import sys
import time

from src.utils.console import force_utf8_streams
from src.utils.logging_config import setup_logging

force_utf8_streams()
setup_logging()

import schedule as schedule_lib

from src.commands.api_command import handle_api
from src.commands.brk_command import set_brk_monitor
from src.commands.command_meta import AUTOTRADE_FEATURE_ALIASES, AUTOTRADE_FEATURES_KR, korean_command_map
from src.commands.grid_command import set_grid_monitor
from src.commands.login_command import handle_login
from src.commands.registry import CommandContext, build_common_commands
from src.commands.wave_command import set_wave_monitor
from src.msgr.telegram.tel_receive import get_updates, parse_callback_query, parse_message
from src.msgr.telegram.tel_send import (
    answer_callback_query,
    send_document,
    send_message,
    send_message_with_buttons,
    send_photo,
)
from src.run.command_pipeline import CommandPipelineMixin
from src.utils.ai_command_converter import convert_natural_to_commands
from src.utils.brk_monitor import BrkMonitor
from src.utils.command_executor import (
    ApiCallPending,
    ApiNameSelectionPending,
    CommandPendingExecution,
    StockSelectionPending,
    get_session_manager,
)
from src.utils.dead_cross_monitor import DeadCrossMonitor
from src.utils.direct_api_command import execute_direct_command, resolve_direct_command
from src.utils.golden_cross_monitor import GoldenCrossMonitor
from src.utils.grid_monitor import GridMonitor
from src.utils.holdings_monitor import HoldingsMonitor
from src.utils.schedule_manager import ScheduleManager
from src.utils.session import SessionManager
from src.utils.stoploss_manager import StopLossManager
from src.utils.trailing_stop_monitor import TrailingStopMonitor
from src.utils.wave_monitor import WaveMonitor

_AUTOTRADE_FEATURES = ("stls", "gdcrs", "ddcrs", "trst", "hold", "brk", "wave", "grid")

HELP_TEXT = """🤖 KB증권 Open API Agent - 사용 가능한 명령어

ℹ️  / 로 시작하면 아래 명령어로 즉시 실행되고, / 없이 입력하면 자연어로 인식되어
   AI가 명령어로 변환한 뒤 확인을 거쳐 실행됩니다 (예: "KB금융 10주 사줘").
   명령어는 한글이 기본이며, 기존 영문 명령(srch/buy 등)도 그대로 사용할 수 있습니다.

━━━━━━━━━━━━━━━
📝 인증 및 상태
/login real            로그인 (운영환경 — KB증권 개발환경(모의투자)은 아직 미제공)
/상태                  현재 로그인 상태 확인

━━━━━━━━━━━━━━━
📊 조회
/종목정보 {종목코드}    종목 현재가/기본정보 조회 (예: /종목정보 105560)
/순위                  상위 종목 랭킹 메뉴
/순위 {1~4}            거래대금/등락률/거래량/업종 상위
/잔고                  계좌 현황(보유종목+미체결) 조회
/종목마스터            종목마스터 로드 현황
/종목검색 {키워드}      종목명 키워드 검색 (예: /종목검색 KB금융)

━━━━━━━━━━━━━━━
💰 매매
/매수 {종목코드} {수량}                시장가 매수
/매수 {종목코드} {수량} {지정가}       지정가 매수
/매수 {종목코드} max {금액}            금액 범위 내 최대 매수
/매도 all                             보유 전체 종목 시장가 매도
/매도 {종목코드}                      전량 매도 (시장가)
/매도 {종목코드} {수량} [{지정가}]    수량 지정 매도
/취소 pend                            미체결 주문 전체 취소

━━━━━━━━━━━━━━━
⚙️  설정
/장시간 [{시작} {종료}]  장 시간 조회/설정
/익절 [{퍼센티지}]      익절 기준 조회/설정
/손절 [{퍼센티지}]      손절 기준 조회/설정
/타임아웃 {초} cancel|market  주문 타임아웃 설정
/쿨다운 {시간}          매도 후 재매수 금지 시간
/금지종목 add|list|remove  매매 금지 종목 관리
/최대보유 {개수}        최대 보유 종목 수
/설정                  전체 설정값 조회

━━━━━━━━━━━━━━━
📅 예약 / 기록
/예약 {시간} {명령어}   매일 반복 예약
/예약 once {시간} {명령어}  한 번만 예약
/예약 list / remove     예약 조회/삭제
/체결기록 [{일수}]      체결 내역 CSV 파일 전송
/분석 [{일수}]          체결 내역 AI 분석 (Claude)
/투자자 {종목코드} {개월수}  투자자별 누적 순매수 차트

━━━━━━━━━━━━━━━
🔧 API 직접호출 (개발자용 — 영문 유지)
/api {API코드}          docs/api/md 명세 기반 API 직접 호출
/api info {API코드}     실행 전 파라미터 미리보기, 실행하지 않음
/api list [키워드]      코드/API명/업무구분으로 검색

━━━━━━━━━━━━━━━
🤖 자동매매 (폴링 기반, 09:00~15:30)
/골든크로스 intv|add|list|remove|clear   골든크로스 설정
/데드크로스                             데드크로스 (설정은 골든크로스 분봉 공유)
/트레일링 [{하락율} {최소수익률}]        트레일링 스탑 설정
/돌파매수 rate|add|list|remove          돌파매수 설정
/분할매매 set|view|add|list|remove      분할매매 설정
/그리드 add|list|remove                 그리드 트레이딩 설정
/감시시작 {전략}        감시 시작 (전략: 골든크로스|데드크로스|트레일링|돌파매수|분할매매|그리드|손절매|보유감시)
/감시중단 {전략}        감시 중단
※ 조건검색식 실시간거래(jggs)·VI감시(vi)·테마(theme)·공매도(short/loan)는
   KB API에 대응 API가 없어 지원하지 않습니다.

━━━━━━━━━━━━━━━
🛠️  기타
/도움말                도움말 표시
/종료                  봇 종료 (터미널/텔레그램)

💡 자연어 입력도 지원합니다 (Claude API 키 설정 시).
예: "KB금융 10주 사줘"
━━━━━━━━━━━━━━━
"""


class _TelegramContext(CommandContext):
    """텔레그램 클라이언트가 공용 명령 핸들러에 넘길 의존성.

    문서/사진은 텔레그램 전송 함수를 그대로 쓰고, 모니터는 프로세스당 하나뿐이라
    전역 싱글턴에 맡긴다(None 반환 = 핸들러가 set_*_monitor로 등록된 것을 사용).
    """

    def __init__(self, bot):
        super().__init__(bot.session)
        self._bot = bot

    @property
    def document_sender(self):
        return send_document

    @property
    def photo_sender(self):
        return send_photo

    @property
    def execute_command(self):
        # rank가 하위 명령을 실행할 때 사용 — 이미 확정된 문자열이라 AI를 거치지 않는다.
        return lambda text, chat_id=None: self._bot._dispatch_direct(text)


class TelegramBot(CommandPipelineMixin):
    """텔레그램 명령어 기반 KB증권 Open API Agent.

    AI 자연어 변환 이후의 처리(종목명/API명 해석, 선택/확인 세션, 일괄 실행)는
    terminal.py와 공유하는 CommandPipelineMixin(src/run/command_pipeline.py)에 있다.
    """

    def __init__(self):
        self.session = SessionManager()
        self.offset = 0

        # 돌파매수/분할매매/그리드는 명령(add/list/remove)이 감시 시작 전에도 필요하므로
        # 시작 시점에 즉시 생성하고 싱글턴으로 등록해둔다.
        self.brk_monitor = BrkMonitor(self.session, self._execute_monitor_command, send_message)
        set_brk_monitor(self.brk_monitor)
        self.wave_monitor = WaveMonitor(self.session, self._execute_monitor_command, send_message)
        set_wave_monitor(self.wave_monitor)
        self.grid_monitor = GridMonitor(self.session, self._execute_monitor_command, send_message)
        set_grid_monitor(self.grid_monitor)

        # gdcrs/ddcrs/trst/stls/hold는 설정만 존재하면 되고 모니터 인스턴스는
        # start 시점에 지연 생성한다.
        self.gdcrs_monitor = None
        self.ddcrs_monitor = None
        self.trst_monitor = None
        self.stls_monitor = None
        self.hold_monitor = None

        # 공용 명령은 src/commands/registry.py 한 곳에 선언돼 있고, 세 클라이언트가
        # 그대로 가져다 쓴다 — 예전처럼 클라이언트마다 위임 래퍼를 복사하지 않는다.
        self.commands = build_common_commands(_TelegramContext(self))
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
        self.last_executed_schedules = {}

    def handle_command_login(self, args):
        return handle_login(args, self.session)

    def handle_command_help(self, args):
        return HELP_TEXT.strip()

    def handle_command_api(self, args, chat_id=None):
        return handle_api(args, self.session, get_session_manager(), chat_id)

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
                self.hold_monitor = HoldingsMonitor(self.session, send_message)
            monitor = self.hold_monitor
        else:
            return f"❌ 알 수 없는 전략: {feature}"

        return monitor.start() if action == "start" else monitor.stop()

    def handle_command_power(self, args):
        if not args or args[0].lower() != "off":
            return "사용법: /power off  (또는 /종료)"
        send_message("👋 봇이 종료됩니다.")
        sys.exit(0)

    def handle_command_quit(self, args):
        """/종료 — 인자 없이 즉시 종료. (오작동 방지 가드가 있는 /power off 와 별개 진입점)"""
        send_message("👋 봇이 종료됩니다.")
        sys.exit(0)

    def process_command(self, text, chat_id):
        """
        텍스트 명령어 처리 (명령어 또는 자연어)

        구분 기준은 오직 '/' 유무다 — '/'로 시작하면 명확한 커맨드로 간주해 AI 없이
        곧바로 실행하고(예: `/buy 005930 10`), '/' 없이 입력되면 자연어로 간주해
        무조건 Claude로 변환 후 확인을 거친다(예: "삼성전자 10주 주문해줘"). 명령어와
        같은 단어로 시작한다고 해서 직접 실행되지 않는다 — 애매함을 없애기 위해서다.

        순서: 1) 활성 확인/선택 세션 있으면 그 응답으로 처리
              2) '/'면 즉시 실행 3) 그 외는 Claude로 변환 후 확인 요청
        """
        text = text.strip()
        if not text:
            return "명령어를 입력하세요. /help를 입력하면 도움말을 볼 수 있습니다."

        session_mgr = get_session_manager()
        if session_mgr.has_active_session(chat_id):
            return self._handle_session_response(text, chat_id, session_mgr.get_session(chat_id))

        if text.startswith("/"):
            return self._dispatch_direct(text[1:], chat_id)

        commands, error = convert_natural_to_commands(text)
        if commands:
            return self._handle_ai_commands(commands, chat_id)
        if error:
            return f"❌ {error}"
        return f"❌ '{text}'를 이해하지 못했습니다.\n\n💡 팁: /help로 명령어를 확인하거나, 자연어로 요청하세요.\n예: 'KB금융 10주 사줘'"

    def _buttons_for_session(self, session):
        """
        활성 세션 타입에 맞는 인라인 키보드 버튼 구성을 만든다.
        list[list[(라벨, callback_data)]] — 바깥 리스트의 각 항목이 버튼 한 줄(row).

        선택 세션(StockSelectionPending/ApiNameSelectionPending/ApiCallPending)은
        candidates/필드 선택지가 전부 title()/option_labels()로 균일하게 노출되므로
        (src/utils/command_executor.py) 여기서 세 타입을 따로 다룰 필요가 없다.
        """
        if isinstance(session, CommandPendingExecution):
            return [[("✅ 실행", "confirm:yes"), ("❌ 취소", "confirm:no")]]
        if isinstance(session, (StockSelectionPending, ApiNameSelectionPending, ApiCallPending)):
            labels = session.option_labels()
            rows = [[(f"{i + 1}. {label}", f"select:{i + 1}")] for i, label in enumerate(labels)]
            rows.append([("❌ 취소", "select:cancel")])
            return rows
        return None

    @staticmethod
    def _callback_data_to_text(data):
        """
        인라인 버튼 callback_data를 텍스트 기반 세션 처리 로직
        (command_pipeline.py의 _handle_session_response 등)이 이해하는 문자열로 변환.
        """
        if data == "confirm:yes":
            return "y"
        if data == "confirm:no":
            return "n"
        if data.startswith("select:"):
            value = data[len("select:") :]
            return value if value != "cancel" else "취소"
        return ""

    def _send_response(self, chat_id, response_text):
        """응답을 전송한다 — 이 응답으로 확인/선택 세션이 열려 있으면 인라인 버튼을 붙인다."""
        if not response_text:
            return
        print(f"[응답]\n{response_text}\n", flush=True)

        session_mgr = get_session_manager()
        if session_mgr.has_active_session(chat_id):
            buttons = self._buttons_for_session(session_mgr.get_session(chat_id))
            if buttons:
                send_message_with_buttons(response_text, buttons)
                return
        send_message(response_text)

    def _dispatch_direct(self, text, chat_id=None):
        """
        '/'가 이미 벗겨진 명령어 문자열을 AI 없이 곧바로 실행한다.

        process_command의 '/' 분기뿐 아니라, rsv 예약 재실행처럼 이미 완전히
        해석된 문자열을 신뢰하고 즉시 실행해야 하는 내부 호출에서도 사용한다.
        chat_id는 '/api'가 선택 대기 세션을 열 때만 필요 — rsv/모니터 등 내부
        호출에는 없어도 되고(그 경우 선택 필요한 API는 대화형 세션 없이 안내만 반환),
        process_command에서 들어온 실제 사용자 메시지에서만 채워진다.
        """
        parts = text.split()
        if not parts:
            return "❌ 명령어를 입력하세요. /help를 입력하면 도움말을 볼 수 있습니다."
        command, args = parts[0].lower(), parts[1:]
        if command == "api":
            return self.handle_command_api(args, chat_id)
        if command in self.commands:
            return self.commands[command](args)

        direct_entry = resolve_direct_command(command)
        if direct_entry is not None:
            if not self.session.is_logged_in():
                return "❌ 로그인이 필요합니다. /login real 을 먼저 실행하세요."
            return execute_direct_command(direct_entry, args, self.session.access_token, self.session.host_url)

        return f"❌ 알 수 없는 명령어: /{command}\n\n/help로 명령어를 확인하세요."

    def _execute_scheduled_commands(self):
        """schedule_manager에 등록된 오늘 예약 명령을 시각이 되면 실행."""
        from datetime import datetime

        today_schedules = ScheduleManager.get_today_schedules()
        if not today_schedules:
            return
        current_time = datetime.now()

        for schedule_item in today_schedules:
            schedule_id = schedule_item.get("id")
            command = schedule_item.get("command")
            repeat_type = schedule_item.get("repeat_type", "daily")

            if not ScheduleManager.should_execute_schedule(schedule_item, current_time):
                continue
            last_executed = self.last_executed_schedules.get(schedule_id)
            if last_executed and last_executed.strftime("%H:%M") == current_time.strftime("%H:%M"):
                continue

            print(f"\n[예약 실행] #{schedule_id} {command}", flush=True)
            response_text = self._dispatch_direct(command)
            if response_text:
                send_message(f"🔔 예약 실행 (#{schedule_id})\n명령어: {command}\n\n{response_text}")

            self.last_executed_schedules[schedule_id] = current_time
            if repeat_type == "once":
                ScheduleManager.remove_schedule(schedule_id)

    def _daily_report_job(self):
        from datetime import datetime

        from src.utils import trade_logger

        if datetime.now().weekday() >= 5:
            return
        try:
            send_message(trade_logger.generate_summary())
        except Exception as e:
            print(f"[일일보고] 오류: {e}", flush=True)

    def run(self):
        """봇 실행 - 메시지 수신 루프"""
        print("=" * 60, flush=True)
        print("[KB증권 Open API Agent 시작]", flush=True)
        print("=" * 60, flush=True)

        # 봇 시작 알림 텔레그램 메시지
        # 주의: KB증권 개발환경(모의투자)은 아직 제공되지 않아 운영환경(실거래)으로만 로그인한다.
        # 실제 계좌로 주문이 나갈 수 있으니 자동매매 설정을 시작하기 전에 반드시 확인할 것.
        startup_message = """🚀 자동매매 봇이 시작되었습니다!

환경: 운영환경 (실거래)
상태: 로그인 중...

/help 명령으로 사용 가능한 명령어를 확인하세요."""

        send_result = send_message(startup_message)
        if send_result["success"]:
            print("[시작 알림] 텔레그램 전송 성공", flush=True)
        else:
            print("[시작 알림] 텔레그램 전송 실패", flush=True)

        # 일일 거래 보고 스케줄 등록 (15:31)
        print("[스케줄] 일일 거래 보고 15:31 등록", flush=True)
        schedule_lib.every().day.at("15:31").do(self._daily_report_job)

        # 운영환경으로 자동 로그인 (KB증권 개발환경/모의투자는 미제공)
        print("[자동 로그인] 운영환경으로 로그인 시도...", flush=True)
        login_result = self.handle_command_login(["real"])

        if self.session.is_logged_in():
            login_message = f"""✅ 운영환경 로그인 성공!

{login_result}

이제 명령어를 사용할 수 있습니다."""
            send_message(login_message)
            print("[자동 로그인] 성공", flush=True)

            # 참고: KB증권 API는 실시간 웹소켓을 제공하지 않는다 (docs/features.md 참고).
            # 트레일링스탑/자동손절 등은 REST 폴링(utils/monitor_base.py)으로 처리하므로
            # 이 자리에는 아직 아무것도 없다. KB가 추후 실시간 API를 제공하면 여기서
            # WebSocketClient 연결 + 백그라운드 스레드 시작 로직을 추가한다.
        else:
            login_message = f"""❌ 운영환경 로그인 실패

{login_result}

수동으로 로그인해주세요: /login real"""
            send_message(login_message)
            print("[자동 로그인] 실패", flush=True)

        print("\n메시지를 기다리는 중...", flush=True)
        while True:
            try:
                schedule_lib.run_pending()
                self._execute_scheduled_commands()

                response = get_updates(self.offset)
                if response.get("ok"):
                    updates = response.get("result", [])
                    for update in updates:
                        callback = parse_callback_query(update)
                        if callback:
                            data, chat_id, sender = callback["data"], callback["chat_id"], callback["sender"]
                            print(f"\n{'=' * 60}\n[버튼] {sender}: {data}\n{'=' * 60}", flush=True)
                            answer_callback_query(callback["callback_query_id"])
                            response_text = self.process_command(self._callback_data_to_text(data), chat_id)
                            self._send_response(chat_id, response_text)
                            continue

                        parsed = parse_message(update)
                        if not parsed:
                            continue
                        text, chat_id, sender = parsed["text"], parsed["chat_id"], parsed["sender"]
                        print(f"\n{'=' * 60}\n[수신] {sender}: {text}\n{'=' * 60}", flush=True)

                        response_text = self.process_command(text, chat_id)
                        self._send_response(chat_id, response_text)

                    if updates:
                        self.offset = updates[-1]["update_id"] + 1
                else:
                    time.sleep(0.5)
            except Exception as e:
                print(f"[메시지 수신] 오류: {str(e)}", flush=True)
                time.sleep(0.5)


def main():
    bot = TelegramBot()
    bot.run()


if __name__ == "__main__":
    main()
