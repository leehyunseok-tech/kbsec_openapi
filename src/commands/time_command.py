"""time 명령 처리 - 미체결 주문 타임아웃 설정 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_time(args):
    """
    time 명령 처리 - 미체결 주문 타임아웃 설정

    사용법:
      /타임아웃 {초} cancel  - s초 후 미체결 시 취소
      /타임아웃 {초} market  - s초마다 호가를 한 칸 올려 재주문 (시장가까지)
      /타임아웃 0 cancel     - 기능 비활성화
    """
    if len(args) < 2:
        current = SettingsManager.get_order_timeout_settings()
        s, action = current.get("seconds", 0), current.get("action", "cancel")
        status = "비활성화" if s == 0 else f"{s}초 미체결 시 → {'취소' if action == 'cancel' else '시장가 재주문'}"
        return (
            f"⏱️  주문 타임아웃 현재 설정: {status}\n\n"
            f"사용법:\n  /타임아웃 {{초}} cancel  - s초 후 취소\n  /타임아웃 {{초}} market  - s초마다 호가 한 칸 올려 재주문\n  /타임아웃 0 cancel     - 비활성화"
        )

    try:
        seconds = int(args[0])
    except ValueError:
        return "❌ 초(seconds)는 정수여야 합니다."

    action = args[1].lower()
    if action not in ("cancel", "market"):
        return "❌ 모드는 cancel 또는 market이어야 합니다."

    success, msg = SettingsManager.set_order_timeout(seconds, action)
    return msg if success else f"❌ {msg}"
