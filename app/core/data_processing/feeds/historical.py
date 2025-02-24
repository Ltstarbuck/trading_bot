"""
Historical market data feed
"""

from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger
import ccxt.async_support as ccxt

from .base_feed import MarketDataFeed
from ...utils.validation import validate_trading_pair, validate_timeframe

class HistoricalFeed:
    """Retrieves and processes historical market data"""
    
    def __init__(
        self,
        exchange_id: str,
        api_key: str = "",
        api_secret: str = "",
        rate_limit: int = 1
    ):
        """
        Initialize historical feed
        
        Args:
            exchange_id: CCXT exchange ID
            api_key: Optional API key
            api_secret: Optional API secret
            rate_limit: Requests per second limit
        """
        # Initialize exchange
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'asyncio_loop': asyncio.get_event_loop()
        })
        
        self.rate_limit = rate_limit
        self._last_request = datetime.min
        self._cache: Dict[str, pd.DataFrame] = {}
        self._lock = asyncio.Lock()
        
    async def fetch_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data
        
        Args:
            symbol: Trading pair symbol
            timeframe: Time interval (e.g. '1m', '1h', '1d')
            start_time: Start timestamp
            end_time: Optional end timestamp
            limit: Optional limit on number of candles
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Validate inputs
            validate_trading_pair(symbol)
            validate_timeframe(timeframe)
            
            if end_time is None:
                end_time = datetime.now()
                
            # Check cache
            cache_key = f"{symbol}_{timeframe}"
            if cache_key in self._cache:
                cached_df = self._cache[cache_key]
                if self._is_cache_valid(cached_df, start_time, end_time):
                    return self._filter_cached_data(
                        cached_df, start_time, end_time
                    )
                    
            # Fetch data
            async with self._lock:
                ohlcv_data = await self._fetch_ohlcv_chunks(
                    symbol, timeframe, start_time, end_time, limit
                )
                
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv_data,
                columns=[
                    'timestamp', 'open', 'high',
                    'low', 'close', 'volume'
                ]
            )
            
            # Process DataFrame
            df['timestamp'] = pd.to_datetime(
                df['timestamp'], unit='ms'
            )
            df.set_index('timestamp', inplace=True)
            
            # Calculate additional metrics
            df['typical_price'] = (
                df['high'] + df['low'] + df['close']
            ) / 3
            df['vwap'] = (
                df['typical_price'] * df['volume']
            ).cumsum() / df['volume'].cumsum()
            
            # Update cache
            self._cache[cache_key] = df
            
            return df
            
        except Exception as e:
            logger.error(
                f"Error fetching historical data for {symbol}: {str(e)}"
            )
            raise
            
    async def fetch_historical_trades(
        self,
        symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical trades
        
        Args:
            symbol: Trading pair symbol
            start_time: Start timestamp
            end_time: Optional end timestamp
            limit: Optional limit on number of trades
            
        Returns:
            DataFrame with trade data
        """
        try:
            validate_trading_pair(symbol)
            
            if end_time is None:
                end_time = datetime.now()
                
            async with self._lock:
                trades = await self._fetch_trades_chunks(
                    symbol, start_time, end_time, limit
                )
                
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            
            if len(df) > 0:
                df['timestamp'] = pd.to_datetime(
                    df['timestamp'], unit='ms'
                )
                df.set_index('timestamp', inplace=True)
                
            return df
            
        except Exception as e:
            logger.error(
                f"Error fetching historical trades for {symbol}: {str(e)}"
            )
            raise
            
    async def _fetch_ohlcv_chunks(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List:
        """Fetch OHLCV data in chunks"""
        all_candles = []
        current_time = start_time
        
        while current_time < end_time:
            # Apply rate limiting
            await self._rate_limit()
            
            # Fetch chunk
            since = int(current_time.timestamp() * 1000)
            candles = await self.exchange.fetch_ohlcv(
                symbol, timeframe, since, limit
            )
            
            if not candles:
                break
                
            all_candles.extend(candles)
            
            # Update current time
            last_candle_time = datetime.fromtimestamp(
                candles[-1][0] / 1000
            )
            if last_candle_time <= current_time:
                break
                
            current_time = last_candle_time
            
            # Check if we have enough data
            if limit and len(all_candles) >= limit:
                all_candles = all_candles[:limit]
                break
                
        return all_candles
        
    async def _fetch_trades_chunks(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List:
        """Fetch trades in chunks"""
        all_trades = []
        current_time = start_time
        
        while current_time < end_time:
            # Apply rate limiting
            await self._rate_limit()
            
            # Fetch chunk
            since = int(current_time.timestamp() * 1000)
            trades = await self.exchange.fetch_trades(
                symbol, since, limit
            )
            
            if not trades:
                break
                
            all_trades.extend(trades)
            
            # Update current time
            last_trade_time = datetime.fromtimestamp(
                trades[-1]['timestamp'] / 1000
            )
            if last_trade_time <= current_time:
                break
                
            current_time = last_trade_time
            
            # Check if we have enough data
            if limit and len(all_trades) >= limit:
                all_trades = all_trades[:limit]
                break
                
        return all_trades
        
    async def _rate_limit(self) -> None:
        """Apply rate limiting"""
        async with self._lock:
            now = datetime.now()
            elapsed = (now - self._last_request).total_seconds()
            
            if elapsed < (1 / self.rate_limit):
                await asyncio.sleep(1 / self.rate_limit - elapsed)
                
            self._last_request = datetime.now()
            
    def _is_cache_valid(
        self,
        df: pd.DataFrame,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if cached data covers the requested range"""
        if len(df) == 0:
            return False
            
        cache_start = df.index.min()
        cache_end = df.index.max()
        
        return (
            cache_start <= start_time and
            cache_end >= end_time
        )
        
    def _filter_cached_data(
        self,
        df: pd.DataFrame,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Filter cached data to requested range"""
        return df[
            (df.index >= start_time) &
            (df.index <= end_time)
        ]
        
    async def close(self) -> None:
        """Close exchange connection"""
        try:
            await self.exchange.close()
        except Exception as e:
            logger.error(f"Error closing exchange: {str(e)}")
            
    def clear_cache(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> None:
        """
        Clear data cache
        
        Args:
            symbol: Optional symbol to clear
            timeframe: Optional timeframe to clear
        """
        if symbol and timeframe:
            cache_key = f"{symbol}_{timeframe}"
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()
