"""
json_store 원자성·동시성 검증.

config/data/*.json 은 자동매매 모니터 데몬 스레드와 웹 다중 사용자가 동시에
read-modify-write 하는 파일이라, 원자적 교체와 락이 실제로 동작해야 감시목록이
유실되거나 파일이 깨지지 않는다.
"""

import json
import threading

from src.utils import json_store


def test_roundtrip(tmp_json_path):
    assert json_store.write_json(tmp_json_path, {"a": 1})
    assert json_store.read_json(tmp_json_path, {}) == {"a": 1}


def test_missing_file_returns_default(tmp_json_path):
    assert json_store.read_json(tmp_json_path, {"fallback": True}) == {"fallback": True}


def test_default_is_copied_not_shared(tmp_json_path):
    """반환된 기본값을 호출자가 수정해도 원본 상수(DEFAULTS 등)가 오염되면 안 된다."""
    default = {"x": 0}
    got = json_store.read_json(tmp_json_path, default)
    got["x"] = 99
    assert default == {"x": 0}


def test_corrupt_file_falls_back_instead_of_raising(tmp_json_path):
    """잘린 JSON이 남아 있어도 예외를 던지지 않고 기본값으로 복구해야 한다."""
    tmp_json_path.write_text('{"a": 1', encoding="utf-8")
    assert json_store.read_json(tmp_json_path, {"fallback": True}) == {"fallback": True}


def test_write_is_atomic_leaves_no_temp_files(tmp_json_path):
    json_store.write_json(tmp_json_path, {"a": 1})
    leftovers = [p.name for p in tmp_json_path.parent.iterdir() if ".tmp" in p.name]
    assert not leftovers, f"임시 파일이 남았습니다: {leftovers}"


def test_write_produces_valid_json_on_disk(tmp_json_path):
    json_store.write_json(tmp_json_path, {"한글": "값", "n": 1})
    assert json.loads(tmp_json_path.read_text(encoding="utf-8")) == {"한글": "값", "n": 1}


def test_concurrent_updates_do_not_lose_writes(tmp_json_path):
    """여러 스레드가 동시에 증가시켜도 단 한 건도 유실되면 안 된다 (lost update 방지).

    반복 횟수는 검출력과 실행 시간의 절충이다 — 락이 없으면 수십 회만 겹쳐도 유실이
    확실히 발생하므로 320회면 충분하다. 매 쓰기마다 fsync가 걸려(원자성·내구성의
    대가) 횟수를 더 늘리면 CI가 느려진다.
    """
    threads, per_thread = 8, 40
    json_store.write_json(tmp_json_path, {"n": 0})

    def bump():
        for _ in range(per_thread):
            json_store.update_json(tmp_json_path, lambda d: d.__setitem__("n", d["n"] + 1), {"n": 0})

    workers = [threading.Thread(target=bump) for _ in range(threads)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()

    assert json_store.read_json(tmp_json_path, {})["n"] == threads * per_thread


def test_update_json_can_return_replacement_value(tmp_json_path):
    """mutate가 새 값을 반환하면 그것으로 대체돼야 한다 (제자리 수정 외의 사용법)."""
    json_store.write_json(tmp_json_path, {"old": True})
    ok, data = json_store.update_json(tmp_json_path, lambda d: {"new": True}, {})
    assert ok and data == {"new": True}
    assert json_store.read_json(tmp_json_path, {}) == {"new": True}
