"""
Technical oscillator indicators
"""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from loguru import logger

from .base_indicator import BaseIndicator

class RSI(BaseIndicator):
    """Relative Strength Index"""
    
    def __init__(self):
        """Initialize RSI indicator"""
        super().__init__("RSI")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 14,
        column: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate Relative Strength Index
        
        Args:
            data: OHLCV DataFrame
            period: RSI period
            column: Column to calculate RSI for
            
        Returns:
            DataFrame with RSI values
        """
        try:
            # Validate input data
            if not self.validate_data(data, [column]):
                return data
                
            # Calculate price changes
            delta = data[column].diff()
            
            # Separate gains and losses
            gain = (delta.where(delta > 0, 0)).rolling(
                window=period
            ).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(
                window=period
            ).mean()
            
            # Calculate RS and RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Prepare output
            indicator_data = pd.DataFrame(
                {'value': rsi},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return data

class Stochastic(BaseIndicator):
    """Stochastic Oscillator"""
    
    def __init__(self):
        """Initialize Stochastic indicator"""
        super().__init__("Stochastic")
        
    def calculate(
        self,
        data: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3
    ) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator
        
        Args:
            data: OHLCV DataFrame
            k_period: %K period
            d_period: %D period
            smooth_k: %K smoothing period
            
        Returns:
            DataFrame with Stochastic values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data, ['high', 'low', 'close']
            ):
                return data
                
            # Calculate %K
            low_min = data['low'].rolling(
                window=k_period
            ).min()
            high_max = data['high'].rolling(
                window=k_period
            ).max()
            
            k = 100 * (
                (data['close'] - low_min) /
                (high_max - low_min)
            )
            
            # Smooth %K if specified
            if smooth_k > 1:
                k = k.rolling(window=smooth_k).mean()
                
            # Calculate %D
            d = k.rolling(window=d_period).mean()
            
            # Prepare output
            indicator_data = pd.DataFrame({
                'k': k,
                'd': d
            }, index=data.index)
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {str(e)}")
            return data

class MACD(BaseIndicator):
    """Moving Average Convergence Divergence"""
    
    def __init__(self):
        """Initialize MACD indicator"""
        super().__init__("MACD")
        
    def calculate(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate MACD
        
        Args:
            data: OHLCV DataFrame
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            column: Column to calculate MACD for
            
        Returns:
            DataFrame with MACD values
        """
        try:
            # Validate input data
            if not self.validate_data(data, [column]):
                return data
                
            # Calculate EMAs
            fast_ema = data[column].ewm(
                span=fast_period,
                adjust=False
            ).mean()
            slow_ema = data[column].ewm(
                span=slow_period,
                adjust=False
            ).mean()
            
            # Calculate MACD line
            macd_line = fast_ema - slow_ema
            
            # Calculate signal line
            signal_line = macd_line.ewm(
                span=signal_period,
                adjust=False
            ).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            # Prepare output
            indicator_data = pd.DataFrame({
                'line': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }, index=data.index)
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return data

class CCI(BaseIndicator):
    """Commodity Channel Index"""
    
    def __init__(self):
        """Initialize CCI indicator"""
        super().__init__("CCI")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 20,
        constant: float = 0.015
    ) -> pd.DataFrame:
        """
        Calculate CCI
        
        Args:
            data: OHLCV DataFrame
            period: CCI period
            constant: CCI constant
            
        Returns:
            DataFrame with CCI values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data, ['high', 'low', 'close']
            ):
                return data
                
            # Calculate typical price
            tp = (
                data['high'] +
                data['low'] +
                data['close']
            ) / 3
            
            # Calculate SMA of typical price
            tp_sma = tp.rolling(window=period).mean()
            
            # Calculate mean deviation
            mean_dev = pd.Series(
                [
                    abs(tp[i - period + 1:i + 1] - tp_sma[i]).mean()
                    for i in range(period - 1, len(tp))
                ],
                index=tp.index[period - 1:]
            )
            
            # Calculate CCI
            cci = (tp - tp_sma) / (constant * mean_dev)
            
            # Prepare output
            indicator_data = pd.DataFrame(
                {'value': cci},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating CCI: {str(e)}")
            return data

class MFI(BaseIndicator):
    """Money Flow Index"""
    
    def __init__(self):
        """Initialize MFI indicator"""
        super().__init__("MFI")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """
        Calculate MFI
        
        Args:
            data: OHLCV DataFrame
            period: MFI period
            
        Returns:
            DataFrame with MFI values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data,
                ['high', 'low', 'close', 'volume']
            ):
                return data
                
            # Calculate typical price
            tp = (
                data['high'] +
                data['low'] +
                data['close']
            ) / 3
            
            # Calculate money flow
            money_flow = tp * data['volume']
            
            # Get positive and negative money flow
            diff = tp.diff()
            pos_flow = pd.Series(
                [
                    flow if diff[i] > 0 else 0
                    for i, flow in enumerate(money_flow)
                ],
                index=money_flow.index
            )
            neg_flow = pd.Series(
                [
                    flow if diff[i] < 0 else 0
                    for i, flow in enumerate(money_flow)
                ],
                index=money_flow.index
            )
            
            # Calculate money ratio
            pos_sum = pos_flow.rolling(window=period).sum()
            neg_sum = neg_flow.rolling(window=period).sum()
            money_ratio = pos_sum / neg_sum
            
            # Calculate MFI
            mfi = 100 - (100 / (1 + money_ratio))
            
            # Prepare output
            indicator_data = pd.DataFrame(
                {'value': mfi},
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating MFI: {str(e)}")
            return data
