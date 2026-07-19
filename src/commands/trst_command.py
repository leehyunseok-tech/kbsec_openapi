"""trst 명령 처리 - 트레일링 스탑 설정 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_trst(args):
    """
    trst 명령 처리

    사용법:
      /trst                       현재 설정 조회
      /trst {하락율} {최소수익률}  설정 변경 (예: /trst 3.5 5)
    """
    if not args:
        return _show_trst_settings()

    if len(args) != 2:
        return "❌ 사용법:\n/trst                    현재 트레일링 스탑 설정 조회\n/trst {하락율} {최소수익률}  설정 변경\n\n예: /trst 3.5 5"

    try:
        drop_rate = float(args[0])
    except ValueError:
        return "❌ 고점 대비 하락율은 숫자여야 합니다 (예: 3.5)"
    try:
        min_profit = float(args[1])
    except ValueError:
        return "❌ 최소 발동 수익률은 숫자여야 합니다 (예: 5)"

    if not (0 < drop_rate < 100):
        return "❌ 고점 대비 하락율은 0 초과 100 미만이어야 합니다"
    if not (0 <= min_profit < 100):
        return "❌ 최소 발동 수익률은 0 이상 100 미만이어야 합니다"

    success, message = SettingsManager.set_trailing_stop(drop_rate, min_profit)
    return message if success else f"❌ {message}"


def _show_trst_settings():
    s = SettingsManager.get_trailing_stop_settings()
    return f"📉 트레일링 스탑 설정\n\n  고점 대비 하락율: -{s.get('drop_rate', 3.0)}%\n  최소 발동 수익률: +{s.get('min_profit', 5.0)}%\n\n설정 변경: /trst {{하락율}} {{최소수익률}}\n예: /trst 3.5 5"
