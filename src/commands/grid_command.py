"""grid 명령 처리 - 그리드 트레이딩 관리."""

_grid_monitor = None


def set_grid_monitor(monitor):
    global _grid_monitor
    _grid_monitor = monitor


def handle_grid(args, session):
    if not args:
        return _usage()

    sub = args[0].lower()

    if sub == "add":
        if len(args) < 6:
            return "❌ 사용법: grid add {종목코드} {기준가} {간격} {주문금액} {최대단계}\n예: grid add 005930 75000 2 100000 3"
        stk_cd = args[1]
        if not (stk_cd.isdigit() and len(stk_cd) == 6):
            return "❌ 종목코드는 6자리 숫자여야 합니다."
        try:
            base_price = float(args[2])
            interval = float(args[3])
            order_amount = int(args[4])
            max_stages = int(args[5])
        except (ValueError, IndexError):
            return "❌ 값을 확인하세요. 기준가, 간격, 주문금액, 최대단계는 숫자로 입력합니다."
        if base_price <= 0 or interval <= 0 or order_amount <= 0:
            return "❌ 기준가/간격/주문금액은 0보다 커야 합니다."
        if not (1 <= max_stages <= 10):
            return "❌ 최대단계는 1~10 사이여야 합니다."
        return _grid_monitor.add(stk_cd, base_price, interval, order_amount, max_stages) if _grid_monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "list":
        return _grid_monitor.get_list_text() if _grid_monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    if sub == "remove":
        if len(args) < 2:
            return "❌ 사용법: grid remove {일련번호}"
        try:
            idx = int(args[1])
        except ValueError:
            return "❌ 일련번호는 숫자로 입력하세요."
        return _grid_monitor.remove(idx) if _grid_monitor else "❌ 내부 오류: 모니터가 초기화되지 않았습니다."

    return _usage()


def _usage():
    return """📋 그리드 트레이딩 명령어

grid add {종목코드} {기준가} {간격} {주문금액} {최대단계}   항목 추가
  예: grid add 005930 75000 2 100000 3
grid list                                                    목록 조회
grid remove {일련번호}                                       항목 제거
start grid                                                   감시 시작
stop grid                                                    감시 중단"""
