"""
JSON 상태 파일의 원자적 읽기/쓰기 (브로커 무관 공용 유틸).

`config/data/*.json`(설정·예약·쿨다운 기록)은 여러 주체가 동시에 건드린다:

  - brk/wave/grid 등 자동매매 모니터가 각자 데몬 스레드에서 감시목록을 갱신
  - 웹은 브라우저 세션마다 WebClient가 따로 있고 설정 파일은 서버 공용
  - 텔레그램/터미널 클라이언트의 설정 명령

원래는 각 매니저가 `Path.write_text(json.dumps(...))`로 직접 덮어썼는데, 이 방식은

  1. **원자적이지 않다** — write_text는 파일을 먼저 비우고 다시 쓰므로, 쓰는 도중
     프로세스가 죽거나 디스크가 차면 잘린 JSON(또는 빈 파일)이 남아 다음 로드가
     실패한다. 감시목록이 통째로 날아가면 자동매매가 조용히 멈춘다.
  2. **락이 없다** — 읽고(load) → 고치고 → 쓰는(save) 사이에 다른 스레드가 끼어들면
     나중 쓰기가 앞선 변경을 덮어쓴다(lost update). 모니터 셋이 동시에 도는 상황에서
     실제로 발생 가능하다.

이 모듈은 두 가지를 한곳에서 해결한다:

  - `write_json()`은 같은 디렉터리에 임시 파일로 먼저 쓰고 flush+fsync 후
    `os.replace()`로 교체한다. os.replace는 같은 파일시스템 안에서 원자적이라
    (POSIX rename / Windows MoveFileEx) 어느 시점에 죽어도 파일은 항상
    "이전 내용" 또는 "새 내용" 중 하나이며 잘린 중간 상태가 남지 않는다.
  - `update_json()`은 읽기-수정-쓰기 전체를 프로세스 전역 RLock으로 감싸 lost
    update를 막는다. 파일별로 락을 따로 두어 서로 다른 파일은 병렬로 처리된다.

한계: 락은 **프로세스 내부** 동기화다. 같은 config/data를 여러 프로세스가 동시에
쓰는 구성(예: 텔레그램 봇과 웹 서버를 따로 띄우기)에서는 프로세스 간 lost update가
여전히 가능하다 — 그 경우 파일 락(fcntl/msvcrt)이나 SQLite로 옮겨야 한다. 다만
원자적 쓰기 덕분에 **파일이 깨지는 일은 프로세스가 몇 개든 발생하지 않는다.**
"""

import contextlib
import json
import os
import tempfile
import threading
from pathlib import Path

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# 파일 경로별 RLock. 재진입 가능(RLock)이라 update_json 안에서 read_json을 불러도 안전하다.
_locks: dict[str, threading.RLock] = {}
_locks_guard = threading.Lock()


def _lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _locks_guard:
        if key not in _locks:
            _locks[key] = threading.RLock()
        return _locks[key]


def read_json(path: Path, default):
    """path의 JSON을 읽어 반환. 파일이 없거나 손상됐으면 default를 (복사해) 반환한다.

    default가 dict/list면 얕은 복사본을 돌려주므로, 호출자가 반환값을 수정해도
    모듈 상수(DEFAULTS 등)가 오염되지 않는다.
    """
    with _lock_for(path):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"[json_store] 로드 실패({path.name}): {e} — 기본값으로 복구합니다")
    if isinstance(default, dict):
        return dict(default)
    if isinstance(default, list):
        return list(default)
    return default


def write_json(path: Path, data) -> bool:
    """data를 path에 원자적으로 기록한다. 성공하면 True.

    같은 디렉터리에 임시 파일로 쓴 뒤 os.replace로 교체한다 — 임시 파일을 굳이 같은
    폴더에 두는 이유는, 다른 파일시스템으로 건너뛰면 os.replace가 원자성을 보장하지
    못하기 때문이다.
    """
    with _lock_for(path):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(data, ensure_ascii=False, indent=2)

            fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(payload)
                    fh.flush()
                    os.fsync(fh.fileno())  # 교체 전에 내용이 실제 디스크에 닿도록 보장
                os.replace(tmp_name, path)  # 원자적 교체
            except BaseException:
                # 교체 전에 실패했으면 임시 파일이 남지 않게 치운다(원본은 그대로 유효).
                with contextlib.suppress(OSError):
                    os.unlink(tmp_name)
                raise
            return True
        except OSError as e:
            logger.error(f"[json_store] 저장 실패({path.name}): {e}")
            return False


def update_json(path: Path, mutate, default):
    """읽기-수정-쓰기를 하나의 임계 구역으로 처리한다.

    mutate(data)는 읽어온 data를 제자리에서 고치거나 새 값을 반환하면 된다
    (None을 반환하면 제자리 수정으로 간주). 반환값은 (성공여부, 최종 data).

    load_settings() 후 save_settings()를 따로 부르는 대신 이걸 쓰면, 그 사이에 다른
    스레드가 끼어들어 변경을 덮어쓰는 lost update가 발생하지 않는다.
    """
    with _lock_for(path):
        data = read_json(path, default)
        result = mutate(data)
        if result is not None:
            data = result
        return write_json(path, data), data
