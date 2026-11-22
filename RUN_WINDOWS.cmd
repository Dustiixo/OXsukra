@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m flowmesh gui --root "%~dp0FLOWMESH_WORKSPACE"
) else (
  python -m flowmesh gui --root "%~dp0FLOWMESH_WORKSPACE"
)
if errorlevel 1 pause
