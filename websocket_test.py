"""
WebSocket Test - Direct connection test for Enigma-Apex WebSocket server
"""

import asyncio
import json
import websockets
import time

async def test_websocket_connection():
    """Test WebSocket server connectivity and basic functionality"""
    print("🔧 Testing WebSocket Connection...")
    print("Connecting to ws://localhost:8765...")
    
    try:
        # Connect to WebSocket server
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("✅ Connected to WebSocket server!")
            
            # Test 1: Send ping
            print("\n📡 Test 1: Ping/Pong")
            ping_message = {
                "type": "heartbeat",
                "data": {"message": "ping"},
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(ping_message))
            print("   Sent: ping message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                print(f"   Received: {response_data}")
                
                if response_data.get('type') == 'heartbeat':
                    print("   ✅ Ping/Pong successful")
                else:
                    print("   ⚠️  Unexpected response")
                    
            except asyncio.TimeoutError:
                print("   ⚠️  No response within 5 seconds")
            
            # Test 2: Status request
            print("\n📊 Test 2: Status Request")
            status_request = {
                "type": "status_request",
                "data": {"request": "full_status"}
            }
            
            await websocket.send(json.dumps(status_request))
            print("   Sent: status request")
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                print(f"   Received: {response_data.get('type', 'unknown')}")
                
                if 'enigma_data' in response_data.get('data', {}):
                    print("   ✅ Status response includes Enigma data")
                else:
                    print("   ⚠️  Status response missing expected data")
                    
            except asyncio.TimeoutError:
                print("   ⚠️  No status response within 5 seconds")
            
            # Test 3: Keep connection alive for a few seconds
            print("\n⏱️  Test 3: Connection Stability")
            print("   Maintaining connection for 10 seconds...")
            
            start_time = time.time()
            messages_received = 0
            
            while time.time() - start_time < 10:
                try:
                    # Check for any incoming messages
                    response = await asyncio.wait_for(websocket.recv(), timeout=1)
                    messages_received += 1
                    print(f"   📨 Message {messages_received}: {json.loads(response).get('type', 'unknown')}")
                    
                except asyncio.TimeoutError:
                    # No message received, that's okay
                    pass
                except Exception as e:
                    print(f"   ⚠️  Error receiving message: {e}")
                    break
            
            print(f"   ✅ Connection stable - {messages_received} messages received")
            
            print("\n🎉 WebSocket test completed successfully!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused - WebSocket server may not be running")
        print("   Make sure the Enigma-Apex system is started with: python main.py")
        
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

async def test_ninja_trader_endpoint():
    """Test NinjaTrader specific endpoint"""
    print("\n🥷 Testing NinjaTrader Endpoint...")
    
    try:
        async with websockets.connect('ws://localhost:8765/ninja') as websocket:
            print("✅ Connected to NinjaTrader endpoint!")
            
            # Send NinjaTrader identification
            ninja_hello = {
                "type": "client_identification",
                "data": {
                    "client_type": "ninja_dashboard",
                    "version": "1.0.0"
                }
            }
            
            await websocket.send(json.dumps(ninja_hello))
            print("   Sent: NinjaTrader identification")
            
            # Wait for dashboard data
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                print(f"   Received: {response_data.get('type', 'unknown')}")
                
                if 'enigma_data' in response_data.get('data', {}):
                    enigma_data = response_data['data']['enigma_data']
                    print(f"   📊 Power Score: {enigma_data.get('power_score', 'N/A')}")
                    print(f"   📊 Confluence: {enigma_data.get('confluence_level', 'N/A')}")
                    print(f"   📊 Signal Color: {enigma_data.get('signal_color', 'N/A')}")
                    print("   ✅ NinjaTrader endpoint working correctly")
                    
            except asyncio.TimeoutError:
                print("   ⚠️  No dashboard data received")
                
    except Exception as e:
        print(f"❌ NinjaTrader endpoint test failed: {e}")

async def main():
    """Run all WebSocket tests"""
    print("🚀 ENIGMA-APEX WEBSOCKET TEST SUITE")
    print("=" * 50)
    
    await test_websocket_connection()
    await test_ninja_trader_endpoint()
    
    print("\n" + "=" * 50)
    print("WebSocket testing complete!")
    print("\nIf tests passed:")
    print("✅ Your NinjaTrader dashboard can connect to: ws://localhost:8765/ninja")
    print("✅ Mobile apps can connect to: ws://localhost:8765")
    print("✅ Real-time data streaming is operational")

if __name__ == "__main__":
    asyncio.run(main())
