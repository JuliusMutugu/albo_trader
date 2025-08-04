"""
Cadence Tracker - Monitor Enigma Signal Timing and Performance
Tracks power score patterns and failure thresholds (2 AM, 3 PM)
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
import json
from enum import Enum

class CadenceState(Enum):
    """Cadence tracking states"""
    NORMAL = "normal"
    WARNING = "warning"
    FAILURE = "failure"
    RECOVERY = "recovery"

@dataclass
class PowerScoreReading:
    """Individual power score reading"""
    timestamp: datetime
    power_score: int
    confluence_level: str
    signal_color: str
    valid: bool

@dataclass
class CadencePattern:
    """Detected cadence pattern"""
    pattern_type: str
    start_time: datetime
    end_time: Optional[datetime]
    readings: List[PowerScoreReading]
    avg_power_score: float
    state: CadenceState
    notes: str

@dataclass
class FailureEvent:
    """Cadence failure event"""
    timestamp: datetime
    failure_type: str  # "2am_failure", "3pm_failure", "extended_low"
    duration_minutes: int
    min_power_score: int
    recovery_time: Optional[datetime]
    impact_assessment: str

class CadenceTracker:
    """
    Tracks Enigma signal cadence and identifies failure patterns
    """
    
    def __init__(self, 
                 reading_history_hours: int = 48,
                 low_power_threshold: int = 30,
                 failure_duration_minutes: int = 60):
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.reading_history_hours = reading_history_hours
        self.low_power_threshold = low_power_threshold
        self.failure_duration_minutes = failure_duration_minutes
        
        # Data storage
        max_readings = reading_history_hours * 60  # Assuming 1 reading per minute
        self.power_readings: deque = deque(maxlen=max_readings)
        self.patterns: List[CadencePattern] = []
        self.failure_events: List[FailureEvent] = []
        
        # Current state
        self.current_state = CadenceState.NORMAL
        self.current_pattern: Optional[CadencePattern] = None
        self.state_start_time = datetime.now()
        
        # Critical time windows (2 AM and 3 PM failures)
        self.critical_times = {
            '2am_window': {'start': time(1, 30), 'end': time(2, 30)},  # 1:30-2:30 AM
            '3pm_window': {'start': time(14, 30), 'end': time(15, 30)}  # 2:30-3:30 PM
        }
        
        # Tracking statistics
        self.stats = {
            'total_readings': 0,
            'failure_events': 0,
            'recovery_events': 0,
            'avg_power_score_24h': 0.0,
            'last_failure': None,
            'longest_failure_minutes': 0,
            'current_streak_minutes': 0
        }
    
    async def add_reading(self, reading: PowerScoreReading):
        """Add a new power score reading"""
        try:
            self.power_readings.append(reading)
            self.stats['total_readings'] += 1
            
            # Update current pattern
            await self._update_current_pattern(reading)
            
            # Check for state changes
            await self._check_state_changes(reading)
            
            # Update statistics
            await self._update_statistics()
            
            self.logger.debug(f"Added reading: Power={reading.power_score}, State={self.current_state.value}")
            
        except Exception as e:
            self.logger.error(f"Error adding reading: {e}")
    
    async def _update_current_pattern(self, reading: PowerScoreReading):
        """Update the current cadence pattern"""
        if self.current_pattern is None:
            # Start new pattern
            self.current_pattern = CadencePattern(
                pattern_type="monitoring",
                start_time=reading.timestamp,
                end_time=None,
                readings=[reading],
                avg_power_score=reading.power_score,
                state=self.current_state,
                notes=""
            )
        else:
            # Add to existing pattern
            self.current_pattern.readings.append(reading)
            
            # Recalculate average
            valid_readings = [r for r in self.current_pattern.readings if r.valid]
            if valid_readings:
                self.current_pattern.avg_power_score = sum(r.power_score for r in valid_readings) / len(valid_readings)
            
            self.current_pattern.state = self.current_state
    
    async def _check_state_changes(self, reading: PowerScoreReading):
        """Check if the cadence state should change"""
        current_time = reading.timestamp.time()
        
        # Check for critical time window failures
        if self._is_in_critical_window(current_time):
            if reading.power_score < self.low_power_threshold:
                await self._handle_critical_failure(reading)
        
        # Check for general state changes
        recent_readings = self._get_recent_readings(30)  # Last 30 readings
        if len(recent_readings) >= 10:
            recent_power_scores = [r.power_score for r in recent_readings if r.valid]
            
            if recent_power_scores:
                avg_recent_power = sum(recent_power_scores) / len(recent_power_scores)
                
                # State transition logic
                if self.current_state == CadenceState.NORMAL:
                    if avg_recent_power < self.low_power_threshold:
                        await self._transition_to_state(CadenceState.WARNING, reading)
                
                elif self.current_state == CadenceState.WARNING:
                    if avg_recent_power < self.low_power_threshold * 0.7:  # 70% of threshold
                        await self._transition_to_state(CadenceState.FAILURE, reading)
                    elif avg_recent_power > self.low_power_threshold * 1.2:  # 120% of threshold
                        await self._transition_to_state(CadenceState.NORMAL, reading)
                
                elif self.current_state == CadenceState.FAILURE:
                    if avg_recent_power > self.low_power_threshold:
                        await self._transition_to_state(CadenceState.RECOVERY, reading)
                
                elif self.current_state == CadenceState.RECOVERY:
                    if avg_recent_power > self.low_power_threshold * 1.5:  # Strong recovery
                        await self._transition_to_state(CadenceState.NORMAL, reading)
                    elif avg_recent_power < self.low_power_threshold * 0.8:
                        await self._transition_to_state(CadenceState.WARNING, reading)
    
    def _is_in_critical_window(self, current_time: time) -> bool:
        """Check if current time is in a critical failure window"""
        for window_name, window in self.critical_times.items():
            if window['start'] <= current_time <= window['end']:
                return True
        return False
    
    async def _handle_critical_failure(self, reading: PowerScoreReading):
        """Handle failure during critical time windows"""
        current_time = reading.timestamp.time()
        
        # Determine which critical window
        failure_type = None
        for window_name, window in self.critical_times.items():
            if window['start'] <= current_time <= window['end']:
                failure_type = window_name.replace('_window', '_failure')
                break
        
        if failure_type:
            # Create failure event
            failure_event = FailureEvent(
                timestamp=reading.timestamp,
                failure_type=failure_type,
                duration_minutes=0,  # Will be updated when recovered
                min_power_score=reading.power_score,
                recovery_time=None,
                impact_assessment="critical_time_failure"
            )
            
            self.failure_events.append(failure_event)
            self.stats['failure_events'] += 1
            self.stats['last_failure'] = reading.timestamp
            
            await self._transition_to_state(CadenceState.FAILURE, reading)
            
            self.logger.warning(f"Critical failure detected: {failure_type} at {reading.timestamp}")
    
    async def _transition_to_state(self, new_state: CadenceState, reading: PowerScoreReading):
        """Transition to a new cadence state"""
        old_state = self.current_state
        
        # Calculate duration in current state
        state_duration = (reading.timestamp - self.state_start_time).total_seconds() / 60
        
        # Complete current pattern
        if self.current_pattern:
            self.current_pattern.end_time = reading.timestamp
            self.current_pattern.notes = f"Duration: {state_duration:.1f} minutes"
            self.patterns.append(self.current_pattern)
        
        # Update state
        self.current_state = new_state
        self.state_start_time = reading.timestamp
        self.current_pattern = None
        
        # Handle recovery
        if old_state == CadenceState.FAILURE and new_state in [CadenceState.RECOVERY, CadenceState.NORMAL]:
            await self._handle_recovery(reading, state_duration)
        
        # Update streak tracking
        if new_state == CadenceState.NORMAL:
            self.stats['current_streak_minutes'] += state_duration
        else:
            self.stats['current_streak_minutes'] = 0
        
        self.logger.info(f"State transition: {old_state.value} -> {new_state.value} "
                        f"(duration: {state_duration:.1f} minutes)")
    
    async def _handle_recovery(self, reading: PowerScoreReading, failure_duration: float):
        """Handle recovery from failure state"""
        self.stats['recovery_events'] += 1
        
        # Update the most recent failure event
        if self.failure_events:
            latest_failure = self.failure_events[-1]
            if latest_failure.recovery_time is None:
                latest_failure.recovery_time = reading.timestamp
                latest_failure.duration_minutes = int(failure_duration)
                
                # Update longest failure tracking
                if failure_duration > self.stats['longest_failure_minutes']:
                    self.stats['longest_failure_minutes'] = failure_duration
        
        self.logger.info(f"Recovery detected after {failure_duration:.1f} minutes")
    
    def _get_recent_readings(self, count: int) -> List[PowerScoreReading]:
        """Get the most recent N readings"""
        if len(self.power_readings) <= count:
            return list(self.power_readings)
        else:
            return list(self.power_readings)[-count:]
    
    async def _update_statistics(self):
        """Update tracking statistics"""
        if not self.power_readings:
            return
        
        # Calculate 24-hour average
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_readings = [r for r in self.power_readings 
                          if r.timestamp >= last_24h and r.valid]
        
        if recent_readings:
            self.stats['avg_power_score_24h'] = sum(r.power_score for r in recent_readings) / len(recent_readings)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current cadence status"""
        current_time = datetime.now()
        state_duration = (current_time - self.state_start_time).total_seconds() / 60
        
        # Get recent readings for trend analysis
        recent_readings = self._get_recent_readings(10)
        trend = "stable"
        
        if len(recent_readings) >= 2:
            recent_power_scores = [r.power_score for r in recent_readings if r.valid]
            if len(recent_power_scores) >= 2:
                first_half = recent_power_scores[:len(recent_power_scores)//2]
                second_half = recent_power_scores[len(recent_power_scores)//2:]
                
                avg_first = sum(first_half) / len(first_half) if first_half else 0
                avg_second = sum(second_half) / len(second_half) if second_half else 0
                
                if avg_second > avg_first * 1.1:
                    trend = "improving"
                elif avg_second < avg_first * 0.9:
                    trend = "declining"
        
        return {
            'current_state': self.current_state.value,
            'state_duration_minutes': round(state_duration, 1),
            'trend': trend,
            'is_critical_window': self._is_in_critical_window(current_time.time()),
            'latest_power_score': recent_readings[-1].power_score if recent_readings else 0,
            'avg_power_score_10min': sum(r.power_score for r in recent_readings if r.valid) / len([r for r in recent_readings if r.valid]) if recent_readings else 0,
            'total_readings': len(self.power_readings),
            'failure_count_24h': len([f for f in self.failure_events if f.timestamp >= current_time - timedelta(hours=24)])
        }
    
    def get_failure_analysis(self) -> Dict[str, Any]:
        """Get detailed failure analysis"""
        if not self.failure_events:
            return {'no_failures': True}
        
        # Analyze failure patterns
        failure_types = {}
        total_failure_time = 0
        
        for failure in self.failure_events:
            failure_type = failure.failure_type
            if failure_type not in failure_types:
                failure_types[failure_type] = {'count': 0, 'total_duration': 0}
            
            failure_types[failure_type]['count'] += 1
            failure_types[failure_type]['total_duration'] += failure.duration_minutes
            total_failure_time += failure.duration_minutes
        
        # Recent failures (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_failures = [f for f in self.failure_events if f.timestamp >= week_ago]
        
        return {
            'total_failures': len(self.failure_events),
            'failure_types': failure_types,
            'total_failure_time_minutes': total_failure_time,
            'recent_failures_7d': len(recent_failures),
            'longest_failure_minutes': self.stats['longest_failure_minutes'],
            'last_failure': self.stats['last_failure'].isoformat() if self.stats['last_failure'] else None,
            'avg_failure_duration': total_failure_time / len(self.failure_events) if self.failure_events else 0
        }
    
    def get_cadence_report(self) -> Dict[str, Any]:
        """Get comprehensive cadence report"""
        return {
            'current_status': self.get_current_status(),
            'failure_analysis': self.get_failure_analysis(),
            'statistics': self.stats.copy(),
            'pattern_count': len(self.patterns),
            'monitoring_duration_hours': self.reading_history_hours,
            'thresholds': {
                'low_power_threshold': self.low_power_threshold,
                'failure_duration_minutes': self.failure_duration_minutes
            },
            'critical_windows': self.critical_times
        }
    
    async def export_cadence_data(self, file_path: str):
        """Export cadence tracking data"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'cadence_report': self.get_cadence_report(),
                'power_readings': [asdict(reading) for reading in self.power_readings],
                'patterns': [asdict(pattern) for pattern in self.patterns],
                'failure_events': [asdict(failure) for failure in self.failure_events]
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Cadence data exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting cadence data: {e}")
    
    def is_healthy(self) -> bool:
        """Check if cadence tracker is healthy"""
        return (
            len(self.power_readings) > 0 and
            self.current_state != CadenceState.FAILURE
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cadence tracker statistics"""
        return {
            **self.stats,
            'readings_count': len(self.power_readings),
            'patterns_detected': len(self.patterns),
            'current_state': self.current_state.value,
            'is_healthy': self.is_healthy()
        }
