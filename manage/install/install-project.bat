@echo off
REM One-shot dev environment installer for a fresh clone (Windows).
REM Checks Python, installs uv if missing, installs all dependencies (uv sync),
REM and creates config\config.py from the template so manage\run\run-*.bat scripts work.
cd /d "%~dp0..\.."

echo ============================================================
echo  KB Securities auto-trading bot - project installer
echo ============================================================
echo.

REM -- 1) Python ------------------------------------------------
REM The Microsoft Store alias for python.exe exits with an error when
REM Python is not really installed, so this check covers that case too.
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed ^(or not on PATH^).
    echo.
    echo   Download and install Python first:
    echo     https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: check "Add python.exe to PATH" in the installer,
    echo   then run this script again.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] Found %%v

REM -- 2) uv (package manager) ---------------------------------
where uv >nul 2>&1
if errorlevel 1 (
    echo [..] Installing uv package manager...
    winget install --id=astral-sh.uv -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo [..] winget failed or not available - trying official installer...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    )
    REM Make freshly installed uv visible in THIS session (new terminals get it via PATH).
    set "PATH=%USERPROFILE%\.local\bin;%LOCALAPPDATA%\Microsoft\WinGet\Links;%PATH%"
)
where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv was installed but is not on PATH yet.
    echo   Close this window, open a NEW terminal and run install-project.bat again.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('uv --version 2^>^&1') do echo [OK] Found %%v

REM -- 3) Dependencies (creates .venv, may auto-download the pinned Python) --
echo [..] Installing project dependencies ^(uv sync^)...
uv sync
if errorlevel 1 (
    echo [ERROR] "uv sync" failed. Check your network connection and retry.
    pause
    exit /b 1
)
echo [OK] Dependencies installed into .venv

REM -- 4) config\config.py -------------------------------------
if exist "config\config.py" (
    echo [OK] config\config.py already exists - keeping it as is
) else (
    copy "config\config.example.py" "config\config.py" >nul
    echo [OK] Created config\config.py from template
)

echo.
echo ============================================================
echo  Install complete. Next steps:
echo ============================================================
echo   1. Edit config\config.py and fill in your real keys
echo      ^(real_client_key / real_client_secret are required^)
echo   2. Run one of:
echo        manage\run\run-terminal.bat   - terminal client ^(fastest way to start^)
echo        manage\run\run-main.bat       - Telegram bot
echo        manage\run\run-web.bat        - web client ^(http://localhost:8000^)
echo.
pause
