"""
Enhanced Comprehensive System Testing Suite
Advanced testing with improved WebSocket compatibility and stress testing
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
import statistics
import gc
import tracemalloc

class AdvancedSystemTester:
    """Advanced testing of the entire Enigma-Apex system with enhanced scenarios"""
    
    def __init__(self):
        self.test_results = {}
        self.issues_found = []
        self.improvements_suggested = []
        self.performance_metrics = {}
        self.stress_test_results = {}
        
    def test_database_integrity(self):
        """Enhanced database testing with performance analysis"""
        print("🗄️  TESTING DATABASE INTEGRITY (ENHANCED)")
        print("=" * 50)
        
        try:
            # Test database connection
            conn = sqlite3.connect('enigma_apex_pro.db')
            cursor = conn.cursor()
            
            # Check all tables exist
            tables = ['trading_signals', 'market_data', 'trade_performance', 
                     'system_metrics', 'websocket_connections']
            
            existing_tables = []
            table_stats = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    existing_tables.append(table)
                    
                    # Get table size and performance metrics
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = len(cursor.fetchall())
                    
                    table_stats[table] = {
                        'record_count': count,
                        'column_count': columns
                    }
                    
                    print(f"  ✅ {table}: {count} records, {columns} columns")
                    
                except Exception as e:
                    print(f"  ❌ {table}: Missing or corrupted ({e})")
                    self.issues_found.append(f"Database table {table} issue: {e}")
            
            # Enhanced performance testing
            performance_tests = [
                ("Simple SELECT", "SELECT COUNT(*) FROM trading_signals"),
                ("Complex JOIN", """
                    SELECT ts.symbol, COUNT(*) as signal_count 
                    FROM trading_signals ts 
                    GROUP BY ts.symbol 
                    ORDER BY signal_count DESC
                """),
                ("Recent signals", """
                    SELECT * FROM trading_signals 
                    WHERE timestamp > datetime('now', '-1 day')
                    ORDER BY timestamp DESC LIMIT 10
                """)
            ]
            
            query_performance = {}
            for test_name, query in performance_tests:
                start_time = time.time()
                cursor.execute(query)
                results = cursor.fetchall()
                query_time = time.time() - start_time
                
                query_performance[test_name] = {
                    'time': query_time,
                    'result_count': len(results)
                }
                
                print(f"  ⚡ {test_name}: {query_time:.3f}s ({len(results)} results)")
                
                if query_time > 0.1:
                    self.improvements_suggested.append(f"{test_name} query is slow - consider indexing")
            
            # Data integrity checks
            integrity_checks = [
                ("NULL signal_id", "SELECT COUNT(*) FROM trading_signals WHERE signal_id IS NULL"),
                ("NULL symbol", "SELECT COUNT(*) FROM trading_signals WHERE symbol IS NULL"),
                ("Invalid timestamps", "SELECT COUNT(*) FROM trading_signals WHERE timestamp = ''"),
                ("Duplicate signals", """
                    SELECT signal_id, COUNT(*) as count 
                    FROM trading_signals 
                    GROUP BY signal_id 
                    HAVING count > 1
                """)
            ]
            
            integrity_issues = 0
            for check_name, query in integrity_checks:
                cursor.execute(query)
                result = cursor.fetchall()
                
                if check_name == "Duplicate signals":
                    duplicates = len(result)
                    if duplicates > 0:
                        print(f"  ⚠️  {check_name}: {duplicates} duplicates found")
                        integrity_issues += duplicates
                    else:
                        print(f"  ✅ {check_name}: None found")
                else:
                    invalid_count = result[0][0]
                    if invalid_count > 0:
                        print(f"  ⚠️  {check_name}: {invalid_count} issues")
                        integrity_issues += invalid_count
                    else:
                        print(f"  ✅ {check_name}: None found")
            
            if integrity_issues > 0:
                self.issues_found.append(f"Found {integrity_issues} data integrity issues")
            
            conn.close()
            
            self.test_results['database'] = {
                'status': 'pass' if len([t for t in tables if t in existing_tables]) == len(tables) and integrity_issues == 0 else 'fail',
                'tables_found': len(existing_tables),
                'tables_expected': len(tables),
                'query_performance': query_performance,
                'table_stats': table_stats,
                'integrity_issues': integrity_issues
            }
            
        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
            self.issues_found.append(f"Database connection failed: {e}")
            self.test_results['database'] = {'status': 'fail', 'error': str(e)}
    
    async def test_websocket_server_enhanced(self):
        """Enhanced WebSocket server testing with better compatibility"""
        print("\n🔌 TESTING WEBSOCKET SERVER (ENHANCED)")
        print("=" * 50)
        
        connection_times = []
        response_times = []
        
        try:
            # Test multiple connection attempts to measure consistency
            for attempt in range(3):
                start_time = time.time()
                
                try:
                    # Use asyncio.wait_for for better compatibility
                    websocket = await asyncio.wait_for(
                        websockets.connect('ws://localhost:8765'),
                        timeout=10
                    )
                    
                    connection_time = time.time() - start_time
                    connection_times.append(connection_time)
                    
                    print(f"  ✅ Connection {attempt + 1}: {connection_time:.3f}s")
                    
                    # Test message exchange
                    test_message = {
                        "type": "heartbeat",
                        "data": {"test": f"connection_test_{attempt}"},
                        "timestamp": time.time()
                    }
                    
                    msg_start = time.time()
                    await websocket.send(json.dumps(test_message))
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        response_time = time.time() - msg_start
                        response_times.append(response_time)
                        
                        # Parse response
                        response_data = json.loads(response)
                        print(f"  ✅ Response {attempt + 1}: {response_time:.3f}s - {response_data.get('type', 'unknown')}")
                        
                    except asyncio.TimeoutError:
                        print(f"  ⚠️  No response for attempt {attempt + 1}")
                        self.issues_found.append(f"WebSocket server timeout on attempt {attempt + 1}")
                    
                    await websocket.close()
                    
                except asyncio.TimeoutError:
                    print(f"  ❌ Connection timeout on attempt {attempt + 1}")
                    self.issues_found.append(f"WebSocket connection timeout on attempt {attempt + 1}")
                    
                # Small delay between attempts
                await asyncio.sleep(1)
            
            # Calculate performance statistics
            if connection_times:
                avg_connection_time = statistics.mean(connection_times)
                max_connection_time = max(connection_times)
                print(f"  📊 Connection times - Avg: {avg_connection_time:.3f}s, Max: {max_connection_time:.3f}s")
                
                if avg_connection_time > 1.0:
                    self.improvements_suggested.append("WebSocket connection time is slow")
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                print(f"  📊 Response times - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
                
                if avg_response_time > 0.1:
                    self.improvements_suggested.append("WebSocket response time is slow")
            
            # Test status
            test_status = 'pass' if len(connection_times) == 3 and len(response_times) >= 2 else 'partial' if len(connection_times) > 0 else 'fail'
            
            self.test_results['websocket'] = {
                'status': test_status,
                'successful_connections': len(connection_times),
                'total_attempts': 3,
                'avg_connection_time': statistics.mean(connection_times) if connection_times else 0,
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'connection_times': connection_times,
                'response_times': response_times
            }
                
        except Exception as e:
            print(f"  ❌ WebSocket server test failed: {e}")
            self.issues_found.append(f"WebSocket server issue: {e}")
            self.test_results['websocket'] = {
                'status': 'fail',
                'error': str(e)
            }
    
    async def test_stress_load_performance(self):
        """Advanced stress testing with detailed metrics"""
        print("\n⚡ TESTING STRESS LOAD PERFORMANCE")
        print("=" * 50)
        
        # Progressive load testing
        test_scenarios = [
            {'connections': 5, 'messages_per_conn': 3, 'name': 'Light Load'},
            {'connections': 25, 'messages_per_conn': 5, 'name': 'Medium Load'},
            {'connections': 50, 'messages_per_conn': 10, 'name': 'Heavy Load'}
        ]
        
        stress_results = {}
        
        for scenario in test_scenarios:
            print(f"\n  🔄 Testing {scenario['name']}: {scenario['connections']} connections, {scenario['messages_per_conn']} messages each")
            
            connection_count = scenario['connections']
            message_count = scenario['messages_per_conn']
            
            async def create_stress_connection(conn_id):
                try:
                    websocket = await asyncio.wait_for(
                        websockets.connect('ws://localhost:8765'),
                        timeout=15
                    )
                    
                    messages_sent = 0
                    for i in range(message_count):
                        message = {
                            "type": "heartbeat",
                            "data": {
                                "stress_test": True, 
                                "connection_id": conn_id,
                                "message_id": i,
                                "scenario": scenario['name']
                            },
                            "timestamp": time.time()
                        }
                        await websocket.send(json.dumps(message))
                        messages_sent += 1
                        
                        # Small delay to simulate realistic usage
                        await asyncio.sleep(0.05)
                    
                    await websocket.close()
                    return {'success': True, 'messages_sent': messages_sent}
                    
                except Exception as e:
                    return {'success': False, 'error': str(e), 'messages_sent': 0}
            
            # Run stress test
            start_time = time.time()
            
            tasks = [create_stress_connection(i) for i in range(connection_count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze results
            successful_connections = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
            total_messages = sum(r.get('messages_sent', 0) for r in results if isinstance(r, dict))
            
            messages_per_second = total_messages / total_time if total_time > 0 else 0
            
            print(f"    ✅ Successful connections: {successful_connections}/{connection_count}")
            print(f"    📤 Total messages sent: {total_messages}")
            print(f"    ⏱️  Total time: {total_time:.2f}s")
            print(f"    ⚡ Messages per second: {messages_per_second:.1f}")
            
            stress_results[scenario['name']] = {
                'successful_connections': successful_connections,
                'total_connections': connection_count,
                'total_messages': total_messages,
                'total_time': total_time,
                'messages_per_second': messages_per_second,
                'success_rate': (successful_connections / connection_count) * 100
            }
            
            # Check for performance issues
            if successful_connections < connection_count:
                self.issues_found.append(f"{scenario['name']}: Failed {connection_count - successful_connections} connections")
            
            if messages_per_second < 50:  # Expect at least 50 messages/second
                self.improvements_suggested.append(f"{scenario['name']}: Low message processing rate")
            
            # Small break between scenarios
            await asyncio.sleep(2)
        
        # Overall assessment
        overall_success_rate = statistics.mean([s['success_rate'] for s in stress_results.values()])
        max_messages_per_second = max([s['messages_per_second'] for s in stress_results.values()])
        
        print(f"\n  📊 Overall Performance Summary:")
        print(f"    🎯 Average success rate: {overall_success_rate:.1f}%")
        print(f"    ⚡ Peak messages/second: {max_messages_per_second:.1f}")
        
        self.test_results['stress_load_performance'] = {
            'status': 'pass' if overall_success_rate >= 90 else 'partial' if overall_success_rate >= 70 else 'fail',
            'scenarios': stress_results,
            'overall_success_rate': overall_success_rate,
            'max_messages_per_second': max_messages_per_second
        }
    
    async def test_memory_performance(self):
        """Test memory usage and detect memory leaks"""
        print("\n🧠 TESTING MEMORY PERFORMANCE")
        print("=" * 50)
        
        try:
            # Start memory tracking
            tracemalloc.start()
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"  📊 Initial memory usage: {initial_memory:.1f} MB")
            
            # Simulate workload to test for memory leaks
            print("  🔄 Running memory stress test...")
            
            for cycle in range(5):
                # Create multiple WebSocket connections
                tasks = []
                for i in range(10):
                    async def memory_test_connection():
                        try:
                            websocket = await asyncio.wait_for(
                                websockets.connect('ws://localhost:8765'),
                                timeout=10
                            )
                            
                            # Send multiple messages
                            for j in range(20):
                                message = {
                                    "type": "heartbeat",
                                    "data": {"memory_test": True, "cycle": cycle, "iteration": j},
                                    "timestamp": time.time()
                                }
                                await websocket.send(json.dumps(message))
                                await asyncio.sleep(0.01)
                            
                            await websocket.close()
                            
                        except Exception:
                            pass  # Ignore individual connection failures for memory testing
                    
                    tasks.append(memory_test_connection())
                
                # Run connections
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Force garbage collection
                gc.collect()
                
                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = current_memory - initial_memory
                
                print(f"  📊 Cycle {cycle + 1}: {current_memory:.1f} MB (+{memory_delta:.1f} MB)")
                
                await asyncio.sleep(1)
            
            # Final memory check
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_memory_increase = final_memory - initial_memory
            
            print(f"  📊 Final memory usage: {final_memory:.1f} MB")
            print(f"  📈 Total memory increase: {total_memory_increase:.1f} MB")
            
            # Memory leak detection
            if total_memory_increase > 20:  # More than 20MB increase is concerning
                self.issues_found.append(f"Potential memory leak detected: {total_memory_increase:.1f} MB increase")
            elif total_memory_increase > 10:
                self.improvements_suggested.append(f"Memory usage increase: {total_memory_increase:.1f} MB - monitor for leaks")
            else:
                print("  ✅ No significant memory leaks detected")
            
            # Get memory allocation details
            current, peak = tracemalloc.get_traced_memory()
            print(f"  📊 Peak memory allocation: {peak / 1024 / 1024:.1f} MB")
            
            tracemalloc.stop()
            
            self.test_results['memory_performance'] = {
                'status': 'pass' if total_memory_increase < 20 else 'warning' if total_memory_increase < 50 else 'fail',
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': total_memory_increase,
                'peak_allocation_mb': peak / 1024 / 1024
            }
            
        except Exception as e:
            print(f"  ❌ Memory performance test failed: {e}")
            self.issues_found.append(f"Memory performance test error: {e}")
            self.test_results['memory_performance'] = {'status': 'fail', 'error': str(e)}
    
    async def test_notification_system(self):
        """Enhanced notification system testing"""
        print("\n🔔 TESTING NOTIFICATION SYSTEM (ENHANCED)")
        print("=" * 50)
        
        try:
            from desktop_notifier import DesktopNotifier
            
            notifier = DesktopNotifier()
            print("  ✅ Desktop notifier initialized")
            
            # Test multiple notification types
            test_scenarios = [
                {
                    'type': 'signal',
                    'data': {'symbol': 'EURUSD', 'type': 'L3', 'power_score': 95, 'direction': 'BUY', 'timestamp': time.time()},
                    'description': 'High-power signal notification'
                },
                {
                    'type': 'signal', 
                    'data': {'symbol': 'GBPUSD', 'type': 'L2', 'power_score': 65, 'direction': 'SELL', 'timestamp': time.time()},
                    'description': 'Medium-power signal notification'
                },
                {
                    'type': 'trade',
                    'data': {'symbol': 'EURUSD', 'action': 'BUY', 'price': 1.0850, 'quantity': 1000},
                    'alert_type': 'entry',
                    'description': 'Trade entry notification'
                },
                {
                    'type': 'risk',
                    'data': {'type': 'Drawdown Warning', 'message': 'Test risk alert', 'account_value': 50000, 'drawdown_percent': 3.5},
                    'severity': 'medium',
                    'description': 'Risk management notification'
                }
            ]
            
            notification_results = []
            
            for i, scenario in enumerate(test_scenarios):
                print(f"  🔔 Testing {scenario['description']}...")
                
                start_time = time.time()
                
                if scenario['type'] == 'signal':
                    success = await notifier.send_signal_notification(scenario['data'])
                elif scenario['type'] == 'trade':
                    success = await notifier.send_trade_notification(scenario['data'], scenario['alert_type'])
                elif scenario['type'] == 'risk':
                    success = await notifier.send_risk_notification(scenario['data'], scenario['severity'])
                else:
                    success = False
                
                delivery_time = time.time() - start_time
                
                result = {
                    'scenario': scenario['description'],
                    'success': success,
                    'delivery_time': delivery_time
                }
                notification_results.append(result)
                
                if success:
                    print(f"    ✅ Success - {delivery_time:.3f}s delivery time")
                else:
                    print(f"    ❌ Failed - {delivery_time:.3f}s")
                    self.issues_found.append(f"Notification failed: {scenario['description']}")
                
                # Small delay between notifications
                await asyncio.sleep(1)
            
            # Get notification statistics
            stats = notifier.get_notification_stats()
            
            success_rate = (sum(1 for r in notification_results if r['success']) / len(notification_results)) * 100
            avg_delivery_time = statistics.mean([r['delivery_time'] for r in notification_results])
            
            print(f"  📊 Notification test summary:")
            print(f"    🎯 Success rate: {success_rate:.1f}%")
            print(f"    ⚡ Average delivery time: {avg_delivery_time:.3f}s")
            print(f"    📈 Total notifications sent: {stats['total_sent']}")
            
            if success_rate < 100:
                self.issues_found.append(f"Notification success rate below 100%: {success_rate:.1f}%")
            
            if avg_delivery_time > 0.5:
                self.improvements_suggested.append(f"Notification delivery time is slow: {avg_delivery_time:.3f}s")
            
            self.test_results['notification_system'] = {
                'status': 'pass' if success_rate == 100 else 'partial' if success_rate >= 75 else 'fail',
                'success_rate': success_rate,
                'avg_delivery_time': avg_delivery_time,
                'test_results': notification_results,
                'stats': stats
            }
            
        except ImportError as e:
            print(f"  ❌ Notification dependencies missing: {e}")
            self.issues_found.append(f"Notification dependencies: {e}")
            self.test_results['notification_system'] = {'status': 'fail', 'error': str(e)}
            
        except Exception as e:
            print(f"  ❌ Notification system test failed: {e}")
            self.issues_found.append(f"Notification system error: {e}")
            self.test_results['notification_system'] = {'status': 'fail', 'error': str(e)}
    
    def test_file_structure_enhanced(self):
        """Enhanced file structure testing"""
        print("\n📁 TESTING FILE STRUCTURE (ENHANCED)")
        print("=" * 50)
        
        required_files = [
            'enhanced_websocket_server.py',
            'desktop_notifier.py',
            'enhanced_database_manager.py',
            'production_websocket_integration.py',
            'comprehensive_system_test.py',
            'main.py',
            'requirements.txt',
            'enigma_apex_pro.db'
        ]
        
        optional_files = [
            'test_desktop_notifications.py',
            'start_server_with_notifications.py',
            'STRATEGIC_PRODUCT_ROADMAP.md',
            'IMMEDIATE_NOTIFICATION_PLAN.md',
            'TESTING_IMPROVEMENT_ROADMAP.md'
        ]
        
        missing_files = []
        existing_files = []
        file_sizes = {}
        
        # Check required files
        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                existing_files.append(file_path)
                file_sizes[file_path] = path.stat().st_size
                print(f"  ✅ {file_path} ({file_sizes[file_path]:,} bytes)")
            else:
                missing_files.append(file_path)
                print(f"  ❌ {file_path} - Missing")
        
        # Check optional files
        print(f"\n  📋 Optional files:")
        optional_found = []
        for file_path in optional_files:
            path = Path(file_path)
            if path.exists():
                optional_found.append(file_path)
                file_sizes[file_path] = path.stat().st_size
                print(f"  ✅ {file_path} ({file_sizes[file_path]:,} bytes)")
            else:
                print(f"  ⚪ {file_path} - Not present")
        
        if missing_files:
            self.issues_found.extend([f"Missing required file: {f}" for f in missing_files])
        
        # Check Python dependencies with versions
        dependencies_info = {}
        dependency_tests = [
            ('websockets', 'WebSocket communication'),
            ('pandas', 'Data processing'),
            ('numpy', 'Numerical operations'),
            ('plyer', 'Cross-platform notifications'),
            ('win10toast', 'Windows notifications'),
            ('psutil', 'System monitoring'),
            ('sqlite3', 'Database operations')
        ]
        
        print(f"\n  📦 Python dependencies:")
        for dep_name, description in dependency_tests:
            try:
                module = __import__(dep_name)
                version = getattr(module, '__version__', 'Unknown')
                dependencies_info[dep_name] = {'available': True, 'version': version}
                print(f"  ✅ {dep_name} v{version} - {description}")
            except ImportError as e:
                dependencies_info[dep_name] = {'available': False, 'error': str(e)}
                print(f"  ❌ {dep_name} - Missing ({description})")
                self.issues_found.append(f"Missing dependency: {dep_name}")
        
        # Calculate project statistics
        total_size = sum(file_sizes.values())
        
        self.test_results['file_structure'] = {
            'status': 'pass' if not missing_files else 'fail',
            'required_files': {
                'found': len(existing_files),
                'expected': len(required_files),
                'missing': missing_files
            },
            'optional_files': {
                'found': len(optional_found),
                'total': len(optional_files)
            },
            'project_size_bytes': total_size,
            'dependencies': dependencies_info,
            'file_sizes': file_sizes
        }
        
        print(f"\n  📊 Project summary:")
        print(f"    📁 Total project size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
        print(f"    ✅ Required files: {len(existing_files)}/{len(required_files)}")
        print(f"    📋 Optional files: {len(optional_found)}/{len(optional_files)}")
    
    def generate_enhanced_test_report(self):
        """Generate comprehensive test report with recommendations"""
        print("\n" + "=" * 80)
        print("📊 ENHANCED COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'pass')
        partial_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'partial')
        
        print(f"\n🎯 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed, {partial_tests} partial")
        
        # Detailed test summaries
        for test_name, result in self.test_results.items():
            status = result.get('status', 'unknown')
            if status == 'pass':
                status_emoji = "✅"
            elif status == 'partial':
                status_emoji = "⚠️"
            else:
                status_emoji = "❌"
            
            test_display_name = test_name.title().replace('_', ' ')
            print(f"  {status_emoji} {test_display_name}: {status}")
            
            # Show key metrics for each test
            if test_name == 'websocket' and 'avg_connection_time' in result:
                print(f"    ⚡ Avg connection time: {result['avg_connection_time']:.3f}s")
            elif test_name == 'stress_load_performance' and 'max_messages_per_second' in result:
                print(f"    ⚡ Peak performance: {result['max_messages_per_second']:.1f} msg/s")
            elif test_name == 'memory_performance' and 'memory_increase_mb' in result:
                print(f"    🧠 Memory increase: {result['memory_increase_mb']:.1f} MB")
            elif test_name == 'notification_system' and 'success_rate' in result:
                print(f"    🔔 Success rate: {result['success_rate']:.1f}%")
        
        # Issues found
        if self.issues_found:
            print(f"\n⚠️  CRITICAL ISSUES FOUND ({len(self.issues_found)}):")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        # Improvement suggestions
        if self.improvements_suggested:
            print(f"\n💡 IMPROVEMENT SUGGESTIONS ({len(self.improvements_suggested)}):")
            for i, suggestion in enumerate(self.improvements_suggested, 1):
                print(f"  {i}. {suggestion}")
        else:
            print("\n🎉 NO IMPROVEMENTS NEEDED")
        
        # Enhanced system health score
        health_score = ((passed_tests + (partial_tests * 0.7)) / total_tests) * 100
        print(f"\n🏥 ENHANCED SYSTEM HEALTH SCORE: {health_score:.1f}%")
        
        # Detailed health assessment
        if health_score >= 95:
            print("🎉 EXCELLENT: Your system is production-ready and optimized!")
            recommendation = "Ready for advanced features and scaling"
        elif health_score >= 85:
            print("👍 VERY GOOD: Minor optimizations recommended")
            recommendation = "Address performance suggestions, then proceed with features"
        elif health_score >= 75:
            print("🔧 GOOD: Some improvements needed")
            recommendation = "Fix identified issues before adding new features"
        elif health_score >= 60:
            print("⚠️  FAIR: Several issues need attention")
            recommendation = "Focus on fixing critical issues first"
        else:
            print("❌ POOR: Major issues require immediate attention")
            recommendation = "Address all critical issues before proceeding"
        
        print(f"\n🎯 RECOMMENDATION: {recommendation}")
        
        # Performance summary
        if 'stress_load_performance' in self.test_results:
            stress_result = self.test_results['stress_load_performance']
            if 'max_messages_per_second' in stress_result:
                print(f"\n⚡ PERFORMANCE SUMMARY:")
                print(f"  📊 Peak message throughput: {stress_result['max_messages_per_second']:.1f} messages/second")
                print(f"  🎯 Overall connection success: {stress_result.get('overall_success_rate', 0):.1f}%")
        
        # Next steps
        print(f"\n📅 IMMEDIATE NEXT STEPS:")
        if health_score >= 90:
            print("1. ✅ System is excellent - ready for mobile app development")
            print("2. 🚀 Consider implementing essential indicators (RSI, MACD)")
            print("3. 📱 Start React Native mobile app")
            print("4. 🔗 Expand to additional trading platforms")
        elif health_score >= 75:
            print("1. 🔧 Address identified performance issues")
            print("2. ⚡ Optimize WebSocket connection handling")
            print("3. 🧪 Run extended stress tests")
            print("4. 📊 Implement system monitoring dashboard")
        else:
            print("1. 🚨 Fix all critical issues immediately")
            print("2. 🔧 Improve system stability and reliability")
            print("3. 🧪 Re-run comprehensive tests")
            print("4. 📋 Focus on core functionality before adding features")
        
        return {
            'health_score': health_score,
            'tests_passed': passed_tests,
            'tests_partial': partial_tests,
            'total_tests': total_tests,
            'issues_count': len(self.issues_found),
            'improvements_count': len(self.improvements_suggested),
            'recommendation': recommendation
        }

async def main():
    """Run enhanced comprehensive system testing"""
    print("🚀 ENIGMA-APEX ENHANCED COMPREHENSIVE SYSTEM TEST")
    print("=" * 80)
    print("Advanced testing with stress scenarios, memory analysis, and performance optimization...")
    print()
    
    tester = AdvancedSystemTester()
    
    # Run all enhanced tests
    tester.test_file_structure_enhanced()
    tester.test_database_integrity()
    await tester.test_websocket_server_enhanced()
    await tester.test_stress_load_performance()
    await tester.test_memory_performance()
    await tester.test_notification_system()
    
    # Generate enhanced report
    report = tester.generate_enhanced_test_report()
    
    print("\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT AND RECOMMENDATIONS")
    print("=" * 80)
    
    if report['health_score'] >= 90:
        print("🏆 CONGRATULATIONS! Your system is production-ready!")
        print("✅ Excellent foundation for advanced features")
        print("🚀 Ready to proceed with mobile app and indicators")
    elif report['health_score'] >= 75:
        print("👍 Your system is in good shape with minor improvements needed")
        print("🔧 Address the identified issues for optimal performance")
        print("📈 Close to production-ready status")
    else:
        print("⚠️  Your system needs attention before adding new features")
        print("🔨 Focus on stability and reliability improvements")
        print("🧪 Re-test after implementing fixes")
    
    print(f"\n📊 FINAL SCORE: {report['health_score']:.1f}%")
    print(f"🎯 Next milestone: {95 - report['health_score']:.1f} points to excellent rating")

if __name__ == "__main__":
    # Setup enhanced logging
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce log noise during testing
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚡ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing error: {e}")
        import traceback
        traceback.print_exc()
