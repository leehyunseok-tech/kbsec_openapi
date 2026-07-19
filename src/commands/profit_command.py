"""익절 명령 처리 - 익절 기준 설정 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_profit(args):
    """
    익절 명령 처리

    사용법:
      /익절              - 현재 익절 설정 조회
      /익절 {퍼센티지}   - 익절 기준 설정 (예: /익절 5)
    """
    if not args:
        settings = SettingsManager.get_stop_loss_settings()
        return f"📈 현재 익절 설정\n\n익절 기준: +{settings.get('take_profit', 5.0)}%\n\n설정 변경: /익절 {{퍼센티지}}\n예: /익절 5"

    if len(args) != 1:
        return "❌ 사용법:\n/익절              - 현재 익절 설정 조회\n/익절 {퍼센티지}   - 익절 기준 설정"

    success, message = SettingsManager.set_take_profit(args[0])
    return message if success else f"❌ {message}"
