"""
애플리케이션 로깅 설정.

## 왜 print가 아니라 logging인가

자동매매 모니터는 **백그라운드 데몬 스레드에서 사용자가 보고 있지 않을 때** 동작한다.
돌파 감지, 매도 주문, 루프 오류 같은 사건이 `print()`로만 남으면 터미널을 닫는 순간
사라져서, 장 마감 후 "왜 이 종목이 팔렸지?"를 되짚을 방법이 없다. 실거래 자금이
걸린 시스템에서 이건 실질적인 문제다.

그래서 **진단 성격의 출력만** 이 모듈의 로거로 옮겼다:

  - 대상: `*_monitor.py`, `stoploss_manager.py`, `json_store.py`, `api_logger.py`,
    메신저 전송 계층 등 — 사후에 되짚어야 하는 사건
  - 제외: `terminal_ui.py`의 프롬프트, 터미널/웹 배너처럼 **사용자에게 지금 보여주는
    화면 자체** — 이건 UI지 로그가 아니므로 `print()`가 맞다

## 콘솔 출력 형식을 최소로 두는 이유

기존에는 모니터가 `[brk] 돌파 감지 ...` 형태로 콘솔에 바로 찍혔고 사용자는 그 화면에
익숙하다. 콘솔 핸들러에 타임스탬프·레벨을 붙이면 같은 정보가 갑자기 지저분해지므로,
**콘솔은 메시지만**(기존과 동일하게) 보여주고 **파일에는 타임스탬프·레벨·모듈명까지**
전부 남긴다. 사람이 보는 화면은 그대로 두고 사후 추적 능력만 얻는 구성이다.
"""

import logging
import logging.handlers
import sys

from src.paths import LOGS_DIR
from src.utils.console import force_utf8_streams

LOG_FILE = LOGS_DIR / "app.log"

# 파일: 사후 추적용 전체 정보 / 콘솔: 기존 print와 같은 모양 유지
_FILE_FORMAT = "%(asctime)s %(levelname)-7s [%(name)s] %(message)s"
_CONSOLE_FORMAT = "%(message)s"

_configured = False


def setup_logging(level: int = logging.INFO, console: bool = True) -> None:
    """루트 로거를 설정한다. 클라이언트 진입점에서 한 번만 호출하면 된다.

    여러 번 불러도 핸들러가 중복 등록되지 않는다(웹은 uvicorn 리로드 등으로 모듈이
    다시 로드될 수 있다).
    """
    global _configured
    if _configured:
        return

    # 콘솔 핸들러는 생성 시점의 sys.stdout을 붙잡으므로, 그 전에 UTF-8을 보장해야 한다.
    # 진입점이 이미 호출했다면 무해하게 다시 적용될 뿐이고(멱등), 스크립트/테스트처럼
    # 호출을 빠뜨린 경로에서도 Windows cp949 콘솔에서 UnicodeEncodeError가 나지 않는다.
    force_utf8_streams()

    root = logging.getLogger()
    root.setLevel(level)

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        # 5MB × 5개 로테이션 — 폴링 주기가 10초라 로그가 꾸준히 쌓이므로 상한을 둔다.
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
        root.addHandler(file_handler)
    except OSError as e:
        # 로그 파일을 못 만들어도 프로그램은 동작해야 한다(권한 없는 디렉터리 등).
        print(f"[로깅] 파일 로그를 열 수 없어 콘솔로만 기록합니다: {e}", flush=True)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
        root.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """모듈용 로거. `logger = get_logger(__name__)` 형태로 쓴다."""
    return logging.getLogger(name)
