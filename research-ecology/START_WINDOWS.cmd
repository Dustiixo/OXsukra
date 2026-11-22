@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 -m research_ecology desktop
  if not errorlevel 1 exit /b 0
  py -3 -m research_ecology desktop
  if not errorlevel 1 exit /b 0
)
where python >nul 2>nul
if not errorlevel 1 (
  python -m research_ecology desktop
  if not errorlevel 1 exit /b 0
)
echo Could not start native Study Desk. Python 3.10+ with working Tk is needed.
echo No dependencies were installed or changed.
pause
exit /b 1
