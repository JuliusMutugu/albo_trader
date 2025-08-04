"""
Enigma Cadence Tracker - Monitors consecutive failed signals for optimal entry timing.

This module implements the "Three Losses, Two Winners, Restart" cadence strategy
for identifying high-probability Enigma signal entry points.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time
from enum import Enum


class TradingSession(Enum):
    """Trading session enumeration."""
    AM = "AM"
    PM = "PM"
    OVERNIGHT = "OVERNIGHT"


class CadenceTracker:
    """
    Enigma signal cadence tracker for optimal entry timing.
    
    Strategy:
    - Track consecutive failed Enigma signals
    - AM session: Alert after 2 consecutive failures
    - PM session: Alert after 3 consecutive failures
    - Reset counter on successful signal
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cadence thresholds
        self.am_threshold = config.get('am_threshold', 2)
        self.pm_threshold = config.get('pm_threshold', 3)
        
        # Session timing (Eastern Time)
        self.am_start = time(9, 30)   # 9:30 AM
        self.am_end = time(12, 0)     # 12:00 PM
        self.pm_start = time(12, 0)   # 12:00 PM
        self.pm_end = time(16, 0)     # 4:00 PM
        
        # Cadence state
        self.consecutive_failures = 0
        self.consecutive_wins = 0
        self.last_signal_time = None
        self.current_session = None
        
        # Signal history
        self.signal_history = []
        self.max_history = config.get('max_history', 1000)
        
        # Cadence statistics
        self.session_stats = {
            'AM': {'signals': 0, 'wins': 0, 'losses': 0},
            'PM': {'signals': 0, 'wins': 0, 'losses': 0}
        }
        
    def update_signal(self, signal_data: Dict[str, Any]):
        """
        Update cadence tracker with new signal data.
        
        Args:
            signal_data: Enigma signal information from OCR
        """
        try:
            current_time = datetime.now()
            session = self._get_current_session(current_time.time())
            
            # For now, we'll track signals and update outcome later
            # when we know if the trade was successful
            signal_record = {
                'timestamp': current_time,
                'session': session.value,
                'signal_data': signal_data,
                'outcome': 'pending'  # Will be updated when trade closes
            }
            
            self.signal_history.append(signal_record)
            
            # Limit history size
            if len(self.signal_history) > self.max_history:
                self.signal_history = self.signal_history[-self.max_history:]
                
            self.last_signal_time = current_time
            self.current_session = session
            
            # Update session statistics
            self.session_stats[session.value]['signals'] += 1
            
            self.logger.debug(f"Signal tracked: {session.value} session, "
                            f"consecutive failures: {self.consecutive_failures}")
            
        except Exception as e:
            self.logger.error(f"Signal update error: {e}")
            
    def update_signal_outcome(self, outcome: str, signal_index: int = -1):
        """
        Update the outcome of a previously tracked signal.
        
        Args:
            outcome: 'win' or 'loss'
            signal_index: Index of signal to update (default: most recent)
        """
        try:
            if not self.signal_history:
                self.logger.warning("No signals to update")
                return
                
            # Update signal outcome
            signal = self.signal_history[signal_index]
            signal['outcome'] = outcome
            
            session = signal['session']
            
            # Update cadence counters
            if outcome == 'win':
                self.consecutive_failures = 0
                self.consecutive_wins += 1
                self.session_stats[session]['wins'] += 1
                
                self.logger.info(f"Signal WIN recorded - Consecutive failures reset to 0")
                
            elif outcome == 'loss':
                self.consecutive_failures += 1
                self.consecutive_wins = 0
                self.session_stats[session]['losses'] += 1
                
                self.logger.info(f"Signal LOSS recorded - Consecutive failures: {self.consecutive_failures}")
                
            else:
                self.logger.warning(f"Invalid outcome: {outcome}")
                
        except Exception as e:
            self.logger.error(f"Signal outcome update error: {e}")
            
    def threshold_met(self, session: TradingSession = None) -> bool:
        """
        Check if cadence threshold is met for high-probability entry.
        
        Args:
            session: Trading session to check (default: current session)
            
        Returns:
            True if threshold is met
        """
        try:
            if session is None:
                session = self.current_session or self._get_current_session()
                
            if session == TradingSession.AM:
                threshold = self.am_threshold
            elif session == TradingSession.PM:
                threshold = self.pm_threshold
            else:
                # Overnight session - use PM threshold
                threshold = self.pm_threshold
                
            is_met = self.consecutive_failures >= threshold
            
            if is_met:
                self.logger.info(f"Cadence threshold MET - {session.value} session: "
                               f"{self.consecutive_failures} >= {threshold}")
            else:
                self.logger.debug(f"Cadence threshold not met - {session.value} session: "
                                f"{self.consecutive_failures} < {threshold}")
                
            return is_met
            
        except Exception as e:
            self.logger.error(f"Threshold check error: {e}")
            return False
            
    def _get_current_session(self, current_time: time = None) -> TradingSession:
        """
        Determine current trading session based on time.
        
        Args:
            current_time: Time to check (default: now)
            
        Returns:
            Current trading session
        """
        if current_time is None:
            current_time = datetime.now().time()
            
        if self.am_start <= current_time < self.am_end:
            return TradingSession.AM
        elif self.pm_start <= current_time < self.pm_end:
            return TradingSession.PM
        else:
            return TradingSession.OVERNIGHT
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get current cadence tracker status.
        
        Returns:
            Dictionary with cadence status and statistics
        """
        try:
            current_session = self._get_current_session()
            
            # Calculate session win rates
            session_win_rates = {}
            for session in ['AM', 'PM']:
                stats = self.session_stats[session]
                total = stats['wins'] + stats['losses']
                win_rate = stats['wins'] / total if total > 0 else 0
                session_win_rates[session] = win_rate
                
            # Get recent signal history
            recent_signals = self.signal_history[-10:] if self.signal_history else []
            
            return {
                'consecutive_failures': self.consecutive_failures,
                'consecutive_wins': self.consecutive_wins,
                'current_session': current_session.value,
                'am_threshold': self.am_threshold,
                'pm_threshold': self.pm_threshold,
                'threshold_met': self.threshold_met(),
                'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
                'session_stats': self.session_stats,
                'session_win_rates': session_win_rates,
                'total_signals': len(self.signal_history),
                'recent_signals': recent_signals
            }
            
        except Exception as e:
            self.logger.error(f"Status calculation error: {e}")
            return {}
            
    def reset_cadence(self):
        """Reset cadence counters (use carefully)."""
        self.consecutive_failures = 0
        self.consecutive_wins = 0
        self.logger.info("Cadence counters reset")
        
    def reset_session_stats(self):
        """Reset session statistics."""
        self.session_stats = {
            'AM': {'signals': 0, 'wins': 0, 'losses': 0},
            'PM': {'signals': 0, 'wins': 0, 'losses': 0}
        }
        self.logger.info("Session statistics reset")
        
    def get_win_rate_by_session(self, session: str = None) -> float:
        """
        Get win rate for specific session or overall.
        
        Args:
            session: 'AM', 'PM', or None for overall
            
        Returns:
            Win rate as decimal (0.0 to 1.0)
        """
        try:
            if session:
                stats = self.session_stats.get(session, {'wins': 0, 'losses': 0})
                total = stats['wins'] + stats['losses']
                return stats['wins'] / total if total > 0 else 0.0
            else:
                # Overall win rate
                total_wins = sum(s['wins'] for s in self.session_stats.values())
                total_losses = sum(s['losses'] for s in self.session_stats.values())
                total = total_wins + total_losses
                return total_wins / total if total > 0 else 0.0
                
        except Exception as e:
            self.logger.error(f"Win rate calculation error: {e}")
            return 0.0
            
    def get_failure_streak_analysis(self) -> Dict[str, Any]:
        """
        Analyze failure streaks and success rates after thresholds.
        
        Returns:
            Analysis of cadence effectiveness
        """
        try:
            if len(self.signal_history) < 10:
                return {'insufficient_data': True}
                
            # Analyze signals after cadence thresholds were met
            threshold_met_signals = []
            consecutive_count = 0
            
            for signal in self.signal_history:
                if signal['outcome'] == 'loss':
                    consecutive_count += 1
                elif signal['outcome'] == 'win':
                    # Check if we had met threshold before this win
                    session = signal['session']
                    threshold = self.am_threshold if session == 'AM' else self.pm_threshold
                    
                    if consecutive_count >= threshold:
                        threshold_met_signals.append({
                            'failures_before': consecutive_count,
                            'session': session,
                            'outcome': 'win'
                        })
                        
                    consecutive_count = 0
                    
            # Calculate success rate after threshold
            if threshold_met_signals:
                wins_after_threshold = len([s for s in threshold_met_signals if s['outcome'] == 'win'])
                success_rate = wins_after_threshold / len(threshold_met_signals)
            else:
                success_rate = 0.0
                
            return {
                'threshold_signals': len(threshold_met_signals),
                'success_rate_after_threshold': success_rate,
                'average_failures_before_win': sum(s['failures_before'] for s in threshold_met_signals) / len(threshold_met_signals) if threshold_met_signals else 0,
                'max_consecutive_failures': max((consecutive_count, self.consecutive_failures)),
                'cadence_effectiveness': success_rate > 0.6  # 60% threshold
            }
            
        except Exception as e:
            self.logger.error(f"Failure streak analysis error: {e}")
            return {}
            
    def should_adjust_thresholds(self) -> Dict[str, Any]:
        """
        Analyze if cadence thresholds should be adjusted based on performance.
        
        Returns:
            Recommendations for threshold adjustments
        """
        try:
            analysis = self.get_failure_streak_analysis()
            
            if analysis.get('insufficient_data'):
                return {'adjust': False, 'reason': 'Insufficient data'}
                
            success_rate = analysis.get('success_rate_after_threshold', 0)
            
            recommendations = {
                'adjust': False,
                'current_am_threshold': self.am_threshold,
                'current_pm_threshold': self.pm_threshold,
                'recommended_am_threshold': self.am_threshold,
                'recommended_pm_threshold': self.pm_threshold,
                'success_rate': success_rate
            }
            
            # If success rate is too low, consider increasing thresholds
            if success_rate < 0.5:
                recommendations['adjust'] = True
                recommendations['recommended_am_threshold'] = min(self.am_threshold + 1, 5)
                recommendations['recommended_pm_threshold'] = min(self.pm_threshold + 1, 6)
                recommendations['reason'] = 'Low success rate - increase thresholds'
                
            # If success rate is very high, consider decreasing thresholds
            elif success_rate > 0.8:
                recommendations['adjust'] = True
                recommendations['recommended_am_threshold'] = max(self.am_threshold - 1, 1)
                recommendations['recommended_pm_threshold'] = max(self.pm_threshold - 1, 2)
                recommendations['reason'] = 'High success rate - decrease thresholds for more opportunities'
                
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Threshold adjustment analysis error: {e}")
            return {'adjust': False, 'reason': f'Analysis error: {e}'}
