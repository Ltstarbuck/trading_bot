"""
Position Sizing Module
Implements various position sizing strategies
"""

from decimal import Decimal
from typing import Dict, Optional
import numpy as np
from loguru import logger

class PositionSizer:
    """Calculates appropriate position sizes based on various methods"""
    
    def __init__(self, config: Dict):
        """
        Initialize position sizer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_position_size = Decimal(str(config.get('max_position_size', 0.1)))
        self.risk_per_trade = Decimal(str(config.get('risk_per_trade', 0.01)))
        self.max_positions = int(config.get('max_positions', 5))
        
    def calculate_position_size(
        self,
        available_balance: Decimal,
        current_price: Decimal,
        volatility: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None,
        method: str = 'fixed_risk'
    ) -> Decimal:
        """
        Calculate position size based on specified method
        
        Args:
            available_balance: Available balance for trading
            current_price: Current market price
            volatility: Optional market volatility
            stop_loss: Optional stop loss price
            method: Position sizing method
            
        Returns:
            Position size in base currency
        """
        try:
            # Validate inputs
            if available_balance <= 0:
                logger.error("Available balance must be positive")
                return Decimal('0')
            if current_price <= 0:
                logger.error("Current price must be positive")
                return Decimal('0')
            if volatility is not None and volatility < 0:
                logger.error("Volatility cannot be negative")
                return Decimal('0')
            if stop_loss is not None and stop_loss <= 0:
                logger.error("Stop loss must be positive")
                return Decimal('0')
                
            if method == 'fixed_risk':
                return self._fixed_risk_position_size(
                    available_balance,
                    current_price,
                    stop_loss
                )
            elif method == 'kelly':
                return self._kelly_position_size(
                    available_balance,
                    current_price,
                    volatility
                )
            elif method == 'equal_weight':
                return self._equal_weight_position_size(
                    available_balance,
                    current_price
                )
            else:
                logger.warning(f"Unknown position sizing method: {method}")
                return self._fixed_risk_position_size(
                    available_balance,
                    current_price,
                    stop_loss
                )
                
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return Decimal('0')
            
    def _fixed_risk_position_size(
        self,
        available_balance: Decimal,
        current_price: Decimal,
        stop_loss: Optional[Decimal]
    ) -> Decimal:
        """
        Calculate position size based on fixed risk per trade
        
        Args:
            available_balance: Available balance
            current_price: Current price
            stop_loss: Stop loss price
            
        Returns:
            Position size
        """
        # If no stop loss, use maximum drawdown
        if not stop_loss:
            stop_loss = current_price * (Decimal('1') - self.risk_per_trade)
            
        # Calculate risk amount
        risk_amount = available_balance * self.risk_per_trade
        
        # Calculate position size based on risk
        price_risk = abs(current_price - stop_loss)
        if price_risk == 0:
            return Decimal('0')
            
        position_size = risk_amount / price_risk
        
        # Apply maximum position size limit
        max_size = available_balance * self.max_position_size / current_price
        return min(position_size, max_size)
        
    def _kelly_position_size(
        self,
        available_balance: Decimal,
        current_price: Decimal,
        volatility: Optional[Decimal]
    ) -> Decimal:
        """
        Calculate position size using Kelly Criterion
        
        Args:
            available_balance: Available balance
            current_price: Current price
            volatility: Market volatility
            
        Returns:
            Position size
        """
        if not volatility:
            return self._fixed_risk_position_size(
                available_balance,
                current_price,
                None
            )
            
        try:
            # Estimate win probability based on volatility and market conditions
            # Higher volatility = lower win probability
            base_prob = Decimal('0.55')  # Slight edge assumption
            vol_adjustment = volatility * Decimal('5')  # Scale volatility impact
            win_prob = max(
                Decimal('0.1'),
                min(Decimal('0.9'), base_prob - vol_adjustment)
            )
            
            # Calculate payoff ratio based on risk management settings
            risk_amount = self.risk_per_trade * available_balance
            target_return = risk_amount * Decimal('2')  # 2:1 reward-risk ratio
            payoff_ratio = target_return / risk_amount
            
            # Kelly formula: f = (bp - q) / b
            # where: b = net odds received on win
            #        p = probability of win
            #        q = probability of loss (1 - p)
            kelly_fraction = (payoff_ratio * win_prob - (Decimal('1') - win_prob)) / payoff_ratio
            
            # Apply a fraction of Kelly to be more conservative
            kelly_fraction = kelly_fraction * Decimal('0.5')  # Half-Kelly
            
            # Ensure kelly fraction is within reasonable bounds
            kelly_fraction = max(Decimal('0'), min(kelly_fraction, Decimal('0.5')))
            
            # Calculate position size
            position_size = (available_balance * kelly_fraction) / current_price
            
            # Apply maximum position size limit
            max_size = available_balance * self.max_position_size / current_price
            return min(position_size, max_size)
            
        except Exception as e:
            logger.error(f"Error in Kelly calculation: {str(e)}")
            return self._fixed_risk_position_size(
                available_balance,
                current_price,
                None
            )
        
    def _equal_weight_position_size(
        self,
        available_balance: Decimal,
        current_price: Decimal
    ) -> Decimal:
        """
        Calculate position size by equally dividing available balance
        
        Args:
            available_balance: Available balance
            current_price: Current price
            
        Returns:
            Position size
        """
        # Divide balance by maximum number of positions
        position_value = available_balance / Decimal(str(self.max_positions))
        position_size = position_value / current_price
        
        # Apply maximum position size limit
        max_size = available_balance * self.max_position_size / current_price
        return min(position_size, max_size)
        
    def adjust_for_correlation(
        self,
        position_size: Decimal,
        symbol: str,
        open_positions: Dict
    ) -> Decimal:
        """
        Adjust position size based on correlation with open positions
        
        Args:
            position_size: Initial position size
            symbol: Trading symbol
            open_positions: Currently open positions
            
        Returns:
            Adjusted position size
        """
        # This is a placeholder for correlation-based adjustment
        # In a real implementation, you would:
        # 1. Calculate correlation between assets
        # 2. Reduce position size if adding highly correlated assets
        # 3. Consider portfolio beta and sector exposure
        
        return position_size
        
    def adjust_for_volatility(
        self,
        position_size: Decimal,
        volatility: Decimal,
        avg_volatility: Decimal
    ) -> Decimal:
        """
        Adjust position size based on relative volatility
        
        Args:
            position_size: Initial position size
            volatility: Current volatility
            avg_volatility: Average market volatility
            
        Returns:
            Adjusted position size
        """
        if avg_volatility == 0:
            return position_size
            
        # Adjust size inversely to relative volatility
        volatility_ratio = avg_volatility / volatility
        return position_size * Decimal(str(volatility_ratio))
