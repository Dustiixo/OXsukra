@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ENGINE=%~dp0engine\Godot_v4.7.2-stable_win64.exe"
if not exist "%ENGINE%" (
  where godot.exe >nul 2>&1
  if errorlevel 1 (
    echo Godot not found. Run RUN_UNDERBYTE_WINDOWS.cmd once.
    exit /b 2
  )
  set "ENGINE=godot.exe"
)
"%ENGINE%" --headless --path "%~dp0" --script res://tests/test_godot.gd -- --isolated-test
exit /b %ERRORLEVEL%
