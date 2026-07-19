#!/usr/bin/env bash
# KB증권 API 터미널 클라이언트 실행 (개발/테스트용, 텔레그램 불필요)
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
uv run python -m src.run.terminal
