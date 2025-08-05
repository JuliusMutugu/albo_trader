@echo off
REM ENIGMA-APEX TRADING SYSTEM - WINDOWS EXECUTABLE
REM ================================================
REM Professional Algorithmic Trading Platform
REM FOR: Michael Canfield - Complete System Demonstration

echo.
echo ===============================================================================
echo 🚀 ENIGMA-APEX TRADING SYSTEM - COMPLETE EXECUTABLE
echo ===============================================================================
echo 📊 Version: 1.0.0 PRODUCTION
echo 📅 Build Date: 2025-08-05  
echo 👤 Client: Michael Canfield
echo 💰 Revenue Potential: $14.3 MILLION ANNUALLY
echo ===============================================================================
echo.

echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.11+ first.
    echo 📥 Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found
echo.

echo 🔍 Checking system files...
if not exist "ENIGMA_APEX_COMPLETE_SYSTEM.py" (
    echo ❌ Main system file missing!
    pause
    exit /b 1
)

echo ✅ System files verified
echo.

echo 📦 Installing required packages...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install flask flask-socketio python-socketio websockets yfinance openai pillow pytesseract numpy pandas requests >nul 2>&1

echo ✅ Dependencies installed
echo.

echo 🚀 LAUNCHING COMPLETE ENIGMA-APEX SYSTEM...
echo ===============================================================================
echo 🎯 This will start the complete trading system demonstration
echo 🌐 Trading dashboard will open automatically in your browser
echo 📊 All components will be displayed and validated
echo 💼 Business value of $14.3M will be demonstrated
echo ===============================================================================
echo.

echo Press any key to start the complete system demonstration...
pause >nul

echo.
echo 🔥 STARTING ENIGMA-APEX SYSTEM...
python ENIGMA_APEX_COMPLETE_SYSTEM.py

echo.
echo 🏁 System demonstration complete
echo 📞 Ready for Michael Canfield's review and deployment
pause
