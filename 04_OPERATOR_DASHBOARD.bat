@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title HERMES - Operator Review
if not exist ".venv\Scripts\python.exe" goto not_installed
".venv\Scripts\python.exe" -m funnel local-operator
if errorlevel 1 goto failed
exit /b 0
:not_installed
echo Run INSTALL_HERMES.bat first.
pause
exit /b 1
:failed
echo Could not attach to local bot hub. Start 03_CONNECT_DISCORD.bat first.
pause
exit /b 1
