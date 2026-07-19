"""API 요청/응답 콘솔 로거. Bearer 토큰과 요청/응답 바디의 민감 필드는 로그에 일부만 노출한다."""

import json

# 요청/응답 바디에 등장하는 민감 필드 (대소문자 무시하고 매칭).
# clientSecret: 앱시크릿, access_token/refresh_token: 발급된 토큰.
_SENSITIVE_BODY_KEYS = {"clientsecret", "access_token", "refresh_token"}


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


def log_api_response(status_code, response_headers, response_body):
    print(f"[API 응답] status_code={status_code}")
    print(f"[응답 바디]\n{json.dumps(_masked_body(response_body), indent=2, ensure_ascii=False)}")


def log_api_error(error_type, error_message):
    print(f"[API 오류] {error_type}: {error_message}")
