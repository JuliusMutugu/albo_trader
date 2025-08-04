"""
Apex Prop Firm Compliance Monitor - Real-time rule enforcement and violation prevention.

This module monitors Apex prop firm rules including daily drawdown limits,
position sizes, and trading cycle requirements to prevent account violations.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from enum import Enum


class AccountStatus(Enum):
    """Account status enumeration."""
    ACTIVE = "active"
    WARNING = "warning"
    VIOLATION = "violation"
    SUSPENDED = "suspended"


class ViolationType(Enum):
    """Violation type enumeration."""
    DAILY_DRAWDOWN = "daily_drawdown"
    TRAILING_DRAWDOWN = "trailing_drawdown"
    POSITION_SIZE = "position_size"
    CONSISTENCY_RULE = "consistency_rule"
    PROFIT_TARGET = "profit_target"


class ApexMonitor:
    """
    Apex Prop Firm compliance monitoring system.
    
    Features:
    - Real-time drawdown monitoring
    - Position size validation
    - Consistency rule enforcement
    - Profit target tracking
    - Violation prevention alerts
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Account configuration
        self.account_size = config.get('account_size', 50000)
        self.max_daily_loss = config.get('max_daily_loss', 2000)  # $2,000
        self.max_trailing_loss = config.get('max_trailing_loss', 3000)  # $3,000
        self.profit_target = config.get('profit_target', 3000)  # $3,000
        
        # Position limits
        self.max_contracts = config.get('max_contracts', 10)
        self.max_position_value = config.get('max_position_value', 50000)
        
        # Consistency rule (largest win can't exceed X% of total profit)
        self.consistency_threshold = config.get('consistency_threshold', 0.4)  # 40%
        
        # Current account state
        self.current_balance = self.account_size
        self.daily_pnl = 0.0
        self.peak_balance = self.account_size
        self.current_drawdown = 0.0
        
        # Trading day tracking
        self.last_trading_day = None
        self.daily_trades = []
        self.all_time_trades = []
        
        # Violation tracking
        self.violations = []
        self.warnings = []
        self.account_status = AccountStatus.ACTIVE
        
    async def update_account_status(self):
        """Update account status with latest trading data."""
        try:
            # Check if new trading day
            today = date.today()
            if self.last_trading_day != today:
                self._start_new_trading_day()
                
            # Update drawdown calculations
            self._update_drawdown()
            
            # Check for violations
            await self._check_violations()
            
            # Update account status
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Account status update error: {e}")
            
    def _start_new_trading_day(self):
        """Initialize new trading day."""
        try:
            today = date.today()
            
            self.logger.info(f"Starting new trading day: {today}")
            
            # Reset daily metrics
            self.daily_pnl = 0.0
            self.daily_trades = []
            self.last_trading_day = today
            
            # Clear daily warnings
            self.warnings = [w for w in self.warnings if w.get('type') != 'daily']
            
        except Exception as e:
            self.logger.error(f"New trading day initialization error: {e}")
            
    def add_trade(self, entry_price: float, exit_price: float, 
                  position_size: int, direction: str, 
                  timestamp: datetime = None) -> bool:
        """
        Add completed trade and update account metrics.
        
        Args:
            entry_price: Trade entry price
            exit_price: Trade exit price
            position_size: Number of contracts
            direction: 'long' or 'short'
            timestamp: Trade timestamp (default: now)
            
        Returns:
            True if trade was valid and added
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
                
            # Calculate P&L (simplified - actual calculation depends on instrument)
            if direction.lower() == 'long':
                pnl = (exit_price - entry_price) * position_size * 12.50  # $12.50 per point for ES
            else:  # short
                pnl = (entry_price - exit_price) * position_size * 12.50
                
            trade_record = {
                'timestamp': timestamp,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position_size': position_size,
                'direction': direction,
                'pnl': pnl,
                'trade_date': timestamp.date()
            }
            
            # Add to daily and all-time records
            self.daily_trades.append(trade_record)
            self.all_time_trades.append(trade_record)
            
            # Update account metrics
            self.current_balance += pnl
            self.daily_pnl += pnl
            
            # Update peak balance if necessary
            if self.current_balance > self.peak_balance:
                self.peak_balance = self.current_balance
                
            self.logger.info(f"Trade added: P&L ${pnl:.2f}, Daily P&L: ${self.daily_pnl:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Trade addition error: {e}")
            return False
            
    def can_open_position(self, position_size: int, 
                         estimated_value: float = None) -> bool:
        """
        Check if position can be opened without violating rules.
        
        Args:
            position_size: Number of contracts to trade
            estimated_value: Estimated position value (optional)
            
        Returns:
            True if position is allowed
        """
        try:
            # Check account status
            if self.account_status in [AccountStatus.VIOLATION, AccountStatus.SUSPENDED]:
                self.logger.warning("Position blocked - account has violations")
                return False
                
            # Check position size limits
            if position_size > self.max_contracts:
                self.logger.warning(f"Position size {position_size} exceeds max {self.max_contracts}")
                return False
                
            # Check position value if provided
            if estimated_value and estimated_value > self.max_position_value:
                self.logger.warning(f"Position value ${estimated_value} exceeds max ${self.max_position_value}")
                return False
                
            # Check if close to daily loss limit
            if self.daily_pnl < -(self.max_daily_loss * 0.8):  # 80% of limit
                self.logger.warning("Position blocked - approaching daily loss limit")
                return False
                
            # Check trailing drawdown
            if self.current_drawdown > (self.max_trailing_loss * 0.8):  # 80% of limit
                self.logger.warning("Position blocked - approaching trailing drawdown limit")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Position validation error: {e}")
            return False
            
    def get_max_position_size(self) -> int:
        """
        Get maximum allowed position size based on current account state.
        
        Returns:
            Maximum contracts allowed
        """
        try:
            # Start with configured maximum
            max_size = self.max_contracts
            
            # Reduce if approaching daily loss limit
            daily_loss_pct = abs(self.daily_pnl) / self.max_daily_loss
            if daily_loss_pct > 0.5:
                max_size = max(1, int(max_size * (1 - daily_loss_pct)))
                
            # Reduce if high drawdown
            drawdown_pct = self.current_drawdown / self.max_trailing_loss
            if drawdown_pct > 0.5:
                max_size = max(1, int(max_size * (1 - drawdown_pct)))
                
            return max_size
            
        except Exception as e:
            self.logger.error(f"Max position size calculation error: {e}")
            return 1  # Conservative fallback
            
    def is_violation_imminent(self) -> bool:
        """
        Check if violation is imminent (within 90% of limits).
        
        Returns:
            True if violation is imminent
        """
        try:
            # Daily loss approaching limit
            if abs(self.daily_pnl) > (self.max_daily_loss * 0.9):
                return True
                
            # Trailing drawdown approaching limit
            if self.current_drawdown > (self.max_trailing_loss * 0.9):
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Violation check error: {e}")
            return True  # Conservative - assume violation imminent on error
            
    def _update_drawdown(self):
        """Update current drawdown calculations."""
        try:
            # Update peak balance
            if self.current_balance > self.peak_balance:
                self.peak_balance = self.current_balance
                
            # Calculate current drawdown
            self.current_drawdown = self.peak_balance - self.current_balance
            
        except Exception as e:
            self.logger.error(f"Drawdown update error: {e}")
            
    async def _check_violations(self):
        """Check for rule violations and add to violations list."""
        try:
            current_time = datetime.now()
            
            # Check daily loss limit
            if abs(self.daily_pnl) > self.max_daily_loss:
                violation = {
                    'type': ViolationType.DAILY_DRAWDOWN,
                    'timestamp': current_time,
                    'description': f"Daily loss ${abs(self.daily_pnl):.2f} exceeds limit ${self.max_daily_loss}",
                    'severity': 'critical'
                }
                self.violations.append(violation)
                self.logger.critical(f"VIOLATION: {violation['description']}")
                
            # Check trailing drawdown
            elif self.current_drawdown > self.max_trailing_loss:
                violation = {
                    'type': ViolationType.TRAILING_DRAWDOWN,
                    'timestamp': current_time,
                    'description': f"Trailing drawdown ${self.current_drawdown:.2f} exceeds limit ${self.max_trailing_loss}",
                    'severity': 'critical'
                }
                self.violations.append(violation)
                self.logger.critical(f"VIOLATION: {violation['description']}")
                
            # Check consistency rule
            await self._check_consistency_rule()
            
            # Add warnings for approaching limits
            await self._check_warnings()
            
        except Exception as e:
            self.logger.error(f"Violation check error: {e}")
            
    async def _check_consistency_rule(self):
        """Check consistency rule (largest win can't exceed threshold of total profit)."""
        try:
            if len(self.all_time_trades) < 5:  # Need minimum trades
                return
                
            # Calculate total profit and largest winning trade
            profitable_trades = [t for t in self.all_time_trades if t['pnl'] > 0]
            
            if not profitable_trades:
                return
                
            total_profit = sum(t['pnl'] for t in profitable_trades)
            largest_win = max(t['pnl'] for t in profitable_trades)
            
            if total_profit > 0:
                largest_win_pct = largest_win / total_profit
                
                if largest_win_pct > self.consistency_threshold:
                    violation = {
                        'type': ViolationType.CONSISTENCY_RULE,
                        'timestamp': datetime.now(),
                        'description': f"Largest win {largest_win_pct:.1%} exceeds consistency threshold {self.consistency_threshold:.1%}",
                        'severity': 'warning'
                    }
                    self.violations.append(violation)
                    self.logger.warning(f"CONSISTENCY VIOLATION: {violation['description']}")
                    
        except Exception as e:
            self.logger.error(f"Consistency rule check error: {e}")
            
    async def _check_warnings(self):
        """Check for approaching violations and issue warnings."""
        try:
            current_time = datetime.now()
            
            # Daily loss warning (80% of limit)
            if abs(self.daily_pnl) > (self.max_daily_loss * 0.8):
                warning = {
                    'type': 'daily_loss_warning',
                    'timestamp': current_time,
                    'description': f"Daily loss ${abs(self.daily_pnl):.2f} approaching limit ${self.max_daily_loss}",
                    'urgency': 'high'
                }
                self.warnings.append(warning)
                
            # Trailing drawdown warning (80% of limit)
            if self.current_drawdown > (self.max_trailing_loss * 0.8):
                warning = {
                    'type': 'trailing_drawdown_warning',
                    'timestamp': current_time,
                    'description': f"Trailing drawdown ${self.current_drawdown:.2f} approaching limit ${self.max_trailing_loss}",
                    'urgency': 'high'
                }
                self.warnings.append(warning)
                
        except Exception as e:
            self.logger.error(f"Warning check error: {e}")
            
    def _update_status(self):
        """Update overall account status based on violations and warnings."""
        try:
            # Check for critical violations
            critical_violations = [v for v in self.violations 
                                 if v.get('severity') == 'critical' and
                                 v['timestamp'].date() == date.today()]
                                 
            if critical_violations:
                self.account_status = AccountStatus.VIOLATION
                return
                
            # Check for high urgency warnings
            high_warnings = [w for w in self.warnings 
                           if w.get('urgency') == 'high' and
                           w['timestamp'].date() == date.today()]
                           
            if high_warnings:
                self.account_status = AccountStatus.WARNING
                return
                
            # Default to active
            self.account_status = AccountStatus.ACTIVE
            
        except Exception as e:
            self.logger.error(f"Status update error: {e}")
            
    def has_violations(self) -> bool:
        """Check if account has active violations."""
        return self.account_status == AccountStatus.VIOLATION
        
    def can_enable_trading(self) -> bool:
        """Check if trading can be enabled."""
        return self.account_status in [AccountStatus.ACTIVE, AccountStatus.WARNING]
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive account status.
        
        Returns:
            Dictionary with account metrics and status
        """
        try:
            # Calculate percentages of limits used
            daily_loss_pct = abs(self.daily_pnl) / self.max_daily_loss
            trailing_dd_pct = self.current_drawdown / self.max_trailing_loss
            
            # Calculate profit progress
            profit_progress = (self.current_balance - self.account_size) / self.profit_target
            
            return {
                'account_status': self.account_status.value,
                'current_balance': self.current_balance,
                'daily_pnl': self.daily_pnl,
                'current_drawdown': self.current_drawdown,
                'peak_balance': self.peak_balance,
                'daily_loss_pct': daily_loss_pct,
                'trailing_dd_pct': trailing_dd_pct,
                'profit_progress': profit_progress,
                'max_contracts': self.get_max_position_size(),
                'daily_trades_count': len(self.daily_trades),
                'total_trades_count': len(self.all_time_trades),
                'violations_count': len(self.violations),
                'warnings_count': len(self.warnings),
                'can_trade': self.can_enable_trading(),
                'violation_imminent': self.is_violation_imminent(),
                'last_trading_day': self.last_trading_day.isoformat() if self.last_trading_day else None
            }
            
        except Exception as e:
            self.logger.error(f"Status calculation error: {e}")
            return {}
            
    def get_detailed_report(self) -> Dict[str, Any]:
        """Get detailed account report with trade history and analysis."""
        try:
            status = self.get_status()
            
            # Add detailed information
            status.update({
                'account_config': {
                    'account_size': self.account_size,
                    'max_daily_loss': self.max_daily_loss,
                    'max_trailing_loss': self.max_trailing_loss,
                    'profit_target': self.profit_target,
                    'max_contracts': self.max_contracts,
                    'consistency_threshold': self.consistency_threshold
                },
                'recent_trades': self.daily_trades[-10:],  # Last 10 trades
                'active_violations': [v for v in self.violations if v['timestamp'].date() == date.today()],
                'active_warnings': [w for w in self.warnings if w['timestamp'].date() == date.today()],
                'trading_metrics': self._calculate_trading_metrics()
            })
            
            return status
            
        except Exception as e:
            self.logger.error(f"Detailed report error: {e}")
            return {}
            
    def _calculate_trading_metrics(self) -> Dict[str, Any]:
        """Calculate trading performance metrics."""
        try:
            if not self.all_time_trades:
                return {}
                
            profitable_trades = [t for t in self.all_time_trades if t['pnl'] > 0]
            losing_trades = [t for t in self.all_time_trades if t['pnl'] < 0]
            
            win_rate = len(profitable_trades) / len(self.all_time_trades)
            avg_win = sum(t['pnl'] for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0
            avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            gross_profit = sum(t['pnl'] for t in profitable_trades)
            gross_loss = abs(sum(t['pnl'] for t in losing_trades))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            return {
                'total_trades': len(self.all_time_trades),
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'largest_win': max((t['pnl'] for t in profitable_trades), default=0),
                'largest_loss': min((t['pnl'] for t in losing_trades), default=0)
            }
            
        except Exception as e:
            self.logger.error(f"Trading metrics calculation error: {e}")
            return {}
