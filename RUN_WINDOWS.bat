@echo off
setlocal EnableExtensions
pushd "%~dp0" || (
  echo ERROR: Cannot access the VELA installation folder.
  pause
  exit /b 1
)
title VELA - The Water's Edge - M1.1

echo ==========================================
echo   VELA  -  THE WATER'S EDGE - M1.1
echo   Native Windows audio workstation
echo ==========================================
echo.

rem Python installations can be poisoned by copied environment variables.
rem A venv must inherit the chosen installed Python, NOT a foreign PYTHONHOME.
if defined PYTHONHOME echo Clearing inherited PYTHONHOME for this launch.
if defined PYTHONPATH echo Clearing inherited PYTHONPATH for this launch.
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONPLATLIBDIR="
set "PYTHONUSERBASE="
set "VIRTUAL_ENV="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"

rem Prefer known mainstream versions with mature audio package wheels.
rem The :probe subroutine rejects broken Python, missing tkinter/Tcl,
rem missing standard library, or versions outside the supported window.
set "PYTHON="
call :probe py -3.12
if not defined PYTHON call :probe py -3.13
if not defined PYTHON call :probe py -3.11
if not defined PYTHON call :probe py -3.10
if not defined PYTHON call :probe py -3.14
if not defined PYTHON call :probe py -3
if not defined PYTHON call :probe python
if not defined PYTHON call :probe python3
if not defined PYTHON goto missing_python

echo Verified Python runtime: %PYTHON%
%PYTHON% -V
if errorlevel 1 goto error
echo.

rem Handle an interrupted or damaged first-run venv non-destructively.
if exist ".venv" (
  if not exist ".venv\Scripts\python.exe" goto repair_venv
  ".venv\Scripts\python.exe" -c "import sys,encodings,venv,ensurepip,tkinter; t=tkinter.Tk(); t.withdraw(); t.destroy(); assert (3,10) <= sys.version_info[:2] <= (3,14)" >nul 2>&1
  if errorlevel 1 goto repair_venv
  goto dependencies
)
goto create_venv

:repair_venv
echo Existing Python environment failed verification. Keeping a backup.
set "BACKUP=.venv_unusable_%RANDOM%_%RANDOM%"
move ".venv" "%BACKUP%" >nul
if errorlevel 1 (
  echo ERROR: Could not rename the old .venv. Close any Python processes using it.
  goto error
)
echo Previous environment moved to %BACKUP%

:create_venv
echo First launch: creating a verified local Python environment...
%PYTHON% -m venv ".venv"
if errorlevel 1 (
  echo ERROR: Python's venv module failed. Try DIAGNOSE_WINDOWS.bat.
  goto error
)

:dependencies
if not exist ".venv\Scripts\python.exe" goto error
".venv\Scripts\python.exe" -c "import numpy,scipy,soundfile,sounddevice" >nul 2>&1
if errorlevel 1 (
  echo Installing native audio dependencies. Internet required on first installation...
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "requirements.txt"
  if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    echo Try DIAGNOSE_WINDOWS.bat, then share its output and this error.
    goto error
  )
)
echo Starting the VELA native desktop application...
".venv\Scripts\python.exe" "launch.py"
if errorlevel 1 goto error
popd
exit /b 0

:probe
%* -c "import sys,encodings,venv,ensurepip,tkinter,_ctypes; t=tkinter.Tk(); t.withdraw(); t.destroy(); assert (3,10) <= sys.version_info[:2] <= (3,14)" >nul 2>&1
if not errorlevel 1 set "PYTHON=%*"
exit /b 0

:missing_python
echo ERROR: No working Python 3.10-3.14 installation with tkinter was found.
echo This can occur with a broken Python install, embeddable Python,
echo Windows Store execution aliases, or missing Tcl/Tk libraries.
echo.
echo Install the standard 64-bit Python 3.12 or 3.13 Windows installer
echo from https://www.python.org/downloads/windows/
echo Ensure pip, venv, and Tcl/Tk are selected during installation.
echo Then run this file again. You do not need to delete the app files.
echo.
echo For diagnostics, double-click DIAGNOSE_WINDOWS.bat.
goto error

:error
echo.
echo VELA launcher encountered an error.
echo Run DIAGNOSE_WINDOWS.bat if you need a detailed system report.
pause
popd
exit /b 1
