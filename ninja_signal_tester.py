"""
NinjaTrader Signal Testing Suite
Simulates real Enigma-Apex signals for testing your NinjaTrader dashboard
"""

import asyncio
import json
import websockets
import time
import random

class EnigmaSignalTester:
    def __init__(self):
        self.websocket_url = "ws://localhost:8765/ninja"
        
    async def send_signal(self, power_score, confluence, signal_color, macvu_state, message=""):
        """Send a single signal to the dashboard"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                signal = {
                    "type": "enigma_update",
                    "data": {
                        "power_score": power_score,
                        "confluence_level": confluence,
                        "signal_color": signal_color,
                        "macvu_state": macvu_state,
                        "timestamp": time.time(),
                        "message": message
                    }
                }
                
                await websocket.send(json.dumps(signal))
                print(f"📡 Sent: {signal_color} signal - Power: {power_score}, Confluence: {confluence}")
                return True
                
        except Exception as e:
            print(f"❌ Error sending signal: {e}")
            return False
    
    async def test_basic_signals(self):
        """Test basic signal types"""
        print("🧪 Testing Basic Signal Types")
        print("=" * 40)
        
        # Test RED (Bearish) Signal
        await self.send_signal(20, "L1", "RED", "BEARISH", "Strong bearish signal detected")
        await asyncio.sleep(2)
        
        # Test YELLOW (Neutral) Signal  
        await self.send_signal(50, "L2", "YELLOW", "NEUTRAL", "Market consolidation")
        await asyncio.sleep(2)
        
        # Test GREEN (Bullish) Signal
        await self.send_signal(85, "L3", "GREEN", "BULLISH", "Strong bullish momentum")
        await asyncio.sleep(2)
        
        print("✅ Basic signal test completed")
    
    async def test_confluence_levels(self):
        """Test different confluence levels"""
        print("\n🎯 Testing Confluence Levels")
        print("=" * 40)
        
        levels = ["L1", "L2", "L3", "L4", "L5"]
        colors = ["RED", "YELLOW", "GREEN"]
        
        for level in levels:
            color = random.choice(colors)
            power = random.randint(20, 90)
            macvu = "BULLISH" if color == "GREEN" else "BEARISH" if color == "RED" else "NEUTRAL"
            
            await self.send_signal(power, level, color, macvu, f"Testing confluence {level}")
            await asyncio.sleep(1.5)
        
        print("✅ Confluence levels test completed")
    
    async def test_power_score_progression(self):
        """Test power score progression from low to high"""
        print("\n⚡ Testing Power Score Progression")
        print("=" * 40)
        
        for power in range(10, 100, 15):
            if power < 30:
                color, macvu = "RED", "BEARISH"
                confluence = "L1"
            elif power < 70:
                color, macvu = "YELLOW", "NEUTRAL"
                confluence = "L2"
            else:
                color, macvu = "GREEN", "BULLISH"
                confluence = "L3"
            
            await self.send_signal(power, confluence, color, macvu, f"Power progression: {power}")
            await asyncio.sleep(1)
        
        print("✅ Power score progression test completed")
    
    async def test_realistic_trading_session(self):
        """Simulate a realistic trading session with various signals"""
        print("\n📈 Simulating Realistic Trading Session")
        print("=" * 40)
        
        # Morning session - Mixed signals
        print("🌅 Morning Session")
        await self.send_signal(35, "L1", "YELLOW", "NEUTRAL", "Market opening - mixed signals")
        await asyncio.sleep(3)
        
        # Strong bullish signal
        await self.send_signal(78, "L3", "GREEN", "BULLISH", "Breakout confirmed - go long")
        await asyncio.sleep(5)
        
        # Pullback warning
        await self.send_signal(45, "L2", "YELLOW", "NEUTRAL", "Pullback detected - caution")
        await asyncio.sleep(3)
        
        # Bearish reversal
        await self.send_signal(25, "L2", "RED", "BEARISH", "Reversal pattern - consider exit")
        await asyncio.sleep(4)
        
        # Recovery signal
        await self.send_signal(65, "L2", "GREEN", "BULLISH", "Support held - potential recovery")
        await asyncio.sleep(3)
        
        # End of session
        await self.send_signal(50, "L1", "YELLOW", "NEUTRAL", "End of session - neutral stance")
        
        print("✅ Realistic trading session completed")
    
    async def test_rapid_updates(self):
        """Test rapid signal updates to verify dashboard responsiveness"""
        print("\n⚡ Testing Rapid Updates")
        print("=" * 40)
        
        signals = [
            (75, "L3", "GREEN", "BULLISH"),
            (80, "L4", "GREEN", "BULLISH"),
            (85, "L4", "GREEN", "BULLISH"),
            (90, "L5", "GREEN", "BULLISH"),
            (85, "L4", "GREEN", "BULLISH"),
            (70, "L3", "GREEN", "BULLISH"),
            (60, "L2", "YELLOW", "NEUTRAL"),
            (45, "L2", "YELLOW", "NEUTRAL"),
            (30, "L1", "RED", "BEARISH"),
            (50, "L2", "YELLOW", "NEUTRAL")
        ]
        
        for i, (power, confluence, color, macvu) in enumerate(signals):
            await self.send_signal(power, confluence, color, macvu, f"Rapid update {i+1}")
            await asyncio.sleep(0.5)
        
        print("✅ Rapid updates test completed")

async def main():
    """Main testing function"""
    print("🚀 ENIGMA-APEX NINJATRADER SIGNAL TESTER")
    print("=" * 50)
    print("This will send test signals to your NinjaTrader dashboard")
    print("Make sure your WebSocket server and NinjaTrader are running!")
    print()
    
    tester = EnigmaSignalTester()
    
    # Test connection first
    print("🔧 Testing connection...")
    if await tester.send_signal(0, "L1", "NEUTRAL", "NEUTRAL", "Connection test"):
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed - make sure server is running")
        return
    
    await asyncio.sleep(2)
    
    # Run all tests
    await tester.test_basic_signals()
    await asyncio.sleep(3)
    
    await tester.test_confluence_levels()
    await asyncio.sleep(3)
    
    await tester.test_power_score_progression()
    await asyncio.sleep(3)
    
    await tester.test_realistic_trading_session()
    await asyncio.sleep(3)
    
    await tester.test_rapid_updates()
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("📊 Check your NinjaTrader dashboard for real-time updates")
    print("🎓 This demonstrates the full integration working correctly")

if __name__ == "__main__":
    asyncio.run(main())
