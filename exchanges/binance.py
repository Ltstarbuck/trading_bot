"""
Binance Exchange Implementation
"""

import ccxt.async_support as ccxt
from decimal import Decimal
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger

from .base_exchange import BaseExchange

class BinanceExchange(BaseExchange):
    """Binance exchange implementation"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        """Initialize Binance exchange"""
        super().__init__(api_key, api_secret, testnet)
        
        # Configure ccxt
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        }
        
        if testnet:
            config['urls'] = {
                'api': 'https://testnet.binance.vision/api',
            }
            
        self.exchange = ccxt.binance(config)
        
    async def connect(self) -> bool:
        """Establish connection to exchange"""
        try:
            await self.exchange.load_markets()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {str(e)}")
            return False
            
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker data"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'last': Decimal(str(ticker['last'])),
                'bid': Decimal(str(ticker['bid'])),
                'ask': Decimal(str(ticker['ask'])),
                'volume': Decimal(str(ticker['baseVolume'])),
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            raise
            
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book data"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            return {
                'bids': [[Decimal(str(price)), Decimal(str(amount))] 
                        for price, amount in orderbook['bids']],
                'asks': [[Decimal(str(price)), Decimal(str(amount))] 
                        for price, amount in orderbook['asks']],
                'timestamp': orderbook['timestamp']
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {str(e)}")
            raise
            
    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: Decimal,
        price: Optional[Decimal] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Place a new order"""
        try:
            params = params or {}
            order = await self.exchange.create_order(
                symbol,
                order_type,
                side,
                float(amount),
                float(price) if price else None,
                params
            )
            return order
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise
            
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an existing order"""
        try:
            return await self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            raise
            
    async def get_balance(self, currency: Optional[str] = None) -> Dict:
        """Get account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            if currency:
                return {
                    'free': Decimal(str(balance[currency]['free'])),
                    'used': Decimal(str(balance[currency]['used'])),
                    'total': Decimal(str(balance[currency]['total']))
                }
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            raise
            
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders"""
        try:
            return await self.exchange.fetch_open_orders(symbol)
        except Exception as e:
            logger.error(f"Error fetching open orders: {str(e)}")
            raise
            
    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get status of an order"""
        try:
            return await self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error fetching order status: {str(e)}")
            raise
            
    async def get_trade_fee(self, symbol: str) -> Dict:
        """Get trading fees"""
        try:
            return await self.exchange.fetch_trading_fee(symbol)
        except Exception as e:
            logger.error(f"Error fetching trading fee: {str(e)}")
            raise
            
    async def get_price_history(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get historical price data"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching price history: {str(e)}")
            raise
            
    def get_markets(self) -> List[Dict]:
        """Get available markets"""
        return list(self.exchange.markets.values())
        
    async def get_volatility(self, symbol: str, window: int = 24) -> Decimal:
        """Calculate volatility for symbol"""
        try:
            # Get hourly candles for the specified window
            ohlcv = await self.get_price_history(
                symbol,
                timeframe='1h',
                limit=window
            )
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Calculate returns
            df['returns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Calculate volatility (standard deviation of returns)
            volatility = Decimal(str(df['returns'].std() * np.sqrt(24)))  # Annualized
            
            return volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            raise
