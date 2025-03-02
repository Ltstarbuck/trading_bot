"""
Real-time market data feed aggregator
"""

from typing import Dict, List, Optional, Any, Set
from decimal import Decimal
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger

from .base_feed import MarketDataFeed
from ..market_data import MarketData
from ...utils.validation import validate_trading_pair

class RealtimeFeed:
    """Aggregates and processes real-time market data from multiple feeds"""
    
    def __init__(
        self,
        feeds: List[MarketDataFeed],
        symbols: Set[str],
        update_interval: float = 1.0,
        cache_size: int = 1000
    ):
        """
        Initialize real-time feed
        
        Args:
            feeds: List of market data feeds
            symbols: Set of trading pairs to track
            update_interval: Update interval in seconds
            cache_size: Number of data points to cache
        """
        self.feeds = feeds
        self.symbols = symbols
        self.update_interval = update_interval
        self.cache_size = cache_size
        
        # Validate symbols
        for symbol in symbols:
            validate_trading_pair(symbol)
            
        # Initialize data structures
        self._market_data = {}
        self._ohlcv_cache = {}
        self._order_book_cache = {}
        self._trade_cache = {}
        self._last_update = {}
        self._subscribers = []
        self._running = False
        self._lock = asyncio.Lock()
        
        # Initialize caches for each symbol
        for symbol in symbols:
            self._init_symbol_cache(symbol)
            
    def _init_symbol_cache(self, symbol: str) -> None:
        """
        Initialize data caches for symbol
        
        Args:
            symbol: Trading pair symbol
        """
        # OHLCV cache with columns
        self._ohlcv_cache[symbol] = pd.DataFrame(
            columns=[
                'timestamp', 'open', 'high', 'low',
                'close', 'volume', 'vwap'
            ]
        )
        
        # Order book cache
        self._order_book_cache[symbol] = {
            'bids': pd.DataFrame(columns=['price', 'amount']),
            'asks': pd.DataFrame(columns=['price', 'amount'])
        }
        
        # Trade cache
        self._trade_cache[symbol] = pd.DataFrame(
            columns=[
                'timestamp', 'price', 'amount',
                'side', 'type'
            ]
        )
        
    async def start(self) -> None:
        """Start real-time feed"""
        if self._running:
            return
            
        try:
            # Start all feeds
            for feed in self.feeds:
                await feed.start()
                feed.subscribe(self._handle_feed_update)
                
            self._running = True
            
            # Start update loop
            asyncio.create_task(self._update_loop())
            
            logger.info("Started real-time feed")
            
        except Exception as e:
            logger.error(f"Error starting real-time feed: {str(e)}")
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop real-time feed"""
        self._running = False
        
        # Stop all feeds
        for feed in self.feeds:
            feed.unsubscribe(self._handle_feed_update)
            await feed.stop()
            
        logger.info("Stopped real-time feed")
        
    async def _update_loop(self) -> None:
        """Update loop for processing and aggregating data"""
        while self._running:
            try:
                async with self._lock:
                    for symbol in self.symbols:
                        await self._process_symbol_data(symbol)
                        
            except Exception as e:
                logger.error(f"Error in update loop: {str(e)}")
                
            await asyncio.sleep(self.update_interval)
            
    async def _handle_feed_update(
        self,
        symbol: str,
        data: Dict
    ) -> None:
        """
        Handle feed data update
        
        Args:
            symbol: Trading pair symbol
            data: Market data dictionary
        """
        if symbol not in self.symbols:
            return
            
        try:
            async with self._lock:
                # Update market data
                if symbol not in self._market_data:
                    self._market_data[symbol] = {}
                    
                self._market_data[symbol].update(data)
                self._last_update[symbol] = datetime.now()
                
        except Exception as e:
            logger.error(
                f"Error handling feed update for {symbol}: {str(e)}"
            )
            
    async def _process_symbol_data(self, symbol: str) -> None:
        """
        Process and aggregate symbol data
        
        Args:
            symbol: Trading pair symbol
        """
        try:
            data = self._market_data.get(symbol, {})
            if not data:
                return
                
            # Process OHLCV data
            if 'last' in data and 'baseVolume' in data:
                self._update_ohlcv(symbol, data)
                
            # Process order book
            if 'orderbook' in data:
                self._update_order_book(symbol, data['orderbook'])
                
            # Process trades
            if 'trades' in data:
                self._update_trades(symbol, data['trades'])
                
            # Notify subscribers
            await self._notify_subscribers(symbol)
            
        except Exception as e:
            logger.error(
                f"Error processing {symbol} data: {str(e)}"
            )
            
    def _update_ohlcv(
        self,
        symbol: str,
        data: Dict
    ) -> None:
        """
        Update OHLCV cache
        
        Args:
            symbol: Trading pair symbol
            data: Market data dictionary
        """
        try:
            timestamp = pd.Timestamp(data['timestamp'])
            price = Decimal(data['last'])
            volume = Decimal(data['baseVolume'])
            
            df = self._ohlcv_cache[symbol]
            
            # Add new data point
            new_row = pd.DataFrame([{
                'timestamp': timestamp,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume,
                'vwap': price
            }])
            
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Maintain cache size
            if len(df) > self.cache_size:
                df = df.iloc[-self.cache_size:]
                
            self._ohlcv_cache[symbol] = df
            
        except Exception as e:
            logger.error(
                f"Error updating OHLCV for {symbol}: {str(e)}"
            )
            
    def _update_order_book(
        self,
        symbol: str,
        orderbook: Dict
    ) -> None:
        """
        Update order book cache
        
        Args:
            symbol: Trading pair symbol
            orderbook: Order book dictionary
        """
        try:
            # Update bids
            bids_df = pd.DataFrame(
                orderbook['bids'],
                columns=['price', 'amount']
            )
            bids_df = bids_df.astype(float)
            bids_df = bids_df.sort_values('price', ascending=False)
            
            # Update asks
            asks_df = pd.DataFrame(
                orderbook['asks'],
                columns=['price', 'amount']
            )
            asks_df = asks_df.astype(float)
            asks_df = asks_df.sort_values('price', ascending=True)
            
            self._order_book_cache[symbol] = {
                'bids': bids_df,
                'asks': asks_df
            }
            
        except Exception as e:
            logger.error(
                f"Error updating order book for {symbol}: {str(e)}"
            )
            
    def _update_trades(
        self,
        symbol: str,
        trades: List[Dict]
    ) -> None:
        """
        Update trade cache
        
        Args:
            symbol: Trading pair symbol
            trades: List of trade dictionaries
        """
        try:
            # Convert to DataFrame
            trades_df = pd.DataFrame(trades)
            trades_df['timestamp'] = pd.to_datetime(
                trades_df['timestamp']
            )
            
            df = self._trade_cache[symbol]
            df = pd.concat([df, trades_df], ignore_index=True)
            
            # Maintain cache size
            if len(df) > self.cache_size:
                df = df.iloc[-self.cache_size:]
                
            self._trade_cache[symbol] = df
            
        except Exception as e:
            logger.error(
                f"Error updating trades for {symbol}: {str(e)}"
            )
            
    def subscribe(self, callback) -> None:
        """
        Subscribe to data updates
        
        Args:
            callback: Async callback function
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            
    def unsubscribe(self, callback) -> None:
        """
        Unsubscribe from data updates
        
        Args:
            callback: Subscribed callback function
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            
    async def _notify_subscribers(self, symbol: str) -> None:
        """
        Notify subscribers of data update
        
        Args:
            symbol: Updated symbol
        """
        for callback in self._subscribers:
            try:
                await callback(symbol, self.get_symbol_data(symbol))
            except Exception as e:
                logger.error(
                    f"Error in subscriber callback: {str(e)}"
                )
                
    def get_symbol_data(self, symbol: str) -> Dict:
        """
        Get current symbol data
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Symbol data dictionary
        """
        return {
            'symbol': symbol,
            'ohlcv': self._ohlcv_cache[symbol],
            'orderbook': self._order_book_cache[symbol],
            'trades': self._trade_cache[symbol],
            'last_update': self._last_update.get(symbol)
        }
        
    @property
    def is_running(self) -> bool:
        """Check if feed is running"""
        return self._running
