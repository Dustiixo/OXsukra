@echo off
setlocal
set "PAGE=%~dp0visual_lab\index.html"
if not exist "%PAGE%" (
  echo Missing visual lab: %PAGE%
  exit /b 1
)
start "" "%PAGE%"
exit /b 0
