"""API 요청/응답 콘솔 로거. Bearer 토큰과 요청/응답 바디의 민감 필드는 로그에 일부만 노출한다.

콘솔 출력과 별개로 최근 로그를 인메모리 링버퍼에도 쌓는다 — 웹 화면의 "API 로그"
패널이 폴링(/api/apilog)으로 가져가 터미널과 동일한 RQ/RP JSON을 보여주기 위함.
버퍼에 들어가는 내용도 콘솔과 동일하게 마스킹을 거친다(토큰/시크릿 원문 없음).
주의: 프로세스 전역 버퍼라 웹 다중 사용자 환경에서는 모든 사용자의 API 로그가
공유된다(설정값과 동일한 서버 공용 제약 — 화면에 안내됨).
"""

import json
import threading
from collections import deque
from datetime import datetime

_LOG_BUFFER = deque(maxlen=300)
_log_lock = threading.Lock()
_log_seq = 0


def _push_log(entry: dict):
    global _log_seq
    with _log_lock:
        _log_seq += 1
        entry["seq"] = _log_seq
        entry["ts"] = datetime.now().strftime("%H:%M:%S")
        _LOG_BUFFER.append(entry)


def get_logs_since(seq: int):
    """seq 이후에 쌓인 로그 항목들을 반환 (웹 API 로그 패널의 증분 폴링용)."""
    with _log_lock:
        return [e for e in _LOG_BUFFER if e["seq"] > seq]


# 요청/응답 바디에 등장하는 민감 필드 (대소문자 무시하고 매칭).
# clientSecret: 앱시크릿, access_token/refresh_token: 발급된 토큰,
# token: 토큰 폐기(/oauth2/revoke) 요청 바디의 접근토큰 필드.
_SENSITIVE_BODY_KEYS = {"clientsecret", "access_token", "refresh_token", "token"}


def _masked_headers(headers):
    if not headers:
        return headers
    masked = dict(headers)
    auth = masked.get("authorization") or masked.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth[7:]
        masked_value = f"Bearer {token[:50]}..." if len(token) > 50 else auth
        if "authorization" in masked:
            masked["authorization"] = masked_value
        if "Authorization" in masked:
            masked["Authorization"] = masked_value
    return masked


def _masked_body(data):
    """clientSecret/access_token 등 민감 필드를 앞 8자만 남기고 마스킹한 사본을 반환."""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                masked[key] = _masked_body(value)
            elif key.lower() in _SENSITIVE_BODY_KEYS and isinstance(value, str) and value:
                masked[key] = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                masked[key] = value
        return masked
    if isinstance(data, list):
        return [_masked_body(item) for item in data]
    return data


def log_api_request(api_name, api_id, url, headers, data):
    print(f"\n{'=' * 60}")
    print(f"[API 요청] {api_name} ({api_id})")
    print(f"{'=' * 60}")
    print(f"URL: {url}")
    print(f"[요청 헤더]\n{json.dumps(_masked_headers(headers), indent=2, ensure_ascii=False)}")
    print(f"[요청 바디]\n{json.dumps(_masked_body(data), indent=2, ensure_ascii=False)}")
    _push_log({"type": "request", "api_name": api_name, "api_id": api_id, "url": url, "data": _masked_body(data)})


def log_api_response(status_code, response_headers, response_body):
    print(f"[API 응답] status_code={status_code}")
    print(f"[응답 바디]\n{json.dumps(_masked_body(response_body), indent=2, ensure_ascii=False)}")
    _push_log({"type": "response", "status_code": status_code, "body": _masked_body(response_body)})


def log_api_error(error_type, error_message):
    print(f"[API 오류] {error_type}: {error_message}")
    _push_log({"type": "error", "error_type": error_type, "message": str(error_message)})
