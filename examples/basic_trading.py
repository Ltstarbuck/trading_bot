"""
Basic trading example demonstrating core functionality
"""

import asyncio
from decimal import Decimal
from app.core.exchanges.ftx import FTXExchange
from app.core.risk_management.risk_monitor import RiskMonitor
from app.core.portfolio.position_tracker import PositionTracker
from app.core.logging.logger import TradingBotLogger

async def run_basic_trading():
    """Run basic trading example"""
    # Initialize components
    logger = TradingBotLogger('config/logging_config.yaml')
    exchange = FTXExchange()
    risk_monitor = RiskMonitor()
    position_tracker = PositionTracker()
    
    # Set up trading parameters
    symbol = "BTC/USD"
    side = "buy"
    amount = Decimal("0.01")
    
    try:
        # Get market data
        ticker = await exchange.get_ticker(symbol)
        logger.info(f"Current {symbol} price: ${ticker['last']}")
        
        # Check risk limits
        position_size = amount * Decimal(str(ticker['last']))
        if not risk_monitor.check_position_size(position_size):
            logger.warning("Position size exceeds risk limits")
            return
            
        # Create market order
        order = await exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=amount
        )
        logger.info(f"Order created: {order['id']}")
        
        # Wait for fill
        filled_order = await exchange.wait_for_fill(order['id'])
        logger.info(f"Order filled at ${filled_order['price']}")
        
        # Track position
        position_tracker.add_position(
            symbol=symbol,
            side=side,
            size=amount,
            entry_price=Decimal(str(filled_order['price']))
        )
        
        # Monitor position
        while True:
            # Update price
            ticker = await exchange.get_ticker(symbol)
            current_price = Decimal(str(ticker['last']))
            
            # Update position
            position_tracker.update_position(
                symbol=symbol,
                current_price=current_price
            )
            
            # Check stop loss
            position = position_tracker.get_position(symbol)
            if position and position.unrealized_pnl_pct <= -0.01:
                # Close position if down 1%
                await exchange.create_order(
                    symbol=symbol,
                    type="market",
                    side="sell" if side == "buy" else "buy",
                    amount=amount
                )
                logger.info("Position closed due to stop loss")
                break
                
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.exception(f"Error in trading loop: {e}")
        
if __name__ == "__main__":
    asyncio.run(run_basic_trading())
