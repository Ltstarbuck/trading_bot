"""
Market analysis module
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from decimal import Decimal
from loguru import logger

class MarketAnalysis:
    """Market analysis and pattern detection"""
    
    @staticmethod
    def detect_trend(
        prices: pd.Series,
        window: int = 20
    ) -> str:
        """
        Detect price trend
        
        Args:
            prices: Price series
            window: Analysis window
            
        Returns:
            Trend direction ('up', 'down', or 'sideways')
        """
        try:
            # Calculate moving average
            ma = prices.rolling(window).mean()
            
            # Calculate price slope
            slope = (ma - ma.shift(window)) / window
            
            # Determine trend
            if slope.iloc[-1] > 0.001:  # Uptrend
                return 'up'
            elif slope.iloc[-1] < -0.001:  # Downtrend
                return 'down'
            else:  # Sideways
                return 'sideways'
                
        except Exception as e:
            logger.error(f"Error detecting trend: {str(e)}")
            return 'sideways'
            
    @staticmethod
    def detect_breakout(
        df: pd.DataFrame,
        window: int = 20,
        std_dev: float = 2.0
    ) -> Optional[str]:
        """
        Detect price breakouts
        
        Args:
            df: OHLCV DataFrame
            window: Analysis window
            std_dev: Standard deviation threshold
            
        Returns:
            Breakout direction ('up', 'down', or None)
        """
        try:
            # Calculate mean and standard deviation
            mean = df['close'].rolling(window).mean()
            std = df['close'].rolling(window).std()
            
            # Calculate upper and lower bands
            upper = mean + (std * std_dev)
            lower = mean - (std * std_dev)
            
            # Check for breakouts
            current_price = df['close'].iloc[-1]
            if current_price > upper.iloc[-1]:
                return 'up'
            elif current_price < lower.iloc[-1]:
                return 'down'
            return None
            
        except Exception as e:
            logger.error(f"Error detecting breakout: {str(e)}")
            return None
            
    @staticmethod
    def calculate_momentum(
        prices: pd.Series,
        period: int = 14
    ) -> Optional[float]:
        """
        Calculate price momentum
        
        Args:
            prices: Price series
            period: Momentum period
            
        Returns:
            Momentum value
        """
        try:
            # Calculate momentum
            momentum = prices / prices.shift(period) - 1
            return momentum.iloc[-1]
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {str(e)}")
            return None
            
    @staticmethod
    def detect_divergence(
        prices: pd.Series,
        indicator: pd.Series,
        window: int = 20
    ) -> Optional[str]:
        """
        Detect price-indicator divergence
        
        Args:
            prices: Price series
            indicator: Indicator series
            window: Analysis window
            
        Returns:
            Divergence type ('bullish', 'bearish', or None)
        """
        try:
            # Get price and indicator slopes
            price_slope = (
                prices.iloc[-1] - prices.iloc[-window]
            ) / window
            ind_slope = (
                indicator.iloc[-1] - indicator.iloc[-window]
            ) / window
            
            # Check for divergence
            if price_slope > 0 and ind_slope < 0:
                return 'bearish'
            elif price_slope < 0 and ind_slope > 0:
                return 'bullish'
            return None
            
        except Exception as e:
            logger.error(f"Error detecting divergence: {str(e)}")
            return None
            
    @staticmethod
    def calculate_correlation(
        symbol1_prices: pd.Series,
        symbol2_prices: pd.Series,
        window: int = 30
    ) -> Optional[float]:
        """
        Calculate price correlation between symbols
        
        Args:
            symbol1_prices: First symbol prices
            symbol2_prices: Second symbol prices
            window: Correlation window
            
        Returns:
            Correlation coefficient
        """
        try:
            # Calculate rolling correlation
            correlation = symbol1_prices.rolling(window).corr(symbol2_prices)
            return correlation.iloc[-1]
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {str(e)}")
            return None
            
    @staticmethod
    def analyze_volume_trend(
        df: pd.DataFrame,
        window: int = 20
    ) -> Dict[str, float]:
        """
        Analyze volume trends
        
        Args:
            df: OHLCV DataFrame
            window: Analysis window
            
        Returns:
            Dict with volume metrics
        """
        try:
            # Calculate volume metrics
            avg_volume = df['volume'].rolling(window).mean().iloc[-1]
            vol_change = (
                df['volume'].iloc[-1] / avg_volume - 1
            ) * 100
            
            # Calculate price-volume correlation
            price_changes = df['close'].pct_change()
            volume_changes = df['volume'].pct_change()
            correlation = price_changes.corr(volume_changes)
            
            return {
                'average_volume': avg_volume,
                'volume_change': vol_change,
                'price_volume_correlation': correlation
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume: {str(e)}")
            return {}
