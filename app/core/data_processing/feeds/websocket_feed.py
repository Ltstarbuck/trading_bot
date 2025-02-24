"""
WebSocket market data feed
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
import asyncio
import json
import websockets
from datetime import datetime
from loguru import logger

from .base_feed import MarketDataFeed

class WebSocketFeed(MarketDataFeed):
    """Market data feed using WebSocket"""
    
    def __init__(
        self,
        url: str,
        symbols: List[str],
        subscribe_message: Dict,
        message_parser: Optional[callable] = None,
        ping_interval: float = 30.0,
        update_interval: float = 1.0
    ):
        """
        Initialize WebSocket feed
        
        Args:
            url: WebSocket endpoint URL
            symbols: List of trading pairs
            subscribe_message: Subscription message template
            message_parser: Optional message parser function
            ping_interval: Ping interval in seconds
            update_interval: Update interval in seconds
        """
        super().__init__(symbols, update_interval)
        self.url = url
        self.subscribe_message = subscribe_message
        self.message_parser = message_parser
        self.ping_interval = ping_interval
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._ping_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> None:
        """
        Connect to WebSocket feed
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Connect to WebSocket
            self._ws = await websockets.connect(self.url)
            
            # Subscribe to symbols
            for symbol in self.symbols:
                message = self.subscribe_message.copy()
                message['symbol'] = symbol
                await self._ws.send(json.dumps(message))
                
            # Start ping task
            self._ping_task = asyncio.create_task(
                self._ping_loop()
            )
            
            logger.info(f"Connected to WebSocket feed: {self.url}")
            
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to WebSocket feed: {str(e)}"
            )
            
    async def disconnect(self) -> None:
        """Disconnect from WebSocket feed"""
        try:
            if self._ping_task:
                self._ping_task.cancel()
                
            if self._ws:
                await self._ws.close()
                
            logger.info(f"Disconnected from WebSocket feed: {self.url}")
            
        except Exception as e:
            logger.error(
                f"Error disconnecting from WebSocket feed: {str(e)}"
            )
            
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
        try:
            if not self._ws:
                raise ConnectionError("WebSocket not connected")
                
            # Receive message
            message = await self._ws.recv()
            
            # Parse message
            if self.message_parser:
                data = self.message_parser(message)
            else:
                data = json.loads(message)
                
            return data
            
        except Exception as e:
            logger.error(
                f"Error fetching {symbol} data from "
                f"WebSocket feed: {str(e)}"
            )
            raise
            
    async def _ping_loop(self) -> None:
        """Send periodic ping messages"""
        while self._running:
            try:
                if self._ws:
                    await self._ws.ping()
            except Exception as e:
                logger.error(f"Error sending ping: {str(e)}")
                
            await asyncio.sleep(self.ping_interval)
            
    async def send_message(self, message: Dict) -> None:
        """
        Send message to WebSocket server
        
        Args:
            message: Message to send
            
        Raises:
            ConnectionError: If WebSocket not connected
        """
        if not self._ws:
            raise ConnectionError("WebSocket not connected")
            
        await self._ws.send(json.dumps(message))
