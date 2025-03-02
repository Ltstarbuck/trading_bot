"""
Market data processing module
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from decimal import Decimal
from loguru import logger

class MarketData:
    """Handles market data processing and storage"""
    
    def __init__(self, timeframe: str = "1m"):
        """
        Initialize market data handler
        
        Args:
            timeframe: Data timeframe (e.g. '1m', '5m', '1h')
        """
        self.timeframe = timeframe
        self.data: Dict[str, pd.DataFrame] = {}  # Symbol -> OHLCV data
        
    def update_ohlcv(
        self,
        symbol: str,
        ohlcv_data: List[List[float]],
        columns: List[str] = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    ) -> None:
        """
        Update OHLCV data for a symbol
        
        Args:
            symbol: Trading symbol
            ohlcv_data: List of OHLCV data points
            columns: Column names
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=columns)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Update existing data
            if symbol in self.data:
                self.data[symbol] = pd.concat([
                    self.data[symbol],
                    df
                ]).drop_duplicates()
            else:
                self.data[symbol] = df
                
            # Sort by timestamp
            self.data[symbol].sort_index(inplace=True)
            
            logger.debug(f"Updated market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error updating market data for {symbol}: {str(e)}")
            
    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        """Get latest price for symbol"""
        try:
            if symbol in self.data:
                return Decimal(str(self.data[symbol]['close'].iloc[-1]))
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {str(e)}")
        return None
        
    def get_price_range(
        self,
        symbol: str,
        lookback: int = 20
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Get high/low price range over lookback period
        
        Args:
            symbol: Trading symbol
            lookback: Number of periods to look back
            
        Returns:
            Tuple of (high, low) prices
        """
        try:
            if symbol in self.data:
                df = self.data[symbol].iloc[-lookback:]
                return (
                    Decimal(str(df['high'].max())),
                    Decimal(str(df['low'].min()))
                )
        except Exception as e:
            logger.error(f"Error getting price range for {symbol}: {str(e)}")
        return None, None
        
    def get_volatility(
        self,
        symbol: str,
        window: int = 20
    ) -> Optional[Decimal]:
        """
        Calculate price volatility
        
        Args:
            symbol: Trading symbol
            window: Rolling window size
            
        Returns:
            Volatility as decimal
        """
        try:
            if symbol in self.data:
                df = self.data[symbol]
                returns = np.log(df['close'] / df['close'].shift(1))
                volatility = returns.rolling(window).std()
                return Decimal(str(volatility.iloc[-1]))
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {str(e)}")
        return None
        
    def get_volume_profile(
        self,
        symbol: str,
        bins: int = 10
    ) -> Optional[pd.Series]:
        """
        Calculate volume profile
        
        Args:
            symbol: Trading symbol
            bins: Number of price bins
            
        Returns:
            Volume profile as series
        """
        try:
            if symbol in self.data:
                df = self.data[symbol]
                # Calculate volume-weighted price distribution
                profile = pd.cut(
                    df['close'],
                    bins=bins,
                    labels=False
                ).value_counts().sort_index()
                return profile
        except Exception as e:
            logger.error(f"Error calculating volume profile for {symbol}: {str(e)}")
        return None
        
    def cleanup_old_data(
        self,
        max_periods: int = 10000
    ) -> None:
        """Remove old data beyond max periods"""
        try:
            for symbol in self.data:
                if len(self.data[symbol]) > max_periods:
                    self.data[symbol] = self.data[symbol].iloc[-max_periods:]
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
