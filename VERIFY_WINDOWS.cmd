@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 VERIFY_PACKAGE.py && py -3 -m unittest discover -s tests -v && py -3 -m unittest discover -s visual_lab\tests -v
) else (
  python VERIFY_PACKAGE.py && python -m unittest discover -s tests -v && python -m unittest discover -s visual_lab\tests -v
)
if errorlevel 1 pause
