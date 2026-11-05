@echo off
setlocal
cd /d "%~dp0.."
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo npm was not found. Install Node.js 20 or newer, then run scripts\setup.bat.
  exit /b 1
)
if not exist "node_modules" (
  echo Frontend packages are missing. Run scripts\setup.bat first.
  exit /b 1
)
call npm.cmd run dev
endlocal

