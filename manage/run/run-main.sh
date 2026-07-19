#!/usr/bin/env bash
# KB증권 자동매매 봇 실행 (텔레그램 폴링, 운영용)
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
uv run python -m src.run.main
