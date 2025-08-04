# Technical Architecture Documentation

## System Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AlgoBox       │    │  Python Backend  │    │  NinjaTrader 8  │
│   Enigma Panel  │───▶│  Guardian Engine │───▶│   Dashboard     │
│   (OCR Input)   │    │                  │    │   (NinjaScript) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Mobile Remote   │
                       │     Control      │
                       └──────────────────┘
```

### Core Components

#### 1. OCR Processing Layer
**Technology Stack:**
- **Primary**: EasyOCR (fast, multi-language support)
- **Secondary**: Tesseract (backup accuracy)
- **Computer Vision**: OpenCV (color detection, image preprocessing)
- **Screen Capture**: mss (high-performance screen grabbing)

**Architecture:**
```python
class OCRProcessor:
    def __init__(self):
        self.easy_reader = easyocr.Reader(['en'])
        self.tesseract_config = '--psm 7 -c tessedit_char_whitelist=0123456789'
        self.region_manager = RegionManager()
        self.confidence_validator = ConfidenceValidator()
    
    def process_enigma_panel(self) -> EnigmaData:
        # Multi-engine processing with validation
        pass
```

#### 2. Guardian Engine (Core Logic)
**Microservices Architecture:**
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  OCR Service    │  │ Kelly Engine    │  │ Cadence Tracker │
│                 │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
         ┌─────────────────────▼─────────────────────┐
         │          Guardian Decision Engine          │
         │                                           │
         └─────────────────────┬─────────────────────┘
                               │
┌─────────────────┐  ┌─────────▼─────────┐  ┌─────────────────┐
│ Apex Compliance │  │   Risk Manager    │  │  Alert System   │
│                 │  │                   │  │                 │
└─────────────────┘  └───────────────────┘  └─────────────────┘
```

#### 3. Real-Time Communication
**WebSocket Architecture:**
```python
class GuardianWebSocketServer:
    async def handle_client(self, websocket, path):
        if path == "/ninjatrader":
            await self.handle_ninjatrader_client(websocket)
        elif path == "/mobile":
            await self.handle_mobile_client(websocket)
        elif path == "/dashboard":
            await self.handle_dashboard_client(websocket)
```

## Detailed Component Specifications

### OCR Engine Specifications

#### Multi-Engine Processing
```python
class MultiEngineOCR:
    def __init__(self):
        self.engines = {
            'easyocr': EasyOCREngine(),
            'tesseract': TesseractEngine(),
            'opencv': OpenCVEngine()
        }
        self.consensus_threshold = 0.8
    
    def read_with_consensus(self, image_region: np.ndarray) -> OCRResult:
        results = []
        for engine_name, engine in self.engines.items():
            result = engine.process(image_region)
            results.append(result)
        
        return self.consensus_validator.validate(results)
```

#### Region Management
```python
class RegionManager:
    def __init__(self, config_path: str):
        self.regions = self.load_regions(config_path)
        self.calibration_data = CalibrationData()
    
    def auto_calibrate(self, reference_image: np.ndarray):
        """Auto-detect regions using template matching"""
        pass
    
    def get_region_coordinates(self, region_name: str) -> Tuple[int, int, int, int]:
        """Returns (x1, y1, x2, y2) coordinates"""
        pass
```

#### Screen Capture Optimization
```python
class HighPerformanceCapture:
    def __init__(self):
        self.sct = mss.mss()
        self.capture_queue = asyncio.Queue(maxsize=100)
        self.processing_pool = ThreadPoolExecutor(max_workers=4)
    
    async def continuous_capture(self, regions: Dict[str, Tuple]):
        """Capture multiple regions at 20 FPS"""
        while self.running:
            timestamp = time.time()
            captures = {}
            
            for region_name, coordinates in regions.items():
                capture = self.sct.grab(coordinates)
                captures[region_name] = {
                    'image': np.array(capture),
                    'timestamp': timestamp,
                    'region': region_name
                }
            
            await self.capture_queue.put(captures)
            await asyncio.sleep(0.05)  # 20 FPS
```

### Kelly Criterion Engine

#### Mathematical Implementation
```python
class KellyEngine:
    def __init__(self, history_size: int = 100):
        self.trade_history = deque(maxlen=history_size)
        self.base_win_rate = 0.5
        self.confidence_threshold = 0.95
        self.kelly_safety_factor = 0.5  # Half-Kelly
    
    def calculate_kelly_fraction(self, reward_risk_ratio: float) -> float:
        """
        Kelly Formula: f = (bp - q) / b
        where:
        - f = fraction of capital to risk
        - b = reward/risk ratio
        - p = probability of winning
        - q = probability of losing (1-p)
        """
        p = self.get_dynamic_win_rate()
        q = 1 - p
        b = reward_risk_ratio
        
        kelly_fraction = (b * p - q) / b
        
        # Apply safety factor (half-Kelly)
        safe_fraction = kelly_fraction * self.kelly_safety_factor
        
        # Ensure non-negative and within bounds
        return max(0, min(safe_fraction, 0.25))  # Max 25% risk
    
    def get_dynamic_win_rate(self) -> float:
        """Calculate adaptive win rate with confidence weighting"""
        if len(self.trade_history) == 0:
            return self.base_win_rate
        
        actual_win_rate = sum(self.trade_history) / len(self.trade_history)
        sample_size = len(self.trade_history)
        
        # Confidence weighting based on sample size
        confidence_weight = min(sample_size / 100, 1.0)
        
        # Weighted average between actual and baseline
        dynamic_rate = (actual_win_rate * confidence_weight + 
                       self.base_win_rate * (1 - confidence_weight))
        
        return dynamic_rate
    
    def should_trade(self, kelly_fraction: float) -> bool:
        """Determine if Kelly fraction indicates positive edge"""
        return kelly_fraction > 0.01  # Minimum 1% edge required
```

#### Performance Analytics
```python
class PerformanceAnalytics:
    def __init__(self, kelly_engine: KellyEngine):
        self.kelly_engine = kelly_engine
        self.metrics = {}
    
    def calculate_sharpe_ratio(self) -> float:
        """Calculate risk-adjusted returns"""
        if len(self.kelly_engine.trade_history) < 10:
            return 0.0
        
        returns = np.array(self.kelly_engine.trade_history)
        excess_returns = returns - np.mean(returns)
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns)
    
    def calculate_maximum_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        cumulative = np.cumsum(self.kelly_engine.trade_history)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0
```

### ATR Risk Management

#### Dynamic ATR Calculator
```python
class ATRCalculator:
    def __init__(self, period: int = 14):
        self.period = period
        self.price_history = deque(maxlen=period * 2)
        self.atr_history = deque(maxlen=50)
    
    def calculate_atr(self, high: float, low: float, close: float) -> float:
        """Calculate True Range and Average True Range"""
        if len(self.price_history) == 0:
            self.price_history.append({'high': high, 'low': low, 'close': close})
            return high - low
        
        previous_close = self.price_history[-1]['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - previous_close)
        tr3 = abs(low - previous_close)
        true_range = max(tr1, tr2, tr3)
        
        self.price_history.append({'high': high, 'low': low, 'close': close})
        
        # Calculate ATR (Simple Moving Average of True Range)
        if len(self.price_history) >= self.period:
            recent_trs = [self._calculate_tr(i) for i in range(-self.period, 0)]
            atr = sum(recent_trs) / len(recent_trs)
            self.atr_history.append(atr)
            return atr
        
        return true_range
    
    def get_dynamic_multipliers(self, market_session: str, trend_strength: float) -> Dict[str, float]:
        """Get session and trend-adjusted multipliers"""
        base_multipliers = {
            'stop_loss': 1.5,
            'profit_target': 2.0
        }
        
        # Session adjustments
        session_adjustments = {
            'AM': {'stop_loss': 1.0, 'profit_target': 1.2},  # Tighter in AM
            'PM': {'stop_loss': 1.2, 'profit_target': 0.9}   # Wider in PM
        }
        
        # Trend strength adjustments
        trend_adjustments = {
            'stop_loss': 1.0 + (trend_strength * 0.3),
            'profit_target': 1.0 - (trend_strength * 0.2)
        }
        
        final_multipliers = {}
        for key in base_multipliers:
            final_multipliers[key] = (
                base_multipliers[key] * 
                session_adjustments.get(market_session, {}).get(key, 1.0) *
                trend_adjustments[key]
            )
        
        return final_multipliers
```

### Cadence Tracking System

#### State Machine Implementation
```python
class CadenceTracker:
    def __init__(self):
        self.state = CadenceState.NEUTRAL
        self.failure_count = 0
        self.success_count = 0
        self.session_thresholds = {
            'AM': 2,
            'PM': 3
        }
        self.current_session = self._detect_session()
        self.state_history = []
    
    def update_signal_outcome(self, outcome: SignalOutcome, timestamp: datetime):
        """Update cadence state based on signal outcome"""
        previous_state = self.state
        
        if outcome == SignalOutcome.SUCCESS:
            self.failure_count = 0
            self.success_count += 1
            self.state = CadenceState.NEUTRAL
        elif outcome == SignalOutcome.FAILURE:
            self.failure_count += 1
            self.success_count = 0
            
            threshold = self.session_thresholds[self.current_session]
            if self.failure_count >= threshold:
                self.state = CadenceState.HIGH_PROBABILITY
            else:
                self.state = CadenceState.BUILDING
        
        # Log state transition
        self.state_history.append({
            'timestamp': timestamp,
            'previous_state': previous_state,
            'new_state': self.state,
            'failure_count': self.failure_count,
            'outcome': outcome
        })
    
    def is_high_probability_setup(self) -> bool:
        """Check if cadence indicates high probability"""
        return self.state == CadenceState.HIGH_PROBABILITY
    
    def get_probability_boost(self) -> float:
        """Get probability boost based on cadence state"""
        boosts = {
            CadenceState.NEUTRAL: 0.0,
            CadenceState.BUILDING: 0.05,
            CadenceState.HIGH_PROBABILITY: 0.15
        }
        return boosts.get(self.state, 0.0)
```

### Apex Compliance Engine

#### Multi-Layer Protection System
```python
class ApexComplianceEngine:
    def __init__(self, account_config: ApexAccountConfig):
        self.config = account_config
        self.daily_stats = DailyStats()
        self.protection_layers = [
            HardLimitProtection(self.config),
            SoftWarningProtection(self.config),
            PredictiveProtection(self.config)
        ]
    
    def validate_trade_proposal(self, trade: TradeProposal) -> ComplianceResult:
        """Multi-layer validation of proposed trade"""
        result = ComplianceResult()
        
        for layer in self.protection_layers:
            layer_result = layer.validate(trade, self.daily_stats)
            result.merge(layer_result)
            
            if layer_result.violation_level == ViolationLevel.CRITICAL:
                result.allow_trade = False
                break
        
        return result
    
    def monitor_real_time_compliance(self):
        """Continuous monitoring of account compliance"""
        while self.monitoring:
            current_stats = self.get_current_account_stats()
            
            # Check for approaching violations
            warnings = self._check_approaching_violations(current_stats)
            
            if warnings:
                self.alert_system.send_warnings(warnings)
            
            # Emergency stop if critical violation detected
            critical_violations = self._check_critical_violations(current_stats)
            if critical_violations:
                self.emergency_stop_all_trades()
                self.alert_system.send_critical_alerts(critical_violations)
            
            await asyncio.sleep(1)  # Check every second
```

### NinjaScript Integration

#### C# NinjaScript Architecture
```csharp
public class EnigmaGuardianPanel : NTTabPage
{
    private GuardianWebSocketClient webSocketClient;
    private Dictionary<string, InstrumentPanel> instrumentPanels;
    private CompliancePanel compliancePanel;
    private ControlPanel controlPanel;
    
    public override void OnStateChange()
    {
        if (State == State.SetDefaults)
        {
            Name = "Enigma Guardian";
            TabName = "Guardian";
            
            // Initialize WebSocket client
            webSocketClient = new GuardianWebSocketClient("ws://localhost:8765/ninjatrader");
            webSocketClient.OnDataReceived += HandleGuardianData;
        }
        else if (State == State.Active)
        {
            // Create UI panels
            CreateInstrumentPanels();
            CreateCompliancePanel();
            CreateControlPanel();
            
            // Start WebSocket connection
            webSocketClient.ConnectAsync();
        }
    }
    
    private void HandleGuardianData(GuardianData data)
    {
        Dispatcher.BeginInvoke(new Action(() =>
        {
            UpdateInstrumentPanel(data.Instrument, data);
            UpdateCompliancePanel(data.Compliance);
            UpdateAlerts(data.Alerts);
        }));
    }
}

public class GuardianWebSocketClient
{
    private ClientWebSocket webSocket;
    private CancellationTokenSource cancellationToken;
    
    public event Action<GuardianData> OnDataReceived;
    
    public async Task ConnectAsync()
    {
        webSocket = new ClientWebSocket();
        cancellationToken = new CancellationTokenSource();
        
        await webSocket.ConnectAsync(new Uri(serverUrl), cancellationToken.Token);
        
        // Start listening for messages
        _ = Task.Run(async () => await ListenForMessages());
    }
    
    private async Task ListenForMessages()
    {
        var buffer = new byte[4096];
        
        while (webSocket.State == WebSocketState.Open)
        {
            var result = await webSocket.ReceiveAsync(
                new ArraySegment<byte>(buffer), 
                cancellationToken.Token
            );
            
            if (result.MessageType == WebSocketMessageType.Text)
            {
                var message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                var data = JsonConvert.DeserializeObject<GuardianData>(message);
                OnDataReceived?.Invoke(data);
            }
        }
    }
}
```

### Mobile Application Architecture

#### Cross-Platform Framework (Flutter)
```dart
class GuardianMobileApp extends StatefulWidget {
  @override
  _GuardianMobileAppState createState() => _GuardianMobileAppState();
}

class _GuardianMobileAppState extends State<GuardianMobileApp> {
  late WebSocketChannel channel;
  late AuthenticationService authService;
  late TradingControlService controlService;
  
  @override
  void initState() {
    super.initState();
    
    authService = AuthenticationService();
    controlService = TradingControlService();
    
    // Initialize secure WebSocket connection
    initializeWebSocket();
  }
  
  void initializeWebSocket() async {
    final token = await authService.getSecureToken();
    
    channel = WebSocketChannel.connect(
      Uri.parse('wss://guardian-server.com/mobile'),
      protocols: ['guardian-protocol']
    );
    
    // Send authentication
    channel.sink.add(jsonEncode({
      'type': 'auth',
      'token': token
    }));
    
    // Listen for data
    channel.stream.listen((data) {
      final message = jsonDecode(data);
      handleServerMessage(message);
    });
  }
  
  void handleServerMessage(Map<String, dynamic> message) {
    switch (message['type']) {
      case 'account_status':
        setState(() {
          // Update account status display
        });
        break;
      case 'alert':
        showAlert(message['data']);
        break;
      case 'compliance_warning':
        showComplianceWarning(message['data']);
        break;
    }
  }
}

class EmergencyStopButton extends StatelessWidget {
  final VoidCallback onPressed;
  
  const EmergencyStopButton({Key? key, required this.onPressed}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 200,
      height: 200,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.red,
          shape: CircleBorder(),
          elevation: 10,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.stop, size: 48, color: Colors.white),
            SizedBox(height: 8),
            Text(
              'EMERGENCY\nSTOP',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Database Schema

### Trade History & Analytics
```sql
-- Trade history table
CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    instrument VARCHAR(10) NOT NULL,
    direction VARCHAR(4) NOT NULL, -- LONG/SHORT
    entry_price DECIMAL(10,4) NOT NULL,
    exit_price DECIMAL(10,4),
    quantity INTEGER NOT NULL,
    stop_loss DECIMAL(10,4),
    profit_target DECIMAL(10,4),
    atr_value DECIMAL(10,4),
    kelly_fraction DECIMAL(8,6),
    win_rate DECIMAL(6,4),
    cadence_state VARCHAR(20),
    outcome VARCHAR(10), -- WIN/LOSS/OPEN
    pnl DECIMAL(10,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cadence tracking table
CREATE TABLE cadence_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    session VARCHAR(2) NOT NULL, -- AM/PM
    failure_count INTEGER NOT NULL,
    state VARCHAR(20) NOT NULL,
    signal_outcome VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Account compliance table
CREATE TABLE compliance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    violation_type VARCHAR(50),
    severity VARCHAR(20), -- INFO/WARNING/CRITICAL
    current_drawdown DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    daily_pnl DECIMAL(10,2),
    action_taken VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- OCR accuracy tracking
CREATE TABLE ocr_accuracy_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    region_name VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(6,4),
    raw_text VARCHAR(100),
    validated_text VARCHAR(100),
    processing_time_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Configuration Management
```sql
-- User configurations
CREATE TABLE user_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL, -- STRING/INTEGER/FLOAT/BOOLEAN/JSON
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, config_key)
);

-- OCR region configurations
CREATE TABLE ocr_regions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_name VARCHAR(50) NOT NULL UNIQUE,
    x1 INTEGER NOT NULL,
    y1 INTEGER NOT NULL,
    x2 INTEGER NOT NULL,
    y2 INTEGER NOT NULL,
    screen_resolution VARCHAR(20),
    confidence_threshold DECIMAL(4,2) DEFAULT 0.8,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Security Architecture

### Authentication & Authorization
```python
class SecurityManager:
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET_KEY')
        self.encryption_key = Fernet.generate_key()
        self.session_manager = SessionManager()
        self.rate_limiter = RateLimiter()
    
    def generate_secure_token(self, user_id: str, permissions: List[str]) -> str:
        """Generate JWT token with permissions"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityException("Token has expired")
        except jwt.InvalidTokenError:
            raise SecurityException("Invalid token")
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage"""
        f = Fernet(self.encryption_key)
        return f.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        f = Fernet(self.encryption_key)
        return f.decrypt(encrypted_data.encode()).decode()
```

### Rate Limiting & DDoS Protection
```python
class RateLimiter:
    def __init__(self):
        self.request_counts = defaultdict(lambda: {'count': 0, 'reset_time': time.time()})
        self.limits = {
            'api_calls': {'limit': 100, 'window': 60},  # 100 per minute
            'login_attempts': {'limit': 5, 'window': 300},  # 5 per 5 minutes
            'trade_commands': {'limit': 50, 'window': 60}  # 50 per minute
        }
    
    def check_rate_limit(self, identifier: str, action_type: str) -> bool:
        """Check if action is within rate limits"""
        current_time = time.time()
        key = f"{identifier}:{action_type}"
        
        limit_config = self.limits.get(action_type, {'limit': 10, 'window': 60})
        
        if key not in self.request_counts:
            self.request_counts[key] = {
                'count': 1,
                'reset_time': current_time + limit_config['window']
            }
            return True
        
        request_data = self.request_counts[key]
        
        if current_time > request_data['reset_time']:
            # Reset the counter
            request_data['count'] = 1
            request_data['reset_time'] = current_time + limit_config['window']
            return True
        
        if request_data['count'] < limit_config['limit']:
            request_data['count'] += 1
            return True
        
        return False  # Rate limit exceeded
```

This technical architecture provides a comprehensive foundation for building a robust, scalable, and secure trading system that meets all the specified requirements while maintaining industry best practices.
