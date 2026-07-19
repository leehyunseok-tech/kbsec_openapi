"""손절 명령 처리 - 손절 기준 설정 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_loss(args):
    """
    손절 명령 처리

    사용법:
      /손절              - 현재 손절 설정 조회
      /손절 {퍼센티지}   - 손절 기준 설정 (예: /손절 5)
    """
    if not args:
        settings = SettingsManager.get_stop_loss_settings()
        return f"📉 현재 손절 설정\n\n손절 기준: {settings.get('stop_loss', -5.0)}%\n\n설정 변경: /손절 {{퍼센티지}}\n예: /손절 5"

    if len(args) != 1:
        return "❌ 사용법:\n/손절              - 현재 손절 설정 조회\n/손절 {퍼센티지}   - 손절 기준 설정"

    success, message = SettingsManager.set_stop_loss(args[0])
    return message if success else f"❌ {message}"
