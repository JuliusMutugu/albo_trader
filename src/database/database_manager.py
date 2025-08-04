"""
Database Manager - SQLite database for trade logging and analytics
Handles trade history, compliance events, and system metrics
"""

import sqlite3
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import aiosqlite
from dataclasses import asdict

class DatabaseManager:
    """
    SQLite database manager for the Guardian system
    """
    
    def __init__(self, db_path: str = "data/guardian.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connection pool for async operations
        self.connection = None
        
        # Schema version for migrations
        self.schema_version = 1
    
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            self.connection = await aiosqlite.connect(str(self.db_path))
            
            # Enable foreign keys
            await self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            await self._create_tables()
            
            # Check and run migrations
            await self._check_migrations()
            
            await self.connection.commit()
            
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        
        # Trades table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                instrument TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                position_size REAL NOT NULL,
                side TEXT NOT NULL,  -- 'long' or 'short'
                pnl REAL,
                win BOOLEAN,
                hold_time_minutes INTEGER,
                strategy_signal TEXT,
                enigma_power_score INTEGER,
                enigma_confluence TEXT,
                kelly_percentage REAL,
                risk_percentage REAL,
                status TEXT DEFAULT 'open',  -- 'open', 'closed', 'cancelled'
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # OCR readings table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS ocr_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                power_score INTEGER,
                confluence_level TEXT,
                signal_color TEXT,
                macvu_state TEXT,
                current_price REAL,
                confidence REAL,
                validated BOOLEAN,
                processing_time_ms INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Compliance events table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS compliance_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                level TEXT NOT NULL,  -- 'warning', 'critical', 'violation'
                current_value REAL,
                threshold_value REAL,
                message TEXT,
                action_taken TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Kelly metrics table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS kelly_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                instrument TEXT,  -- NULL for general metrics
                win_rate REAL,
                avg_win REAL,
                avg_loss REAL,
                payoff_ratio REAL,
                kelly_percentage REAL,
                half_kelly_percentage REAL,
                confidence_level REAL,
                sample_size INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Cadence patterns table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS cadence_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                pattern_type TEXT,
                avg_power_score REAL,
                state TEXT,
                duration_minutes INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System metrics table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                component TEXT NOT NULL,  -- 'ocr', 'kelly', 'cadence', 'compliance', 'websocket'
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_data TEXT,  -- JSON data for complex metrics
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Configuration history table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                config_key TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indices for performance
        await self._create_indices()
    
    async def _create_indices(self):
        """Create database indices for performance"""
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_instrument ON trades(instrument)",
            "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)",
            "CREATE INDEX IF NOT EXISTS idx_ocr_timestamp ON ocr_readings(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_timestamp ON compliance_events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_rule ON compliance_events(rule_id)",
            "CREATE INDEX IF NOT EXISTS idx_kelly_timestamp ON kelly_metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_kelly_instrument ON kelly_metrics(instrument)",
            "CREATE INDEX IF NOT EXISTS idx_cadence_start ON cadence_patterns(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_component ON system_metrics(component)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)"
        ]
        
        for index_sql in indices:
            await self.connection.execute(index_sql)
    
    async def _check_migrations(self):
        """Check and run database migrations"""
        # Get current schema version
        try:
            cursor = await self.connection.execute(
                "SELECT value FROM config_history WHERE config_key = 'schema_version' ORDER BY id DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            current_version = int(row[0]) if row else 0
        except:
            current_version = 0
        
        # Run migrations if needed
        if current_version < self.schema_version:
            await self._run_migrations(current_version)
    
    async def _run_migrations(self, from_version: int):
        """Run database migrations"""
        self.logger.info(f"Running migrations from version {from_version} to {self.schema_version}")
        
        # Record migration
        await self.connection.execute("""
            INSERT INTO config_history (timestamp, config_key, old_value, new_value, changed_by, reason)
            VALUES (?, 'schema_version', ?, ?, 'system', 'database_migration')
        """, (datetime.now().isoformat(), str(from_version), str(self.schema_version)))
    
    # Trade operations
    async def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """Insert a new trade record"""
        try:
            cursor = await self.connection.execute("""
                INSERT INTO trades (
                    timestamp, instrument, entry_price, exit_price, position_size, side,
                    pnl, win, hold_time_minutes, strategy_signal, enigma_power_score,
                    enigma_confluence, kelly_percentage, risk_percentage, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data.get('timestamp', datetime.now().isoformat()),
                trade_data['instrument'],
                trade_data['entry_price'],
                trade_data.get('exit_price'),
                trade_data['position_size'],
                trade_data['side'],
                trade_data.get('pnl'),
                trade_data.get('win'),
                trade_data.get('hold_time_minutes'),
                trade_data.get('strategy_signal'),
                trade_data.get('enigma_power_score'),
                trade_data.get('enigma_confluence'),
                trade_data.get('kelly_percentage'),
                trade_data.get('risk_percentage'),
                trade_data.get('status', 'open'),
                trade_data.get('notes')
            ))
            
            await self.connection.commit()
            return cursor.lastrowid
            
        except Exception as e:
            self.logger.error(f"Error inserting trade: {e}")
            raise
    
    async def update_trade(self, trade_id: int, update_data: Dict[str, Any]):
        """Update an existing trade record"""
        try:
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for key, value in update_data.items():
                if key != 'id':  # Don't allow updating ID
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if not set_clauses:
                return
            
            # Add updated_at timestamp
            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(trade_id)
            
            query = f"UPDATE trades SET {', '.join(set_clauses)} WHERE id = ?"
            
            await self.connection.execute(query, values)
            await self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating trade {trade_id}: {e}")
            raise
    
    async def get_trades(self, 
                        instrument: str = None,
                        start_date: datetime = None,
                        end_date: datetime = None,
                        status: str = None,
                        limit: int = None) -> List[Dict[str, Any]]:
        """Get trade records with filtering"""
        try:
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if instrument:
                query += " AND instrument = ?"
                params.append(instrument)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor = await self.connection.execute(query, params)
            rows = await cursor.fetchall()
            
            # Convert to dictionaries
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting trades: {e}")
            return []
    
    # OCR operations
    async def insert_ocr_reading(self, reading_data: Dict[str, Any]):
        """Insert OCR reading"""
        try:
            await self.connection.execute("""
                INSERT INTO ocr_readings (
                    timestamp, power_score, confluence_level, signal_color,
                    macvu_state, current_price, confidence, validated, processing_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reading_data.get('timestamp', datetime.now().isoformat()),
                reading_data.get('power_score'),
                reading_data.get('confluence_level'),
                reading_data.get('signal_color'),
                reading_data.get('macvu_state'),
                reading_data.get('current_price'),
                reading_data.get('confidence'),
                reading_data.get('validated', False),
                reading_data.get('processing_time_ms')
            ))
            
            await self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Error inserting OCR reading: {e}")
            raise
    
    async def get_recent_ocr_readings(self, hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent OCR readings"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor = await self.connection.execute("""
                SELECT * FROM ocr_readings 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (cutoff_time.isoformat(), limit))
            
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting OCR readings: {e}")
            return []
    
    # Compliance operations
    async def insert_compliance_event(self, event_data: Dict[str, Any]):
        """Insert compliance event"""
        try:
            await self.connection.execute("""
                INSERT INTO compliance_events (
                    timestamp, rule_id, violation_type, level, current_value,
                    threshold_value, message, action_taken, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get('timestamp', datetime.now().isoformat()),
                event_data['rule_id'],
                event_data['violation_type'],
                event_data['level'],
                event_data.get('current_value'),
                event_data.get('threshold_value'),
                event_data.get('message'),
                event_data.get('action_taken'),
                event_data.get('resolved', False)
            ))
            
            await self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Error inserting compliance event: {e}")
            raise
    
    async def get_compliance_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent compliance events"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor = await self.connection.execute("""
                SELECT * FROM compliance_events 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            """, (cutoff_time.isoformat(),))
            
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting compliance events: {e}")
            return []
    
    # Kelly metrics operations
    async def insert_kelly_metrics(self, metrics_data: Dict[str, Any]):
        """Insert Kelly metrics"""
        try:
            await self.connection.execute("""
                INSERT INTO kelly_metrics (
                    timestamp, instrument, win_rate, avg_win, avg_loss,
                    payoff_ratio, kelly_percentage, half_kelly_percentage,
                    confidence_level, sample_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics_data.get('timestamp', datetime.now().isoformat()),
                metrics_data.get('instrument'),
                metrics_data.get('win_rate'),
                metrics_data.get('avg_win'),
                metrics_data.get('avg_loss'),
                metrics_data.get('payoff_ratio'),
                metrics_data.get('kelly_percentage'),
                metrics_data.get('half_kelly_percentage'),
                metrics_data.get('confidence_level'),
                metrics_data.get('sample_size')
            ))
            
            await self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Error inserting Kelly metrics: {e}")
            raise
    
    # System metrics operations
    async def insert_system_metric(self, component: str, metric_name: str, metric_value: float, metric_data: Dict = None):
        """Insert system metric"""
        try:
            await self.connection.execute("""
                INSERT INTO system_metrics (timestamp, component, metric_name, metric_value, metric_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                component,
                metric_name,
                metric_value,
                json.dumps(metric_data) if metric_data else None
            ))
            
            await self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Error inserting system metric: {e}")
            raise
    
    # Analytics and reporting
    async def get_trading_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get trading statistics for the specified period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get trade statistics
            cursor = await self.connection.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN win = 1 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN win = 0 THEN 1 END) as losing_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    MIN(pnl) as worst_trade,
                    MAX(pnl) as best_trade,
                    AVG(hold_time_minutes) as avg_hold_time,
                    COUNT(DISTINCT instrument) as instruments_traded
                FROM trades 
                WHERE timestamp >= ? AND status = 'closed'
            """, (cutoff_date.isoformat(),))
            
            stats = await cursor.fetchone()
            
            if stats[0] == 0:  # No trades
                return {'no_trades': True, 'period_days': days}
            
            # Calculate additional metrics
            win_rate = (stats[1] / stats[0]) * 100 if stats[0] > 0 else 0
            
            # Get instrument breakdown
            cursor = await self.connection.execute("""
                SELECT instrument, COUNT(*) as trades, SUM(pnl) as pnl 
                FROM trades 
                WHERE timestamp >= ? AND status = 'closed'
                GROUP BY instrument
                ORDER BY pnl DESC
            """, (cutoff_date.isoformat(),))
            
            instrument_stats = await cursor.fetchall()
            
            return {
                'period_days': days,
                'total_trades': stats[0],
                'winning_trades': stats[1],
                'losing_trades': stats[2],
                'win_rate': round(win_rate, 2),
                'total_pnl': round(stats[3], 2) if stats[3] else 0,
                'avg_pnl': round(stats[4], 2) if stats[4] else 0,
                'worst_trade': round(stats[5], 2) if stats[5] else 0,
                'best_trade': round(stats[6], 2) if stats[6] else 0,
                'avg_hold_time_minutes': round(stats[7], 1) if stats[7] else 0,
                'instruments_traded': stats[8],
                'instrument_breakdown': [
                    {'instrument': row[0], 'trades': row[1], 'pnl': round(row[2], 2)}
                    for row in instrument_stats
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trading statistics: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to prevent database bloat"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.isoformat()
            
            # Clean up old OCR readings (keep fewer)
            await self.connection.execute("""
                DELETE FROM ocr_readings WHERE timestamp < ?
            """, (cutoff_str,))
            
            # Clean up old system metrics
            await self.connection.execute("""
                DELETE FROM system_metrics WHERE timestamp < ?
            """, (cutoff_str,))
            
            # Clean up resolved compliance events older than retention period
            await self.connection.execute("""
                DELETE FROM compliance_events 
                WHERE timestamp < ? AND resolved = 1
            """, (cutoff_str,))
            
            await self.connection.commit()
            
            self.logger.info(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    async def export_data(self, export_path: str, start_date: datetime = None, end_date: datetime = None):
        """Export data to JSON file"""
        try:
            export_data = {}
            
            # Export trades
            trades = await self.get_trades(start_date=start_date, end_date=end_date)
            export_data['trades'] = trades
            
            # Export compliance events
            compliance_events = await self.get_compliance_events(hours=24*30)  # 30 days
            export_data['compliance_events'] = compliance_events
            
            # Export recent OCR readings
            ocr_readings = await self.get_recent_ocr_readings(hours=24*7)  # 7 days
            export_data['ocr_readings'] = ocr_readings
            
            # Add metadata
            export_data['metadata'] = {
                'export_timestamp': datetime.now().isoformat(),
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'total_records': len(trades) + len(compliance_events) + len(ocr_readings)
            }
            
            # Write to file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Data exported to {export_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            self.logger.info("Database connection closed")
    
    def is_healthy(self) -> bool:
        """Check if database is healthy"""
        return self.connection is not None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if not self.connection:
                return {'error': 'No database connection'}
            
            # Get table counts
            tables = ['trades', 'ocr_readings', 'compliance_events', 'kelly_metrics', 'cadence_patterns', 'system_metrics']
            counts = {}
            
            for table in tables:
                cursor = await self.connection.execute(f"SELECT COUNT(*) FROM {table}")
                count = await cursor.fetchone()
                counts[f"{table}_count"] = count[0] if count else 0
            
            # Get database size
            cursor = await self.connection.execute("PRAGMA page_count")
            page_count = await cursor.fetchone()
            cursor = await self.connection.execute("PRAGMA page_size")
            page_size = await cursor.fetchone()
            
            db_size_bytes = (page_count[0] * page_size[0]) if page_count and page_size else 0
            
            return {
                **counts,
                'database_size_mb': round(db_size_bytes / (1024 * 1024), 2),
                'database_path': str(self.db_path),
                'is_healthy': self.is_healthy()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting database statistics: {e}")
            return {'error': str(e)}
