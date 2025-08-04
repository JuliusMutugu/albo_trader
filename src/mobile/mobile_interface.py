"""
Enigma-Apex Mobile Interface Server
FastAPI server providing secure mobile control and monitoring
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import json
import jwt
import hashlib
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

# Import our core components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.guardian_engine import GuardianEngine
from src.core.config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "enigma-apex-mobile-secret-2024"  # In production, use environment variable
security = HTTPBearer()

@dataclass
class MobileUser:
    """Mobile user authentication data"""
    username: str
    hashed_password: str
    permissions: List[str]
    device_id: str
    last_login: datetime

@dataclass
class DashboardData:
    """Complete dashboard data for mobile interface"""
    timestamp: datetime
    trading_enabled: bool
    emergency_stop: bool
    enigma_data: dict
    kelly_data: dict
    compliance_data: dict
    cadence_data: dict
    account_data: dict
    system_status: dict

class MobileInterfaceServer:
    """
    FastAPI server providing secure mobile interface for Enigma-Apex system
    Features:
    - JWT authentication
    - Real-time WebSocket updates
    - Secure trading controls
    - Emergency stop functionality
    - Complete dashboard monitoring
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="Enigma-Apex Mobile Interface",
            description="Professional mobile trading control panel",
            version="1.0.0"
        )
        
        # CORS configuration for mobile apps
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.guardian_engine = None
        
        # Connected WebSocket clients
        self.active_connections: List[WebSocket] = []
        
        # User management (in production, use proper database)
        self.users: Dict[str, MobileUser] = {
            "trader1": MobileUser(
                username="trader1",
                hashed_password=self._hash_password("secure123"),
                permissions=["view", "trade", "emergency_stop"],
                device_id="",
                last_login=datetime.utcnow()
            )
        }
        
        # Setup routes
        self._setup_routes()
        
        # Dashboard data cache
        self.current_dashboard_data: Optional[DashboardData] = None
        
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == hashed
    
    def _create_jwt_token(self, username: str) -> str:
        """Create JWT token for authenticated user"""
        payload = {
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    def _verify_jwt_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return username"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload.get("username")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def _get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """Get current authenticated user"""
        username = self._verify_jwt_token(credentials.credentials)
        if not username or username not in self.users:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return username
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with mobile interface HTML"""
            return HTMLResponse(self._get_mobile_interface_html())
        
        @self.app.post("/auth/login")
        async def login(credentials: dict):
            """Authenticate user and return JWT token"""
            username = credentials.get("username")
            password = credentials.get("password")
            device_id = credentials.get("device_id", "")
            
            if not username or not password:
                raise HTTPException(status_code=400, detail="Username and password required")
            
            user = self.users.get(username)
            if not user or not self._verify_password(password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Update device ID and last login
            user.device_id = device_id
            user.last_login = datetime.utcnow()
            
            token = self._create_jwt_token(username)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "permissions": user.permissions,
                "expires_in": 86400  # 24 hours
            }
        
        @self.app.get("/api/dashboard")
        async def get_dashboard_data(current_user: str = Depends(self._get_current_user)):
            """Get complete dashboard data"""
            if not self.current_dashboard_data:
                # Initialize with default data if guardian not running
                self.current_dashboard_data = DashboardData(
                    timestamp=datetime.utcnow(),
                    trading_enabled=False,
                    emergency_stop=False,
                    enigma_data={
                        "power_score": 0,
                        "confluence_level": "L1",
                        "signal_color": "NEUTRAL",
                        "macvu_state": "NEUTRAL"
                    },
                    kelly_data={
                        "half_kelly_percentage": 0,
                        "position_size": 0,
                        "confidence": 0
                    },
                    compliance_data={
                        "overall_level": "unknown",
                        "trading_enabled": False,
                        "daily_loss": 0,
                        "max_loss": 0
                    },
                    cadence_data={
                        "morning_failures": 0,
                        "afternoon_failures": 0,
                        "last_signal_time": None
                    },
                    account_data={
                        "balance": 50000,
                        "daily_pnl": 0,
                        "total_pnl": 0
                    },
                    system_status={
                        "guardian_running": False,
                        "ocr_status": "inactive",
                        "websocket_connected": False
                    }
                )
            
            return asdict(self.current_dashboard_data)
        
        @self.app.post("/api/trading/enable")
        async def enable_trading(current_user: str = Depends(self._get_current_user)):
            """Enable trading"""
            user = self.users[current_user]
            if "trade" not in user.permissions:
                raise HTTPException(status_code=403, detail="Trading permission required")
            
            if self.guardian_engine:
                await self.guardian_engine.enable_trading()
                logger.info(f"Trading enabled by {current_user}")
                return {"status": "success", "message": "Trading enabled"}
            else:
                raise HTTPException(status_code=503, detail="Guardian engine not available")
        
        @self.app.post("/api/trading/disable")
        async def disable_trading(current_user: str = Depends(self._get_current_user)):
            """Disable trading"""
            user = self.users[current_user]
            if "trade" not in user.permissions:
                raise HTTPException(status_code=403, detail="Trading permission required")
            
            if self.guardian_engine:
                await self.guardian_engine.disable_trading()
                logger.info(f"Trading disabled by {current_user}")
                return {"status": "success", "message": "Trading disabled"}
            else:
                raise HTTPException(status_code=503, detail="Guardian engine not available")
        
        @self.app.post("/api/emergency_stop")
        async def emergency_stop(current_user: str = Depends(self._get_current_user)):
            """Trigger emergency stop"""
            user = self.users[current_user]
            if "emergency_stop" not in user.permissions:
                raise HTTPException(status_code=403, detail="Emergency stop permission required")
            
            if self.guardian_engine:
                await self.guardian_engine.emergency_stop(f"Emergency stop triggered by {current_user}")
                logger.warning(f"EMERGENCY STOP triggered by {current_user}")
                
                # Broadcast emergency stop to all connected clients
                await self._broadcast_emergency_stop(current_user)
                
                return {"status": "success", "message": "Emergency stop activated"}
            else:
                raise HTTPException(status_code=503, detail="Guardian engine not available")
        
        @self.app.post("/api/system/restart")
        async def restart_system(current_user: str = Depends(self._get_current_user)):
            """Restart the Guardian system"""
            user = self.users[current_user]
            if "trade" not in user.permissions:
                raise HTTPException(status_code=403, detail="Trading permission required")
            
            if self.guardian_engine:
                await self.guardian_engine.restart_system()
                logger.info(f"System restart initiated by {current_user}")
                return {"status": "success", "message": "System restart initiated"}
            else:
                raise HTTPException(status_code=503, detail="Guardian engine not available")
        
        @self.app.websocket("/ws/dashboard")
        async def websocket_dashboard(websocket: WebSocket):
            """WebSocket endpoint for real-time dashboard updates"""
            await self._websocket_endpoint(websocket)
    
    async def _websocket_endpoint(self, websocket: WebSocket):
        """Handle WebSocket connections for real-time updates"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        try:
            # Send initial dashboard data
            if self.current_dashboard_data:
                await websocket.send_text(json.dumps({
                    "type": "dashboard_update",
                    "data": asdict(self.current_dashboard_data)
                }))
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages (ping/pong, auth, etc.)
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    await websocket.send_text(json.dumps({"type": "ping"}))
                
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    async def update_dashboard_data(self, dashboard_data: DashboardData):
        """Update dashboard data and broadcast to connected clients"""
        self.current_dashboard_data = dashboard_data
        
        # Broadcast to all connected WebSocket clients
        if self.active_connections:
            message = json.dumps({
                "type": "dashboard_update",
                "data": asdict(dashboard_data)
            })
            
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections.remove(conn)
    
    async def _broadcast_emergency_stop(self, triggered_by: str):
        """Broadcast emergency stop to all connected clients"""
        if self.active_connections:
            message = json.dumps({
                "type": "emergency_stop",
                "data": {
                    "triggered_by": triggered_by,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections.remove(conn)
    
    def _get_mobile_interface_html(self) -> str:
        """Generate mobile interface HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enigma-Apex Mobile Control</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-connected { background: #4CAF50; }
        .status-disconnected { background: #F44336; }
        .status-warning { background: #FF9800; }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .card-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        
        .data-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .data-label {
            font-size: 14px;
            opacity: 0.8;
        }
        
        .data-value {
            font-size: 16px;
            font-weight: bold;
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        
        .btn-success {
            background: #4CAF50;
            color: white;
        }
        
        .btn-danger {
            background: #F44336;
            color: white;
        }
        
        .btn-warning {
            background: #FF9800;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .emergency-btn {
            background: #D32F2F !important;
            font-size: 18px;
            padding: 20px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(211, 47, 47, 0); }
            100% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
        }
        
        .login-form {
            display: none;
        }
        
        .login-form.active {
            display: block;
        }
        
        .dashboard {
            display: none;
        }
        
        .dashboard.active {
            display: block;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-size: 14px;
        }
        
        .input-group input {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
        }
        
        .error-message {
            background: rgba(244, 67, 54, 0.9);
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .success-message {
            background: rgba(76, 175, 80, 0.9);
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">ENIGMA-APEX</div>
            <div class="subtitle">Mobile Control Panel</div>
        </div>
        
        <!-- Login Form -->
        <div id="loginForm" class="login-form active">
            <div class="card">
                <div class="card-title">Authentication Required</div>
                <div id="errorMessage" class="error-message" style="display: none;"></div>
                <div class="input-group">
                    <label>Username</label>
                    <input type="text" id="username" placeholder="Enter username">
                </div>
                <div class="input-group">
                    <label>Password</label>
                    <input type="password" id="password" placeholder="Enter password">
                </div>
                <button class="btn btn-success" onclick="login()">Login</button>
            </div>
        </div>
        
        <!-- Dashboard -->
        <div id="dashboard" class="dashboard">
            <!-- Connection Status -->
            <div class="card">
                <div class="card-title">
                    <span id="connectionIndicator" class="status-indicator status-disconnected"></span>
                    System Status
                </div>
                <div class="data-row">
                    <span class="data-label">Guardian Engine</span>
                    <span id="guardianStatus" class="data-value">Disconnected</span>
                </div>
                <div class="data-row">
                    <span class="data-label">OCR Status</span>
                    <span id="ocrStatus" class="data-value">Inactive</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Trading</span>
                    <span id="tradingStatus" class="data-value">Disabled</span>
                </div>
            </div>
            
            <!-- Enigma Signals -->
            <div class="card">
                <div class="card-title">Enigma Signals</div>
                <div class="data-row">
                    <span class="data-label">Power Score</span>
                    <span id="powerScore" class="data-value">0</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Confluence</span>
                    <span id="confluence" class="data-value">L1</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Signal Color</span>
                    <span id="signalColor" class="data-value">NEUTRAL</span>
                </div>
                <div class="data-row">
                    <span class="data-label">MACVU</span>
                    <span id="macvuState" class="data-value">NEUTRAL</span>
                </div>
            </div>
            
            <!-- Kelly & Account -->
            <div class="card">
                <div class="card-title">Position & Account</div>
                <div class="data-row">
                    <span class="data-label">Kelly %</span>
                    <span id="kellyPercentage" class="data-value">0%</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Position Size</span>
                    <span id="positionSize" class="data-value">0</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Account Balance</span>
                    <span id="accountBalance" class="data-value">$50,000</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Daily P&L</span>
                    <span id="dailyPnL" class="data-value">$0.00</span>
                </div>
            </div>
            
            <!-- Trading Controls -->
            <div class="card">
                <div class="card-title">Trading Controls</div>
                <div id="successMessage" class="success-message" style="display: none;"></div>
                <div id="controlErrorMessage" class="error-message" style="display: none;"></div>
                <button id="enableTradingBtn" class="btn btn-success" onclick="enableTrading()">Enable Trading</button>
                <button id="disableTradingBtn" class="btn btn-warning" onclick="disableTrading()">Disable Trading</button>
                <button class="btn btn-danger emergency-btn" onclick="emergencyStop()">EMERGENCY STOP</button>
            </div>
        </div>
    </div>
    
    <script>
        let authToken = null;
        let websocket = null;
        
        function showError(message, elementId = 'errorMessage') {
            const errorElement = document.getElementById(elementId);
            errorElement.textContent = message;
            errorElement.style.display = 'block';
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 5000);
        }
        
        function showSuccess(message) {
            const successElement = document.getElementById('successMessage');
            successElement.textContent = message;
            successElement.style.display = 'block';
            setTimeout(() => {
                successElement.style.display = 'none';
            }, 3000);
        }
        
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                showError('Please enter username and password');
                return;
            }
            
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password,
                        device_id: 'mobile_web'
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    authToken = data.access_token;
                    document.getElementById('loginForm').classList.remove('active');
                    document.getElementById('dashboard').classList.add('active');
                    connectWebSocket();
                    loadDashboard();
                } else {
                    showError(data.detail || 'Login failed');
                }
            } catch (error) {
                showError('Connection error: ' + error.message);
            }
        }
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function() {
                updateConnectionStatus(true);
            };
            
            websocket.onmessage = function(event) {
                const message = JSON.parse(event.data);
                
                if (message.type === 'dashboard_update') {
                    updateDashboard(message.data);
                } else if (message.type === 'emergency_stop') {
                    showError('EMERGENCY STOP ACTIVATED by ' + message.data.triggered_by, 'controlErrorMessage');
                    updateTradingControls(false, true);
                } else if (message.type === 'ping') {
                    websocket.send(JSON.stringify({type: 'pong'}));
                }
            };
            
            websocket.onclose = function() {
                updateConnectionStatus(false);
                // Attempt to reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }
        
        function updateConnectionStatus(connected) {
            const indicator = document.getElementById('connectionIndicator');
            const status = document.getElementById('guardianStatus');
            
            if (connected) {
                indicator.className = 'status-indicator status-connected';
                status.textContent = 'Connected';
            } else {
                indicator.className = 'status-indicator status-disconnected';
                status.textContent = 'Disconnected';
            }
        }
        
        async function loadDashboard() {
            try {
                const response = await fetch('/api/dashboard', {
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateDashboard(data);
                }
            } catch (error) {
                console.error('Failed to load dashboard:', error);
            }
        }
        
        function updateDashboard(data) {
            // Update Enigma signals
            document.getElementById('powerScore').textContent = data.enigma_data.power_score;
            document.getElementById('confluence').textContent = data.enigma_data.confluence_level;
            document.getElementById('signalColor').textContent = data.enigma_data.signal_color;
            document.getElementById('macvuState').textContent = data.enigma_data.macvu_state;
            
            // Update Kelly and account
            document.getElementById('kellyPercentage').textContent = 
                (data.kelly_data.half_kelly_percentage * 100).toFixed(2) + '%';
            document.getElementById('positionSize').textContent = data.kelly_data.position_size;
            document.getElementById('accountBalance').textContent = 
                '$' + data.account_data.balance.toLocaleString();
            document.getElementById('dailyPnL').textContent = 
                '$' + data.account_data.daily_pnl.toFixed(2);
            
            // Update system status
            document.getElementById('ocrStatus').textContent = 
                data.system_status.ocr_status || 'Unknown';
            
            // Update trading controls
            updateTradingControls(data.trading_enabled, data.emergency_stop);
        }
        
        function updateTradingControls(tradingEnabled, emergencyStop) {
            const enableBtn = document.getElementById('enableTradingBtn');
            const disableBtn = document.getElementById('disableTradingBtn');
            const statusElement = document.getElementById('tradingStatus');
            
            if (emergencyStop) {
                statusElement.textContent = 'EMERGENCY STOP';
                statusElement.style.color = '#F44336';
                enableBtn.disabled = true;
                disableBtn.disabled = true;
            } else if (tradingEnabled) {
                statusElement.textContent = 'Enabled';
                statusElement.style.color = '#4CAF50';
                enableBtn.disabled = true;
                disableBtn.disabled = false;
            } else {
                statusElement.textContent = 'Disabled';
                statusElement.style.color = '#FF9800';
                enableBtn.disabled = false;
                disableBtn.disabled = true;
            }
        }
        
        async function enableTrading() {
            await makeControlRequest('/api/trading/enable', 'Trading enabled successfully');
        }
        
        async function disableTrading() {
            await makeControlRequest('/api/trading/disable', 'Trading disabled successfully');
        }
        
        async function emergencyStop() {
            if (confirm('Are you sure you want to trigger EMERGENCY STOP? This will immediately halt all trading.')) {
                await makeControlRequest('/api/emergency_stop', 'Emergency stop activated');
            }
        }
        
        async function makeControlRequest(endpoint, successMessage) {
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showSuccess(successMessage);
                } else {
                    showError(data.detail || 'Operation failed', 'controlErrorMessage');
                }
            } catch (error) {
                showError('Connection error: ' + error.message, 'controlErrorMessage');
            }
        }
        
        // Handle page visibility changes to maintain connection
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && websocket && websocket.readyState !== WebSocket.OPEN) {
                connectWebSocket();
            }
        });
    </script>
</body>
</html>
        """
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the mobile interface server"""
        logger.info(f"Starting Enigma-Apex Mobile Interface on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def connect_guardian_engine(self, guardian_engine: GuardianEngine):
        """Connect to the Guardian Engine for system integration"""
        self.guardian_engine = guardian_engine
        logger.info("Connected to Guardian Engine")

# Main execution
if __name__ == "__main__":
    mobile_server = MobileInterfaceServer()
    
    # Run the server
    asyncio.run(mobile_server.start_server(host="0.0.0.0", port=8000))
