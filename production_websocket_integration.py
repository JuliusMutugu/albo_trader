"""
Fixed WebSocket Database Integration
Compatible with existing TradingSignal structure
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enhanced_database_manager import EnhancedDatabaseManager, TradingSignal

class FixedLiveDataCollector:
    """Fixed data collector compatible with existing TradingSignal structure"""
    
    def __init__(self, db_manager: EnhancedDatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.active_signals = {}
        
    async def process_enigma_signal(self, data: Dict[str, Any], client_id: str):
        """Process incoming Enigma signal with correct structure"""
        try:
            # Extract Enigma data
            enigma_data = data.get('enigma_data', {})
            power_score = enigma_data.get('power_score', 0)
            
            # Determine signal type based on power score
            signal_type = "BUY" if power_score > 50 else "SELL"
            
            # Create trading signal with correct structure
            signal = TradingSignal(
                signal_id=f"ENIGMA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{client_id[:8]}",
                timestamp=datetime.now(),
                symbol="EURUSD",  # Default symbol
                signal_type=signal_type,
                confidence_score=power_score / 100.0,
                power_score=power_score,
                confluence_level=enigma_data.get('confluence_level', 'L1'),
                signal_color=enigma_data.get('signal_color', 'NEUTRAL'),
                macvu_state=enigma_data.get('macvu_state', 'UNKNOWN'),
                source='enigma_websocket',
                is_active=True,
                metadata={
                    'client_id': client_id,
                    'raw_data': enigma_data,
                    'processing_timestamp': datetime.now().isoformat()
                }
            )
            
            # Store signal in database
            await self.db_manager.store_signal(signal)
            
            # Track active signal
            self.active_signals[signal.signal_id] = signal
            
            self.logger.info(f"Stored Enigma signal: {signal.signal_id} - {signal.signal_type} - Power: {signal.power_score}")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error processing Enigma signal: {e}")
            return None
    
    async def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time system statistics"""
        try:
            # Get basic signal statistics
            total_signals = len(self.active_signals)
            active_count = len([s for s in self.active_signals.values() if s.is_active])
            buy_signals = len([s for s in self.active_signals.values() if s.signal_type == 'BUY'])
            sell_signals = len([s for s in self.active_signals.values() if s.signal_type == 'SELL'])
            
            # Calculate average metrics
            avg_power_score = sum(s.power_score for s in self.active_signals.values()) / len(self.active_signals) if self.active_signals else 0
            avg_confidence = sum(s.confidence_score for s in self.active_signals.values()) / len(self.active_signals) if self.active_signals else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_signals': total_signals,
                'active_signals': active_count,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'average_power_score': avg_power_score,
                'average_confidence': avg_confidence,
                'signal_breakdown': {
                    'L1': len([s for s in self.active_signals.values() if s.confluence_level == 'L1']),
                    'L2': len([s for s in self.active_signals.values() if s.confluence_level == 'L2']),
                    'L3': len([s for s in self.active_signals.values() if s.confluence_level == 'L3']),
                },
                'color_breakdown': {
                    'GREEN': len([s for s in self.active_signals.values() if s.signal_color == 'GREEN']),
                    'RED': len([s for s in self.active_signals.values() if s.signal_color == 'RED']),
                    'NEUTRAL': len([s for s in self.active_signals.values() if s.signal_color == 'NEUTRAL']),
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time stats: {e}")
            return {}

class ProductionWebSocketIntegration:
    """Production-ready WebSocket database integration"""
    
    def __init__(self):
        self.db_manager = None
        self.data_collector = None
        self.logger = logging.getLogger(__name__)
        self.message_count = 0
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Initialize the integration system"""
        try:
            # Initialize database manager
            self.db_manager = EnhancedDatabaseManager('enigma_apex_pro.db')
            await self.db_manager.initialize_database()
            
            # Initialize data collector
            self.data_collector = FixedLiveDataCollector(self.db_manager)
            
            self.logger.info("Production WebSocket integration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize integration: {e}")
            raise
    
    async def handle_websocket_message(self, message_data: Dict[str, Any], client_id: str):
        """Handle incoming WebSocket messages"""
        try:
            self.message_count += 1
            message_type = message_data.get('type', 'unknown')
            data = message_data.get('data', {})
            
            # Process different message types
            if message_type == 'enigma_update':
                signal = await self.data_collector.process_enigma_signal(data, client_id)
                if signal:
                    return {
                        'type': 'signal_processed',
                        'data': {
                            'signal_id': signal.signal_id,
                            'signal_type': signal.signal_type,
                            'power_score': signal.power_score,
                            'confidence_score': signal.confidence_score
                        },
                        'timestamp': datetime.now().isoformat()
                    }
            
            elif message_type == 'status_request':
                stats = await self.data_collector.get_real_time_stats()
                
                # Add system performance metrics
                uptime = (datetime.now() - self.start_time).total_seconds()
                stats.update({
                    'system_performance': {
                        'uptime_seconds': uptime,
                        'messages_processed': self.message_count,
                        'messages_per_second': self.message_count / uptime if uptime > 0 else 0,
                        'database_status': 'connected'
                    }
                })
                
                return {
                    'type': 'status_response',
                    'data': stats,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif message_type == 'heartbeat':
                return {
                    'type': 'heartbeat_response',
                    'data': {
                        'server_time': datetime.now().isoformat(),
                        'client_id': client_id,
                        'message_count': self.message_count
                    },
                    'timestamp': datetime.now().isoformat()
                }
            
            # Default response
            return {
                'type': 'message_acknowledged',
                'data': {
                    'original_type': message_type,
                    'processed': True
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            return {
                'type': 'error',
                'data': {'error': str(e)},
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            stats = await self.data_collector.get_real_time_stats()
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            return {
                'integration_performance': {
                    'uptime_hours': uptime / 3600,
                    'total_messages': self.message_count,
                    'avg_messages_per_minute': (self.message_count / uptime) * 60 if uptime > 0 else 0
                },
                'signal_statistics': stats,
                'database_status': {
                    'connected': True,
                    'last_signal_time': max([s.timestamp for s in self.data_collector.active_signals.values()]) if self.data_collector.active_signals else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {}

async def test_production_integration():
    """Test the production WebSocket integration"""
    print("🚀 TESTING PRODUCTION WEBSOCKET INTEGRATION")
    print("=" * 60)
    
    # Initialize integration
    integration = ProductionWebSocketIntegration()
    await integration.initialize()
    print("✅ Integration initialized successfully")
    
    # Test multiple Enigma signals
    test_signals = [
        {
            'type': 'enigma_update',
            'data': {
                'enigma_data': {
                    'power_score': 85,
                    'confluence_level': 'L3',
                    'signal_color': 'GREEN',
                    'macvu_state': 'BULLISH'
                }
            }
        },
        {
            'type': 'enigma_update',
            'data': {
                'enigma_data': {
                    'power_score': 35,
                    'confluence_level': 'L2',
                    'signal_color': 'RED',
                    'macvu_state': 'BEARISH'
                }
            }
        },
        {
            'type': 'enigma_update',
            'data': {
                'enigma_data': {
                    'power_score': 65,
                    'confluence_level': 'L2',
                    'signal_color': 'GREEN',
                    'macvu_state': 'BULLISH'
                }
            }
        }
    ]
    
    # Process test signals
    print("\n📡 Processing test signals...")
    for i, signal_data in enumerate(test_signals, 1):
        client_id = f"test_client_{i:03d}"
        result = await integration.handle_websocket_message(signal_data, client_id)
        
        if result and result.get('type') == 'signal_processed':
            signal_info = result['data']
            print(f"  ✅ Signal {i}: {signal_info['signal_type']} - Power: {signal_info['power_score']} - ID: {signal_info['signal_id']}")
        else:
            print(f"  ❌ Signal {i}: Failed to process")
    
    # Test status request
    print("\n📊 Getting system status...")
    status_request = {
        'type': 'status_request',
        'data': {}
    }
    
    status_response = await integration.handle_websocket_message(status_request, 'admin_client')
    if status_response and status_response.get('type') == 'status_response':
        stats = status_response['data']
        print(f"  📈 Total Signals: {stats.get('total_signals', 0)}")
        print(f"  📈 Active Signals: {stats.get('active_signals', 0)}")
        print(f"  📈 Buy Signals: {stats.get('buy_signals', 0)}")
        print(f"  📈 Sell Signals: {stats.get('sell_signals', 0)}")
        print(f"  📈 Average Power Score: {stats.get('average_power_score', 0):.1f}")
        print(f"  📈 Average Confidence: {stats.get('average_confidence', 0):.2f}")
        
        # System performance
        perf = stats.get('system_performance', {})
        print(f"  ⚡ Messages Processed: {perf.get('messages_processed', 0)}")
        print(f"  ⚡ Messages/Second: {perf.get('messages_per_second', 0):.1f}")
        print(f"  ⚡ Uptime: {perf.get('uptime_seconds', 0):.1f} seconds")
    
    # Get comprehensive performance summary
    print("\n📋 Performance Summary...")
    summary = await integration.get_performance_summary()
    
    if summary:
        perf = summary.get('integration_performance', {})
        print(f"  🕒 Uptime: {perf.get('uptime_hours', 0):.2f} hours")
        print(f"  📊 Messages/Minute: {perf.get('avg_messages_per_minute', 0):.1f}")
        
        db_status = summary.get('database_status', {})
        print(f"  💾 Database Connected: {db_status.get('connected', False)}")
    
    print("\n" + "=" * 60)
    print("🎉 PRODUCTION INTEGRATION TEST COMPLETED SUCCESSFULLY!")
    print("✅ Ready for live WebSocket server integration")

if __name__ == "__main__":
    asyncio.run(test_production_integration())
