
@echo off
title Enigma-Apex System Monitor
:loop
cls
echo ENIGMA-APEX SYSTEM MONITOR
echo ==============================
echo.
echo Current Time: %date% %time%
echo.

echo WebSocket Server (Port 8765):
netstat -an | findstr ":8765" >nul
if %errorlevel%==0 (
    echo RUNNING
) else (
    echo STOPPED
)

echo.
echo Signal Interface (Port 5000):
netstat -an | findstr ":5000" >nul
if %errorlevel%==0 (
    echo RUNNING
) else (
    echo STOPPED
)

echo.
echo Risk Dashboard (Port 3000):
netstat -an | findstr ":3000" >nul
if %errorlevel%==0 (
    echo RUNNING
) else (
    echo STOPPED
)

echo.
echo Quick Links:
echo   Signal Input: http://localhost:5000
echo   Risk Dashboard: http://localhost:3000
echo.
echo Press Ctrl+C to exit
timeout /t 5 >nul
goto loop
