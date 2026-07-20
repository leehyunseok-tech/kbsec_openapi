"""wave 명령 처리 - 분할매매 관리."""

_wave_monitor = None


def set_wave_monitor(monitor):
    global _wave_monitor
    _wave_monitor = monitor


def handle_wave(args, session, monitor=None):
    # monitor 인자는 다중 인스턴스 클라이언트(src/web/client.py — 웹 세션마다 모니터가
    # 따로 있음)가 자기 것을 명시적으로 넘기기 위한 것. 생략하면 set_wave_monitor로
    # 등록된 프로세스 전역 모니터를 쓴다(main.py/terminal.py — 프로세스당 1개라 충분).
    monitor = monitor if monitor is not None else _wave_monitor
    if not args:
        return _usage()

    sub = args[0].lower()

    if sub == "set":
        if len(args) < 9 or args[1].lower() != "buy" or args[5].lower() != "sell":
            return "❌ 사용법: wave set buy {a} {b} {c} sell {d} {e} {f}\n예: wave set buy 3 6 2 sell 3 6 2"
        try:
            a, b, c = float(args[2]), float(args[3]), float(args[4])
            d, e, f = float(args[6]), float(args[7]), float(args[8])
        except (ValueError, IndexError):
            return "❌ 퍼센티지 값은 숫자로 입력하세요."
        if min(a, b, c, d, e, f) <= 0:
            return "❌ 모든 퍼센티지는 0보다 커야 합니다."
        return monitor.set_config(a, b, c, d, e, f) if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "view":
        return monitor.get_config_text() if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "add":
        if len(args) < 3:
            return "❌ 사용법: wave add {종목코드} {투자금액}\n예: wave add 005930 1000000"
        stk_cd = args[1]
        if not (stk_cd.isdigit() and len(stk_cd) == 6):
            return "❌ 종목코드는 6자리 숫자여야 합니다."
        try:
            total_amount = int(args[2])
        except ValueError:
            return "❌ 투자금액은 숫자로 입력하세요."
        if total_amount < 3:
            return "❌ 투자금액은 3 이상이어야 합니다 (3단계 분할 필요)."
        return monitor.add(stk_cd, total_amount) if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "list":
        return monitor.get_list_text() if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "remove":
        if len(args) < 2:
            return "❌ 사용법: wave remove {일련번호}"
        try:
            idx = int(args[1])
        except ValueError:
            return "❌ 일련번호는 숫자로 입력하세요."
        return monitor.remove(idx) if monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    return _usage()


def _usage():
    return """📋 분할매매 명령어

분할매매 set buy {a} {b} {c} sell {d} {e} {f}   퍼센티지 설정
  예: 분할매매 set buy 3 6 2 sell 3 6 2
분할매매 view                                     설정 조회
분할매매 add {종목코드} {투자금액}               감시 종목 추가
분할매매 list                                     목록 조회
분할매매 remove {일련번호}                        항목 제거
감시시작 분할매매                                 감시 시작
감시중단 분할매매                                 감시 중단"""
