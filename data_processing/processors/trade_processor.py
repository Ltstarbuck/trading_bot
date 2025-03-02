"""
Trade data processor
"""

from typing import Dict, List, Optional, Union
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

class TradeProcessor:
    """Processes trade data"""
    
    def __init__(
        self,
        time_windows: List[str] = ['1m', '5m', '15m', '1h'],
        cache_size: int = 1000
    ):
        """
        Initialize trade processor
        
        Args:
            time_windows: List of time windows for analysis
            cache_size: Maximum trades to cache
        """
        self.time_windows = time_windows
        self.cache_size = cache_size
        self._cache: Dict[str, pd.DataFrame] = {}
        
    def process_trades(
        self,
        symbol: str,
        trades: pd.DataFrame
    ) -> Dict:
        """
        Process trade data
        
        Args:
            symbol: Trading pair symbol
            trades: Trade data DataFrame
            
        Returns:
            Dictionary of trade metrics
        """
        try:
            # Initialize cache for symbol
            if symbol not in self._cache:
                self._cache[symbol] = pd.DataFrame()
                
            # Update cache
            cached = self._cache[symbol]
            updated = pd.concat([cached, trades])
            
            # Remove duplicates and sort
            updated = updated[~updated.index.duplicated(keep='last')]
            updated.sort_index(inplace=True)
            
            # Maintain cache size
            if len(updated) > self.cache_size:
                updated = updated.iloc[-self.cache_size:]
                
            self._cache[symbol] = updated
            
            # Calculate metrics for different time windows
            metrics = {}
            current_time = datetime.now()
            
            for window in self.time_windows:
                window_td = self._parse_time_window(window)
                window_start = current_time - window_td
                window_trades = updated[updated.index >= window_start]
                
                metrics[window] = {
                    'volume': self._calculate_volume(window_trades),
                    'price': self._calculate_price_metrics(window_trades),
                    'trades': self._calculate_trade_metrics(window_trades),
                    'buy_sell': self._calculate_buy_sell_metrics(window_trades)
                }
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error processing trades: {str(e)}")
            raise
            
    def _calculate_volume(
        self,
        trades: pd.DataFrame
    ) -> Dict:
        """Calculate volume metrics"""
        try:
            metrics = {
                'total': float(trades['amount'].sum()),
                'mean': float(trades['amount'].mean()),
                'max': float(trades['amount'].max()),
                'count': len(trades)
            }
            
            # Buy/Sell volume
            buy_trades = trades[trades['side'] == 'buy']
            sell_trades = trades[trades['side'] == 'sell']
            
            metrics.update({
                'buy_volume': float(buy_trades['amount'].sum()),
                'sell_volume': float(sell_trades['amount'].sum()),
                'volume_imbalance': float(
                    (buy_trades['amount'].sum() - 
                     sell_trades['amount'].sum()) /
                    trades['amount'].sum()
                    if len(trades) > 0 else 0
                )
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating volume metrics: {str(e)}")
            return {
                'total': 0,
                'mean': 0,
                'max': 0,
                'count': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'volume_imbalance': 0
            }
            
    def _calculate_price_metrics(
        self,
        trades: pd.DataFrame
    ) -> Dict:
        """Calculate price metrics"""
        try:
            prices = trades['price']
            returns = prices.pct_change()
            
            metrics = {
                'open': float(prices.iloc[0]) if len(prices) > 0 else 0,
                'high': float(prices.max()),
                'low': float(prices.min()),
                'close': float(prices.iloc[-1]) if len(prices) > 0 else 0,
                'vwap': float(
                    (trades['price'] * trades['amount']).sum() /
                    trades['amount'].sum()
                    if len(trades) > 0 else 0
                ),
                'volatility': float(returns.std() * np.sqrt(len(trades)))
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating price metrics: {str(e)}")
            return {
                'open': 0,
                'high': 0,
                'low': 0,
                'close': 0,
                'vwap': 0,
                'volatility': 0
            }
            
    def _calculate_trade_metrics(
        self,
        trades: pd.DataFrame
    ) -> Dict:
        """Calculate trade frequency metrics"""
        try:
            if len(trades) < 2:
                return {
                    'count': len(trades),
                    'frequency': 0,
                    'avg_size': 0,
                    'size_std': 0
                }
                
            # Calculate time between trades
            trade_times = trades.index
            time_diffs = np.diff(trade_times.astype(np.int64)) / 1e9
            
            metrics = {
                'count': len(trades),
                'frequency': float(
                    len(trades) /
                    (trade_times[-1] - trade_times[0]).total_seconds()
                    if len(trades) > 1 else 0
                ),
                'avg_size': float(trades['amount'].mean()),
                'size_std': float(trades['amount'].std())
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating trade metrics: {str(e)}")
            return {
                'count': 0,
                'frequency': 0,
                'avg_size': 0,
                'size_std': 0
            }
            
    def _calculate_buy_sell_metrics(
        self,
        trades: pd.DataFrame
    ) -> Dict:
        """Calculate buy/sell metrics"""
        try:
            buy_trades = trades[trades['side'] == 'buy']
            sell_trades = trades[trades['side'] == 'sell']
            
            metrics = {
                'buy_count': len(buy_trades),
                'sell_count': len(sell_trades),
                'buy_ratio': float(
                    len(buy_trades) / len(trades)
                    if len(trades) > 0 else 0
                ),
                'avg_buy_size': float(
                    buy_trades['amount'].mean()
                    if len(buy_trades) > 0 else 0
                ),
                'avg_sell_size': float(
                    sell_trades['amount'].mean()
                    if len(sell_trades) > 0 else 0
                )
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating buy/sell metrics: {str(e)}")
            return {
                'buy_count': 0,
                'sell_count': 0,
                'buy_ratio': 0,
                'avg_buy_size': 0,
                'avg_sell_size': 0
            }
            
    def _parse_time_window(self, window: str) -> timedelta:
        """
        Parse time window string to timedelta
        
        Args:
            window: Time window string (e.g. '1m', '1h')
            
        Returns:
            Time window as timedelta
        """
        units = {
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks'
        }
        
        # Extract number and unit
        number = int(''.join(filter(str.isdigit, window)))
        unit = ''.join(filter(str.isalpha, window))
        
        if unit not in units:
            raise ValueError(f"Invalid time window unit: {unit}")
            
        return timedelta(**{units[unit]: number})
        
    def get_cached_trades(
        self,
        symbol: str,
        start_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get cached trades for symbol
        
        Args:
            symbol: Trading pair symbol
            start_time: Optional start time filter
            
        Returns:
            DataFrame of cached trades
        """
        if symbol not in self._cache:
            return pd.DataFrame()
            
        trades = self._cache[symbol]
        
        if start_time:
            trades = trades[trades.index >= start_time]
            
        return trades
        
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
