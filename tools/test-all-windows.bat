@echo off
setlocal
cd /d "%~dp0.."
python -m compileall -q bytebridge engine.py run.py tests || exit /b 1
python -m unittest discover -s tests -v || exit /b 1
where node >nul 2>nul
if errorlevel 1 (
 echo Node not installed: JavaScript tests NOT RUN.
 exit /b 0
)
node --check static\byte.js || exit /b 1
node tests\test_splice_core.mjs || exit /b 1
node tests\test_byte_core.mjs || exit /b 1
