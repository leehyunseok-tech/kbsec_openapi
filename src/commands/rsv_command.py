"""rsv 명령 처리 - 명령 예약 (브로커 무관)."""

from src.utils.schedule_manager import ScheduleManager


def handle_rsv(args: list[str]) -> str:
    """
    rsv 명령 처리 - 명령 예약

    사용법:
      /예약 {시간} {명령어}          - 매일 평일 실행 예약
      /예약 once {시간} {명령어}     - 한 번만 실행 예약
      /예약 list                     - 예약 목록 조회
      /예약 remove {일련번호}         - 특정 예약 삭제
      /예약 remove all               - 모든 예약 삭제
    """
    if not args:
        return """📅 예약 명령어 (rsv)

사용법:
/예약 {시간} {명령어}          - 매일 평일 실행 예약
/예약 once {시간} {명령어}     - 한 번만 실행 예약
/예약 list                     - 예약 목록 조회
/예약 remove {일련번호}         - 특정 예약 삭제
/예약 remove all               - 모든 예약 삭제

예제:
/예약 10:00 매수 005930 5       - 매일 10:00에 삼성전자 5주 매수
/예약 once 15:30 매도 005930 5 - 오늘 15:30에만 삼성전자 5주 매도

반복: 매일 평일(월~금) 반복, 토/일요일 제외"""

    if args[0].lower() == "list":
        return _handle_rsv_list()
    if args[0].lower() == "remove":
        if len(args) < 2:
            return "❌ 사용법: /예약 remove {일련번호} 또는 /예약 remove all"
        return _handle_rsv_remove(args[1])
    if args[0].lower() == "once":
        if len(args) < 3:
            return "❌ 사용법: /예약 once {시간} {명령어}"
        return _handle_rsv_add(args[1], " ".join(args[2:]), repeat_type="once")
    if len(args) >= 2:
        return _handle_rsv_add(args[0], " ".join(args[1:]), repeat_type="daily")
    return "❌ 사용법을 확인하세요. /도움말을 입력하세요."


def _handle_rsv_add(time, command, repeat_type="daily"):
    success, message, schedule_id = ScheduleManager.add_schedule(time, command, repeat_type)
    if not success:
        return f"❌ {message}"
    repeat_desc = "매일 평일(월~금)" if repeat_type == "daily" else "한 번만"
    return f"{message}\n\n📅 예약 정보:\n일련번호: #{schedule_id}\n실행 시간: {time}\n명령어: {command}\n반복: {repeat_desc}"


def _handle_rsv_list():
    schedules = ScheduleManager.get_schedules()
    if not schedules:
        return "📋 등록된 예약이 없습니다.\n\n/예약 {시간} {명령어}로 예약을 추가하세요."

    message = f"📋 등록된 예약 ({len(schedules)}개)\n\n"
    for s in schedules:
        repeat_desc = "📅 매일" if s.get("repeat_type", "daily") == "daily" else "⏱️  한 번"
        message += f"#{s.get('id')} | {s.get('time')} | {repeat_desc}\n명령: {s.get('command')}\n등록: {s.get('created_at', 'N/A')}\n\n"
    message += "⚙️  삭제하려면:\n/예약 remove {일련번호}  - 특정 예약 삭제\n/예약 remove all        - 모든 예약 삭제"
    return message.strip()


def _handle_rsv_remove(schedule_id_str):
    success, message = ScheduleManager.remove_schedule(schedule_id_str)
    return message if success else f"❌ {message}"
