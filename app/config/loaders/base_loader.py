"""
Base configuration loader
"""

from typing import Any, Dict, Optional, Type, TypeVar
from pathlib import Path
import yaml
from pydantic import BaseModel
from loguru import logger

T = TypeVar('T', bound=BaseModel)

class BaseConfigLoader:
    """Base class for configuration loaders"""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize config loader
        
        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = Path(config_dir)
        
    def load_config(
        self,
        filename: str,
        config_class: Type[T],
        env_prefix: Optional[str] = None
    ) -> T:
        """
        Load configuration from file and environment
        
        Args:
            filename: Configuration filename
            config_class: Configuration class
            env_prefix: Environment variable prefix
            
        Returns:
            Configuration object
        """
        # Load from file
        config_data = self._load_yaml(filename)
        
        # Create config object
        config = config_class(**config_data)
        
        # Update from environment if prefix specified
        if env_prefix:
            self._update_from_env(config, env_prefix)
            
        return config
        
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_path = self.config_dir / filename
        
        try:
            if config_path.exists():
                with open(config_path) as f:
                    return yaml.safe_load(f) or {}
            else:
                logger.warning(f"Config file not found: {config_path}")
                return {}
                
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {str(e)}")
            return {}
            
    def _update_from_env(self, config: BaseModel, prefix: str) -> None:
        """Update config from environment variables"""
        import os
        
        # Get all environment variables with prefix
        env_vars = {
            k: v for k, v in os.environ.items()
            if k.startswith(prefix)
        }
        
        # Update config
        for key, value in env_vars.items():
            # Remove prefix and convert to lowercase
            config_key = key[len(prefix):].lower()
            
            try:
                # Update nested config using dot notation
                self._set_nested_attr(config, config_key, value)
            except Exception as e:
                logger.warning(
                    f"Failed to set config value from env {key}: {str(e)}"
                )
                
    def _set_nested_attr(
        self,
        obj: Any,
        attr_path: str,
        value: Any
    ) -> None:
        """Set nested attribute using dot notation"""
        parts = attr_path.split('.')
        
        for part in parts[:-1]:
            obj = getattr(obj, part)
            
        setattr(obj, parts[-1], value)
