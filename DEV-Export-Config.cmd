@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Le venv local n'existe pas encore. Lancez d'abord DEV-Noethys.cmd.
  pause
  exit /b 1
)
"%PY%" scripts\config_profile.py export --config-dir noethys\Portable --output Noethys-configuration.json
set CODE=%ERRORLEVEL%
echo.
if %CODE%==0 echo Fichier cree : %CD%\Noethys-configuration.json
pause
exit /b %CODE%
