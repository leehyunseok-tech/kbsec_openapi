"""
런타임 설정 관리 (브로커 무관).

SettingsManager는 순수 정적 메서드만 제공한다 — 인스턴스화하지 않는다.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "data"
SETTINGS_PATH = DATA_DIR / "settings.json"

DEFAULTS = {
    "market_hours": {"start_time": "09:00", "end_time": "15:30", "description": "한국 정규 거래시간"},
    "stop_loss": {"take_profit": 5.0, "stop_loss": -5.0, "description": "익절/손절 기준 (퍼센티지)"},
    "trailing_stop": {"drop_rate": 3.0, "min_profit": 5.0, "description": "트레일링 스탑 설정"},
    "order_timeout": {"seconds": 0, "action": "cancel"},
    "cooldown_hours": 0,
    "max_holdings": 0,
    "blacklist": [],
}


class SettingsManager:
    """설정 관리 클래스. 모든 메서드는 @staticmethod — 인스턴스화 금지."""

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
    def _time_to_minutes(time_str):
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)

    @staticmethod
    def load_settings():
        if SETTINGS_PATH.exists():
            try:
                return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[설정] 로드 실패: {e}", flush=True)
        return dict(DEFAULTS)

    @staticmethod
    def save_settings(settings):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            print(f"[설정] 저장 실패: {e}", flush=True)
            return False

    # ── 장 시간 ──────────────────────────────────────────────────────────────
    @staticmethod
    def get_market_hours():
        return SettingsManager.load_settings().get("market_hours", DEFAULTS["market_hours"])

    @staticmethod
    def set_market_hours(start_time, end_time, description=None):
        ok, err = SettingsManager._validate_time_format(start_time)
        if not ok:
            return False, f"시작 시간 오류: {err}"
        ok, err = SettingsManager._validate_time_format(end_time)
        if not ok:
            return False, f"종료 시간 오류: {err}"
        if SettingsManager._time_to_minutes(start_time) >= SettingsManager._time_to_minutes(end_time):
            return False, "시작 시간이 종료 시간보다 커야 합니다"
        settings = SettingsManager.load_settings()
        settings["market_hours"] = {
            "start_time": start_time,
            "end_time": end_time,
            "description": description or f"{start_time} ~ {end_time}",
        }
        if SettingsManager.save_settings(settings):
            return True, f"✅ 장 시간이 설정되었습니다\n시작: {start_time}, 종료: {end_time}"
        return False, "❌ 설정 저장 실패"

    # ── 익절/손절 ────────────────────────────────────────────────────────────
    @staticmethod
    def get_stop_loss_settings():
        return SettingsManager.load_settings().get("stop_loss", DEFAULTS["stop_loss"])

    @staticmethod
    def set_take_profit(percentage):
        try:
            value = abs(float(percentage))
        except ValueError:
            return False, "익절 기준은 숫자여야 합니다"
        if not (0 <= value <= 100):
            return False, "익절 기준은 0~100 사이의 값이어야 합니다"
        settings = SettingsManager.load_settings()
        settings.setdefault("stop_loss", dict(DEFAULTS["stop_loss"]))["take_profit"] = value
        if SettingsManager.save_settings(settings):
            return True, f"✅ 익절 기준이 설정되었습니다\n익절: +{value}%"
        return False, "❌ 익절 설정 저장 실패"

    @staticmethod
    def set_stop_loss(percentage):
        try:
            value = float(percentage)
        except ValueError:
            return False, "손절 기준은 숫자여야 합니다"
        if value > 0:
            value = -value
        if not (-100 <= value <= 0):
            return False, "손절 기준은 -100~0 사이의 값이어야 합니다"
        settings = SettingsManager.load_settings()
        settings.setdefault("stop_loss", dict(DEFAULTS["stop_loss"]))["stop_loss"] = value
        if SettingsManager.save_settings(settings):
            return True, f"✅ 손절 기준이 설정되었습니다\n손절: {value}%"
        return False, "❌ 손절 설정 저장 실패"

    # ── 트레일링 스탑 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_trailing_stop_settings():
        return SettingsManager.load_settings().get("trailing_stop", DEFAULTS["trailing_stop"])

    @staticmethod
    def set_trailing_stop(drop_rate, min_profit):
        settings = SettingsManager.load_settings()
        settings["trailing_stop"] = {
            "drop_rate": drop_rate,
            "min_profit": min_profit,
            "description": "트레일링 스탑 설정",
        }
        if SettingsManager.save_settings(settings):
            return True, f"✅ 트레일링 스탑 설정 완료\n  고점 대비 하락율: -{drop_rate}%\n  최소 발동 수익률: +{min_profit}%"
        return False, "트레일링 스탑 설정 저장 실패"

    # ── 주문 타임아웃 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_order_timeout_settings():
        return SettingsManager.load_settings().get("order_timeout", DEFAULTS["order_timeout"])

    @staticmethod
    def set_order_timeout(seconds: int, action: str):
        if action not in ("cancel", "market"):
            return False, "action은 cancel 또는 market이어야 합니다"
        if seconds < 0:
            return False, "초(seconds)는 0 이상이어야 합니다"
        settings = SettingsManager.load_settings()
        settings["order_timeout"] = {"seconds": seconds, "action": action}
        if SettingsManager.save_settings(settings):
            if seconds == 0:
                return True, "✅ 주문 타임아웃 기능이 비활성화되었습니다"
            return True, f"✅ 주문 타임아웃 설정 완료\n  {seconds}초 미체결 시 → {action}"
        return False, "설정 저장 실패"

    # ── 쿨다운 ───────────────────────────────────────────────────────────────
    @staticmethod
    def get_cooldown_hours() -> int:
        return int(SettingsManager.load_settings().get("cooldown_hours", 0))

    @staticmethod
    def set_cooldown_hours(hours: int):
        if hours < 0:
            return False, "쿨다운 시간은 0 이상이어야 합니다"
        settings = SettingsManager.load_settings()
        settings["cooldown_hours"] = hours
        if SettingsManager.save_settings(settings):
            if hours == 0:
                return True, "✅ 쿨다운 기능이 비활성화되었습니다"
            return True, f"✅ 쿨다운 설정 완료\n  매도 후 {hours}시간 동안 재매수 불가"
        return False, "설정 저장 실패"

    # ── 최대 보유 종목 수 ──────────────────────────────────────────────────────
    @staticmethod
    def get_max_holdings() -> int:
        return int(SettingsManager.load_settings().get("max_holdings", 0))

    @staticmethod
    def set_max_holdings(count: int):
        if count < 0:
            return False, "최대 보유 수는 0 이상이어야 합니다"
        settings = SettingsManager.load_settings()
        settings["max_holdings"] = count
        if SettingsManager.save_settings(settings):
            if count == 0:
                return True, "✅ 보유 종목 수 제한이 해제되었습니다"
            return True, f"✅ 최대 보유 종목 수 설정 완료: {count}개"
        return False, "설정 저장 실패"

    # ── 블랙리스트 ────────────────────────────────────────────────────────────
    @staticmethod
    def get_blacklist() -> list:
        return SettingsManager.load_settings().get("blacklist", [])

    @staticmethod
    def add_to_blacklist(stk_cd: str):
        stk_cd = stk_cd.strip().upper()
        is_domestic = stk_cd.isdigit() and len(stk_cd) == 6
        is_overseas_ticker = stk_cd.isalpha() and 1 <= len(stk_cd) <= 6
        if not (is_domestic or is_overseas_ticker):
            return False, "종목코드는 국내 6자리 숫자 또는 해외 티커(영문)여야 합니다"
        settings = SettingsManager.load_settings()
        blacklist = settings.get("blacklist", [])
        if stk_cd in blacklist:
            return False, f"{stk_cd}은(는) 이미 블랙리스트에 있습니다"
        blacklist.append(stk_cd)
        settings["blacklist"] = blacklist
        if SettingsManager.save_settings(settings):
            return True, f"✅ 블랙리스트 추가: {stk_cd}"
        return False, "설정 저장 실패"

    @staticmethod
    def remove_from_blacklist(index: int):
        settings = SettingsManager.load_settings()
        blacklist = settings.get("blacklist", [])
        if index < 1 or index > len(blacklist):
            return False, f"잘못된 번호입니다. 1~{len(blacklist)} 범위로 입력하세요"
        removed = blacklist.pop(index - 1)
        settings["blacklist"] = blacklist
        if SettingsManager.save_settings(settings):
            return True, f"✅ 블랙리스트 제거: {removed}"
        return False, "설정 저장 실패"
