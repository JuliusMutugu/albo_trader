"""
Configuration management for the Enigma-Apex trading system.

This module handles loading and validation of configuration files
for all system components.
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


def load_settings(config_file: str = "config/settings.yaml") -> Dict[str, Any]:
    """
    Load system settings from YAML configuration file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        config_path = Path(config_file)
        
        if not config_path.exists():
            # Create default configuration
            default_config = _get_default_settings()
            _save_default_config(config_path, default_config)
            return default_config
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate configuration
        validated_config = _validate_config(config)
        
        return validated_config
        
    except Exception as e:
        logging.error(f"Configuration loading error: {e}")
        return _get_default_settings()


def _get_default_settings() -> Dict[str, Any]:
    """Get default system configuration."""
    return {
        'ocr': {
            'read_interval': 1.0,  # seconds
            'confidence_threshold': 0.8,
            'regions_file': 'config/ocr_regions.json',
            'default_atr': 10.0
        },
        'kelly': {
            'history_length': 100,
            'base_win_rate': 0.5,
            'kelly_fraction': 0.5,  # Half-Kelly
            'min_trades_for_dynamic': 10,
            'max_position_pct': 0.02,  # 2%
            'initial_balance': 50000,
            'min_balance': 25000,
            'drawdown_reduction_factor': 0.5
        },
        'atr': {
            'atr_period': 14,
            'sl_multiplier': 1.5,
            'pt_multiplier': 2.0,
            'default_atr': 10.0,
            'max_price_history': 1000
        },
        'cadence': {
            'am_threshold': 2,
            'pm_threshold': 3,
            'max_history': 1000
        },
        'apex': {
            'account_size': 50000,
            'max_daily_loss': 2000,
            'max_trailing_loss': 3000,
            'profit_target': 3000,
            'max_contracts': 10,
            'max_position_value': 50000,
            'consistency_threshold': 0.4,
            'monitor_interval': 5.0  # seconds
        },
        'ninjatrader': {
            'websocket_host': 'localhost',
            'websocket_port': 8080,
            'reconnect_delay': 5.0,
            'heartbeat_interval': 30.0
        },
        'mobile': {
            'api_host': '0.0.0.0',
            'api_port': 8000,
            'auth_token': 'change_this_token',
            'ssl_enabled': False
        },
        'risk': {
            'monitor_interval': 1.0,  # seconds
            'emergency_stop_enabled': True,
            'max_daily_trades': 20
        },
        'filters': {
            'min_power': 15,
            'required_confluence': ['L3', 'L4'],
            'macvu_required': True
        },
        'logging': {
            'level': 'INFO',
            'max_file_size': 10485760,  # 10MB
            'backup_count': 5
        }
    }


def _validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration values and apply defaults for missing keys.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated configuration dictionary
    """
    default_config = _get_default_settings()
    
    # Merge with defaults for missing keys
    validated = {}
    
    for section, section_config in default_config.items():
        if section in config:
            validated[section] = {}
            for key, default_value in section_config.items():
                validated[section][key] = config[section].get(key, default_value)
        else:
            validated[section] = section_config.copy()
            
    # Validate specific values
    _validate_numeric_ranges(validated)
    
    return validated


def _validate_numeric_ranges(config: Dict[str, Any]):
    """Validate that numeric configuration values are within reasonable ranges."""
    
    # Kelly configuration validation
    kelly_config = config['kelly']
    kelly_config['kelly_fraction'] = max(0.1, min(1.0, kelly_config['kelly_fraction']))
    kelly_config['base_win_rate'] = max(0.1, min(0.9, kelly_config['base_win_rate']))
    kelly_config['max_position_pct'] = max(0.001, min(0.1, kelly_config['max_position_pct']))
    
    # ATR configuration validation
    atr_config = config['atr']
    atr_config['sl_multiplier'] = max(0.5, min(5.0, atr_config['sl_multiplier']))
    atr_config['pt_multiplier'] = max(0.5, min(10.0, atr_config['pt_multiplier']))
    
    # Cadence configuration validation
    cadence_config = config['cadence']
    cadence_config['am_threshold'] = max(1, min(10, cadence_config['am_threshold']))
    cadence_config['pm_threshold'] = max(1, min(10, cadence_config['pm_threshold']))
    
    # Apex configuration validation
    apex_config = config['apex']
    apex_config['max_daily_loss'] = max(100, apex_config['max_daily_loss'])
    apex_config['max_trailing_loss'] = max(100, apex_config['max_trailing_loss'])
    apex_config['consistency_threshold'] = max(0.1, min(0.9, apex_config['consistency_threshold']))


def _save_default_config(config_path: Path, config: Dict[str, Any]):
    """Save default configuration to file."""
    try:
        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
            
        logging.info(f"Default configuration saved to {config_path}")
        
    except Exception as e:
        logging.error(f"Failed to save default configuration: {e}")


def save_config(config: Dict[str, Any], config_file: str = "config/settings.yaml"):
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        config_file: Path to save configuration file
    """
    try:
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
            
        logging.info(f"Configuration saved to {config_path}")
        
    except Exception as e:
        logging.error(f"Configuration save error: {e}")


def update_config_value(section: str, key: str, value: Any, 
                       config_file: str = "config/settings.yaml"):
    """
    Update a specific configuration value.
    
    Args:
        section: Configuration section
        key: Configuration key
        value: New value
        config_file: Configuration file path
    """
    try:
        config = load_settings(config_file)
        
        if section not in config:
            config[section] = {}
            
        config[section][key] = value
        
        save_config(config, config_file)
        
        logging.info(f"Updated {section}.{key} = {value}")
        
    except Exception as e:
        logging.error(f"Configuration update error: {e}")


def get_config_value(section: str, key: str, default: Any = None,
                    config_file: str = "config/settings.yaml") -> Any:
    """
    Get a specific configuration value.
    
    Args:
        section: Configuration section
        key: Configuration key  
        default: Default value if not found
        config_file: Configuration file path
        
    Returns:
        Configuration value or default
    """
    try:
        config = load_settings(config_file)
        return config.get(section, {}).get(key, default)
        
    except Exception as e:
        logging.error(f"Configuration value retrieval error: {e}")
        return default
