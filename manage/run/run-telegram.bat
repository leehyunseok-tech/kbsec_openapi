@echo off
REM Run the KB Securities auto-trading Telegram bot (src/run/telegram.py)
cd /d "%~dp0..\.."
uv run python -m src.run.telegram
if errorlevel 1 (
    echo.
    echo [ERROR] Something went wrong. Check config\config.py.
    pause
)
