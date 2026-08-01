@echo off
chcp 65001 >nul
REM Run the KB Securities terminal client (src/run/terminal.py) - for dev/testing, no Telegram needed
cd /d "%~dp0..\.."
echo KB증권 터미널 클라이언트를 시작합니다...
echo 종료하려면 이 창을 닫으세요 (X 버튼).
echo.
uv run python -m src.run.terminal
if errorlevel 1 (
    echo.
    echo [오류] 문제가 발생했습니다.
    pause
)
