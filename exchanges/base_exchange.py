"""
Base Exchange Interface
Defines the contract that all exchange implementations must follow
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

class BaseExchange(ABC):
    """Abstract base class for all exchange implementations"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        """
        Initialize exchange
        
        Args:
            api_key: Exchange API key
            api_secret: Exchange API secret
            testnet: Whether to use testnet/sandbox
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to exchange"""
        pass
        
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data for symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dict containing ticker data
        """
        pass
        
    @abstractmethod
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book for symbol
        
        Args:
            symbol: Trading pair symbol
            limit: Depth of orderbook
            
        Returns:
            Dict containing bids and asks
        """
        pass
        
    @abstractmethod
    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: Decimal,
        price: Optional[Decimal] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Place a new order
        
        Args:
            symbol: Trading pair symbol
            order_type: Type of order (market, limit, etc)
            side: buy or sell
            amount: Amount to trade
            price: Price for limit orders
            params: Additional parameters
            
        Returns:
            Dict containing order details
        """
        pass
        
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an existing order
        
        Args:
            order_id: ID of order to cancel
            symbol: Trading pair symbol
            
        Returns:
            Dict containing cancellation details
        """
        pass
        
    @abstractmethod
    async def get_balance(self, currency: Optional[str] = None) -> Dict:
        """
        Get account balance
        
        Args:
            currency: Specific currency to get balance for
            
        Returns:
            Dict containing balance information
        """
        pass
        
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of open orders
        """
        pass
        
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """
        Get status of an order
        
        Args:
            order_id: ID of order to check
            symbol: Trading pair symbol
            
        Returns:
            Dict containing order status
        """
        pass
        
    @abstractmethod
    async def get_trade_fee(self, symbol: str) -> Dict:
        """
        Get trading fees for symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dict containing fee information
        """
        pass
        
    @abstractmethod
    async def get_price_history(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get historical price data
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            since: Start time in milliseconds
            limit: Number of candles
            
        Returns:
            List of OHLCV data
        """
        pass
        
    @abstractmethod
    def get_markets(self) -> List[Dict]:
        """
        Get available markets
        
        Returns:
            List of available trading pairs and their metadata
        """
        pass
        
    @abstractmethod
    async def get_volatility(self, symbol: str, window: int = 24) -> Decimal:
        """
        Calculate volatility for symbol
        
        Args:
            symbol: Trading pair symbol
            window: Time window in hours
            
        Returns:
            Volatility as a decimal
        """
        pass
