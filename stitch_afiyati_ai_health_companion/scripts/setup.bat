@echo off
setlocal
cd /d "%~dp0.."
echo [Afiyati] Creating local Python environment...
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1
echo [Afiyati] Installing frontend packages...
call npm.cmd install
if errorlevel 1 exit /b 1
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama was not found. Install it, then pull the models listed in README.md.
  exit /b 1
)
echo [Afiyati] Setup complete.
endlocal

