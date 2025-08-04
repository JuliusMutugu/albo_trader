"""
Core Guardian Engine - Orchestrates all trading decisions and risk management.

This module integrates OCR reading, Kelly Criterion calculations, Apex compliance,
and cadence tracking to make intelligent trading decisions.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..ocr.ocr_processor import OCRProcessor
from ..kelly.kelly_engine import KellyEngine
from ..cadence.cadence_tracker import CadenceTracker
from ..compliance.compliance_monitor import ComplianceMonitor
from ..websocket.websocket_server import WebSocketServer
from ..database.database_manager import DatabaseManager


class GuardianEngine:
    """
    Main decision engine that coordinates all trading components.
    
    Responsibilities:
    - Orchestrate OCR signal reading
    - Calculate Kelly position sizing
    - Monitor Apex compliance
    - Track Enigma cadence
    - Communicate with NinjaTrader
    - Provide mobile API endpoints
    """
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.ocr_processor = None
        self.kelly_engine = None
        self.cadence_tracker = None
        self.compliance_monitor = None
        self.websocket_server = None
        self.database_manager = None
        
        # State tracking
        self.is_trading_enabled = False
        self.last_signal_time = None
        self.current_position = None
        
    async def initialize(self):
        """Initialize all engine components."""
        try:
            self.logger.info("Initializing Guardian Engine components...")
            
            # Initialize database manager
            self.database_manager = DatabaseManager(self.settings.get('database', {}).get('path', 'data/guardian.db'))
            await self.database_manager.initialize()
            
            # Initialize OCR processor with real OCR capabilities
            self.ocr_processor = OCRProcessor(
                regions_config=self.settings.get('ocr', {}).get('regions_config', 'config/ocr_regions.json'),
                confidence_threshold=self.settings.get('ocr', {}).get('confidence_threshold', 0.8)
            )
            await self.ocr_processor.initialize()
            
            # Initialize Kelly engine
            self.kelly_engine = KellyEngine(
                trade_history_size=self.settings.get('kelly', {}).get('trade_history_size', 100),
                min_trades_for_kelly=self.settings.get('kelly', {}).get('min_trades_for_kelly', 20),
                max_position_percentage=self.settings.get('kelly', {}).get('max_position_percentage', 0.05),
                kelly_multiplier=self.settings.get('kelly', {}).get('kelly_multiplier', 0.5)
            )
            
            # Initialize cadence tracker
            self.cadence_tracker = CadenceTracker(
                reading_history_hours=self.settings.get('cadence', {}).get('reading_history_hours', 48),
                low_power_threshold=self.settings.get('cadence', {}).get('low_power_threshold', 30),
                failure_duration_minutes=self.settings.get('cadence', {}).get('failure_duration_minutes', 60)
            )
            
            # Initialize compliance monitor
            self.compliance_monitor = ComplianceMonitor(
                account_size=self.settings.get('compliance', {}).get('account_size', 50000.0),
                max_loss_percentage=self.settings.get('compliance', {}).get('max_loss_percentage', 0.08),
                daily_loss_percentage=self.settings.get('compliance', {}).get('daily_loss_percentage', 0.05),
                trailing_stop_percentage=self.settings.get('compliance', {}).get('trailing_stop_percentage', 0.05)
            )
            
            # Initialize WebSocket server
            self.websocket_server = WebSocketServer(
                host=self.settings.get('websocket', {}).get('host', 'localhost'),
                port=self.settings.get('websocket', {}).get('port', 8765),
                ssl_cert_path=self.settings.get('websocket', {}).get('ssl_cert_path'),
                ssl_key_path=self.settings.get('websocket', {}).get('ssl_key_path')
            )
            
            self.logger.info("Guardian Engine initialization complete")
            
        except Exception as e:
            self.logger.error(f"Guardian Engine initialization failed: {e}")
            raise
            
    async def start(self):
        """Start the Guardian Engine main loop."""
        try:
            self.logger.info("Starting Guardian Engine...")
            
            # Start all components
            await asyncio.gather(
                self._ocr_monitoring_loop(),
                self._risk_monitoring_loop(),
                self._apex_compliance_loop(),
                self.mobile_server.start(),
                self.ninjatrader_client.start()
            )
            
        except Exception as e:
            self.logger.error(f"Guardian Engine error: {e}")
            raise
            
    async def shutdown(self):
        """Shutdown all engine components."""
        self.logger.info("Shutting down Guardian Engine...")
        
        if self.mobile_server:
            await self.mobile_server.shutdown()
            
        if self.ninjatrader_client:
            await self.ninjatrader_client.shutdown()
            
        self.logger.info("Guardian Engine shutdown complete")
        
    async def _ocr_monitoring_loop(self):
        """Main OCR monitoring and signal processing loop."""
        while True:
            try:
                # Read Enigma panel
                signal_data = await self.enigma_reader.read_panel()
                
                if signal_data:
                    await self._process_enigma_signal(signal_data)
                    
                # Control reading frequency
                await asyncio.sleep(self.settings['ocr']['read_interval'])
                
            except Exception as e:
                self.logger.error(f"OCR monitoring error: {e}")
                await asyncio.sleep(1)
                
    async def _process_enigma_signal(self, signal_data: Dict[str, Any]):
        """Process new Enigma signal and make trading decision."""
        try:
            self.logger.debug(f"Processing Enigma signal: {signal_data}")
            
            # Update cadence tracker
            self.cadence_tracker.update_signal(signal_data)
            
            # Check if we should consider trading
            if not self._should_consider_trade(signal_data):
                return
                
            # Calculate position sizing
            position_size = await self._calculate_position_size(signal_data)
            
            # Make trading decision
            decision = await self._make_trading_decision(signal_data, position_size)
            
            if decision['trade']:
                await self._execute_trade_decision(decision)
                
        except Exception as e:
            self.logger.error(f"Signal processing error: {e}")
            
    def _should_consider_trade(self, signal_data: Dict[str, Any]) -> bool:
        """Determine if signal meets basic criteria for consideration."""
        
        # Check if trading is enabled
        if not self.is_trading_enabled:
            return False
            
        # Check signal quality filters
        if signal_data.get('power', 0) < self.settings['filters']['min_power']:
            return False
            
        if signal_data.get('confluence') not in self.settings['filters']['required_confluence']:
            return False
            
        # Check cadence threshold
        if not self.cadence_tracker.threshold_met():
            return False
            
        return True
        
    async def _calculate_position_size(self, signal_data: Dict[str, Any]) -> int:
        """Calculate optimal position size using Kelly Criterion."""
        try:
            # Get current ATR for risk calculation
            atr_value = await self.atr_calculator.get_current_atr()
            
            # Calculate Kelly fraction
            kelly_fraction = self.kelly_engine.calculate_kelly_fraction(atr_value)
            
            # Apply Apex position limits
            max_position = self.apex_monitor.get_max_position_size()
            
            # Calculate final position size
            position_size = min(
                self.kelly_engine.calculate_position_size(kelly_fraction),
                max_position
            )
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Position sizing error: {e}")
            return 0
            
    async def _make_trading_decision(self, signal_data: Dict[str, Any], position_size: int) -> Dict[str, Any]:
        """Make final trading decision based on all criteria."""
        
        decision = {
            'trade': False,
            'direction': signal_data.get('direction'),
            'position_size': position_size,
            'stop_loss': None,
            'profit_target': None,
            'reason': None
        }
        
        try:
            # Final Apex compliance check
            if not self.apex_monitor.can_open_position(position_size):
                decision['reason'] = "Apex compliance violation"
                return decision
                
            # Calculate stop loss and profit target
            atr_value = await self.atr_calculator.get_current_atr()
            decision['stop_loss'] = self.atr_calculator.calculate_stop_loss(
                signal_data.get('entry_price'), atr_value, signal_data.get('direction')
            )
            decision['profit_target'] = self.atr_calculator.calculate_profit_target(
                signal_data.get('entry_price'), atr_value, signal_data.get('direction')
            )
            
            # All checks passed
            decision['trade'] = True
            decision['reason'] = "All criteria met"
            
        except Exception as e:
            self.logger.error(f"Decision making error: {e}")
            decision['reason'] = f"Error: {e}"
            
        return decision
        
    async def _execute_trade_decision(self, decision: Dict[str, Any]):
        """Execute approved trading decision."""
        try:
            self.logger.info(f"Executing trade decision: {decision}")
            
            # Send order to NinjaTrader
            await self.ninjatrader_client.send_order(decision)
            
            # Update position tracking
            self.current_position = decision
            self.last_signal_time = datetime.now()
            
            # Log trade for Kelly engine
            # Note: Actual outcome will be logged when position closes
            
        except Exception as e:
            self.logger.error(f"Trade execution error: {e}")
            
    async def _risk_monitoring_loop(self):
        """Continuous risk monitoring and position management."""
        while True:
            try:
                if self.current_position:
                    # Monitor position risk
                    await self._monitor_position_risk()
                    
                await asyncio.sleep(self.settings['risk']['monitor_interval'])
                
            except Exception as e:
                self.logger.error(f"Risk monitoring error: {e}")
                await asyncio.sleep(1)
                
    async def _monitor_position_risk(self):
        """Monitor current position for risk violations."""
        try:
            # Check Apex compliance
            if self.apex_monitor.is_violation_imminent():
                await self._emergency_close_position("Apex violation imminent")
                
            # Check ATR-based stops
            # Implementation depends on real-time price feed
            
        except Exception as e:
            self.logger.error(f"Position monitoring error: {e}")
            
    async def _emergency_close_position(self, reason: str):
        """Emergency position closure."""
        try:
            self.logger.warning(f"Emergency position closure: {reason}")
            
            await self.ninjatrader_client.close_position()
            self.current_position = None
            
        except Exception as e:
            self.logger.error(f"Emergency closure error: {e}")
            
    async def _apex_compliance_loop(self):
        """Continuous Apex compliance monitoring."""
        while True:
            try:
                # Update account status
                await self.apex_monitor.update_account_status()
                
                # Check for violations
                if self.apex_monitor.has_violations():
                    self.is_trading_enabled = False
                    self.logger.warning("Trading disabled due to Apex violations")
                    
                await asyncio.sleep(self.settings['apex']['monitor_interval'])
                
            except Exception as e:
                self.logger.error(f"Apex monitoring error: {e}")
                await asyncio.sleep(5)
                
    # Mobile API interface methods
    def enable_trading(self) -> bool:
        """Enable trading (called from mobile API)."""
        if self.apex_monitor.can_enable_trading():
            self.is_trading_enabled = True
            self.logger.info("Trading enabled via mobile command")
            return True
        return False
        
    def disable_trading(self) -> bool:
        """Disable trading (called from mobile API)."""
        self.is_trading_enabled = False
        self.logger.info("Trading disabled via mobile command")
        return True
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status (called from mobile API)."""
        return {
            'trading_enabled': self.is_trading_enabled,
            'current_position': self.current_position,
            'apex_status': self.apex_monitor.get_status(),
            'kelly_stats': self.kelly_engine.get_stats(),
            'cadence_status': self.cadence_tracker.get_status(),
            'last_signal': self.last_signal_time
        }
