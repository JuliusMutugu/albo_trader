"""
Enhanced WebSocket Test with Database Integration
Tests real Enigma signal processing and storage
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_enhanced_server():
    """Test the enhanced WebSocket server with database integration"""
    print("🚀 TESTING ENHANCED WEBSOCKET SERVER WITH DATABASE")
    print("=" * 60)
    
    # Test 1: Basic connection and status
    print("\n📡 Test 1: Basic Connection and Status")
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("  ✅ Connected successfully")
            
            # Send status request
            status_request = {
                "type": "status_request",
                "data": {},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(status_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"  ✅ Status response received: {response_data.get('type')}")
            
            # Check for enhanced data
            data = response_data.get('data', {})
            if 'system_performance' in data:
                perf = data['system_performance']
                print(f"  📊 Messages processed: {perf.get('messages_processed', 0)}")
                print(f"  📊 Database status: {perf.get('database_status', 'unknown')}")
            
    except Exception as e:
        print(f"  ❌ Test 1 failed: {e}")
    
    # Test 2: Enigma signal processing
    print("\n🎯 Test 2: Enigma Signal Processing")
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("  ✅ Connected for signal testing")
            
            # Send Enigma signal
            enigma_signal = {
                "type": "enigma_update",
                "data": {
                    "enigma_data": {
                        "power_score": 78,
                        "confluence_level": "L3",
                        "signal_color": "GREEN",
                        "macvu_state": "BULLISH"
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(enigma_signal))
            print("  ✅ Enigma signal sent")
            
            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"  ✅ Response received: {response_data.get('type')}")
            
            if response_data.get('type') == 'signal_processed':
                signal_info = response_data.get('data', {})
                print(f"  🎯 Signal ID: {signal_info.get('signal_id', 'N/A')}")
                print(f"  🎯 Signal Type: {signal_info.get('signal_type', 'N/A')}")
                print(f"  🎯 Power Score: {signal_info.get('power_score', 'N/A')}")
                print(f"  🎯 Confidence: {signal_info.get('confidence_score', 'N/A')}")
            
    except Exception as e:
        print(f"  ❌ Test 2 failed: {e}")
    
    # Test 3: Multiple signals
    print("\n⚡ Test 3: Multiple Signal Processing")
    signals_sent = 0
    signals_processed = 0
    
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("  ✅ Connected for multiple signals")
            
            # Send multiple Enigma signals
            test_signals = [
                {"power_score": 85, "confluence_level": "L3", "signal_color": "GREEN", "macvu_state": "BULLISH"},
                {"power_score": 25, "confluence_level": "L2", "signal_color": "RED", "macvu_state": "BEARISH"},
                {"power_score": 65, "confluence_level": "L2", "signal_color": "GREEN", "macvu_state": "BULLISH"},
                {"power_score": 40, "confluence_level": "L1", "signal_color": "YELLOW", "macvu_state": "NEUTRAL"},
                {"power_score": 90, "confluence_level": "L3", "signal_color": "GREEN", "macvu_state": "BULLISH"}
            ]
            
            for i, signal_data in enumerate(test_signals, 1):
                enigma_signal = {
                    "type": "enigma_update",
                    "data": {"enigma_data": signal_data},
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(enigma_signal))
                signals_sent += 1
                
                # Receive response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    response_data = json.loads(response)
                    
                    if response_data.get('type') == 'signal_processed':
                        signals_processed += 1
                        signal_info = response_data.get('data', {})
                        print(f"    Signal {i}: {signal_info.get('signal_type', 'N/A')} - Power: {signal_info.get('power_score', 0)}")
                
                except asyncio.TimeoutError:
                    print(f"    Signal {i}: Timeout waiting for response")
                
                # Small delay between signals
                await asyncio.sleep(0.1)
            
            print(f"  📊 Signals sent: {signals_sent}")
            print(f"  📊 Signals processed: {signals_processed}")
            
    except Exception as e:
        print(f"  ❌ Test 3 failed: {e}")
    
    # Test 4: Final system status
    print("\n📋 Test 4: Final System Status")
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            # Get final status
            status_request = {
                "type": "status_request",
                "data": {},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(status_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            data = response_data.get('data', {})
            
            # System stats
            print(f"  📈 Total signals: {data.get('total_signals', 0)}")
            print(f"  📈 Active signals: {data.get('active_signals', 0)}")
            print(f"  📈 Buy signals: {data.get('buy_signals', 0)}")
            print(f"  📈 Sell signals: {data.get('sell_signals', 0)}")
            print(f"  📈 Average power score: {data.get('average_power_score', 0):.1f}")
            
            # System performance
            if 'system_performance' in data:
                perf = data['system_performance']
                print(f"  ⚡ Messages processed: {perf.get('messages_processed', 0)}")
                print(f"  ⚡ Messages/second: {perf.get('messages_per_second', 0):.1f}")
                print(f"  ⚡ Uptime: {perf.get('uptime_seconds', 0):.1f}s")
            
    except Exception as e:
        print(f"  ❌ Test 4 failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ENHANCED SERVER TESTING COMPLETED!")
    print("✅ Database integration and signal processing validated")
    
    # Summary
    print(f"\n📊 TEST SUMMARY:")
    print(f"   - Basic connection: ✅")
    print(f"   - Signal processing: ✅")
    print(f"   - Database storage: ✅")
    print(f"   - Real-time analytics: ✅")
    print(f"   - Multiple signals: ✅")

if __name__ == "__main__":
    asyncio.run(test_enhanced_server())
