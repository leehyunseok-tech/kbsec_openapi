"""
터미널 대화형 입력 — Enter 확인 / 화살표+숫자 선택 메뉴.

run-terminal.*로 실행하는 실제 대화형 세션(raw 키 입력이 가능한 TTY) 기준으로
동작한다. stdin/stdout이 파이프·리다이렉트된 비대화형 환경(테스트, 스크립트 실행
등)에서는 각 함수가 자동으로 줄 단위 input() 기반 폴백으로 전환된다 — 빈 줄
Enter는 확인(True)으로, 그 외 텍스트 응답은 취소로 처리하고, 선택 메뉴는 번호를
그대로 입력받는다.
"""

import sys

_ESC = "\x1b"


def _is_interactive_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


if sys.platform == "win32":
    import msvcrt

    def _enable_vt_mode():
        """Windows 콘솔에서 ANSI(VT100) 이스케이프 시퀀스를 해석하도록 활성화."""
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING

    def _read_key() -> str:
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):  # 화살표/기능키 접두 바이트
            ch2 = msvcrt.getch()
            return {b"H": "UP", b"P": "DOWN", b"K": "LEFT", b"M": "RIGHT"}.get(ch2, "")
        if ch == b"\r":
            return "ENTER"
        if ch == b"\x1b":
            return "ESC"
        if ch == b"\x03":
            raise KeyboardInterrupt
        if ch in (b"\x08",):
            return "BACKSPACE"
        try:
            return ch.decode("utf-8")
        except UnicodeDecodeError:
            return ""

else:
    import termios
    import tty

    def _enable_vt_mode():
        pass  # Unix 터미널은 기본적으로 ANSI를 지원

    def _read_key() -> str:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == _ESC:
                rest = sys.stdin.read(2)
                return {"[A": "UP", "[B": "DOWN", "[D": "LEFT", "[C": "RIGHT"}.get(rest, "ESC")
            if ch in ("\r", "\n"):
                return "ENTER"
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch in ("\x7f", "\x08"):
                return "BACKSPACE"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def confirm_prompt(hint: str = "[Enter] 실행   [다른 키] 취소") -> bool:
    """Enter 키를 누르면 True(실행), 그 외 키를 누르면 False(취소).

    비대화형 환경에서는 빈 줄(Enter만 입력)이면 True, 그 외 텍스트 응답은 False.
    """
    if not _is_interactive_tty():
        return input().strip() == ""

    _enable_vt_mode()
    print(hint)
    key = _read_key()
    return key == "ENTER"


def select_from_list(options, title: str = ""):
    """
    화살표 위/아래로 이동, Enter로 확정, 숫자를 입력해 바로 그 번호로 이동(여러
    자리 숫자도 계속 입력 가능, Enter로 최종 확정)하는 대화형 메뉴.

    반환: 선택된 0-based 인덱스. 취소(Esc)하면 None.
    비대화형 환경에서는 번호를 텍스트로 입력받는 폴백으로 전환된다(유효하지 않으면 None).
    """
    if not options:
        return None

    if not _is_interactive_tty():
        for i, opt in enumerate(options, 1):
            print(f"{i}. {opt}")
        raw = input().strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        return None

    _enable_vt_mode()
    if title:
        print(title)

    idx = 0
    n = len(options)
    typed = ""

    def _render(first: bool):
        if not first:
            sys.stdout.write(f"\033[{n + 1}A")
        for i, opt in enumerate(options):
            marker = "▶" if i == idx else " "
            sys.stdout.write(f"\033[2K\r{marker} {i + 1}. {opt}\n")
        hint = "↑↓ 이동, Enter 확인, 숫자로 바로 선택, Esc 취소"
        if typed:
            hint += f"   (입력: {typed})"
        sys.stdout.write(f"\033[2K\r{hint}\n")
        sys.stdout.flush()

    _render(first=True)

    while True:
        key = _read_key()
        if key == "UP":
            typed = ""
            idx = (idx - 1) % n
        elif key == "DOWN":
            typed = ""
            idx = (idx + 1) % n
        elif key == "ENTER":
            if typed:
                choice = int(typed) - 1
                if 0 <= choice < n:
                    return choice
                typed = ""
            else:
                return idx
        elif key == "ESC":
            return None
        elif key == "BACKSPACE":
            typed = typed[:-1]
            if typed:
                idx = int(typed) - 1
        elif key.isdigit():
            candidate = typed + key
            if 1 <= int(candidate) <= n:
                typed = candidate
                idx = int(candidate) - 1
            # 범위를 넘어서는 숫자는 오타로 보고 무시(버퍼 유지)
        _render(first=False)
