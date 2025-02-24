"""
Technical indicators module
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from decimal import Decimal
from loguru import logger

class TechnicalIndicators:
    """Technical analysis indicators"""
    
    @staticmethod
    def calculate_atr(
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range
        
        Args:
            df: OHLCV DataFrame
            period: ATR period
            
        Returns:
            ATR values
        """
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            # Calculate true range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate ATR
            atr = tr.rolling(period).mean()
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return pd.Series()
            
    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Args:
            df: OHLCV DataFrame
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Dict with upper, middle, lower bands
        """
        try:
            # Calculate middle band (SMA)
            middle = df['close'].rolling(period).mean()
            
            # Calculate standard deviation
            std = df['close'].rolling(period).std()
            
            # Calculate upper and lower bands
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return {}
            
    @staticmethod
    def calculate_rsi(
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Relative Strength Index
        
        Args:
            df: OHLCV DataFrame
            period: RSI period
            
        Returns:
            RSI values
        """
        try:
            # Calculate price changes
            delta = df['close'].diff()
            
            # Separate gains and losses
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            
            # Calculate RS and RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series()
            
    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate MACD
        
        Args:
            df: OHLCV DataFrame
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            Dict with MACD line, signal line, histogram
        """
        try:
            # Calculate EMAs
            fast_ema = df['close'].ewm(span=fast_period).mean()
            slow_ema = df['close'].ewm(span=slow_period).mean()
            
            # Calculate MACD line
            macd_line = fast_ema - slow_ema
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return {}
            
    @staticmethod
    def calculate_support_resistance(
        df: pd.DataFrame,
        window: int = 20,
        num_points: int = 3
    ) -> Dict[str, Decimal]:
        """
        Calculate support and resistance levels
        
        Args:
            df: OHLCV DataFrame
            window: Rolling window size
            num_points: Number of points to confirm level
            
        Returns:
            Dict with support and resistance prices
        """
        try:
            # Find local maxima and minima
            highs = df['high'].rolling(window, center=True).apply(
                lambda x: x.argmax() == len(x)//2
            )
            lows = df['low'].rolling(window, center=True).apply(
                lambda x: x.argmin() == len(x)//2
            )
            
            # Get recent levels
            resistance = df.loc[highs]['high'].iloc[-num_points:].mean()
            support = df.loc[lows]['low'].iloc[-num_points:].mean()
            
            return {
                'support': Decimal(str(support)),
                'resistance': Decimal(str(resistance))
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {str(e)}")
            return {}
