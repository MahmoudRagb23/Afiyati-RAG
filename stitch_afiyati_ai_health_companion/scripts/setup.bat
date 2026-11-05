@echo off
setlocal
cd /d "%~dp0.."
echo [Afiyati] Creating local Python environment...
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher was not found. Install Python 3.12 and select "Add Python to PATH".
  exit /b 1
)
py -3.12 -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 was not found. Afiyati requires Python 3.12; install it, then run this script again.
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
  echo Existing .venv does not use Python 3.12. Delete only the .venv folder, then run this script again.
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1
echo [Afiyati] Installing frontend packages...
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo npm was not found. Install Node.js 20 or newer, then run this script again.
  exit /b 1
)
call npm.cmd install
if errorlevel 1 exit /b 1
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama was not found. Install it, then pull the models listed in README.md.
  exit /b 1
)
echo [Afiyati] Setup complete.
endlocal

