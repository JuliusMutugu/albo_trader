@echo off
REM Enigma-Apex System Launcher

echo ====================================================================
echo               ENIGMA-APEX PROP TRADING PANEL STARTUP
echo ====================================================================

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Check if required directories exist
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "screenshots" mkdir screenshots

REM Start the system
echo.
echo Starting Enigma-Apex Prop Trading Panel...
echo.
echo Components starting:
echo ✓ Guardian Engine (Core trading logic)
echo ✓ OCR Processor (AlgoBox Enigma reading)
echo ✓ Kelly Engine (Position sizing)
echo ✓ Compliance Monitor (Apex rules)
echo ✓ Mobile Interface (Port 8000)
echo ✓ NinjaTrader WebSocket (Port 8765)
echo.
echo Press Ctrl+C to stop the system
echo.

python main.py

echo.
echo System stopped. Press any key to exit.
pause
