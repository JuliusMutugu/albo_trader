# Enigma-Apex Prop Trading Panel

A professional algorithmic trading system designed for NinjaTrader 8 integration with AlgoBox Enigma signals, featuring advanced risk management and prop firm compliance.

## Features

### Phase 1 (Core System)
- **OCR-Based Signal Reading**: Real-time AlgoBox Enigma panel monitoring
- **Kelly Criterion Engine**: Dynamic position sizing based on historical performance
- **ATR Risk Management**: Volatility-adjusted stop losses and profit targets
- **Apex Compliance**: Real-time prop firm rule enforcement
- **NinjaScript Dashboard**: Professional trading interface for NinjaTrader 8
- **Mobile Remote Control**: Secure trading control from mobile devices

### Architecture
- **Python Backend**: Core logic processing and risk management
- **NinjaScript Frontend**: Native NinjaTrader 8 integration
- **WebSocket Communication**: Real-time data synchronization
- **OCR Engine**: Computer vision for signal recognition
- **Mobile API**: Remote trading control capabilities

## Quick Start

### Prerequisites
- Python 3.11+
- NinjaTrader 8
- Windows 10/11 (for NinjaTrader compatibility)

### Installation
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate environment: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure OCR regions: Edit `config/ocr_regions.json`
6. Start the system: `python src/main.py`

### NinjaTrader Setup
1. Copy NinjaScript files to NinjaTrader directory
2. Compile strategies in NinjaTrader
3. Configure API settings for WebSocket communication

## Configuration

### OCR Setup
Configure screen regions for AlgoBox panel elements in `config/ocr_regions.json`

### Risk Management
Adjust Kelly Criterion and ATR parameters in `config/settings.yaml`

### Apex Compliance
Set prop firm specific rules in `config/apex_rules.yaml`

## Development

### Project Structure
```
enigma-apex-panel/
├── src/                    # Python source code
├── ninjatrader/           # NinjaScript files
├── config/                # Configuration files
├── tests/                 # Unit tests
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

### Testing
Run tests: `python -m pytest tests/`

### Building
Create distribution: `python setup.py sdist bdist_wheel`

## License
Proprietary - All rights reserved

## Support
For technical support, contact the development team.
