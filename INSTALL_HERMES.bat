@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title HERMES - Install Once
echo ==========================================================
echo  HERMES / OX FUNNEL - LOCAL INSTALLER v0.6
echo ==========================================================
echo  This installs ONLY HERMES for your current Windows user.
echo  It does not install or change Discord, Obsidian, Java,
echo  Ollama, LM Studio, Docker, your LLMs or other projects.
echo  No account connection or file upload takes place.
echo.
if exist ".venv\Scripts\python.exe" goto check_environment
where py >nul 2>nul
if not errorlevel 1 goto make_env_py
where python >nul 2>nul
if not errorlevel 1 goto make_env_python
goto no_python

:make_env_py
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto no_python
py -3 -m venv .venv
if errorlevel 1 goto failed
goto check_environment

:make_env_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto no_python
python -m venv .venv
if errorlevel 1 goto failed

:check_environment
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto failed
echo Verifying HERMES source and Python tests...
".venv\Scripts\python.exe" -m compileall -q funnel tools
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m unittest discover -s tests -q
if errorlevel 1 goto failed
echo Preparing your persistent LOCAL HERMES profile...
".venv\Scripts\python.exe" -m funnel local-install
if errorlevel 1 goto failed
echo.
echo INSTALLATION VERIFIED. No other programs were modified.
echo Next: double-click OPEN_HERMES.bat
pause
exit /b 0

:no_python
echo Python 3.10 or newer is required for HERMES.
echo Nothing was installed. See README_FIRST.md for help.
pause
exit /b 1

:failed
echo.
echo HERMES setup did not complete. Existing vault data was not removed.
echo Do not delete your LOCALAPPDATA OX_HERMES folder to troubleshoot.
pause
exit /b 1
