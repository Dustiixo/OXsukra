@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title HERMES - Local Application
if not exist ".venv\Scripts\python.exe" goto install_first
".venv\Scripts\python.exe" -m funnel local-app
if errorlevel 1 goto failed
exit /b 0

:install_first
echo HERMES is not installed in this folder.
echo Please run INSTALL_HERMES.bat first.
pause
exit /b 1

:failed
echo HERMES could not start. Your existing vault was not deleted.
echo Check your Python/Tkinter installation and README_FIRST.md.
pause
exit /b 1
