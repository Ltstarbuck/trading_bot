"""
Base API adapter interface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import aiohttp
import asyncio
from loguru import logger

class APIAdapter(ABC):
    """Abstract base class for API adapters"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        timeout: int = 30,
        rate_limit: int = 10,
        retry_attempts: int = 3,
        retry_delay: int = 1
    ):
        """
        Initialize adapter
        
        Args:
            api_key: API key
            api_secret: API secret
            base_url: Base API URL
            timeout: Request timeout
            rate_limit: Requests per second
            retry_attempts: Max retry attempts
            retry_delay: Delay between retries
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Initialize rate limiter
        self.request_times: List[float] = []
        self.rate_limit_lock = asyncio.Lock()
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with API
        
        Returns:
            True if authenticated
        """
        pass
        
    @abstractmethod
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
        pass
        
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limit"""
        async with self.rate_limit_lock:
            current_time = datetime.now().timestamp()
            
            # Remove old requests
            self.request_times = [
                t for t in self.request_times
                if current_time - t < 1.0
            ]
            
            # Check limit
            if len(self.request_times) >= self.rate_limit:
                sleep_time = 1.0 - (current_time - self.request_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    
            # Add new request
            self.request_times.append(current_time)
            
    async def request(
        self,
        method: str,
        endpoint: str,
        authenticate: bool = False,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Any:
        """
        Make API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            authenticate: Sign request
            params: Query parameters
            data: Request data
            headers: Request headers
            timeout: Request timeout
            
        Returns:
            Response data
        """
        try:
            # Check rate limit
            await self._check_rate_limit()
            
            # Build URL
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            # Get headers
            if authenticate:
                request_headers = await self.sign_request(
                    method,
                    endpoint,
                    params,
                    data
                )
                if headers:
                    request_headers.update(headers)
            else:
                request_headers = headers or {}
                
            # Make request with retries
            for attempt in range(self.retry_attempts):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.request(
                            method,
                            url,
                            params=params,
                            json=data,
                            headers=request_headers,
                            timeout=timeout or self.timeout
                        ) as response:
                            # Check status
                            if response.status == 429:  # Rate limit
                                retry_after = int(
                                    response.headers.get(
                                        'Retry-After',
                                        self.retry_delay
                                    )
                                )
                                await asyncio.sleep(retry_after)
                                continue
                                
                            response.raise_for_status()
                            return await response.json()
                            
                except aiohttp.ClientError as e:
                    if attempt == self.retry_attempts - 1:
                        raise
                    await asyncio.sleep(self.retry_delay)
                    
            raise Exception("Max retry attempts exceeded")
            
        except Exception as e:
            logger.error(
                f"API request failed: {str(e)}\n"
                f"Method: {method}\n"
                f"Endpoint: {endpoint}\n"
                f"Params: {params}\n"
                f"Data: {data}"
            )
            raise
            
    async def get(
        self,
        endpoint: str,
        authenticate: bool = False,
        **kwargs
    ) -> Any:
        """Make GET request"""
        return await self.request('GET', endpoint, authenticate, **kwargs)
        
    async def post(
        self,
        endpoint: str,
        authenticate: bool = False,
        **kwargs
    ) -> Any:
        """Make POST request"""
        return await self.request('POST', endpoint, authenticate, **kwargs)
        
    async def put(
        self,
        endpoint: str,
        authenticate: bool = False,
        **kwargs
    ) -> Any:
        """Make PUT request"""
        return await self.request('PUT', endpoint, authenticate, **kwargs)
        
    async def delete(
        self,
        endpoint: str,
        authenticate: bool = False,
        **kwargs
    ) -> Any:
        """Make DELETE request"""
        return await self.request('DELETE', endpoint, authenticate, **kwargs)
        
    async def ping(self) -> bool:
        """
        Check API connectivity
        
        Returns:
            True if connected
        """
        try:
            await self.get('ping')
            return True
        except Exception:
            return False
            
    async def get_server_time(self) -> Optional[datetime]:
        """
        Get server timestamp
        
        Returns:
            Server datetime
        """
        try:
            response = await self.get('time')
            timestamp = response.get('serverTime', response.get('timestamp'))
            return datetime.fromtimestamp(timestamp / 1000)
        except Exception:
            return None
