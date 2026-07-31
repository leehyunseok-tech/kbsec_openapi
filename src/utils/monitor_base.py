"""
자동매매 폴링 모니터 공용 베이스.

brk/wave/grid/holdings 등 각 모니터가 공통으로 쓰는 threading.Thread(daemon=True) +
_stop_event.wait(interval) 폴링 루프와 시작/중단/장중여부 판별 로직을 한 곳에 모았다 —
각 모니터는 `_check_all()`만 구현하면 된다.
"""

import threading
from datetime import datetime


class MonitorBase:
    POLL_INTERVAL = 10
    MARKET_START = (9, 0)
    MARKET_END = (15, 30)
    LABEL = "모니터"

    def __init__(self, session, execute_fn=None, send_message_fn=None):
        self.session = session
        self._execute = execute_fn
        self.send_message = send_message_fn or (lambda msg: None)
        self._thread = None
        self._stop_event = threading.Event()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, require_list: bool = True) -> str:
        if self.is_running():
            return f"⚠️ {self.LABEL} 감시가 이미 실행 중입니다."
        if not self.session.is_logged_in():
            return "❌ 로그인이 필요합니다."
        if require_list and not self._has_targets():
            return "❌ 감시 목록이 비어 있습니다. add 명령으로 먼저 추가하세요."
        self._on_start()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return f"🟢 {self.LABEL} 감시 시작 ({self.POLL_INTERVAL}초 주기, {self.MARKET_START[0]:02d}:{self.MARKET_START[1]:02d}~{self.MARKET_END[0]:02d}:{self.MARKET_END[1]:02d})"

    def stop(self) -> str:
        if not self.is_running():
            return f"⚠️ {self.LABEL} 감시가 실행 중이 아닙니다."
        self._stop_event.set()
        self._thread = None
        return f"🔴 {self.LABEL} 감시 중단됨"

    def _has_targets(self) -> bool:
        """감시 대상이 있는지 확인 (하위 클래스에서 override, 기본은 항상 True)."""
        return True

    def _on_start(self):
        """감시 시작 시 초기화 훅 (하위 클래스에서 override 가능)."""

    def _is_market_hours(self) -> bool:
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        sh, sm = self.MARKET_START
        eh, em = self.MARKET_END
        start = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
        end = now.replace(hour=eh, minute=em, second=0, microsecond=0)
        return start <= now <= end

    def _run_loop(self):
        print(f"[{self.LABEL}] 감시 루프 시작", flush=True)
        while not self._stop_event.is_set():
            try:
                if self._is_market_hours():
                    self._check_all()
            except Exception as e:
                print(f"[{self.LABEL}] 루프 오류: {e}", flush=True)
            self._stop_event.wait(self.POLL_INTERVAL)
        print(f"[{self.LABEL}] 감시 루프 종료", flush=True)

    def _check_all(self):
        raise NotImplementedError
