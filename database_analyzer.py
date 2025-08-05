"""
Database Checker and Analytics Tool for Enigma-Apex
Real-time monitoring and analysis of your trading system
"""

import asyncio
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from enhanced_database_manager import EnhancedDatabaseManager

class DatabaseAnalyzer:
    """Analyze and monitor your trading database"""
    
    def __init__(self, db_path="enigma_apex_pro.db"):
        self.db_path = db_path
        
    def check_database_status(self):
        """Quick database status check"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print("🔍 ENIGMA-APEX DATABASE STATUS")
            print("=" * 50)
            
            # Check signals
            cursor.execute("SELECT COUNT(*) FROM trading_signals")
            signal_count = cursor.fetchone()[0]
            print(f"📊 Total signals stored: {signal_count}")
            
            if signal_count > 0:
                # Recent signals
                cursor.execute("""
                    SELECT signal_id, symbol, signal_type, power_score, signal_color, timestamp 
                    FROM trading_signals 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                
                print("\n🔥 Recent signals:")
                for row in cursor.fetchall():
                    print(f"  {row[0][:15]} | {row[1]} | {row[2]} | Power: {row[3]} | {row[4]} | {row[5]}")
                
                # Signal distribution
                cursor.execute("""
                    SELECT signal_type, COUNT(*) as count
                    FROM trading_signals 
                    GROUP BY signal_type
                """)
                
                print("\n📈 Signal distribution:")
                for row in cursor.fetchall():
                    print(f"  {row[0]}: {row[1]} signals")
                
                # Power score analysis
                cursor.execute("""
                    SELECT 
                        AVG(power_score) as avg_power,
                        MIN(power_score) as min_power,
                        MAX(power_score) as max_power
                    FROM trading_signals
                """)
                
                power_stats = cursor.fetchone()
                print(f"\n⚡ Power score stats:")
                print(f"  Average: {power_stats[0]:.1f}")
                print(f"  Range: {power_stats[1]} - {power_stats[2]}")
            
            # Check market data
            cursor.execute("SELECT COUNT(*) FROM market_data")
            market_count = cursor.fetchone()[0]
            print(f"\n📊 Market data points: {market_count}")
            
            # Check system metrics
            cursor.execute("SELECT COUNT(*) FROM system_metrics")
            metrics_count = cursor.fetchone()[0]
            print(f"📊 System metrics logged: {metrics_count}")
            
            # Check WebSocket connections
            cursor.execute("SELECT COUNT(*) FROM websocket_connections")
            conn_count = cursor.fetchone()[0]
            print(f"🔌 WebSocket connections logged: {conn_count}")
            
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def generate_performance_report(self):
        """Generate detailed performance report"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            print("\n📊 ENIGMA-APEX PERFORMANCE REPORT")
            print("=" * 50)
            
            # Signal performance by type
            df_signals = pd.read_sql_query("""
                SELECT signal_type, signal_color, power_score, confluence_level, timestamp
                FROM trading_signals
                ORDER BY timestamp DESC
            """, conn)
            
            if len(df_signals) > 0:
                print("\n🎯 Signal Analysis:")
                
                # By signal type
                type_counts = df_signals['signal_type'].value_counts()
                print(f"  Signal types:")
                for signal_type, count in type_counts.items():
                    percentage = (count / len(df_signals)) * 100
                    print(f"    {signal_type}: {count} ({percentage:.1f}%)")
                
                # By signal color
                color_counts = df_signals['signal_color'].value_counts()
                print(f"\n  Signal colors:")
                for color, count in color_counts.items():
                    percentage = (count / len(df_signals)) * 100
                    print(f"    {color}: {count} ({percentage:.1f}%)")
                
                # Power score distribution
                print(f"\n  Power score distribution:")
                print(f"    Average: {df_signals['power_score'].mean():.1f}")
                print(f"    Median: {df_signals['power_score'].median():.1f}")
                print(f"    Standard deviation: {df_signals['power_score'].std():.1f}")
                
                # Recent activity
                last_24h = df_signals[pd.to_datetime(df_signals['timestamp']) > 
                                    datetime.now() - timedelta(hours=24)]
                print(f"\n  Last 24 hours: {len(last_24h)} signals")
                
                if len(last_24h) > 0:
                    avg_power_24h = last_24h['power_score'].mean()
                    print(f"    Average power score: {avg_power_24h:.1f}")
            
            # System health metrics
            df_metrics = pd.read_sql_query("""
                SELECT metric_name, metric_value, timestamp
                FROM system_metrics
                ORDER BY timestamp DESC
                LIMIT 100
            """, conn)
            
            if len(df_metrics) > 0:
                print(f"\n🏥 System Health:")
                
                # Metrics by type
                metric_summary = df_metrics.groupby('metric_name').agg({
                    'metric_value': ['count', 'mean', 'sum']
                }).round(2)
                
                for metric_name in metric_summary.index:
                    count = metric_summary.loc[metric_name, ('metric_value', 'count')]
                    avg = metric_summary.loc[metric_name, ('metric_value', 'mean')]
                    total = metric_summary.loc[metric_name, ('metric_value', 'sum')]
                    print(f"    {metric_name}: {count} events, avg: {avg}, total: {total}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Report generation error: {e}")
    
    def monitor_real_time(self, duration_seconds=60):
        """Monitor database changes in real-time"""
        print(f"\n👁️  REAL-TIME MONITORING ({duration_seconds} seconds)")
        print("=" * 50)
        
        start_time = datetime.now()
        last_signal_count = 0
        last_metric_count = 0
        
        try:
            while (datetime.now() - start_time).seconds < duration_seconds:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check signal count
                cursor.execute("SELECT COUNT(*) FROM trading_signals")
                current_signal_count = cursor.fetchone()[0]
                
                # Check metrics count
                cursor.execute("SELECT COUNT(*) FROM system_metrics")
                current_metric_count = cursor.fetchone()[0]
                
                # Report changes
                new_signals = current_signal_count - last_signal_count
                new_metrics = current_metric_count - last_metric_count
                
                if new_signals > 0 or new_metrics > 0:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] New signals: {new_signals}, New metrics: {new_metrics}")
                    
                    # Show latest signal if any
                    if new_signals > 0:
                        cursor.execute("""
                            SELECT signal_id, symbol, signal_type, power_score, signal_color
                            FROM trading_signals 
                            ORDER BY timestamp DESC 
                            LIMIT 1
                        """)
                        latest = cursor.fetchone()
                        print(f"  Latest: {latest[0][:15]} | {latest[1]} | {latest[2]} | Power: {latest[3]} | {latest[4]}")
                
                last_signal_count = current_signal_count
                last_metric_count = current_metric_count
                
                conn.close()
                import time
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print("\n✋ Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")

def main():
    """Main analyzer function"""
    analyzer = DatabaseAnalyzer()
    
    print("🚀 ENIGMA-APEX DATABASE ANALYZER")
    print("=" * 50)
    
    # Check database status
    if analyzer.check_database_status():
        
        # Generate performance report
        analyzer.generate_performance_report()
        
        print("\n" + "=" * 50)
        print("💡 WHAT THESE METRICS MEAN:")
        print("- Signal count: Total trading signals processed")
        print("- Power score: Signal strength (0-100)")
        print("- Signal colors: GREEN=bullish, RED=bearish, YELLOW=neutral")
        print("- System metrics: Performance and health tracking")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Run your WebSocket server to collect more data")
        print("2. Send test signals using ninja_signal_tester.py")
        print("3. Monitor real-time activity")
        print("4. Analyze patterns in your signals")
        
        # Option for real-time monitoring
        print("\n" + "=" * 50)
        monitor = input("\n🔍 Would you like to monitor real-time activity? (y/n): ").lower()
        if monitor == 'y':
            duration = input("⏱️  How many seconds to monitor? (default 60): ")
            try:
                duration = int(duration) if duration else 60
            except:
                duration = 60
            analyzer.monitor_real_time(duration)
    
    else:
        print("\n❌ Database not accessible. Run enhanced_database_manager.py first.")

if __name__ == "__main__":
    main()
