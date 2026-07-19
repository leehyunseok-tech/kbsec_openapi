"""웹 브라우저 세션(쿠키)별로 WebClient 인스턴스를 보관하는 인메모리 저장소.

다중 사용자가 하나의 서버 프로세스를 같이 써도 각자의 KB증권 토큰/설정이 섞이지
않도록, 쿠키 하나당 WebClient 인스턴스 하나를 붙인다(src/web/client.py 참고).
서버가 재시작되면 전부 사라진다 — 사용자가 입력한 client_key/client_secret 등
민감정보를 의도적으로 디스크에 남기지 않기 위해서다(공개 배포 시 다른 사용자의
시크릿이 파일로 남으면 안 되므로).
"""

import secrets
import threading
from datetime import datetime, timedelta

from src.web.client import WebClient

COOKIE_NAME = "kbsec_web_sid"
IDLE_TIMEOUT = timedelta(hours=12)

_lock = threading.Lock()
_clients: dict[str, WebClient] = {}
_last_seen: dict[str, datetime] = {}


def _sweep_idle_locked():
    """오래 활동이 없던 세션을 정리한다(_lock을 쥔 상태에서만 호출)."""
    cutoff = datetime.now() - IDLE_TIMEOUT
    stale = [sid for sid, seen in _last_seen.items() if seen < cutoff]
    for sid in stale:
        _clients.pop(sid, None)
        _last_seen.pop(sid, None)


def get_or_create(session_id: str | None) -> tuple[str, WebClient]:
    """session_id가 없거나 저장소에 없으면 새로 발급, 있으면 그대로 재사용."""
    with _lock:
        _sweep_idle_locked()
        if session_id and session_id in _clients:
            _last_seen[session_id] = datetime.now()
            return session_id, _clients[session_id]

        new_id = secrets.token_urlsafe(32)
        client = WebClient(new_id)
        _clients[new_id] = client
        _last_seen[new_id] = datetime.now()
        return new_id, client
