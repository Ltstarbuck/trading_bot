# Trading Bot Examples

This guide provides examples of how to use the trading bot for various trading scenarios.

## Basic Trading

### Market Order Example
```python
from app.core.exchanges.ftx import FTXExchange

async def place_market_order():
    exchange = FTXExchange()
    
    # Place market buy order
    order = await exchange.create_order(
        symbol="BTC/USD",
        type="market",
        side="buy",
        amount=0.01
    )
    print(f"Order created: {order['id']}")
```

### Limit Order Example
```python
from decimal import Decimal

async def place_limit_order():
    exchange = FTXExchange()
    
    # Place limit sell order
    order = await exchange.create_order(
        symbol="BTC/USD",
        type="limit",
        side="sell",
        amount=0.01,
        price=50000.00
    )
    print(f"Order created: {order['id']}")
```

## Risk Management

### Position Sizing Example
```python
from app.core.risk_management.position_sizing import PositionSizer

def calculate_position_size():
    sizer = PositionSizer(
        equity=100000,
        risk_per_trade=0.01  # 1% risk
    )
    
    size = sizer.calculate_size(
        entry_price=50000,
        stop_loss=49000,
        risk_amount=1000
    )
    print(f"Position size: {size} BTC")
```

### Stop Loss Management
```python
from app.core.risk_management.stop_loss import StopLossManager

def manage_stop_loss():
    manager = StopLossManager()
    
    # Set initial stop loss
    stop_price = manager.calculate_stop_loss(
        entry_price=50000,
        risk_percent=0.02,  # 2% risk
        side="buy"
    )
    
    # Update trailing stop
    new_stop = manager.update_trailing_stop(
        current_price=51000,
        current_stop=49000,
        trail_percent=0.01  # 1% trail
    )
```

## Portfolio Management

### Position Tracking
```python
from app.core.portfolio.position_tracker import PositionTracker

def track_positions():
    tracker = PositionTracker()
    
    # Add position
    tracker.add_position(
        symbol="BTC/USD",
        side="buy",
        size=0.1,
        entry_price=50000
    )
    
    # Update position
    tracker.update_position(
        symbol="BTC/USD",
        current_price=51000
    )
    
    # Get position details
    position = tracker.get_position("BTC/USD")
    print(f"Unrealized P&L: ${position.unrealized_pnl}")
```

### Portfolio Analysis
```python
from app.core.portfolio.portfolio_analyzer import PortfolioAnalyzer

def analyze_portfolio():
    analyzer = PortfolioAnalyzer()
    
    # Calculate metrics
    metrics = analyzer.calculate_metrics()
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']}")
    print(f"Max Drawdown: {metrics['max_drawdown']}%")
    print(f"Win Rate: {metrics['win_rate']}%")
```

## Strategy Development

### Simple Moving Average Strategy
```python
from app.core.strategies.base_strategy import BaseStrategy

class SMAStrategy(BaseStrategy):
    def __init__(self, fast_period=20, slow_period=50):
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    async def generate_signal(self, data):
        # Calculate moving averages
        fast_ma = self.calculate_sma(data, self.fast_period)
        slow_ma = self.calculate_sma(data, self.slow_period)
        
        # Generate signals
        if fast_ma > slow_ma:
            return Signal.BUY
        elif fast_ma < slow_ma:
            return Signal.SELL
        return Signal.HOLD
```

### RSI Strategy
```python
class RSIStrategy(BaseStrategy):
    def __init__(self, period=14, overbought=70, oversold=30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    async def generate_signal(self, data):
        # Calculate RSI
        rsi = self.calculate_rsi(data, self.period)
        
        # Generate signals
        if rsi <= self.oversold:
            return Signal.BUY
        elif rsi >= self.overbought:
            return Signal.SELL
        return Signal.HOLD
```

## GUI Usage

### Custom Chart Indicator
```python
from app.core.gui.components.chart_widget import ChartWidget

def add_custom_indicator():
    chart = ChartWidget()
    
    # Add Bollinger Bands
    chart.add_indicator(
        name="BB",
        indicator_type="bollinger_bands",
        params={
            "period": 20,
            "std_dev": 2
        }
    )
```

### Trading Panel Integration
```python
from app.core.gui.components.trading_panel import TradingPanel

def setup_trading_panel():
    panel = TradingPanel()
    
    # Set available symbols
    panel.set_symbols(["BTC/USD", "ETH/USD"])
    
    # Set order defaults
    panel.set_order_defaults({
        "amount": 0.01,
        "price": 50000
    })
    
    # Handle order submission
    async def handle_order(order):
        try:
            result = await exchange.create_order(**order)
            print(f"Order created: {result['id']}")
        except Exception as e:
            print(f"Order error: {e}")
            
    panel.order_submitted.connect(handle_order)
```

## Backtesting

### Strategy Backtesting
```python
from app.core.backtesting.backtester import Backtester

async def backtest_strategy():
    backtester = Backtester()
    
    # Run backtest
    results = await backtester.run(
        strategy=SMAStrategy(20, 50),
        symbol="BTC/USD",
        timeframe="1h",
        start_date="2025-01-01",
        end_date="2025-02-01"
    )
    
    # Print results
    print(f"Total Return: {results['total_return']}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']}")
    print(f"Max Drawdown: {results['max_drawdown']}%")
```

### Parameter Optimization
```python
async def optimize_strategy():
    backtester = Backtester()
    
    # Define parameter ranges
    params = {
        "fast_period": range(10, 30, 5),
        "slow_period": range(40, 60, 5)
    }
    
    # Run optimization
    results = await backtester.optimize(
        strategy=SMAStrategy,
        params=params,
        symbol="BTC/USD",
        timeframe="1h",
        start_date="2025-01-01",
        end_date="2025-02-01"
    )
    
    # Print best parameters
    print(f"Best parameters: {results['best_params']}")
    print(f"Best return: {results['best_return']}%")
```

## Logging and Monitoring

### Custom Logging
```python
from app.core.logging.logger import TradingBotLogger

def setup_logging():
    logger = TradingBotLogger("config/logging_config.yaml")
    
    # Log trading events
    logger.info("Starting trading bot...")
    logger.warning("Risk limit approaching...")
    logger.error("Order execution failed...")
    
    # Log with context
    logger.info("Order filled", extra={
        "symbol": "BTC/USD",
        "side": "buy",
        "price": 50000,
        "amount": 0.1
    })
```

### Performance Monitoring
```python
from app.core.monitoring.performance_monitor import PerformanceMonitor

async def monitor_performance():
    monitor = PerformanceMonitor()
    
    # Start monitoring
    await monitor.start()
    
    # Log metrics
    monitor.log_latency("order_execution", 50)  # ms
    monitor.log_memory_usage(100)  # MB
    monitor.log_cpu_usage(25)  # %
    
    # Get summary
    stats = monitor.get_statistics()
    print(f"Average latency: {stats['avg_latency']}ms")
    print(f"Peak memory: {stats['peak_memory']}MB")
```
