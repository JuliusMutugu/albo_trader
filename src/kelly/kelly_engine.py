"""
Kelly Criterion Engine - Dynamic Position Sizing for Prop Trading
Mathematical position sizing based on win rate, payoff ratio, and account equity
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import json
import asyncio
import numpy as np

@dataclass
class TradeRecord:
    """Individual trade record for Kelly calculations"""
    timestamp: datetime
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    win: bool
    hold_time_minutes: int
    instrument: str
    strategy_signal: str
    
@dataclass
class KellyMetrics:
    """Kelly Criterion calculation results"""
    win_rate: float
    avg_win: float
    avg_loss: float
    payoff_ratio: float
    kelly_percentage: float
    half_kelly_percentage: float
    recommended_size: float
    confidence_level: float
    sample_size: int
    last_updated: datetime

class KellyEngine:
    """
    Kelly Criterion position sizing engine with rolling window analysis
    """
    
    def __init__(self, 
                 trade_history_size: int = 100,
                 min_trades_for_kelly: int = 20,
                 max_position_percentage: float = 0.05,  # 5% max of account
                 kelly_multiplier: float = 0.5):  # Half-Kelly for safety
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.trade_history_size = trade_history_size
        self.min_trades_for_kelly = min_trades_for_kelly
        self.max_position_percentage = max_position_percentage
        self.kelly_multiplier = kelly_multiplier
        
        # Trade history storage (rolling window)
        self.trade_history: deque = deque(maxlen=trade_history_size)
        self.trade_history_by_instrument: Dict[str, deque] = {}
        
        # Current metrics
        self.current_metrics: Optional[KellyMetrics] = None
        self.instrument_metrics: Dict[str, KellyMetrics] = {}
        
        # Account information
        self.account_equity = 50000.0  # Default starting equity
        self.current_risk_per_trade = 0.01  # 1% default risk
        
        # Performance tracking
        self.calculation_stats = {
            'total_calculations': 0,
            'last_calculation': None,
            'avg_calculation_time_ms': 0.0
        }
    
    async def add_trade(self, trade: TradeRecord):
        """Add a completed trade to the history"""
        try:
            # Add to main history
            self.trade_history.append(trade)
            
            # Add to instrument-specific history
            if trade.instrument not in self.trade_history_by_instrument:
                self.trade_history_by_instrument[trade.instrument] = deque(maxlen=self.trade_history_size)
            
            self.trade_history_by_instrument[trade.instrument].append(trade)
            
            # Recalculate metrics
            await self._recalculate_metrics()
            
            self.logger.debug(f"Added trade: {trade.instrument} PnL: ${trade.pnl:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error adding trade: {e}")
    
    async def get_position_size(self, 
                              instrument: str,
                              entry_price: float,
                              stop_loss_price: float,
                              signal_strength: float = 1.0,
                              use_instrument_specific: bool = True) -> Dict[str, float]:
        """
        Calculate optimal position size using Kelly Criterion
        
        Args:
            instrument: Trading instrument
            entry_price: Proposed entry price
            stop_loss_price: Stop loss price
            signal_strength: Signal confidence (0.0 to 1.0)
            use_instrument_specific: Use instrument-specific metrics if available
            
        Returns:
            Dictionary with position sizing recommendations
        """
        try:
            start_time = datetime.now()
            
            # Get relevant metrics
            metrics = self._get_relevant_metrics(instrument, use_instrument_specific)
            
            if not metrics:
                # Use default conservative sizing
                return self._get_default_sizing(entry_price, stop_loss_price)
            
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss_price)
            if risk_per_share <= 0:
                self.logger.warning("Invalid stop loss price - no risk per share")
                return self._get_default_sizing(entry_price, stop_loss_price)
            
            # Base Kelly size
            kelly_size = self.account_equity * metrics.half_kelly_percentage
            
            # Adjust for signal strength
            adjusted_kelly_size = kelly_size * signal_strength
            
            # Convert to position size (number of shares/contracts)
            position_size = adjusted_kelly_size / risk_per_share
            
            # Apply maximum position limits
            max_position_value = self.account_equity * self.max_position_percentage
            max_position_size = max_position_value / entry_price
            
            final_position_size = min(position_size, max_position_size)
            
            # Calculate dollar amounts
            position_value = final_position_size * entry_price
            risk_amount = final_position_size * risk_per_share
            risk_percentage = (risk_amount / self.account_equity) * 100
            
            # Update stats
            calc_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_calculation_stats(calc_time)
            
            result = {
                'position_size': final_position_size,
                'position_value': position_value,
                'risk_amount': risk_amount,
                'risk_percentage': risk_percentage,
                'kelly_percentage': metrics.kelly_percentage,
                'half_kelly_percentage': metrics.half_kelly_percentage,
                'win_rate': metrics.win_rate,
                'payoff_ratio': metrics.payoff_ratio,
                'confidence_level': metrics.confidence_level,
                'signal_strength': signal_strength,
                'max_position_limit': max_position_value,
                'calculation_source': 'instrument_specific' if use_instrument_specific and instrument in self.instrument_metrics else 'general'
            }
            
            self.logger.info(f"Kelly position size for {instrument}: {final_position_size:.2f} units, "
                           f"Risk: ${risk_amount:.2f} ({risk_percentage:.2f}%)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return self._get_default_sizing(entry_price, stop_loss_price)
    
    def _get_relevant_metrics(self, instrument: str, use_instrument_specific: bool) -> Optional[KellyMetrics]:
        """Get the most relevant metrics for position sizing"""
        
        # Try instrument-specific metrics first
        if use_instrument_specific and instrument in self.instrument_metrics:
            instrument_metrics = self.instrument_metrics[instrument]
            if instrument_metrics.sample_size >= self.min_trades_for_kelly:
                return instrument_metrics
        
        # Fall back to general metrics
        if self.current_metrics and self.current_metrics.sample_size >= self.min_trades_for_kelly:
            return self.current_metrics
        
        return None
    
    def _get_default_sizing(self, entry_price: float, stop_loss_price: float) -> Dict[str, float]:
        """Get conservative default position sizing when Kelly is not available"""
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share <= 0:
            return {'error': 'Invalid stop loss price'}
        
        # Use fixed 1% risk
        risk_amount = self.account_equity * self.current_risk_per_trade
        position_size = risk_amount / risk_per_share
        
        # Apply maximum position limits
        max_position_value = self.account_equity * self.max_position_percentage
        max_position_size = max_position_value / entry_price
        
        final_position_size = min(position_size, max_position_size)
        position_value = final_position_size * entry_price
        
        return {
            'position_size': final_position_size,
            'position_value': position_value,
            'risk_amount': risk_amount,
            'risk_percentage': self.current_risk_per_trade * 100,
            'kelly_percentage': 0.0,
            'half_kelly_percentage': 0.0,
            'win_rate': 0.0,
            'payoff_ratio': 0.0,
            'confidence_level': 0.0,
            'signal_strength': 1.0,
            'max_position_limit': max_position_value,
            'calculation_source': 'default_fixed_risk'
        }
    
    async def _recalculate_metrics(self):
        """Recalculate Kelly metrics for all trades and by instrument"""
        try:
            # Calculate general metrics
            if len(self.trade_history) >= self.min_trades_for_kelly:
                self.current_metrics = self._calculate_kelly_metrics(list(self.trade_history))
            
            # Calculate instrument-specific metrics
            for instrument, trades in self.trade_history_by_instrument.items():
                if len(trades) >= self.min_trades_for_kelly:
                    self.instrument_metrics[instrument] = self._calculate_kelly_metrics(list(trades))
            
        except Exception as e:
            self.logger.error(f"Error recalculating metrics: {e}")
    
    def _calculate_kelly_metrics(self, trades: List[TradeRecord]) -> KellyMetrics:
        """Calculate Kelly Criterion metrics from trade list"""
        if not trades:
            return self._get_empty_metrics()
        
        # Separate wins and losses
        wins = [t.pnl for t in trades if t.win]
        losses = [abs(t.pnl) for t in trades if not t.win]
        
        # Basic statistics
        total_trades = len(trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        loss_rate = losing_trades / total_trades if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = statistics.mean(wins) if wins else 0
        avg_loss = statistics.mean(losses) if losses else 0
        
        # Payoff ratio (average win / average loss)
        payoff_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Kelly percentage calculation
        # Kelly = (bp - q) / b
        # Where: b = payoff ratio, p = win rate, q = loss rate
        if payoff_ratio > 0 and loss_rate > 0:
            kelly_percentage = (payoff_ratio * win_rate - loss_rate) / payoff_ratio
        else:
            kelly_percentage = 0
        
        # Ensure Kelly is not negative or too large
        kelly_percentage = max(0, min(kelly_percentage, 0.25))  # Cap at 25%
        
        # Half-Kelly for safety
        half_kelly_percentage = kelly_percentage * self.kelly_multiplier
        
        # Confidence level based on sample size and consistency
        confidence_level = self._calculate_confidence_level(trades, total_trades)
        
        # Recommended size (percentage of equity)
        recommended_size = half_kelly_percentage * self.account_equity
        
        return KellyMetrics(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            payoff_ratio=payoff_ratio,
            kelly_percentage=kelly_percentage,
            half_kelly_percentage=half_kelly_percentage,
            recommended_size=recommended_size,
            confidence_level=confidence_level,
            sample_size=total_trades,
            last_updated=datetime.now()
        )
    
    def _calculate_confidence_level(self, trades: List[TradeRecord], sample_size: int) -> float:
        """Calculate confidence level in Kelly metrics"""
        
        # Base confidence on sample size
        if sample_size < self.min_trades_for_kelly:
            return 0.0
        elif sample_size < 50:
            base_confidence = 0.6
        elif sample_size < 100:
            base_confidence = 0.8
        else:
            base_confidence = 0.9
        
        # Adjust for recent performance consistency
        if sample_size >= 10:
            recent_trades = trades[-10:]
            recent_win_rate = sum(1 for t in recent_trades if t.win) / len(recent_trades)
            overall_win_rate = sum(1 for t in trades if t.win) / len(trades)
            
            # Penalize if recent performance differs significantly from overall
            consistency_factor = 1.0 - abs(recent_win_rate - overall_win_rate)
            base_confidence *= consistency_factor
        
        return max(0.0, min(1.0, base_confidence))
    
    def _get_empty_metrics(self) -> KellyMetrics:
        """Get empty metrics object"""
        return KellyMetrics(
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            payoff_ratio=0.0,
            kelly_percentage=0.0,
            half_kelly_percentage=0.0,
            recommended_size=0.0,
            confidence_level=0.0,
            sample_size=0,
            last_updated=datetime.now()
        )
    
    def _update_calculation_stats(self, calc_time_ms: float):
        """Update calculation performance statistics"""
        self.calculation_stats['total_calculations'] += 1
        self.calculation_stats['last_calculation'] = datetime.now()
        
        # Running average of calculation time
        total_calcs = self.calculation_stats['total_calculations']
        current_avg = self.calculation_stats['avg_calculation_time_ms']
        new_avg = ((current_avg * (total_calcs - 1)) + calc_time_ms) / total_calcs
        self.calculation_stats['avg_calculation_time_ms'] = new_avg
    
    async def update_account_equity(self, new_equity: float):
        """Update account equity for position sizing calculations"""
        if new_equity > 0:
            self.account_equity = new_equity
            self.logger.info(f"Updated account equity to ${new_equity:,.2f}")
            
            # Recalculate metrics to update recommended sizes
            await self._recalculate_metrics()
    
    def get_current_metrics(self, instrument: str = None) -> Optional[Dict]:
        """Get current Kelly metrics"""
        if instrument and instrument in self.instrument_metrics:
            return asdict(self.instrument_metrics[instrument])
        elif self.current_metrics:
            return asdict(self.current_metrics)
        return None
    
    def get_trade_history_summary(self) -> Dict:
        """Get summary of trade history"""
        total_trades = len(self.trade_history)
        if total_trades == 0:
            return {'total_trades': 0}
        
        wins = sum(1 for t in self.trade_history if t.win)
        total_pnl = sum(t.pnl for t in self.trade_history)
        
        return {
            'total_trades': total_trades,
            'winning_trades': wins,
            'losing_trades': total_trades - wins,
            'win_rate': wins / total_trades,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': total_pnl / total_trades,
            'instruments_traded': list(self.trade_history_by_instrument.keys()),
            'date_range': {
                'first_trade': min(t.timestamp for t in self.trade_history).isoformat(),
                'last_trade': max(t.timestamp for t in self.trade_history).isoformat()
            } if total_trades > 0 else None
        }
    
    async def export_trade_history(self, file_path: str):
        """Export trade history to JSON file"""
        try:
            history_data = {
                'export_timestamp': datetime.now().isoformat(),
                'account_equity': self.account_equity,
                'current_metrics': asdict(self.current_metrics) if self.current_metrics else None,
                'instrument_metrics': {k: asdict(v) for k, v in self.instrument_metrics.items()},
                'trade_history': [asdict(trade) for trade in self.trade_history],
                'summary': self.get_trade_history_summary()
            }
            
            with open(file_path, 'w') as f:
                json.dump(history_data, f, indent=2, default=str)
            
            self.logger.info(f"Trade history exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting trade history: {e}")
    
    async def import_trade_history(self, file_path: str):
        """Import trade history from JSON file"""
        try:
            with open(file_path, 'r') as f:
                history_data = json.load(f)
            
            # Import trades
            for trade_data in history_data.get('trade_history', []):
                trade_data['timestamp'] = datetime.fromisoformat(trade_data['timestamp'])
                trade = TradeRecord(**trade_data)
                await self.add_trade(trade)
            
            # Update account equity if provided
            if 'account_equity' in history_data:
                await self.update_account_equity(history_data['account_equity'])
            
            self.logger.info(f"Trade history imported from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error importing trade history: {e}")
    
    def is_healthy(self) -> bool:
        """Check if Kelly engine is healthy"""
        return len(self.trade_history) >= 0  # Always healthy, just may not have enough data
    
    def get_statistics(self) -> Dict:
        """Get Kelly engine statistics"""
        return {
            **self.calculation_stats,
            'trade_history_size': len(self.trade_history),
            'instruments_tracked': len(self.trade_history_by_instrument),
            'current_equity': self.account_equity,
            'has_sufficient_data': len(self.trade_history) >= self.min_trades_for_kelly
        }
