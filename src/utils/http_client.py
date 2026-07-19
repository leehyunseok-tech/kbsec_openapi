"""
requests.Session 기반 단순 HTTP 클라이언트.

KB증권 API 문서에는 공개된 호출 제한이 없어 레이트리미터 없이 단순하게 구현했다.
필요해지면 이 모듈에 레이트리미팅(초당 요청 수 제한, 동시 요청 dedup 등)을 추가하면 된다.
"""

import requests

DEFAULT_TIMEOUT = 10


class HttpClient:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.session = requests.Session()
        self.timeout = timeout

    def get(self, url, headers=None, params=None, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, headers=headers, params=params, **kwargs)

    def post(self, url, headers=None, json=None, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return self.session.post(url, headers=headers, json=json, **kwargs)


http_client = HttpClient()
