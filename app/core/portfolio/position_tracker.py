"""
Position Tracker
Manages and tracks all trading positions
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import asyncio
from loguru import logger

class Position:
    """Represents a trading position"""
    
    def __init__(
        self,
        symbol: str,
        entry_price: Decimal,
        amount: Decimal,
        side: str,
        stop_loss: Decimal,
        trailing_stop: Decimal,
        exchange_id: str,
        fees: Decimal = Decimal('0'),
        position_id: Optional[str] = None
    ):
        self.symbol = symbol
        self.entry_price = entry_price
        self.amount = amount
        self.side = side  # 'long' or 'short'
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        self.exchange_id = exchange_id
        self.fees = fees
        self.position_id = position_id or f"{symbol}-{datetime.now().timestamp()}"
        
        self.current_price: Decimal = entry_price
        self.highest_price: Decimal = entry_price
        self.lowest_price: Decimal = entry_price
        self.unrealized_pnl: Decimal = Decimal('0')
        self.realized_pnl: Decimal = Decimal('0')
        self.status = 'open'
        self.entry_time = datetime.now()
        self.exit_time: Optional[datetime] = None
        
    def update_price(self, price: Decimal) -> bool:
        """
        Update position with new price
        
        Returns:
            bool: True if stop loss triggered
        """
        self.current_price = price
        
        if price > self.highest_price:
            self.highest_price = price
        if price < self.lowest_price:
            self.lowest_price = price
            
        # Calculate unrealized P&L
        if self.side == 'long':
            self.unrealized_pnl = (price - self.entry_price) * self.amount - self.fees
            # Update trailing stop
            trailing_stop_price = price * (Decimal('1') - self.trailing_stop)
            self.stop_loss = max(self.stop_loss, trailing_stop_price)
            # Check stop loss
            return price <= self.stop_loss
        else:  # short
            self.unrealized_pnl = (self.entry_price - price) * self.amount - self.fees
            # Update trailing stop
            trailing_stop_price = price * (Decimal('1') + self.trailing_stop)
            self.stop_loss = min(self.stop_loss, trailing_stop_price)
            # Check stop loss
            return price >= self.stop_loss
            
    def close(self, exit_price: Decimal, exit_fees: Decimal = Decimal('0')) -> None:
        """Close the position"""
        self.current_price = exit_price
        self.exit_time = datetime.now()
        self.status = 'closed'
        self.fees += exit_fees
        
        if self.side == 'long':
            self.realized_pnl = (exit_price - self.entry_price) * self.amount - self.fees
        else:
            self.realized_pnl = (self.entry_price - exit_price) * self.amount - self.fees

class PositionTracker:
    """Tracks and manages all trading positions"""
    
    def __init__(self):
        """Initialize position tracker"""
        self.positions: Dict[str, Position] = {}  # Active positions
        self.closed_positions: List[Position] = []  # Historical positions
        self._price_update_tasks: Dict[str, asyncio.Task[None]] = {}
        
    def open_position(
        self,
        symbol: str,
        entry_price: Decimal,
        amount: Decimal,
        side: str,
        stop_loss: Decimal,
        trailing_stop: Decimal,
        exchange_id: str,
        fees: Decimal = Decimal('0')
    ) -> Position:
        """
        Open a new position
        
        Returns:
            Position: The newly created position
        """
        position = Position(
            symbol=symbol,
            entry_price=entry_price,
            amount=amount,
            side=side,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop,
            exchange_id=exchange_id,
            fees=fees
        )
        
        self.positions[position.position_id] = position
        logger.info(f"Opened {side} position for {symbol} at {entry_price}")
        return position
        
    def close_position(
        self,
        position_id: str,
        exit_price: Decimal,
        exit_fees: Decimal = Decimal('0')
    ) -> Optional[Position]:
        """
        Close an existing position
        
        Returns:
            Position: The closed position or None if not found
        """
        position = self.positions.get(position_id)
        if position:
            position.close(exit_price, exit_fees)
            self.closed_positions.append(position)
            del self.positions[position_id]
            
            # Cancel any associated price update task
            if position_id in self._price_update_tasks:
                self._price_update_tasks[position_id].cancel()
                del self._price_update_tasks[position_id]
            
            logger.info(
                f"Closed {position.side} position for {position.symbol} "
                f"at {exit_price} with P&L: {position.realized_pnl}"
            )
            return position
        return None
        
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        return self.positions.get(position_id)
        
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get all positions for a symbol"""
        return [p for p in self.positions.values() if p.symbol == symbol]
        
    def get_all_positions(self) -> List[Position]:
        """Get all active positions"""
        return list(self.positions.values())
        
    def get_closed_positions(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Position]:
        """Get closed positions with optional filters"""
        positions = self.closed_positions
        
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
            
        if start_time:
            positions = [p for p in positions if p.exit_time >= start_time]
            
        if end_time:
            positions = [p for p in positions if p.exit_time <= end_time]
            
        return positions
        
    def get_total_pnl(self) -> Decimal:
        """Get total P&L across all positions"""
        realized_pnl = sum(p.realized_pnl for p in self.closed_positions)
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        return realized_pnl + unrealized_pnl
        
    def get_position_value(self) -> Decimal:
        """Get total value of all open positions"""
        return sum(p.current_price * p.amount for p in self.positions.values())
        
    async def update_position_prices(
        self,
        symbol: str,
        price: Decimal
    ) -> List[str]:
        """
        Update prices for all positions of a symbol
        
        Returns:
            List[str]: IDs of positions that hit their stop loss
        """
        stop_loss_triggered = []
        
        for position in self.get_positions_by_symbol(symbol):
            if position.update_price(price):
                stop_loss_triggered.append(position.position_id)
                
        return stop_loss_triggered
        
    def clear_positions(self) -> None:
        """Clear all position data"""
        self.positions.clear()
        self.closed_positions.clear()
        logger.info("Cleared all position data")
