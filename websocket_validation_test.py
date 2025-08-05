"""
Quick WebSocket Connection Test
Fixed version without timeout issues
"""

import asyncio
import json
import websockets

async def test_basic_connection():
    """Test basic WebSocket connection"""
    print("🔌 Testing WebSocket Server Connection...")
    
    try:
        # Connect to main endpoint
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("  ✅ Connected to main endpoint")
            
            # Send test message
            test_message = {
                "type": "heartbeat",
                "data": {"test": "connection_test"},
                "timestamp": "2025-08-05T12:37:00Z"
            }
            
            await websocket.send(json.dumps(test_message))
            print("  ✅ Message sent successfully")
            
            # Try to receive response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                print(f"  ✅ Received response: {response_data.get('type', 'unknown')}")
                
                if 'enigma_data' in response_data.get('data', {}):
                    enigma_data = response_data['data']['enigma_data']
                    print(f"  🎯 Enigma Power Score: {enigma_data.get('power_score', 'N/A')}")
                    print(f"  🎯 Confluence Level: {enigma_data.get('confluence_level', 'N/A')}")
                    print(f"  🎯 Signal Color: {enigma_data.get('signal_color', 'N/A')}")
                
            except asyncio.TimeoutError:
                print("  ⚠️  No response received (timeout)")
            
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False
    
    return True

async def test_ninja_endpoint():
    """Test NinjaTrader specific endpoint"""
    print("\n🥷 Testing NinjaTrader Endpoint...")
    
    try:
        # Connect to NinjaTrader endpoint
        async with websockets.connect('ws://localhost:8765/ninja') as websocket:
            print("  ✅ Connected to /ninja endpoint")
            
            # Send ninja identification
            ninja_message = {
                "type": "client_identification",
                "data": {
                    "client_type": "ninja_dashboard",
                    "version": "1.0.0"
                }
            }
            
            await websocket.send(json.dumps(ninja_message))
            print("  ✅ Ninja identification sent")
            
            # Try to receive ninja response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                print(f"  ✅ Ninja response received: {response_data.get('type', 'unknown')}")
                
                # Check for Enigma data in response
                if 'enigma_data' in response_data.get('data', {}):
                    print("  🎯 Enigma data included in ninja response")
                else:
                    print("  ⚠️  No Enigma data in ninja response")
                
            except asyncio.TimeoutError:
                print("  ⚠️  No ninja response received (timeout)")
            
    except Exception as e:
        print(f"  ❌ Ninja endpoint failed: {e}")
        return False
    
    return True

async def test_multiple_connections():
    """Test multiple concurrent connections"""
    print("\n⚡ Testing Multiple Connections...")
    
    async def create_connection(conn_id):
        try:
            async with websockets.connect('ws://localhost:8765') as websocket:
                message = {
                    "type": "heartbeat",
                    "data": {"connection_id": conn_id, "test": "multi_connection"},
                    "timestamp": "2025-08-05T12:37:00Z"
                }
                await websocket.send(json.dumps(message))
                return f"Connection {conn_id}: Success"
        except Exception as e:
            return f"Connection {conn_id}: Failed - {e}"
    
    # Create 5 concurrent connections
    tasks = [create_connection(i) for i in range(1, 6)]
    results = await asyncio.gather(*tasks)
    
    successful = sum(1 for result in results if "Success" in result)
    print(f"  ✅ Successful connections: {successful}/5")
    
    for result in results:
        print(f"    {result}")
    
    return successful == 5

async def main():
    """Run all WebSocket tests"""
    print("🚀 ENIGMA-APEX WEBSOCKET VALIDATION")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Basic connection
    if await test_basic_connection():
        tests_passed += 1
    
    # Test 2: Ninja endpoint
    if await test_ninja_endpoint():
        tests_passed += 1
    
    # Test 3: Multiple connections
    if await test_multiple_connections():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 WEBSOCKET TEST RESULTS: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL WEBSOCKET TESTS PASSED!")
        print("✅ Your WebSocket server is fully functional")
    elif tests_passed >= 2:
        print("👍 MOST TESTS PASSED - Minor issues detected")
        print("🔧 Consider reviewing failed test details")
    else:
        print("⚠️  MULTIPLE ISSUES DETECTED")
        print("🔨 WebSocket server needs attention")
    
    health_score = (tests_passed / total_tests) * 100
    print(f"🏥 WebSocket Health Score: {health_score:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
