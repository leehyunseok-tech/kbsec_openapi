"""cooldown 명령 처리 - 매도 후 재매수 금지 시간 설정 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_cooldown(args):
    """
    cooldown 명령 처리

    사용법:
      /쿨다운 {시간}  - 매도 후 해당 시간(시간) 동안 재매수 불가
      /쿨다운 0       - 제한 없음
    """
    if not args:
        hours = SettingsManager.get_cooldown_hours()
        status = "비활성화 (제한 없음)" if hours == 0 else f"{hours}시간"
        return f"⏳ 쿨다운 현재 설정: {status}\n\n사용법:\n  /쿨다운 {{시간}}\n  /쿨다운 0  - 제한 없음"

    try:
        hours = int(args[0])
    except ValueError:
        return "❌ 시간은 정수여야 합니다."

    success, msg = SettingsManager.set_cooldown_hours(hours)
    return msg if success else f"❌ {msg}"
