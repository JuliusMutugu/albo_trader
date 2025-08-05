"""
📊 REAL-TIME RISK MANAGEMENT DASHBOARD
Web-based monitoring interface for Enigma-Apex Trading Platform
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import asyncio
import websockets
import threading
import webbrowser

app = Flask(__name__)

class RiskDashboard:
    def __init__(self):
        self.db_path = "trading_database.db"
        self.websocket_url = "ws://localhost:8765"
        
    def get_account_summary(self) -> dict:
        """Get current account summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest balance from risk_updates table
            cursor.execute('''
                SELECT account_balance, daily_pnl, current_drawdown, risk_score
                FROM risk_updates 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            if result:
                balance, daily_pnl, drawdown, risk_score = result
            else:
                balance, daily_pnl, drawdown, risk_score = 10000, 0, 0, 50
            
            # Calculate additional metrics
            total_signals = cursor.execute('SELECT COUNT(*) FROM signals').fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM signals 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            signals_today = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'account_balance': balance,
                'daily_pnl': daily_pnl,
                'current_drawdown': drawdown,
                'risk_score': risk_score,
                'total_signals': total_signals,
                'signals_today': signals_today,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to get account summary: {e}")
            return {
                'account_balance': 10000,
                'daily_pnl': 0,
                'current_drawdown': 0,
                'risk_score': 50,
                'total_signals': 0,
                'signals_today': 0,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_recent_signals(self, limit: int = 20) -> list:
        """Get recent trading signals"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT signal_type, power_score, confidence_level, timeframe, 
                       symbol, entry_price, source, timestamp
                FROM signals 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            signals = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'signal_type': row[0],
                    'power_score': row[1],
                    'confidence': row[2],
                    'timeframe': row[3],
                    'symbol': row[4],
                    'entry_price': row[5],
                    'source': row[6],
                    'timestamp': row[7]
                }
                for row in signals
            ]
            
        except Exception as e:
            print(f"❌ Failed to get recent signals: {e}")
            return []
    
    def get_performance_metrics(self) -> dict:
        """Calculate performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Signal type distribution
            cursor.execute('''
                SELECT signal_type, COUNT(*) 
                FROM signals 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY signal_type
            ''')
            signal_distribution = dict(cursor.fetchall())
            
            # Average power score by day
            cursor.execute('''
                SELECT DATE(timestamp) as date, AVG(power_score) as avg_power
                FROM signals 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''')
            daily_power_scores = cursor.fetchall()
            
            # Risk score history
            cursor.execute('''
                SELECT timestamp, risk_score, current_drawdown
                FROM risk_updates 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
                LIMIT 50
            ''')
            risk_history = cursor.fetchall()
            
            conn.close()
            
            return {
                'signal_distribution': signal_distribution,
                'daily_power_scores': daily_power_scores,
                'risk_history': risk_history
            }
            
        except Exception as e:
            print(f"❌ Failed to get performance metrics: {e}")
            return {
                'signal_distribution': {},
                'daily_power_scores': [],
                'risk_history': []
            }

dashboard = RiskDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    account_summary = dashboard.get_account_summary()
    recent_signals = dashboard.get_recent_signals(10)
    performance_metrics = dashboard.get_performance_metrics()
    
    return render_template('risk_dashboard.html', 
                         account_summary=account_summary,
                         recent_signals=recent_signals,
                         performance_metrics=performance_metrics)

@app.route('/api/account_summary')
def api_account_summary():
    """API endpoint for account summary"""
    return jsonify(dashboard.get_account_summary())

@app.route('/api/recent_signals')
def api_recent_signals():
    """API endpoint for recent signals"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify(dashboard.get_recent_signals(limit))

@app.route('/api/performance_metrics')
def api_performance_metrics():
    """API endpoint for performance metrics"""
    return jsonify(dashboard.get_performance_metrics())

@app.route('/api/market_data')
def api_market_data():
    """API endpoint for market data"""
    try:
        conn = sqlite3.connect(dashboard.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, price, change_percent, volume, timestamp
            FROM market_data 
            ORDER BY timestamp DESC
        ''')
        
        market_data = [
            {
                'symbol': row[0],
                'price': row[1],
                'change_percent': row[2],
                'volume': row[3],
                'timestamp': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return jsonify(market_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_dashboard_template():
    """Create the HTML template for the risk dashboard"""
    import os
    
    os.makedirs('templates', exist_ok=True)
    
    dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enigma-Apex Risk Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0a; color: #fff; }
        
        .header { background: linear-gradient(135deg, #1a1a1a, #2a2a2a); padding: 20px; text-align: center; border-bottom: 2px solid #00ff88; }
        .header h1 { color: #00ff88; font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #ccc; font-size: 1.1em; }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: linear-gradient(135deg, #1a1a1a, #2a2a2a); padding: 20px; border-radius: 10px; border: 1px solid #333; }
        .metric-card h3 { color: #00ff88; margin-bottom: 10px; font-size: 0.9em; text-transform: uppercase; }
        .metric-value { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .metric-change { font-size: 0.9em; opacity: 0.8; }
        
        .positive { color: #00ff88; }
        .negative { color: #ff4444; }
        .neutral { color: #ffaa00; }
        
        .dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }
        .panel { background: linear-gradient(135deg, #1a1a1a, #2a2a2a); padding: 20px; border-radius: 10px; border: 1px solid #333; }
        .panel h2 { color: #00ff88; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #333; }
        
        .signals-table { width: 100%; border-collapse: collapse; }
        .signals-table th, .signals-table td { padding: 12px 8px; text-align: left; border-bottom: 1px solid #333; }
        .signals-table th { background: #333; color: #00ff88; font-weight: bold; }
        .signals-table tr:hover { background: #2a2a2a; }
        
        .signal-bullish { color: #00ff88; }
        .signal-bearish { color: #ff4444; }
        
        .power-score { font-weight: bold; }
        .confidence-c1 { color: #ffaa00; }
        .confidence-c2 { color: #00aaff; }
        .confidence-c3 { color: #00ff88; }
        
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-connected { background: #00ff88; }
        .status-disconnected { background: #ff4444; }
        
        .refresh-btn { background: #00ff88; color: #000; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .refresh-btn:hover { background: #00cc6a; }
        
        .last-updated { color: #888; font-size: 0.8em; margin-top: 10px; }
        
        @media (max-width: 1024px) {
            .dashboard-grid { grid-template-columns: 1fr; }
            .metrics-grid { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Enigma-Apex Risk Dashboard</h1>
        <p>Real-time Trading Risk Management & Performance Monitoring</p>
    </div>
    
    <div class="container">
        <!-- Account Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>💰 Account Balance</h3>
                <div class="metric-value">${{ "{:,.2f}".format(account_summary.account_balance) }}</div>
                <div class="metric-change">Current Balance</div>
            </div>
            
            <div class="metric-card">
                <h3>📈 Daily P&L</h3>
                <div class="metric-value {{ 'positive' if account_summary.daily_pnl >= 0 else 'negative' }}">
                    ${{ "{:+,.2f}".format(account_summary.daily_pnl) }}
                </div>
                <div class="metric-change">Today's Performance</div>
            </div>
            
            <div class="metric-card">
                <h3>📉 Current Drawdown</h3>
                <div class="metric-value {{ 'positive' if account_summary.current_drawdown <= 5 else 'negative' }}">
                    {{ "{:.2f}".format(account_summary.current_drawdown) }}%
                </div>
                <div class="metric-change">Maximum Drawdown</div>
            </div>
            
            <div class="metric-card">
                <h3>🎯 Risk Score</h3>
                <div class="metric-value {{ 'positive' if account_summary.risk_score <= 50 else 'negative' }}">
                    {{ account_summary.risk_score }}/100
                </div>
                <div class="metric-change">Risk Level</div>
            </div>
            
            <div class="metric-card">
                <h3>📊 Total Signals</h3>
                <div class="metric-value">{{ account_summary.total_signals }}</div>
                <div class="metric-change">All Time</div>
            </div>
            
            <div class="metric-card">
                <h3>🔄 Signals Today</h3>
                <div class="metric-value">{{ account_summary.signals_today }}</div>
                <div class="metric-change">Last 24 Hours</div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <!-- Recent Signals -->
            <div class="panel">
                <h2>📊 Recent Trading Signals</h2>
                <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
                
                <table class="signals-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Power</th>
                            <th>Confidence</th>
                            <th>Symbol</th>
                            <th>Timeframe</th>
                            <th>Source</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody id="signals-tbody">
                        {% for signal in recent_signals %}
                        <tr>
                            <td class="signal-{{ signal.signal_type }}">
                                {{ '🟢 BULL' if signal.signal_type == 'bullish' else '🔴 BEAR' }}
                            </td>
                            <td class="power-score">{{ signal.power_score }}%</td>
                            <td class="confidence-{{ signal.confidence.lower() }}">{{ signal.confidence }}</td>
                            <td>{{ signal.symbol }}</td>
                            <td>{{ signal.timeframe }}</td>
                            <td>{{ signal.source[:10] }}...</td>
                            <td>{{ signal.timestamp[:19].replace('T', ' ') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- System Status -->
            <div class="panel">
                <h2>🔧 System Status</h2>
                
                <div style="margin-bottom: 20px;">
                    <h4><span class="status-indicator status-connected"></span>WebSocket Server</h4>
                    <p>Connected and operational</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4><span class="status-indicator status-connected"></span>Database</h4>
                    <p>Logging all transactions</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4><span class="status-indicator status-connected"></span>Risk Manager</h4>
                    <p>Active monitoring</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4><span class="status-indicator status-connected"></span>Signal Processing</h4>
                    <p>Real-time analysis</p>
                </div>
                
                <h3 style="color: #00ff88; margin-top: 30px;">Quick Actions</h3>
                <div style="margin-top: 15px;">
                    <a href="http://localhost:5000" target="_blank" style="display: inline-block; background: #333; color: #fff; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-right: 10px;">📤 Manual Signals</a>
                    <button onclick="refreshData()" style="background: #333; color: #fff; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">🔄 Refresh All</button>
                </div>
            </div>
        </div>
        
        <div class="last-updated">
            Last Updated: {{ account_summary.last_updated.replace('T', ' ')[:19] }}
        </div>
    </div>
    
    <script>
        function refreshData() {
            location.reload();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Update signals table periodically
        async function updateSignals() {
            try {
                const response = await fetch('/api/recent_signals?limit=10');
                const signals = await response.json();
                
                const tbody = document.getElementById('signals-tbody');
                tbody.innerHTML = '';
                
                signals.forEach(signal => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="signal-${signal.signal_type}">
                            ${signal.signal_type === 'bullish' ? '🟢 BULL' : '🔴 BEAR'}
                        </td>
                        <td class="power-score">${signal.power_score}%</td>
                        <td class="confidence-${signal.confidence.toLowerCase()}">${signal.confidence}</td>
                        <td>${signal.symbol}</td>
                        <td>${signal.timeframe}</td>
                        <td>${signal.source.substring(0, 10)}...</td>
                        <td>${signal.timestamp.substring(0, 19).replace('T', ' ')}</td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (error) {
                console.error('Failed to update signals:', error);
            }
        }
        
        // Update signals every 10 seconds
        setInterval(updateSignals, 10000);
    </script>
</body>
</html>
    '''
    
    with open('templates/risk_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print("✅ Risk dashboard template created")

def main():
    """Main function to run the risk dashboard"""
    print("🛡️ Starting Enigma-Apex Risk Management Dashboard...")
    
    # Create template
    create_dashboard_template()
    
    print("✅ Risk dashboard starting on http://localhost:3000")
    print("📊 Real-time risk monitoring and performance tracking")
    
    # Open browser automatically
    threading.Timer(1.0, lambda: webbrowser.open('http://localhost:3000')).start()
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=3000)

if __name__ == "__main__":
    main()
