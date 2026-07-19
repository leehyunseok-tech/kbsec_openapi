@echo off
REM Run the KB Securities auto-trading Telegram bot (src/run/main.py)
cd /d "%~dp0"
uv run python -m src.run.main
if errorlevel 1 (
    echo.
    echo [ERROR] Something went wrong. Check config\config.py.
    pause
)
