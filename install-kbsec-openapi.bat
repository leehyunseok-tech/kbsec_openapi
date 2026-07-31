@echo off
REM KB Securities Open API - one-time installer entry point (Windows).
REM Runs manage\install\install-project.bat, then deletes BOTH
REM install-kbsec-openapi.bat and install-kbsec-openapi.sh once installation
REM succeeds, regardless of which one you ran, so neither lingers after
REM first use. Re-run anytime via manage\install\install-project.bat
REM directly if you need to reinstall. Unix counterpart: install-kbsec-openapi.sh
setlocal
set "SCRIPT_DIR=%~dp0"

call "%SCRIPT_DIR%manage\install\install-project.bat"
if errorlevel 1 (
    echo.
    echo [X] Installation did not finish successfully - keeping install-kbsec-openapi.bat/.sh so you can retry.
    exit /b 1
)

echo.
echo [OK] Installation complete - removing install-kbsec-openapi.bat/.sh...
if exist "%SCRIPT_DIR%install-kbsec-openapi.sh" del /f /q "%SCRIPT_DIR%install-kbsec-openapi.sh"
start "" /b cmd /c del "%~f0"
exit /b 0
