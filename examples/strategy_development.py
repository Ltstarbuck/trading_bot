"""
Example of developing and implementing trading strategies
"""

import asyncio
from decimal import Decimal
from typing import Dict, Optional
from app.core.strategies.base_strategy import BaseStrategy, Signal
from app.core.exchanges.ftx import FTXExchange
from app.core.risk_management.risk_monitor import RiskMonitor
from app.core.portfolio.position_tracker import PositionTracker
from app.core.logging.logger import TradingBotLogger

class MovingAverageCrossStrategy(BaseStrategy):
    """Simple moving average crossover strategy"""
    
    def __init__(self, fast_period: int = 20,
                 slow_period: int = 50):
        """Initialize strategy parameters"""
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices = []
        
    def calculate_sma(self, period: int) -> Optional[Decimal]:
        """Calculate simple moving average"""
        if len(self.prices) < period:
            return None
        return sum(self.prices[-period:]) / period
        
    async def generate_signal(self, data: Dict) -> Signal:
        """Generate trading signal based on MA cross"""
        # Add new price
        price = Decimal(str(data['close']))
        self.prices.append(price)
        
        # Calculate moving averages
        fast_ma = self.calculate_sma(self.fast_period)
        slow_ma = self.calculate_sma(self.slow_period)
        
        if not (fast_ma and slow_ma):
            return Signal.HOLD
            
        # Generate signal
        if fast_ma > slow_ma:
            return Signal.BUY
        elif fast_ma < slow_ma:
            return Signal.SELL
        return Signal.HOLD
        
class RSIStrategy(BaseStrategy):
    """RSI-based mean reversion strategy"""
    
    def __init__(self, period: int = 14,
                 overbought: int = 70,
                 oversold: int = 30):
        """Initialize strategy parameters"""
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.prices = []
        self.gains = []
        self.losses = []
        
    def calculate_rsi(self) -> Optional[Decimal]:
        """Calculate RSI value"""
        if len(self.prices) < self.period + 1:
            return None
            
        # Calculate price changes
        changes = [self.prices[i+1] - self.prices[i]
                  for i in range(len(self.prices)-1)]
        
        # Separate gains and losses
        gains = [max(0, change) for change in changes]
        losses = [max(0, -change) for change in changes]
        
        # Calculate averages
        avg_gain = sum(gains[-self.period:]) / self.period
        avg_loss = sum(losses[-self.period:]) / self.period
        
        if avg_loss == 0:
            return Decimal(100)
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return Decimal(str(rsi))
        
    async def generate_signal(self, data: Dict) -> Signal:
        """Generate trading signal based on RSI"""
        # Add new price
        price = Decimal(str(data['close']))
        self.prices.append(price)
        
        # Calculate RSI
        rsi = self.calculate_rsi()
        if not rsi:
            return Signal.HOLD
            
        # Generate signal
        if rsi <= self.oversold:
            return Signal.BUY
        elif rsi >= self.overbought:
            return Signal.SELL
        return Signal.HOLD
        
async def run_strategy_example():
    """Run strategy trading example"""
    # Initialize components
    logger = TradingBotLogger('config/logging_config.yaml')
    exchange = FTXExchange()
    risk_monitor = RiskMonitor()
    position_tracker = PositionTracker()
    
    # Create strategies
    ma_strategy = MovingAverageCrossStrategy()
    rsi_strategy = RSIStrategy()
    
    # Trading parameters
    symbol = "BTC/USD"
    amount = Decimal("0.01")
    
    try:
        while True:
            # Get market data
            candle = await exchange.get_candle(symbol)
            
            # Generate signals
            ma_signal = await ma_strategy.generate_signal(candle)
            rsi_signal = await rsi_strategy.generate_signal(candle)
            
            # Combined signal logic
            signal = Signal.HOLD
            if ma_signal == rsi_signal:
                signal = ma_signal
                
            # Execute trades
            position = position_tracker.get_position(symbol)
            
            if signal == Signal.BUY and not position:
                # Check risk limits
                price = Decimal(str(candle['close']))
                position_size = amount * price
                
                if risk_monitor.check_position_size(position_size):
                    # Create buy order
                    order = await exchange.create_order(
                        symbol=symbol,
                        type="market",
                        side="buy",
                        amount=amount
                    )
                    logger.info(f"Buy order created: {order['id']}")
                    
            elif signal == Signal.SELL and position:
                # Create sell order
                order = await exchange.create_order(
                    symbol=symbol,
                    type="market",
                    side="sell",
                    amount=position.size
                )
                logger.info(f"Sell order created: {order['id']}")
                
            await asyncio.sleep(60)  # Check every minute
            
    except Exception as e:
        logger.exception(f"Error in strategy loop: {e}")
        
if __name__ == "__main__":
    asyncio.run(run_strategy_example())
