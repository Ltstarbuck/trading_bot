"""
Trend indicators
"""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from loguru import logger

from .base_indicator import BaseIndicator

class ADX(BaseIndicator):
    """Average Directional Index"""
    
    def __init__(self):
        """Initialize ADX indicator"""
        super().__init__("ADX")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """
        Calculate ADX
        
        Args:
            data: OHLCV DataFrame
            period: ADX period
            
        Returns:
            DataFrame with ADX values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data, ['high', 'low', 'close']
            ):
                return data
                
            # Calculate True Range
            tr = self._true_range(data)
            
            # Calculate Directional Movement
            pos_dm = self._positive_dm(data)
            neg_dm = self._negative_dm(data)
            
            # Calculate Smoothed Values
            smoothed_tr = self._smoothed_average(tr, period)
            smoothed_pos_dm = self._smoothed_average(pos_dm, period)
            smoothed_neg_dm = self._smoothed_average(neg_dm, period)
            
            # Calculate Directional Indicators
            pdi = 100 * smoothed_pos_dm / smoothed_tr
            ndi = 100 * smoothed_neg_dm / smoothed_tr
            
            # Calculate ADX
            dx = 100 * abs(pdi - ndi) / (pdi + ndi)
            adx = dx.rolling(window=period).mean()
            
            # Prepare output
            indicator_data = pd.DataFrame({
                'adx': adx,
                'pdi': pdi,
                'ndi': ndi
            }, index=data.index)
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating ADX: {str(e)}")
            return data
            
    def _true_range(self, data: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        ranges = pd.concat(
            [high_low, high_close, low_close],
            axis=1
        )
        return ranges.max(axis=1)
        
    def _positive_dm(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Positive Directional Movement"""
        up_move = data['high'] - data['high'].shift()
        down_move = data['low'].shift() - data['low']
        return pd.Series(
            [
                up if up > down and up > 0 else 0
                for up, down in zip(up_move, down_move)
            ],
            index=data.index
        )
        
    def _negative_dm(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Negative Directional Movement"""
        up_move = data['high'] - data['high'].shift()
        down_move = data['low'].shift() - data['low']
        return pd.Series(
            [
                down if down > up and down > 0 else 0
                for up, down in zip(up_move, down_move)
            ],
            index=data.index
        )
        
    def _smoothed_average(
        self,
        data: pd.Series,
        period: int
    ) -> pd.Series:
        """Calculate Smoothed Average"""
        alpha = 1 / period
        return data.ewm(
            alpha=alpha,
            adjust=False
        ).mean()

class Aroon(BaseIndicator):
    """Aroon Indicator"""
    
    def __init__(self):
        """Initialize Aroon indicator"""
        super().__init__("Aroon")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 25
    ) -> pd.DataFrame:
        """
        Calculate Aroon indicator
        
        Args:
            data: OHLCV DataFrame
            period: Aroon period
            
        Returns:
            DataFrame with Aroon values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data, ['high', 'low']
            ):
                return data
                
            # Calculate Aroon Up
            rolling_high = data['high'].rolling(period)
            days_since_high = period - rolling_high.apply(
                lambda x: x.argmax()
            )
            aroon_up = 100 * (period - days_since_high) / period
            
            # Calculate Aroon Down
            rolling_low = data['low'].rolling(period)
            days_since_low = period - rolling_low.apply(
                lambda x: x.argmin()
            )
            aroon_down = 100 * (period - days_since_low) / period
            
            # Calculate Aroon Oscillator
            oscillator = aroon_up - aroon_down
            
            # Prepare output
            indicator_data = pd.DataFrame({
                'up': aroon_up,
                'down': aroon_down,
                'oscillator': oscillator
            }, index=data.index)
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating Aroon: {str(e)}")
            return data

class SuperTrend(BaseIndicator):
    """SuperTrend Indicator"""
    
    def __init__(self):
        """Initialize SuperTrend indicator"""
        super().__init__("SuperTrend")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0
    ) -> pd.DataFrame:
        """
        Calculate SuperTrend
        
        Args:
            data: OHLCV DataFrame
            period: ATR period
            multiplier: ATR multiplier
            
        Returns:
            DataFrame with SuperTrend values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data, ['high', 'low', 'close']
            ):
                return data
                
            # Calculate ATR
            tr = self._true_range(data)
            atr = tr.rolling(window=period).mean()
            
            # Calculate basic upper and lower bands
            hl2 = (data['high'] + data['low']) / 2
            basic_upper = hl2 + (multiplier * atr)
            basic_lower = hl2 - (multiplier * atr)
            
            # Initialize final upper and lower bands
            final_upper = pd.Series(index=data.index)
            final_lower = pd.Series(index=data.index)
            
            # Initialize SuperTrend
            supertrend = pd.Series(index=data.index)
            
            # Calculate SuperTrend
            for i in range(period, len(data)):
                if i > period:
                    # Calculate final upper band
                    if (
                        basic_upper[i] < final_upper[i-1] or
                        data['close'][i-1] > final_upper[i-1]
                    ):
                        final_upper[i] = basic_upper[i]
                    else:
                        final_upper[i] = final_upper[i-1]
                        
                    # Calculate final lower band
                    if (
                        basic_lower[i] > final_lower[i-1] or
                        data['close'][i-1] < final_lower[i-1]
                    ):
                        final_lower[i] = basic_lower[i]
                    else:
                        final_lower[i] = final_lower[i-1]
                else:
                    final_upper[i] = basic_upper[i]
                    final_lower[i] = basic_lower[i]
                    
                # Determine trend
                if (
                    data['close'][i] > final_upper[i-1]
                    if i > period else
                    data['close'][i] > final_upper[i]
                ):
                    supertrend[i] = final_lower[i]
                else:
                    supertrend[i] = final_upper[i]
                    
            # Prepare output
            indicator_data = pd.DataFrame({
                'value': supertrend,
                'upper': final_upper,
                'lower': final_lower
            }, index=data.index)
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating SuperTrend: {str(e)}")
            return data
            
    def _true_range(self, data: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        ranges = pd.concat(
            [high_low, high_close, low_close],
            axis=1
        )
        return ranges.max(axis=1)

class ParabolicSAR(BaseIndicator):
    """Parabolic Stop and Reverse"""
    
    def __init__(self):
        """Initialize PSAR indicator"""
        super().__init__("PSAR")
        
    def calculate(
        self,
        data: pd.DataFrame,
        acceleration: float = 0.02,
        max_acceleration: float = 0.2
    ) -> pd.DataFrame:
        """
        Calculate Parabolic SAR
        
        Args:
            data: OHLCV DataFrame
            acceleration: Initial acceleration factor
            max_acceleration: Maximum acceleration factor
            
        Returns:
            DataFrame with PSAR values
        """
        try:
            # Validate input data
            if not self.validate_data(
                data, ['high', 'low']
            ):
                return data
                
            # Initialize variables
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            psar = close[0]
            af = acceleration
            bull = True
            ep = high[0]
            
            # Arrays to store results
            psar_values = np.zeros(len(close))
            psar_values[0] = psar
            
            # Calculate PSAR
            for i in range(1, len(close)):
                if bull:
                    psar = psar + af * (ep - psar)
                    psar = min(psar, low[i-1], low[i-2] if i > 1 else low[i-1])
                    
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + acceleration, max_acceleration)
                        
                    if low[i] < psar:
                        bull = False
                        psar = ep
                        ep = low[i]
                        af = acceleration
                else:
                    psar = psar - af * (psar - ep)
                    psar = max(psar, high[i-1], high[i-2] if i > 1 else high[i-1])
                    
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + acceleration, max_acceleration)
                        
                    if high[i] > psar:
                        bull = True
                        psar = ep
                        ep = high[i]
                        af = acceleration
                        
                psar_values[i] = psar
                
            # Prepare output
            indicator_data = pd.DataFrame({
                'value': psar_values
            }, index=data.index)
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating PSAR: {str(e)}")
            return data
