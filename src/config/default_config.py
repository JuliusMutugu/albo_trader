"""
Default configuration for the Enigma-Apex Guardian System
"""

# Default configuration dictionary
DEFAULT_CONFIG = {
    # Database settings
    "database": {
        "path": "data/guardian.db"
    },
    
    # OCR processing settings
    "ocr": {
        "regions_config": "config/ocr_regions.json",
        "confidence_threshold": 0.8,
        "read_interval": 1.0,  # seconds between OCR readings
        "min_power_score": 50,  # minimum power score to consider
        "required_confluence": ["L3", "L4"]  # required confluence levels
    },
    
    # Kelly Criterion settings
    "kelly": {
        "trade_history_size": 100,
        "min_trades_for_kelly": 20,
        "max_position_percentage": 0.05,  # 5% max position size
        "kelly_multiplier": 0.5,  # Half-Kelly for safety
        "min_confidence": 0.6  # minimum confidence for Kelly sizing
    },
    
    # Cadence tracking settings
    "cadence": {
        "reading_history_hours": 48,
        "low_power_threshold": 30,
        "failure_duration_minutes": 60,
        "critical_failure_threshold": 15,  # Power score below this is critical
        "recovery_threshold": 60  # Power score above this is recovery
    },
    
    # Compliance monitoring settings
    "compliance": {
        "account_size": 50000.0,
        "max_loss_percentage": 0.08,  # 8% max loss (Apex rule)
        "daily_loss_percentage": 0.05,  # 5% daily loss limit
        "trailing_stop_percentage": 0.05,  # 5% trailing stop
        "max_position_risk": 0.02,  # 2% max risk per trade
        "max_daily_trades": 50,
        "max_consecutive_losses": 5,
        "monitor_interval": 30  # seconds between compliance checks
    },
    
    # WebSocket server settings
    "websocket": {
        "host": "localhost",
        "port": 8765,
        "ssl_cert_path": None,
        "ssl_key_path": None,
        "ping_interval": 30,
        "ping_timeout": 10
    },
    
    # Trading filters and criteria
    "filters": {
        "min_power": 50,
        "required_confluence": ["L3", "L4"],
        "required_signals": ["GREEN", "BLUE"],
        "macvu_filter": True,
        "cadence_threshold": True
    },
    
    # Risk management settings
    "risk": {
        "monitor_interval": 5,  # seconds between risk checks
        "atr_period": 14,
        "stop_loss_atr_multiplier": 1.5,
        "profit_target_atr_multiplier": 2.0,
        "emergency_stop_conditions": [
            "apex_violation",
            "cadence_failure",
            "system_error"
        ]
    },
    
    # Logging settings
    "logging": {
        "level": "INFO",
        "file": "logs/guardian.log",
        "max_size_mb": 50,
        "backup_count": 5,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    },
    
    # NinjaTrader integration settings (placeholder)
    "ninjatrader": {
        "websocket_port": 9999,
        "host": "localhost",
        "timeout": 30,
        "auto_connect": True,
        "instruments": ["ES", "NQ", "YM", "RTY"],
        "order_timeout": 10
    },
    
    # Mobile app settings (placeholder)
    "mobile": {
        "api_port": 8080,
        "authentication": True,
        "ssl_enabled": False,
        "session_timeout": 3600,
        "max_connections": 10
    },
    
    # System monitoring settings
    "monitoring": {
        "health_check_interval": 60,  # seconds
        "component_timeout": 30,
        "alert_thresholds": {
            "ocr_failure_rate": 0.1,  # 10% failure rate threshold
            "compliance_warnings": 5,  # max warnings before alert
            "memory_usage_mb": 1000,
            "cpu_usage_percent": 80
        }
    },
    
    # Performance settings
    "performance": {
        "ocr_parallel_processing": True,
        "max_concurrent_ocr": 3,
        "database_connection_pool": 5,
        "websocket_max_connections": 50,
        "cache_size_mb": 100
    },
    
    # Emergency settings
    "emergency": {
        "auto_stop_on_violation": True,
        "emergency_contacts": [],  # Email addresses for critical alerts
        "backup_data_interval": 3600,  # seconds between backups
        "max_recovery_attempts": 3
    }
}

# Environment-specific overrides
DEVELOPMENT_CONFIG = {
    "logging": {
        "level": "DEBUG"
    },
    "ocr": {
        "read_interval": 2.0  # Slower in development
    },
    "compliance": {
        "account_size": 5000.0  # Smaller account for testing
    }
}

PRODUCTION_CONFIG = {
    "logging": {
        "level": "INFO"
    },
    "websocket": {
        "ssl_cert_path": "/path/to/cert.pem",
        "ssl_key_path": "/path/to/key.pem"
    },
    "emergency": {
        "emergency_contacts": ["trader@company.com", "risk@company.com"]
    }
}

# Configuration validation rules
CONFIG_VALIDATION = {
    "required_keys": [
        "database.path",
        "ocr.confidence_threshold",
        "kelly.trade_history_size",
        "compliance.account_size",
        "websocket.port"
    ],
    "numeric_ranges": {
        "ocr.confidence_threshold": (0.0, 1.0),
        "kelly.max_position_percentage": (0.0, 0.1),
        "compliance.max_loss_percentage": (0.0, 0.2),
        "websocket.port": (1024, 65535)
    },
    "string_choices": {
        "logging.level": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    }
}
