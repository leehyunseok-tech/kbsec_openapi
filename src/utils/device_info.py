"""dataHeader.ipAddr / macAddr 자동 채움용 헬퍼.

IP/MAC은 프로세스 수명 동안 변하지 않는다고 보고 최초 1회만 조회해 캐시한다.
(모든 API 호출마다 소켓을 여는 비용 제거)
"""

import socket
import uuid
from functools import lru_cache


@lru_cache(maxsize=1)
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return "127.0.0.1"


@lru_cache(maxsize=1)
def get_mac_address():
    node = uuid.getnode()
    return ":".join(f"{(node >> shift) & 0xFF:02X}" for shift in range(40, -1, -8))
