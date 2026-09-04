@echo off
setlocal
cd /d "%~dp0"
python evaluate_manual_reviews_v1_14.py
if errorlevel 1 (
  echo.
  echo Evaluation failed. See the message above.
  pause
  exit /b 1
)
echo.
echo Review validation finished. This is research only; production was not changed.
pause
endlocal
