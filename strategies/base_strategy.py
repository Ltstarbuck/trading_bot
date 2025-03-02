"""
Base Strategy Interface
Defines the contract that all trading strategies must follow
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

class Signal:
    """Represents a trading signal with parameters for trading decisions."""

    def __init__(self, symbol: str, action: str, confidence: float):
        """Initialize a trading signal.
        
        Args:
            symbol (str): The trading pair symbol.
            action (str): The action to take (e.g., 'buy' or 'sell').
            confidence (float): The confidence level of the signal.
        """
        self.symbol = symbol
        self.action = action
        self.confidence = confidence

    def __repr__(self):
        return f"Signal(symbol={self.symbol}, action={self.action}, confidence={self.confidence})"


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, config: Dict):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration
        """
        self.config = config
        
    @abstractmethod
    async def analyze(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> Dict:
        """
        Analyze market data and generate trading signals
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            limit: Number of candles to analyze
            
        Returns:
            Dict containing analysis results and signals
        """
        pass
        
    @abstractmethod
    async def should_open_position(
        self,
        symbol: str,
        current_price: Decimal,
        available_balance: Decimal
    ) -> Optional[Dict]:
        """
        Determine if a position should be opened
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            available_balance: Available balance for trading
            
        Returns:
            Dict with position parameters if should open, None otherwise
        """
        pass
        
    @abstractmethod
    async def should_close_position(
        self,
        position: Dict,
        current_price: Decimal
    ) -> bool:
        """
        Determine if a position should be closed
        
        Args:
            position: Position information
            current_price: Current market price
            
        Returns:
            True if position should be closed, False otherwise
        """
        pass
        
    @abstractmethod
    def calculate_position_size(
        self,
        symbol: str,
        current_price: Decimal,
        available_balance: Decimal
    ) -> Decimal:
        """
        Calculate appropriate position size
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            available_balance: Available balance for trading
            
        Returns:
            Position size to open
        """
        pass
        
    @abstractmethod
    def calculate_stop_loss(
        self,
        symbol: str,
        entry_price: Decimal,
        side: str
    ) -> Decimal:
        """
        Calculate stop loss price
        
        Args:
            symbol: Trading pair symbol
            entry_price: Position entry price
            side: Position side (long/short)
            
        Returns:
            Stop loss price
        """
        pass
        
    @abstractmethod
    def calculate_take_profit(
        self,
        symbol: str,
        entry_price: Decimal,
        side: str
    ) -> Decimal:
        """
        Calculate take profit price
        
        Args:
            symbol: Trading pair symbol
            entry_price: Position entry price
            side: Position side (long/short)
            
        Returns:
            Take profit price
        """
        pass
        
    @abstractmethod
    def update_parameters(
        self,
        symbol: str,
        current_price: Decimal,
        position: Optional[Dict] = None
    ) -> None:
        """
        Update strategy parameters based on current market conditions
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            position: Optional current position information
        """
        pass
