@echo off
setlocal
cd /d "%~dp0"
if not exist "data" mkdir "data"
echo Inspecting fictional eBay own-orders export only.
py -3 marketplace_map.py --source "samples\ebay_own_orders_FICTIONAL.csv" --inspect
if errorlevel 1 goto error
if exist "data\ebay_normalized_FICTIONAL.csv" (
  echo Existing fictional output preserved. Delete manually if you wish to regenerate.
  goto done
)
echo Creating sanitized fictional CSV for review. No database import happens.
py -3 marketplace_map.py --source "samples\ebay_own_orders_FICTIONAL.csv" --annotations "samples\ebay_annotations_FICTIONAL.csv" --currency CAD --out "data\ebay_normalized_FICTIONAL.csv"
if errorlevel 1 goto error
echo Review data\ebay_normalized_FICTIONAL.csv before any separate import.
goto done
:error
echo The command failed safely. No brokerage or gambling accounts were accessed.
:done
pause
