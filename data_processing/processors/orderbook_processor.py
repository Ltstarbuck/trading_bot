"""
Order book processor
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger

class OrderBookProcessor:
    """Processes order book data"""
    
    def __init__(
        self,
        depth_levels: List[int] = [5, 10, 20, 50],
        cache_size: int = 100
    ):
        """
        Initialize order book processor
        
        Args:
            depth_levels: List of depth levels to analyze
            cache_size: Maximum snapshots to cache
        """
        self.depth_levels = depth_levels
        self.cache_size = cache_size
        self._cache: Dict[str, List[Dict]] = {}
        
    def process_orderbook(
        self,
        symbol: str,
        bids: pd.DataFrame,
        asks: pd.DataFrame,
        timestamp: datetime
    ) -> Dict:
        """
        Process order book data
        
        Args:
            symbol: Trading pair symbol
            bids: Bid orders DataFrame
            asks: Ask orders DataFrame
            timestamp: Current timestamp
            
        Returns:
            Processed metrics dictionary
        """
        try:
            # Initialize cache for symbol
            if symbol not in self._cache:
                self._cache[symbol] = []
                
            # Calculate metrics
            metrics = {
                'timestamp': timestamp,
                'spread': self._calculate_spread(bids, asks),
                'mid_price': self._calculate_mid_price(bids, asks),
                'imbalance': self._calculate_imbalance(bids, asks),
                'depth': self._calculate_depth(bids, asks),
                'pressure': self._calculate_pressure(bids, asks),
                'volatility': self._calculate_volatility(bids, asks)
            }
            
            # Update cache
            self._cache[symbol].append(metrics)
            
            # Maintain cache size
            if len(self._cache[symbol]) > self.cache_size:
                self._cache[symbol].pop(0)
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error processing order book: {str(e)}")
            raise
            
    def _calculate_spread(
        self,
        bids: pd.DataFrame,
        asks: pd.DataFrame
    ) -> Dict:
        """Calculate bid-ask spread metrics"""
        try:
            best_bid = float(bids['price'].iloc[0])
            best_ask = float(asks['price'].iloc[0])
            mid_price = (best_bid + best_ask) / 2
            
            return {
                'absolute': best_ask - best_bid,
                'relative': (best_ask - best_bid) / mid_price * 100
            }
            
        except Exception:
            return {'absolute': 0, 'relative': 0}
            
    def _calculate_mid_price(
        self,
        bids: pd.DataFrame,
        asks: pd.DataFrame
    ) -> float:
        """Calculate mid price"""
        try:
            best_bid = float(bids['price'].iloc[0])
            best_ask = float(asks['price'].iloc[0])
            return (best_bid + best_ask) / 2
        except Exception:
            return 0
            
    def _calculate_imbalance(
        self,
        bids: pd.DataFrame,
        asks: pd.DataFrame
    ) -> Dict:
        """Calculate order book imbalance"""
        imbalance = {}
        
        try:
            for depth in self.depth_levels:
                bid_volume = float(
                    bids['amount'][:depth].sum()
                )
                ask_volume = float(
                    asks['amount'][:depth].sum()
                )
                total_volume = bid_volume + ask_volume
                
                if total_volume > 0:
                    imbalance[f'depth_{depth}'] = (
                        (bid_volume - ask_volume) / total_volume
                    )
                else:
                    imbalance[f'depth_{depth}'] = 0
                    
        except Exception as e:
            logger.error(f"Error calculating imbalance: {str(e)}")
            for depth in self.depth_levels:
                imbalance[f'depth_{depth}'] = 0
                
        return imbalance
        
    def _calculate_depth(
        self,
        bids: pd.DataFrame,
        asks: pd.DataFrame
    ) -> Dict:
        """Calculate order book depth"""
        depth = {}
        
        try:
            for level in self.depth_levels:
                depth[f'bids_{level}'] = float(
                    bids['amount'][:level].sum()
                )
                depth[f'asks_{level}'] = float(
                    asks['amount'][:level].sum()
                )
                
        except Exception as e:
            logger.error(f"Error calculating depth: {str(e)}")
            for level in self.depth_levels:
                depth[f'bids_{level}'] = 0
                depth[f'asks_{level}'] = 0
                
        return depth
        
    def _calculate_pressure(
        self,
        bids: pd.DataFrame,
        asks: pd.DataFrame
    ) -> Dict:
        """Calculate buying/selling pressure"""
        pressure = {}
        
        try:
            mid_price = self._calculate_mid_price(bids, asks)
            
            for depth in self.depth_levels:
                # Calculate price-weighted volume
                bid_pressure = float(sum(
                    row['price'] * row['amount']
                    for _, row in bids[:depth].iterrows()
                )) / mid_price
                
                ask_pressure = float(sum(
                    row['price'] * row['amount']
                    for _, row in asks[:depth].iterrows()
                )) / mid_price
                
                pressure[f'depth_{depth}'] = {
                    'buy': bid_pressure,
                    'sell': ask_pressure,
                    'ratio': (
                        bid_pressure / ask_pressure
                        if ask_pressure > 0
                        else 0
                    )
                }
                
        except Exception as e:
            logger.error(f"Error calculating pressure: {str(e)}")
            for depth in self.depth_levels:
                pressure[f'depth_{depth}'] = {
                    'buy': 0,
                    'sell': 0,
                    'ratio': 0
                }
                
        return pressure
        
    def _calculate_volatility(
        self,
        bids: pd.DataFrame,
        asks: pd.DataFrame
    ) -> Dict:
        """Calculate order book volatility"""
        volatility = {}
        
        try:
            for depth in self.depth_levels:
                # Calculate price variance
                bid_prices = bids['price'][:depth].values
                ask_prices = asks['price'][:depth].values
                all_prices = np.concatenate([bid_prices, ask_prices])
                
                volatility[f'depth_{depth}'] = float(np.std(all_prices))
                
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            for depth in self.depth_levels:
                volatility[f'depth_{depth}'] = 0
                
        return volatility
        
    def get_cached_metrics(
        self,
        symbol: str,
        window: Optional[int] = None
    ) -> List[Dict]:
        """
        Get cached metrics for symbol
        
        Args:
            symbol: Trading pair symbol
            window: Optional number of recent snapshots
            
        Returns:
            List of metric dictionaries
        """
        if symbol not in self._cache:
            return []
            
        if window:
            return self._cache[symbol][-window:]
        return self._cache[symbol]
        
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
