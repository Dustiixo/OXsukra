@echo off
cd /d "%~dp0"
echo OX Treasury v0.3 - copy a previous ledger (source is never changed)
echo Close both Treasury windows before continuing.
echo Paste your previous OX_Treasury_v0_2 folder path or full treasury.db path.
set /p "OLDFOLDER=Old folder or database path: "
where py >nul 2>nul
if %errorlevel%==0 (py -3 migrate.py --source "%OLDFOLDER%") else (python migrate.py --source "%OLDFOLDER%")
pause
