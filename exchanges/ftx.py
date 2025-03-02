"""
FTX Exchange Implementation
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import asyncio
import hmac
import hashlib
import time
import json
import aiohttp
from loguru import logger

from .base_exchange import BaseExchange

class FTXExchange(BaseExchange):
    """FTX exchange implementation"""
    
    def __init__(self, config: Dict):
        """Initialize FTX exchange"""
        super().__init__(config)
        self.api_url = config['api_url']
        self.ws_url = config['websocket_url']
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.subaccount = config.get('subaccount')
        
        # Rate limiting
        self.rate_limits = config['rate_limits']
        self._last_request_time = 0
        self._request_count = 0
        
    async def _get_server_time(self) -> int:
        """Get server timestamp"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/time") as response:
                if response.status == 200:
                    data = await response.json()
                    return int(data['result'] * 1000)
                raise Exception(f"Error getting server time: {response.status}")
                
    def _generate_signature(
        self,
        method: str,
        path: str,
        params: Dict = None
    ) -> Tuple[str, str, str]:
        """Generate API request signature"""
        ts = int(time.time() * 1000)
        params = params or {}
        
        if method == 'GET' and params:
            path = path + '?' + '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
            params = {}
            
        signature_payload = f"{ts}{method}{path}"
        if method != 'GET':
            signature_payload += json.dumps(params)
            
        signature = hmac.new(
            self.api_secret.encode(),
            signature_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "FTX-KEY": self.api_key,
            "FTX-SIGN": signature,
            "FTX-TS": str(ts)
        }
        
        if self.subaccount:
            headers["FTX-SUBACCOUNT"] = self.subaccount
            
        return path, json.dumps(params) if params else "", headers
        
    async def _make_request(
        self,
        method: str,
        path: str,
        params: Dict = None,
        auth: bool = False
    ) -> Dict:
        """Make API request"""
        # Rate limit check
        current_time = time.time()
        if current_time - self._last_request_time < 1:
            if self._request_count >= self.rate_limits['requests_per_minute'] / 60:
                await asyncio.sleep(1)
                self._request_count = 0
                self._last_request_time = current_time
                
        try:
            if auth:
                path, data, headers = self._generate_signature(method, path, params)
            else:
                headers = {}
                data = json.dumps(params) if params else ""
                
            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    async with session.get(
                        f"{self.api_url}{path}",
                        headers=headers
                    ) as response:
                        result = await response.json()
                else:
                    async with session.post(
                        f"{self.api_url}{path}",
                        headers=headers,
                        data=data
                    ) as response:
                        result = await response.json()
                        
                if response.status != 200:
                    raise Exception(f"API error: {result}")
                    
                self._request_count += 1
                self._last_request_time = current_time
                
                return result['result']
                
        except Exception as e:
            logger.error(f"Error making request: {str(e)}")
            raise
            
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker data"""
        return await self._make_request('GET', f"/markets/{symbol}")
        
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """Get current orderbook"""
        return await self._make_request(
            'GET',
            f"/markets/{symbol}/orderbook",
            {'depth': depth}
        )
        
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent trades"""
        return await self._make_request(
            'GET',
            f"/markets/{symbol}/trades",
            {'limit': limit}
        )
        
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get historical candles"""
        return await self._make_request(
            'GET',
            f"/markets/{symbol}/candles",
            {
                'resolution': timeframe,
                'limit': limit
            }
        )
        
    async def get_balance(self, currency: str = None) -> Dict:
        """Get account balance"""
        balances = await self._make_request('GET', "/wallet/balances", auth=True)
        if currency:
            return next(
                (b for b in balances if b['coin'] == currency),
                {'coin': currency, 'free': 0, 'total': 0}
            )
        return balances
        
    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        return await self._make_request('GET', "/positions", auth=True)
        
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: Decimal,
        price: Optional[Decimal] = None,
        params: Dict = None
    ) -> Dict:
        """Create new order"""
        order_data = {
            'market': symbol,
            'side': side.lower(),
            'type': order_type.lower(),
            'size': float(amount),
            'price': float(price) if price else None,
            'reduceOnly': params.get('reduce_only', False),
            'ioc': params.get('ioc', False),
            'postOnly': params.get('post_only', False)
        }
        
        return await self._make_request(
            'POST',
            "/orders",
            order_data,
            auth=True
        )
        
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel existing order"""
        return await self._make_request(
            'DELETE',
            f"/orders/{order_id}",
            auth=True
        )
        
    async def cancel_all_orders(
        self,
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """Cancel all orders"""
        params = {'market': symbol} if symbol else {}
        return await self._make_request(
            'DELETE',
            "/orders",
            params,
            auth=True
        )
        
    async def get_order(self, order_id: str) -> Dict:
        """Get order details"""
        return await self._make_request(
            'GET',
            f"/orders/{order_id}",
            auth=True
        )
        
    async def get_open_orders(
        self,
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """Get open orders"""
        params = {'market': symbol} if symbol else {}
        return await self._make_request(
            'GET',
            "/orders",
            params,
            auth=True
        )
        
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get order history"""
        params = {
            'market': symbol,
            'limit': limit
        } if symbol else {'limit': limit}
        
        return await self._make_request(
            'GET',
            "/orders/history",
            params,
            auth=True
        )
        
    async def get_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get trade history"""
        params = {
            'market': symbol,
            'limit': limit
        } if symbol else {'limit': limit}
        
        return await self._make_request(
            'GET',
            "/fills",
            params,
            auth=True
        )
        
    async def get_leverage(self) -> int:
        """Get account leverage"""
        account = await self._make_request('GET', "/account", auth=True)
        return account['leverage']
        
    async def set_leverage(self, leverage: int) -> Dict:
        """Set account leverage"""
        return await self._make_request(
            'POST',
            "/account/leverage",
            {'leverage': leverage},
            auth=True
        )
        
    async def get_funding_rates(
        self,
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """Get funding rates"""
        params = {'future': symbol} if symbol else {}
        return await self._make_request(
            'GET',
            "/funding_rates",
            params
        )
        
    async def get_funding_payments(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """Get funding payments"""
        params = {}
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
            
        return await self._make_request(
            'GET',
            "/funding_payments",
            params,
            auth=True
        )
