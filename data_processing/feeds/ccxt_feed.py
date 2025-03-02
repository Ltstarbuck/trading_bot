"""
CCXT market data feed
"""

from typing import Dict, List, Any
from decimal import Decimal
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime
from loguru import logger

from .base_feed import MarketDataFeed

class CCXTFeed(MarketDataFeed):
    """Market data feed using CCXT"""
    
    def __init__(
        self,
        exchange_id: str,
        symbols: List[str],
        api_key: str = "",
        api_secret: str = "",
        update_interval: float = 1.0
    ):
        """
        Initialize CCXT feed
        
        Args:
            exchange_id: CCXT exchange ID
            symbols: List of trading pairs
            api_key: Optional API key
            api_secret: Optional API secret
            update_interval: Update interval in seconds
        """
        super().__init__(symbols, update_interval)
        
        # Initialize exchange
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'asyncio_loop': asyncio.get_event_loop()
        })
        
    async def connect(self) -> None:
        """
        Connect to exchange
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Load markets
            await self.exchange.load_markets()
            
            # Validate symbols
            for symbol in self.symbols:
                if symbol not in self.exchange.markets:
                    raise ValueError(
                        f"Invalid symbol for {self.exchange.id}: {symbol}"
                    )
                    
            logger.info(
                f"Connected to {self.exchange.id}"
            )
            
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to {self.exchange.id}: {str(e)}"
            )
            
    async def disconnect(self) -> None:
        """Disconnect from exchange"""
        try:
            await self.exchange.close()
            logger.info(
                f"Disconnected from {self.exchange.id}"
            )
        except Exception as e:
            logger.error(
                f"Error disconnecting from {self.exchange.id}: {str(e)}"
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
            # Fetch ticker
            ticker = await self.exchange.fetch_ticker(symbol)
            
            # Fetch order book
            order_book = await self.exchange.fetch_order_book(symbol)
            
            # Fetch recent trades
            trades = await self.exchange.fetch_trades(symbol, limit=50)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.fromtimestamp(
                    ticker['timestamp'] / 1000
                ).isoformat(),
                'bid': str(ticker['bid']),
                'ask': str(ticker['ask']),
                'last': str(ticker['last']),
                'baseVolume': str(ticker['baseVolume']),
                'quoteVolume': str(ticker['quoteVolume']),
                'high': str(ticker['high']),
                'low': str(ticker['low']),
                'orderbook': {
                    'bids': [
                        [str(price), str(amount)]
                        for price, amount in order_book['bids']
                    ],
                    'asks': [
                        [str(price), str(amount)]
                        for price, amount in order_book['asks']
                    ]
                },
                'trades': [
                    {
                        'timestamp': datetime.fromtimestamp(
                            trade['timestamp'] / 1000
                        ).isoformat(),
                        'side': trade['side'],
                        'price': str(trade['price']),
                        'amount': str(trade['amount'])
                    }
                    for trade in trades
                ]
            }
            
        except Exception as e:
            logger.error(
                f"Error fetching {symbol} data from "
                f"{self.exchange.id}: {str(e)}"
            )
            raise
