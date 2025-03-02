"""
Moving average indicators
"""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from loguru import logger

from .base_indicator import BaseIndicator

class SMA(BaseIndicator):
    """Simple Moving Average"""
    
    def __init__(self):
        """Initialize SMA indicator"""
        super().__init__("SMA")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 20,
        column: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate Simple Moving Average
        
        Args:
            data: OHLCV DataFrame
            period: Moving average period
            column: Column to calculate SMA for
            
        Returns:
            DataFrame with SMA values
        """
        try:
            # Validate input data
            if not self.validate_data(data, [column]):
                return data
                
            # Calculate SMA
            sma = data[column].rolling(
                window=period,
                min_periods=1
            ).mean()
            
            # Prepare output
            indicator_data = pd.DataFrame(
                {str(period): sma},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating SMA: {str(e)}")
            return data

class EMA(BaseIndicator):
    """Exponential Moving Average"""
    
    def __init__(self):
        """Initialize EMA indicator"""
        super().__init__("EMA")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 20,
        column: str = 'close',
        alpha: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Calculate Exponential Moving Average
        
        Args:
            data: OHLCV DataFrame
            period: Moving average period
            column: Column to calculate EMA for
            alpha: Optional smoothing factor
            
        Returns:
            DataFrame with EMA values
        """
        try:
            # Validate input data
            if not self.validate_data(data, [column]):
                return data
                
            # Calculate EMA
            if alpha is None:
                alpha = 2 / (period + 1)
                
            ema = data[column].ewm(
                alpha=alpha,
                min_periods=1,
                adjust=False
            ).mean()
            
            # Prepare output
            indicator_data = pd.DataFrame(
                {str(period): ema},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating EMA: {str(e)}")
            return data

class WMA(BaseIndicator):
    """Weighted Moving Average"""
    
    def __init__(self):
        """Initialize WMA indicator"""
        super().__init__("WMA")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 20,
        column: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate Weighted Moving Average
        
        Args:
            data: OHLCV DataFrame
            period: Moving average period
            column: Column to calculate WMA for
            
        Returns:
            DataFrame with WMA values
        """
        try:
            # Validate input data
            if not self.validate_data(data, [column]):
                return data
                
            # Calculate weights
            weights = np.arange(1, period + 1)
            weights = weights / weights.sum()
            
            # Calculate WMA
            values = data[column].values
            wma = []
            
            for i in range(len(values)):
                if i < period - 1:
                    wma.append(np.nan)
                else:
                    window = values[i - period + 1:i + 1]
                    wma.append(np.sum(window * weights))
                    
            # Prepare output
            indicator_data = pd.DataFrame(
                {str(period): wma},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating WMA: {str(e)}")
            return data

class VWMA(BaseIndicator):
    """Volume Weighted Moving Average"""
    
    def __init__(self):
        """Initialize VWMA indicator"""
        super().__init__("VWMA")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 20,
        price_column: str = 'close',
        volume_column: str = 'volume'
    ) -> pd.DataFrame:
        """
        Calculate Volume Weighted Moving Average
        
        Args:
            data: OHLCV DataFrame
            period: Moving average period
            price_column: Price column name
            volume_column: Volume column name
            
        Returns:
            DataFrame with VWMA values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data, [price_column, volume_column]
            ):
                return data
                
            # Calculate VWMA
            pv = data[price_column] * data[volume_column]
            vwma = (
                pv.rolling(window=period).sum() /
                data[volume_column].rolling(window=period).sum()
            )
            
            # Prepare output
            indicator_data = pd.DataFrame(
                {str(period): vwma},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating VWMA: {str(e)}")
            return data

class HMA(BaseIndicator):
    """Hull Moving Average"""
    
    def __init__(self):
        """Initialize HMA indicator"""
        super().__init__("HMA")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 20,
        column: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate Hull Moving Average
        
        Args:
            data: OHLCV DataFrame
            period: Moving average period
            column: Column to calculate HMA for
            
        Returns:
            DataFrame with HMA values
        """
        try:
            # Validate input data
            if not self.validate_data(data, [column]):
                return data
                
            # Calculate WMAs
            half_period = period // 2
            sqrt_period = int(np.sqrt(period))
            
            wma1 = self._weighted_ma(
                data[column],
                half_period
            )
            wma2 = self._weighted_ma(
                data[column],
                period
            )
            
            # Calculate HMA
            hma = self._weighted_ma(
                2 * wma1 - wma2,
                sqrt_period
            )
            
            # Prepare output
            indicator_data = pd.DataFrame(
                {str(period): hma},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating HMA: {str(e)}")
            return data
            
    def _weighted_ma(
        self,
        data: pd.Series,
        period: int
    ) -> pd.Series:
        """Calculate weighted moving average"""
        weights = np.arange(1, period + 1)
        wma = data.rolling(period).apply(
            lambda x: np.sum(weights * x) / weights.sum(),
            raw=True
        )
        return wma
