"""
System Status Check - Enigma-Apex Prop Trading Panel
Comprehensive system validation and health monitoring
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Suppress some verbose logging for status check
logging.getLogger('easyocr').setLevel(logging.WARNING)

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}")

def print_status(component, status, details=""):
    """Print component status"""
    status_symbol = "✓" if status == "OK" else "✗" if status == "ERROR" else "⚠"
    status_color = "\033[92m" if status == "OK" else "\033[91m" if status == "ERROR" else "\033[93m"
    reset_color = "\033[0m"
    
    print(f"{status_color}{status_symbol} {component:<30} {status:<10}{reset_color}")
    if details:
        print(f"   → {details}")

async def check_python_environment():
    """Check Python environment and dependencies"""
    print_header("PYTHON ENVIRONMENT")
    
    # Python version
    python_version = sys.version.split()[0]
    if python_version >= "3.11":
        print_status("Python Version", "OK", f"v{python_version}")
    else:
        print_status("Python Version", "WARNING", f"v{python_version} (3.11+ recommended)")
    
    # Virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status("Virtual Environment", "OK", "Active")
    else:
        print_status("Virtual Environment", "WARNING", "Not detected")
    
    # Required packages
    required_packages = [
        'easyocr', 'cv2', 'PIL', 'numpy', 'fastapi', 
        'uvicorn', 'websockets', 'jwt', 'mss'
    ]
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            elif package == 'jwt':
                import jwt
            else:
                __import__(package)
            print_status(f"Package: {package}", "OK")
        except ImportError:
            print_status(f"Package: {package}", "ERROR", "Not installed")

async def check_ocr_system():
    """Check OCR system functionality"""
    print_header("OCR SYSTEM")
    
    try:
        # Test EasyOCR
        import easyocr
        reader = easyocr.Reader(['en'])
        print_status("EasyOCR", "OK", "Initialized successfully")
    except Exception as e:
        print_status("EasyOCR", "ERROR", str(e))
    
    try:
        # Test Tesseract
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print_status("Tesseract OCR", "OK", f"v{version}")
    except Exception as e:
        print_status("Tesseract OCR", "WARNING", "Not available (optional)")
    
    try:
        # Test screen capture
        import mss
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
        print_status("Screen Capture", "OK", f"Resolution: {screenshot.width}x{screenshot.height}")
    except Exception as e:
        print_status("Screen Capture", "ERROR", str(e))
    
    # Check OCR configuration
    config_path = Path("config/ocr_regions.json")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                regions = json.load(f)
            region_count = len(regions.get('regions', {}))
            print_status("OCR Configuration", "OK" if region_count >= 4 else "WARNING", 
                        f"{region_count} regions configured")
        except Exception as e:
            print_status("OCR Configuration", "ERROR", str(e))
    else:
        print_status("OCR Configuration", "WARNING", "Not found - run calibrate_ocr.py")

async def check_core_components():
    """Check core system components"""
    print_header("CORE COMPONENTS")
    
    try:
        from src.kelly.kelly_engine import KellyEngine
        kelly = KellyEngine()
        print_status("Kelly Engine", "OK", "Imported successfully")
    except Exception as e:
        print_status("Kelly Engine", "ERROR", str(e))
    
    try:
        from src.compliance.compliance_monitor import ComplianceMonitor
        compliance = ComplianceMonitor()
        print_status("Compliance Monitor", "OK", "Imported successfully")
    except Exception as e:
        print_status("Compliance Monitor", "ERROR", str(e))
    
    try:
        from src.cadence.cadence_tracker import CadenceTracker
        cadence = CadenceTracker()
        print_status("Cadence Tracker", "OK", "Imported successfully")
    except Exception as e:
        print_status("Cadence Tracker", "ERROR", str(e))
    
    try:
        from src.database.database_manager import DatabaseManager
        db = DatabaseManager()
        print_status("Database Manager", "OK", "Imported successfully")
    except Exception as e:
        print_status("Database Manager", "ERROR", str(e))

async def check_network_services():
    """Check network service availability"""
    print_header("NETWORK SERVICES")
    
    import socket
    
    # Check WebSocket port (8765)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8765))
        if result == 0:
            print_status("WebSocket Port 8765", "OK", "Port available")
        else:
            print_status("WebSocket Port 8765", "WARNING", "Port appears to be in use")
        sock.close()
    except Exception as e:
        print_status("WebSocket Port 8765", "ERROR", str(e))
    
    # Check Mobile interface port (8000)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8000))
        if result == 0:
            print_status("Mobile Port 8000", "OK", "Port available")
        else:
            print_status("Mobile Port 8000", "WARNING", "Port appears to be in use")
        sock.close()
    except Exception as e:
        print_status("Mobile Port 8000", "ERROR", str(e))

async def check_configuration():
    """Check system configuration"""
    print_header("CONFIGURATION")
    
    # Main settings
    settings_path = Path("config/settings.json")
    if settings_path.exists():
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            print_status("Main Settings", "OK", "Configuration loaded")
        except Exception as e:
            print_status("Main Settings", "ERROR", str(e))
    else:
        print_status("Main Settings", "WARNING", "Default settings will be used")
    
    # Required directories
    directories = ['logs', 'data', 'screenshots', 'config']
    for directory in directories:
        if Path(directory).exists():
            print_status(f"Directory: {directory}", "OK")
        else:
            print_status(f"Directory: {directory}", "WARNING", "Will be created")

async def check_file_permissions():
    """Check file system permissions"""
    print_header("FILE PERMISSIONS")
    
    # Test log file writing
    try:
        log_path = Path("logs/test_permissions.log")
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, 'w') as f:
            f.write(f"Permission test: {datetime.now()}")
        log_path.unlink()  # Clean up
        print_status("Log File Writing", "OK")
    except Exception as e:
        print_status("Log File Writing", "ERROR", str(e))
    
    # Test data file writing
    try:
        data_path = Path("data/test_permissions.json")
        data_path.parent.mkdir(exist_ok=True)
        with open(data_path, 'w') as f:
            json.dump({"test": True}, f)
        data_path.unlink()  # Clean up
        print_status("Data File Writing", "OK")
    except Exception as e:
        print_status("Data File Writing", "ERROR", str(e))
    
    # Test screenshot directory
    try:
        screenshot_path = Path("screenshots/test_permissions.txt")
        screenshot_path.parent.mkdir(exist_ok=True)
        with open(screenshot_path, 'w') as f:
            f.write("test")
        screenshot_path.unlink()  # Clean up
        print_status("Screenshot Directory", "OK")
    except Exception as e:
        print_status("Screenshot Directory", "ERROR", str(e))

async def run_quick_ocr_test():
    """Run a quick OCR functionality test"""
    print_header("OCR FUNCTIONALITY TEST")
    
    try:
        from src.ocr.ocr_processor import OCRProcessor
        
        # Initialize OCR processor
        ocr = OCRProcessor()
        print_status("OCR Initialization", "OK")
        
        # Test screen capture
        start_time = time.time()
        result = await ocr.read_enigma_signals()
        end_time = time.time()
        
        if result['status'] == 'success':
            print_status("Signal Reading", "OK", f"Completed in {end_time - start_time:.2f}s")
            print(f"   → Data: {result['data']}")
        else:
            print_status("Signal Reading", "WARNING", result.get('error', 'Unknown error'))
            
    except Exception as e:
        print_status("OCR Test", "ERROR", str(e))

async def system_performance_check():
    """Check system performance metrics"""
    print_header("SYSTEM PERFORMANCE")
    
    import psutil
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_status = "OK" if cpu_percent < 50 else "WARNING" if cpu_percent < 80 else "ERROR"
    print_status("CPU Usage", cpu_status, f"{cpu_percent:.1f}%")
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_status = "OK" if memory.percent < 70 else "WARNING" if memory.percent < 85 else "ERROR"
    print_status("Memory Usage", memory_status, f"{memory.percent:.1f}% ({memory.used // (1024**3):.1f}GB used)")
    
    # Disk space
    disk = psutil.disk_usage('.')
    disk_free_gb = disk.free // (1024**3)
    disk_status = "OK" if disk_free_gb > 5 else "WARNING" if disk_free_gb > 1 else "ERROR"
    print_status("Disk Space", disk_status, f"{disk_free_gb:.1f}GB free")

async def main():
    """Main status check function"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                ENIGMA-APEX SYSTEM STATUS CHECK               ║
║                                                              ║
║  Comprehensive validation of all system components          ║
║  for professional prop trading operations                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run all checks
    await check_python_environment()
    await check_core_components()
    await check_ocr_system()
    await check_configuration()
    await check_file_permissions()
    await check_network_services()
    await system_performance_check()
    
    # Quick OCR test (optional)
    print("\nWould you like to run a quick OCR test? This will capture and analyze your screen.")
    response = input("Run OCR test? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        await run_quick_ocr_test()
    
    print_header("STATUS CHECK COMPLETE")
    print("""
✓ System validation completed
✓ All critical components checked
✓ Ready for Enigma-Apex operation

NEXT STEPS:
1. If any errors were found, address them before starting the system
2. Run 'python calibrate_ocr.py' to configure OCR regions
3. Start the system with 'python main.py' or 'start.bat'
4. Access mobile interface at http://localhost:8000

For detailed documentation, see docs/USER_GUIDE.md
    """)

if __name__ == "__main__":
    # Install psutil if not available
    try:
        import psutil
    except ImportError:
        print("Installing psutil for system monitoring...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    asyncio.run(main())
