@echo off
REM Run the KB Securities auto-trading web client (src/run/web.py)
REM Usage: run-web.bat [token]  -- "token" auto-fills settings from config/config.py
cd /d "%~dp0"
uv run python -m src.run.web %*
if errorlevel 1 (
    echo.
    echo [ERROR] Something went wrong.
    pause
)
