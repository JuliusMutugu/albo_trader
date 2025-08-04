"""
ATR (Average True Range) calculator for volatility-based risk management.

This module calculates dynamic stop losses and profit targets based on 
market volatility using ATR indicators.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime, timedelta


class ATRCalculator:
    """
    ATR-based risk management calculator.
    
    Features:
    - Dynamic stop loss calculation
    - Volatility-adjusted profit targets
    - ATR-based position sizing inputs
    - Multi-timeframe ATR monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # ATR parameters
        self.atr_period = config.get('atr_period', 14)
        self.sl_multiplier = config.get('sl_multiplier', 1.5)
        self.pt_multiplier = config.get('pt_multiplier', 2.0)
        
        # ATR data storage
        self.current_atr = None
        self.atr_history = []
        self.last_update = None
        
        # Price data for ATR calculation
        self.price_data = []
        self.max_price_history = config.get('max_price_history', 1000)
        
    async def get_current_atr(self) -> Optional[float]:
        """
        Get current ATR value.
        
        Returns:
            Current ATR value or None if not available
        """
        try:
            # Check if we have recent ATR data
            if (self.current_atr is not None and 
                self.last_update and 
                (datetime.now() - self.last_update).seconds < 300):  # 5 minutes
                return self.current_atr
                
            # Try to update ATR from data source
            await self._update_atr()
            
            return self.current_atr
            
        except Exception as e:
            self.logger.error(f"ATR retrieval error: {e}")
            return None
            
    async def _update_atr(self):
        """Update ATR calculation with latest price data."""
        try:
            # In production, this would connect to price feed
            # For now, use manual input or mock data
            
            if len(self.price_data) < self.atr_period:
                # Not enough data for ATR calculation
                self.current_atr = self.config.get('default_atr', 10.0)
                self.logger.warning("Using default ATR - insufficient price data")
                return
                
            # Calculate True Range for each period
            true_ranges = []
            
            for i in range(1, len(self.price_data)):
                current = self.price_data[i]
                previous = self.price_data[i-1]
                
                # True Range = max(high-low, |high-prev_close|, |low-prev_close|)
                tr1 = current['high'] - current['low']
                tr2 = abs(current['high'] - previous['close'])
                tr3 = abs(current['low'] - previous['close'])
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
                
            # Calculate ATR as moving average of True Range
            if len(true_ranges) >= self.atr_period:
                recent_trs = true_ranges[-self.atr_period:]
                self.current_atr = sum(recent_trs) / len(recent_trs)
                self.last_update = datetime.now()
                
                # Store in history
                self.atr_history.append({
                    'timestamp': self.last_update,
                    'atr': self.current_atr
                })
                
                # Limit history size
                if len(self.atr_history) > self.max_price_history:
                    self.atr_history = self.atr_history[-self.max_price_history:]
                    
                self.logger.debug(f"ATR updated: {self.current_atr:.2f}")
                
        except Exception as e:
            self.logger.error(f"ATR update error: {e}")
            
    def add_price_data(self, high: float, low: float, close: float, 
                      timestamp: datetime = None):
        """
        Add new price data for ATR calculation.
        
        Args:
            high: High price for the period
            low: Low price for the period  
            close: Close price for the period
            timestamp: Timestamp for the data point
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
                
            price_point = {
                'timestamp': timestamp,
                'high': high,
                'low': low,
                'close': close
            }
            
            self.price_data.append(price_point)
            
            # Limit price data size
            if len(self.price_data) > self.max_price_history:
                self.price_data = self.price_data[-self.max_price_history:]
                
            self.logger.debug(f"Price data added: H:{high} L:{low} C:{close}")
            
        except Exception as e:
            self.logger.error(f"Price data addition error: {e}")
            
    def calculate_stop_loss(self, entry_price: float, atr_value: float, 
                          direction: str) -> float:
        """
        Calculate stop loss price based on ATR.
        
        Args:
            entry_price: Entry price for the trade
            atr_value: Current ATR value
            direction: 'long' or 'short'
            
        Returns:
            Stop loss price
        """
        try:
            stop_distance = atr_value * self.sl_multiplier
            
            if direction.lower() == 'long':
                stop_loss = entry_price - stop_distance
            elif direction.lower() == 'short':
                stop_loss = entry_price + stop_distance
            else:
                raise ValueError(f"Invalid direction: {direction}")
                
            self.logger.debug(f"Stop loss calculated: {stop_loss:.2f} "
                            f"(distance: {stop_distance:.2f})")
            
            return stop_loss
            
        except Exception as e:
            self.logger.error(f"Stop loss calculation error: {e}")
            return entry_price  # Conservative fallback
            
    def calculate_profit_target(self, entry_price: float, atr_value: float,
                              direction: str) -> float:
        """
        Calculate profit target price based on ATR.
        
        Args:
            entry_price: Entry price for the trade
            atr_value: Current ATR value
            direction: 'long' or 'short'
            
        Returns:
            Profit target price
        """
        try:
            target_distance = atr_value * self.pt_multiplier
            
            if direction.lower() == 'long':
                profit_target = entry_price + target_distance
            elif direction.lower() == 'short':
                profit_target = entry_price - target_distance
            else:
                raise ValueError(f"Invalid direction: {direction}")
                
            self.logger.debug(f"Profit target calculated: {profit_target:.2f} "
                            f"(distance: {target_distance:.2f})")
            
            return profit_target
            
        except Exception as e:
            self.logger.error(f"Profit target calculation error: {e}")
            return entry_price  # Conservative fallback
            
    def get_risk_reward_ratio(self, atr_value: float = None) -> float:
        """
        Get current risk/reward ratio based on ATR multipliers.
        
        Args:
            atr_value: ATR value (optional, uses current if not provided)
            
        Returns:
            Risk/reward ratio (profit target / stop loss distance)
        """
        try:
            return self.pt_multiplier / self.sl_multiplier
            
        except Exception as e:
            self.logger.error(f"Risk/reward calculation error: {e}")
            return 1.0  # 1:1 fallback
            
    def adjust_multipliers_for_volatility(self):
        """
        Dynamically adjust ATR multipliers based on current volatility.
        """
        try:
            if len(self.atr_history) < 20:
                return  # Not enough history
                
            # Calculate recent ATR average and volatility
            recent_atrs = [h['atr'] for h in self.atr_history[-20:]]
            avg_atr = sum(recent_atrs) / len(recent_atrs)
            
            # Adjust multipliers based on volatility regime
            if self.current_atr > avg_atr * 1.5:
                # High volatility - widen stops
                self.sl_multiplier = self.config.get('sl_multiplier', 1.5) * 1.2
                self.pt_multiplier = self.config.get('pt_multiplier', 2.0) * 1.2
                self.logger.info("High volatility detected - widening stops")
                
            elif self.current_atr < avg_atr * 0.7:
                # Low volatility - tighten stops
                self.sl_multiplier = self.config.get('sl_multiplier', 1.5) * 0.8
                self.pt_multiplier = self.config.get('pt_multiplier', 2.0) * 0.8
                self.logger.info("Low volatility detected - tightening stops")
                
            else:
                # Normal volatility - use default multipliers
                self.sl_multiplier = self.config.get('sl_multiplier', 1.5)
                self.pt_multiplier = self.config.get('pt_multiplier', 2.0)
                
        except Exception as e:
            self.logger.error(f"Multiplier adjustment error: {e}")
            
    def get_position_risk_dollars(self, entry_price: float, stop_loss: float,
                                 position_size: int, tick_value: float = 12.50) -> float:
        """
        Calculate position risk in dollars.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            position_size: Number of contracts
            tick_value: Dollar value per tick
            
        Returns:
            Risk amount in dollars
        """
        try:
            risk_per_contract = abs(entry_price - stop_loss) * tick_value
            total_risk = risk_per_contract * position_size
            
            return total_risk
            
        except Exception as e:
            self.logger.error(f"Position risk calculation error: {e}")
            return 0.0
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get ATR calculator statistics.
        
        Returns:
            Dictionary with ATR metrics
        """
        try:
            if not self.atr_history:
                return {
                    'current_atr': self.current_atr,
                    'sl_multiplier': self.sl_multiplier,
                    'pt_multiplier': self.pt_multiplier,
                    'risk_reward_ratio': self.get_risk_reward_ratio()
                }
                
            recent_atrs = [h['atr'] for h in self.atr_history[-20:]]
            
            return {
                'current_atr': self.current_atr,
                'avg_atr_20': sum(recent_atrs) / len(recent_atrs) if recent_atrs else None,
                'min_atr_20': min(recent_atrs) if recent_atrs else None,
                'max_atr_20': max(recent_atrs) if recent_atrs else None,
                'sl_multiplier': self.sl_multiplier,
                'pt_multiplier': self.pt_multiplier,
                'risk_reward_ratio': self.get_risk_reward_ratio(),
                'atr_history_count': len(self.atr_history),
                'price_data_count': len(self.price_data),
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            self.logger.error(f"ATR stats calculation error: {e}")
            return {}
            
    def set_manual_atr(self, atr_value: float):
        """
        Manually set ATR value (for testing or when automated calculation unavailable).
        
        Args:
            atr_value: ATR value to set
        """
        try:
            self.current_atr = atr_value
            self.last_update = datetime.now()
            
            self.logger.info(f"Manual ATR set: {atr_value:.2f}")
            
        except Exception as e:
            self.logger.error(f"Manual ATR setting error: {e}")
            
    def validate_atr_data(self) -> bool:
        """
        Validate that ATR data is reasonable and current.
        
        Returns:
            True if ATR data is valid
        """
        try:
            # Check if ATR exists
            if self.current_atr is None:
                return False
                
            # Check if ATR is reasonable (not zero or extremely high)
            if self.current_atr <= 0 or self.current_atr > 1000:
                return False
                
            # Check if data is recent (within last hour)
            if (self.last_update and 
                (datetime.now() - self.last_update).seconds > 3600):
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"ATR validation error: {e}")
            return False
