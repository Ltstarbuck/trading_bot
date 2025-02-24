"""
Example of implementing risk management strategies
"""

import asyncio
from decimal import Decimal
from typing import Dict, List
from app.core.risk_management.risk_monitor import RiskMonitor
from app.core.risk_management.position_sizing import PositionSizer
from app.core.risk_management.stop_loss import StopLossManager
from app.core.portfolio.position_tracker import PositionTracker
from app.core.exchanges.ftx import FTXExchange
from app.core.logging.logger import TradingBotLogger

class RiskManager:
    """Risk management system implementation"""
    
    def __init__(self):
        """Initialize risk management components"""
        self.logger = TradingBotLogger('config/logging_config.yaml')
        self.risk_monitor = RiskMonitor()
        self.position_sizer = PositionSizer()
        self.stop_loss_manager = StopLossManager()
        self.position_tracker = PositionTracker()
        self.exchange = FTXExchange()
        
        # Risk parameters
        self.max_position_size = Decimal("0.1")  # 10% of equity
        self.risk_per_trade = Decimal("0.01")    # 1% risk per trade
        self.max_correlation = Decimal("0.7")     # 70% correlation limit
        self.max_drawdown = Decimal("0.1")       # 10% max drawdown
        
    async def check_portfolio_risk(self) -> bool:
        """Check overall portfolio risk levels"""
        # Get portfolio stats
        stats = self.position_tracker.get_portfolio_stats()
        
        # Check drawdown
        if stats['drawdown'] >= self.max_drawdown:
            self.logger.warning(
                f"Maximum drawdown exceeded: {stats['drawdown']:.2%}")
            return False
            
        # Check exposure
        if stats['total_exposure'] >= self.max_position_size:
            self.logger.warning(
                f"Maximum exposure exceeded: {stats['total_exposure']:.2%}")
            return False
            
        return True
        
    async def check_position_correlation(self,
                                       symbol: str) -> bool:
        """Check position correlation with portfolio"""
        # Get current positions
        positions = self.position_tracker.get_all_positions()
        if not positions:
            return True
            
        # Get correlation matrix
        correlations = await self._calculate_correlations(
            [p.symbol for p in positions] + [symbol]
        )
        
        # Check correlation limits
        for pos in positions:
            corr = correlations.get((symbol, pos.symbol))
            if corr and abs(corr) >= self.max_correlation:
                self.logger.warning(
                    f"High correlation between {symbol} "
                    f"and {pos.symbol}: {corr:.2f}")
                return False
                
        return True
        
    async def calculate_position_size(self,
                                    symbol: str,
                                    entry_price: Decimal,
                                    stop_loss: Decimal) -> Decimal:
        """Calculate appropriate position size"""
        # Get account equity
        account = await self.exchange.get_account()
        equity = Decimal(str(account['equity']))
        
        # Calculate risk amount
        risk_amount = equity * self.risk_per_trade
        
        # Calculate position size
        size = self.position_sizer.calculate_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            risk_amount=risk_amount
        )
        
        # Check against limits
        max_size = equity * self.max_position_size
        return min(size, max_size)
        
    async def set_stop_loss(self,
                           symbol: str,
                           entry_price: Decimal,
                           side: str) -> Decimal:
        """Set initial stop loss level"""
        # Calculate stop loss price
        stop_price = self.stop_loss_manager.calculate_stop_loss(
            entry_price=entry_price,
            risk_percent=float(self.risk_per_trade),
            side=side
        )
        
        # Create stop loss order
        await self.exchange.create_order(
            symbol=symbol,
            type="stop",
            side="sell" if side == "buy" else "buy",
            stop_price=stop_price,
            amount=self.position_tracker.get_position(symbol).size
        )
        
        return stop_price
        
    async def update_trailing_stop(self,
                                 symbol: str,
                                 current_price: Decimal,
                                 current_stop: Decimal) -> Decimal:
        """Update trailing stop loss"""
        # Calculate new stop price
        new_stop = self.stop_loss_manager.update_trailing_stop(
            current_price=current_price,
            current_stop=current_stop,
            trail_percent=0.01  # 1% trailing stop
        )
        
        if new_stop != current_stop:
            # Update stop loss order
            position = self.position_tracker.get_position(symbol)
            await self.exchange.create_order(
                symbol=symbol,
                type="stop",
                side="sell" if position.side == "buy" else "buy",
                stop_price=new_stop,
                amount=position.size
            )
            
        return new_stop
        
    async def _calculate_correlations(self,
                                    symbols: List[str]) -> Dict:
        """Calculate correlation matrix for symbols"""
        # Get historical prices
        prices = {}
        for symbol in symbols:
            candles = await self.exchange.get_candles(
                symbol=symbol,
                timeframe="1h",
                limit=168  # 1 week of hourly data
            )
            prices[symbol] = [
                Decimal(str(c['close'])) for c in candles
            ]
            
        # Calculate correlations
        correlations = {}
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self._calculate_correlation(
                    prices[sym1], prices[sym2]
                )
                correlations[(sym1, sym2)] = corr
                correlations[(sym2, sym1)] = corr
                
        return correlations
        
    def _calculate_correlation(self,
                             prices1: List[Decimal],
                             prices2: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient between two price series"""
        if len(prices1) != len(prices2):
            return Decimal('0')
            
        n = len(prices1)
        if n < 2:
            return Decimal('0')
            
        # Calculate means
        mean1 = sum(prices1) / n
        mean2 = sum(prices2) / n
        
        # Calculate covariance and variances
        covar = sum((p1 - mean1) * (p2 - mean2)
                   for p1, p2 in zip(prices1, prices2))
        var1 = sum((p - mean1) ** 2 for p in prices1)
        var2 = sum((p - mean2) ** 2 for p in prices2)
        
        # Calculate correlation
        if var1 == 0 or var2 == 0:
            return Decimal('0')
            
        return covar / (var1.sqrt() * var2.sqrt())
        
async def run_risk_example():
    """Run risk management example"""
    risk_manager = RiskManager()
    logger = risk_manager.logger
    
    try:
        # Trading parameters
        symbol = "BTC/USD"
        side = "buy"
        
        # Check portfolio risk
        if not await risk_manager.check_portfolio_risk():
            logger.warning("Portfolio risk limits exceeded")
            return
            
        # Check correlation
        if not await risk_manager.check_position_correlation(symbol):
            logger.warning("Correlation limits exceeded")
            return
            
        # Get market data
        ticker = await risk_manager.exchange.get_ticker(symbol)
        entry_price = Decimal(str(ticker['last']))
        
        # Calculate stop loss
        stop_loss = entry_price * Decimal("0.98")  # 2% below entry
        
        # Calculate position size
        size = await risk_manager.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
        
        # Place entry order
        order = await risk_manager.exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=size
        )
        logger.info(f"Entry order created: {order['id']}")
        
        # Set stop loss
        stop_price = await risk_manager.set_stop_loss(
            symbol=symbol,
            entry_price=entry_price,
            side=side
        )
        logger.info(f"Stop loss set at: ${stop_price}")
        
        # Monitor and update stops
        while True:
            # Get current price
            ticker = await risk_manager.exchange.get_ticker(symbol)
            current_price = Decimal(str(ticker['last']))
            
            # Update trailing stop
            new_stop = await risk_manager.update_trailing_stop(
                symbol=symbol,
                current_price=current_price,
                current_stop=stop_price
            )
            
            if new_stop != stop_price:
                logger.info(f"Stop loss updated to: ${new_stop}")
                stop_price = new_stop
                
            # Check portfolio risk
            if not await risk_manager.check_portfolio_risk():
                logger.warning("Closing position due to risk limits")
                await risk_manager.exchange.create_order(
                    symbol=symbol,
                    type="market",
                    side="sell" if side == "buy" else "buy",
                    amount=size
                )
                break
                
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.exception(f"Error in risk management loop: {e}")
        
if __name__ == "__main__":
    asyncio.run(run_risk_example())
