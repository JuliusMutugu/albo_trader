"""
Test Desktop Notifications with Enhanced WebSocket Server
Simulates Enigma signals and tests notification delivery
"""

import asyncio
import json
import websockets
import time
from datetime import datetime

async def test_notifications_with_server():
    """Test desktop notifications through WebSocket server"""
    print("🧪 Testing Desktop Notifications with WebSocket Server")
    print("=" * 60)
    
    # Test signals with different power scores
    test_signals = [
        {
            "symbol": "EURUSD",
            "signal_type": "L3", 
            "power_score": 95,
            "signal_direction": "BUY",
            "confluence_level": "L3",
            "signal_color": "GREEN",
            "timestamp": datetime.now().isoformat()
        },
        {
            "symbol": "GBPUSD", 
            "signal_type": "L2",
            "power_score": 75,
            "signal_direction": "SELL",
            "confluence_level": "L2", 
            "signal_color": "RED",
            "timestamp": datetime.now().isoformat()
        },
        {
            "symbol": "USDJPY",
            "signal_type": "L1", 
            "power_score": 45,
            "signal_direction": "BUY",
            "confluence_level": "L1",
            "signal_color": "YELLOW", 
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    try:
        print("📡 Connecting to WebSocket server...")
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("✅ Connected to server")
            
            # Send client identification
            client_msg = {
                "type": "client_identification",
                "data": {
                    "client_type": "external_api",
                    "version": "1.0.0"
                }
            }
            
            await websocket.send(json.dumps(client_msg))
            print("📤 Sent client identification")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"📥 Server response: {json.loads(response).get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⚠️  No response from server")
            
            # Send test signals
            for i, signal in enumerate(test_signals, 1):
                print(f"\n📤 Sending test signal {i}/{len(test_signals)}: {signal['symbol']} (Score: {signal['power_score']})")
                
                enigma_message = {
                    "type": "enigma_update",
                    "data": {
                        "enigma_data": signal
                    }
                }
                
                await websocket.send(json.dumps(enigma_message))
                print(f"✅ Signal sent - Desktop notification should appear!")
                
                # Wait between signals to see notifications clearly
                await asyncio.sleep(3)
            
            print(f"\n🎉 All {len(test_signals)} test signals sent!")
            print("💡 Check your desktop for notification popups")
            
    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket server")
        print("💡 Make sure the enhanced WebSocket server is running")
        print("   Run: python enhanced_websocket_server.py")
        
    except Exception as e:
        print(f"❌ Test error: {e}")

async def test_direct_notifications():
    """Test desktop notifications directly"""
    print("\n🧪 Testing Direct Desktop Notifications")
    print("=" * 50)
    
    from desktop_notifier import DesktopNotifier
    
    notifier = DesktopNotifier()
    
    # Test different signal types
    test_signals = [
        {
            'symbol': 'EURUSD',
            'type': 'L3',
            'power_score': 92,
            'direction': 'BUY',
            'timestamp': time.time()
        },
        {
            'symbol': 'GBPUSD', 
            'type': 'L2',
            'power_score': 68,
            'direction': 'SELL',
            'timestamp': time.time()
        }
    ]
    
    for signal in test_signals:
        print(f"📤 Sending direct notification: {signal['symbol']} (Score: {signal['power_score']})")
        success = await notifier.send_signal_notification(signal)
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
        await asyncio.sleep(2)
    
    # Get notification stats
    stats = notifier.get_notification_stats()
    print(f"\n📊 Notification Statistics:")
    print(f"Total sent: {stats['total_sent']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Average power score: {stats['average_power_score']:.1f}")

async def main():
    """Run all notification tests"""
    print("🚀 DESKTOP NOTIFICATION TESTING SUITE")
    print("=" * 60)
    
    # Test direct notifications first
    await test_direct_notifications()
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Test notifications through WebSocket server
    await test_notifications_with_server()
    
    print("\n" + "=" * 60)
    print("🎯 TESTING COMPLETE")
    print("\nNotifications should have appeared on your desktop!")
    print("If you didn't see any notifications:")
    print("1. Check Windows notification settings")
    print("2. Make sure notifications are enabled for Python")
    print("3. Try running as administrator if needed")

if __name__ == "__main__":
    asyncio.run(main())
