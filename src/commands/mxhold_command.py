"""mxhold 명령 처리 - 최대 보유 종목 수 설정 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_mxhold(args):
    """
    mxhold 명령 처리

    사용법:
      /최대보유 {개수}  - 최대 보유 종목 수 설정
      /최대보유 0       - 제한 없음
    """
    if not args:
        count = SettingsManager.get_max_holdings()
        status = f"{count}개" if count > 0 else "제한 없음"
        return f"📦 최대 보유 종목 수 현재 설정: {status}\n\n사용법:\n  /최대보유 {{개수}}\n  /최대보유 0  - 제한 없음"

    try:
        count = int(args[0])
    except ValueError:
        return "❌ 개수는 정수여야 합니다."

    success, msg = SettingsManager.set_max_holdings(count)
    return msg if success else f"❌ {msg}"
