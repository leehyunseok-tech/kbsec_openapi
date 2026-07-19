"""매도 후 재매수 쿨다운 추적 (브로커 무관)."""

import json
from datetime import datetime, timedelta
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "data" / "cooldown_log.json"


def _load():
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save(data: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def record_sell(stk_cd: str):
    data = _load()
    data[stk_cd] = datetime.now().isoformat()
    _save(data)


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
