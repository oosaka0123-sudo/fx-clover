@echo off
setlocal
cd /d "%~dp0"
python system_health_check_v1_23.py
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (echo FX-Clover MTF health check: PASS) else (echo FX-Clover MTF health check: ACTION REQUIRED)
echo Details: FX_Clover_health_v1_23.json
pause
exit /b %RESULT%
