@echo off
setlocal EnableExtensions
pushd "%~dp0"
set "REPORT=VELA_DIAGNOSTICS.txt"
>"%REPORT%" echo VELA WINDOWS DIAGNOSTICS
>>"%REPORT%" echo ========================
>>"%REPORT%" echo NOTE: Full executable paths can contain your Windows username.
>>"%REPORT%" echo.
>>"%REPORT%" echo OS version:
ver >>"%REPORT%" 2>&1
>>"%REPORT%" echo.
>>"%REPORT%" echo Selected Python paths:
where py >>"%REPORT%" 2>nul
where python >>"%REPORT%" 2>nul
where python3 >>"%REPORT%" 2>nul
>>"%REPORT%" echo.
>>"%REPORT%" echo Registered Python installations:
py -0p >>"%REPORT%" 2>&1
>>"%REPORT%" echo.
>>"%REPORT%" echo Python environment variable presence:
if defined PYTHONHOME (echo PYTHONHOME is SET>>"%REPORT%") else (echo PYTHONHOME is empty>>"%REPORT%")
if defined PYTHONPATH (echo PYTHONPATH is SET>>"%REPORT%") else (echo PYTHONPATH is empty>>"%REPORT%")
if defined VIRTUAL_ENV (echo VIRTUAL_ENV is SET>>"%REPORT%") else (echo VIRTUAL_ENV is empty>>"%REPORT%")
>>"%REPORT%" echo.
>>"%REPORT%" echo Direct Python probes, including Tcl/Tk initialization:
call :test py -3.12
call :test py -3.13
call :test py -3.11
call :test py -3.10
call :test py -3.14
call :test py -3
call :test python
call :test python3
if exist ".venv\Scripts\python.exe" call :test ".venv\Scripts\python.exe"
echo.
echo Saved report: %CD%\%REPORT%
echo Paste the report and the last error from RUN_WINDOWS.bat.
echo Full paths in this report might include your Windows username.
pause
popd
exit /b 0

:test
echo.>>"%REPORT%"
echo Check: %*>>"%REPORT%"
%* -c "import sys,encodings,venv,ensurepip,tkinter,_ctypes; t=tkinter.Tk(); t.withdraw(); t.destroy(); print(sys.version); print('Executable:',sys.executable); print('Tcl/Tk:',tkinter.TkVersion); print('PASS')" >>"%REPORT%" 2>&1
if errorlevel 1 (echo FAIL>>"%REPORT%") else (echo PASS>>"%REPORT%")
exit /b 0
