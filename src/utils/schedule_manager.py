"""명령 예약 관리 (브로커 무관)."""

from datetime import datetime

from src.paths import SCHEDULES_JSON as SCHEDULES_PATH
from src.utils import json_store


class ScheduleManager:
    """예약 관리 클래스. 모든 메서드는 @staticmethod — 인스턴스화 금지."""

    @staticmethod
    def _validate_time_format(time_str):
        if not isinstance(time_str, str):
            return False, "시간은 문자열이어야 합니다"
        parts = time_str.split(":")
        if len(parts) != 2:
            return False, "형식: HH:MM"
        try:
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23):
                return False, "시간: 00~23"
            if not (0 <= minute <= 59):
                return False, "분: 00~59"
            return True, ""
        except ValueError:
            return False, "시간과 분은 숫자여야 합니다"

    @staticmethod
    def load_schedules():
        return json_store.read_json(SCHEDULES_PATH, [])

    @staticmethod
    def save_schedules(schedules):
        return json_store.write_json(SCHEDULES_PATH, schedules)

    @staticmethod
    def get_next_schedule_id():
        schedules = ScheduleManager.load_schedules()
        return max((s.get("id", 0) for s in schedules), default=0) + 1

    @staticmethod
    def add_schedule(time, command, repeat_type="daily"):
        valid, error = ScheduleManager._validate_time_format(time)
        if not valid:
            return False, f"시간 형식 오류: {error}", None
        if not command or not command.strip():
            return False, "명령어는 비워둘 수 없습니다", None
        if repeat_type not in ("daily", "once"):
            repeat_type = "daily"

        schedules = ScheduleManager.load_schedules()
        schedule_id = ScheduleManager.get_next_schedule_id()
        schedules.append(
            {
                "id": schedule_id,
                "time": time,
                "command": command.strip(),
                "repeat_type": repeat_type,
                "days": ["MON", "TUE", "WED", "THU", "FRI"],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        if ScheduleManager.save_schedules(schedules):
            repeat_desc = "매일 평일" if repeat_type == "daily" else "한 번만"
            return True, f"✅ 예약이 추가되었습니다\n시간: {time}, 명령: {command}\n반복: {repeat_desc}", schedule_id
        return False, "❌ 예약 저장 실패", None

    @staticmethod
    def get_schedules():
        return ScheduleManager.load_schedules()

    @staticmethod
    def remove_schedule(schedule_id):
        if schedule_id == "all":
            schedules = ScheduleManager.load_schedules()
            if not schedules:
                return False, "❌ 삭제할 예약이 없습니다"
            if ScheduleManager.save_schedules([]):
                return True, f"✅ 모든 예약({len(schedules)}개)이 삭제되었습니다"
            return False, "❌ 모든 예약 삭제 실패"

        try:
            schedule_id = int(schedule_id)
        except ValueError:
            return False, "일련번호는 숫자여야 합니다"

        schedules = ScheduleManager.load_schedules()
        remaining = [s for s in schedules if s.get("id") != schedule_id]
        if len(remaining) == len(schedules):
            return False, f"❌ 일련번호 {schedule_id}인 예약을 찾을 수 없습니다"
        if ScheduleManager.save_schedules(remaining):
            return True, f"✅ 예약 #{schedule_id}이 삭제되었습니다"
        return False, "❌ 예약 삭제 실패"

    @staticmethod
    def get_today_schedules():
        now = datetime.now()
        if now.weekday() >= 5:
            return []
        today = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][now.weekday()]
        return [s for s in ScheduleManager.load_schedules() if today in s.get("days", [])]

    @staticmethod
    def should_execute_schedule(schedule, current_time=None):
        current_time = current_time or datetime.now()
        schedule_time = schedule.get("time")
        if not schedule_time:
            return False
        return current_time.strftime("%H:%M") == schedule_time
