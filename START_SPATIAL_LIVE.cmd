@echo off
setlocal
cd /d "%~dp0"
echo This is a PRIVATE, local-only, READ-ONLY viewer of a FlowMesh workspace.
echo It does not start AI inference, mutate sessions or grant permission to run code.
set /p SESSION=Paste the full folder path of your FlowMesh session: 
py -3 -m spatial_lab.live_server --root "%SESSION%"
pause
