"""
Configuration Manager
Handles all application configuration settings with validation and environment support
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from ..config.default_config import DEFAULT_CONFIG, DEVELOPMENT_CONFIG, PRODUCTION_CONFIG, CONFIG_VALIDATION
import logging

class ConfigManager:
    """Centralized configuration management with validation and environment support"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = Path(config_path)
        self.config_data = {}
        self.logger = logging.getLogger(__name__)
        
        # Use imported default configuration
        self.default_config = DEFAULT_CONFIG.copy()
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from file with environment variable substitution"""
        try:
            # Start with default configuration
            self.config_data = self.default_config.copy()
            
            # Load from file if it exists
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self.config_data = self._deep_merge(self.config_data, file_config)
            else:
                self.logger.warning(f"Config file {self.config_path} not found, using defaults")
                self.save_config()  # Create default config file
            
            # Apply environment variable overrides
            self._apply_env_overrides()
            
            # Validate configuration
            self._validate_config()
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config_data = self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'ocr.confidence_threshold')"""
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting config value for '{key}': {e}")
            return default
    
    def get_settings(self) -> Dict[str, Any]:
        """Get complete settings dictionary"""
        return self.config_data.copy()
    
    def set(self, key: str, value: Any, save: bool = False):
        """Set configuration value using dot notation"""
        try:
            keys = key.split('.')
            config = self.config_data
            
            # Navigate to the parent dictionary
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            if save:
                self.save_config()
            
            self.logger.debug(f"Set config value '{key}' = {value}")
            
        except Exception as e:
            self.logger.error(f"Error setting config value for '{key}': {e}")
            raise
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration dictionary"""
        return self.config_data.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section, {})
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        env_overrides = {
            'GUARDIAN_LOG_LEVEL': 'logging.level',
            'GUARDIAN_OCR_CONFIDENCE': 'ocr.confidence_threshold',
            'GUARDIAN_KELLY_HISTORY_SIZE': 'kelly.history_size',
            'GUARDIAN_APEX_ACCOUNT_SIZE': 'apex.account_size',
            'GUARDIAN_WEBSOCKET_PORT': 'websocket.port',
            'GUARDIAN_DB_URL': 'database.url'
        }
        
        for env_var, config_key in env_overrides.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Try to convert to appropriate type
                try:
                    if '.' in env_value:
                        converted_value = float(env_value)
                    elif env_value.isdigit():
                        converted_value = int(env_value)
                    elif env_value.lower() in ('true', 'false'):
                        converted_value = env_value.lower() == 'true'
                    else:
                        converted_value = env_value
                    
                    self.set(config_key, converted_value)
                    self.logger.debug(f"Applied environment override: {env_var} -> {config_key} = {converted_value}")
                    
                except ValueError:
                    self.logger.warning(f"Could not convert environment variable {env_var}={env_value}")
    
    def _validate_config(self):
        """Validate configuration values"""
        validations = [
            ('ocr.confidence_threshold', lambda x: 0.0 <= x <= 1.0, "Must be between 0.0 and 1.0"),
            ('kelly.history_size', lambda x: x > 0, "Must be positive integer"),
            ('kelly.safety_factor', lambda x: 0.0 < x <= 1.0, "Must be between 0.0 and 1.0"),
            ('cadence.am_threshold', lambda x: x > 0, "Must be positive integer"),
            ('cadence.pm_threshold', lambda x: x > 0, "Must be positive integer"),
            ('apex.daily_drawdown_limit', lambda x: 0.0 < x < 1.0, "Must be between 0.0 and 1.0"),
            ('apex.max_drawdown_limit', lambda x: 0.0 < x < 1.0, "Must be between 0.0 and 1.0"),
            ('apex.account_size', lambda x: x > 0, "Must be positive number"),
            ('websocket.port', lambda x: 1024 <= x <= 65535, "Must be valid port number"),
        ]
        
        for key, validator, error_msg in validations:
            value = self.get(key)
            if value is not None and not validator(value):
                self.logger.error(f"Invalid configuration for '{key}': {error_msg}")
                raise ValueError(f"Invalid configuration for '{key}': {error_msg}")
    
    def reload(self):
        """Reload configuration from file"""
        self.load_config()
    
    def get_env_specific_config(self, environment: str = None) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        if environment is None:
            environment = os.getenv('GUARDIAN_ENV', 'production')
        
        env_config = self.get(f'environments.{environment}', {})
        base_config = self.get_all_config()
        
        # Remove environments section from base config
        if 'environments' in base_config:
            del base_config['environments']
        
        return self._deep_merge(base_config, env_config)
