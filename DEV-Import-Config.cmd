@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Le venv local n'existe pas encore. Lancez d'abord DEV-Noethys.cmd.
  pause
  exit /b 1
)
if not exist "Noethys-configuration.json" (
  echo Fichier Noethys-configuration.json introuvable a la racine du depot.
  pause
  exit /b 1
)
"%PY%" scripts\config_profile.py import --config-dir noethys\Portable --profile Noethys-configuration.json
set CODE=%ERRORLEVEL%
echo.
if %CODE%==0 echo Configuration importee. Relancez Noethys.
pause
exit /b %CODE%
