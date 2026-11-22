@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title VELA - THE WATER'S EDGE
cls
echo.
echo  =========================================
echo     VELA  -  THE WATER'S EDGE
 echo     ONE-CLICK WINDOWS STARTER
 echo  =========================================
echo.
echo  Setting up if needed, then opening VELA...
echo  The first launch may download Python and audio packages.
echo.
where powershell.exe >nul 2>&1
if errorlevel 1 (
  echo ERROR: Windows PowerShell was not found.
  pause
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0VELA_SETUP_AND_RUN.ps1"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo VELA could not open. See VELA_STARTUP_LOG.txt for the details.
  echo Your files have not been deleted. Send the error message for help.
  echo.
  pause
)
exit /b %RESULT%
