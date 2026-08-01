@echo off
chcp 65001 >nul
REM Run the KB Securities auto-trading web client (src/run/web.py)
REM Usage: run-web.bat [token]  -- "token" auto-fills settings from config/config.py
cd /d "%~dp0..\.."
echo KB증권 웹 클라이언트를 시작합니다... (http://localhost:8000)
echo 종료하려면 이 창을 닫으세요 (X 버튼).
echo.
uv run python -m src.run.web %*
if errorlevel 1 (
    echo.
    echo [오류] 문제가 발생했습니다.
    pause
)
