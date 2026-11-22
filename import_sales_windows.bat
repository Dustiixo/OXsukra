@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag a CSV file onto this BAT or run: import_sales_windows.bat "path-to-sales.csv"
  echo The import is OFFLINE and stores UNVERIFIED sale claims only.
  pause
  exit /b 2
)
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 sold_research.py "%~1"
) else (
  python sold_research.py "%~1"
)
if errorlevel 1 (
  echo Import failed. No partial sale batch was committed.
  pause
  exit /b 1
)
echo Import complete. Run watch_dashboard.py to view the evidence.
pause
