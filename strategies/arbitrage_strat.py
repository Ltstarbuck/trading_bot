"""
Arbitrage trading strategy implementation
"""

from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
import asyncio
from loguru import logger

from ..data_processing.feeds import CCXTFeed, WebSocketFeed
from ..portfolio.position_tracker import PositionTracker
from ..risk_management.position_sizing import PositionSizer
from ..risk_management.stop_loss import StopLossManager

class ArbitrageStrategy:
    """
    Implements various arbitrage strategies:
    - Triangular arbitrage
    - Cross-exchange arbitrage
    - Statistical arbitrage
    """
    
    def __init__(
        self,
        exchanges: List[str],
        trading_pairs: List[str],
        min_profit_threshold: float = 0.002,  # 0.2%
        max_position_size: float = 1000.0,
        risk_per_trade: float = 0.01,  # 1%
        max_slippage: float = 0.001,  # 0.1%
        execution_timeout: int = 5  # seconds
    ):
        """
        Initialize arbitrage strategy
        
        Args:
            exchanges: List of exchange IDs
            trading_pairs: List of trading pairs
            min_profit_threshold: Minimum profit threshold
            max_position_size: Maximum position size
            risk_per_trade: Risk per trade as percentage
            max_slippage: Maximum allowed slippage
            execution_timeout: Maximum execution timeout
        """
        self.exchanges = exchanges
        self.trading_pairs = trading_pairs
        self.min_profit_threshold = min_profit_threshold
        self.max_position_size = max_position_size
        self.risk_per_trade = risk_per_trade
        self.max_slippage = max_slippage
        self.execution_timeout = execution_timeout
        
        # Initialize components
        self.position_tracker = PositionTracker()
        self.position_sizer = PositionSizer()
        self.stop_loss_manager = StopLossManager()
        
        # Initialize data feeds
        self.feeds: Dict[str, Union[CCXTFeed, WebSocketFeed]] = {}
        self._initialize_feeds()
        
        # Cache for order books and trades
        self.orderbook_cache: Dict[str, Dict] = {}
        self.trade_cache: Dict[str, List] = {}
        
    async def run(self) -> None:
        """Run arbitrage strategy"""
        try:
            # Start data feeds
            await self._start_feeds()
            
            while True:
                # Update market data
                await self._update_market_data()
                
                # Find arbitrage opportunities
                opportunities = await asyncio.gather(
                    self._find_triangular_arbitrage(),
                    self._find_cross_exchange_arbitrage(),
                    self._find_statistical_arbitrage()
                )
                
                # Execute profitable opportunities
                for opportunity in opportunities:
                    if opportunity and self._validate_opportunity(opportunity):
                        await self._execute_arbitrage(opportunity)
                        
                # Sleep to avoid overwhelming the exchanges
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error running arbitrage strategy: {str(e)}")
            raise
            
    async def _find_triangular_arbitrage(self) -> Optional[Dict]:
        """
        Find triangular arbitrage opportunities
        Returns opportunity dict if found, None otherwise
        """
        try:
            opportunities = []
            
            for exchange in self.exchanges:
                pairs = self._get_trading_pairs(exchange)
                
                # Find currency triangles
                triangles = self._find_currency_triangles(pairs)
                
                for triangle in triangles:
                    # Calculate profit potential
                    profit = await self._calculate_triangular_profit(
                        exchange,
                        triangle
                    )
                    
                    if profit > self.min_profit_threshold:
                        opportunities.append({
                            'type': 'triangular',
                            'exchange': exchange,
                            'pairs': triangle,
                            'profit': profit
                        })
                        
            # Return best opportunity
            return max(
                opportunities,
                key=lambda x: x['profit']
            ) if opportunities else None
            
        except Exception as e:
            logger.error(
                f"Error finding triangular arbitrage: {str(e)}"
            )
            return None
            
    async def _find_cross_exchange_arbitrage(self) -> Optional[Dict]:
        """
        Find cross-exchange arbitrage opportunities
        Returns opportunity dict if found, None otherwise
        """
        try:
            opportunities = []
            
            for pair in self.trading_pairs:
                # Get order books from all exchanges
                order_books = {
                    ex: self.orderbook_cache.get(
                        f"{ex}_{pair}"
                    )
                    for ex in self.exchanges
                }
                
                # Find price discrepancies
                for ex1 in self.exchanges:
                    for ex2 in self.exchanges:
                        if ex1 != ex2:
                            profit = await self._calculate_cross_exchange_profit(
                                ex1,
                                ex2,
                                pair,
                                order_books
                            )
                            
                            if profit > self.min_profit_threshold:
                                opportunities.append({
                                    'type': 'cross_exchange',
                                    'buy_exchange': ex1,
                                    'sell_exchange': ex2,
                                    'pair': pair,
                                    'profit': profit
                                })
                                
            # Return best opportunity
            return max(
                opportunities,
                key=lambda x: x['profit']
            ) if opportunities else None
            
        except Exception as e:
            logger.error(
                f"Error finding cross-exchange arbitrage: {str(e)}"
            )
            return None
            
    async def _find_statistical_arbitrage(self) -> Optional[Dict]:
        """
        Find statistical arbitrage opportunities
        Returns opportunity dict if found, None otherwise
        """
        try:
            opportunities = []
            
            for pair in self.trading_pairs:
                # Get price history from all exchanges
                price_history = {
                    ex: self._get_price_history(ex, pair)
                    for ex in self.exchanges
                }
                
                # Calculate price relationships
                for ex1 in self.exchanges:
                    for ex2 in self.exchanges:
                        if ex1 != ex2:
                            # Calculate z-score of price spread
                            z_score = self._calculate_spread_zscore(
                                price_history[ex1],
                                price_history[ex2]
                            )
                            
                            # Check for mean reversion opportunity
                            if abs(z_score) > 2:
                                opportunities.append({
                                    'type': 'statistical',
                                    'long_exchange': ex1 if z_score < 0 else ex2,
                                    'short_exchange': ex2 if z_score < 0 else ex1,
                                    'pair': pair,
                                    'z_score': abs(z_score)
                                })
                                
            # Return best opportunity
            return max(
                opportunities,
                key=lambda x: x['z_score']
            ) if opportunities else None
            
        except Exception as e:
            logger.error(
                f"Error finding statistical arbitrage: {str(e)}"
            )
            return None
            
    async def _execute_arbitrage(self, opportunity: Dict) -> None:
        """
        Execute arbitrage opportunity
        
        Args:
            opportunity: Arbitrage opportunity dict
        """
        try:
            # Calculate position size
            size = self._calculate_position_size(opportunity)
            
            if opportunity['type'] == 'triangular':
                await self._execute_triangular_arbitrage(
                    opportunity,
                    size
                )
            elif opportunity['type'] == 'cross_exchange':
                await self._execute_cross_exchange_arbitrage(
                    opportunity,
                    size
                )
            else:  # statistical
                await self._execute_statistical_arbitrage(
                    opportunity,
                    size
                )
                
        except Exception as e:
            logger.error(f"Error executing arbitrage: {str(e)}")
            
    def _validate_opportunity(self, opportunity: Dict) -> bool:
        """
        Validate arbitrage opportunity
        
        Args:
            opportunity: Arbitrage opportunity dict
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if opportunity is still profitable
            if opportunity['type'] == 'triangular':
                current_profit = self._calculate_triangular_profit(
                    opportunity['exchange'],
                    opportunity['pairs']
                )
            elif opportunity['type'] == 'cross_exchange':
                current_profit = self._calculate_cross_exchange_profit(
                    opportunity['buy_exchange'],
                    opportunity['sell_exchange'],
                    opportunity['pair'],
                    self.orderbook_cache
                )
            else:  # statistical
                current_profit = abs(opportunity['z_score'])
                
            # Check profitability threshold
            if current_profit < self.min_profit_threshold:
                return False
                
            # Check position limits
            if not self._check_position_limits(opportunity):
                return False
                
            # Check liquidity
            if not self._check_liquidity(opportunity):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating opportunity: {str(e)}")
            return False
            
    def _calculate_position_size(self, opportunity: Dict) -> float:
        """
        Calculate position size for arbitrage
        
        Args:
            opportunity: Arbitrage opportunity dict
            
        Returns:
            Position size
        """
        try:
            # Get base position size
            size = self.position_sizer.calculate_size(
                self.risk_per_trade,
                self.max_position_size
            )
            
            # Adjust for liquidity
            size = min(
                size,
                self._get_max_executable_size(opportunity)
            )
            
            return size
            
        except Exception as e:
            logger.error(
                f"Error calculating position size: {str(e)}"
            )
            return 0
            
    async def _start_feeds(self) -> None:
        """Start market data feeds"""
        try:
            for exchange in self.exchanges:
                if exchange not in self.feeds:
                    # Initialize feed
                    self.feeds[exchange] = CCXTFeed(
                        exchange_id=exchange
                    )
                    
                # Start feed
                await self.feeds[exchange].connect()
                
                # Subscribe to trading pairs
                for pair in self.trading_pairs:
                    await self.feeds[exchange].subscribe(pair)
                    
        except Exception as e:
            logger.error(f"Error starting feeds: {str(e)}")
            raise
            
    async def _update_market_data(self) -> None:
        """Update market data caches"""
        try:
            for exchange in self.exchanges:
                for pair in self.trading_pairs:
                    # Update order book
                    orderbook = await self.feeds[
                        exchange
                    ].fetch_order_book(pair)
                    
                    self.orderbook_cache[
                        f"{exchange}_{pair}"
                    ] = orderbook
                    
                    # Update trades
                    trades = await self.feeds[
                        exchange
                    ].fetch_trades(pair)
                    
                    self.trade_cache[
                        f"{exchange}_{pair}"
                    ] = trades
                    
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
            
    def _initialize_feeds(self) -> None:
        """Initialize market data feeds"""
        try:
            for exchange in self.exchanges:
                self.feeds[exchange] = CCXTFeed(
                    exchange_id=exchange
                )
                
        except Exception as e:
            logger.error(f"Error initializing feeds: {str(e)}")
            raise
            
    def _get_trading_pairs(self, exchange: str) -> List[str]:
        """Get trading pairs for exchange"""
        return self.trading_pairs
        
    def _find_currency_triangles(
        self,
        pairs: List[str]
    ) -> List[List[str]]:
        """Find currency triangles in trading pairs"""
        triangles = []
        
        # Implementation depends on pair format
        # This is a simplified version
        return triangles
        
    async def _calculate_triangular_profit(
        self,
        exchange: str,
        triangle: List[str]
    ) -> float:
        """Calculate profit for triangular arbitrage"""
        try:
            # Get order books
            books = [
                self.orderbook_cache.get(f"{exchange}_{pair}")
                for pair in triangle
            ]
            
            # Calculate cross-rates and profit
            # Implementation depends on pair format
            return 0.0
            
        except Exception:
            return 0.0
            
    async def _calculate_cross_exchange_profit(
        self,
        ex1: str,
        ex2: str,
        pair: str,
        order_books: Dict
    ) -> float:
        """Calculate profit for cross-exchange arbitrage"""
        try:
            book1 = order_books.get(ex1)
            book2 = order_books.get(ex2)
            
            if not (book1 and book2):
                return 0.0
                
            # Get best bid/ask
            bid1 = book1['bids'][0][0] if book1['bids'] else 0
            ask1 = book1['asks'][0][0] if book1['asks'] else float('inf')
            bid2 = book2['bids'][0][0] if book2['bids'] else 0
            ask2 = book2['asks'][0][0] if book2['asks'] else float('inf')
            
            # Calculate profit opportunities
            profit1 = (bid2 / ask1) - 1  # Buy on ex1, sell on ex2
            profit2 = (bid1 / ask2) - 1  # Buy on ex2, sell on ex1
            
            return max(profit1, profit2)
            
        except Exception:
            return 0.0
            
    def _get_price_history(
        self,
        exchange: str,
        pair: str
    ) -> pd.Series:
        """Get price history for pair"""
        try:
            trades = self.trade_cache.get(f"{exchange}_{pair}", [])
            prices = [t['price'] for t in trades]
            return pd.Series(prices)
        except Exception:
            return pd.Series()
            
    def _calculate_spread_zscore(
        self,
        prices1: pd.Series,
        prices2: pd.Series
    ) -> float:
        """Calculate z-score of price spread"""
        try:
            if len(prices1) == 0 or len(prices2) == 0:
                return 0.0
                
            # Calculate spread
            spread = prices1 / prices2
            
            # Calculate z-score
            z_score = (
                spread - spread.mean()
            ) / spread.std()
            
            return float(z_score.iloc[-1])
            
        except Exception:
            return 0.0
            
    def _check_position_limits(
        self,
        opportunity: Dict
    ) -> bool:
        """Check if opportunity respects position limits"""
        try:
            # Get current positions
            positions = self.position_tracker.get_positions()
            
            # Check limits based on opportunity type
            if opportunity['type'] == 'triangular':
                # Check each pair in triangle
                for pair in opportunity['pairs']:
                    if not self._check_pair_limit(
                        pair,
                        positions
                    ):
                        return False
                        
            elif opportunity['type'] == 'cross_exchange':
                # Check single pair across exchanges
                if not self._check_pair_limit(
                    opportunity['pair'],
                    positions
                ):
                    return False
                    
            else:  # statistical
                # Check pair on both exchanges
                if not (
                    self._check_pair_limit(
                        opportunity['pair'],
                        positions,
                        opportunity['long_exchange']
                    ) and
                    self._check_pair_limit(
                        opportunity['pair'],
                        positions,
                        opportunity['short_exchange']
                    )
                ):
                    return False
                    
            return True
            
        except Exception:
            return False
            
    def _check_pair_limit(
        self,
        pair: str,
        positions: Dict,
        exchange: Optional[str] = None
    ) -> bool:
        """Check if pair respects position limits"""
        try:
            # Get current position
            position = positions.get(
                f"{exchange}_{pair}" if exchange else pair,
                0
            )
            
            # Check against limit
            return abs(position) < self.max_position_size
            
        except Exception:
            return False
            
    def _check_liquidity(self, opportunity: Dict) -> bool:
        """Check if opportunity has sufficient liquidity"""
        try:
            if opportunity['type'] == 'triangular':
                # Check liquidity for each pair
                for pair in opportunity['pairs']:
                    if not self._check_pair_liquidity(
                        opportunity['exchange'],
                        pair
                    ):
                        return False
                        
            elif opportunity['type'] == 'cross_exchange':
                # Check liquidity on both exchanges
                if not (
                    self._check_pair_liquidity(
                        opportunity['buy_exchange'],
                        opportunity['pair']
                    ) and
                    self._check_pair_liquidity(
                        opportunity['sell_exchange'],
                        opportunity['pair']
                    )
                ):
                    return False
                    
            else:  # statistical
                # Check liquidity for both positions
                if not (
                    self._check_pair_liquidity(
                        opportunity['long_exchange'],
                        opportunity['pair']
                    ) and
                    self._check_pair_liquidity(
                        opportunity['short_exchange'],
                        opportunity['pair']
                    )
                ):
                    return False
                    
            return True
            
        except Exception:
            return False
            
    def _check_pair_liquidity(
        self,
        exchange: str,
        pair: str
    ) -> bool:
        """Check if pair has sufficient liquidity"""
        try:
            # Get order book
            book = self.orderbook_cache.get(
                f"{exchange}_{pair}"
            )
            
            if not book:
                return False
                
            # Calculate available liquidity
            bid_liquidity = sum(
                amt for _, amt in book['bids'][:5]
            )
            ask_liquidity = sum(
                amt for _, amt in book['asks'][:5]
            )
            
            # Check against minimum required
            min_required = self.max_position_size * 3
            return (
                bid_liquidity > min_required and
                ask_liquidity > min_required
            )
            
        except Exception:
            return False
            
    def _get_max_executable_size(
        self,
        opportunity: Dict
    ) -> float:
        """Get maximum executable size for opportunity"""
        try:
            sizes = []
            
            if opportunity['type'] == 'triangular':
                # Check each pair
                for pair in opportunity['pairs']:
                    sizes.append(
                        self._get_pair_executable_size(
                            opportunity['exchange'],
                            pair
                        )
                    )
                    
            elif opportunity['type'] == 'cross_exchange':
                # Check both exchanges
                sizes.extend([
                    self._get_pair_executable_size(
                        opportunity['buy_exchange'],
                        opportunity['pair']
                    ),
                    self._get_pair_executable_size(
                        opportunity['sell_exchange'],
                        opportunity['pair']
                    )
                ])
                
            else:  # statistical
                # Check both positions
                sizes.extend([
                    self._get_pair_executable_size(
                        opportunity['long_exchange'],
                        opportunity['pair']
                    ),
                    self._get_pair_executable_size(
                        opportunity['short_exchange'],
                        opportunity['pair']
                    )
                ])
                
            return min(sizes) if sizes else 0
            
        except Exception:
            return 0
            
    def _get_pair_executable_size(
        self,
        exchange: str,
        pair: str
    ) -> float:
        """Get maximum executable size for pair"""
        try:
            # Get order book
            book = self.orderbook_cache.get(
                f"{exchange}_{pair}"
            )
            
            if not book:
                return 0
                
            # Calculate executable size with slippage limit
            size = 0
            initial_price = book['asks'][0][0]
            
            for price, amount in book['asks']:
                # Check slippage
                slippage = (price - initial_price) / initial_price
                if slippage > self.max_slippage:
                    break
                    
                size += amount
                
            return size
            
        except Exception:
            return 0
