"""
콘솔 표준 스트림 인코딩 설정 (클라이언트 진입점 공용).

Windows 콘솔 기본 코드페이지(cp949)는 이모지와 일부 한글 조합을 인코딩하지 못해
`UnicodeEncodeError`가 난다. 그래서 각 클라이언트 진입점은 다른 모듈을 import 하기
전에 표준 스트림을 UTF-8로 재설정한다.

다만 `sys.stdout.reconfigure(...)`를 무조건 호출하면 표준 스트림이 진짜 파일 객체가
아닌 환경에서 깨진다 — 예를 들어 pytest는 stdin을 `DontReadFromInput`으로 바꿔치기
하는데 여기엔 `reconfigure`가 없어 `AttributeError`로 **import 자체가 실패**한다
(테스트에서 클라이언트를 import 할 수 없게 된다). 출력이 파이프로 리다이렉트되거나
임베디드 환경에서 실행될 때도 같은 문제가 생길 수 있다.

`reconfigure`는 편의 기능일 뿐 실패해도 프로그램이 동작하지 못할 이유가 없으므로,
가능한 스트림에만 적용하고 나머지는 조용히 건너뛴다.
"""

import contextlib
import sys


def force_utf8_streams(include_stdin: bool = False) -> None:
    """stdout/stderr(선택적으로 stdin)를 UTF-8로 재설정한다. 불가능한 스트림은 건너뛴다."""
    streams = [sys.stdout, sys.stderr]
    if include_stdin:
        streams.insert(0, sys.stdin)

    for stream in streams:
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue  # pytest의 DontReadFromInput, 일부 래핑된 스트림 등
        # 이미 분리된 스트림 등 — 인코딩 설정 실패가 실행을 막을 이유는 없다.
        with contextlib.suppress(ValueError, OSError):
            reconfigure(encoding="utf-8")
