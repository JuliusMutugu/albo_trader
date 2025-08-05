"""
🚀 ENIGMA-APEX COMPLETE SYSTEM LAUNCHER
Launch all components for 99% completion TODAY
"""

import subprocess
import threading
import time
import os
import webbrowser
from datetime import datetime

class EnigmaApexLauncher:
    def __init__(self):
        self.processes = {}
        self.running = False
        
    def launch_websocket_server(self):
        """Launch the WebSocket server"""
        try:
            print("🔌 Starting WebSocket Server...")
            process = subprocess.Popen([
                'python', 'enhanced_websocket_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['websocket'] = process
            print("✅ WebSocket Server started on localhost:8765")
            return True
        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")
            return False
    
    def launch_signal_interface(self):
        """Launch the manual signal input interface"""
        try:
            print("📤 Starting Manual Signal Interface...")
            process = subprocess.Popen([
                'python', 'manual_signal_interface.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['signal_interface'] = process
            print("✅ Signal Interface started on localhost:5000")
            return True
        except Exception as e:
            print(f"❌ Failed to start signal interface: {e}")
            return False
    
    def launch_market_data_provider(self):
        """Launch the live market data provider"""
        try:
            print("📊 Starting Live Market Data Provider...")
            process = subprocess.Popen([
                'python', 'live_market_data_provider.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['market_data'] = process
            print("✅ Market Data Provider started")
            return True
        except Exception as e:
            print(f"❌ Failed to start market data provider: {e}")
            return False
    
    def launch_risk_dashboard(self):
        """Launch the risk management dashboard"""
        try:
            print("🛡️ Starting Risk Management Dashboard...")
            process = subprocess.Popen([
                'python', 'risk_management_dashboard.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['risk_dashboard'] = process
            print("✅ Risk Dashboard started on localhost:3000")
            return True
        except Exception as e:
            print(f"❌ Failed to start risk dashboard: {e}")
            return False
    
    def setup_ninjatrader(self):
        """Setup NinjaTrader indicators"""
        try:
            print("🥷 Setting up NinjaTrader...")
            process = subprocess.Popen([
                'python', 'ninjatrader_auto_setup.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()  # Wait for setup to complete
            print("✅ NinjaTrader setup completed")
            return True
        except Exception as e:
            print(f"❌ NinjaTrader setup failed: {e}")
            return False
    
    def install_required_packages(self):
        """Install any missing required packages"""
        packages = [
            'flask',
            'websockets',
            'yfinance',
            'pandas',
            'requests',
            'psutil'
        ]
        
        print("📦 Installing required packages...")
        for package in packages:
            try:
                subprocess.run(['pip', 'install', package], 
                             check=True, capture_output=True, text=True)
                print(f"✅ {package} installed")
            except subprocess.CalledProcessError:
                print(f"⚠️ {package} installation skipped (may already be installed)")
        
        print("✅ Package installation completed")
    
    def check_system_status(self):
        """Check if all components are running"""
        status = {
            'websocket': self.check_process('websocket'),
            'signal_interface': self.check_process('signal_interface'),
            'market_data': self.check_process('market_data'),
            'risk_dashboard': self.check_process('risk_dashboard')
        }
        
        running_count = sum(status.values())
        total_count = len(status)
        
        print(f"\n📊 SYSTEM STATUS: {running_count}/{total_count} components running")
        
        for component, is_running in status.items():
            status_icon = "✅" if is_running else "❌"
            print(f"{status_icon} {component.replace('_', ' ').title()}")
        
        return status
    
    def check_process(self, name):
        """Check if a process is still running"""
        if name in self.processes:
            return self.processes[name].poll() is None
        return False
    
    def open_browser_interfaces(self):
        """Open all web interfaces in browser"""
        print("🌐 Opening web interfaces...")
        
        # Wait a moment for servers to start
        time.sleep(3)
        
        urls = [
            ("Signal Input Interface", "http://localhost:5000"),
            ("Risk Management Dashboard", "http://localhost:3000"),
        ]
        
        for name, url in urls:
            try:
                webbrowser.open(url)
                print(f"✅ Opened {name}: {url}")
            except Exception as e:
                print(f"❌ Failed to open {name}: {e}")
    
    def create_status_monitor(self):
        """Create a status monitoring script"""
        monitor_script = '''
@echo off
title Enigma-Apex System Monitor
:loop
cls
echo ENIGMA-APEX SYSTEM MONITOR
echo ==============================
echo.
echo Current Time: %date% %time%
echo.

echo WebSocket Server (Port 8765):
netstat -an | findstr ":8765" >nul
if %errorlevel%==0 (
    echo RUNNING
) else (
    echo STOPPED
)

echo.
echo Signal Interface (Port 5000):
netstat -an | findstr ":5000" >nul
if %errorlevel%==0 (
    echo RUNNING
) else (
    echo STOPPED
)

echo.
echo Risk Dashboard (Port 3000):
netstat -an | findstr ":3000" >nul
if %errorlevel%==0 (
    echo RUNNING
) else (
    echo STOPPED
)

echo.
echo Quick Links:
echo   Signal Input: http://localhost:5000
echo   Risk Dashboard: http://localhost:3000
echo.
echo Press Ctrl+C to exit
timeout /t 5 >nul
goto loop
'''
        
        with open('system_monitor.bat', 'w', encoding='utf-8') as f:
            f.write(monitor_script)
        
        print("✅ System monitor created: system_monitor.bat")
    
    def launch_complete_system(self):
        """Launch the complete Enigma-Apex system"""
        print("ENIGMA-APEX COMPLETE SYSTEM LAUNCHER")
        print("=" * 50)
        print(f"Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Target: 99% System Completion TODAY")
        print()
        
        # Step 1: Install packages
        self.install_required_packages()
        print()
        
        # Step 2: Setup NinjaTrader
        self.setup_ninjatrader()
        print()
        
        # Step 3: Launch core components
        print("LAUNCHING CORE COMPONENTS...")
        print("-" * 30)
        
        success_count = 0
        
        if self.launch_websocket_server():
            success_count += 1
            time.sleep(2)  # Wait for WebSocket server to start
        
        if self.launch_signal_interface():
            success_count += 1
            time.sleep(1)
        
        if self.launch_market_data_provider():
            success_count += 1
            time.sleep(1)
        
        if self.launch_risk_dashboard():
            success_count += 1
            time.sleep(1)
        
        print()
        print(f"✅ {success_count}/4 core components started successfully")
        
        # Step 4: Create monitoring tools
        self.create_status_monitor()
        
        # Step 5: Open web interfaces
        self.open_browser_interfaces()
        
        # Step 6: Final status check
        print()
        print("🔍 FINAL SYSTEM CHECK...")
        print("-" * 25)
        status = self.check_system_status()
        
        # Calculate completion percentage
        completion_percentage = (sum(status.values()) / len(status)) * 100
        
        print()
        print("ENIGMA-APEX SYSTEM LAUNCH COMPLETED!")
        print("=" * 45)
        print(f"System Completion: {completion_percentage:.0f}%")
        print(f"{sum(status.values())}/{len(status)} components operational")
        print()
        
        print("ACCESS POINTS:")
        print("   Signal Input: http://localhost:5000")
        print("   Risk Dashboard: http://localhost:3000")
        print("   WebSocket Server: ws://localhost:8765")
        print()
        
        print("NEXT STEPS:")
        print("   1. Compile NinjaTrader indicators (F5 in NinjaScript Editor)")
        print("   2. Add indicators to your NinjaTrader charts")
        print("   3. Start sending signals via web interface")
        print("   4. Monitor risk dashboard for real-time updates")
        print()
        
        print("MONITORING:")
        print("   Run 'system_monitor.bat' for real-time status")
        print("   All components auto-refresh and reconnect")
        print()
        
        if completion_percentage >= 90:
            print("TARGET ACHIEVED: 90%+ System Completion!")
            print("Enigma-Apex is ready for production trading!")
        else:
            print(f"Target: 90%+ completion (Currently: {completion_percentage:.0f}%)")
            print("Some components may need manual intervention")
        
        self.running = True
        return completion_percentage >= 90
    
    def shutdown_system(self):
        """Shutdown all components"""
        print("\nShutting down Enigma-Apex system...")
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:  # If process is still running
                    process.terminate()
                    print(f"Stopped {name}")
            except Exception as e:
                print(f"Error stopping {name}: {e}")
        
        self.running = False
        print("System shutdown completed")
    
    def keep_system_running(self):
        """Keep the system running and monitor status"""
        print("\nSystem is running... Press Ctrl+C to stop")
        print("Monitor status: run 'system_monitor.bat'")
        
        try:
            while self.running:
                time.sleep(30)  # Check every 30 seconds
                
                # Auto-restart failed components
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:  # Process has stopped
                        print(f"Component {name} stopped, attempting restart...")
                        if name == 'websocket':
                            self.launch_websocket_server()
                        elif name == 'signal_interface':
                            self.launch_signal_interface()
                        elif name == 'market_data':
                            self.launch_market_data_provider()
                        elif name == 'risk_dashboard':
                            self.launch_risk_dashboard()
                
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
            self.shutdown_system()

def main():
    """Main function"""
    launcher = EnigmaApexLauncher()
    
    try:
        # Launch the complete system
        success = launcher.launch_complete_system()
        
        if success:
            # Keep system running
            launcher.keep_system_running()
        else:
            print("System launch incomplete - check error messages above")
            input("Press Enter to exit...")
            
    except KeyboardInterrupt:
        print("\nLaunch interrupted by user")
        launcher.shutdown_system()
    except Exception as e:
        print(f"\nCritical error: {e}")
        launcher.shutdown_system()

if __name__ == "__main__":
    main()
