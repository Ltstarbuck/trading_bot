"""
Stop Loss Management Module
Implements various stop loss strategies including trailing stops
"""

from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime
import numpy as np
from loguru import logger

class StopLossManager:
    """Manages stop loss calculations and updates"""
    
    def __init__(self, config: Dict):
        """
        Initialize stop loss manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.default_stop_loss = Decimal(str(config.get('stop_loss_percent', 0.02)))
        self.trailing_stop = Decimal(str(config.get('trailing_stop_percent', 0.01)))
        self.atr_multiplier = Decimal(str(config.get('atr_multiplier', 2.0)))
        self.break_even_trigger = Decimal(str(config.get('break_even_trigger', 0.01)))
        
    def calculate_initial_stop(
        self,
        entry_price: Decimal,
        side: str,
        volatility: Optional[Decimal] = None,
        method: str = 'fixed'
    ) -> Decimal:
        """
        Calculate initial stop loss price
        
        Args:
            entry_price: Position entry price
            side: Position side ('long' or 'short')
            volatility: Optional market volatility
            method: Stop loss calculation method
            
        Returns:
            Stop loss price
        """
        try:
            # Validate inputs
            if entry_price <= 0:
                raise ValueError("Entry price must be positive")
            if side not in ['long', 'short']:
                raise ValueError("Side must be 'long' or 'short'")
            if volatility is not None and volatility < 0:
                raise ValueError("Volatility cannot be negative")
                
            if method == 'fixed':
                return self._fixed_stop_loss(entry_price, side)
            elif method == 'atr':
                return self._atr_based_stop(entry_price, side, volatility)
            elif method == 'volatility':
                return self._volatility_based_stop(entry_price, side, volatility)
            else:
                logger.warning(f"Unknown stop loss method: {method}")
                return self._fixed_stop_loss(entry_price, side)
                
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return entry_price  # Return entry price as fallback
        except Exception as e:
            logger.error(f"Error calculating stop loss: {str(e)}")
            return self._fixed_stop_loss(entry_price, side)
            
    def update_trailing_stop(
        self,
        position: Dict,
        current_price: Decimal
    ) -> Decimal:
        """
        Update trailing stop loss
        
        Args:
            position: Position information
            current_price: Current market price
            
        Returns:
            Updated stop loss price
        """
        try:
            entry_price = Decimal(str(position['entry_price']))
            current_stop = Decimal(str(position['stop_loss']))
            side = position['side']
            
            if side == 'long':
                # Calculate new stop for long position
                trailing_price = current_price * (Decimal('1') - self.trailing_stop)
                
                # Move stop loss up if price has moved up enough
                if trailing_price > current_stop:
                    return trailing_price
                    
            else:  # short position
                # Calculate new stop for short position
                trailing_price = current_price * (Decimal('1') + self.trailing_stop)
                
                # Move stop loss down if price has moved down enough
                if trailing_price < current_stop:
                    return trailing_price
                    
            return current_stop
            
        except Exception as e:
            logger.error(f"Error updating trailing stop: {str(e)}")
            return current_stop
            
    def check_stop_loss(
        self,
        position: Dict,
        current_price: Decimal
    ) -> bool:
        """
        Check if stop loss has been triggered
        
        Args:
            position: Position information
            current_price: Current market price
            
        Returns:
            True if stop loss triggered
        """
        try:
            stop_price = Decimal(str(position['stop_loss']))
            side = position['side']
            
            if side == 'long':
                return current_price <= stop_price
            else:  # short
                return current_price >= stop_price
                
        except Exception as e:
            logger.error(f"Error checking stop loss: {str(e)}")
            return False
            
    def adjust_for_break_even(
        self,
        position: Dict,
        current_price: Decimal,
        fees: Optional[Decimal] = None
    ) -> Optional[Decimal]:
        """
        Adjust stop loss to break even if sufficient profit
        
        Args:
            position: Position information
            current_price: Current market price
            fees: Optional trading fees
            
        Returns:
            New stop loss price if adjusted, None otherwise
        """
        try:
            if current_price <= 0:
                raise ValueError("Current price must be positive")
                
            entry_price = Decimal(str(position['entry_price']))
            side = position['side']
            
            # Calculate total fees
            total_fees = Decimal('0')
            if fees is not None:
                total_fees += fees
            if 'entry_fees' in position:
                total_fees += Decimal(str(position['entry_fees']))
                
            # Calculate required profit to cover fees
            fee_adjustment = total_fees / entry_price
            
            if side == 'long':
                # Need extra profit to cover fees
                profit_pct = (current_price - entry_price) / entry_price - fee_adjustment
                if profit_pct >= self.break_even_trigger:
                    # Set stop slightly above entry to ensure fees are covered
                    return entry_price * (Decimal('1') + fee_adjustment)
                    
            else:  # short
                profit_pct = (entry_price - current_price) / entry_price - fee_adjustment
                if profit_pct >= self.break_even_trigger:
                    # Set stop slightly below entry to ensure fees are covered
                    return entry_price * (Decimal('1') - fee_adjustment)
                    
            return None
            
        except ValueError as e:
            logger.error(f"Validation error in break even adjustment: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error adjusting break even stop: {str(e)}")
            return None
            
    def _fixed_stop_loss(
        self,
        entry_price: Decimal,
        side: str
    ) -> Decimal:
        """Calculate fixed percentage stop loss"""
        if side == 'long':
            return entry_price * (Decimal('1') - self.default_stop_loss)
        else:  # short
            return entry_price * (Decimal('1') + self.default_stop_loss)
            
    def _atr_based_stop(
        self,
        entry_price: Decimal,
        side: str,
        atr: Optional[Decimal]
    ) -> Decimal:
        """Calculate ATR-based stop loss"""
        if not atr:
            return self._fixed_stop_loss(entry_price, side)
            
        stop_distance = atr * self.atr_multiplier
        
        if side == 'long':
            return entry_price - stop_distance
        else:  # short
            return entry_price + stop_distance
            
    def _volatility_based_stop(
        self,
        entry_price: Decimal,
        side: str,
        volatility: Optional[Decimal]
    ) -> Decimal:
        """Calculate volatility-based stop loss"""
        if not volatility:
            return self._fixed_stop_loss(entry_price, side)
            
        # Use volatility to determine stop distance
        stop_distance = entry_price * volatility
        
        if side == 'long':
            return entry_price - stop_distance
        else:  # short
            return entry_price + stop_distance
            
    def get_risk_reward_ratio(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
        side: str
    ) -> Decimal:
        """
        Calculate risk/reward ratio
        
        Args:
            entry_price: Position entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            side: Position side
            
        Returns:
            Risk/Reward ratio
        """
        try:
            if side == 'long':
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:  # short
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
                
            if risk == 0:
                return Decimal('0')
                
            return reward / risk
            
        except Exception as e:
            logger.error(f"Error calculating R/R ratio: {str(e)}")
            return Decimal('0')
