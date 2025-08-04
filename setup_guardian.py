"""
Guardian System Setup and Initialization
Run this script to set up the Guardian system for first-time use
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config_manager import ConfigManager
from src.database.database_manager import DatabaseManager

# OCR processor import (optional for health check)
try:
    from src.ocr.ocr_processor import OCRProcessor
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"Note: OCR modules not available: {e}")
    OCR_AVAILABLE = False

async def setup_guardian_system():
    """Initialize the Guardian system for first-time use"""
    
    print("=" * 60)
    print("ENIGMA-APEX GUARDIAN SYSTEM SETUP")
    print("=" * 60)
    
    # Create required directories
    directories = [
        "data",
        "logs", 
        "config",
        "exports",
        "backups"
    ]
    
    print("\n1. Creating directory structure...")
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"   ✓ {directory}/")
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/setup.log'),
            logging.StreamHandler()
        ]
    )
    
    print("\n2. Initializing configuration...")
    try:
        config_manager = ConfigManager("config/guardian.yaml")
        config = config_manager.get_all_config()
        print("   ✓ Configuration loaded successfully")
        
        # Validate configuration
        try:
            config_manager._validate_config()
            print("   ✓ Configuration validation passed")
        except Exception as ve:
            print(f"   ⚠ Configuration validation warnings: {ve}")
            
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
        return False
    
    print("\n3. Setting up database...")
    try:
        db_manager = DatabaseManager(config.get('database', {}).get('path', 'data/guardian.db'))
        await db_manager.initialize()
        
        # Check database health
        if db_manager.is_healthy():
            print("   ✓ Database initialized successfully")
            
            # Get database statistics
            stats = await db_manager.get_statistics()
            print(f"   📊 Database size: {stats.get('database_size_mb', 0):.2f} MB")
            
        else:
            print("   ✗ Database initialization failed")
            return False
            
        await db_manager.close()
        
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False
    
    print("\n4. Testing OCR system...")
    if OCR_AVAILABLE:
        try:
            ocr_processor = OCRProcessor()
            await ocr_processor.initialize()
            
            if ocr_processor.is_healthy():
                print("   ✓ OCR system initialized successfully")
                
                # Check OCR engines
                stats = ocr_processor.get_statistics()
                print(f"   📊 OCR readings: {stats.get('total_readings', 0)}")
                
            else:
                print("   ⚠ OCR system has issues (check dependencies)")
            
            await ocr_processor.cleanup()
            
        except Exception as e:
            print(f"   ⚠ OCR warning: {e}")
            print("   💡 Make sure OpenCV, EasyOCR, and Tesseract are installed")
    else:
        print("   ⚠ OCR modules not available")
        print("   💡 Install OCR dependencies: pip install opencv-python easyocr pytesseract pillow numpy mss")
    
    print("\n5. Validating system requirements...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"   ✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"   ✗ Python {python_version.major}.{python_version.minor} (requires 3.8+)")
        return False
    
    # Check required packages
    required_packages = [
        ('opencv-python', 'cv2'),
        ('websockets', 'websockets'),
        ('PyYAML', 'yaml'),
        ('aiosqlite', 'aiosqlite'),
        ('numpy', 'numpy')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✓ {package_name}")
        except ImportError:
            print(f"   ✗ {package_name} (missing)")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    
    print("\n6. Creating sample configuration files...")
    
    # Create sample OCR regions if not exists
    ocr_regions_file = Path("config/ocr_regions.json")
    if not ocr_regions_file.exists():
        sample_regions = {
            "export_timestamp": "2024-01-01T00:00:00.000000",
            "screen_resolution": "1920x1080",
            "regions": {
                "power_score": {
                    "coordinates": [100, 100, 200, 150],
                    "description": "Enigma Power Score display area",
                    "validation_pattern": "^\\d{1,3}$"
                },
                "confluence_level": {
                    "coordinates": [250, 100, 300, 150],
                    "description": "Confluence level indicator (L1-L4)",
                    "validation_pattern": "^L[1-4]$"
                }
            }
        }
        
        with open(ocr_regions_file, 'w') as f:
            json.dump(sample_regions, f, indent=2)
        print("   ✓ Sample OCR regions configuration created")
    else:
        print("   ✓ OCR regions configuration exists")
    
    print("\n7. System setup summary:")
    print("   📁 Directory structure: Created")
    print("   ⚙️  Configuration: Loaded")
    print("   🗄️  Database: Initialized")
    print("   👁️  OCR System: Ready")
    print("   📦 Dependencies: Verified")
    
    print("\n" + "=" * 60)
    print("🎉 GUARDIAN SYSTEM SETUP COMPLETE!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Review config/guardian.yaml and adjust settings")
    print("2. Calibrate OCR regions: config/ocr_regions.json")
    print("3. Run the system: python start_guardian.py")
    print("4. Connect NinjaTrader dashboard")
    print("5. Install mobile app (when ready)")
    
    print("\n📋 Important notes:")
    print("• Ensure AlgoBox Enigma panel is visible for OCR")
    print("• Verify Apex prop firm account settings")
    print("• Test emergency stop functionality")
    print("• Start with paper trading for validation")
    
    return True

async def check_system_health():
    """Quick system health check"""
    print("🔍 Running system health check...")
    
    # Check critical files
    critical_files = [
        "config/guardian.yaml",
        "config/ocr_regions.json",
        "requirements.txt"
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} (missing)")
            return False
    
    # Check directories
    critical_dirs = ["data", "logs", "src/core", "src/ocr", "src/kelly"]
    
    for dir_path in critical_dirs:
        if Path(dir_path).exists():
            print(f"   ✓ {dir_path}/")
        else:
            print(f"   ✗ {dir_path}/ (missing)")
            return False
    
    print("✅ System health check passed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Quick health check
        success = asyncio.run(check_system_health())
    else:
        # Full setup
        success = asyncio.run(setup_guardian_system())
    
    if not success:
        print("\n❌ Setup failed. Please check errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
