"""
Quick System Test - Verify Enigma-Apex is running correctly
"""

import asyncio
import sys
import json
from pathlib import Path
import aiohttp
import websockets

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

async def test_mobile_interface():
    """Test the mobile interface"""
    print("🔧 Testing Mobile Interface...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test root endpoint
            async with session.get('http://localhost:8000') as response:
                if response.status == 200:
                    print("✅ Mobile Interface: ONLINE")
                    return True
                else:
                    print(f"❌ Mobile Interface: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Mobile Interface: {e}")
        return False

async def test_websocket_server():
    """Test the WebSocket server"""
    print("🔧 Testing WebSocket Server...")
    
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get('type') == 'pong':
                print("✅ WebSocket Server: ONLINE")
                return True
            else:
                print(f"❌ WebSocket Server: Unexpected response {data}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket Server: {e}")
        return False

async def test_ocr_system():
    """Test OCR system"""
    print("🔧 Testing OCR System...")
    
    try:
        from src.ocr.ocr_processor import OCRProcessor
        
        ocr = OCRProcessor()
        await ocr.initialize()
        
        # Test signal reading
        result = await ocr.read_enigma_signals()
        
        if result['status'] in ['success', 'no_signal']:
            print("✅ OCR System: OPERATIONAL")
            print(f"   Status: {result['status']}")
            print(f"   Data: {result['data']}")
            return True
        else:
            print(f"❌ OCR System: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ OCR System: {e}")
        return False

async def main():
    """Run all system tests"""
    print("🚀 ENIGMA-APEX SYSTEM TEST")
    print("=" * 40)
    
    tests = [
        test_mobile_interface(),
        test_websocket_server(),
        test_ocr_system()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    passed = sum(1 for result in results if result is True)
    total = len(results)
    
    print("\n" + "=" * 40)
    print(f"SYSTEM TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n✅ Ready for trading operations")
        print("📱 Mobile Interface: http://localhost:8000")
        print("🔌 NinjaTrader WebSocket: ws://localhost:8765")
        print("👤 Login: trader1 / secure123")
    else:
        print("⚠️  Some systems need attention")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   Test {i+1}: {result}")

if __name__ == "__main__":
    asyncio.run(main())
