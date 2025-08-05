"""
NinjaTrader Testing Client - Simulate Enigma Signals
Send test signals to NinjaTrader indicators for real-time testing
"""

import asyncio
import websockets
import json
import time
import random
from datetime import datetime

class NinjaTesterClient:
    """Client to send test signals to NinjaTrader indicators"""
    
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.test_signals = [
            {
                "symbol": "EURUSD",
                "power_score": 85,
                "signal_color": "green",
                "macvu_state": "BULLISH",
                "confluence_level": 4,
                "direction": "BUY"
            },
            {
                "symbol": "GBPUSD", 
                "power_score": 78,
                "signal_color": "green",
                "macvu_state": "BULLISH",
                "confluence_level": 3,
                "direction": "BUY"
            },
            {
                "symbol": "AUDUSD",
                "power_score": 72,
                "signal_color": "red", 
                "macvu_state": "BEARISH",
                "confluence_level": 2,
                "direction": "SELL"
            },
            {
                "symbol": "USDJPY",
                "power_score": 90,
                "signal_color": "green",
                "macvu_state": "BULLISH", 
                "confluence_level": 5,
                "direction": "BUY"
            }
        ]
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"✅ Connected to {self.uri}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def send_test_signal(self, signal):
        """Send a test signal to the server"""
        if not self.websocket:
            return False
        
        try:
            # Create Enigma update message
            message = {
                "type": "enigma_update",
                "data": {
                    "enigma_data": {
                        "power_score": signal["power_score"],
                        "signal_color": signal["signal_color"],
                        "macvu_state": signal["macvu_state"],
                        "confluence_level": signal["confluence_level"],
                        "symbol": signal["symbol"],
                        "direction": signal["direction"],
                        "timestamp": time.time()
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(message))
            print(f"📡 Sent signal: {signal['symbol']} {signal['direction']} (Power: {signal['power_score']}%)")
            return True
            
        except Exception as e:
            print(f"❌ Error sending signal: {e}")
            return False
    
    async def send_risk_update(self):
        """Send risk management update"""
        if not self.websocket:
            return False
        
        try:
            risk_data = {
                "type": "risk_dashboard_update",
                "data": {
                    "metrics": {
                        "account_balance": 10000 + random.uniform(-500, 1000),
                        "daily_pnl": random.uniform(-200, 300),
                        "weekly_pnl": random.uniform(-800, 1200),
                        "current_drawdown": random.uniform(0, 5),
                        "risk_score": random.randint(20, 80),
                        "kelly_percentage": random.uniform(0.01, 0.05)
                    },
                    "violations": [],
                    "status": "SAFE"
                }
            }
            
            await self.websocket.send(json.dumps(risk_data))
            print(f"🛡️ Sent risk update: Balance ${risk_data['data']['metrics']['account_balance']:.0f}, P&L ${risk_data['data']['metrics']['daily_pnl']:.0f}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending risk update: {e}")
            return False
    
    async def run_continuous_testing(self, interval=30):
        """Run continuous signal testing for NinjaTrader"""
        print("🚀 Starting continuous NinjaTrader testing...")
        print("📊 Sending test signals every 30 seconds")
        print("🛡️ Sending risk updates every 10 seconds")
        print("⚠️ Press Ctrl+C to stop")
        
        signal_counter = 0
        risk_counter = 0
        
        try:
            while True:
                # Send risk update every 10 seconds
                if risk_counter % 3 == 0:  # Every 3 iterations (10 seconds each)
                    await self.send_risk_update()
                
                # Send signal every 30 seconds (9 iterations)
                if signal_counter % 9 == 0:
                    # Choose random signal
                    signal = random.choice(self.test_signals)
                    
                    # Add some randomization
                    signal["power_score"] = random.randint(60, 95)
                    signal["confluence_level"] = random.randint(2, 5)
                    
                    await self.send_test_signal(signal)
                
                signal_counter += 1
                risk_counter += 1
                
                await asyncio.sleep(10)  # Base interval
                
        except KeyboardInterrupt:
            print("\n⏹️ Testing stopped by user")
        except Exception as e:
            print(f"❌ Testing error: {e}")
    
    async def run_manual_testing(self):
        """Interactive manual testing"""
        print("\n🎯 MANUAL NINJATRADER TESTING MODE")
        print("=" * 50)
        print("Commands:")
        print("1 - Send BULLISH signal (EURUSD)")
        print("2 - Send BEARISH signal (GBPUSD)")  
        print("3 - Send HIGH POWER signal (USDJPY)")
        print("4 - Send risk update")
        print("5 - Send random signal")
        print("q - Quit")
        print("=" * 50)
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == 'q':
                    break
                elif command == '1':
                    signal = self.test_signals[0]  # EURUSD Bullish
                    await self.send_test_signal(signal)
                elif command == '2':
                    signal = self.test_signals[2]  # AUDUSD Bearish
                    signal["symbol"] = "GBPUSD"
                    await self.send_test_signal(signal)
                elif command == '3':
                    signal = self.test_signals[3]  # USDJPY High Power
                    await self.send_test_signal(signal)
                elif command == '4':
                    await self.send_risk_update()
                elif command == '5':
                    signal = random.choice(self.test_signals)
                    signal["power_score"] = random.randint(60, 95)
                    await self.send_test_signal(signal)
                else:
                    print("❌ Invalid command")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 Manual testing ended")
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from server")

async def main():
    """Main testing function"""
    print("🥷 NINJATRADER TESTING CLIENT")
    print("=" * 40)
    print("This client sends test signals to NinjaTrader indicators")
    print("Make sure the WebSocket server is running on localhost:8765")
    print()
    
    client = NinjaTesterClient()
    
    # Connect to server
    if not await client.connect():
        print("❌ Failed to connect to server. Make sure it's running!")
        return
    
    try:
        # Choose testing mode
        print("Choose testing mode:")
        print("1 - Continuous automated testing (recommended)")
        print("2 - Manual testing (interactive)")
        
        mode = input("Enter mode (1 or 2): ").strip()
        
        if mode == "1":
            await client.run_continuous_testing()
        elif mode == "2":
            await client.run_manual_testing()
        else:
            print("❌ Invalid mode selected")
            
    except Exception as e:
        print(f"❌ Testing error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
