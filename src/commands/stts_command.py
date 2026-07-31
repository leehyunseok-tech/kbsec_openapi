"""stts 명령 처리 - 전체 설정값 조회 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager

KNOWN_KEYS = {
    "market_hours",
    "stop_loss",
    "gdcrs",
    "ddcrs",
    "trailing_stop",
    "order_timeout",
    "cooldown_hours",
    "max_holdings",
    "blacklist",
    "brk_rate",
    "brk_watch_list",
    "wave_config",
    "wave_watch_list",
    "grid_watch_list",
}


def handle_stts(args):
    """stts 명령 처리 - 전체 설정값 조회"""
    settings = SettingsManager.load_settings()
    message = "⚙️  현재 설정값\n\n"

    if "market_hours" in settings:
        h = settings["market_hours"]
        message += (
            f"📊 장 시간 (market_hours)\n  시작: {h.get('start_time', 'N/A')}  종료: {h.get('end_time', 'N/A')}\n\n"
        )

    if "stop_loss" in settings:
        sl = settings["stop_loss"]
        message += (
            f"💰 익절/손절 (stop_loss)\n  익절: +{sl.get('take_profit', 5.0)}%  손절: {sl.get('stop_loss', -5.0)}%\n\n"
        )

    if "gdcrs" in settings:
        g = settings["gdcrs"]
        message += f"🔄 골든크로스 (gdcrs)\n  분봉: {g.get('intv_short', 5)}/{g.get('intv_long', 20)}분  추적종목: {len(g.get('stocks', []))}개\n\n"

    if "ddcrs" in settings:
        d = settings["ddcrs"]
        message += f"⚠️  데드크로스 (ddcrs)\n  분봉: {d.get('intv_short', 5)}/{d.get('intv_long', 20)}분  상태: {'활성화' if d.get('enabled') else '비활성화'}\n\n"

    if "trailing_stop" in settings:
        ts = settings["trailing_stop"]
        message += f"📉 트레일링 스탑 (trailing_stop)\n  하락율: -{ts.get('drop_rate', 3.0)}%  최소수익률: +{ts.get('min_profit', 5.0)}%\n\n"

    if "order_timeout" in settings:
        ot = settings["order_timeout"]
        s, action = ot.get("seconds", 0), ot.get("action", "cancel")
        status = "비활성화" if s == 0 else f"{s}초 → {'취소' if action == 'cancel' else '시장가 재주문'}"
        message += f"⏱️  주문 타임아웃 (order_timeout)\n  상태: {status}\n\n"

    cooldown = settings.get("cooldown_hours", 0)
    message += f"⏳ 쿨다운 (cooldown_hours)\n  매도 후 재매수 금지: {f'{cooldown}시간' if cooldown else '비활성화'}\n\n"

    max_hold = settings.get("max_holdings", 0)
    message += f"📦 최대 보유 종목 수 (max_holdings)\n  한도: {f'{max_hold}개' if max_hold else '제한 없음'}\n\n"

    blacklist = settings.get("blacklist", [])
    message += (
        "🚫 블랙리스트 (blacklist)\n  "
        + (f"{', '.join(blacklist)} ({len(blacklist)}개)" if blacklist else "없음")
        + "\n\n"
    )

    brk_rate, brk_list = settings.get("brk_rate", 3.0), settings.get("brk_watch_list", [])
    message += f"📈 돌파매수 (brk)\n  기준 상승률: +{float(brk_rate):.1f}%  감시 종목: {len(brk_list)}개\n\n"

    wave_list = settings.get("wave_watch_list", [])
    message += f"📊 분할매매 (wave)\n  감시 종목: {len(wave_list)}개\n\n"

    grid_list = settings.get("grid_watch_list", [])
    message += f"🔲 그리드 트레이딩 (grid)\n  감시 종목: {len(grid_list)}개\n\n"

    other = {k: v for k, v in settings.items() if k not in KNOWN_KEYS}
    for key, value in other.items():
        message += f"⚙️  {key}: {value}\n"

    return message.rstrip()
