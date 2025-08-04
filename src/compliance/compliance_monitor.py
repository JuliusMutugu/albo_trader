"""
Compliance Monitor - Apex Prop Firm Rule Enforcement
Multi-layer protection with hard limits, warnings, and predictive alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

class ComplianceLevel(Enum):
    """Compliance alert levels"""
    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"
    VIOLATION = "violation"

class ViolationType(Enum):
    """Types of rule violations"""
    MAX_LOSS = "max_loss"
    DAILY_LOSS = "daily_loss"
    TRAILING_STOP = "trailing_stop"
    POSITION_SIZE = "position_size"
    TRADING_HOURS = "trading_hours"
    REVENGE_TRADING = "revenge_trading"
    CONSISTENCY = "consistency"

@dataclass
class ComplianceRule:
    """Individual compliance rule definition"""
    rule_id: str
    name: str
    description: str
    violation_type: ViolationType
    hard_limit: float
    warning_threshold: float
    critical_threshold: float
    enabled: bool
    auto_stop: bool  # Whether violation triggers automatic stop

@dataclass
class ComplianceAlert:
    """Compliance alert/violation record"""
    timestamp: datetime
    rule_id: str
    violation_type: ViolationType
    level: ComplianceLevel
    current_value: float
    threshold_value: float
    message: str
    action_taken: str
    resolved: bool

@dataclass
class AccountMetrics:
    """Current account metrics for compliance checking"""
    starting_balance: float
    current_balance: float
    daily_pnl: float
    total_pnl: float
    max_drawdown: float
    peak_balance: float
    open_positions_value: float
    daily_trades: int
    consecutive_losses: int
    last_trade_time: Optional[datetime]

class ComplianceMonitor:
    """
    Apex Prop Firm compliance monitoring and enforcement
    """
    
    def __init__(self, 
                 account_size: float = 50000.0,
                 max_loss_percentage: float = 0.08,  # 8% max loss
                 daily_loss_percentage: float = 0.05,  # 5% daily loss limit
                 trailing_stop_percentage: float = 0.05):  # 5% trailing stop
        
        self.logger = logging.getLogger(__name__)
        
        # Account configuration
        self.account_size = account_size
        self.max_loss_percentage = max_loss_percentage
        self.daily_loss_percentage = daily_loss_percentage
        self.trailing_stop_percentage = trailing_stop_percentage
        
        # Compliance rules
        self.rules = self._initialize_rules()
        
        # Current metrics
        self.account_metrics = AccountMetrics(
            starting_balance=account_size,
            current_balance=account_size,
            daily_pnl=0.0,
            total_pnl=0.0,
            max_drawdown=0.0,
            peak_balance=account_size,
            open_positions_value=0.0,
            daily_trades=0,
            consecutive_losses=0,
            last_trade_time=None
        )
        
        # Alert history
        self.alerts: List[ComplianceAlert] = []
        self.daily_reset_time = dt_time(17, 0)  # 5 PM EST reset
        self.last_daily_reset = datetime.now().date()
        
        # Trading state
        self.trading_enabled = True
        self.emergency_stop_triggered = False
        self.violation_count = 0
        
        # Performance tracking
        self.compliance_stats = {
            'total_checks': 0,
            'warnings_issued': 0,
            'violations_recorded': 0,
            'auto_stops_triggered': 0,
            'last_check': None
        }
    
    def _initialize_rules(self) -> Dict[str, ComplianceRule]:
        """Initialize Apex prop firm compliance rules"""
        rules = {}
        
        # Maximum Loss Rule (8% of account)
        max_loss_amount = self.account_size * self.max_loss_percentage
        rules['max_loss'] = ComplianceRule(
            rule_id='max_loss',
            name='Maximum Loss Limit',
            description=f'Account cannot lose more than ${max_loss_amount:,.2f} ({self.max_loss_percentage*100}%)',
            violation_type=ViolationType.MAX_LOSS,
            hard_limit=-max_loss_amount,
            warning_threshold=-max_loss_amount * 0.7,  # 70% of limit
            critical_threshold=-max_loss_amount * 0.9,  # 90% of limit
            enabled=True,
            auto_stop=True
        )
        
        # Daily Loss Rule (5% of account)
        daily_loss_amount = self.account_size * self.daily_loss_percentage
        rules['daily_loss'] = ComplianceRule(
            rule_id='daily_loss',
            name='Daily Loss Limit',
            description=f'Daily loss cannot exceed ${daily_loss_amount:,.2f} ({self.daily_loss_percentage*100}%)',
            violation_type=ViolationType.DAILY_LOSS,
            hard_limit=-daily_loss_amount,
            warning_threshold=-daily_loss_amount * 0.7,
            critical_threshold=-daily_loss_amount * 0.9,
            enabled=True,
            auto_stop=True
        )
        
        # Trailing Stop Rule (5% from peak)
        trailing_amount = self.account_size * self.trailing_stop_percentage
        rules['trailing_stop'] = ComplianceRule(
            rule_id='trailing_stop',
            name='Trailing Stop',
            description=f'Account cannot fall more than ${trailing_amount:,.2f} from peak balance',
            violation_type=ViolationType.TRAILING_STOP,
            hard_limit=-trailing_amount,
            warning_threshold=-trailing_amount * 0.7,
            critical_threshold=-trailing_amount * 0.9,
            enabled=True,
            auto_stop=True
        )
        
        # Position Size Rule (2% max risk per trade)
        max_position_risk = self.account_size * 0.02
        rules['position_size'] = ComplianceRule(
            rule_id='position_size',
            name='Maximum Position Risk',
            description=f'Single trade risk cannot exceed ${max_position_risk:,.2f} (2%)',
            violation_type=ViolationType.POSITION_SIZE,
            hard_limit=max_position_risk,
            warning_threshold=max_position_risk * 0.8,
            critical_threshold=max_position_risk * 0.95,
            enabled=True,
            auto_stop=False
        )
        
        # Revenge Trading Rule (max 5 consecutive losses)
        rules['revenge_trading'] = ComplianceRule(
            rule_id='revenge_trading',
            name='Revenge Trading Prevention',
            description='Stop trading after 5 consecutive losses',
            violation_type=ViolationType.REVENGE_TRADING,
            hard_limit=5,
            warning_threshold=3,
            critical_threshold=4,
            enabled=True,
            auto_stop=True
        )
        
        # Daily Trade Limit (prevent overtrading)
        rules['daily_trades'] = ComplianceRule(
            rule_id='daily_trades',
            name='Daily Trade Limit',
            description='Maximum 50 trades per day',
            violation_type=ViolationType.CONSISTENCY,
            hard_limit=50,
            warning_threshold=35,
            critical_threshold=45,
            enabled=True,
            auto_stop=False
        )
        
        return rules
    
    async def check_compliance(self) -> Dict[str, Any]:
        """Run comprehensive compliance check"""
        try:
            self.compliance_stats['total_checks'] += 1
            self.compliance_stats['last_check'] = datetime.now()
            
            # Check for daily reset
            await self._check_daily_reset()
            
            # Check all rules
            compliance_results = {}
            overall_level = ComplianceLevel.SAFE
            
            for rule_id, rule in self.rules.items():
                if rule.enabled:
                    result = await self._check_rule(rule)
                    compliance_results[rule_id] = result
                    
                    # Track highest alert level
                    if result['level'] == ComplianceLevel.VIOLATION:
                        overall_level = ComplianceLevel.VIOLATION
                    elif result['level'] == ComplianceLevel.CRITICAL and overall_level != ComplianceLevel.VIOLATION:
                        overall_level = ComplianceLevel.CRITICAL
                    elif result['level'] == ComplianceLevel.WARNING and overall_level == ComplianceLevel.SAFE:
                        overall_level = ComplianceLevel.WARNING
            
            # Create summary
            summary = {
                'overall_level': overall_level.value,
                'trading_enabled': self.trading_enabled,
                'emergency_stop': self.emergency_stop_triggered,
                'violations_count': self.violation_count,
                'rules_checked': len([r for r in self.rules.values() if r.enabled]),
                'account_metrics': asdict(self.account_metrics),
                'rule_results': compliance_results,
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in compliance check: {e}")
            return {'error': str(e)}
    
    async def _check_daily_reset(self):
        """Check if we need to reset daily metrics"""
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        
        # Reset daily metrics at 5 PM EST (or if date changed)
        if (current_date > self.last_daily_reset or 
            (current_date == self.last_daily_reset and 
             current_time >= self.daily_reset_time and 
             self.account_metrics.daily_trades > 0)):
            
            await self._reset_daily_metrics()
    
    async def _reset_daily_metrics(self):
        """Reset daily trading metrics"""
        self.account_metrics.daily_pnl = 0.0
        self.account_metrics.daily_trades = 0
        self.last_daily_reset = datetime.now().date()
        
        # Reset daily compliance alerts
        for alert in self.alerts:
            if alert.violation_type == ViolationType.DAILY_LOSS and not alert.resolved:
                alert.resolved = True
        
        self.logger.info("Daily metrics reset completed")
    
    async def _check_rule(self, rule: ComplianceRule) -> Dict[str, Any]:
        """Check compliance for a specific rule"""
        try:
            current_value = self._get_current_value_for_rule(rule)
            level = self._determine_compliance_level(rule, current_value)
            
            # Create alert if necessary
            if level in [ComplianceLevel.WARNING, ComplianceLevel.CRITICAL, ComplianceLevel.VIOLATION]:
                await self._create_alert(rule, level, current_value)
            
            # Take action if required
            action_taken = "none"
            if level == ComplianceLevel.VIOLATION and rule.auto_stop:
                action_taken = await self._trigger_emergency_stop(rule)
            
            return {
                'rule_id': rule.rule_id,
                'name': rule.name,
                'level': level,
                'current_value': current_value,
                'hard_limit': rule.hard_limit,
                'warning_threshold': rule.warning_threshold,
                'critical_threshold': rule.critical_threshold,
                'action_taken': action_taken,
                'compliance_percentage': self._calculate_compliance_percentage(rule, current_value)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking rule {rule.rule_id}: {e}")
            return {'error': str(e)}
    
    def _get_current_value_for_rule(self, rule: ComplianceRule) -> float:
        """Get current value relevant to the rule"""
        if rule.violation_type == ViolationType.MAX_LOSS:
            return self.account_metrics.total_pnl
        
        elif rule.violation_type == ViolationType.DAILY_LOSS:
            return self.account_metrics.daily_pnl
        
        elif rule.violation_type == ViolationType.TRAILING_STOP:
            return self.account_metrics.current_balance - self.account_metrics.peak_balance
        
        elif rule.violation_type == ViolationType.POSITION_SIZE:
            return self.account_metrics.open_positions_value
        
        elif rule.violation_type == ViolationType.REVENGE_TRADING:
            return self.account_metrics.consecutive_losses
        
        elif rule.violation_type == ViolationType.CONSISTENCY:
            return self.account_metrics.daily_trades
        
        return 0.0
    
    def _determine_compliance_level(self, rule: ComplianceRule, current_value: float) -> ComplianceLevel:
        """Determine compliance level based on current value"""
        
        # For negative thresholds (losses), check if value is below threshold
        if rule.hard_limit < 0:
            if current_value <= rule.hard_limit:
                return ComplianceLevel.VIOLATION
            elif current_value <= rule.critical_threshold:
                return ComplianceLevel.CRITICAL
            elif current_value <= rule.warning_threshold:
                return ComplianceLevel.WARNING
        
        # For positive thresholds (limits), check if value is above threshold
        else:
            if current_value >= rule.hard_limit:
                return ComplianceLevel.VIOLATION
            elif current_value >= rule.critical_threshold:
                return ComplianceLevel.CRITICAL
            elif current_value >= rule.warning_threshold:
                return ComplianceLevel.WARNING
        
        return ComplianceLevel.SAFE
    
    def _calculate_compliance_percentage(self, rule: ComplianceRule, current_value: float) -> float:
        """Calculate compliance percentage (0-100%)"""
        try:
            if rule.hard_limit == 0:
                return 100.0
            
            if rule.hard_limit < 0:  # Loss limits
                usage_percentage = (current_value / rule.hard_limit) * 100
            else:  # Positive limits
                usage_percentage = (current_value / rule.hard_limit) * 100
            
            return max(0, min(100, usage_percentage))
        except ZeroDivisionError:
            return 0.0
    
    async def _create_alert(self, rule: ComplianceRule, level: ComplianceLevel, current_value: float):
        """Create compliance alert"""
        threshold_value = rule.hard_limit
        if level == ComplianceLevel.WARNING:
            threshold_value = rule.warning_threshold
        elif level == ComplianceLevel.CRITICAL:
            threshold_value = rule.critical_threshold
        
        alert = ComplianceAlert(
            timestamp=datetime.now(),
            rule_id=rule.rule_id,
            violation_type=rule.violation_type,
            level=level,
            current_value=current_value,
            threshold_value=threshold_value,
            message=f"{rule.name}: {level.value.upper()} - Current: {current_value}, Threshold: {threshold_value}",
            action_taken="pending",
            resolved=False
        )
        
        self.alerts.append(alert)
        
        # Update statistics
        if level == ComplianceLevel.WARNING:
            self.compliance_stats['warnings_issued'] += 1
        elif level in [ComplianceLevel.CRITICAL, ComplianceLevel.VIOLATION]:
            self.compliance_stats['violations_recorded'] += 1
            self.violation_count += 1
        
        self.logger.warning(f"Compliance alert: {alert.message}")
    
    async def _trigger_emergency_stop(self, rule: ComplianceRule) -> str:
        """Trigger emergency stop"""
        self.trading_enabled = False
        self.emergency_stop_triggered = True
        self.compliance_stats['auto_stops_triggered'] += 1
        
        action_message = f"EMERGENCY STOP triggered by {rule.name}"
        self.logger.critical(action_message)
        
        # Update latest alert
        if self.alerts:
            self.alerts[-1].action_taken = "emergency_stop"
        
        return "emergency_stop"
    
    async def update_account_metrics(self, 
                                   current_balance: float = None,
                                   daily_pnl: float = None,
                                   open_positions_value: float = None,
                                   trade_completed: bool = False,
                                   trade_won: bool = None):
        """Update account metrics for compliance monitoring"""
        try:
            if current_balance is not None:
                self.account_metrics.current_balance = current_balance
                self.account_metrics.total_pnl = current_balance - self.account_metrics.starting_balance
                
                # Update peak balance and drawdown
                if current_balance > self.account_metrics.peak_balance:
                    self.account_metrics.peak_balance = current_balance
                
                current_drawdown = self.account_metrics.peak_balance - current_balance
                if current_drawdown > self.account_metrics.max_drawdown:
                    self.account_metrics.max_drawdown = current_drawdown
            
            if daily_pnl is not None:
                self.account_metrics.daily_pnl = daily_pnl
            
            if open_positions_value is not None:
                self.account_metrics.open_positions_value = abs(open_positions_value)
            
            if trade_completed:
                self.account_metrics.daily_trades += 1
                self.account_metrics.last_trade_time = datetime.now()
                
                # Track consecutive losses
                if trade_won is not None:
                    if trade_won:
                        self.account_metrics.consecutive_losses = 0
                    else:
                        self.account_metrics.consecutive_losses += 1
            
        except Exception as e:
            self.logger.error(f"Error updating account metrics: {e}")
    
    async def validate_trade(self, 
                           position_size: float,
                           entry_price: float,
                           stop_loss: float) -> Dict[str, Any]:
        """Validate a proposed trade against compliance rules"""
        try:
            # Calculate trade risk
            risk_per_share = abs(entry_price - stop_loss)
            total_risk = position_size * risk_per_share
            
            # Check position size rule
            position_rule = self.rules.get('position_size')
            if position_rule and position_rule.enabled:
                if total_risk > position_rule.hard_limit:
                    return {
                        'approved': False,
                        'reason': f'Trade risk ${total_risk:.2f} exceeds maximum ${position_rule.hard_limit:.2f}',
                        'rule_violated': 'position_size'
                    }
            
            # Check if trading is enabled
            if not self.trading_enabled:
                return {
                    'approved': False,
                    'reason': 'Trading is currently disabled due to compliance violation',
                    'rule_violated': 'trading_disabled'
                }
            
            # Check revenge trading rule
            revenge_rule = self.rules.get('revenge_trading')
            if (revenge_rule and revenge_rule.enabled and 
                self.account_metrics.consecutive_losses >= revenge_rule.critical_threshold):
                return {
                    'approved': False,
                    'reason': f'Too many consecutive losses ({self.account_metrics.consecutive_losses})',
                    'rule_violated': 'revenge_trading'
                }
            
            # Check daily trade limit
            trade_limit_rule = self.rules.get('daily_trades')
            if (trade_limit_rule and trade_limit_rule.enabled and 
                self.account_metrics.daily_trades >= trade_limit_rule.hard_limit):
                return {
                    'approved': False,
                    'reason': f'Daily trade limit reached ({self.account_metrics.daily_trades})',
                    'rule_violated': 'daily_trades'
                }
            
            return {
                'approved': True,
                'risk_amount': total_risk,
                'risk_percentage': (total_risk / self.account_metrics.current_balance) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return {
                'approved': False,
                'reason': f'Validation error: {str(e)}',
                'rule_violated': 'system_error'
            }
    
    async def reset_emergency_stop(self, admin_override: bool = False):
        """Reset emergency stop (requires admin override)"""
        if admin_override:
            self.emergency_stop_triggered = False
            self.trading_enabled = True
            self.logger.info("Emergency stop reset by admin override")
        else:
            self.logger.warning("Emergency stop reset attempted without admin override")
    
    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """Get recent alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [alert for alert in self.alerts if alert.timestamp >= cutoff_time]
        return [asdict(alert) for alert in recent_alerts]
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get comprehensive compliance summary"""
        return {
            'account_metrics': asdict(self.account_metrics),
            'trading_status': {
                'enabled': self.trading_enabled,
                'emergency_stop': self.emergency_stop_triggered,
                'violation_count': self.violation_count
            },
            'statistics': self.compliance_stats.copy(),
            'rules_summary': {
                rule_id: {
                    'name': rule.name,
                    'enabled': rule.enabled,
                    'auto_stop': rule.auto_stop,
                    'hard_limit': rule.hard_limit
                }
                for rule_id, rule in self.rules.items()
            },
            'recent_alerts': len(self.get_alert_history(24))
        }
    
    def is_healthy(self) -> bool:
        """Check if compliance monitor is healthy"""
        return (
            self.trading_enabled and
            not self.emergency_stop_triggered and
            self.violation_count < 5  # Less than 5 violations
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get compliance monitor statistics"""
        return {
            **self.compliance_stats,
            'trading_enabled': self.trading_enabled,
            'emergency_stop': self.emergency_stop_triggered,
            'violation_count': self.violation_count,
            'rules_enabled': len([r for r in self.rules.values() if r.enabled]),
            'is_healthy': self.is_healthy()
        }
