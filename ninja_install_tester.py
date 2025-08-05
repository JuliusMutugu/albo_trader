"""
🚀 NinjaTrader Live Installation Tester
Test your indicators immediately after compilation!
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime

class NinjaTraderInstallTester:
    def __init__(self):
        self.websocket = None
        self.running = False
        
    async def connect_and_test(self):
        """Connect to WebSocket server and send test signals"""
        try:
            print("🔌 Connecting to WebSocket server...")
            self.websocket = await websockets.connect("ws://localhost:8765")
            print("✅ Connected successfully!")
            
            # Send initial connection message
            await self.send_message({
                'type': 'connection',
                'source': 'NinjaTrader_Test',
                'status': 'connected',
                'timestamp': datetime.now().isoformat()
            })
            
            print("\n🎯 Starting signal test sequence...")
            await self.run_test_sequence()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\n💡 Make sure:")
            print("   1. WebSocket server is running: python enhanced_websocket_server.py")
            print("   2. Port 8765 is not blocked by firewall")
            
    async def send_message(self, message):
        """Send message to WebSocket server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Sent: {message.get('type', 'unknown')}")
            
    async def run_test_sequence(self):
        """Run comprehensive test sequence for NinjaTrader"""
        
        print("\n🧪 TEST 1: Signal Generation")
        # Test different signal types
        signals = [
            {'type': 'bullish', 'power': 85, 'timeframe': 'M5'},
            {'type': 'bearish', 'power': 78, 'timeframe': 'M15'},
            {'type': 'bullish', 'power': 92, 'timeframe': 'H1'},
        ]
        
        for i, signal in enumerate(signals, 1):
            print(f"   📊 Test Signal {i}: {signal['type'].upper()} (Power: {signal['power']})")
            
            await self.send_message({
                'type': 'signal',
                'data': {
                    'power_score': signal['power'],
                    'signal_type': signal['type'],
                    'timeframe': signal['timeframe'],
                    'symbol': 'ES',
                    'confidence': 'C3',
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            await asyncio.sleep(3)  # Wait for NinjaTrader to process
            
        print("\n🧪 TEST 2: Risk Updates")
        # Test risk management updates
        risk_updates = [
            {'balance': 10000, 'pnl': 150, 'drawdown': 2.1},
            {'balance': 10150, 'pnl': 300, 'drawdown': 1.8},
            {'balance': 10300, 'pnl': 450, 'drawdown': 1.5},
        ]
        
        for i, update in enumerate(risk_updates, 1):
            print(f"   🛡️ Risk Update {i}: Balance ${update['balance']}, P&L ${update['pnl']}")
            
            await self.send_message({
                'type': 'risk_update',
                'data': {
                    'account_balance': update['balance'],
                    'daily_pnl': update['pnl'],
                    'current_drawdown': update['drawdown'],
                    'risk_score': random.randint(20, 50),
                    'kelly_percentage': round(random.uniform(1.5, 3.5), 1),
                    'recommended_size': random.randint(500, 1000),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            await asyncio.sleep(2)
            
        print("\n🧪 TEST 3: Market Context")
        # Test market context updates
        await self.send_message({
            'type': 'market_context',
            'data': {
                'vix_level': 18.5,
                'market_sentiment': 'BULLISH',
                'volume_profile': 'HIGH',
                'economic_events': ['FOMC', 'NFP'],
                'timestamp': datetime.now().isoformat()
            }
        })
        
        print("   📈 Market Context Update sent")
        
        print("\n✅ Test sequence completed!")
        print("\n🎯 IN NINJATRADER YOU SHOULD SEE:")
        print("   📊 Signal arrows on your chart")
        print("   🛡️ Risk panel with live data")
        print("   🔊 Audio alerts for signals")
        print("   📈 Power score updates")
        
        # Keep connection alive for manual testing
        print("\n⏰ Keeping connection alive for 2 minutes...")
        print("   🔄 Sending periodic updates...")
        
        for i in range(24):  # 2 minutes of updates every 5 seconds
            await asyncio.sleep(5)
            
            # Send random signal update
            power = random.randint(55, 95)
            signal_type = random.choice(['bullish', 'bearish'])
            
            await self.send_message({
                'type': 'signal',
                'data': {
                    'power_score': power,
                    'signal_type': signal_type,
                    'timeframe': random.choice(['M5', 'M15', 'H1']),
                    'symbol': 'ES',
                    'confidence': random.choice(['C1', 'C2', 'C3']),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            print(f"   📊 Update {i+1}/24: {signal_type.upper()} (Power: {power})")
            
        print("\n🏁 Test completed! Check your NinjaTrader chart for results.")

async def main():
    print("🥷 NINJATRADER INSTALLATION TESTER")
    print("=" * 50)
    print("🎯 This will test your newly installed indicators")
    print("📊 Make sure you have:")
    print("   ✅ Compiled indicators in NinjaTrader (F5)")
    print("   ✅ Added indicators to your chart")
    print("   ✅ WebSocket server running")
    print("\n🚀 Starting test in 3 seconds...")
    
    await asyncio.sleep(3)
    
    tester = NinjaTraderInstallTester()
    await tester.connect_and_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test stopped by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
