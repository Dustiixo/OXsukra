@echo off
setlocal
cd /d "%~dp0"
where godot.exe >nul 2>nul
if errorlevel 1 (
  echo Godot not found on PATH.
  echo Open godot\project.godot in the native Godot 4.6 editor and press F5.
  pause
  exit /b 2
)
godot --path "%~dp0godot"
if errorlevel 1 (
  echo ECHOFOLD Ocean returned an error. Run the verification commands in README.md.
  pause
  exit /b 1
)
endlocal
