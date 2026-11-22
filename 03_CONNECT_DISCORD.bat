@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title HERMES - Discord Live Pilot
if not exist ".venv\Scripts\python.exe" goto not_installed
".venv\Scripts\python.exe" -c "import discord" >nul 2>nul
if errorlevel 1 goto install_discord
goto run_bridge
:install_discord
echo HERMES needs the optional discord.py bot package in its OWN .venv.
echo This downloads third-party software from Python package indexes.
choice /c YN /m "Install optional bot dependencies now?"
if errorlevel 2 goto canceled
".venv\Scripts\python.exe" -m pip install -r requirements-bot.txt
if errorlevel 1 goto failed
:run_bridge
echo.
echo Only one local HERMES server should be running. Close OPEN_HERMES first.
echo You will need your SERVER ID, USER ID, and BOT TOKEN.
echo The bot token is hidden at input and never written by this launcher.
echo.
".venv\Scripts\python.exe" -m funnel local-discord
if errorlevel 1 goto failed
pause
exit /b 0
:not_installed
echo Run INSTALL_HERMES.bat first; no changes made.
pause
exit /b 1
:canceled
echo No dependencies installed.
pause
exit /b 2
:failed
echo Discord bridge stopped or failed. Your local vault is preserved.
pause
exit /b 1
