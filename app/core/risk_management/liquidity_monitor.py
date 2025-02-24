"""
Liquidity Monitoring Module
Monitors market liquidity and adjusts trading accordingly
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

class LiquidityMonitor:
    """Monitors market liquidity and provides trading recommendations"""
    
    def __init__(self, config: Dict):
        """
        Initialize liquidity monitor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.min_liquidity_ratio = Decimal(str(config.get('min_liquidity_ratio', 3.0)))
        self.max_slippage = Decimal(str(config.get('max_slippage', 0.01)))
        self.volume_window = int(config.get('volume_window', 24))  # hours
        self.liquidity_threshold = Decimal(str(config.get('liquidity_threshold', 1000.0)))
        
        # Cache for liquidity data
        self.liquidity_cache: Dict[str, Dict] = {}
        
    async def check_liquidity(
        self,
        symbol: str,
        order_size: Decimal,
        orderbook: Dict,
        recent_volume: Decimal
    ) -> Dict:
        """
        Check if market has sufficient liquidity for order
        
        Args:
            symbol: Trading pair symbol
            order_size: Intended order size
            orderbook: Current orderbook
            recent_volume: Recent trading volume
            
        Returns:
            Dict containing liquidity analysis
        """
        try:
            # Calculate liquidity metrics
            spread = self._calculate_spread(orderbook)
            depth = self._calculate_depth(orderbook, order_size)
            volume_ratio = self._calculate_volume_ratio(order_size, recent_volume)
            
            # Estimate slippage
            estimated_slippage = self._estimate_slippage(order_size, orderbook)
            
            # Update liquidity cache
            self.update_liquidity_cache(symbol, spread, depth, volume_ratio)
            
            # Determine if liquidity is sufficient
            is_liquid = (
                spread <= self.max_slippage and
                depth >= self.min_liquidity_ratio and
                volume_ratio <= Decimal('0.1')  # Order size <= 10% of volume
            )
            
            return {
                'is_liquid': is_liquid,
                'spread': spread,
                'depth': depth,
                'volume_ratio': volume_ratio,
                'estimated_slippage': estimated_slippage,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error checking liquidity for {symbol}: {str(e)}")
            return {
                'is_liquid': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
            
    def get_optimal_order_size(
        self,
        symbol: str,
        desired_size: Decimal,
        orderbook: Dict,
        recent_volume: Decimal
    ) -> Decimal:
        """
        Calculate optimal order size based on liquidity
        
        Args:
            symbol: Trading pair symbol
            desired_size: Desired order size
            orderbook: Current orderbook
            recent_volume: Recent trading volume
            
        Returns:
            Optimal order size
        """
        try:
            # Calculate maximum order size based on different metrics
            max_by_depth = self._max_size_by_depth(orderbook)
            max_by_volume = recent_volume * Decimal('0.1')  # Max 10% of volume
            
            # Take the minimum of all constraints
            optimal_size = min(
                desired_size,
                max_by_depth,
                max_by_volume
            )
            
            logger.debug(
                f"Optimal order size for {symbol}: {optimal_size} "
                f"(desired: {desired_size}, depth: {max_by_depth}, "
                f"volume: {max_by_volume})"
            )
            
            return optimal_size
            
        except Exception as e:
            logger.error(f"Error calculating optimal order size: {str(e)}")
            return Decimal('0')
            
    def should_split_order(
        self,
        order_size: Decimal,
        orderbook: Dict,
        recent_volume: Decimal
    ) -> Optional[List[Decimal]]:
        """
        Determine if order should be split and suggest sizes
        
        Args:
            order_size: Intended order size
            orderbook: Current orderbook
            recent_volume: Recent trading volume
            
        Returns:
            List of split order sizes if should split, None otherwise
        """
        try:
            # Calculate metrics
            avg_trade_size = recent_volume / Decimal('24')  # Assuming 24h volume
            book_depth = self._calculate_depth(orderbook, order_size)
            
            # Determine if splitting is needed
            if (order_size > avg_trade_size * Decimal('2') or
                book_depth < self.min_liquidity_ratio):
                
                # Calculate number of splits needed
                num_splits = int(max(
                    2,
                    min(
                        5,  # Maximum 5 splits
                        (order_size / avg_trade_size).quantize(Decimal('1'))
                    )
                ))
                
                # Calculate split sizes
                base_size = (order_size / Decimal(str(num_splits))).quantize(
                    Decimal('0.00001')
                )
                
                return [base_size] * num_splits
                
            return None
            
        except Exception as e:
            logger.error(f"Error calculating order splits: {str(e)}")
            return None
            
    def update_liquidity_cache(
        self,
        symbol: str,
        spread: Decimal,
        depth: Decimal,
        volume_ratio: Decimal
    ) -> None:
        """Update liquidity metrics cache"""
        self.liquidity_cache[symbol] = {
            'spread': spread,
            'depth': depth,
            'volume_ratio': volume_ratio,
            'timestamp': datetime.now()
        }
        
    def _calculate_spread(self, orderbook: Dict) -> Decimal:
        """Calculate bid-ask spread"""
        try:
            best_bid = Decimal(str(orderbook['bids'][0][0]))
            best_ask = Decimal(str(orderbook['asks'][0][0]))
            mid_price = (best_bid + best_ask) / Decimal('2')
            
            return (best_ask - best_bid) / mid_price
            
        except (IndexError, KeyError) as e:
            logger.error(f"Error calculating spread: {str(e)}")
            return Decimal('999')
            
    def _calculate_depth(
        self,
        orderbook: Dict,
        order_size: Decimal
    ) -> Decimal:
        """Calculate market depth ratio"""
        try:
            # Sum order book depth up to 2x order size
            target_size = order_size * Decimal('2')
            
            bid_depth = sum(
                Decimal(str(size)) for _, size in orderbook['bids']
                if Decimal(str(size)) <= target_size
            )
            
            ask_depth = sum(
                Decimal(str(size)) for _, size in orderbook['asks']
                if Decimal(str(size)) <= target_size
            )
            
            return min(bid_depth, ask_depth) / order_size
            
        except Exception as e:
            logger.error(f"Error calculating depth: {str(e)}")
            return Decimal('0')
            
    def _calculate_volume_ratio(
        self,
        order_size: Decimal,
        recent_volume: Decimal
    ) -> Decimal:
        """Calculate order size to volume ratio"""
        if recent_volume == 0:
            return Decimal('999')
            
        return order_size / recent_volume
        
    def _estimate_slippage(
        self,
        order_size: Decimal,
        orderbook: Dict
    ) -> Decimal:
        """Estimate slippage for order size"""
        try:
            # Get best bid/ask
            best_bid = Decimal(str(orderbook['bids'][0][0]))
            best_ask = Decimal(str(orderbook['asks'][0][0]))
            
            # Calculate weighted average price after order
            if order_size > 0:
                total_size = Decimal('0')
                weighted_price = Decimal('0')
                
                for price, size in orderbook['asks']:
                    price = Decimal(str(price))
                    size = Decimal(str(size))
                    
                    if total_size + size > order_size:
                        remaining = order_size - total_size
                        weighted_price += price * remaining
                        break
                        
                    weighted_price += price * size
                    total_size += size
                    
                    if total_size >= order_size:
                        break
                        
                avg_price = weighted_price / order_size
                return (avg_price - best_ask) / best_ask
                
            return Decimal('0')
            
        except Exception as e:
            logger.error(f"Error estimating slippage: {str(e)}")
            return Decimal('999')
            
    def _max_size_by_depth(self, orderbook: Dict) -> Decimal:
        """Calculate maximum order size based on orderbook depth"""
        try:
            # Sum up to configured depth threshold
            bid_depth = Decimal('0')
            ask_depth = Decimal('0')
            
            for _, size in orderbook['bids']:
                bid_depth += Decimal(str(size))
                if bid_depth >= self.liquidity_threshold:
                    break
                    
            for _, size in orderbook['asks']:
                ask_depth += Decimal(str(size))
                if ask_depth >= self.liquidity_threshold:
                    break
                    
            return min(bid_depth, ask_depth)
            
        except Exception as e:
            logger.error(f"Error calculating max size by depth: {str(e)}")
            return Decimal('0')
