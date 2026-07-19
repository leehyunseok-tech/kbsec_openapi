@echo off
REM Run the KB Securities terminal client (src/run/terminal.py) - for dev/testing, no Telegram needed
cd /d "%~dp0"
uv run python -m src.run.terminal
if errorlevel 1 (
    echo.
    echo [ERROR] Something went wrong.
    pause
)
