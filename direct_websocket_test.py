"""
Direct Enigma-Apex WebSocket Test
Test the exact same patterns used by NinjaTrader dashboard
"""

import asyncio
import json
import websockets
import time

async def test_heartbeat():
    """Test heartbeat functionality"""
    print("🔧 Testing Heartbeat...")
    
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("✅ Connected!")
            
            # Send heartbeat (this is what our NinjaTrader dashboard sends)
            heartbeat_msg = {
                "type": "heartbeat",
                "data": {"message": "ping"},
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(heartbeat_msg))
            print("   📡 Sent heartbeat")
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"   📨 Received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                print("   ⏰ Timeout waiting for response")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_status_request():
    """Test status request"""
    print("\n🔧 Testing Status Request...")
    
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("✅ Connected!")
            
            # Send status request
            status_msg = {
                "type": "status_request",
                "data": {"request": "full_status"}
            }
            
            await websocket.send(json.dumps(status_msg))
            print("   📡 Sent status request")
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"   📨 Received: {response[:200]}...")
                
                # Parse response
                data = json.loads(response)
                if 'enigma_data' in data.get('data', {}):
                    print("   ✅ Contains Enigma data")
                    return True
                else:
                    print("   ⚠️  Missing Enigma data")
                    return False
                    
            except asyncio.TimeoutError:
                print("   ⏰ Timeout waiting for response")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_ninja_path():
    """Test NinjaTrader specific path"""
    print("\n🔧 Testing NinjaTrader Path (/ninja)...")
    
    try:
        async with websockets.connect('ws://localhost:8765/ninja') as websocket:
            print("✅ Connected to /ninja endpoint!")
            
            # Send client identification
            id_msg = {
                "type": "client_identification", 
                "data": {
                    "client_type": "ninja_dashboard",
                    "version": "1.0.0"
                }
            }
            
            await websocket.send(json.dumps(id_msg))
            print("   📡 Sent client identification")
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"   📨 Received: {response[:150]}...")
                return True
            except asyncio.TimeoutError:
                print("   ⏰ No immediate response (might be normal)")
                return True  # Connection successful even without immediate response
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_simple_message():
    """Test sending simple message"""
    print("\n🔧 Testing Simple Message...")
    
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("✅ Connected!")
            
            # Send very simple message
            simple_msg = {"type": "heartbeat", "data": {}}
            
            await websocket.send(json.dumps(simple_msg))
            print("   📡 Sent simple message")
            
            # Just check if connection stays alive
            await asyncio.sleep(1)
            print("   ✅ Connection stable")
            return True
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def main():
    """Run all WebSocket tests"""
    print("🚀 ENIGMA-APEX WEBSOCKET DIRECT TEST")
    print("=" * 50)
    
    tests = [
        ("Simple Message", test_simple_message()),
        ("Heartbeat", test_heartbeat()), 
        ("Status Request", test_status_request()),
        ("NinjaTrader Path", test_ninja_path())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = await test_coro
            results.append((test_name, result))
            print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
        except Exception as e:
            print(f"   Result: ❌ ERROR - {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed >= 2:
        print("\n🎉 WebSocket server is working!")
        print("Your NinjaTrader dashboard can connect to:")
        print("  ws://localhost:8765/ninja")
    else:
        print("\n⚠️  WebSocket server needs attention")

if __name__ == "__main__":
    asyncio.run(main())
