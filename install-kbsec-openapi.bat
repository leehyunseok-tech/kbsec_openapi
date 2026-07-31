@echo off
REM KB Securities Open API - one-time installer entry point (Windows).
REM Runs manage\install\install-project.bat, then deletes itself once installation
REM succeeds so it doesn't linger after first use. Re-run anytime via
REM manage\install\install-project.bat directly if you need to reinstall.
REM Unix counterpart: install-kbsec-openapi.sh
setlocal
set "SCRIPT_DIR=%~dp0"

call "%SCRIPT_DIR%manage\install\install-project.bat"
if errorlevel 1 (
    echo.
    echo [X] Installation did not finish successfully - keeping this script so you can retry.
    exit /b 1
)

echo.
echo [OK] Installation complete - removing this one-time installer script (%~nx0)...
start "" /b cmd /c del "%~f0"
exit /b 0
