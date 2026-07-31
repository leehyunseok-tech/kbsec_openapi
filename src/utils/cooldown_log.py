"""매도 후 재매수 쿨다운 추적 (브로커 무관)."""

from datetime import datetime, timedelta

from src.paths import COOLDOWN_LOG_JSON as LOG_PATH
from src.utils import json_store


def _load():
    return json_store.read_json(LOG_PATH, {})


def _save(data: dict):
    return json_store.write_json(LOG_PATH, data)


def record_sell(stk_cd: str):
    """매도 시각 기록 — 읽기-수정-쓰기를 원자적으로 처리해 동시 매도 기록이 유실되지 않게 한다."""

    def _mutate(data):
        data[stk_cd] = datetime.now().isoformat()

    json_store.update_json(LOG_PATH, _mutate, {})


def is_in_cooldown(stk_cd: str, cooldown_hours: int) -> bool:
    if cooldown_hours <= 0:
        return False
    data = _load()
    if stk_cd not in data:
        return False
    try:
        sell_time = datetime.fromisoformat(data[stk_cd])
        return datetime.now() < sell_time + timedelta(hours=cooldown_hours)
    except Exception:
        return False


def get_remaining(stk_cd: str, cooldown_hours: int) -> str:
    data = _load()
    if stk_cd not in data:
        return "0분"
    try:
        sell_time = datetime.fromisoformat(data[stk_cd])
        remaining = sell_time + timedelta(hours=cooldown_hours) - datetime.now()
        if remaining.total_seconds() <= 0:
            return "0분"
        total_minutes = int(remaining.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}시간 {minutes}분" if hours else f"{minutes}분"
    except Exception:
        return "알 수 없음"
