@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ENGINE=%~dp0engine\Godot_v4.7.2-stable_win64.exe"
if exist "%ENGINE%" goto run_game
where godot.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  set "ENGINE=godot.exe"
  goto run_game
)
where Godot_v4.7.2-stable_win64.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  set "ENGINE=Godot_v4.7.2-stable_win64.exe"
  goto run_game
)
echo.
echo UNDERBYTE needs the official Godot 4.7.2 engine for this native project.
echo It is free and open source. First launch requires internet to get it.
echo Download source: https://godotengine.org/download/windows/
echo.
choice /C YN /N /M "Download the official Godot 4.7.2 Windows build now? [Y/N] "
if errorlevel 2 goto canceled
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $u='https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_win64.exe.zip'; $dest=Join-Path (Get-Location) 'engine'; New-Item -ItemType Directory -Force -Path $dest|Out-Null; $zip=Join-Path $dest 'godot.zip'; Invoke-WebRequest -Uri $u -OutFile $zip; $actual=(Get-FileHash -LiteralPath $zip -Algorithm SHA512).Hash.ToLowerInvariant(); if ($actual -ne '83decd58fdf67b9d657958a1ae6bf1929c20785315a81effe245874cdc57acb709bf868e00778a96984338c1b29dafdb453c6847747694621c6ecf5da2259993') { Remove-Item -LiteralPath $zip -ErrorAction SilentlyContinue; throw 'Godot checksum mismatch: engine archive rejected' }; Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force; Remove-Item -LiteralPath $zip"
if errorlevel 1 (
  echo Engine download failed. Nothing was installed outside the UNDERBYTE folder.
  pause
  exit /b 1
)
if not exist "%ENGINE%" (
  echo Download completed, but engine filename was unexpected. Check the engine folder.
  pause
  exit /b 1
)
:run_game
"%ENGINE%" --path "%~dp0" --editor --import --headless --quit
if errorlevel 1 (
  echo Godot import failed. See terminal output; no success is assumed.
  pause
  exit /b 1
)
"%ENGINE%" --path "%~dp0" --rendering-method gl_compatibility
exit /b %ERRORLEVEL%
:canceled
echo Canceled. The project has not been changed.
exit /b 1
