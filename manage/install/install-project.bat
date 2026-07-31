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
powershell -NoProfile -Command "[IO.File]::WriteAllBytes('run-kbsec-openapi.bat', [Convert]::FromBase64String('QGVjaG8gb2ZmDQpzZXRsb2NhbCBlbmFibGVkZWxheWVkZXhwYW5zaW9uDQpSRU0gS0IgU2VjdXJpdGllcyBPcGVuIEFQSSBsYXVuY2hlciAoV2luZG93cykuDQpSRU0gRGlzcGF0Y2hlcyB0byBtYW5hZ2VccnVuXHJ1bi0qLmJhdCBieSBhcmd1bWVudC4gVW5peCBjb3VudGVycGFydDogcnVuLWtic2VjLW9wZW5hcGkuc2gNCnNldCAiU0NSSVBUX0RJUj0lfmRwMCINCnNldCAiUlVOX0RJUj0lU0NSSVBUX0RJUiVtYW5hZ2VccnVuIg0KDQpzZXQgIlRBUkdFVD0lfjEiDQppZiAiJVRBUkdFVCUiPT0iIiBzZXQgIlRBUkdFVD13ZWIiDQoNCmlmIC9pICIlVEFSR0VUJSI9PSJ0ZWxlZ3JhbSIgKA0KICAgIHNldCAiREVTQz1UZWxlZ3JhbSBBZ2VudCINCiAgICBzZXQgIlNDUklQVD1ydW4tdGVsZWdyYW0uYmF0Ig0KKSBlbHNlIGlmIC9pICIlVEFSR0VUJSI9PSJ0ZXJtaW5hbCIgKA0KICAgIHNldCAiREVTQz1UZXJtaW5hbCBjbGllbnQiDQogICAgc2V0ICJTQ1JJUFQ9cnVuLXRlcm1pbmFsLmJhdCINCikgZWxzZSBpZiAvaSAiJVRBUkdFVCUiPT0id2ViIiAoDQogICAgc2V0ICJERVNDPVdlYiBjbGllbnQgKGh0dHA6Ly9sb2NhbGhvc3Q6ODAwMCkiDQogICAgc2V0ICJTQ1JJUFQ9cnVuLXdlYi5iYXQiDQopIGVsc2UgaWYgL2kgIiVUQVJHRVQlIj09Ii1oIiAoDQogICAgY2FsbCA6dXNhZ2UNCiAgICBleGl0IC9iIDANCikgZWxzZSBpZiAvaSAiJVRBUkdFVCUiPT0iLS1oZWxwIiAoDQogICAgY2FsbCA6dXNhZ2UNCiAgICBleGl0IC9iIDANCikgZWxzZSBpZiAvaSAiJVRBUkdFVCUiPT0iaGVscCIgKA0KICAgIGNhbGwgOnVzYWdlDQogICAgZXhpdCAvYiAwDQopIGVsc2UgKA0KICAgIGVjaG8gW1hdIFVua25vd24gb3B0aW9uOiAlVEFSR0VUJQ0KICAgIGVjaG8uDQogICAgY2FsbCA6b3B0aW9ucw0KICAgIGV4aXQgL2IgMQ0KKQ0KDQpSRU0gUGFzcyBhbnkgYXJncyBhZnRlciB0aGUgZmlyc3QgKFRBUkdFVCkgdGhyb3VnaCB0byB0aGUgdW5kZXJseWluZyBydW4tKi5iYXQuDQpzZXQgIlJFU1Q9JSoiDQppZiBkZWZpbmVkIFJFU1Qgc2V0ICJSRVNUPSFSRVNUOiolfjE9ISINCg0KY2FsbCA6b3B0aW9ucw0KZWNoby4NCmVjaG8gXj4gU2VsZWN0ZWQ6ICVUQVJHRVQlIC0gJURFU0MlIF4oJVNDUklQVCVeKQ0KZWNoby4NCmNhbGwgIiVSVU5fRElSJVwlU0NSSVBUJSIgIVJFU1QhDQpleGl0IC9iICVlcnJvcmxldmVsJQ0KDQo6b3B0aW9ucw0KZWNobyBLQiBTZWN1cml0aWVzIE9wZW4gQVBJIC0gcnVuIG9wdGlvbnM6DQplY2hvICAgdGVsZWdyYW0gICAgICBSdW4gVGVsZWdyYW0gQWdlbnQNCmVjaG8gICB0ZXJtaW5hbCAgICAgIFJ1biB0ZXJtaW5hbCBjbGllbnQNCmVjaG8gICB3ZWIgW3Rva2VuXSAgIFJ1biB3ZWIgY2xpZW50IChodHRwOi8vbG9jYWxob3N0OjgwMDAsIGRlZmF1bHQpDQplY2hvICAgICAgICAgICAgICAgICB0b2tlbjogYXV0by1sb2dpbiB1c2luZyBjb25maWdcY29uZmlnLnB5IGtleXMgKGxvY2FsIG9ubHkpDQpnb3RvIDplb2YNCg0KOnVzYWdlDQplY2hvIFVzYWdlOiBydW4ta2JzZWMtb3BlbmFwaSBbdGVsZWdyYW1efHRlcm1pbmFsXnx3ZWIgW3Rva2VuXV0NCmVjaG8uDQpjYWxsIDpvcHRpb25zDQpnb3RvIDplb2YNCg=='))"
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
echo        run-kbsec-openapi telegram   - Telegram Agent
echo      ^(individual scripts also work: manage\run\run-*.bat^)
echo.
pause
