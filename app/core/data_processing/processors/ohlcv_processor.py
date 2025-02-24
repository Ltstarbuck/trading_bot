"""
OHLCV data processor
"""

from typing import Dict, List, Optional, Union
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

class OHLCVProcessor:
    """Processes OHLCV (Open, High, Low, Close, Volume) data"""
    
    def __init__(
        self,
        timeframes: Optional[List[str]] = None,
        cache_size: int = 1000
    ):
        """
        Initialize OHLCV processor
        
        Args:
            timeframes: List of timeframes to process
            cache_size: Maximum number of candles to cache
        """
        self.timeframes = timeframes or ['1m', '5m', '15m', '1h', '4h', '1d']
        self.cache_size = cache_size
        self._cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        
    def process_ohlcv(
        self,
        symbol: str,
        data: pd.DataFrame,
        timeframe: str = '1m'
    ) -> pd.DataFrame:
        """
        Process OHLCV data
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame
            timeframe: Base timeframe of data
            
        Returns:
            Processed DataFrame
        """
        try:
            # Initialize cache for symbol
            if symbol not in self._cache:
                self._cache[symbol] = {}
                
            # Resample to different timeframes
            resampled = {}
            for tf in self.timeframes:
                if tf not in self._cache[symbol]:
                    self._cache[symbol][tf] = pd.DataFrame()
                    
                # Resample data
                tf_data = self._resample_ohlcv(data, tf)
                
                # Update cache
                cached = self._cache[symbol][tf]
                updated = pd.concat([cached, tf_data])
                
                # Remove duplicates and sort
                updated = updated[~updated.index.duplicated(keep='last')]
                updated.sort_index(inplace=True)
                
                # Maintain cache size
                if len(updated) > self.cache_size:
                    updated = updated.iloc[-self.cache_size:]
                    
                self._cache[symbol][tf] = updated
                resampled[tf] = updated
                
            # Calculate additional metrics
            for tf, df in resampled.items():
                self._calculate_metrics(df)
                
            return resampled[timeframe]
            
        except Exception as e:
            logger.error(f"Error processing OHLCV data: {str(e)}")
            raise
            
    def _resample_ohlcv(
        self,
        data: pd.DataFrame,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Resample OHLCV data to different timeframe
        
        Args:
            data: OHLCV DataFrame
            timeframe: Target timeframe
            
        Returns:
            Resampled DataFrame
        """
        # Convert timeframe to pandas offset
        offset = self._timeframe_to_offset(timeframe)
        
        # Resample data
        resampled = data.resample(offset).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        return resampled
        
    def _calculate_metrics(self, df: pd.DataFrame) -> None:
        """
        Calculate additional metrics
        
        Args:
            df: OHLCV DataFrame
        """
        try:
            # Price metrics
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
            df['median_price'] = (df['high'] + df['low']) / 2
            
            # Volume metrics
            df['vwap'] = (df['typical_price'] * df['volume']).cumsum() / df['volume'].cumsum()
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            
            # Returns
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Volatility
            df['volatility'] = df['returns'].rolling(window=20).std()
            
            # Price changes
            df['price_change'] = df['close'] - df['open']
            df['price_change_pct'] = (df['close'] - df['open']) / df['open'] * 100
            
            # Candle metrics
            df['body_size'] = abs(df['close'] - df['open'])
            df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
            df['total_range'] = df['high'] - df['low']
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            
    def _timeframe_to_offset(self, timeframe: str) -> str:
        """
        Convert timeframe to pandas offset string
        
        Args:
            timeframe: Timeframe string (e.g. '1m', '1h')
            
        Returns:
            Pandas offset string
        """
        units = {
            'm': 'T',  # minute
            'h': 'H',  # hour
            'd': 'D',  # day
            'w': 'W',  # week
            'M': 'M'   # month
        }
        
        # Extract number and unit
        number = int(''.join(filter(str.isdigit, timeframe)))
        unit = ''.join(filter(str.isalpha, timeframe))
        
        if unit not in units:
            raise ValueError(f"Invalid timeframe unit: {unit}")
            
        return f"{number}{units[unit]}"
        
    def get_cached_data(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Get cached data for symbol and timeframe
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            
        Returns:
            Cached DataFrame or None
        """
        return self._cache.get(symbol, {}).get(timeframe)
        
    def clear_cache(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> None:
        """
        Clear cached data
        
        Args:
            symbol: Optional symbol to clear
            timeframe: Optional timeframe to clear
        """
        if symbol:
            if timeframe:
                self._cache[symbol].pop(timeframe, None)
            else:
                self._cache.pop(symbol, None)
        else:
            self._cache.clear()
