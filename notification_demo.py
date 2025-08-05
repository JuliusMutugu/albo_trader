"""
Live Desktop Notification Demo
Sends real-time signals to the WebSocket server to demonstrate notifications
"""

import asyncio
import json
import websockets
import time
from datetime import datetime
import random

class NotificationDemo:
    """Demo class for testing desktop notifications with live signals"""
    
    def __init__(self):
        self.server_url = 'ws://localhost:8765'
        self.demo_signals = [
            {
                "symbol": "EURUSD",
                "signal_type": "L3", 
                "power_score": 95,
                "signal_direction": "BUY",
                "confluence_level": "L3",
                "signal_color": "GREEN"
            },
            {
                "symbol": "GBPUSD", 
                "signal_type": "L2",
                "power_score": 82,
                "signal_direction": "SELL",
                "confluence_level": "L2", 
                "signal_color": "RED"
            },
            {
                "symbol": "USDJPY",
                "signal_type": "L3", 
                "power_score": 88,
                "signal_direction": "BUY",
                "confluence_level": "L3",
                "signal_color": "GREEN"
            },
            {
                "symbol": "AUDUSD",
                "signal_type": "L1", 
                "power_score": 55,
                "signal_direction": "SELL",
                "confluence_level": "L1",
                "signal_color": "YELLOW"
            },
            {
                "symbol": "USDCAD",
                "signal_type": "L2", 
                "power_score": 78,
                "signal_direction": "BUY",
                "confluence_level": "L2",
                "signal_color": "GREEN"
            }
        ]
    
    async def send_signal_burst(self):
        """Send a burst of signals to test notifications"""
        print("🚀 DESKTOP NOTIFICATION LIVE DEMO")
        print("=" * 50)
        print("🎯 This demo will send live Enigma signals to your WebSocket server")
        print("🔔 Watch for desktop notifications to appear!")
        print("=" * 50)
        
        try:
            async with websockets.connect(self.server_url) as websocket:
                print("✅ Connected to WebSocket server")
                
                # Send client identification
                await websocket.send(json.dumps({
                    "type": "client_identification",
                    "data": {
                        "client_type": "external_api",
                        "version": "1.0.0"
                    }
                }))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print("📡 Server connection established")
                
                # Send signals with dramatic pauses
                for i, signal in enumerate(self.demo_signals, 1):
                    print(f"\n📤 Signal {i}/{len(self.demo_signals)}: {signal['symbol']}")
                    print(f"   💪 Power Score: {signal['power_score']}")
                    print(f"   📊 Direction: {signal['signal_direction']}")
                    print(f"   🎯 Level: {signal['signal_type']}")
                    
                    # Add timestamp
                    signal_with_timestamp = {
                        **signal,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send the signal
                    message = {
                        "type": "enigma_update",
                        "data": {
                            "enigma_data": signal_with_timestamp
                        }
                    }
                    
                    await websocket.send(json.dumps(message))
                    print("   ✅ Signal sent to server")
                    print("   🔔 Desktop notification should appear now!")
                    
                    # Dramatic pause between signals
                    if i < len(self.demo_signals):
                        print("   ⏱️  Waiting 4 seconds for next signal...")
                        await asyncio.sleep(4)
                
                print(f"\n🎉 Demo complete! Sent {len(self.demo_signals)} signals with notifications")
                
        except ConnectionRefusedError:
            print("❌ Could not connect to WebSocket server")
            print("💡 Please start the server first:")
            print("   python start_server_with_notifications.py")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
    
    async def send_critical_alert(self):
        """Send a critical signal to test high-priority notifications"""
        print("\n🚨 SENDING CRITICAL ALERT SIGNAL")
        print("=" * 40)
        
        critical_signal = {
            "symbol": "XAUUSD",  # Gold
            "signal_type": "L3",
            "power_score": 98,  # Very high score
            "signal_direction": "BUY", 
            "confluence_level": "L3",
            "signal_color": "GREEN",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with websockets.connect(self.server_url) as websocket:
                print("📡 Connected for critical alert")
                
                # Send identification
                await websocket.send(json.dumps({
                    "type": "client_identification",
                    "data": {"client_type": "external_api", "version": "1.0.0"}
                }))
                
                await asyncio.wait_for(websocket.recv(), timeout=3)
                
                # Send critical signal
                message = {
                    "type": "enigma_update",
                    "data": {"enigma_data": critical_signal}
                }
                
                await websocket.send(json.dumps(message))
                print(f"🔥 CRITICAL SIGNAL SENT: {critical_signal['symbol']} (Score: {critical_signal['power_score']})")
                print("🔔 High-priority notification should appear!")
                
        except Exception as e:
            print(f"❌ Critical alert error: {e}")
    
    async def interactive_demo(self):
        """Interactive demo that lets user control signal sending"""
        print("\n🎮 INTERACTIVE NOTIFICATION DEMO")
        print("=" * 40)
        print("Press Enter to send signals one by one...")
        print("Type 'quit' to exit")
        
        try:
            async with websockets.connect(self.server_url) as websocket:
                # Send identification
                await websocket.send(json.dumps({
                    "type": "client_identification", 
                    "data": {"client_type": "external_api", "version": "1.0.0"}
                }))
                
                await asyncio.wait_for(websocket.recv(), timeout=3)
                print("✅ Ready for interactive demo")
                
                for signal in self.demo_signals:
                    print(f"\n📊 Next signal ready: {signal['symbol']} (Score: {signal['power_score']})")
                    user_input = input("Press Enter to send (or 'quit' to exit): ").strip().lower()
                    
                    if user_input == 'quit':
                        break
                    
                    # Send signal
                    signal_with_timestamp = {**signal, "timestamp": datetime.now().isoformat()}
                    message = {
                        "type": "enigma_update",
                        "data": {"enigma_data": signal_with_timestamp}
                    }
                    
                    await websocket.send(json.dumps(message))
                    print("🔔 Signal sent! Check for desktop notification!")
                
                print("Demo finished!")
                
        except Exception as e:
            print(f"❌ Interactive demo error: {e}")

async def main():
    """Main demo function"""
    demo = NotificationDemo()
    
    print("🔔 ENIGMA-APEX DESKTOP NOTIFICATION DEMO")
    print("=" * 60)
    print("Choose a demo mode:")
    print("1. Automatic signal burst (5 signals with 4-second intervals)")
    print("2. Critical alert test (high-priority notification)")
    print("3. Interactive mode (manual signal sending)")
    print("4. All demos")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        await demo.send_signal_burst()
    elif choice == "2":
        await demo.send_critical_alert()
    elif choice == "3":
        await demo.interactive_demo()
    elif choice == "4":
        print("\n🎯 Running all demos...")
        await demo.send_signal_burst()
        await asyncio.sleep(2)
        await demo.send_critical_alert()
        await asyncio.sleep(2)
        await demo.interactive_demo()
    else:
        print("❌ Invalid choice. Running automatic demo...")
        await demo.send_signal_burst()

if __name__ == "__main__":
    asyncio.run(main())
