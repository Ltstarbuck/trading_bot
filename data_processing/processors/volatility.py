"""
Volatility processor for market data analysis
"""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

class VolatilityProcessor:
    """Processes and analyzes market volatility"""
    
    def __init__(
        self,
        windows: List[int] = [14, 30, 60],
        alpha: float = 0.94,  # EWMA decay factor
        cache_size: int = 1000
    ):
        """
        Initialize volatility processor
        
        Args:
            windows: List of lookback periods for calculations
            alpha: EWMA decay factor for realized volatility
            cache_size: Maximum data points to cache
        """
        self.windows = windows
        self.alpha = alpha
        self.cache_size = cache_size
        self._cache: Dict[str, pd.DataFrame] = {}
        
    def process_volatility(
        self,
        symbol: str,
        data: pd.DataFrame
    ) -> Dict:
        """
        Process volatility metrics
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame with columns [open, high, low, close, volume]
            
        Returns:
            Dictionary of volatility metrics
        """
        try:
            # Initialize cache for symbol
            if symbol not in self._cache:
                self._cache[symbol] = pd.DataFrame()
                
            # Update cache
            cached = self._cache[symbol]
            updated = pd.concat([cached, data])
            
            # Remove duplicates and sort
            updated = updated[~updated.index.duplicated(keep='last')]
            updated.sort_index(inplace=True)
            
            # Maintain cache size
            if len(updated) > self.cache_size:
                updated = updated.iloc[-self.cache_size:]
                
            self._cache[symbol] = updated
            
            # Calculate volatility metrics
            metrics = {
                'historical': self._calculate_historical_volatility(updated),
                'realized': self._calculate_realized_volatility(updated),
                'parkinson': self._calculate_parkinson_volatility(updated),
                'garman_klass': self._calculate_garman_klass_volatility(updated),
                'yang_zhang': self._calculate_yang_zhang_volatility(updated),
                'indicators': self._calculate_volatility_indicators(updated)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error processing volatility: {str(e)}")
            raise
            
    def _calculate_historical_volatility(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """Calculate historical volatility for different windows"""
        try:
            # Calculate log returns
            log_returns = np.log(data['close'] / data['close'].shift(1))
            
            metrics = {}
            for window in self.windows:
                # Annualized volatility
                vol = np.sqrt(252) * log_returns.rolling(
                    window=window
                ).std()
                
                metrics[f'{window}d'] = {
                    'current': float(vol.iloc[-1]),
                    'mean': float(vol.mean()),
                    'max': float(vol.max()),
                    'min': float(vol.min())
                }
                
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error calculating historical volatility: {str(e)}"
            )
            return {
                f'{w}d': {
                    'current': 0, 'mean': 0,
                    'max': 0, 'min': 0
                }
                for w in self.windows
            }
            
    def _calculate_realized_volatility(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """Calculate realized volatility using EWMA"""
        try:
            # Calculate squared returns
            returns = data['close'].pct_change()
            squared_returns = returns ** 2
            
            # EWMA volatility
            ewma_var = squared_returns.ewm(
                alpha=self.alpha,
                adjust=False
            ).mean()
            ewma_vol = np.sqrt(252 * ewma_var)
            
            metrics = {
                'current': float(ewma_vol.iloc[-1]),
                'mean': float(ewma_vol.mean()),
                'max': float(ewma_vol.max()),
                'min': float(ewma_vol.min())
            }
            
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error calculating realized volatility: {str(e)}"
            )
            return {
                'current': 0,
                'mean': 0,
                'max': 0,
                'min': 0
            }
            
    def _calculate_parkinson_volatility(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """Calculate Parkinson volatility using high-low range"""
        try:
            # Parkinson estimator
            hl_range = np.log(data['high'] / data['low'])
            factor = 1 / (4 * np.log(2))
            
            metrics = {}
            for window in self.windows:
                vol = np.sqrt(
                    252 * factor * 
                    hl_range.pow(2).rolling(window).mean()
                )
                
                metrics[f'{window}d'] = {
                    'current': float(vol.iloc[-1]),
                    'mean': float(vol.mean()),
                    'max': float(vol.max()),
                    'min': float(vol.min())
                }
                
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error calculating Parkinson volatility: {str(e)}"
            )
            return {
                f'{w}d': {
                    'current': 0, 'mean': 0,
                    'max': 0, 'min': 0
                }
                for w in self.windows
            }
            
    def _calculate_garman_klass_volatility(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """Calculate Garman-Klass volatility"""
        try:
            # Garman-Klass estimator
            log_hl = np.log(data['high'] / data['low']).pow(2)
            log_co = np.log(data['close'] / data['open']).pow(2)
            
            estimator = (
                0.5 * log_hl -
                (2 * np.log(2) - 1) * log_co
            )
            
            metrics = {}
            for window in self.windows:
                vol = np.sqrt(252 * estimator.rolling(window).mean())
                
                metrics[f'{window}d'] = {
                    'current': float(vol.iloc[-1]),
                    'mean': float(vol.mean()),
                    'max': float(vol.max()),
                    'min': float(vol.min())
                }
                
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error calculating Garman-Klass volatility: {str(e)}"
            )
            return {
                f'{w}d': {
                    'current': 0, 'mean': 0,
                    'max': 0, 'min': 0
                }
                for w in self.windows
            }
            
    def _calculate_yang_zhang_volatility(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """Calculate Yang-Zhang volatility"""
        try:
            # Yang-Zhang components
            overnight_vol = np.log(
                data['open'] / data['close'].shift(1)
            ).pow(2)
            open_close_vol = np.log(
                data['close'] / data['open']
            ).pow(2)
            rogers_satchell = (
                np.log(data['high'] / data['close']) *
                np.log(data['high'] / data['open']) +
                np.log(data['low'] / data['close']) *
                np.log(data['low'] / data['open'])
            )
            
            metrics = {}
            for window in self.windows:
                # Calculate components
                overnight = overnight_vol.rolling(window).mean()
                open_close = open_close_vol.rolling(window).mean()
                rs = rogers_satchell.rolling(window).mean()
                
                # Combine components (k=0.34 as suggested by Yang-Zhang)
                vol = np.sqrt(252 * (
                    overnight + 0.34 * open_close + (1 - 0.34) * rs
                ))
                
                metrics[f'{window}d'] = {
                    'current': float(vol.iloc[-1]),
                    'mean': float(vol.mean()),
                    'max': float(vol.max()),
                    'min': float(vol.min())
                }
                
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error calculating Yang-Zhang volatility: {str(e)}"
            )
            return {
                f'{w}d': {
                    'current': 0, 'mean': 0,
                    'max': 0, 'min': 0
                }
                for w in self.windows
            }
            
    def _calculate_volatility_indicators(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """Calculate additional volatility indicators"""
        try:
            # Calculate returns
            returns = data['close'].pct_change()
            
            # Volatility indicators
            indicators = {
                'volatility_ratio': self._calculate_volatility_ratio(
                    data, returns
                ),
                'volatility_trend': self._calculate_volatility_trend(
                    data, returns
                ),
                'volatility_regime': self._detect_volatility_regime(
                    data, returns
                )
            }
            
            return indicators
            
        except Exception as e:
            logger.error(
                f"Error calculating volatility indicators: {str(e)}"
            )
            return {
                'volatility_ratio': {},
                'volatility_trend': {},
                'volatility_regime': {}
            }
            
    def _calculate_volatility_ratio(
        self,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict:
        """Calculate ratio between different volatility measures"""
        try:
            metrics = {}
            for window in self.windows:
                # Historical vs realized
                hist_vol = returns.rolling(window).std()
                real_vol = np.sqrt(
                    returns.pow(2).ewm(
                        alpha=self.alpha,
                        adjust=False
                    ).mean()
                )
                
                ratio = real_vol / hist_vol
                metrics[f'{window}d'] = {
                    'current': float(ratio.iloc[-1]),
                    'mean': float(ratio.mean())
                }
                
            return metrics
            
        except Exception:
            return {
                f'{w}d': {'current': 0, 'mean': 0}
                for w in self.windows
            }
            
    def _calculate_volatility_trend(
        self,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict:
        """Calculate volatility trend indicators"""
        try:
            metrics = {}
            for window in self.windows:
                # Volatility moving averages
                vol = returns.rolling(window).std()
                vol_sma = vol.rolling(window).mean()
                vol_ratio = vol / vol_sma
                
                metrics[f'{window}d'] = {
                    'current_ratio': float(vol_ratio.iloc[-1]),
                    'trend': 'increasing'
                    if vol_ratio.iloc[-1] > 1
                    else 'decreasing'
                }
                
            return metrics
            
        except Exception:
            return {
                f'{w}d': {
                    'current_ratio': 0,
                    'trend': 'unknown'
                }
                for w in self.windows
            }
            
    def _detect_volatility_regime(
        self,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict:
        """Detect current volatility regime"""
        try:
            metrics = {}
            for window in self.windows:
                vol = returns.rolling(window).std()
                vol_mean = vol.mean()
                vol_std = vol.std()
                
                current_vol = vol.iloc[-1]
                z_score = (current_vol - vol_mean) / vol_std
                
                # Classify regime
                if z_score > 2:
                    regime = 'extreme'
                elif z_score > 1:
                    regime = 'high'
                elif z_score < -2:
                    regime = 'very_low'
                elif z_score < -1:
                    regime = 'low'
                else:
                    regime = 'normal'
                    
                metrics[f'{window}d'] = {
                    'regime': regime,
                    'z_score': float(z_score)
                }
                
            return metrics
            
        except Exception:
            return {
                f'{w}d': {
                    'regime': 'unknown',
                    'z_score': 0
                }
                for w in self.windows
            }
            
    def get_cached_data(
        self,
        symbol: str,
        start_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get cached data for symbol
        
        Args:
            symbol: Trading pair symbol
            start_time: Optional start time filter
            
        Returns:
            Cached DataFrame
        """
        if symbol not in self._cache:
            return pd.DataFrame()
            
        data = self._cache[symbol]
        
        if start_time:
            data = data[data.index >= start_time]
            
        return data
        
    def clear_cache(
        self,
        symbol: Optional[str] = None
    ) -> None:
        """
        Clear cached data
        
        Args:
            symbol: Optional symbol to clear
        """
        if symbol:
            self._cache.pop(symbol, None)
        else:
            self._cache.clear()
