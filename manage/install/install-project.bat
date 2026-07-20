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

REM -- 5) Generate the OS-appropriate unified launcher --------
REM run-kbsec-openapi.bat is created here (not committed to the repo) from an
REM embedded base64 blob so the bytes are exact and no escaping is needed.
REM To change the launcher: edit a local run-kbsec-openapi.bat and re-encode with:
REM   powershell -NoProfile -Command "[Convert]::ToBase64String([IO.File]::ReadAllBytes('run-kbsec-openapi.bat'))"
powershell -NoProfile -Command "[IO.File]::WriteAllBytes('run-kbsec-openapi.bat', [Convert]::FromBase64String('QGVjaG8gb2ZmDQpzZXRsb2NhbCBlbmFibGVkZWxheWVkZXhwYW5zaW9uDQpSRU0gS0IgU2VjdXJpdGllcyBPcGVuIEFQSSBsYXVuY2hlciAoV2luZG93cykuDQpSRU0gRGlzcGF0Y2hlcyB0byBtYW5hZ2VccnVuXHJ1bi0qLmJhdCBieSBhcmd1bWVudC4gVW5peCBjb3VudGVycGFydDogcnVuLWtic2VjLW9wZW5hcGkuc2gNCnNldCAiU0NSSVBUX0RJUj0lfmRwMCINCnNldCAiUlVOX0RJUj0lU0NSSVBUX0RJUiVtYW5hZ2VccnVuIg0KDQpzZXQgIlRBUkdFVD0lfjEiDQppZiAiJVRBUkdFVCUiPT0iIiBzZXQgIlRBUkdFVD13ZWIiDQoNCmlmIC9pICIlVEFSR0VUJSI9PSJtYWluIiAoDQogICAgc2V0ICJERVNDPVRlbGVncmFtIEFnZW50Ig0KICAgIHNldCAiU0NSSVBUPXJ1bi1tYWluLmJhdCINCikgZWxzZSBpZiAvaSAiJVRBUkdFVCUiPT0idGVybWluYWwiICgNCiAgICBzZXQgIkRFU0M9VGVybWluYWwgY2xpZW50Ig0KICAgIHNldCAiU0NSSVBUPXJ1bi10ZXJtaW5hbC5iYXQiDQopIGVsc2UgaWYgL2kgIiVUQVJHRVQlIj09IndlYiIgKA0KICAgIHNldCAiREVTQz1XZWIgY2xpZW50IChodHRwOi8vbG9jYWxob3N0OjgwMDApIg0KICAgIHNldCAiU0NSSVBUPXJ1bi13ZWIuYmF0Ig0KKSBlbHNlIGlmIC9pICIlVEFSR0VUJSI9PSItaCIgKA0KICAgIGNhbGwgOnVzYWdlDQogICAgZXhpdCAvYiAwDQopIGVsc2UgaWYgL2kgIiVUQVJHRVQlIj09Ii0taGVscCIgKA0KICAgIGNhbGwgOnVzYWdlDQogICAgZXhpdCAvYiAwDQopIGVsc2UgaWYgL2kgIiVUQVJHRVQlIj09ImhlbHAiICgNCiAgICBjYWxsIDp1c2FnZQ0KICAgIGV4aXQgL2IgMA0KKSBlbHNlICgNCiAgICBlY2hvIFtYXSBVbmtub3duIG9wdGlvbjogJVRBUkdFVCUNCiAgICBlY2hvLg0KICAgIGNhbGwgOm9wdGlvbnMNCiAgICBleGl0IC9iIDENCikNCg0KUkVNIFBhc3MgYW55IGFyZ3MgYWZ0ZXIgdGhlIGZpcnN0IChUQVJHRVQpIHRocm91Z2ggdG8gdGhlIHVuZGVybHlpbmcgcnVuLSouYmF0Lg0Kc2V0ICJSRVNUPSUqIg0KaWYgZGVmaW5lZCBSRVNUIHNldCAiUkVTVD0hUkVTVDoqJX4xPSEiDQoNCmNhbGwgOm9wdGlvbnMNCmVjaG8uDQplY2hvIF4+IFNlbGVjdGVkOiAlVEFSR0VUJSAtICVERVNDJSBeKCVTQ1JJUFQlXikNCmVjaG8uDQpjYWxsICIlUlVOX0RJUiVcJVNDUklQVCUiICFSRVNUIQ0KZXhpdCAvYiAlZXJyb3JsZXZlbCUNCg0KOm9wdGlvbnMNCmVjaG8gS0IgU2VjdXJpdGllcyBPcGVuIEFQSSAtIHJ1biBvcHRpb25zOg0KZWNobyAgIG1haW4gICAgICAgICAgUnVuIFRlbGVncmFtIEFnZW50DQplY2hvICAgdGVybWluYWwgICAgICBSdW4gdGVybWluYWwgY2xpZW50DQplY2hvICAgd2ViIFt0b2tlbl0gICBSdW4gd2ViIGNsaWVudCAoaHR0cDovL2xvY2FsaG9zdDo4MDAwLCBkZWZhdWx0KQ0KZWNobyAgICAgICAgICAgICAgICAgdG9rZW46IGF1dG8tbG9naW4gdXNpbmcgY29uZmlnXGNvbmZpZy5weSBrZXlzIChsb2NhbCBvbmx5KQ0KZ290byA6ZW9mDQoNCjp1c2FnZQ0KZWNobyBVc2FnZTogcnVuLWtic2VjLW9wZW5hcGkgW21haW5efHRlcm1pbmFsXnx3ZWIgW3Rva2VuXV0NCmVjaG8uDQpjYWxsIDpvcHRpb25zDQpnb3RvIDplb2YNCg=='))"
if exist "run-kbsec-openapi.bat" (
    echo [OK] Created run-kbsec-openapi.bat
) else (
    echo [WARN] Could not create run-kbsec-openapi.bat ^(PowerShell required^)
)

echo.
echo ============================================================
echo  Install complete. Next steps:
echo ============================================================
echo   1. Edit config\config.py and fill in your real keys
echo      ^(real_client_key / real_client_secret are required^)
echo   2. Run with the unified launcher ^(pick a client by argument^):
echo        run-kbsec-openapi            - web client ^(default, http://localhost:8000^)
echo        run-kbsec-openapi terminal   - terminal client ^(fastest way to start^)
echo        run-kbsec-openapi main       - Telegram Agent
echo      ^(individual scripts also work: manage\run\run-*.bat^)
echo.
pause
