"""
Kelly Criterion engine for dynamic position sizing based on historical performance.

This module implements the Kelly Criterion formula with enhancements for 
trading applications including rolling win rate calculation and risk adjustments.
"""

import logging
from collections import deque
from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timedelta


class KellyEngine:
    """
    Kelly Criterion position sizing engine.
    
    Features:
    - Rolling window win rate calculation (last 100 trades)
    - Fractional Kelly for risk management (half-Kelly default)
    - Dynamic confidence intervals
    - Drawdown-based position reduction
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Trade history for rolling calculations
        self.trade_history = deque(maxlen=config.get('history_length', 100))
        
        # Kelly parameters
        self.base_win_rate = config.get('base_win_rate', 0.5)
        self.kelly_fraction = config.get('kelly_fraction', 0.5)  # Half-Kelly default
        self.min_trades_for_dynamic = config.get('min_trades_for_dynamic', 10)
        
        # Risk management
        self.max_position_pct = config.get('max_position_pct', 0.02)  # 2% max risk
        self.drawdown_reduction_factor = config.get('drawdown_reduction_factor', 0.5)
        
        # Account information
        self.account_balance = config.get('initial_balance', 50000)
        self.current_drawdown = 0.0
        
    def calculate_kelly_fraction(self, atr_value: float, sl_multiplier: float = 1.5, 
                                pt_multiplier: float = 2.0) -> float:
        """
        Calculate Kelly fraction for position sizing.
        
        Args:
            atr_value: Current ATR value for risk calculation
            sl_multiplier: Stop loss ATR multiplier
            pt_multiplier: Profit target ATR multiplier
            
        Returns:
            Kelly fraction (0.0 to 1.0)
        """
        try:
            # Calculate risk/reward ratio (b)
            stop_loss_points = atr_value * sl_multiplier
            profit_target_points = atr_value * pt_multiplier
            b = profit_target_points / stop_loss_points
            
            # Get current win rate (p)
            p = self.get_current_win_rate()
            q = 1 - p
            
            # Kelly formula: f = (bp - q) / b
            kelly_f = (b * p - q) / b
            
            # Apply fractional Kelly
            fractional_kelly = kelly_f * self.kelly_fraction
            
            # Apply risk management constraints
            adjusted_kelly = self._apply_risk_constraints(fractional_kelly)
            
            self.logger.debug(f"Kelly calculation: p={p:.3f}, b={b:.3f}, "
                            f"kelly_f={kelly_f:.3f}, adjusted={adjusted_kelly:.3f}")
            
            return max(0.0, adjusted_kelly)
            
        except Exception as e:
            self.logger.error(f"Kelly fraction calculation error: {e}")
            return 0.0
            
    def get_current_win_rate(self) -> float:
        """
        Get current win rate based on trade history.
        
        Returns:
            Win rate between 0.0 and 1.0
        """
        if len(self.trade_history) < self.min_trades_for_dynamic:
            # Use base win rate if insufficient history
            return self.base_win_rate
            
        # Calculate rolling win rate
        wins = sum(1 for trade in self.trade_history if trade['outcome'] == 'win')
        total_trades = len(self.trade_history)
        
        # Apply smoothing with base win rate
        actual_win_rate = wins / total_trades
        weight = min(total_trades / 100, 1.0)  # Full weight at 100 trades
        
        smoothed_win_rate = (actual_win_rate * weight) + (self.base_win_rate * (1 - weight))
        
        return smoothed_win_rate
        
    def calculate_position_size(self, kelly_fraction: float, 
                              tick_value: float = 12.50) -> int:
        """
        Calculate actual position size in contracts.
        
        Args:
            kelly_fraction: Kelly fraction from calculate_kelly_fraction()
            tick_value: Dollar value per tick/point
            
        Returns:
            Number of contracts to trade
        """
        try:
            if kelly_fraction <= 0:
                return 0
                
            # Calculate dollar risk amount
            risk_amount = self.account_balance * kelly_fraction
            
            # Apply maximum position limit
            max_risk = self.account_balance * self.max_position_pct
            risk_amount = min(risk_amount, max_risk)
            
            # Calculate contracts based on tick value
            # This is simplified - actual calculation depends on stop loss distance
            contracts = int(risk_amount / (tick_value * 10))  # Assuming 10 tick risk
            
            return max(1, contracts) if kelly_fraction > 0 else 0
            
        except Exception as e:
            self.logger.error(f"Position size calculation error: {e}")
            return 0
            
    def log_trade_outcome(self, outcome: str, profit_loss: float, 
                         entry_price: float, exit_price: float, 
                         position_size: int, metadata: Dict[str, Any] = None):
        """
        Log trade outcome for Kelly calculation updates.
        
        Args:
            outcome: 'win' or 'loss'
            profit_loss: P&L in dollars
            entry_price: Entry price
            exit_price: Exit price
            position_size: Number of contracts
            metadata: Additional trade information
        """
        try:
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'outcome': outcome,
                'profit_loss': profit_loss,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position_size': position_size,
                'metadata': metadata or {}
            }
            
            self.trade_history.append(trade_record)
            
            # Update account balance
            self.account_balance += profit_loss
            
            # Update drawdown
            self._update_drawdown(profit_loss)
            
            self.logger.info(f"Trade logged: {outcome}, P&L: {profit_loss:.2f}")
            
        except Exception as e:
            self.logger.error(f"Trade logging error: {e}")
            
    def _apply_risk_constraints(self, kelly_fraction: float) -> float:
        """Apply risk management constraints to Kelly fraction."""
        
        # Reduce position during drawdown periods
        if self.current_drawdown > 0.05:  # 5% drawdown
            kelly_fraction *= self.drawdown_reduction_factor
            
        # Apply maximum position constraint
        kelly_fraction = min(kelly_fraction, self.max_position_pct)
        
        # Ensure non-negative
        kelly_fraction = max(0.0, kelly_fraction)
        
        return kelly_fraction
        
    def _update_drawdown(self, profit_loss: float):
        """Update current drawdown tracking."""
        if profit_loss < 0:
            self.current_drawdown += abs(profit_loss) / self.account_balance
        else:
            # Reduce drawdown on profitable trades
            self.current_drawdown = max(0.0, self.current_drawdown - 
                                      (profit_loss / self.account_balance))
                                      
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current Kelly engine statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            total_trades = len(self.trade_history)
            
            if total_trades == 0:
                return {
                    'total_trades': 0,
                    'win_rate': self.base_win_rate,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'profit_factor': 0.0,
                    'account_balance': self.account_balance,
                    'current_drawdown': self.current_drawdown
                }
                
            # Calculate statistics
            wins = [t for t in self.trade_history if t['outcome'] == 'win']
            losses = [t for t in self.trade_history if t['outcome'] == 'loss']
            
            win_rate = len(wins) / total_trades
            avg_win = sum(t['profit_loss'] for t in wins) / len(wins) if wins else 0
            avg_loss = sum(abs(t['profit_loss']) for t in losses) / len(losses) if losses else 0
            
            gross_profit = sum(t['profit_loss'] for t in wins)
            gross_loss = sum(abs(t['profit_loss']) for t in losses)
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'wins': len(wins),
                'losses': len(losses),
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'account_balance': self.account_balance,
                'current_drawdown': self.current_drawdown,
                'kelly_fraction_used': self.kelly_fraction
            }
            
        except Exception as e:
            self.logger.error(f"Stats calculation error: {e}")
            return {}
            
    def reset_history(self):
        """Reset trade history (use carefully)."""
        self.trade_history.clear()
        self.current_drawdown = 0.0
        self.logger.info("Kelly engine history reset")
        
    def export_history(self, filename: str):
        """Export trade history to JSON file."""
        try:
            history_data = {
                'trades': list(self.trade_history),
                'stats': self.get_stats(),
                'config': self.config,
                'export_time': datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(history_data, f, indent=2)
                
            self.logger.info(f"Trade history exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"History export error: {e}")
            
    def import_history(self, filename: str):
        """Import trade history from JSON file."""
        try:
            with open(filename, 'r') as f:
                history_data = json.load(f)
                
            # Load trades
            self.trade_history.clear()
            for trade in history_data.get('trades', []):
                self.trade_history.append(trade)
                
            # Recalculate account balance and drawdown
            self._recalculate_account_state()
            
            self.logger.info(f"Trade history imported from {filename}")
            
        except Exception as e:
            self.logger.error(f"History import error: {e}")
            
    def _recalculate_account_state(self):
        """Recalculate account balance and drawdown from trade history."""
        self.account_balance = self.config.get('initial_balance', 50000)
        peak_balance = self.account_balance
        max_drawdown = 0.0
        
        for trade in self.trade_history:
            self.account_balance += trade['profit_loss']
            
            if self.account_balance > peak_balance:
                peak_balance = self.account_balance
            else:
                current_dd = (peak_balance - self.account_balance) / peak_balance
                max_drawdown = max(max_drawdown, current_dd)
                
        self.current_drawdown = (peak_balance - self.account_balance) / peak_balance
        
    def should_stop_trading(self) -> bool:
        """
        Determine if trading should be stopped based on performance.
        
        Returns:
            True if trading should be stopped
        """
        # Stop if win rate drops too low with sufficient sample size
        if (len(self.trade_history) >= 50 and 
            self.get_current_win_rate() < 0.35):
            return True
            
        # Stop if drawdown exceeds threshold
        if self.current_drawdown > 0.15:  # 15% drawdown
            return True
            
        # Stop if account balance drops too low
        if self.account_balance < self.config.get('min_balance', 25000):
            return True
            
        return False
