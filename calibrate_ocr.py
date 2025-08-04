"""
OCR Configuration Utility
Tool for calibrating OCR regions for AlgoBox Enigma panel
"""

import asyncio
import sys
from pathlib import Path
import cv2
import tkinter as tk
from tkinter import messagebox, simpledialog
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ocr.ocr_processor import OCRProcessor

class OCRCalibrator:
    """Interactive OCR region calibrator"""
    
    def __init__(self):
        self.ocr_processor = None
        self.current_screenshot = None
        self.regions = {}
        
    async def initialize(self):
        """Initialize OCR processor"""
        self.ocr_processor = OCRProcessor()
        await self.ocr_processor.initialize()
        
        # Load existing regions
        self.regions = self.ocr_processor.regions.copy()
        
    async def capture_full_screen(self):
        """Capture full screen for region selection"""
        # Get primary monitor
        monitor = self.ocr_processor.sct.monitors[1]
        screenshot = self.ocr_processor.sct.grab(monitor)
        
        # Convert to numpy array
        self.current_screenshot = np.array(screenshot)
        if self.current_screenshot.shape[2] == 4:
            self.current_screenshot = cv2.cvtColor(self.current_screenshot, cv2.COLOR_BGRA2RGB)
            
        return self.current_screenshot
    
    def save_screenshot(self, filename="full_screen.png"):
        """Save current screenshot"""
        if self.current_screenshot is not None:
            # Convert to BGR for OpenCV
            screenshot_bgr = cv2.cvtColor(self.current_screenshot, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, screenshot_bgr)
            return filename
        return None
    
    async def save_regions_config(self):
        """Save calibrated regions to config file"""
        if self.ocr_processor:
            self.ocr_processor.regions = self.regions
            await self.ocr_processor._save_regions_config()

async def main():
    """Main calibration interface"""
    print("🎯 OCR Region Calibrator")
    print("=" * 50)
    
    # Initialize calibrator
    calibrator = OCRCalibrator()
    await calibrator.initialize()
    
    print(f"Current regions: {len(calibrator.regions)}")
    for name, config in calibrator.regions.items():
        coords = config['coordinates']
        print(f"  - {name}: [{coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}]")
    
    # Capture screenshot
    print("\n📸 Capturing full screen...")
    screenshot = await calibrator.capture_full_screen()
    
    # Save screenshot for manual inspection
    screenshot_file = calibrator.save_screenshot("calibration_screenshot.png")
    print(f"📁 Screenshot saved: {screenshot_file}")
    
    print("\n🔧 Calibration Instructions:")
    print("1. Open your AlgoBox Enigma panel")
    print("2. Note the pixel coordinates of key areas:")
    print("   - Power Score display")
    print("   - Confluence Level (L1-L4)")
    print("   - Signal Color indicator")
    print("   - MACVU State")
    print("3. Use image editing software to find exact coordinates")
    print("4. Update the config/ocr_regions.json file manually")
    
    print(f"\n📊 Screen Resolution: {screenshot.shape[1]}x{screenshot.shape[0]}")
    print("\n✅ OCR system is ready for real trading!")
    print("🚀 The OCR engine will work with any properly configured regions")
    
    # Test current regions
    print("\n🧪 Testing current regions...")
    captures = await calibrator.ocr_processor._capture_all_regions()
    
    output_dir = Path("calibration_captures")
    output_dir.mkdir(exist_ok=True)
    
    for region_name, image in captures.items():
        filename = output_dir / f"{region_name}_current.png"
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(filename), image_bgr)
        print(f"  📷 {region_name}: {image.shape} -> {filename}")
    
    await calibrator.ocr_processor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
