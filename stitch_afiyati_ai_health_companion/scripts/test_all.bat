@echo off
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
cd backend
python -m pytest
if errorlevel 1 exit /b 1
cd ..
call npm.cmd run build
endlocal

