"""
NinjaTrader WebSocket Integration Test
Tests the exact connection pattern that NinjaTrader dashboard will use
"""

import asyncio
import json
import websockets
import time

async def test_ninja_integration():
    """Test NinjaTrader dashboard integration"""
    print("🥷 NINJATRADER WEBSOCKET INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Connect to NinjaTrader endpoint
        print("1. Connecting to NinjaTrader endpoint...")
        async with websockets.connect('ws://localhost:8765/ninja') as websocket:
            print("✅ Connected to ws://localhost:8765/ninja")
            
            # Step 1: Send client identification (what NinjaTrader will do)
            print("\n2. Sending client identification...")
            identification = {
                "type": "client_identification",
                "data": {
                    "client_type": "ninja_dashboard",
                    "version": "1.0.0",
                    "capabilities": ["real_time_updates", "trade_signals"]
                }
            }
            await websocket.send(json.dumps(identification))
            print("✅ Sent client identification")
            
            # Receive welcome message
            try:
                welcome = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"✅ Received welcome: {welcome[:100]}...")
            except asyncio.TimeoutError:
                print("⏰ No welcome message (might be normal)")
            
            # Step 2: Request current status (what dashboard needs)
            print("\n3. Requesting current Enigma status...")
            status_request = {
                "type": "status_request",
                "data": {
                    "request": "full_status",
                    "include": ["enigma_data", "kelly_data", "compliance"]
                }
            }
            await websocket.send(json.dumps(status_request))
            print("✅ Sent status request")
            
            # Receive status response
            try:
                status_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                status_data = json.loads(status_response)
                print(f"✅ Received status response")
                
                # Check for required data
                if 'enigma_data' in status_data.get('data', {}):
                    enigma_data = status_data['data']['enigma_data']
                    print(f"   📊 Power Score: {enigma_data.get('power_score', 'N/A')}")
                    print(f"   📊 Confluence: {enigma_data.get('confluence_level', 'N/A')}")
                    print(f"   📊 Signal Color: {enigma_data.get('signal_color', 'N/A')}")
                    print(f"   📊 MACVU State: {enigma_data.get('macvu_state', 'N/A')}")
                else:
                    print("   ⚠️  No Enigma data in response")
                    
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for status response")
                return False
            
            # Step 3: Send heartbeat to maintain connection
            print("\n4. Testing heartbeat maintenance...")
            heartbeat = {
                "type": "heartbeat",
                "data": {"message": "ninja_ping"},
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(heartbeat))
            print("✅ Sent heartbeat")
            
            # Receive heartbeat response
            try:
                heartbeat_response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"✅ Received heartbeat response: {heartbeat_response[:50]}...")
            except asyncio.TimeoutError:
                print("❌ No heartbeat response")
                return False
            
            print("\n🎉 ALL TESTS PASSED!")
            print("🚀 NinjaTrader dashboard is ready to connect!")
            print("\nConnection Details:")
            print("  Endpoint: ws://localhost:8765/ninja")
            print("  Protocol: JSON message exchange")
            print("  Features: ✅ Identification, ✅ Status, ✅ Heartbeat")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_ninja_integration())
    if result:
        print("\n✅ Ready for production use!")
    else:
        print("\n❌ Integration needs work")
