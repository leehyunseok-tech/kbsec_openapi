"""mkhr 명령 처리 - 장 시간 설정 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_mkhr(args: list[str]) -> str:
    """
    mkhr 명령 처리 - 장 시간 설정

    사용법:
      /장시간                       - 현재 장 시간 조회
      /장시간 {시작시간} {종료시간}  - 장 시간 설정 (예: /장시간 9:30 15:00)
    """
    if not args:
        hours = SettingsManager.get_market_hours()
        return f"""📊 현재 장 시간 설정

시작 시간: {hours["start_time"]}
종료 시간: {hours["end_time"]}
설명: {hours["description"]}

설정 변경: /장시간 {{시작시간}} {{종료시간}}
예: /장시간 9:30 15:00"""

    if len(args) != 2:
        return """❌ 사용법:
/장시간                       - 현재 장 시간 조회
/장시간 {시작시간} {종료시간}  - 장 시간 설정

예제:
/장시간 9:30 15:00   - 9:30 ~ 15:00으로 설정
/장시간 9:00 15:30   - 9:00 ~ 15:30으로 설정 (디폴트)"""

    success, message = SettingsManager.set_market_hours(args[0], args[1])
    return message if success else f"❌ {message}"
