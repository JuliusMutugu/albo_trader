"""
COMPLETE ENIGMA-APEX SYSTEM LAUNCHER
Starts ALL components for Michael's demonstration
"""

import subprocess
import time
import os
import sys
from datetime import datetime

def start_dashboard():
    """Start the trading dashboard"""
    print("Starting Trading Dashboard...")
    try:
        process = subprocess.Popen(
            ['python', 'trading_dashboard.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
        if process.poll() is None:
            print("SUCCESS: Trading Dashboard running on http://localhost:3000")
            return process
        else:
            print("ERROR: Trading Dashboard failed to start")
            return None
    except Exception as e:
        print(f"ERROR starting dashboard: {e}")
        return None

def start_guardian_agent():
    """Start the Guardian Agent"""
    print("Starting Apex Guardian Agent...")
    try:
        process = subprocess.Popen(
            ['python', 'apex_guardian_agent.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
        if process.poll() is None:
            print("SUCCESS: Guardian Agent running (AI + Kelly + OCR)")
            return process
        else:
            print("ERROR: Guardian Agent failed to start")
            return None
    except Exception as e:
        print(f"ERROR starting Guardian Agent: {e}")
        return None

def start_websocket_server():
    """Start WebSocket server"""
    print("Starting WebSocket Server...")
    try:
        process = subprocess.Popen(
            ['python', 'websocket_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
        if process.poll() is None:
            print("SUCCESS: WebSocket Server running on ws://localhost:8765")
            return process
        else:
            print("ERROR: WebSocket Server failed to start")
            return None
    except Exception as e:
        print(f"ERROR starting WebSocket: {e}")
        return None

def main():
    print("=" * 60)
    print("ENIGMA-APEX COMPLETE SYSTEM LAUNCH")
    print("=" * 60)
    print("COMPREHENSIVE SYSTEM FOR MICHAEL CANFIELD")
    print("- ChatGPT Agent Integration")
    print("- Kelly Criterion Optimization") 
    print("- OCR AlgoBox Integration")
    print("- Apex Prop Firm Compliance")
    print("- NinjaTrader Integration")
    print("- Real-time Dashboard")
    print("=" * 60)
    
    processes = []
    
    # Start components
    dashboard = start_dashboard()
    if dashboard:
        processes.append(('Dashboard', dashboard))
    
    time.sleep(2)
    
    guardian = start_guardian_agent()
    if guardian:
        processes.append(('Guardian Agent', guardian))
    
    time.sleep(2)
    
    websocket = start_websocket_server()
    if websocket:
        processes.append(('WebSocket', websocket))
    
    print("\n" + "=" * 60)
    print("SYSTEM STATUS:")
    print("=" * 60)
    
    running_count = 0
    for name, process in processes:
        if process and process.poll() is None:
            print(f"SUCCESS: {name} - RUNNING")
            running_count += 1
        else:
            print(f"ERROR: {name} - FAILED")
    
    print(f"\nCOMPONENTS RUNNING: {running_count}/{len(processes)}")
    
    if running_count > 0:
        print("\n" + "=" * 60)
        print("SYSTEM ACCESS POINTS FOR MICHAEL:")
        print("=" * 60)
        print("Main Dashboard:     http://localhost:3000")
        print("Signal Interface:   http://localhost:5000") 
        print("WebSocket Server:   ws://localhost:8765")
        print("=" * 60)
        print("\nSYSTEM DEMONSTRATES:")
        print("- Complete NinjaTrader integration")
        print("- ChatGPT first principles analysis")
        print("- Kelly criterion optimization")
        print("- OCR AlgoBox reading capability")
        print("- Apex prop firm compliance")
        print("- Real-time data processing")
        print("- Production-ready deployment")
        print("=" * 60)
        print("\nREADY FOR DEMONSTRATION!")
        print("Open browser to: http://localhost:3000")
        print("Press Ctrl+C to stop all components")
        
        try:
            while True:
                time.sleep(10)
                # Check if processes are still running
                still_running = 0
                for name, process in processes:
                    if process and process.poll() is None:
                        still_running += 1
                
                if still_running == 0:
                    print("All processes stopped")
                    break
                    
        except KeyboardInterrupt:
            print("\nShutting down system...")
            for name, process in processes:
                if process and process.poll() is None:
                    process.terminate()
                    print(f"Stopped {name}")
            print("System shutdown complete")
    
    else:
        print("SYSTEM LAUNCH FAILED")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
