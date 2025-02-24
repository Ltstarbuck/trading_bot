"""
Advanced Relative Strength Index (RSI) implementations
"""

from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger

from .base_indicator import BaseIndicator

class RSIAdvanced(BaseIndicator):
    """Advanced Relative Strength Index implementation"""
    
    def __init__(self):
        """Initialize RSI indicator"""
        super().__init__("RSI")
        
    def calculate(
        self,
        data: pd.DataFrame,
        period: int = 14,
        column: str = 'close',
        ma_type: str = 'ema',
        stochastic: bool = False,
        stoch_period: int = 14,
        divergence: bool = False
    ) -> pd.DataFrame:
        """
        Calculate RSI with advanced features
        
        Args:
            data: OHLCV DataFrame
            period: RSI period
            column: Column to calculate RSI for
            ma_type: Moving average type ('sma' or 'ema')
            stochastic: Whether to calculate Stochastic RSI
            stoch_period: Stochastic RSI period
            divergence: Whether to calculate RSI divergence
            
        Returns:
            DataFrame with RSI values and additional metrics
        """
        try:
            # Validate input data
            if not self.validate_data(data, [column]):
                return data
                
            # Calculate basic RSI
            rsi = self._calculate_rsi(
                data[column],
                period,
                ma_type
            )
            
            # Initialize results dictionary
            results = {'rsi': rsi}
            
            # Calculate Stochastic RSI if requested
            if stochastic:
                stoch_rsi = self._calculate_stoch_rsi(
                    rsi,
                    stoch_period
                )
                results.update(stoch_rsi)
                
            # Calculate RSI divergence if requested
            if divergence:
                div_signals = self._calculate_divergence(
                    data[column],
                    rsi
                )
                results.update(div_signals)
                
            # Add additional analysis
            results.update(
                self._calculate_additional_metrics(rsi)
            )
            
            # Prepare output
            indicator_data = pd.DataFrame(
                results,
                index=data.index
            )
            
            return self.prepare_output(data, indicator_data)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return data
            
    def _calculate_rsi(
        self,
        prices: pd.Series,
        period: int,
        ma_type: str
    ) -> pd.Series:
        """Calculate basic RSI"""
        try:
            # Calculate price changes
            delta = prices.diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses
            if ma_type.lower() == 'sma':
                avg_gains = gains.rolling(window=period).mean()
                avg_losses = losses.rolling(window=period).mean()
            else:  # EMA
                avg_gains = gains.ewm(
                    span=period,
                    adjust=False
                ).mean()
                avg_losses = losses.ewm(
                    span=period,
                    adjust=False
                ).mean()
                
            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(
                f"Error calculating basic RSI: {str(e)}"
            )
            return pd.Series(index=prices.index)
            
    def _calculate_stoch_rsi(
        self,
        rsi: pd.Series,
        period: int
    ) -> Dict[str, pd.Series]:
        """Calculate Stochastic RSI"""
        try:
            # Calculate Stochastic RSI
            rsi_min = rsi.rolling(window=period).min()
            rsi_max = rsi.rolling(window=period).max()
            stoch_rsi = (
                (rsi - rsi_min) /
                (rsi_max - rsi_min)
            ) * 100
            
            # Calculate K and D lines
            k = stoch_rsi.rolling(window=3).mean()
            d = k.rolling(window=3).mean()
            
            return {
                'stoch_rsi': stoch_rsi,
                'stoch_k': k,
                'stoch_d': d
            }
            
        except Exception as e:
            logger.error(
                f"Error calculating Stochastic RSI: {str(e)}"
            )
            return {
                'stoch_rsi': pd.Series(index=rsi.index),
                'stoch_k': pd.Series(index=rsi.index),
                'stoch_d': pd.Series(index=rsi.index)
            }
            
    def _calculate_divergence(
        self,
        prices: pd.Series,
        rsi: pd.Series,
        window: int = 20
    ) -> Dict[str, pd.Series]:
        """Calculate RSI divergence"""
        try:
            # Initialize divergence signals
            bullish_div = pd.Series(0, index=prices.index)
            bearish_div = pd.Series(0, index=prices.index)
            
            # Calculate local extrema
            for i in range(window, len(prices)):
                price_window = prices[i-window:i+1]
                rsi_window = rsi[i-window:i+1]
                
                # Find local minima and maxima
                price_min = price_window.min()
                price_max = price_window.max()
                rsi_min = rsi_window.min()
                rsi_max = rsi_window.max()
                
                # Check for bullish divergence
                if (
                    prices[i] <= price_min and
                    rsi[i] > rsi_min
                ):
                    bullish_div[i] = 1
                    
                # Check for bearish divergence
                if (
                    prices[i] >= price_max and
                    rsi[i] < rsi_max
                ):
                    bearish_div[i] = 1
                    
            return {
                'bullish_divergence': bullish_div,
                'bearish_divergence': bearish_div
            }
            
        except Exception as e:
            logger.error(
                f"Error calculating RSI divergence: {str(e)}"
            )
            return {
                'bullish_divergence': pd.Series(
                    index=prices.index
                ),
                'bearish_divergence': pd.Series(
                    index=prices.index
                )
            }
            
    def _calculate_additional_metrics(
        self,
        rsi: pd.Series
    ) -> Dict[str, pd.Series]:
        """Calculate additional RSI metrics"""
        try:
            # Initialize metrics
            metrics = {}
            
            # Overbought/Oversold conditions
            metrics['overbought'] = (rsi > 70).astype(int)
            metrics['oversold'] = (rsi < 30).astype(int)
            
            # RSI momentum
            metrics['momentum'] = rsi.diff()
            
            # RSI trend
            metrics['trend'] = pd.Series(
                index=rsi.index,
                data=np.where(
                    rsi > rsi.rolling(window=14).mean(),
                    1,  # Uptrend
                    -1  # Downtrend
                )
            )
            
            # RSI volatility
            metrics['volatility'] = rsi.rolling(
                window=14
            ).std()
            
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error calculating additional metrics: {str(e)}"
            )
            return {}
            
    def get_signals(
        self,
        data: pd.DataFrame,
        rsi_period: int = 14,
        stoch_period: int = 14,
        oversold_threshold: float = 30,
        overbought_threshold: float = 70
    ) -> Dict[str, pd.Series]:
        """
        Generate trading signals based on RSI
        
        Args:
            data: OHLCV DataFrame
            rsi_period: RSI period
            stoch_period: Stochastic RSI period
            oversold_threshold: Oversold threshold
            overbought_threshold: Overbought threshold
            
        Returns:
            Dictionary of trading signals
        """
        try:
            # Calculate RSI with all features
            results = self.calculate(
                data,
                period=rsi_period,
                stochastic=True,
                stoch_period=stoch_period,
                divergence=True
            )
            
            # Extract RSI values
            rsi = results[f'{self.name}_rsi']
            stoch_rsi = results[f'{self.name}_stoch_rsi']
            bull_div = results[f'{self.name}_bullish_divergence']
            bear_div = results[f'{self.name}_bearish_divergence']
            
            # Generate signals
            signals = {
                'buy': pd.Series(0, index=data.index),
                'sell': pd.Series(0, index=data.index),
                'strength': pd.Series(0, index=data.index)
            }
            
            # Basic RSI signals
            signals['buy'] = (
                (rsi < oversold_threshold) |
                (bull_div == 1)
            ).astype(int)
            
            signals['sell'] = (
                (rsi > overbought_threshold) |
                (bear_div == 1)
            ).astype(int)
            
            # Signal strength (0-100)
            signals['strength'] = (
                (100 - rsi) * signals['buy'] +
                rsi * signals['sell']
            )
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return {
                'buy': pd.Series(index=data.index),
                'sell': pd.Series(index=data.index),
                'strength': pd.Series(index=data.index)
            }
