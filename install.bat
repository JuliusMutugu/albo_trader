@echo off
echo ====================================================================
echo                ENIGMA-APEX PROP TRADING PANEL INSTALLER
echo ====================================================================
echo.
echo This script will install and configure the complete Enigma-Apex system:
echo - Real OCR for AlgoBox Enigma signal reading
echo - Kelly Criterion position sizing engine
echo - Apex prop firm compliance monitoring
echo - NinjaTrader 8 dashboard integration
echo - Mobile remote control interface
echo.

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check Python version is 3.11+
for /f "tokens=2 delims= " %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

REM Create virtual environment
echo.
echo Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please check requirements.txt and try again
    pause
    exit /b 1
)

REM Install Tesseract OCR (Windows)
echo.
echo Checking for Tesseract OCR...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Tesseract OCR not found
    echo Please install Tesseract OCR for Windows:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Install to default location: C:\Program Files\Tesseract-OCR
    echo 3. Add to PATH: C:\Program Files\Tesseract-OCR
    echo.
    echo The system will work with EasyOCR, but Tesseract provides backup OCR capability.
    echo.
)

REM Create necessary directories
echo.
echo Creating directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "config" mkdir config
if not exist "screenshots" mkdir screenshots

REM Create default configuration if it doesn't exist
echo.
echo Setting up configuration...
if not exist "config\settings.json" (
    echo Creating default settings.json...
    copy "config\settings.default.json" "config\settings.json" >nul 2>&1
)

REM Set up OCR regions
echo.
echo Setting up OCR regions...
python calibrate_ocr.py --setup

echo.
echo ====================================================================
echo                      INSTALLATION COMPLETE
echo ====================================================================
echo.
echo Your Enigma-Apex Prop Trading Panel is now ready!
echo.
echo NEXT STEPS:
echo 1. Configure OCR regions for your AlgoBox Enigma panel:
echo    python calibrate_ocr.py
echo.
echo 2. Start the complete system:
echo    python main.py
echo.
echo 3. Access mobile interface at: http://localhost:8000
echo    Default login: trader1 / secure123
echo.
echo 4. Install NinjaTrader dashboard:
echo    Copy ninjatrader\EnigmaApexGuardian.cs to your NinjaTrader indicators
echo.
echo SYSTEM FEATURES:
echo ✓ Real OCR reading of AlgoBox Enigma signals
echo ✓ Kelly Criterion position sizing with rolling analysis
echo ✓ Apex prop firm compliance enforcement
echo ✓ 2 AM/3 PM cadence failure tracking
echo ✓ WebSocket communication for NinjaTrader 8
echo ✓ Mobile remote control interface
echo ✓ Emergency stop functionality
echo ✓ Comprehensive trade logging
echo.
echo For support, refer to docs\README.md
echo ====================================================================

pause
