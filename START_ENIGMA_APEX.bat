@echo off
title Enigma-Apex Trading System
color 0A

echo.
echo ENIGMA-APEX TRADING SYSTEM
echo ==============================
echo.
echo Starting complete trading system...
echo.

echo Installing packages...
pip install flask websockets yfinance pandas requests psutil

echo.
echo Launching system...
python complete_system_launcher.py

pause
