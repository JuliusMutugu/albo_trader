"""
Debug OCR region loading
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ocr.ocr_processor import OCRProcessor

async def debug_regions():
    print("🔍 Debugging OCR region loading...")
    
    ocr = OCRProcessor()
    
    # Test default regions
    default_regions = ocr._get_default_regions()
    print(f"Default regions count: {len(default_regions)}")
    for name, config in default_regions.items():
        print(f"  - {name}: {config}")
    
    # Test initialization
    await ocr.initialize()
    print(f"After init regions count: {len(ocr.regions)}")
    
    # Check config path
    print(f"Config path: {ocr.regions_config_path}")
    print(f"Config path exists: {ocr.regions_config_path.exists()}")

if __name__ == "__main__":
    asyncio.run(debug_regions())
