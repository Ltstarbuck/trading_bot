"""
Coinbase Pro API adapter
"""

import hmac
import hashlib
import time
import base64
from typing import Dict, Optional
from loguru import logger

from .base import APIAdapter

class CoinbaseAdapter(APIAdapter):
    """Coinbase Pro API adapter"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str,
        sandbox: bool = False,
        **kwargs
    ):
        """
        Initialize adapter
        
        Args:
            api_key: API key
            api_secret: API secret
            passphrase: API passphrase
            sandbox: Use sandbox
            **kwargs: Additional arguments
        """
        base_url = (
            'https://api-public.sandbox.pro.coinbase.com'
            if sandbox else
            'https://api.pro.coinbase.com'
        )
        super().__init__(api_key, api_secret, base_url, **kwargs)
        self.passphrase = passphrase
        
    async def authenticate(self) -> bool:
        """
        Authenticate with API
        
        Returns:
            True if authenticated
        """
        try:
            # Test API key permissions
            response = await self.get(
                'accounts',
                authenticate=True
            )
            return isinstance(response, list)
        except Exception as e:
            logger.error(f"Coinbase authentication failed: {str(e)}")
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
        # Get timestamp
        timestamp = str(int(time.time()))
        
        # Create message
        message = f"{timestamp}{method.upper()}/{endpoint}"
        if data:
            message += str(data)
            
        # Create signature
        secret = base64.b64decode(self.api_secret)
        signature = hmac.new(
            secret,
            message.encode('utf-8'),
            hashlib.sha256
        )
        signature_b64 = base64.b64encode(
            signature.digest()
        ).decode('utf-8')
        
        # Add headers
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        return headers
        
    async def get_products(self) -> Dict:
        """
        Get available trading pairs
        
        Returns:
            Product data
        """
        return await self.get('products')
        
    async def get_ticker(self, product_id: str) -> Dict:
        """
        Get ticker price
        
        Args:
            product_id: Trading pair
            
        Returns:
            Ticker data
        """
        return await self.get(f'products/{product_id}/ticker')
        
    async def get_order_book(
        self,
        product_id: str,
        level: int = 2
    ) -> Dict:
        """
        Get order book
        
        Args:
            product_id: Trading pair
            level: Detail level (1, 2, or 3)
            
        Returns:
            Order book data
        """
        return await self.get(
            f'products/{product_id}/book',
            params={'level': level}
        )
        
    async def get_trades(
        self,
        product_id: str,
        limit: int = 100
    ) -> Dict:
        """
        Get recent trades
        
        Args:
            product_id: Trading pair
            limit: Number of trades
            
        Returns:
            Trade data
        """
        return await self.get(
            f'products/{product_id}/trades',
            params={'limit': limit}
        )
        
    async def get_candles(
        self,
        product_id: str,
        granularity: int = 60,
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> Dict:
        """
        Get historical candles
        
        Args:
            product_id: Trading pair
            granularity: Candle duration in seconds
            start: Start time
            end: End time
            
        Returns:
            Candle data
        """
        params = {'granularity': granularity}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
            
        return await self.get(
            f'products/{product_id}/candles',
            params=params
        )
        
    async def create_order(
        self,
        product_id: str,
        side: str,
        order_type: str,
        size: Optional[float] = None,
        funds: Optional[float] = None,
        price: Optional[float] = None,
        time_in_force: str = 'GTC',
        **kwargs
    ) -> Dict:
        """
        Create new order
        
        Args:
            product_id: Trading pair
            side: Order side
            order_type: Order type
            size: Order size
            funds: Order funds
            price: Order price
            time_in_force: Time in force
            **kwargs: Additional parameters
            
        Returns:
            Order data
        """
        data = {
            'product_id': product_id,
            'side': side,
            'type': order_type,
            'time_in_force': time_in_force,
            **kwargs
        }
        
        if size:
            data['size'] = size
        if funds:
            data['funds'] = funds
        if price:
            data['price'] = price
            
        return await self.post(
            'orders',
            authenticate=True,
            data=data
        )
        
    async def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel order
        
        Args:
            order_id: Order ID
            
        Returns:
            Cancellation data
        """
        return await self.delete(
            f'orders/{order_id}',
            authenticate=True
        )
        
    async def get_orders(
        self,
        status: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> Dict:
        """
        Get orders
        
        Args:
            status: Order status
            product_id: Trading pair
            
        Returns:
            Order data
        """
        params = {}
        if status:
            params['status'] = status
        if product_id:
            params['product_id'] = product_id
            
        return await self.get(
            'orders',
            authenticate=True,
            params=params
        )
        
    async def get_accounts(self) -> Dict:
        """
        Get trading accounts
        
        Returns:
            Account data
        """
        return await self.get(
            'accounts',
            authenticate=True
        )
