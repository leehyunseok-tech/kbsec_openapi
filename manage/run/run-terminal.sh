#!/usr/bin/env bash
# KB증권 API 터미널 클라이언트 실행 (개발/테스트용, 텔레그램 불필요)
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
echo "KB증권 터미널 클라이언트를 시작합니다..."
echo "종료하려면 Ctrl+C를 누르거나 이 창을 닫으세요."
echo
uv run python -m src.run.terminal
