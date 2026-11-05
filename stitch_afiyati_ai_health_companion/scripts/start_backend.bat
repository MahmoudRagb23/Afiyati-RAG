@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing. Run scripts\setup.bat first.
  exit /b 1
)
".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
  echo .venv must use Python 3.12. Run scripts\setup.bat after recreating .venv.
  exit /b 1
)
call .venv\Scripts\activate.bat
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
endlocal

