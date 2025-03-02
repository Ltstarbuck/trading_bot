"""
Trading configuration loader
"""

from typing import Optional
from pathlib import Path
from ..schemas import TradingConfig
from .base_loader import BaseConfigLoader

class TradingConfigLoader(BaseConfigLoader):
    """Trading configuration loader"""
    
    def __init__(
        self,
        config_dir: str = "config",
        config_file: str = "trading_config.yml"
    ):
        """
        Initialize trading config loader
        
        Args:
            config_dir: Configuration directory
            config_file: Configuration filename
        """
        super().__init__(config_dir)
        self.config_file = config_file
        
    def load_trading_config(
        self,
        env_prefix: Optional[str] = "TRADING_"
    ) -> TradingConfig:
        """
        Load trading configuration
        
        Args:
            env_prefix: Environment variable prefix
            
        Returns:
            Trading configuration
        """
        return self.load_config(
            self.config_file,
            TradingConfig,
            env_prefix
        )
        
    def save_trading_config(self, config: TradingConfig) -> None:
        """
        Save trading configuration to file
        
        Args:
            config: Trading configuration
        """
        import yaml
        
        config_path = Path(self.config_dir) / self.config_file
        
        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dict
        config_dict = config.dict(
            exclude_none=True,
            exclude_unset=True
        )
        
        # Save to file
        with open(config_path, 'w') as f:
            yaml.safe_dump(
                config_dict,
                f,
                default_flow_style=False,
                sort_keys=False
            )
