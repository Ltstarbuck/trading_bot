"""
Base market data feed
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
import asyncio
from datetime import datetime
from loguru import logger

class MarketDataFeed(ABC):
    """Abstract base class for market data feeds"""
    
    def __init__(
        self,
        symbols: List[str],
        update_interval: float = 1.0
    ):
        """
        Initialize market data feed
        
        Args:
            symbols: List of trading pairs to track
            update_interval: Update interval in seconds
        """
        self.symbols = symbols
        self.update_interval = update_interval
        self._running = False
        self._last_data: Dict[str, Dict] = {}
        self._subscribers: List = []
        self._lock = asyncio.Lock()
        
    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to data feed
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data feed"""
        pass
        
    @abstractmethod
    async def _fetch_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch latest market data
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Market data dictionary
            
        Raises:
            Exception: If data fetch fails
        """
        pass
        
    async def start(self) -> None:
        """Start data feed"""
        if self._running:
            return
            
        try:
            await self.connect()
            self._running = True
            
            # Start update loop for each symbol
            tasks = [
                asyncio.create_task(self._update_loop(symbol))
                for symbol in self.symbols
            ]
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error starting data feed: {str(e)}")
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop data feed"""
        self._running = False
        await self.disconnect()
        
    async def _update_loop(self, symbol: str) -> None:
        """
        Update loop for symbol
        
        Args:
            symbol: Trading pair symbol
        """
        while self._running:
            try:
                # Fetch latest data
                data = await self._fetch_data(symbol)
                
                async with self._lock:
                    self._last_data[symbol] = data
                    
                # Notify subscribers
                await self._notify_subscribers(symbol, data)
                
            except Exception as e:
                logger.error(
                    f"Error updating {symbol} data: {str(e)}"
                )
                
            await asyncio.sleep(self.update_interval)
            
    def subscribe(self, callback) -> None:
        """
        Subscribe to data updates
        
        Args:
            callback: Async callback function
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            
    def unsubscribe(self, callback) -> None:
        """
        Unsubscribe from data updates
        
        Args:
            callback: Subscribed callback function
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            
    async def _notify_subscribers(
        self,
        symbol: str,
        data: Dict
    ) -> None:
        """
        Notify subscribers of data update
        
        Args:
            symbol: Updated symbol
            data: New market data
        """
        for callback in self._subscribers:
            try:
                await callback(symbol, data)
            except Exception as e:
                logger.error(
                    f"Error in subscriber callback: {str(e)}"
                )
                
    def get_last_data(
        self,
        symbol: Optional[str] = None
    ) -> Dict:
        """
        Get last received market data
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            Market data dictionary
        """
        if symbol:
            return self._last_data.get(symbol, {})
        return self._last_data.copy()
        
    @property
    def is_running(self) -> bool:
        """Check if feed is running"""
        return self._running
