"""
Trading configuration schema definitions
"""

from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from .base_config import BaseConfig

class RiskConfig(BaseModel):
    """Risk management configuration"""
    
    max_position_size: Decimal = Field(
        default=Decimal("0.1"),
        description="Maximum position size as fraction of balance"
    )
    risk_per_trade: Decimal = Field(
        default=Decimal("0.01"),
        description="Risk per trade as fraction of balance"
    )
    max_positions: int = Field(
        default=5,
        description="Maximum number of concurrent positions"
    )
    stop_loss_percent: Decimal = Field(
        default=Decimal("0.02"),
        description="Default stop loss percentage"
    )
    trailing_stop_percent: Decimal = Field(
        default=Decimal("0.01"),
        description="Trailing stop percentage"
    )
    break_even_trigger: Decimal = Field(
        default=Decimal("0.01"),
        description="Profit percentage to move stop to break even"
    )
    
    @validator("*")
    def validate_decimals(cls, v):
        """Validate decimal fields are positive"""
        if isinstance(v, Decimal) and v <= 0:
            raise ValueError("Must be positive")
        return v

class TradingConfig(BaseConfig):
    """Trading configuration model"""
    
    # Exchange settings
    exchange_id: str = Field(
        default="binance",
        description="Exchange identifier"
    )
    test_mode: bool = Field(
        default=True,
        description="Use exchange testnet"
    )
    
    # Trading pairs
    trading_pairs: List[str] = Field(
        default=["BTC/USDT"],
        description="Trading pairs to monitor"
    )
    
    # Risk management
    risk: RiskConfig = Field(
        default_factory=RiskConfig,
        description="Risk management settings"
    )
    
    # Strategy settings
    strategy: Dict = Field(
        default_factory=dict,
        description="Strategy-specific settings"
    )
    
    # External bot settings
    external_bots: Dict = Field(
        default_factory=dict,
        description="External bot connection settings"
    )
    
    class Config:
        """Pydantic config"""
        json_encoders = {
            Decimal: str
        }
