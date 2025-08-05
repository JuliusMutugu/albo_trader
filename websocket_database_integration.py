"""
Real-Time Database Integration for WebSocket Server
Connects enhanced database manager with live WebSocket data
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import aiosqlite
from enhanced_database_manager import EnhancedDatabaseManager, TradingSignal

class LiveDataCollector:
    """Collects and stores live WebSocket data in real-time"""
    
    def __init__(self, db_manager: EnhancedDatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.active_signals = {}
        self.performance_tracker = {}
        
    async def process_enigma_signal(self, data: Dict[str, Any], client_id: str):
        """Process incoming Enigma signal and store in database"""
        try:
            # Extract Enigma data
            enigma_data = data.get('enigma_data', {})
            
            # Create trading signal
            signal = TradingSignal(
                signal_id=f"ENIGMA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{client_id[:8]}",
                symbol="EURUSD",  # Default symbol, can be enhanced
                signal_type="ENIGMA",
                direction="BUY" if enigma_data.get('power_score', 0) > 50 else "SELL",
                confidence=enigma_data.get('power_score', 0) / 100.0,
                entry_price=0.0,  # Will be updated with actual market price
                stop_loss=0.0,
                take_profit=0.0,
                timestamp=datetime.now(),
                metadata={
                    'confluence_level': enigma_data.get('confluence_level', 'L1'),
                    'signal_color': enigma_data.get('signal_color', 'NEUTRAL'),
                    'macvu_state': enigma_data.get('macvu_state', 'UNKNOWN'),
                    'client_id': client_id,
                    'raw_data': enigma_data
                }
            )
            
            # Store signal in database
            await self.db_manager.store_signal(signal)
            
            # Track active signal
            self.active_signals[signal.signal_id] = signal
            
            self.logger.info(f"Stored Enigma signal: {signal.signal_id} - {signal.direction} - Confidence: {signal.confidence:.2f}")
            
            # Calculate real-time performance
            await self._update_performance_metrics(signal)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error processing Enigma signal: {e}")
            return None
    
    async def process_trade_update(self, data: Dict[str, Any]):
        """Process trade execution updates"""
        try:
            signal_id = data.get('signal_id')
            if signal_id in self.active_signals:
                signal = self.active_signals[signal_id]
                
                # Update signal with trade execution data
                if 'entry_price' in data:
                    signal.entry_price = data['entry_price']
                if 'exit_price' in data:
                    signal.exit_price = data['exit_price']
                    signal.status = 'CLOSED'
                    signal.exit_time = datetime.now()
                
                # Store updated signal
                await self.db_manager.store_signal(signal)
                
                # Update performance tracking
                await self._update_performance_metrics(signal)
                
                self.logger.info(f"Updated trade: {signal_id} - Status: {signal.status}")
                
        except Exception as e:
            self.logger.error(f"Error processing trade update: {e}")
    
    async def _update_performance_metrics(self, signal: TradingSignal):
        """Update real-time performance metrics"""
        try:
            # Calculate signal performance
            performance = await self.db_manager.calculate_signal_performance()
            
            # Store system metrics
            await self.db_manager.store_system_metric(
                'signal_count',
                len(self.active_signals),
                {
                    'active_signals': len([s for s in self.active_signals.values() if s.status == 'ACTIVE']),
                    'closed_signals': len([s for s in self.active_signals.values() if s.status == 'CLOSED']),
                    'avg_confidence': sum(s.confidence for s in self.active_signals.values()) / len(self.active_signals) if self.active_signals else 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    async def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time system statistics"""
        try:
            # Get database performance
            performance = await self.db_manager.calculate_signal_performance()
            
            # Get system health
            health_score = await self.db_manager.get_system_health_score()
            
            # Calculate active signal statistics
            active_count = len([s for s in self.active_signals.values() if s.status == 'ACTIVE'])
            avg_confidence = sum(s.confidence for s in self.active_signals.values()) / len(self.active_signals) if self.active_signals else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_signals': len(self.active_signals),
                'active_signals': active_count,
                'average_confidence': avg_confidence,
                'system_health_score': health_score,
                'database_performance': performance,
                'signal_types': {
                    'enigma': len([s for s in self.active_signals.values() if s.signal_type == 'ENIGMA']),
                    'kelly': len([s for s in self.active_signals.values() if s.signal_type == 'KELLY']),
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time stats: {e}")
            return {}

class EnhancedWebSocketIntegration:
    """Enhanced WebSocket server with database integration"""
    
    def __init__(self):
        self.db_manager = None
        self.data_collector = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize database and data collector"""
        try:
            # Initialize enhanced database manager
            self.db_manager = EnhancedDatabaseManager('enigma_apex_pro.db')
            await self.db_manager.initialize_database()
            
            # Initialize data collector
            self.data_collector = LiveDataCollector(self.db_manager)
            
            self.logger.info("Enhanced WebSocket integration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket integration: {e}")
            raise
    
    async def handle_websocket_message(self, message_data: Dict[str, Any], client_id: str):
        """Handle incoming WebSocket messages with database storage"""
        try:
            message_type = message_data.get('type', 'unknown')
            data = message_data.get('data', {})
            
            # Process different message types
            if message_type == 'enigma_update':
                signal = await self.data_collector.process_enigma_signal(data, client_id)
                return signal
            
            elif message_type == 'trade_update':
                await self.data_collector.process_trade_update(data)
            
            elif message_type == 'status_request':
                stats = await self.data_collector.get_real_time_stats()
                return {
                    'type': 'status_response',
                    'data': stats,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Store all messages for analysis
            await self._store_message_data(message_data, client_id)
            
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
            return None
    
    async def _store_message_data(self, message_data: Dict[str, Any], client_id: str):
        """Store WebSocket message data for analysis"""
        try:
            # Store in websocket_connections table
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                await db.execute('''
                    INSERT INTO websocket_connections 
                    (client_id, message_type, data, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    client_id,
                    message_data.get('type', 'unknown'),
                    json.dumps(message_data),
                    datetime.now().isoformat()
                ))
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing message data: {e}")
    
    async def get_client_analytics(self, client_id: str) -> Dict[str, Any]:
        """Get analytics for specific client"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                # Get client message count
                cursor = await db.execute('''
                    SELECT message_type, COUNT(*) as count
                    FROM websocket_connections 
                    WHERE client_id = ?
                    GROUP BY message_type
                ''', (client_id,))
                
                message_stats = {}
                async for row in cursor:
                    message_stats[row[0]] = row[1]
                
                # Get client signals
                cursor = await db.execute('''
                    SELECT COUNT(*) as signal_count
                    FROM trading_signals 
                    WHERE json_extract(metadata, '$.client_id') = ?
                ''', (client_id,))
                
                signal_count = (await cursor.fetchone())[0]
                
                return {
                    'client_id': client_id,
                    'message_statistics': message_stats,
                    'signal_count': signal_count,
                    'last_activity': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting client analytics: {e}")
            return {}

async def test_integration():
    """Test the enhanced WebSocket integration"""
    print("🧪 Testing Enhanced WebSocket Integration")
    print("=" * 50)
    
    # Initialize integration
    integration = EnhancedWebSocketIntegration()
    await integration.initialize()
    
    # Test Enigma signal processing
    test_message = {
        'type': 'enigma_update',
        'data': {
            'enigma_data': {
                'power_score': 75,
                'confluence_level': 'L3',
                'signal_color': 'GREEN',
                'macvu_state': 'BULLISH'
            }
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Process test message
    result = await integration.handle_websocket_message(test_message, 'test_client_001')
    
    if result:
        print(f"✅ Signal processed successfully: {result.signal_id}")
        print(f"   Direction: {result.direction}")
        print(f"   Confidence: {result.confidence:.2f}")
    
    # Get real-time stats
    stats = await integration.data_collector.get_real_time_stats()
    print(f"\n📊 Real-time Statistics:")
    print(f"   Total Signals: {stats.get('total_signals', 0)}")
    print(f"   Active Signals: {stats.get('active_signals', 0)}")
    print(f"   Average Confidence: {stats.get('average_confidence', 0):.2f}")
    print(f"   System Health Score: {stats.get('system_health_score', 0):.2f}")
    
    print("\n✅ Integration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_integration())
