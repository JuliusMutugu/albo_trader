# Enigma-Apex Prop Trading Panel - User Guide

## Overview

The **Enigma-Apex Prop Trading Panel** is a professional algorithmic trading system designed specifically for prop firm trading with AlgoBox Enigma signal integration. The system combines real OCR technology, Kelly Criterion position sizing, Apex compliance enforcement, and mobile remote control capabilities.

## 🚀 Quick Start

### 1. Installation
```bash
# Run the installer (Windows)
install.bat

# Or manual installation:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Calibrate OCR regions for your AlgoBox Enigma panel
python calibrate_ocr.py

# Edit configuration if needed
notepad config\settings.json
```

### 3. Launch System
```bash
# Start complete system
start.bat

# Or manually:
python main.py
```

### 4. Access Interfaces
- **Mobile Control**: http://localhost:8000 (Login: trader1/secure123)
- **NinjaTrader Dashboard**: WebSocket ws://localhost:8765
- **System Logs**: logs/enigma_apex.log

## 📱 Mobile Interface

### Authentication
- **Username**: trader1
- **Password**: secure123
- **Device ID**: Automatically detected

### Features
- Real-time signal monitoring
- Trading control (Enable/Disable)
- Emergency stop button
- Account balance tracking
- System status monitoring
- Compliance alerts

### Remote Control
- **Enable Trading**: Activates automated trading
- **Disable Trading**: Stops new positions (existing positions remain)
- **Emergency Stop**: Immediately halts all trading and closes positions
- **System Restart**: Resets all components after emergency stop

## 🖥️ NinjaTrader Integration

### Dashboard Installation
1. Copy `ninjatrader\EnigmaApexGuardian.cs` to your NinjaTrader indicators folder
2. Compile in NinjaScript Editor
3. Add to your chart
4. Configure WebSocket URL: `ws://localhost:8765/ninja`

### Dashboard Features
- **Enigma Signals Panel**: Power score, confluence, signal color, MACVU state
- **Kelly Position Sizing**: Calculated position size and risk percentage
- **Apex Compliance**: Account balance, daily P&L, compliance status
- **Trading Controls**: Enable/disable trading, emergency stop
- **Connection Status**: Real-time connection monitoring

### Dashboard Configuration
- **WebSocket URL**: Default `ws://localhost:8765/ninja`
- **Auto Connect**: Automatically connect on chart load
- **Panel Visibility**: Toggle individual panels on/off

## 🔍 OCR Configuration

### Initial Setup
```bash
# Run calibration tool
python calibrate_ocr.py

# Test OCR functionality
python test_ocr.py

# Visual OCR testing
python visual_test_ocr.py
```

### Region Configuration
The system monitors these AlgoBox Enigma regions:
- **Power Score**: Numerical value (0-100)
- **Confluence Level**: L1, L2, L3, L4
- **Signal Color**: GREEN, BLUE, RED, PINK, NEUTRAL
- **MACVU State**: BULLISH, BEARISH, NEUTRAL

### OCR Settings
```json
{
    "ocr": {
        "regions": {
            "power_score": [x, y, width, height],
            "confluence": [x, y, width, height],
            "signal_color": [x, y, width, height],
            "macvu_state": [x, y, width, height]
        },
        "read_interval": 2.0,
        "confidence_threshold": 0.8
    }
}
```

## 📊 Kelly Criterion Engine

### Position Sizing Formula
The system uses a modified Kelly Criterion with safety factors:
- **Full Kelly**: f = (bp - q) / b
- **Half Kelly**: f* = f / 2 (for safety)
- **Position Size**: contracts = (account_balance * f*) / (atr * point_value)

### Risk Management
- **Rolling Window**: 100 trade history for win rate calculation
- **Confidence Intervals**: Statistical validation of win rate
- **Maximum Position**: Limited to 10% of account regardless of Kelly
- **ATR-based Stops**: Dynamic stop loss based on Average True Range

### Configuration
```json
{
    "kelly": {
        "confidence_level": 0.95,
        "max_position_percentage": 0.10,
        "min_trades_for_calculation": 10,
        "rolling_window_size": 100
    }
}
```

## ⚖️ Apex Compliance Monitor

### Prop Firm Rules
- **Daily Loss Limit**: 5% of account balance
- **Maximum Loss Limit**: 8% of account balance
- **Trailing Stop**: 5% from highest balance
- **Position Size Limits**: Maximum contracts per trade

### Compliance Levels
- **Safe**: All metrics within limits
- **Warning**: Approaching limits (80% threshold)
- **Violation**: Limits exceeded - trading halted

### Emergency Actions
- **Automatic Stop**: Trading disabled on violation
- **Position Closure**: Emergency liquidation if necessary
- **Alert System**: Immediate notifications via mobile interface

## ⏰ Cadence Tracking

### AlgoBox Timing Analysis
The system monitors AlgoBox Enigma signal patterns:
- **2 AM Failures**: Morning signal absence tracking
- **3 PM Failures**: Afternoon signal absence tracking
- **Threshold Monitoring**: 3+ failures trigger alerts
- **Pattern Recognition**: State machine analysis

### Cadence States
- **Normal**: Regular signal patterns detected
- **Warning**: Irregular patterns observed
- **Failure**: Multiple consecutive failures
- **Critical**: Threshold exceeded - system intervention

## 🔧 Configuration Files

### Main Settings (`config/settings.json`)
```json
{
    "ocr": {
        "engines": ["easyocr", "tesseract"],
        "read_interval": 2.0,
        "confidence_threshold": 0.8
    },
    "kelly": {
        "confidence_level": 0.95,
        "max_position_percentage": 0.10
    },
    "compliance": {
        "account_size": 50000,
        "daily_loss_percentage": 0.05,
        "max_loss_percentage": 0.08
    },
    "websocket": {
        "host": "localhost",
        "port": 8765
    },
    "mobile": {
        "host": "0.0.0.0",
        "port": 8000
    }
}
```

### OCR Regions (`config/ocr_regions.json`)
```json
{
    "regions": {
        "power_score": [100, 100, 80, 30],
        "confluence": [200, 100, 40, 30],
        "signal_color": [300, 100, 60, 30],
        "macvu_state": [400, 100, 80, 30]
    }
}
```

## 🚨 Troubleshooting

### Common Issues

**OCR Not Working**
- Ensure AlgoBox Enigma panel is visible
- Run `python calibrate_ocr.py` to reconfigure regions
- Check Tesseract installation path
- Verify screen resolution hasn't changed

**Mobile Interface Connection Failed**
- Check firewall settings (allow port 8000)
- Verify Python FastAPI is running
- Clear browser cache and cookies
- Try different browser or incognito mode

**NinjaTrader Dashboard Not Connecting**
- Verify WebSocket port 8765 is open
- Check NinjaScript compilation errors
- Ensure indicator is properly added to chart
- Restart NinjaTrader if necessary

**Trading Not Enabled**
- Check compliance status (must be "safe")
- Verify emergency stop is not active
- Ensure account balance is above minimum
- Check OCR is receiving valid signals

### Log Analysis
```bash
# Real-time log monitoring
tail -f logs/enigma_apex.log

# Error filtering
findstr "ERROR" logs/enigma_apex.log

# Performance monitoring
findstr "OCR\|Kelly\|Compliance" logs/enigma_apex.log
```

### Performance Optimization
- **OCR Frequency**: Adjust read_interval (default 2 seconds)
- **System Resources**: Monitor CPU/memory usage
- **Network Latency**: Check WebSocket connection quality
- **Database Cleanup**: Regular log file rotation

## 📈 Trading Strategy

### Signal Interpretation
- **Power Score > 80**: Strong signal confidence
- **Confluence L3/L4**: High probability setups
- **Color Coordination**: Multi-timeframe alignment
- **MACVU Confirmation**: Trend direction validation

### Position Management
- **Entry**: Kelly-calculated position size
- **Stop Loss**: ATR-based dynamic stops
- **Take Profit**: Risk/reward ratio optimization
- **Exit**: Signal reversal or time-based closure

### Risk Controls
- **Maximum Risk**: 2% per trade (Kelly limited)
- **Daily Limit**: 5% account drawdown maximum
- **Position Limit**: 10 contracts maximum per trade
- **Emergency Stop**: Immediate liquidation capability

## 🔐 Security Considerations

### Authentication
- Change default mobile login credentials
- Use strong passwords for production
- Enable two-factor authentication (planned Phase 2)
- Secure API endpoints with proper authorization

### Network Security
- Use HTTPS for mobile interface (production)
- Implement WebSocket SSL/TLS encryption
- Firewall configuration for port access
- VPN access for remote trading

### Data Protection
- Encrypted trade data storage
- Secure backup procedures
- No sensitive data in logs
- GDPR compliance measures

## 📞 Support

### Documentation
- **Technical Architecture**: `docs/TECHNICAL_ARCHITECTURE.md`
- **Phase Roadmap**: `docs/PHASE_ROADMAP.md`
- **Complete Requirements**: `docs/COMPLETE_REQUIREMENTS.md`

### Contact Information
- **Developer**: Michael Canfield requirements implementation
- **System**: Professional prop trading automation
- **Version**: Phase 1 Complete
- **License**: Proprietary trading system

### System Requirements
- **OS**: Windows 10/11 (recommended)
- **Python**: 3.11+ required
- **Memory**: 8GB RAM minimum
- **Storage**: 2GB free space
- **Network**: Stable internet connection
- **Display**: 1920x1080 minimum for OCR calibration

---

*Enigma-Apex Prop Trading Panel - Professional algorithmic trading for the modern prop trader*
