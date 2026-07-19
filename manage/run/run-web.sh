#!/usr/bin/env bash
# KB증권 자동매매 봇 웹 클라이언트 실행 (http://localhost:8000)
# 사용법: ./run-web.sh [token]  -- "token"은 config/config.py 값으로 설정 화면을 자동 채움
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
uv run python -m src.run.web "$@"
