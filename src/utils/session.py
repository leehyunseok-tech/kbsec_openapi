"""토큰 및 거래 환경 정보를 메모리에 보관하는 SessionManager."""

from datetime import datetime, timedelta

from config import config


class SessionManager:
    def __init__(self):
        self.access_token = None
        self.trading_env = None  # 'dev' | 'real'
        self.host_url = None
        self.token_issued_at = None  # datetime | None
        self.token_expires_at = None  # datetime | None

    def set_token(self, token, env, expires_in=None):
        self.access_token = token
        self.trading_env = env
        self.host_url = config.dev_host_url if env == "dev" else config.real_host_url
        self.token_issued_at = datetime.now()
        self.token_expires_at = (
            self.token_issued_at + timedelta(seconds=int(expires_in)) if expires_in is not None else None
        )

    def clear(self):
        """로그아웃 — 보관 중인 토큰/환경 정보를 전부 제거한다 (토큰 폐기 API 호출은 호출자 몫)."""
        self.access_token = None
        self.trading_env = None
        self.host_url = None
        self.token_issued_at = None
        self.token_expires_at = None

    def is_logged_in(self):
        return self.access_token is not None

    def get_remaining_seconds(self):
        """토큰 만료까지 남은 초 (만료 정보가 없거나 이미 만료됐으면 None)."""
        if self.token_expires_at is None:
            return None
        remaining = (self.token_expires_at - datetime.now()).total_seconds()
        return int(remaining) if remaining > 0 else None

    def get_headers(self):
        if not self.is_logged_in():
            return None
        return {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
        }

    def get_env_name(self):
        return {"dev": "개발환경", "real": "운영환경"}.get(self.trading_env, "미설정")
