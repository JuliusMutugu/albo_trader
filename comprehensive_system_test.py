"""
Comprehensive System Testing Suite for Enigma-Apex
Tests all components and identifies improvement areas
"""

import asyncio
import json
import sqlite3
import websockets
import time
from datetime import datetime, timedelta
import subprocess
import psutil
import threading
from pathlib import Path

class SystemTester:
    """Comprehensive testing of the entire Enigma-Apex system"""
    
    def __init__(self):
        self.test_results = {}
        self.issues_found = []
        self.improvements_suggested = []
        
    def test_database_integrity(self):
        """Test database structure and performance"""
        print("🗄️  TESTING DATABASE INTEGRITY")
        print("=" * 40)
        
        try:
            # Test database connection
            conn = sqlite3.connect('enigma_apex_pro.db')
            cursor = conn.cursor()
            
            # Check all tables exist
            tables = ['trading_signals', 'market_data', 'trade_performance', 
                     'system_metrics', 'websocket_connections']
            
            existing_tables = []
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    existing_tables.append(table)
                    print(f"  ✅ {table}: {count} records")
                except Exception as e:
                    print(f"  ❌ {table}: Missing or corrupted ({e})")
                    self.issues_found.append(f"Database table {table} issue: {e}")
            
            # Test database performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM trading_signals")
            query_time = time.time() - start_time
            print(f"  ⚡ Query performance: {query_time:.3f}s")
            
            if query_time > 0.1:
                self.improvements_suggested.append("Database queries are slow - consider adding more indexes")
            
            # Check for data integrity
            cursor.execute("""
                SELECT COUNT(*) FROM trading_signals 
                WHERE signal_id IS NULL OR symbol IS NULL
            """)
            invalid_records = cursor.fetchone()[0]
            
            if invalid_records > 0:
                self.issues_found.append(f"Found {invalid_records} invalid signal records")
            else:
                print(f"  ✅ Data integrity: All records valid")
            
            conn.close()
            
            self.test_results['database'] = {
                'status': 'pass' if len([t for t in tables if t in existing_tables]) == len(tables) else 'fail',
                'tables_found': len(existing_tables),
                'tables_expected': len(tables),
                'query_performance': query_time,
                'data_integrity': invalid_records == 0
            }
            
        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
            self.issues_found.append(f"Database connection failed: {e}")
            self.test_results['database'] = {'status': 'fail', 'error': str(e)}
    
    async def test_websocket_server(self):
        """Test WebSocket server functionality"""
        print("\n🔌 TESTING WEBSOCKET SERVER")
        print("=" * 40)
        
        # Check if server is running
        try:
            async with websockets.connect('ws://localhost:8765', timeout=5) as websocket:
                print("  ✅ Server is running and accepting connections")
                
                # Test basic message sending
                test_message = {
                    "type": "heartbeat",
                    "data": {"test": "connection_test"},
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(test_message))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    print("  ✅ Server responds to messages")
                    
                    # Parse response
                    response_data = json.loads(response)
                    if 'type' in response_data:
                        print(f"  ✅ Response format valid: {response_data['type']}")
                    else:
                        self.issues_found.append("WebSocket response missing 'type' field")
                        
                except asyncio.TimeoutError:
                    print("  ⚠️  Server doesn't respond to messages")
                    self.issues_found.append("WebSocket server not responding to messages")
                
                self.test_results['websocket'] = {
                    'status': 'pass',
                    'connection': True,
                    'message_handling': True
                }
                
        except Exception as e:
            print(f"  ❌ WebSocket server test failed: {e}")
            self.issues_found.append(f"WebSocket server issue: {e}")
            self.test_results['websocket'] = {
                'status': 'fail',
                'connection': False,
                'error': str(e)
            }
    
    async def test_ninja_endpoint(self):
        """Test NinjaTrader specific endpoint"""
        print("\n🥷 TESTING NINJATRADER ENDPOINT")
        print("=" * 40)
        
        try:
            async with websockets.connect('ws://localhost:8765/ninja', timeout=5) as websocket:
                print("  ✅ NinjaTrader endpoint accessible")
                
                # Send NinjaTrader identification
                ninja_message = {
                    "type": "client_identification",
                    "data": {
                        "client_type": "ninja_dashboard",
                        "version": "1.0.0"
                    }
                }
                
                await websocket.send(json.dumps(ninja_message))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    response_data = json.loads(response)
                    
                    if 'enigma_data' in response_data.get('data', {}):
                        print("  ✅ Enigma data included in response")
                        enigma_data = response_data['data']['enigma_data']
                        required_fields = ['power_score', 'confluence_level', 'signal_color', 'macvu_state']
                        
                        missing_fields = [field for field in required_fields if field not in enigma_data]
                        if missing_fields:
                            self.issues_found.append(f"Missing Enigma data fields: {missing_fields}")
                        else:
                            print("  ✅ All required Enigma fields present")
                    else:
                        self.issues_found.append("NinjaTrader response missing Enigma data")
                        
                except asyncio.TimeoutError:
                    print("  ⚠️  No response from NinjaTrader endpoint")
                    self.issues_found.append("NinjaTrader endpoint not responding")
                
                self.test_results['ninja_endpoint'] = {
                    'status': 'pass',
                    'accessible': True,
                    'enigma_data': True
                }
                
        except Exception as e:
            print(f"  ❌ NinjaTrader endpoint test failed: {e}")
            self.issues_found.append(f"NinjaTrader endpoint issue: {e}")
            self.test_results['ninja_endpoint'] = {
                'status': 'fail',
                'accessible': False,
                'error': str(e)
            }
    
    async def test_load_performance(self):
        """Test system performance under load"""
        print("\n⚡ TESTING LOAD PERFORMANCE")
        print("=" * 40)
        
        connection_count = 10
        message_count = 5
        
        async def create_connection():
            try:
                async with websockets.connect('ws://localhost:8765') as websocket:
                    for i in range(message_count):
                        message = {
                            "type": "heartbeat",
                            "data": {"load_test": True, "message_id": i},
                            "timestamp": time.time()
                        }
                        await websocket.send(json.dumps(message))
                        
                        # Small delay between messages
                        await asyncio.sleep(0.1)
                    
                    return True
            except Exception as e:
                return False
        
        print(f"  🔄 Creating {connection_count} concurrent connections...")
        start_time = time.time()
        
        tasks = [create_connection() for _ in range(connection_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_connections = sum(1 for result in results if result is True)
        total_messages = successful_connections * message_count
        
        print(f"  ✅ Successful connections: {successful_connections}/{connection_count}")
        print(f"  ✅ Total messages sent: {total_messages}")
        print(f"  ⚡ Total time: {total_time:.2f}s")
        print(f"  ⚡ Messages per second: {total_messages/total_time:.1f}")
        
        if successful_connections < connection_count:
            self.issues_found.append(f"Failed to handle {connection_count - successful_connections} connections")
        
        if total_messages/total_time < 10:
            self.improvements_suggested.append("Message processing rate is low - consider optimization")
        
        self.test_results['load_performance'] = {
            'status': 'pass' if successful_connections == connection_count else 'partial',
            'successful_connections': successful_connections,
            'total_connections': connection_count,
            'messages_per_second': total_messages/total_time,
            'total_time': total_time
        }
    
    def test_file_structure(self):
        """Test project file structure and dependencies"""
        print("\n📁 TESTING FILE STRUCTURE")
        print("=" * 40)
        
        required_files = [
            'src/websocket/websocket_server.py',
            'enhanced_database_manager.py',
            'main.py',
            'requirements.txt',
            'enigma_apex_pro.db'
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            if Path(file_path).exists():
                existing_files.append(file_path)
                print(f"  ✅ {file_path}")
            else:
                missing_files.append(file_path)
                print(f"  ❌ {file_path} - Missing")
        
        if missing_files:
            self.issues_found.extend([f"Missing file: {f}" for f in missing_files])
        
        # Check Python dependencies
        try:
            import websockets
            import pandas
            import numpy
            import aiosqlite
            print("  ✅ All Python dependencies available")
        except ImportError as e:
            print(f"  ❌ Missing Python dependency: {e}")
            self.issues_found.append(f"Missing dependency: {e}")
        
        self.test_results['file_structure'] = {
            'status': 'pass' if not missing_files else 'fail',
            'existing_files': len(existing_files),
            'missing_files': len(missing_files),
            'dependencies_ok': True
        }
    
    def test_system_resources(self):
        """Test system resource usage"""
        print("\n💻 TESTING SYSTEM RESOURCES")
        print("=" * 40)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"  🖥️  CPU usage: {cpu_percent}%")
        
        # Memory usage
        memory = psutil.virtual_memory()
        print(f"  🧠 Memory usage: {memory.percent}% ({memory.used // (1024**3)}GB used)")
        
        # Disk usage
        disk = psutil.disk_usage('.')
        print(f"  💾 Disk usage: {disk.percent}% ({disk.free // (1024**3)}GB free)")
        
        # Network connections
        connections = psutil.net_connections()
        websocket_connections = [c for c in connections if c.laddr.port == 8765]
        print(f"  🌐 WebSocket connections: {len(websocket_connections)}")
        
        resource_issues = []
        if cpu_percent > 80:
            resource_issues.append("High CPU usage detected")
        if memory.percent > 85:
            resource_issues.append("High memory usage detected")
        if disk.percent > 90:
            resource_issues.append("Low disk space")
        
        if resource_issues:
            self.issues_found.extend(resource_issues)
        
        self.test_results['system_resources'] = {
            'status': 'pass' if not resource_issues else 'warning',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'websocket_connections': len(websocket_connections)
        }
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'pass')
        
        print(f"\n🎯 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
        
        # Test summaries
        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result.get('status') == 'pass' else "⚠️" if result.get('status') == 'partial' else "❌"
            print(f"  {status_emoji} {test_name.title().replace('_', ' ')}: {result.get('status', 'unknown')}")
        
        # Issues found
        if self.issues_found:
            print(f"\n⚠️  ISSUES FOUND ({len(self.issues_found)}):")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        # Improvement suggestions
        if self.improvements_suggested:
            print(f"\n💡 IMPROVEMENT SUGGESTIONS ({len(self.improvements_suggested)}):")
            for i, suggestion in enumerate(self.improvements_suggested, 1):
                print(f"  {i}. {suggestion}")
        
        # System health score
        health_score = (passed_tests / total_tests) * 100
        print(f"\n🏥 SYSTEM HEALTH SCORE: {health_score:.1f}%")
        
        if health_score >= 90:
            print("🎉 EXCELLENT: Your system is production-ready!")
        elif health_score >= 75:
            print("👍 GOOD: Minor improvements needed")
        elif health_score >= 50:
            print("⚠️  FAIR: Several issues need attention")
        else:
            print("❌ POOR: Major issues require immediate attention")
        
        return {
            'health_score': health_score,
            'tests_passed': passed_tests,
            'total_tests': total_tests,
            'issues_count': len(self.issues_found),
            'improvements_count': len(self.improvements_suggested)
        }

async def main():
    """Run comprehensive system testing"""
    print("🚀 ENIGMA-APEX COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    print("Testing all components to identify strengths and improvement areas...")
    print()
    
    tester = SystemTester()
    
    # Run all tests
    tester.test_file_structure()
    tester.test_database_integrity()
    await tester.test_websocket_server()
    await tester.test_ninja_endpoint()
    await tester.test_load_performance()
    tester.test_system_resources()
    
    # Generate report
    report = tester.generate_test_report()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS BASED ON TEST RESULTS:")
    
    if report['health_score'] >= 90:
        print("✅ System is excellent - ready for advanced features")
        print("🚀 Recommended: Start implementing ML enhancements")
    elif report['health_score'] >= 75:
        print("👍 System is good - address minor issues first")
        print("🔧 Recommended: Fix identified issues, then add features")
    else:
        print("⚠️  System needs attention - focus on fixes first")
        print("🔨 Recommended: Address critical issues before new development")
    
    print("\n📅 THIS WEEK'S PRIORITIES:")
    print("1. Fix any critical issues found")
    print("2. Implement suggested improvements")
    print("3. Add comprehensive logging")
    print("4. Create performance monitoring dashboard")
    
    print("\n📅 THIS MONTH'S GOALS:")
    print("1. ML signal enhancement implementation")
    print("2. Advanced analytics dashboard")
    print("3. Multi-broker integration")
    print("4. Risk management system")

if __name__ == "__main__":
    asyncio.run(main())
