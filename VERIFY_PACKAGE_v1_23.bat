@echo off
setlocal
cd /d "%~dp0"
python verify_distribution_v1_23.py
if errorlevel 1 (
  echo FAIL: v1.23 package integrity check failed.
  pause
  exit /b 1
)
echo PASS: v1.23 MTF files exist, hashes match, and imports work.
pause
endlocal
