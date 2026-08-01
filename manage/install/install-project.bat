@echo off
chcp 65001 >nul
REM One-shot dev environment installer for a fresh clone (Windows).
REM Checks Python, installs uv if missing, installs all dependencies (uv sync),
REM and creates config\config.py from the template so manage\run\run-*.bat scripts work.
REM chcp 65001: this file is UTF-8 + CRLF and step 6 below compares/echoes literal
REM Korean filenames (웹-실행.bat 등) - without forcing UTF-8 here, the comparison
REM would depend on the console's default codepage and could silently mismatch.
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
powershell -NoProfile -Command "[IO.File]::WriteAllBytes('run-kbsec-openapi.bat', [Convert]::FromBase64String('QGVjaG8gb2ZmDQpzZXRsb2NhbCBlbmFibGVkZWxheWVkZXhwYW5zaW9uDQpSRU0gS0IgU2VjdXJpdGllcyBPcGVuIEFQSSBsYXVuY2hlciAoV2luZG93cykuDQpSRU0gRGlzcGF0Y2hlcyB0byBtYW5hZ2VccnVuXHJ1bi0qLmJhdCBieSBhcmd1bWVudC4gVW5peCBjb3VudGVycGFydDogcnVuLWtic2VjLW9wZW5hcGkuc2gNCnNldCAiU0NSSVBUX0RJUj0lfmRwMCINCnNldCAiUlVOX0RJUj0lU0NSSVBUX0RJUiVtYW5hZ2VccnVuIg0KDQpzZXQgIlRBUkdFVD0lfjEiDQppZiAiJVRBUkdFVCUiPT0iIiBzZXQgIlRBUkdFVD13ZWIiDQoNCmlmIC9pICIlVEFSR0VUJSI9PSJ0ZWxlZ3JhbSIgKA0KICAgIHNldCAiREVTQz1UZWxlZ3JhbSBBZ2VudCINCiAgICBzZXQgIlNDUklQVD1ydW4tdGVsZWdyYW0uYmF0Ig0KKSBlbHNlIGlmIC9pICIlVEFSR0VUJSI9PSJ0ZXJtaW5hbCIgKA0KICAgIHNldCAiREVTQz1UZXJtaW5hbCBjbGllbnQiDQogICAgc2V0ICJTQ1JJUFQ9cnVuLXRlcm1pbmFsLmJhdCINCikgZWxzZSBpZiAvaSAiJVRBUkdFVCUiPT0id2ViIiAoDQogICAgc2V0ICJERVNDPVdlYiBjbGllbnQgKGh0dHA6Ly9sb2NhbGhvc3Q6ODAwMCkiDQogICAgc2V0ICJTQ1JJUFQ9cnVuLXdlYi5iYXQiDQopIGVsc2UgaWYgL2kgIiVUQVJHRVQlIj09Ii1oIiAoDQogICAgY2FsbCA6dXNhZ2UNCiAgICBleGl0IC9iIDANCikgZWxzZSBpZiAvaSAiJVRBUkdFVCUiPT0iLS1oZWxwIiAoDQogICAgY2FsbCA6dXNhZ2UNCiAgICBleGl0IC9iIDANCikgZWxzZSBpZiAvaSAiJVRBUkdFVCUiPT0iaGVscCIgKA0KICAgIGNhbGwgOnVzYWdlDQogICAgZXhpdCAvYiAwDQopIGVsc2UgKA0KICAgIGVjaG8gW1hdIFVua25vd24gb3B0aW9uOiAlVEFSR0VUJQ0KICAgIGVjaG8uDQogICAgY2FsbCA6b3B0aW9ucw0KICAgIGV4aXQgL2IgMQ0KKQ0KDQpSRU0gUGFzcyBhbnkgYXJncyBhZnRlciB0aGUgZmlyc3QgKFRBUkdFVCkgdGhyb3VnaCB0byB0aGUgdW5kZXJseWluZyBydW4tKi5iYXQuDQpzZXQgIlJFU1Q9JSoiDQppZiBkZWZpbmVkIFJFU1Qgc2V0ICJSRVNUPSFSRVNUOiolfjE9ISINCg0KY2FsbCA6b3B0aW9ucw0KZWNoby4NCmVjaG8gXj4gU2VsZWN0ZWQ6ICVUQVJHRVQlIC0gJURFU0MlIF4oJVNDUklQVCVeKQ0KZWNoby4NCmNhbGwgIiVSVU5fRElSJVwlU0NSSVBUJSIgIVJFU1QhDQpleGl0IC9iICVlcnJvcmxldmVsJQ0KDQo6b3B0aW9ucw0KZWNobyBLQiBTZWN1cml0aWVzIE9wZW4gQVBJIC0gcnVuIG9wdGlvbnM6DQplY2hvICAgdGVsZWdyYW0gICAgICBSdW4gVGVsZWdyYW0gQWdlbnQNCmVjaG8gICB0ZXJtaW5hbCAgICAgIFJ1biB0ZXJtaW5hbCBjbGllbnQNCmVjaG8gICB3ZWIgW3Rva2VuXSAgIFJ1biB3ZWIgY2xpZW50IChodHRwOi8vbG9jYWxob3N0OjgwMDAsIGRlZmF1bHQpDQplY2hvICAgICAgICAgICAgICAgICB0b2tlbjogYXV0by1sb2dpbiB1c2luZyBjb25maWdcY29uZmlnLnB5IGtleXMgKGxvY2FsIG9ubHkpDQpnb3RvIDplb2YNCg0KOnVzYWdlDQplY2hvIFVzYWdlOiBydW4ta2JzZWMtb3BlbmFwaSBbdGVsZWdyYW1efHRlcm1pbmFsXnx3ZWIgW3Rva2VuXV0gWy0taGVscF58LWhefGhlbHBdDQplY2hvLg0KZWNobyBBbGwgdGhyZWUgY2xpZW50cyBzaGFyZSB0aGUgc2FtZSBjb21tYW5kcyAtIHBpY2sgd2hpY2hldmVyIGZpdHMgaG93DQplY2hvIHlvdSB3YW50IHRvIGludGVyYWN0IHdpdGggeW91ciBLQiBTZWN1cml0aWVzIGFjY291bnQuDQplY2hvLg0KY2FsbCA6b3B0aW9ucw0KZWNoby4NCmVjaG8gRXhhbXBsZXM6DQplY2hvICAgcnVuLWtic2VjLW9wZW5hcGkgICAgICAgICAgICAgICAgIFN0YXJ0IHRoZSB3ZWIgY2xpZW50IChkZWZhdWx0KQ0KZWNobyAgIHJ1bi1rYnNlYy1vcGVuYXBpIHRlcm1pbmFsICAgICAgICBTdGFydCB0aGUgdGVybWluYWwgY2xpZW50DQplY2hvICAgcnVuLWtic2VjLW9wZW5hcGkgdGVsZWdyYW0gICAgICAgIFN0YXJ0IHRoZSBUZWxlZ3JhbSBBZ2VudA0KZWNobyAgIHJ1bi1rYnNlYy1vcGVuYXBpIHdlYiB0b2tlbiAgICAgICBTdGFydCB0aGUgd2ViIGNsaWVudCwgYXV0by1sb2dnZWQgaW4NCmVjaG8gICBydW4ta2JzZWMtb3BlbmFwaSBoZWxwICAgICAgICAgICAgU2hvdyB0aGlzIG1lc3NhZ2UNCmVjaG8uDQplY2hvIEJlZm9yZSB0aGUgZmlyc3QgcnVuOiBjb3B5IGNvbmZpZ1xjb25maWcuZXhhbXBsZS5weSB0byBjb25maWdcY29uZmlnLnB5DQplY2hvIGFuZCBmaWxsIGluIHlvdXIgcmVhbCBLQiBTZWN1cml0aWVzIEFQSSBrZXlzLg0KZWNobyBJbmRpdmlkdWFsIHNjcmlwdHMgYWxzbyB3b3JrIGRpcmVjdGx5OiBtYW5hZ2VccnVuXHJ1bi0qLmJhdA0KZ290byA6ZW9mDQo='))"
if exist "run-kbsec-openapi.bat" (
    echo [OK] Created run-kbsec-openapi.bat
) else (
    echo [WARN] Could not create run-kbsec-openapi.bat ^(PowerShell required^)
)

REM -- 6) Double-click shortcuts (Korean filenames, one per client) --------
REM 웹-실행.bat / 터미널-실행.bat / 텔레그램-실행.bat let a mouse-only user start
REM each client without typing anything (they just call manage\run\run-*.bat).
REM Encoded via -EncodedCommand (base64 of a UTF-16LE script) instead of plain
REM -Command text, because the target filenames themselves are Korean and a
REM plain command-line argument would depend on the active console codepage.
REM To regenerate after editing a local copy of these 3 files:
REM   $web = [Convert]::ToBase64String([IO.File]::ReadAllBytes('웹-실행.bat'))
REM   $terminal = [Convert]::ToBase64String([IO.File]::ReadAllBytes('터미널-실행.bat'))
REM   $telegram = [Convert]::ToBase64String([IO.File]::ReadAllBytes('텔레그램-실행.bat'))
REM   $script = "[IO.File]::WriteAllBytes('웹-실행.bat', [Convert]::FromBase64String('$web'))`n[IO.File]::WriteAllBytes('터미널-실행.bat', [Convert]::FromBase64String('$terminal'))`n[IO.File]::WriteAllBytes('텔레그램-실행.bat', [Convert]::FromBase64String('$telegram'))"
REM   [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($script))
powershell -NoProfile -EncodedCommand "WwBJAE8ALgBGAGkAbABlAF0AOgA6AFcAcgBpAHQAZQBBAGwAbABCAHkAdABlAHMAKAAnAPnGLQDkwonVLgBiAGEAdAAnACwAIABbAEMAbwBuAHYAZQByAHQAXQA6ADoARgByAG8AbQBCAGEAcwBlADYANABTAHQAcgBpAG4AZwAoACcAUQBHAFYAagBhAEcAOABnAGIAMgBaAG0ARABRAHAAUwBSAFUAMABnAFMAMABMAHMAcABwADMAcQB0AG8AdwBnADcASgB1ADUASQBPADIAQgB0AE8AdQBkAHYATwB5AGQAdABPAHkAVwB1AE8AMgBLAHUAQwBEAHIAagBaAFQAcgB1AEoAVAB0AGcAYgBUAHIAcABxADAAZwA3AEkAdQBrADcAWgBhAEoASQBPAHkASQBqACsAeQA3AHQAeQBBAG8AVgAyAGwAdQBaAEcAOQAzAGMAeQBrAHUARABRAHAAUwBSAFUAMABnADcASQB1AGsANwBLAEMAYwBJAE8AcQAxAHIATwAyAFkAaABEAG8AZwBiAFcARgB1AFkAVwBkAGwAWABIAEoAMQBiAGwAeAB5AGQAVwA0AHQAZAAyAFYAaQBMAG0ASgBoAGQAQwBBAG8ANgA0ACsAWgA3AEoAMgA4AEkATwB1AFAAbQBlAHkAZQBrAFQAbwBnAGMAbgBWAHUATABXAHQAaQBjADIAVgBqAEwAVwA5AHcAWgBXADUAaABjAEcAawBnAGQAMgBWAGkASwBRADAASwBVAGsAVgBOAEkATwB5AGkAaABlAHUAagBqAEQAbwBnADcASQB1AGsANwBaAGEASgA2ADUAQwBjAEkATwB5AHcAdgBlAHkAZABtAEMAQgBZAEkATwB1AHkAaABPADIASwB2AE8AeQBkAGgAQwBEAHQAZwBiAFQAcgBwAHEAMwB0AGwAWgBqAHIAcQBiAFEAZwA2ADUAQwBwADYANAB1AEkANgA0AHUAawBMAGcAMABLAFkAMgBGAHMAYgBDAEEAaQBKAFgANQBrAGMARABCAHQAWQBXADUAaABaADIAVgBjAGMAbgBWAHUAWABIAEoAMQBiAGkAMQAzAFoAVwBJAHUAWQBtAEYAMABJAGkAQQBsAEsAZwAwAEsAJwApACkACgBbAEkATwAuAEYAaQBsAGUAXQA6ADoAVwByAGkAdABlAEEAbABsAEIAeQB0AGUAcwAoACcAMNH4uxCxLQDkwonVLgBiAGEAdAAnACwAIABbAEMAbwBuAHYAZQByAHQAXQA6ADoARgByAG8AbQBCAGEAcwBlADYANABTAHQAcgBpAG4AZwAoACcAUQBHAFYAagBhAEcAOABnAGIAMgBaAG0ARABRAHAAUwBSAFUAMABnAFMAMABMAHMAcABwADMAcQB0AG8AdwBnADcAWQBTAHcANgA2ACsANAA2ADQAUwBRAEkATwAyAEIAdABPAHUAZAB2AE8AeQBkAHQATwB5AFcAdQBPADIASwB1AEMARAByAGoAWgBUAHIAdQBKAFQAdABnAGIAVAByAHAAcQAwAGcANwBJAHUAawA3AFoAYQBKAEkATwB5AEkAagArAHkANwB0AHkAQQBvAFYAMgBsAHUAWgBHADkAMwBjAHkAawB1AEQAUQBwAFMAUgBVADAAZwA3AEkAdQBrADcASwBDAGMASQBPAHEAMQByAE8AMgBZAGgARABvAGcAYgBXAEYAdQBZAFcAZABsAFgASABKADEAYgBsAHgAeQBkAFcANAB0AGQARwBWAHkAYgBXAGwAdQBZAFcAdwB1AFkAbQBGADAASQBDAGoAcgBqADUAbgBzAG4AYgB3AGcANgA0ACsAWgA3AEoANgBSAE8AaQBCAHkAZABXADQAdABhADIASgB6AFoAVwBNAHQAYgAzAEIAbABiAG0ARgB3AGEAUwBCADAAWgBYAEoAdABhAFcANQBoAGIAQwBrAE4AQwBsAEoARgBUAFMARABzAG8AbwBYAHIAbwA0AHcANgBJAE8AeQBMAHAATwAyAFcAaQBlAHUAUQBuAEMARABzAHMATAAzAHMAbgBaAGcAZwBXAEMARAByAHMAbwBUAHQAaQByAHoAcwBuAFkAUQBnADcAWQBHADAANgA2AGEAdAA3AFoAVwBZADYANgBtADAASQBPAHUAUQBxAGUAdQBMAGkATwB1AEwAcABDADQATgBDAG0ATgBoAGIARwB3AGcASQBpAFYAKwBaAEgAQQB3AGIAVwBGAHUAWQBXAGQAbABYAEgASgAxAGIAbAB4AHkAZABXADQAdABkAEcAVgB5AGIAVwBsAHUAWQBXAHcAdQBZAG0ARgAwAEkAaQBBAGwASwBnADAASwAnACkAKQAKAFsASQBPAC4ARgBpAGwAZQBdADoAOgBXAHIAaQB0AGUAQQBsAGwAQgB5AHQAZQBzACgAJwBU0Qi4+K2oty0A5MKJ1S4AYgBhAHQAJwAsACAAWwBDAG8AbgB2AGUAcgB0AF0AOgA6AEYAcgBvAG0AQgBhAHMAZQA2ADQAUwB0AHIAaQBuAGcAKAAnAFEARwBWAGoAYQBHADgAZwBiADIAWgBtAEQAUQBwAFMAUgBVADAAZwBTADAATABzAHAAcAAzAHEAdABvAHcAZwA3AFkAVwBVADYANgBDAEkANgByAGUANAA2ADUANgBvAEkARQBGAG4AWgBXADUAMABJAE8AdQBOAGwATwB1ADQAbABPADIAQgB0AE8AdQBtAHIAUwBEAHMAaQA2AFQAdABsAG8AawBnADcASQBpAFAANwBMAHUAMwBJAEMAaABYAGEAVwA1AGsAYgAzAGQAegBLAFMANABOAEMAbABKAEYAVABTAEQAcwBpADYAVABzAG8ASgB3AGcANgByAFcAcwA3AFoAaQBFAE8AaQBCAHQAWQBXADUAaABaADIAVgBjAGMAbgBWAHUAWABIAEoAMQBiAGkAMQAwAFoAVwB4AGwAWgAzAEoAaABiAFMANQBpAFkAWABRAGcASwBPAHUAUABtAGUAeQBkAHYAQwBEAHIAagA1AG4AcwBuAHAARQA2AEkASABKADEAYgBpADEAcgBZAG4ATgBsAFkAeQAxAHYAYwBHAFYAdQBZAFgAQgBwAEkASABSAGwAYgBHAFYAbgBjAG0ARgB0AEsAUQAwAEsAVQBrAFYATgBJAE8AeQBpAGgAZQB1AGoAagBEAG8AZwA3AEkAdQBrADcAWgBhAEoANgA1AEMAYwBJAE8AeQB3AHYAZQB5AGQAbQBDAEIAWQBJAE8AdQB5AGgATwAyAEsAdgBPAHkAZABoAEMARAB0AGcAYgBUAHIAcABxADMAdABsAFoAagByAHEAYgBRAGcANgA1AEMAcAA2ADQAdQBJADYANAB1AGsATABnADAASwBZADIARgBzAGIAQwBBAGkASgBYADUAawBjAEQAQgB0AFkAVwA1AGgAWgAyAFYAYwBjAG4AVgB1AFgASABKADEAYgBpADEAMABaAFcAeABsAFoAMwBKAGgAYgBTADUAaQBZAFgAUQBpAEkAQwBVAHEARABRAG8APQAnACkAKQA="
if exist "웹-실행.bat" (
    echo [OK] Created 3 double-click shortcuts: 웹-실행.bat / 터미널-실행.bat / 텔레그램-실행.bat
) else (
    echo [WARN] Could not create double-click shortcuts ^(PowerShell required^)
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
echo   3. Or just double-click a shortcut - no typing required:
echo        웹-실행.bat / 터미널-실행.bat / 텔레그램-실행.bat
echo        ^(close the window - the X button - to stop it^)
echo.
pause
