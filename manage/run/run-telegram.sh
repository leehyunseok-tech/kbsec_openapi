#!/usr/bin/env bash
# KB증권 자동매매 봇 실행 (텔레그램 폴링, 운영용)
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
echo "KB증권 텔레그램 Agent를 시작합니다..."
echo "종료하려면 Ctrl+C를 누르거나 이 창을 닫으세요."
echo
uv run python -m src.run.telegram
