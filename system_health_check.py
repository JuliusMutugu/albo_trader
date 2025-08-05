
import requests
import socket
import sqlite3
import os
from datetime import datetime

def check_websocket_server():
    """Check if WebSocket server is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8765))
        sock.close()
        return result == 0
    except:
        return False

def check_web_interfaces():
    """Check if web interfaces are accessible"""
    interfaces = {
        'Signal Interface': 'http://localhost:5000',
        'Risk Dashboard': 'http://localhost:3000'
    }
    
    results = {}
    for name, url in interfaces.items():
        try:
            response = requests.get(url, timeout=5)
            results[name] = response.status_code == 200
        except:
            results[name] = False
    
    return results

def check_database():
    """Check if database is accessible"""
    try:
        conn = sqlite3.connect('trading_signals.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        conn.close()
        return True, count
    except:
        return False, 0

def check_ninjatrader_files():
    """Check if NinjaTrader files exist"""
    nt_path = os.path.expanduser("~/Documents/NinjaTrader 8/bin/Custom/Indicators")
    
    required_files = [
        'EnigmaApexPowerScore.cs',
        'EnigmaApexRiskManager.cs', 
        'EnigmaApexAutoTrader.cs'
    ]
    
    results = {}
    for file in required_files:
        file_path = os.path.join(nt_path, file)
        results[file] = os.path.exists(file_path)
    
    return results

def main():
    print("🔍 ENIGMA-APEX SYSTEM HEALTH CHECK")
    print("=" * 40)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check WebSocket server
    ws_running = check_websocket_server()
    print(f"🔌 WebSocket Server: {'✅ RUNNING' if ws_running else '❌ STOPPED'}")
    
    # Check web interfaces
    web_status = check_web_interfaces()
    for name, status in web_status.items():
        print(f"🌐 {name}: {'✅ ACCESSIBLE' if status else '❌ DOWN'}")
    
    # Check database
    db_status, signal_count = check_database()
    print(f"💾 Database: {'✅ ACCESSIBLE' if db_status else '❌ ERROR'}")
    if db_status:
        print(f"   📊 Total signals: {signal_count}")
    
    # Check NinjaTrader files
    nt_files = check_ninjatrader_files()
    print("🥷 NinjaTrader Files:")
    for file, exists in nt_files.items():
        print(f"   {'✅' if exists else '❌'} {file}")
    
    # Overall health score
    total_checks = 1 + len(web_status) + 1 + len(nt_files)
    passed_checks = (int(ws_running) + sum(web_status.values()) + 
                    int(db_status) + sum(nt_files.values()))
    
    health_score = (passed_checks / total_checks) * 100
    
    print()
    print(f"🏥 OVERALL HEALTH: {health_score:.0f}%")
    print(f"📊 Checks Passed: {passed_checks}/{total_checks}")
    
    if health_score >= 90:
        print("🎉 System is healthy and ready for trading!")
    elif health_score >= 70:
        print("⚠️ System has minor issues - check failed components")
    else:
        print("🚨 System has major issues - restart recommended")
    
    print()
    print("💡 TIP: Run 'python complete_system_launcher.py' to restart all components")

if __name__ == "__main__":
    main()
