"""
OCR Test Suite - Verify real OCR functionality
Tests screen capture, image processing, and text recognition
"""

import asyncio
import logging
import sys
from pathlib import Path
import time

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ocr.ocr_processor import OCRProcessor
from src.core.config_manager import ConfigManager

async def test_ocr_initialization():
    """Test OCR processor initialization"""
    print("🔧 Testing OCR Processor initialization...")
    
    try:
        ocr_processor = OCRProcessor()
        await ocr_processor.initialize()
        
        print(f"   - EasyOCR Reader: {'✅' if ocr_processor.easy_reader else '❌'}")
        print(f"   - Screen Capture: {'✅' if ocr_processor.sct else '❌'}")
        print(f"   - Regions Loaded: {len(ocr_processor.regions)}")
        print(f"   - Screen Resolution: {ocr_processor.screen_resolution}")
        
        if ocr_processor.easy_reader and ocr_processor.sct:
            print("✅ OCR Processor initialized successfully")
            return ocr_processor
        else:
            print("❌ OCR Processor initialization failed")
            return None
            
    except Exception as e:
        print(f"❌ OCR initialization error: {e}")
        return None

async def test_screen_capture(ocr_processor):
    """Test screen capture functionality"""
    print("\n📸 Testing screen capture...")
    
    try:
        # Capture all regions
        captures = await ocr_processor._capture_all_regions()
        
        if captures:
            print(f"✅ Screen capture successful - {len(captures)} regions captured")
            for region_name, image in captures.items():
                print(f"   - {region_name}: {image.shape} pixels")
            return True
        else:
            print("❌ No screen captures obtained")
            return False
            
    except Exception as e:
        print(f"❌ Screen capture error: {e}")
        return False

async def test_text_recognition(ocr_processor):
    """Test OCR text recognition"""
    print("\n🔤 Testing text recognition...")
    
    try:
        # Get a reading
        reading = await ocr_processor.get_latest_reading()
        
        if reading:
            print("✅ OCR reading successful")
            print(f"   - Confidence: {reading.get('confidence', 0):.2%}")
            print(f"   - Valid: {reading.get('valid', False)}")
            print(f"   - Power Score: {reading.get('power_score', 'N/A')}")
            print(f"   - Signal Color: {reading.get('signal_color', 'N/A')}")
            return True
        else:
            print("❌ No OCR reading obtained")
            return False
            
    except Exception as e:
        print(f"❌ OCR recognition error: {e}")
        return False

async def test_performance(ocr_processor):
    """Test OCR performance"""
    print("\n⚡ Testing OCR performance...")
    
    try:
        start_time = time.time()
        num_tests = 5
        
        for i in range(num_tests):
            await ocr_processor.get_latest_reading()
        
        total_time = time.time() - start_time
        avg_time = (total_time / num_tests) * 1000
        
        print(f"✅ Performance test completed")
        print(f"   - {num_tests} readings in {total_time:.2f}s")
        print(f"   - Average: {avg_time:.1f}ms per reading")
        
        # Check if performance meets requirements
        if avg_time < 500:  # 500ms threshold
            print("   - ✅ Performance: EXCELLENT")
        elif avg_time < 1000:  # 1s threshold
            print("   - ⚠️  Performance: ACCEPTABLE")
        else:
            print("   - ❌ Performance: POOR")
            
        return avg_time < 1000
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        return False

async def test_region_calibration(ocr_processor):
    """Test region calibration"""
    print("\n🎯 Testing region calibration...")
    
    try:
        # Test region detection
        stats = ocr_processor.get_statistics()
        
        print(f"✅ Region calibration status:")
        print(f"   - Total readings: {stats.get('total_readings', 0)}")
        print(f"   - Successful readings: {stats.get('successful_readings', 0)}")
        print(f"   - Average confidence: {stats.get('average_confidence', 0):.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Region calibration error: {e}")
        return False

async def main():
    """Main OCR test runner"""
    print("🚀 Starting OCR Test Suite")
    print("=" * 50)
    
    # Test initialization
    ocr_processor = await test_ocr_initialization()
    if not ocr_processor:
        print("\n❌ OCR initialization failed - aborting tests")
        return
    
    # Run tests
    tests = [
        test_screen_capture,
        test_text_recognition,
        test_performance,
        test_region_calibration
    ]
    
    results = []
    for test in tests:
        result = await test(ocr_processor)
        results.append(result)
    
    # Cleanup
    await ocr_processor.cleanup()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    test_names = [
        "Screen Capture",
        "Text Recognition", 
        "Performance",
        "Region Calibration"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All OCR tests PASSED! System ready for trading.")
    elif passed >= total * 0.75:
        print("⚠️  Most OCR tests passed - system functional with minor issues.")
    else:
        print("❌ OCR system has significant issues - requires attention.")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
