@echo off
setlocal
set "PYTHONUTF8=1"
set "IXO_DATA=%LOCALAPPDATA%\IXO_DSOE"
set "UV_PYTHON_INSTALL_DIR=%IXO_DATA%\runtime\python"
set "UV_CACHE_DIR=%IXO_DATA%\runtime\cache"
set "UV_EXE=%IXO_DATA%\tools\uv.exe"
cd /d "%~dp0"
if exist "%UV_EXE%" (
  "%UV_EXE%" run --offline --frozen --python 3.11 python -m ixo_foundation.native_control --home "%IXO_DATA%\state"
) else (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m ixo_foundation.native_control --home "%IXO_DATA%\state"
  ) else (
    python -m ixo_foundation.native_control --home "%IXO_DATA%\state"
  )
)
if errorlevel 1 (
 echo Native GUI couldn't start. You can use the terminal controller:
 echo python -m ixo_foundation.ops_cli --home "%%IXO_DATA%%\state" console
 pause
)
