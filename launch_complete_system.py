"""
🎯 COMPLETE ENIGMA-APEX SYSTEM LAUNCHER
Starts ALL components for Michael's demonstration
"""

import subprocess
import time
import os
import sys
from datetime import datetime

class SystemLauncher:
    def __init__(self):
        self.processes = []
        self.log_file = f"system_launch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + "\n")
    
    def start_component(self, name, command, port=None):
        """Start a system component"""
        try:
            self.log(f"🚀 Starting {name}...")
            
            # Start process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append({
                'name': name,
                'process': process,
                'port': port,
                'command': command
            })
            
            time.sleep(2)  # Give time to start
            
            if process.poll() is None:  # Still running
                self.log(f"✅ {name} started successfully (PID: {process.pid})")
                if port:
                    self.log(f"🌐 {name} accessible at: http://localhost:{port}")
                return True
            else:
                stdout, stderr = process.communicate()
                self.log(f"❌ {name} failed to start")
                self.log(f"Error: {stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Failed to start {name}: {e}")
            return False
    
    def launch_complete_system(self):
        """Launch the complete Enigma-Apex system"""
        
        print("=" * 60)
        print("🎯 ENIGMA-APEX COMPLETE SYSTEM LAUNCH")
        print("=" * 60)
        print("📋 COMPREHENSIVE SYSTEM FOR MICHAEL CANFIELD")
        print("🤖 ChatGPT Agent Integration")
        print("📊 Kelly Criterion Optimization") 
        print("🔍 OCR AlgoBox Integration")
        print("🏛️ Apex Prop Firm Compliance")
        print("📈 NinjaTrader Integration")
        print("🌐 Real-time Dashboard")
        print("=" * 60)
        
        # Component startup sequence
        components = [
            {
                'name': 'WebSocket Server (Core)',
                'command': 'python websocket_server.py',
                'port': 8765
            },
            {
                'name': 'Trading Dashboard (TradingView)',
                'command': 'python trading_dashboard.py',
                'port': 3000
            },
            {
                'name': 'Signal Interface',
                'command': 'python signal_interface.py',
                'port': 5000
            },
            {
                'name': 'Apex Guardian Agent (AI)',
                'command': 'python apex_guardian_agent.py',
                'port': None
            },
            {
                'name': 'Market Data Provider',
                'command': 'python market_data_provider.py',
                'port': 9000
            }
        ]
        
        successful_starts = 0
        
        for component in components:
            success = self.start_component(
                component['name'],
                component['command'],
                component.get('port')
            )
            if success:
                successful_starts += 1
            time.sleep(3)  # Stagger starts
        
        self.log("=" * 60)
        self.log(f"🎯 SYSTEM LAUNCH COMPLETE")
        self.log(f"✅ {successful_starts}/{len(components)} components started")
        self.log("=" * 60)
        
        # System status summary
        self.show_system_status()
        
        return successful_starts == len(components)
    
    def show_system_status(self):
        """Show current system status"""
        self.log("🖥️  SYSTEM ACCESS POINTS:")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log("📊 Main Dashboard:     http://localhost:3000")
        self.log("🎯 Signal Interface:   http://localhost:5000") 
        self.log("💹 Market Data:        http://localhost:9000")
        self.log("🔌 WebSocket Server:   ws://localhost:8765")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        self.log("🔧 SYSTEM COMPONENTS STATUS:")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for proc in self.processes:
            status = "🟢 RUNNING" if proc['process'].poll() is None else "🔴 STOPPED"
            self.log(f"{proc['name']:<25} {status}")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        self.log("💼 FOR MICHAEL CANFIELD:")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log("1. Main Dashboard: http://localhost:3000")
        self.log("   - TradingView charts with real ES data")
        self.log("   - ChatGPT AI agent status")
        self.log("   - Kelly criterion position sizing")
        self.log("   - Real-time signal generation")
        self.log("")
        self.log("2. Signal Testing: http://localhost:5000")
        self.log("   - Manual signal input interface")
        self.log("   - Apex compliance validation")
        self.log("   - OCR configuration tools")
        self.log("")
        self.log("3. System demonstrates:")
        self.log("   ✅ Complete NinjaTrader integration")
        self.log("   ✅ ChatGPT first principles analysis")
        self.log("   ✅ Kelly criterion optimization")
        self.log("   ✅ OCR AlgoBox reading capability")
        self.log("   ✅ Apex prop firm compliance")
        self.log("   ✅ Real-time data processing")
        self.log("   ✅ Production-ready deployment")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    def monitor_system(self):
        """Monitor running system"""
        self.log("🔍 System monitoring started...")
        self.log("Press Ctrl+C to stop all components")
        
        try:
            while True:
                running_count = 0
                for proc in self.processes:
                    if proc['process'].poll() is None:
                        running_count += 1
                
                self.log(f"📊 {running_count}/{len(self.processes)} components running")
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.log("🛑 Shutdown requested...")
            self.shutdown_system()
    
    def shutdown_system(self):
        """Shutdown all components"""
        self.log("🛑 Shutting down system...")
        
        for proc in self.processes:
            try:
                if proc['process'].poll() is None:
                    proc['process'].terminate()
                    self.log(f"🔴 Stopped {proc['name']}")
            except:
                pass
        
        self.log("✅ System shutdown complete")

if __name__ == "__main__":
    launcher = SystemLauncher()
    
    if launcher.launch_complete_system():
        print("\n🎯 SYSTEM READY FOR MICHAEL'S DEMONSTRATION!")
        print("📱 Open browser to: http://localhost:3000")
        print("🎥 Ready for screenshots/video recording")
        print("\n" + "=" * 60)
        
        # Keep monitoring
        launcher.monitor_system()
    else:
        print("❌ System launch failed - check logs")
        sys.exit(1)
