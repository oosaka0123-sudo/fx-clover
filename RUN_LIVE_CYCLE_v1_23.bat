@echo off
setlocal
cd /d "%~dp0"
python live_cycle_v1_23.py
set EXIT_CODE=%ERRORLEVEL%
endlocal & exit /b %EXIT_CODE%
