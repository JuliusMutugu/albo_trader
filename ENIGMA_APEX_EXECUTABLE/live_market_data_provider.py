"""
🚀 LIVE MARKET DATA INTEGRATION
Real-time market data feeds for Enigma-Apex Trading Platform
"""

import asyncio
import websockets
import requests
import json
import sqlite3
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Any
import yfinance as yf
import pandas as pd

class LiveMarketDataProvider:
    def __init__(self):
        self.websocket_url = "ws://localhost:8765"
        self.db_path = "trading_database.db"
        self.is_running = False
        self.symbols = ['ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'EURUSD=X', 'GBPUSD=X']
        self.market_data = {}
        self.update_interval = 5  # seconds
        
    def initialize_database(self):
        """Initialize market data tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create market_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume INTEGER,
                    change_percent REAL,
                    high_24h REAL,
                    low_24h REAL,
                    timestamp TEXT NOT NULL,
                    UNIQUE(symbol, timestamp)
                )
            ''')
            
            # Create technical_indicators table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    indicator_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    period INTEGER,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Market data database tables initialized")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
    
    def fetch_yahoo_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current data
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            
            market_data = {
                'symbol': symbol,
                'price': float(latest['Close']),
                'volume': int(latest['Volume']) if 'Volume' in latest else 0,
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'open': float(latest['Open']),
                'change_percent': ((float(latest['Close']) - float(latest['Open'])) / float(latest['Open'])) * 100,
                'timestamp': datetime.now().isoformat()
            }
            
            return market_data
            
        except Exception as e:
            print(f"❌ Failed to fetch data for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, symbol: str) -> Dict[str, float]:
        """Calculate basic technical indicators"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="5m")
            
            if len(hist) < 20:
                return {}
            
            # Calculate indicators
            indicators = {}
            
            # Simple Moving Averages
            indicators['sma_20'] = hist['Close'].rolling(window=20).mean().iloc[-1]
            indicators['sma_50'] = hist['Close'].rolling(window=min(50, len(hist))).mean().iloc[-1]
            
            # RSI (simplified)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
            
            # MACD (simplified)
            ema_12 = hist['Close'].ewm(span=12).mean()
            ema_26 = hist['Close'].ewm(span=26).mean()
            indicators['macd'] = ema_12.iloc[-1] - ema_26.iloc[-1]
            
            return indicators
            
        except Exception as e:
            print(f"❌ Technical indicators calculation failed for {symbol}: {e}")
            return {}
    
    def store_market_data(self, data: Dict[str, Any]) -> None:
        """Store market data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_data 
                (symbol, price, volume, change_percent, high_24h, low_24h, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['symbol'],
                data['price'],
                data['volume'],
                data['change_percent'],
                data['high'],
                data['low'],
                data['timestamp']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to store market data: {e}")
    
    def store_technical_indicators(self, symbol: str, indicators: Dict[str, float]) -> None:
        """Store technical indicators in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            for indicator_type, value in indicators.items():
                if pd.notna(value):  # Only store valid values
                    cursor.execute('''
                        INSERT INTO technical_indicators 
                        (symbol, indicator_type, value, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (symbol, indicator_type, float(value), timestamp))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to store technical indicators: {e}")
    
    async def send_market_data_to_server(self, data: Dict[str, Any]) -> None:
        """Send market data to WebSocket server"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                message = {
                    'type': 'market_data',
                    'source': 'live_market_feed',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send(json.dumps(message))
                
        except Exception as e:
            print(f"❌ Failed to send market data to server: {e}")
    
    def generate_trading_signals(self, symbol: str, data: Dict[str, Any], indicators: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate basic trading signals based on market data and indicators"""
        signals = []
        
        try:
            # Simple signal generation logic
            current_price = data['price']
            change_percent = data['change_percent']
            
            # RSI-based signals
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi < 30 and change_percent > -2:  # Oversold but not crashing
                    signals.append({
                        'signal_type': 'bullish',
                        'power_score': min(85, 70 + abs(30 - rsi)),
                        'reason': f'RSI Oversold ({rsi:.1f})',
                        'confidence': 'C2',
                        'timeframe': 'M15'
                    })
                elif rsi > 70 and change_percent < 2:  # Overbought but not mooning
                    signals.append({
                        'signal_type': 'bearish',
                        'power_score': min(85, 70 + abs(rsi - 70)),
                        'reason': f'RSI Overbought ({rsi:.1f})',
                        'confidence': 'C2',
                        'timeframe': 'M15'
                    })
            
            # Moving Average crossover signals
            if 'sma_20' in indicators and 'sma_50' in indicators:
                sma_20 = indicators['sma_20']
                sma_50 = indicators['sma_50']
                
                if current_price > sma_20 > sma_50 and change_percent > 0:
                    signals.append({
                        'signal_type': 'bullish',
                        'power_score': 75,
                        'reason': 'Price above MA20 > MA50',
                        'confidence': 'C3',
                        'timeframe': 'H1'
                    })
                elif current_price < sma_20 < sma_50 and change_percent < 0:
                    signals.append({
                        'signal_type': 'bearish',
                        'power_score': 75,
                        'reason': 'Price below MA20 < MA50',
                        'confidence': 'C3',
                        'timeframe': 'H1'
                    })
            
            # Volume spike signals
            if data['volume'] > 0:
                # This is simplified - in real implementation, compare to average volume
                if change_percent > 1 and data['volume'] > 1000000:  # High volume + positive movement
                    signals.append({
                        'signal_type': 'bullish',
                        'power_score': 80,
                        'reason': 'High volume breakout',
                        'confidence': 'C2',
                        'timeframe': 'M30'
                    })
            
            # Add symbol and timestamp to all signals
            for signal in signals:
                signal['symbol'] = symbol
                signal['entry_price'] = current_price
                signal['timestamp'] = datetime.now().isoformat()
            
            return signals
            
        except Exception as e:
            print(f"❌ Signal generation failed for {symbol}: {e}")
            return []
    
    async def process_symbol(self, symbol: str) -> None:
        """Process market data for a single symbol"""
        try:
            # Fetch market data
            market_data = self.fetch_yahoo_data(symbol)
            if not market_data:
                return
            
            # Store market data
            self.store_market_data(market_data)
            self.market_data[symbol] = market_data
            
            # Calculate technical indicators
            indicators = self.calculate_technical_indicators(symbol)
            if indicators:
                self.store_technical_indicators(symbol, indicators)
            
            # Generate trading signals
            signals = self.generate_trading_signals(symbol, market_data, indicators)
            
            # Send market data to server
            await self.send_market_data_to_server(market_data)
            
            # Send signals to server
            for signal in signals:
                await self.send_signal_to_server(signal)
            
            print(f"✅ Processed {symbol}: ${market_data['price']:.2f} ({market_data['change_percent']:+.2f}%) - {len(signals)} signals")
            
        except Exception as e:
            print(f"❌ Failed to process {symbol}: {e}")
    
    async def send_signal_to_server(self, signal: Dict[str, Any]) -> None:
        """Send trading signal to WebSocket server"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                message = {
                    'type': 'signal',
                    'source': 'live_market_analysis',
                    'data': signal,
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send(json.dumps(message))
                print(f"📊 Signal sent: {signal['signal_type'].upper()} {signal['symbol']} at {signal['power_score']}%")
                
        except Exception as e:
            print(f"❌ Failed to send signal to server: {e}")
    
    async def run_market_data_loop(self) -> None:
        """Main market data processing loop"""
        print("🚀 Starting live market data processing...")
        
        while self.is_running:
            try:
                # Process all symbols
                tasks = [self.process_symbol(symbol) for symbol in self.symbols]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                print(f"❌ Market data loop error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def start(self) -> None:
        """Start the market data provider"""
        self.initialize_database()
        self.is_running = True
        
        # Run the async loop in a separate thread
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_market_data_loop())
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        
        print("✅ Live market data provider started")
        print(f"📊 Monitoring symbols: {', '.join(self.symbols)}")
        print(f"🔄 Update interval: {self.update_interval} seconds")
        
        return thread
    
    def stop(self) -> None:
        """Stop the market data provider"""
        self.is_running = False
        print("⏹️ Market data provider stopped")
    
    def get_latest_data(self, symbol: str = None) -> Dict[str, Any]:
        """Get latest market data for symbol or all symbols"""
        if symbol:
            return self.market_data.get(symbol, {})
        return self.market_data

def main():
    """Main function to run the live market data provider"""
    print("🚀 Enigma-Apex Live Market Data Provider")
    print("=" * 50)
    
    provider = LiveMarketDataProvider()
    
    try:
        # Start the provider
        thread = provider.start()
        
        print("\n✅ Market data provider is running!")
        print("📊 Real-time data is being processed and sent to WebSocket server")
        print("🔄 Trading signals will be generated automatically")
        print("\nPress Ctrl+C to stop...")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping market data provider...")
        provider.stop()
        print("✅ Market data provider stopped successfully")

if __name__ == "__main__":
    main()
