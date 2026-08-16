@echo off
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
cd backend
python -m app.rag.validate_guidelines
endlocal

