"""
login 명령 처리 — 운영환경 로그인 (dev/real로 명칭 조정).

주의: KB증권 개발환경(모의투자)은 아직 제공되지 않아 운영환경(실거래)만 정상 동작한다.
`dev` 코드 경로는 KB가 추후 개발환경을 열었을 때를 대비해 남겨뒀지만 현재는 호출해도
실패한다(호스트에 연결되지 않거나 미발급 앱키 오류) — 안내 문구/자동 로그인에서는
노출하지 않는다.
"""

from datetime import datetime

from config import config
from src.api.auth import get_token
from src.utils.formatting import format_duration

_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def handle_login(args, session):
    """
    login 명령 처리

    사용법:
      /login real  - 운영환경(실전) 로그인 — KB증권 개발환경(모의투자)은 아직 미제공
    """
    if not args:
        return "사용법: /login real"

    env = args[0].lower().strip()
    if env == "real":
        host_url, client_key, client_secret = config.real_host_url, config.real_client_key, config.real_client_secret
        env_name = "운영환경"
    elif env == "dev":
        host_url, client_key, client_secret = config.dev_host_url, config.dev_client_key, config.dev_client_secret
        env_name = "개발환경"
    else:
        return "❌ real을 입력하세요 (dev는 KB증권에서 아직 제공하지 않습니다)"

    result = get_token(host_url, client_key, client_secret)

    if result["success"]:
        token = result["access_token"]
        expires_in = result["expires_in"]
        session.set_token(token, env, expires_in)
        now = session.token_issued_at
        expires_at = session.token_expires_at
        return f"""✅ {env_name} 로그인 성공!

환경: {env_name}
상태: 로그인됨
토큰: {token[:30]}...
현재시간: {now.strftime(_DATETIME_FMT)}
유효기간: {format_duration(expires_in)}
유효시간: {expires_at.strftime(_DATETIME_FMT) if expires_at else 'N/A'} 까지

/status 명령으로 상태를 확인할 수 있습니다."""
    else:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get("resultMessage", "알 수 없는 오류")
        return f"""❌ {env_name} 로그인 실패

오류: {error_msg}

/help를 입력하여 도움말을 확인하세요."""


def handle_status(args, session):
    """status 명령 처리 - 현재 로그인 상태 확인"""
    if not session.is_logged_in():
        return "❌ 로그인되지 않음\n\n/login real로 로그인하세요."

    now = datetime.now()
    remaining = session.get_remaining_seconds()
    if remaining is None:
        expiry_lines = "상태: ⚠️ 토큰이 만료되었을 수 있습니다. /login real로 다시 로그인하세요."
    else:
        expiry_lines = (
            f"남은 유효기간: {format_duration(remaining)}\n"
            f"유효시간: {session.token_expires_at.strftime(_DATETIME_FMT)} 까지"
        )

    return f"""✅ 로그인 상태

환경: {session.get_env_name()}
토큰: {session.access_token[:30]}...
현재시간: {now.strftime(_DATETIME_FMT)}
{expiry_lines}"""
