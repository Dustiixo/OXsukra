@echo off
setlocal
cd /d "%~dp0"
py -3 -m research_ecology desktop
if errorlevel 1 (
  echo Python 3.10+ with working Tk is required. Nothing installed.
  pause
  exit /b 1
)
