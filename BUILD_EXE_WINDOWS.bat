@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run RUN_WINDOWS.bat once to install dependencies.
 pause
 exit /b 1
)
.venv\Scripts\python.exe -m pip install pyinstaller
if errorlevel 1 goto error
.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --name "VELA_Waters_Edge" --collect-all sounddevice --collect-all soundfile launch.py
if errorlevel 1 goto error
echo.
echo Built Windows native app folder: dist\VELA_Waters_Edge\
echo Open VELA_Waters_Edge.exe in that folder.
pause
exit /b 0
:error
echo Native executable build failed. See output above.
pause
exit /b 1
