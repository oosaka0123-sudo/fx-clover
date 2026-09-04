@echo off
setlocal
set "TASK_NAME=FX_Clover_Live_Monitor_5min"
set "OLD_TASK_NAME=FX_Clover_Live_Monitor_15min"
set "RUN_FILE=%~dp0RUN_LIVE_CYCLE_v1_23.bat"
rem Disable the superseded M15 task to avoid two monitoring cycles running together.
schtasks /change /tn "%OLD_TASK_NAME%" /disable >nul 2>&1
rem /it keeps Windows desktop notifications visible in the signed-in session.
schtasks /create /tn "%TASK_NAME%" /tr "\"%RUN_FILE%\"" /sc minute /mo 5 /it /f
if errorlevel 1 exit /b 1
schtasks /run /tn "%TASK_NAME%"
if errorlevel 1 exit /b 1
echo FX-Clover M5 live task installed and started. Old 15-minute task disabled.
pause
endlocal
