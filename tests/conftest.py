"""
pytest 공통 설정.

세 클라이언트(telegram/terminal/web)를 import 하려면 `config/config.py`가 있어야 한다.
이 파일은 실제 키가 담겨 gitignore 대상이라 CI에는 없으므로, 없으면 템플릿
(`config/config.example.py`)을 복사해 만든다 — 테스트는 네트워크를 타지 않고
명령 등록 구조만 검사하므로 실제 키가 필요 없다.
"""

import shutil

import pytest

from src.paths import PROJECT_ROOT

CONFIG_PY = PROJECT_ROOT / "config" / "config.py"
CONFIG_EXAMPLE = PROJECT_ROOT / "config" / "config.example.py"


def pytest_configure(config):
    if not CONFIG_PY.exists() and CONFIG_EXAMPLE.exists():
        shutil.copy(CONFIG_EXAMPLE, CONFIG_PY)


@pytest.fixture
def tmp_json_path(tmp_path):
    """json_store 테스트용 임시 JSON 경로."""
    return tmp_path / "state.json"
