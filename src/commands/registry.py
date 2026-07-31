"""
명령 등록의 단일 소스 — 트리플 클라이언트(telegram/terminal/web) 공용.

## 왜 필요한가

세 클라이언트는 `src/commands/*.py`의 같은 핸들러를 호출하는데, 예전에는 각 클라이언트가
`handle_command_srch(self, args): return handle_srch(args, self.session)` 형태의 래퍼
메서드를 **각자 34개씩, 총 100개 가까이** 들고 있었다. 내용은 대부분 바이트 단위로
동일했고, 그래서 명령을 하나 추가할 때마다 세 파일을 똑같이 고쳐야 했다(CLAUDE.md의
"필수 규칙 7단계"가 이 수작업을 강제하는 규칙이었다). 한 곳만 빠뜨리면 그 클라이언트에서만
명령이 사라지는 드리프트가 생긴다.

## 어떻게 해결하는가

명령을 **선언적으로** 한 번만 적고(`COMMON_COMMANDS`), 클라이언트마다 다른 부분은
`CommandContext`가 제공하는 의존성으로 주입한다. 핸들러들의 선택 파라미터가 모두
`None` 기본값이라(`handle_log(args, session, send_document_fn=None)` 등) 값을 못 주는
클라이언트는 `None`을 넘기면 되고, 이는 인자를 생략한 것과 동작이 같다.

클라이언트는 이제 다음 한 줄이면 공용 명령 전체를 얻는다:

    self.commands = build_common_commands(ctx)

진짜로 클라이언트마다 다른 명령(login/help/power/종료/api)만 각자 등록한다 — 아래
`CLIENT_SPECIFIC` 주석 참고.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from src.commands.anss_command import handle_anss
from src.commands.blacklist_command import handle_blacklist
from src.commands.brk_command import handle_brk
from src.commands.buy_command import handle_buy
from src.commands.ccl_command import handle_ccl
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

DDCRS_NOTICE = (
    "ℹ️ ddcrs는 별도 설정 명령이 없습니다. /gdcrs intv 로 분봉 주기를 설정하면 "
    "gdcrs·ddcrs 모두에 적용됩니다.\n/start ddcrs 로 감시를 시작하세요."
)


class CommandContext:
    """클라이언트가 명령 핸들러에 넘길 의존성 모음.

    각 클라이언트는 이 클래스를 상속해 자기 사정에 맞게 property를 덮어쓴다.
    기본값은 "그 기능이 없음"(None)이며, 핸들러들이 모두 None을 허용하므로 안전하다.
    """

    def __init__(self, session):
        self.session = session

    # 파일/사진 전송 — 텔레그램은 전송 함수, 웹은 자기 세션의 전송기, 터미널은 없음(None).
    @property
    def document_sender(self) -> Callable | None:
        return None

    @property
    def photo_sender(self) -> Callable | None:
        return None

    # 명령 문자열을 다시 실행하는 콜백 (rank 등이 하위 명령을 실행할 때 사용).
    @property
    def execute_command(self) -> Callable | None:
        return None

    def monitor(self, name: str):
        """brk/wave/grid 모니터 인스턴스. None이면 핸들러가 전역 싱글턴을 쓴다.

        웹은 브라우저 세션마다 모니터가 따로라 반드시 자기 것을 넘겨야 하고
        (전역 싱글턴을 쓰면 마지막 접속자가 다른 사용자 명령을 가로챈다),
        텔레그램/터미널은 프로세스당 하나뿐이라 전역 방식을 그대로 쓴다.
        """
        return None


@dataclass(frozen=True)
class CommandSpec:
    """명령 하나의 선언. `bind()`가 컨텍스트를 묶어 실제 호출 함수를 만든다."""

    name: str
    # constant를 쓰는 안내 전용 명령은 핸들러가 없다.
    handler: Callable | None = None
    # 컨텍스트에서 가져와 위치 인자로 넘길 항목들 ("session" → ctx.session).
    needs: Sequence[str] = ()
    # 컨텍스트에서 가져와 키워드 인자로 넘길 항목들 ({"monitor": "brk"} → monitor=ctx.monitor("brk")).
    monitor_kwarg: str | None = None
    # 핸들러 호출 없이 고정 문자열만 반환하는 명령(ddcrs 안내 등).
    constant: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.constant is None and self.handler is None:
            raise ValueError(f"{self.name}: handler 또는 constant 중 하나는 있어야 합니다")

    def bind(self, ctx: CommandContext) -> Callable:
        if self.constant is not None:
            constant = self.constant
            return lambda args: constant

        def run(args):
            positional = [_resolve(ctx, need) for need in self.needs]
            kwargs = {}
            if self.monitor_kwarg:
                kwargs["monitor"] = ctx.monitor(self.monitor_kwarg)
            return self.handler(args, *positional, **kwargs)

        run.__name__ = f"command_{self.name}"
        run.__doc__ = f"'{self.name}' 명령 — {self.handler.__name__}() 위임"
        return run


def _resolve(ctx: CommandContext, need: str):
    if need == "session":
        return ctx.session
    if need == "document_sender":
        return ctx.document_sender
    if need == "photo_sender":
        return ctx.photo_sender
    if need == "execute_command":
        return ctx.execute_command
    raise KeyError(f"알 수 없는 컨텍스트 의존성: {need!r}")


# ── 세 클라이언트가 완전히 동일하게 쓰는 명령들 ──────────────────────────────
#
# 여기에 한 줄 추가하면 telegram/terminal/web 세 곳에 동시에 등록된다.
# (CLAUDE.md 필수 규칙의 2·3·4번이 이 한 줄로 대체된다.)
COMMON_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("status", handle_status, needs=("session",)),
    CommandSpec("srch", handle_srch, needs=("session",)),
    CommandSpec("rank", handle_rank, needs=("session", "execute_command")),
    CommandSpec("buy", handle_buy, needs=("session",)),
    CommandSpec("sell", handle_sell, needs=("session",)),
    CommandSpec("ccl", handle_ccl, needs=("session",)),
    CommandSpec("report", handle_report, needs=("session",), aliases=("r",)),
    CommandSpec("mst", handle_mst, needs=("session",)),
    CommandSpec("stcd", handle_stcd, needs=("session",)),
    CommandSpec("mkhr", handle_mkhr),
    CommandSpec("stts", handle_stts),
    CommandSpec("time", handle_time),
    CommandSpec("cooldown", handle_cooldown),
    CommandSpec("blacklist", handle_blacklist),
    CommandSpec("mxhold", handle_mxhold),
    CommandSpec("익절", handle_profit),
    CommandSpec("손절", handle_loss),
    CommandSpec("rsv", handle_rsv),
    CommandSpec("log", handle_log, needs=("session", "document_sender")),
    CommandSpec("anss", handle_anss, needs=("session",)),
    CommandSpec("investor", handle_investor, needs=("session", "photo_sender")),
    CommandSpec("gdcrs", handle_gdcrs, needs=("session",)),
    CommandSpec("ddcrs", constant=DDCRS_NOTICE),
    CommandSpec("trst", handle_trst),
    CommandSpec("brk", handle_brk, needs=("session",), monitor_kwarg="brk"),
    CommandSpec("wave", handle_wave, needs=("session",), monitor_kwarg="wave"),
    CommandSpec("grid", handle_grid, needs=("session",), monitor_kwarg="grid"),
)

# ── 클라이언트별로 다르게 등록해야 하는 명령 (각 클라이언트가 직접 등록) ──────
#
#   login   telegram/terminal은 handle_login, 웹은 설정 화면 안내 문구만 반환
#   help    telegram은 HELP_TEXT, terminal/web은 HELP_TEXT + 저수준 도움말
#   api     선택 세션 생성 여부(interactive)와 user_id 취급이 클라이언트마다 다름
#   start   / stop   각 클라이언트의 _dispatch_monitor에 위임 (모니터 보유 주체가 다름)
#   power   / 종료   telegram은 프로세스 종료, terminal은 루프 종료 플래그, 웹은 미지원
CLIENT_SPECIFIC = ("login", "help", "api", "start", "stop", "power", "종료")


def build_common_commands(ctx: CommandContext) -> dict[str, Callable]:
    """공용 명령 전체를 {이름: 호출가능} 딕셔너리로 만든다 (별칭 포함)."""
    commands: dict[str, Callable] = {}
    for spec in COMMON_COMMANDS:
        bound = spec.bind(ctx)
        commands[spec.name] = bound
        for alias in spec.aliases:
            commands[alias] = bound
    return commands
