@echo off
chcp 65001 >nul
REM Run the KB Securities auto-trading Telegram bot (src/run/telegram.py)
cd /d "%~dp0..\.."
echo KB증권 텔레그램 Agent를 시작합니다...
echo 종료하려면 이 창을 닫으세요 (X 버튼).
echo.
uv run python -m src.run.telegram
if errorlevel 1 (
    echo.
    echo [오류] 문제가 발생했습니다. config\config.py 를 확인하세요.
    pause
)
