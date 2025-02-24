"""
Risk metrics processor for market data analysis
"""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from loguru import logger

class RiskMetricsProcessor:
    """Processes and analyzes market risk metrics"""
    
    def __init__(
        self,
        windows: List[int] = [14, 30, 60],
        confidence_level: float = 0.95,
        cache_size: int = 1000
    ):
        """
        Initialize risk metrics processor
        
        Args:
            windows: List of lookback periods for calculations
            confidence_level: Confidence level for VaR/CVaR
            cache_size: Maximum data points to cache
        """
        self.windows = windows
        self.confidence_level = confidence_level
        self.cache_size = cache_size
        self._cache: Dict[str, pd.DataFrame] = {}
        
    def process_risk_metrics(
        self,
        symbol: str,
        data: pd.DataFrame,
        position_size: Optional[float] = None
    ) -> Dict:
        """
        Process risk metrics
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame
            position_size: Optional position size for calculating monetary risk
            
        Returns:
            Dictionary of risk metrics
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
            
            # Calculate returns
            returns = updated['close'].pct_change().dropna()
            
            # Calculate risk metrics
            metrics = {
                'value_at_risk': self._calculate_var(returns, position_size),
                'expected_shortfall': self._calculate_cvar(returns, position_size),
                'drawdown': self._calculate_drawdown(updated['close']),
                'tail_risk': self._calculate_tail_risk(returns),
                'distribution': self._analyze_distribution(returns),
                'correlation': self._calculate_correlation(updated)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error processing risk metrics: {str(e)}")
            raise
            
    def _calculate_var(
        self,
        returns: pd.Series,
        position_size: Optional[float]
    ) -> Dict:
        """Calculate Value at Risk metrics"""
        try:
            metrics = {}
            for window in self.windows:
                rolling_returns = returns.rolling(window).apply(
                    lambda x: self._var_calculation(
                        x, self.confidence_level
                    )
                )
                
                var_pct = float(rolling_returns.iloc[-1])
                metrics[f'{window}d'] = {
                    'percentage': var_pct,
                    'monetary': float(
                        var_pct * position_size
                        if position_size
                        else 0
                    )
                }
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {str(e)}")
            return {
                f'{w}d': {'percentage': 0, 'monetary': 0}
                for w in self.windows
            }
            
    def _calculate_cvar(
        self,
        returns: pd.Series,
        position_size: Optional[float]
    ) -> Dict:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        try:
            metrics = {}
            for window in self.windows:
                rolling_cvar = returns.rolling(window).apply(
                    lambda x: self._cvar_calculation(
                        x, self.confidence_level
                    )
                )
                
                cvar_pct = float(rolling_cvar.iloc[-1])
                metrics[f'{window}d'] = {
                    'percentage': cvar_pct,
                    'monetary': float(
                        cvar_pct * position_size
                        if position_size
                        else 0
                    )
                }
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating CVaR: {str(e)}")
            return {
                f'{w}d': {'percentage': 0, 'monetary': 0}
                for w in self.windows
            }
            
    def _calculate_drawdown(
        self,
        prices: pd.Series
    ) -> Dict:
        """Calculate drawdown metrics"""
        try:
            # Calculate running maximum
            running_max = prices.expanding().max()
            drawdown = (prices - running_max) / running_max
            
            metrics = {
                'current': float(drawdown.iloc[-1]),
                'max': float(drawdown.min()),
                'avg': float(drawdown.mean()),
                'duration': self._calculate_drawdown_duration(drawdown)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating drawdown: {str(e)}")
            return {
                'current': 0,
                'max': 0,
                'avg': 0,
                'duration': {'current': 0, 'max': 0, 'avg': 0}
            }
            
    def _calculate_tail_risk(
        self,
        returns: pd.Series
    ) -> Dict:
        """Calculate tail risk metrics"""
        try:
            metrics = {}
            for window in self.windows:
                rolling_data = returns.rolling(window)
                
                # Calculate tail risk metrics
                skew = rolling_data.skew()
                kurt = rolling_data.kurt()
                
                metrics[f'{window}d'] = {
                    'skewness': float(skew.iloc[-1]),
                    'kurtosis': float(kurt.iloc[-1]),
                    'tail_ratio': float(
                        self._calculate_tail_ratio(
                            returns.iloc[-window:]
                        )
                    )
                }
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating tail risk: {str(e)}")
            return {
                f'{w}d': {
                    'skewness': 0,
                    'kurtosis': 0,
                    'tail_ratio': 0
                }
                for w in self.windows
            }
            
    def _analyze_distribution(
        self,
        returns: pd.Series
    ) -> Dict:
        """Analyze return distribution"""
        try:
            metrics = {}
            for window in self.windows:
                window_returns = returns.iloc[-window:]
                
                # Fit normal distribution
                loc, scale = stats.norm.fit(window_returns)
                
                # Perform normality test
                stat, p_value = stats.normaltest(window_returns)
                
                metrics[f'{window}d'] = {
                    'mean': float(loc),
                    'std': float(scale),
                    'normality_test': {
                        'statistic': float(stat),
                        'p_value': float(p_value),
                        'is_normal': bool(p_value > 0.05)
                    }
                }
                
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error analyzing return distribution: {str(e)}"
            )
            return {
                f'{w}d': {
                    'mean': 0,
                    'std': 0,
                    'normality_test': {
                        'statistic': 0,
                        'p_value': 0,
                        'is_normal': False
                    }
                }
                for w in self.windows
            }
            
    def _calculate_correlation(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """Calculate correlation metrics"""
        try:
            metrics = {}
            for window in self.windows:
                # Calculate correlations
                corr = data.iloc[-window:].corr()
                
                metrics[f'{window}d'] = {
                    'price_volume': float(
                        corr.loc['close', 'volume']
                    ),
                    'high_low': float(
                        corr.loc['high', 'low']
                    ),
                    'open_close': float(
                        corr.loc['open', 'close']
                    )
                }
                
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error calculating correlations: {str(e)}"
            )
            return {
                f'{w}d': {
                    'price_volume': 0,
                    'high_low': 0,
                    'open_close': 0
                }
                for w in self.windows
            }
            
    def _var_calculation(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> float:
        """Calculate VaR for a single window"""
        try:
            return float(np.percentile(
                returns,
                100 * (1 - confidence_level)
            ))
        except Exception:
            return 0
            
    def _cvar_calculation(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> float:
        """Calculate CVaR for a single window"""
        try:
            var = self._var_calculation(returns, confidence_level)
            return float(
                returns[returns <= var].mean()
                if len(returns[returns <= var]) > 0
                else var
            )
        except Exception:
            return 0
            
    def _calculate_drawdown_duration(
        self,
        drawdown: pd.Series
    ) -> Dict:
        """Calculate drawdown duration metrics"""
        try:
            # Find drawdown periods
            is_drawdown = drawdown < 0
            
            # Calculate durations
            duration = pd.Series(0, index=drawdown.index)
            current_duration = 0
            
            for i, in_drawdown in enumerate(is_drawdown):
                if in_drawdown:
                    current_duration += 1
                else:
                    current_duration = 0
                duration.iloc[i] = current_duration
                
            return {
                'current': int(duration.iloc[-1]),
                'max': int(duration.max()),
                'avg': float(duration[duration > 0].mean())
            }
            
        except Exception:
            return {'current': 0, 'max': 0, 'avg': 0}
            
    def _calculate_tail_ratio(
        self,
        returns: pd.Series
    ) -> float:
        """Calculate ratio of right tail to left tail"""
        try:
            returns_sorted = np.sort(returns)
            tail_size = int(len(returns) * 0.1)
            
            if tail_size == 0:
                return 0
                
            left_tail = abs(returns_sorted[:tail_size].mean())
            right_tail = abs(returns_sorted[-tail_size:].mean())
            
            return (
                right_tail / left_tail
                if left_tail != 0
                else 0
            )
            
        except Exception:
            return 0
            
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
