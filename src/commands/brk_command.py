"""brk 명령 처리 - 돌파매수 감시 관리."""

_brk_monitor = None


def set_brk_monitor(monitor):
    global _brk_monitor
    _brk_monitor = monitor


def handle_brk(args, session, monitor=None):
    # monitor 인자는 다중 인스턴스 클라이언트(src/web/client.py — 웹 세션마다 모니터가
    # 따로 있음)가 자기 것을 명시적으로 넘기기 위한 것. 생략하면 set_brk_monitor로
    # 등록된 프로세스 전역 모니터를 쓴다(main.py/terminal.py — 프로세스당 1개라 충분).
    monitor = monitor if monitor is not None else _brk_monitor
    if not args:
        return _usage()

    sub = args[0].lower()

    if sub == "rate":
        if len(args) < 2:
            if monitor:
                return f"현재 돌파 기준 상승률: +{monitor.get_rate():.1f}%\n변경: brk rate {{상승률}}"
            return "❌ 사용법: brk rate {상승률}"
        try:
            rate = float(args[1])
        except ValueError:
            return "❌ 상승률은 숫자로 입력하세요. 예: brk rate 3.5"
        if monitor is None:
            return "❌ 내부 오류: 모니터가 초기화되지 않았습니다."
        return monitor.set_rate(rate)

    if sub == "list":
        return monitor.get_list_text() if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "remove":
        if len(args) < 2:
            return "❌ 사용법: brk remove {일련번호}"
        try:
            idx = int(args[1])
        except ValueError:
            return "❌ 일련번호는 숫자로 입력하세요."
        return monitor.remove(idx) if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "add":
        if len(args) < 3:
            return "❌ 사용법: brk add {종목코드} {명령어}\n예: brk add 005930 buy 005930 10"
        stk_cd = args[1]
        if not (stk_cd.isdigit() and len(stk_cd) == 6):
            return "❌ 종목코드는 6자리 숫자여야 합니다."
        command = " ".join(args[2:])
        return monitor.add(stk_cd, command) if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    return _usage()


def _usage():
    return """📋 돌파매수 감시 명령어

돌파매수 rate {상승률}            기준 상승률 설정 (예: 돌파매수 rate 3.5)
돌파매수 add {종목코드} {명령어}  감시 종목 추가 (예: 돌파매수 add 005930 매수 005930 10)
돌파매수 list                     감시 목록 조회
돌파매수 remove {일련번호}        항목 제거
감시시작 돌파매수                 감시 시작
감시중단 돌파매수                 감시 중단"""
