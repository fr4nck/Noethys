@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev_windows.ps1"
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" (
  echo.
  echo Noethys a quitte avec le code %EXITCODE%.
  echo Consulte le dossier noethys\Portable pour les logs de diagnostic.
  pause
)
exit /b %EXITCODE%
