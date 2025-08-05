"""
🎯 APEX GUARDIAN AGENT - PRODUCTION READY
Complete implementation of Michael Canfield's ChatGPT Agent vision
First Principles: Profit Extension + Loss Minimization + Kelly Optimization
"""

import asyncio
import json
import sqlite3
import websockets
import numpy as np
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
import logging
import time

# Import our modules
from ocr_enigma_reader import OCRSignalReader, EnigmaSignal
from chatgpt_agent_integration import FirstPrinciplesAI, EnigmaApexAIAgent

@dataclass
class ApexRules:
    """Apex Prop Firm compliance rules"""
    max_daily_loss_pct: float = 0.04  # 4% max daily loss
    max_loss_per_trade_pct: float = 0.02  # 2% max per trade
    max_contracts_per_symbol: int = 5
    trailing_threshold_pct: float = 0.25  # 25% of account for trailing
    consistency_score_min: float = 0.6
    max_correlation_trades: int = 3

@dataclass
class KellyParameters:
    """Kelly Criterion parameters"""
    base_win_rate: float = 0.5
    atr_stop_multiplier: float = 1.5
    atr_target_multiplier: float = 2.0
    max_kelly_fraction: float = 0.25  # 25% max position
    safety_factor: float = 0.5  # Half-Kelly for safety
    min_kelly_threshold: float = 0.01  # 1% minimum for trade

@dataclass
class TradeDecision:
    """Trade decision output"""
    action: str  # "TRADE", "NO_TRADE", "CAUTIOUS_TRADE"
    confidence: float
    position_size_pct: float
    stop_loss_points: float
    profit_target_points: float
    reasoning: List[str]
    risk_level: str
    kelly_fraction: float
    apex_compliant: bool

class ApexGuardianAgent:
    """
    Main Guardian Agent implementing Michael's complete vision:
    - OCR reading of AlgoBox Enigma
    - ChatGPT first principles analysis
    - Kelly Criterion dynamic sizing
    - Apex prop firm compliance
    - Real-time decision making
    """
    
    def __init__(self):
        # Initialize logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.ocr_reader = OCRSignalReader()
        self.ai_agent = EnigmaApexAIAgent()
        self.apex_rules = ApexRules()
        self.kelly_params = KellyParameters()
        
        # State tracking
        self.current_account_balance = 100000  # $100k default
        self.daily_pnl = 0.0
        self.open_positions = {}
        self.trade_history = deque(maxlen=100)
        self.current_drawdown = 0.0
        
        # Performance metrics
        self.performance_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.5,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 1.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        }
        
        # Initialize database after logging is set up
        self.init_database()
        
        self.logger.info("🛡️ Apex Guardian Agent initialized")
        self.logger.info("🎯 Ready for first principles trading optimization")
    
    def init_database(self):
        """Initialize Guardian Agent database"""
        try:
            self.db = sqlite3.connect('apex_guardian.db')
            cursor = self.db.cursor()
            
            # Trade decisions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT,
                    action TEXT,
                    confidence REAL,
                    position_size_pct REAL,
                    kelly_fraction REAL,
                    power_score INTEGER,
                    confluence_level TEXT,
                    cadence_failures INTEGER,
                    atr_value REAL,
                    stop_loss REAL,
                    profit_target REAL,
                    reasoning TEXT,
                    apex_compliant BOOLEAN
                )
            ''')
            
            # Performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    trade_outcome TEXT,
                    pnl REAL,
                    win_rate REAL,
                    kelly_fraction REAL,
                    account_balance REAL,
                    daily_pnl REAL,
                    max_drawdown REAL
                )
            ''')
            
            # Cadence tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cadence_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session TEXT,
                    failure_count INTEGER,
                    threshold_met BOOLEAN,
                    signal_power INTEGER,
                    confluence_level TEXT,
                    trade_taken BOOLEAN
                )
            ''')
            
            self.db.commit()
            self.logger.info("✅ Guardian database initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
    
    def calculate_dynamic_kelly(self, signal: EnigmaSignal) -> float:
        """Calculate dynamic Kelly fraction based on current performance"""
        try:
            # Get current win rate from trade history
            if len(self.trade_history) > 0:
                win_rate = sum(self.trade_history) / len(self.trade_history)
            else:
                win_rate = self.kelly_params.base_win_rate
            
            # Calculate reward-to-risk ratio from ATR
            if signal.atr_value > 0:
                stop_loss = signal.atr_value * self.kelly_params.atr_stop_multiplier
                profit_target = signal.atr_value * self.kelly_params.atr_target_multiplier
                rr_ratio = profit_target / stop_loss
            else:
                rr_ratio = self.kelly_params.atr_target_multiplier / self.kelly_params.atr_stop_multiplier
            
            # Kelly formula: f = (bp - q) / b
            # where b = reward/risk ratio, p = win probability, q = loss probability
            kelly_fraction = (rr_ratio * win_rate - (1 - win_rate)) / rr_ratio
            
            # Apply safety factor (half-Kelly)
            kelly_fraction *= self.kelly_params.safety_factor
            
            # Apply limits
            kelly_fraction = max(0, min(self.kelly_params.max_kelly_fraction, kelly_fraction))
            
            return kelly_fraction
            
        except Exception as e:
            self.logger.error(f"❌ Kelly calculation failed: {e}")
            return 0.01  # Conservative fallback
    
    def check_apex_compliance(self, position_size_pct: float, symbol: str) -> Dict:
        """Check Apex prop firm compliance"""
        compliance = {
            "compliant": True,
            "violations": [],
            "warnings": []
        }
        
        # Daily loss limit check
        daily_loss_pct = abs(self.daily_pnl) / self.current_account_balance
        if daily_loss_pct > self.apex_rules.max_daily_loss_pct * 0.8:  # 80% of limit
            compliance["warnings"].append(f"Approaching daily loss limit: {daily_loss_pct:.2%}")
        
        if daily_loss_pct > self.apex_rules.max_daily_loss_pct:
            compliance["compliant"] = False
            compliance["violations"].append("Daily loss limit exceeded")
        
        # Position size check
        if position_size_pct > self.apex_rules.max_loss_per_trade_pct:
            compliance["compliant"] = False
            compliance["violations"].append(f"Position size too large: {position_size_pct:.2%}")
        
        # Max contracts per symbol
        current_contracts = self.open_positions.get(symbol, 0)
        if current_contracts >= self.apex_rules.max_contracts_per_symbol:
            compliance["compliant"] = False
            compliance["violations"].append(f"Max contracts reached for {symbol}")
        
        # Drawdown check
        if self.current_drawdown > self.apex_rules.trailing_threshold_pct:
            compliance["warnings"].append(f"Approaching trailing threshold: {self.current_drawdown:.2%}")
        
        return compliance
    
    def apply_first_principles(self, signal: EnigmaSignal) -> TradeDecision:
        """Apply first principles analysis to make trading decision"""
        try:
            # Calculate Kelly fraction
            kelly_fraction = self.calculate_dynamic_kelly(signal)
            
            # Convert to position size percentage
            position_size_pct = kelly_fraction
            
            # Check Apex compliance
            apex_compliance = self.check_apex_compliance(position_size_pct, "NQ")  # Default symbol
            
            # Calculate stops and targets
            stop_loss_points = signal.atr_value * self.kelly_params.atr_stop_multiplier
            profit_target_points = signal.atr_value * self.kelly_params.atr_target_multiplier
            
            # Apply first principles logic
            reasoning = []
            confidence = 0.0
            action = "NO_TRADE"
            risk_level = "HIGH"
            
            # 1. PROFIT EXTENSION PRINCIPLES
            if signal.confluence_level in ["L3", "L4"]:
                confidence += 0.3
                reasoning.append(f"High confluence: {signal.confluence_level}")
            
            if signal.power_score >= 20:
                confidence += 0.3
                reasoning.append(f"Strong power score: {signal.power_score}")
            elif signal.power_score >= 15:
                confidence += 0.2
                reasoning.append(f"Moderate power score: {signal.power_score}")
            
            if signal.macvu_status == "GREEN":
                confidence += 0.2
                reasoning.append("MACVU filter aligned")
            
            # 2. LOSS MINIMIZATION PRINCIPLES
            loss_signals = []
            
            if signal.power_score < 10:
                loss_signals.append("Power score too low")
            
            if signal.confluence_level in ["L0", "L1"]:
                loss_signals.append("Confluence too low")
            
            if signal.macvu_status == "RED":
                loss_signals.append("MACVU against trend")
            
            if not apex_compliance["compliant"]:
                loss_signals.append("Apex compliance violation")
            
            # 3. CADENCE LOGIC
            cadence_threshold = 2 if signal.session == "AM" else 3
            if signal.cadence_failures >= cadence_threshold:
                confidence += 0.3
                reasoning.append(f"Cadence threshold met: {signal.cadence_failures} failures")
            
            # 4. KELLY CRITERION APPLICATION
            if kelly_fraction < self.kelly_params.min_kelly_threshold:
                loss_signals.append("Kelly fraction too low")
            
            # 5. DECISION LOGIC
            if loss_signals:
                action = "NO_TRADE"
                reasoning.extend(loss_signals)
                risk_level = "HIGH"
            elif confidence >= 0.7 and kelly_fraction > 0.02:
                action = "TRADE"
                risk_level = "LOW"
            elif confidence >= 0.5 and kelly_fraction > 0.01:
                action = "CAUTIOUS_TRADE"
                position_size_pct *= 0.5  # Reduce size for cautious trades
                risk_level = "MEDIUM"
            
            # Create trade decision
            decision = TradeDecision(
                action=action,
                confidence=confidence,
                position_size_pct=position_size_pct,
                stop_loss_points=stop_loss_points,
                profit_target_points=profit_target_points,
                reasoning=reasoning,
                risk_level=risk_level,
                kelly_fraction=kelly_fraction,
                apex_compliant=apex_compliance["compliant"]
            )
            
            # Log decision to database
            self.log_trade_decision(signal, decision)
            
            return decision
            
        except Exception as e:
            self.logger.error(f"❌ First principles analysis failed: {e}")
            return TradeDecision(
                action="NO_TRADE",
                confidence=0.0,
                position_size_pct=0.0,
                stop_loss_points=0.0,
                profit_target_points=0.0,
                reasoning=["Analysis error"],
                risk_level="HIGH",
                kelly_fraction=0.0,
                apex_compliant=False
            )
    
    def log_trade_decision(self, signal: EnigmaSignal, decision: TradeDecision):
        """Log trade decision to database"""
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO trade_decisions 
                (symbol, action, confidence, position_size_pct, kelly_fraction, 
                 power_score, confluence_level, cadence_failures, atr_value,
                 stop_loss, profit_target, reasoning, apex_compliant)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "NQ",  # Default symbol
                decision.action,
                decision.confidence,
                decision.position_size_pct,
                decision.kelly_fraction,
                signal.power_score,
                signal.confluence_level,
                signal.cadence_failures,
                signal.atr_value,
                decision.stop_loss_points,
                decision.profit_target_points,
                json.dumps(decision.reasoning),
                decision.apex_compliant
            ))
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to log trade decision: {e}")
    
    def update_performance(self, trade_outcome: str, pnl: float):
        """Update performance metrics after trade completion"""
        try:
            # Update trade history
            win = 1 if trade_outcome == "WIN" else 0
            self.trade_history.append(win)
            
            # Update account metrics
            self.daily_pnl += pnl
            self.current_account_balance += pnl
            
            # Update performance stats
            self.performance_stats["total_trades"] += 1
            if win:
                self.performance_stats["winning_trades"] += 1
            else:
                self.performance_stats["losing_trades"] += 1
            
            self.performance_stats["win_rate"] = (
                self.performance_stats["winning_trades"] / self.performance_stats["total_trades"]
            )
            
            # Update drawdown
            if pnl < 0:
                self.current_drawdown = max(self.current_drawdown, abs(pnl) / self.current_account_balance)
            
            # Log to database
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO performance_log 
                (trade_outcome, pnl, win_rate, account_balance, daily_pnl, max_drawdown)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                trade_outcome,
                pnl,
                self.performance_stats["win_rate"],
                self.current_account_balance,
                self.daily_pnl,
                self.current_drawdown
            ))
            self.db.commit()
            
            self.logger.info(f"📊 Performance updated: {trade_outcome}, PnL: ${pnl:.2f}, "
                           f"Win Rate: {self.performance_stats['win_rate']:.2%}")
            
        except Exception as e:
            self.logger.error(f"❌ Performance update failed: {e}")
    
    async def run_continuous_analysis(self):
        """Run continuous signal analysis and decision making"""
        self.logger.info("🚀 Starting continuous Guardian analysis")
        
        # WebSocket server for sending decisions
        websocket_url = "ws://localhost:8765"
        
        while True:
            try:
                # Read current Enigma signal
                signal = self.ocr_reader.read_full_panel()
                
                if signal is None:
                    await asyncio.sleep(2)
                    continue
                
                # Apply first principles analysis
                decision = self.apply_first_principles(signal)
                
                # Create message for NinjaTrader
                message = {
                    "type": "guardian_decision",
                    "timestamp": datetime.now().isoformat(),
                    "signal_data": asdict(signal),
                    "decision": asdict(decision),
                    "performance": self.performance_stats.copy()
                }
                
                # Send to NinjaTrader via WebSocket
                try:
                    async with websockets.connect(websocket_url) as websocket:
                        await websocket.send(json.dumps(message, cls=DateTimeEncoder))
                        
                        # Log significant decisions
                        if decision.action == "TRADE":
                            self.logger.info(f"🎯 TRADE SIGNAL: {decision.action} "
                                           f"(Confidence: {decision.confidence:.2%}, "
                                           f"Size: {decision.position_size_pct:.2%})")
                        elif decision.action == "CAUTIOUS_TRADE":
                            self.logger.info(f"⚠️ CAUTIOUS TRADE: {decision.action} "
                                           f"(Confidence: {decision.confidence:.2%})")
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to send decision: {e}")
                
                # Wait before next analysis
                await asyncio.sleep(3)  # 3-second intervals
                
            except Exception as e:
                self.logger.error(f"❌ Analysis error: {e}")
                await asyncio.sleep(5)
    
    def generate_daily_report(self) -> Dict:
        """Generate daily performance report"""
        try:
            cursor = self.db.cursor()
            
            # Get today's trades
            today = datetime.now().date()
            cursor.execute('''
                SELECT COUNT(*), SUM(CASE WHEN trade_outcome = 'WIN' THEN 1 ELSE 0 END)
                FROM performance_log
                WHERE DATE(timestamp) = ?
            ''', (today,))
            
            total_trades, wins = cursor.fetchone()
            win_rate = wins / total_trades if total_trades > 0 else 0
            
            # Get today's PnL
            cursor.execute('''
                SELECT SUM(pnl) FROM performance_log
                WHERE DATE(timestamp) = ?
            ''', (today,))
            
            daily_pnl = cursor.fetchone()[0] or 0
            
            report = {
                "date": today.isoformat(),
                "total_trades": total_trades,
                "winning_trades": wins,
                "win_rate": win_rate,
                "daily_pnl": daily_pnl,
                "account_balance": self.current_account_balance,
                "max_drawdown": self.current_drawdown,
                "apex_compliant": daily_pnl > -self.current_account_balance * self.apex_rules.max_daily_loss_pct
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {e}")
            return {}
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "account_balance": self.current_account_balance,
            "daily_pnl": self.daily_pnl,
            "current_drawdown": self.current_drawdown,
            "performance_stats": self.performance_stats,
            "apex_compliance": {
                "daily_loss_limit": self.apex_rules.max_daily_loss_pct,
                "current_daily_loss": abs(self.daily_pnl) / self.current_account_balance,
                "compliant": abs(self.daily_pnl) < self.current_account_balance * self.apex_rules.max_daily_loss_pct
            },
            "kelly_params": asdict(self.kelly_params),
            "trade_history_length": len(self.trade_history)
        }

async def main():
    """Main function to run Guardian Agent"""
    guardian = ApexGuardianAgent()
    
    try:
        # Start continuous analysis
        await guardian.run_continuous_analysis()
        
    except KeyboardInterrupt:
        print("\n🛑 Guardian Agent stopped by user")
    except Exception as e:
        print(f"❌ Guardian Agent error: {e}")
    finally:
        if guardian.db:
            guardian.db.close()

if __name__ == "__main__":
    print("🛡️ APEX GUARDIAN AGENT - PRODUCTION READY")
    print("=" * 50)
    print("🎯 Michael Canfield's ChatGPT Agent Vision")
    print("📊 First Principles: Profit Extension + Loss Minimization")
    print("💰 Kelly Criterion Dynamic Sizing")
    print("🏛️ Apex Prop Firm Compliance")
    print("🔍 OCR AlgoBox Enigma Integration")
    print()
    
    asyncio.run(main())
