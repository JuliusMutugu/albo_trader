"""
OCR Visual Test - Save captured regions as images for inspection
"""

import asyncio
import sys
from pathlib import Path
import cv2
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ocr.ocr_processor import OCRProcessor

async def visual_test():
    """Visual test - save captured regions as images"""
    print("📷 OCR Visual Test - Capturing and saving region images")
    
    # Create output directory
    output_dir = Path("test_captures")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize OCR
    ocr = OCRProcessor()
    await ocr.initialize()
    
    print(f"Regions configured: {len(ocr.regions)}")
    for name, config in ocr.regions.items():
        coords = config['coordinates']
        print(f"  - {name}: [{coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}]")
    
    # Capture regions
    captures = await ocr._capture_all_regions()
    
    if captures:
        print(f"\nCaptured {len(captures)} regions:")
        
        for region_name, image in captures.items():
            # Save the captured image
            filename = output_dir / f"{region_name}_capture.png"
            
            # Convert to BGR for OpenCV
            if len(image.shape) == 3:
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image
                
            cv2.imwrite(str(filename), image_bgr)
            
            print(f"  ✅ {region_name}: {image.shape} -> {filename}")
            
            # Try OCR on this region
            try:
                result = await ocr._process_region(region_name, image)
                if result:
                    print(f"     OCR: '{result.text}' (confidence: {result.confidence:.2f})")
                else:
                    print(f"     OCR: No text detected")
            except Exception as e:
                print(f"     OCR Error: {e}")
    
    print(f"\n📁 Images saved to: {output_dir.absolute()}")
    print("🔍 Inspect the captured images to verify OCR regions are correct")
    
    await ocr.cleanup()

if __name__ == "__main__":
    asyncio.run(visual_test())
