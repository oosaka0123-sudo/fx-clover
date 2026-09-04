@echo off
setlocal
cd /d "%~dp0"
python windows_notification_self_test_v1_18.py
if errorlevel 1 (
  echo.
  echo Notification self-test failed to run.
  pause
  exit /b 1
)
echo.
echo If an FX-Clover TEST notification appeared, the local display path works.
echo Diagnostic details: FX_Clover_environment_diagnostic_v1_18.json
pause
endlocal
