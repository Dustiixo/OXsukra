@echo off
setlocal
set "PYTHONUTF8=1"
set "IXO_DATA=%LOCALAPPDATA%\IXO_DSOE"
set "UV_PYTHON_INSTALL_DIR=%IXO_DATA%\runtime\python"
set "UV_CACHE_DIR=%IXO_DATA%\runtime\cache"
set "UV_EXE=%IXO_DATA%\tools\uv.exe"
cd /d "%~dp0"
if not exist "%UV_EXE%" (
 echo IXO DSOE runtime is missing. Re-run Install_IXO_DSOE.cmd.
 pause
 exit /b 1
)
echo.
echo IXO DSOE - local Python runtime
echo Opening your browser. This window runs the local service.
echo Close this window to stop IXO DSOE.
echo.
"%UV_EXE%" run --offline --frozen --python 3.11 python -m ixo_foundation.desktop --home "%IXO_DATA%\state"
if errorlevel 1 (
 echo.
 echo IXO could not start. Run Install_IXO_DSOE.cmd again to repair.
 pause
)
