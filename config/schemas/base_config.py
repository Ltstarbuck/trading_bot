"""
Base configuration schema definitions
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field

class BaseConfig(BaseModel):
    """Base configuration model"""
    
    # General settings
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    data_dir: str = Field(default="data", description="Directory for data storage")
    
    # API settings
    api_key: Optional[str] = Field(default=None, description="API key for exchange")
    api_secret: Optional[str] = Field(default=None, description="API secret for exchange")
    api_passphrase: Optional[str] = Field(default=None, description="Optional API passphrase")
    
    class Config:
        """Pydantic config"""
        extra = "allow"  # Allow extra fields
