"""
Enhanced Database Manager for Enigma-Apex Trading System
Professional-grade data management with performance tracking
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
import aiosqlite

@dataclass
class TradingSignal:
    """Enhanced trading signal data structure"""
    signal_id: str
    timestamp: datetime
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence_score: float
    power_score: int
    confluence_level: str
    signal_color: str
    macvu_state: str
    source: str = 'enigma_ocr'
    is_active: bool = True
    metadata: Dict = None

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    timeframe: str = '1m'

class EnhancedDatabaseManager:
    """Professional database manager for trading system"""
    
    def __init__(self, db_path: str = "enigma_apex_pro.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for database operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database.log'),
                logging.StreamHandler()
            ]
        )
    
    async def initialize_database(self):
        """Initialize database with enhanced schema"""
        
        create_tables_sql = [
            # Market data table
            """
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                timeframe TEXT DEFAULT '1m',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Enhanced signals table
            """
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence_score REAL,
                power_score INTEGER,
                confluence_level TEXT,
                signal_color TEXT,
                macvu_state TEXT,
                source TEXT DEFAULT 'enigma_ocr',
                is_active BOOLEAN DEFAULT 1,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Trading performance table
            """
            CREATE TABLE IF NOT EXISTS trade_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                signal_id TEXT,
                symbol TEXT NOT NULL,
                entry_price REAL,
                exit_price REAL,
                quantity REAL,
                side TEXT, -- 'LONG' or 'SHORT'
                entry_time DATETIME,
                exit_time DATETIME,
                pnl REAL,
                commission REAL,
                status TEXT DEFAULT 'OPEN',
                strategy_name TEXT,
                FOREIGN KEY (signal_id) REFERENCES trading_signals(signal_id)
            )
            """,
            
            # System metrics table
            """
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # WebSocket connections log
            """
            CREATE TABLE IF NOT EXISTS websocket_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                client_type TEXT,
                connection_time DATETIME,
                disconnection_time DATETIME,
                messages_sent INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                ip_address TEXT
            )
            """
        ]
        
        # Create indexes for performance
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time ON market_data(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON trading_signals(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_signals_type ON trading_signals(signal_type)",
            "CREATE INDEX IF NOT EXISTS idx_performance_symbol ON trade_performance(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_performance_pnl ON trade_performance(pnl)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON system_metrics(metric_name, timestamp)"
        ]
        
        async with aiosqlite.connect(self.db_path) as db:
            # Create tables
            for sql in create_tables_sql:
                await db.execute(sql)
            
            # Create indexes
            for sql in create_indexes_sql:
                await db.execute(sql)
            
            await db.commit()
            
        self.logger.info("Database initialized successfully")
    
    async def store_signal(self, signal: TradingSignal):
        """Store trading signal with enhanced metadata"""
        
        sql = """
        INSERT OR REPLACE INTO trading_signals 
        (signal_id, timestamp, symbol, signal_type, confidence_score, 
         power_score, confluence_level, signal_color, macvu_state, 
         source, is_active, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        metadata_json = json.dumps(signal.metadata) if signal.metadata else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql, (
                signal.signal_id,
                signal.timestamp,
                signal.symbol,
                signal.signal_type,
                signal.confidence_score,
                signal.power_score,
                signal.confluence_level,
                signal.signal_color,
                signal.macvu_state,
                signal.source,
                signal.is_active,
                metadata_json
            ))
            await db.commit()
        
        self.logger.info(f"Stored signal: {signal.signal_id} for {signal.symbol}")
    
    async def store_market_data(self, market_data: MarketData):
        """Store market data efficiently"""
        
        sql = """
        INSERT INTO market_data 
        (symbol, timestamp, open_price, high_price, low_price, close_price, volume, timeframe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql, (
                market_data.symbol,
                market_data.timestamp,
                market_data.open_price,
                market_data.high_price,
                market_data.low_price,
                market_data.close_price,
                market_data.volume,
                market_data.timeframe
            ))
            await db.commit()
    
    async def get_signals_by_symbol(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get recent signals for a symbol"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        sql = """
        SELECT * FROM trading_signals 
        WHERE symbol = ? AND timestamp > ?
        ORDER BY timestamp DESC
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, (symbol, cutoff_time))
            rows = await cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    async def calculate_signal_performance(self, symbol: Optional[str] = None, days: int = 30) -> Dict:
        """Calculate comprehensive signal performance metrics"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        base_sql = """
        SELECT s.*, t.pnl, t.status
        FROM trading_signals s
        LEFT JOIN trade_performance t ON s.signal_id = t.signal_id
        WHERE s.timestamp > ?
        """
        
        params = [cutoff_date]
        if symbol:
            base_sql += " AND s.symbol = ?"
            params.append(symbol)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(base_sql, params)
            rows = await cursor.fetchall()
            
            if not rows:
                return {"error": "No data available for analysis"}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame([dict(row) for row in rows])
            
            # Calculate metrics
            total_signals = len(df)
            signals_with_trades = len(df[df['pnl'].notna()])
            
            if signals_with_trades == 0:
                return {
                    "total_signals": total_signals,
                    "signals_with_trades": 0,
                    "note": "No completed trades for analysis"
                }
            
            trade_df = df[df['pnl'].notna()]
            
            metrics = {
                "total_signals": total_signals,
                "signals_with_trades": signals_with_trades,
                "winning_signals": len(trade_df[trade_df['pnl'] > 0]),
                "losing_signals": len(trade_df[trade_df['pnl'] < 0]),
                "win_rate": len(trade_df[trade_df['pnl'] > 0]) / len(trade_df) * 100,
                "total_pnl": trade_df['pnl'].sum(),
                "average_pnl": trade_df['pnl'].mean(),
                "best_trade": trade_df['pnl'].max(),
                "worst_trade": trade_df['pnl'].min(),
                "profit_factor": abs(trade_df[trade_df['pnl'] > 0]['pnl'].sum() / 
                                   trade_df[trade_df['pnl'] < 0]['pnl'].sum()) 
                                   if len(trade_df[trade_df['pnl'] < 0]) > 0 else float('inf')
            }
            
            # Performance by signal type
            signal_type_performance = {}
            for signal_type in trade_df['signal_type'].unique():
                type_df = trade_df[trade_df['signal_type'] == signal_type]
                signal_type_performance[signal_type] = {
                    "count": len(type_df),
                    "win_rate": len(type_df[type_df['pnl'] > 0]) / len(type_df) * 100,
                    "total_pnl": type_df['pnl'].sum(),
                    "average_pnl": type_df['pnl'].mean()
                }
            
            metrics["by_signal_type"] = signal_type_performance
            
            return metrics
    
    async def log_system_metric(self, metric_name: str, metric_value: float, metadata: Dict = None):
        """Log system performance metrics"""
        
        sql = """
        INSERT INTO system_metrics (metric_name, metric_value, metric_metadata)
        VALUES (?, ?, ?)
        """
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql, (metric_name, metric_value, metadata_json))
            await db.commit()
    
    async def log_websocket_connection(self, client_id: str, client_type: str, 
                                     connection_time: datetime, ip_address: str = None):
        """Log WebSocket connection for analytics"""
        
        sql = """
        INSERT INTO websocket_connections 
        (client_id, client_type, connection_time, ip_address)
        VALUES (?, ?, ?, ?)
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql, (client_id, client_type, connection_time, ip_address))
            await db.commit()
    
    async def get_system_health_metrics(self) -> Dict:
        """Get comprehensive system health metrics"""
        
        metrics = {}
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Signal metrics
            cursor = await db.execute("""
                SELECT COUNT(*) as total_signals,
                       COUNT(CASE WHEN timestamp > datetime('now', '-1 hour') THEN 1 END) as signals_last_hour,
                       COUNT(CASE WHEN timestamp > datetime('now', '-24 hours') THEN 1 END) as signals_last_24h
                FROM trading_signals
            """)
            signal_metrics = dict(await cursor.fetchone())
            
            # WebSocket metrics
            cursor = await db.execute("""
                SELECT COUNT(*) as total_connections,
                       COUNT(CASE WHEN connection_time > datetime('now', '-1 hour') THEN 1 END) as connections_last_hour,
                       AVG(messages_sent) as avg_messages_sent,
                       AVG(messages_received) as avg_messages_received
                FROM websocket_connections
            """)
            websocket_metrics = dict(await cursor.fetchone())
            
            # Performance metrics
            cursor = await db.execute("""
                SELECT COUNT(*) as total_trades,
                       SUM(pnl) as total_pnl,
                       AVG(pnl) as avg_pnl,
                       COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades
                FROM trade_performance
                WHERE entry_time > datetime('now', '-30 days')
            """)
            performance_metrics = dict(await cursor.fetchone())
            
            metrics = {
                "signals": signal_metrics,
                "websocket": websocket_metrics,
                "performance": performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        return metrics
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to maintain database performance"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleanup_queries = [
            ("market_data", "DELETE FROM market_data WHERE timestamp < ?"),
            ("old_signals", "DELETE FROM trading_signals WHERE timestamp < ? AND is_active = 0"),
            ("old_metrics", "DELETE FROM system_metrics WHERE timestamp < ?"),
            ("old_connections", "DELETE FROM websocket_connections WHERE connection_time < ?")
        ]
        
        async with aiosqlite.connect(self.db_path) as db:
            for table_name, query in cleanup_queries:
                cursor = await db.execute(query, (cutoff_date,))
                deleted_count = cursor.rowcount
                self.logger.info(f"Cleaned up {deleted_count} old records from {table_name}")
            
            await db.commit()
            
            # Vacuum database to reclaim space
            await db.execute("VACUUM")
            
        self.logger.info("Database cleanup completed")

# Example usage and testing
async def main():
    """Example usage of the enhanced database manager"""
    
    # Initialize database
    db_manager = EnhancedDatabaseManager()
    await db_manager.initialize_database()
    
    # Store sample signal
    sample_signal = TradingSignal(
        signal_id="TEST_001",
        timestamp=datetime.now(),
        symbol="EURUSD",
        signal_type="BUY",
        confidence_score=0.85,
        power_score=75,
        confluence_level="L3",
        signal_color="GREEN",
        macvu_state="BULLISH",
        metadata={"source_confidence": 0.9, "market_conditions": "trending"}
    )
    
    await db_manager.store_signal(sample_signal)
    
    # Store sample market data
    sample_market_data = MarketData(
        symbol="EURUSD",
        timestamp=datetime.now(),
        open_price=1.0850,
        high_price=1.0875,
        low_price=1.0845,
        close_price=1.0870,
        volume=150000
    )
    
    await db_manager.store_market_data(sample_market_data)
    
    # Get performance metrics
    performance = await db_manager.calculate_signal_performance("EURUSD")
    print("Performance Metrics:", json.dumps(performance, indent=2))
    
    # Get system health
    health = await db_manager.get_system_health_metrics()
    print("System Health:", json.dumps(health, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
