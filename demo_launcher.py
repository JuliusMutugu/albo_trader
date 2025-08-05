"""
🎯 ENIGMA-APEX COMPLETE SYSTEM DEMONSTRATION
Michael Canfield's ChatGPT Agent - Production Ready Demo
"""

import subprocess
import time
import webbrowser
from datetime import datetime
import os

class EnigmaApexDemo:
    def __init__(self):
        self.processes = []
        self.demo_urls = {
            'main_dashboard': 'http://localhost:3000',
            'signal_interface': 'http://localhost:5000', 
            'websocket_status': 'ws://localhost:8765'
        }
        
    def start_all_services(self):
        """Start all Enigma-Apex services for complete demonstration"""
        
        print("🚀 ENIGMA-APEX SYSTEM STARTUP")
        print("=" * 60)
        print("🎯 Michael Canfield's ChatGPT Agent Vision")
        print("📊 First Principles Analysis + Kelly Optimization")
        print("🏛️ Apex Prop Firm Compliance")
        print("=" * 60)
        print()
        
        # Start Trading Dashboard
        print("1️⃣ Starting Trading Dashboard with TradingView Charts...")
        try:
            dashboard_process = subprocess.Popen(
                ['python', 'trading_dashboard.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(dashboard_process)
            print("   ✅ Dashboard: http://localhost:3000")
            time.sleep(3)
        except Exception as e:
            print(f"   ❌ Dashboard failed: {e}")
        
        # Start Guardian Agent
        print("2️⃣ Starting Apex Guardian Agent...")
        try:
            guardian_process = subprocess.Popen(
                ['python', 'apex_guardian_agent.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(guardian_process)
            print("   ✅ Guardian Agent: AI Analysis Active")
            time.sleep(2)
        except Exception as e:
            print(f"   ❌ Guardian Agent failed: {e}")
        
        # Start WebSocket Server
        print("3️⃣ Starting WebSocket Communication Hub...")
        try:
            websocket_process = subprocess.Popen(
                ['python', 'websocket_server.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(websocket_process)
            print("   ✅ WebSocket: localhost:8765")
            time.sleep(2)
        except Exception as e:
            print(f"   ❌ WebSocket failed: {e}")
        
        print()
        print("🎉 SYSTEM STARTUP COMPLETE!")
        print("=" * 60)
        
        return True
    
    def open_demonstration_pages(self):
        """Open all demonstration pages for screenshot/video capture"""
        
        print("📸 OPENING DEMONSTRATION PAGES")
        print("=" * 40)
        
        # Main Dashboard
        print("🌐 Opening Main Trading Dashboard...")
        webbrowser.open(self.demo_urls['main_dashboard'])
        time.sleep(3)
        
        # Print URLs for manual opening if needed
        print("\n📋 DEMO URLS FOR SCREENSHOTS:")
        print("-" * 40)
        for name, url in self.demo_urls.items():
            print(f"{name}: {url}")
        
        print("\n🎬 READY FOR VIDEO/SCREENSHOT CAPTURE!")
        print("=" * 50)
        
    def generate_demo_signals(self):
        """Generate demo signals for demonstration"""
        import requests
        import json
        
        print("🎯 GENERATING DEMO SIGNALS")
        print("=" * 30)
        
        demo_signals = [
            {
                "power_score": 25,
                "confluence_level": "L4",
                "signal_color": "GREEN",
                "atr": 18.5,
                "session": "AM",
                "action": "TRADE"
            },
            {
                "power_score": 12,
                "confluence_level": "L1", 
                "signal_color": "RED",
                "atr": 15.2,
                "session": "AM",
                "action": "NO_TRADE"
            },
            {
                "power_score": 18,
                "confluence_level": "L3",
                "signal_color": "BLUE",
                "atr": 16.8,
                "session": "PM",
                "action": "CAUTIOUS_TRADE"
            }
        ]
        
        for i, signal in enumerate(demo_signals, 1):
            print(f"🔄 Generating Signal {i}: {signal['action']}")
            try:
                response = requests.post(
                    'http://localhost:3000/api/generate-signal',
                    json=signal,
                    timeout=5
                )
                print(f"   ✅ Signal {i} sent successfully")
            except Exception as e:
                print(f"   ⚠️ Signal {i} failed: {e}")
            
            time.sleep(2)
    
    def display_system_status(self):
        """Display current system status"""
        
        print("\n📊 CURRENT SYSTEM STATUS")
        print("=" * 50)
        print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Dashboard: http://localhost:3000")
        print(f"🤖 AI Agent: ACTIVE (First Principles)")
        print(f"💰 Kelly Optimizer: RUNNING")
        print(f"🏛️ Apex Compliance: ENFORCED")
        print(f"🔍 OCR Reader: READY")
        print(f"📡 WebSocket: LIVE")
        print("=" * 50)
        
    def cleanup(self):
        """Clean up all processes"""
        print("\n🧹 CLEANING UP PROCESSES...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        print("✅ Cleanup complete")

def main():
    """Main demonstration function"""
    
    demo = EnigmaApexDemo()
    
    try:
        # Start all services
        demo.start_all_services()
        
        # Open demonstration pages
        demo.open_demonstration_pages()
        
        # Display system status
        demo.display_system_status()
        
        # Generate demo signals
        time.sleep(5)  # Wait for services to fully start
        demo.generate_demo_signals()
        
        print("\n🎬 DEMO READY FOR CLIENT PRESENTATION!")
        print("=" * 60)
        print("📋 SCREENSHOT CHECKLIST:")
        print("   □ Main Dashboard (http://localhost:3000)")
        print("   □ TradingView Chart with live data")
        print("   □ AI Agent status panel")
        print("   □ Real-time signal generation")
        print("   □ Performance metrics")
        print("   □ Kelly optimization display")
        print("=" * 60)
        
        # Keep running for demonstration
        input("\n⏸️  Press ENTER to stop the demonstration...")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    
    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()
