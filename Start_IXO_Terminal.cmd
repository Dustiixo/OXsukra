@echo off
setlocal
set "PYTHONUTF8=1"
set "IXO_DATA=%LOCALAPPDATA%\IXO_DSOE"
set "UV_PYTHON_INSTALL_DIR=%IXO_DATA%\runtime\python"
set "UV_CACHE_DIR=%IXO_DATA%\runtime\cache"
cd /d "%~dp0"
if exist "%IXO_DATA%\tools\uv.exe" (
 "%IXO_DATA%\tools\uv.exe" run --offline --frozen --python 3.11 python -m ixo_foundation.ops_cli --home "%IXO_DATA%\state" console
) else (
 py -3 -m ixo_foundation.ops_cli --home "%IXO_DATA%\state" console
)
