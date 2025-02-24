"""
Binance API adapter
"""

import hmac
import hashlib
import time
from typing import Dict, Optional
from urllib.parse import urlencode
from loguru import logger

from .base import APIAdapter

class BinanceAdapter(APIAdapter):
    """Binance API adapter"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        **kwargs
    ):
        """
        Initialize adapter
        
        Args:
            api_key: API key
            api_secret: API secret
            testnet: Use testnet
            **kwargs: Additional arguments
        """
        base_url = (
            'https://testnet.binance.vision/api'
            if testnet else
            'https://api.binance.com/api'
        )
        super().__init__(api_key, api_secret, base_url, **kwargs)
        
    async def authenticate(self) -> bool:
        """
        Authenticate with API
        
        Returns:
            True if authenticated
        """
        try:
            # Test API key permissions
            response = await self.get(
                'v3/account',
                authenticate=True
            )
            return bool(response.get('accountType'))
        except Exception as e:
            logger.error(f"Binance authentication failed: {str(e)}")
            return False
            
    async def sign_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Sign API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request data
            
        Returns:
            Headers with signature
        """
        # Add timestamp
        request_params = params or {}
        request_params['timestamp'] = int(time.time() * 1000)
        
        # Add signature
        query_string = urlencode(request_params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        request_params['signature'] = signature
        
        # Add headers
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        return headers
        
    async def get_exchange_info(self) -> Dict:
        """
        Get exchange information
        
        Returns:
            Exchange info
        """
        return await self.get('v3/exchangeInfo')
        
    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker price
        
        Args:
            symbol: Trading pair
            
        Returns:
            Ticker data
        """
        return await self.get(
            'v3/ticker/price',
            params={'symbol': symbol}
        )
        
    async def get_order_book(
        self,
        symbol: str,
        limit: int = 100
    ) -> Dict:
        """
        Get order book
        
        Args:
            symbol: Trading pair
            limit: Number of orders
            
        Returns:
            Order book data
        """
        return await self.get(
            'v3/depth',
            params={
                'symbol': symbol,
                'limit': limit
            }
        )
        
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 500
    ) -> Dict:
        """
        Get recent trades
        
        Args:
            symbol: Trading pair
            limit: Number of trades
            
        Returns:
            Trade data
        """
        return await self.get(
            'v3/trades',
            params={
                'symbol': symbol,
                'limit': limit
            }
        )
        
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict:
        """
        Get kline/candlestick data
        
        Args:
            symbol: Trading pair
            interval: Kline interval
            limit: Number of candles
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            Kline data
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        return await self.get('v3/klines', params=params)
        
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = 'GTC',
        **kwargs
    ) -> Dict:
        """
        Create new order
        
        Args:
            symbol: Trading pair
            side: Order side
            order_type: Order type
            quantity: Order quantity
            price: Order price
            time_in_force: Time in force
            **kwargs: Additional parameters
            
        Returns:
            Order data
        """
        data = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'timeInForce': time_in_force,
            **kwargs
        }
        
        if price:
            data['price'] = price
            
        return await self.post(
            'v3/order',
            authenticate=True,
            data=data
        )
        
    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None
    ) -> Dict:
        """
        Cancel order
        
        Args:
            symbol: Trading pair
            order_id: Order ID
            orig_client_order_id: Original client order ID
            
        Returns:
            Cancellation data
        """
        data = {'symbol': symbol}
        
        if order_id:
            data['orderId'] = order_id
        if orig_client_order_id:
            data['origClientOrderId'] = orig_client_order_id
            
        return await self.delete(
            'v3/order',
            authenticate=True,
            data=data
        )
        
    async def get_open_orders(
        self,
        symbol: Optional[str] = None
    ) -> Dict:
        """
        Get open orders
        
        Args:
            symbol: Trading pair
            
        Returns:
            Open orders
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
            
        return await self.get(
            'v3/openOrders',
            authenticate=True,
            params=params
        )
        
    async def get_account_info(self) -> Dict:
        """
        Get account information
        
        Returns:
            Account data
        """
        return await self.get(
            'v3/account',
            authenticate=True
        )
