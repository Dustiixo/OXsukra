@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m flowmesh demo --root "%~dp0DEMO_TRIAL_001"
) else (
  python -m flowmesh demo --root "%~dp0DEMO_TRIAL_001"
)
if errorlevel 1 (
  echo.
  echo Refused or failed. If DEMO_TRIAL_001 exists, choose a fresh name via CLI.
  pause
)
