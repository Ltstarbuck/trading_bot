"""
Configuration Management System
Handles loading and validation of configuration from multiple sources
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel
from dotenv import load_dotenv

class TradingConfig(BaseModel):
    """Trading configuration model"""
    max_positions: int = 5
    min_volatility: float = 0.01
    max_position_size: float = 0.1
    stop_loss_percent: float = 0.02
    trailing_stop_percent: float = 0.01
    break_even_padding: float = 0.002  # Additional padding for break-even calculation

class ExchangeConfig(BaseModel):
    """Exchange configuration model"""
    exchange_id: str
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = False

class NotificationConfig(BaseModel):
    """Notification configuration model"""
    enable_sound: bool = True
    enable_visual: bool = True
    loss_alert_threshold: float = -0.05

class AppConfig(BaseModel):
    """Main application configuration model"""
    trading: TradingConfig = TradingConfig()
    exchange: ExchangeConfig
    notifications: NotificationConfig = NotificationConfig()
    log_level: str = "INFO"
    data_dir: str = "data"

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        """Initialize configuration manager"""
        self.config: Optional[AppConfig] = None
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent.parent
        
        # Load configuration
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from all sources"""
        # Load .env file
        load_dotenv(self.project_root / '.env')
        
        # Load YAML config
        config_data = self._load_yaml_config()
        
        # Override with environment variables
        config_data = self._override_from_env(config_data)
        
        # Create config object
        self.config = AppConfig(**config_data)
        
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = self.config_dir / 'config.yaml'
        
        if not config_path.exists():
            return {}
            
        with open(config_path) as f:
            return yaml.safe_load(f)
            
    def _override_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables"""
        env_mapping = {
            'TRADING_MAX_POSITIONS': ('trading', 'max_positions'),
            'TRADING_MIN_VOLATILITY': ('trading', 'min_volatility'),
            'TRADING_MAX_POSITION_SIZE': ('trading', 'max_position_size'),
            'TRADING_STOP_LOSS_PERCENT': ('trading', 'stop_loss_percent'),
            'TRADING_TRAILING_STOP_PERCENT': ('trading', 'trailing_stop_percent'),
            'EXCHANGE_ID': ('exchange', 'exchange_id'),
            'EXCHANGE_API_KEY': ('exchange', 'api_key'),
            'EXCHANGE_API_SECRET': ('exchange', 'api_secret'),
            'EXCHANGE_TESTNET': ('exchange', 'testnet'),
            'NOTIFICATIONS_ENABLE_SOUND': ('notifications', 'enable_sound'),
            'NOTIFICATIONS_ENABLE_VISUAL': ('notifications', 'enable_visual'),
            'NOTIFICATIONS_LOSS_ALERT_THRESHOLD': ('notifications', 'loss_alert_threshold'),
            'LOG_LEVEL': ('log_level',),
            'DATA_DIR': ('data_dir',),
        }
        
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                current = config
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = self._convert_env_value(value)
                
        return config
        
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
                
    def get_config(self) -> AppConfig:
        """Get current configuration"""
        if self.config is None:
            self.load_config()
        return self.config
        
    def save_config(self) -> None:
        """Save current configuration to YAML file"""
        config_path = self.config_dir / 'config.yaml'
        
        with open(config_path, 'w') as f:
            yaml.dump(self.config.dict(), f)
            
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        if self.config is None:
            self.load_config()
            
        current_dict = self.config.dict()
        current_dict.update(updates)
        self.config = AppConfig(**current_dict)
        
        # Save updates
        self.save_config()
