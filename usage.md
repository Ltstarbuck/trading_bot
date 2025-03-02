# Trading Bot Usage Guide

## Getting Started

### Launch the Application

```bash
python main.py
```

The main window will open with several key components:
- Trading Panel (left)
- Chart Display (center)
- Order Book (right)
- Position/Order Tables (bottom)

### Basic Navigation

- Use the symbol selector to choose trading pairs
- Switch between timeframes using the chart toolbar
- Toggle between different chart types (candlestick, line, area)
- Use keyboard shortcuts for common actions

## Trading Operations

### Creating Orders

1. **Market Orders**
   - Select symbol
   - Choose "Market" order type
   - Enter amount
   - Click "Buy" or "Sell"

2. **Limit Orders**
   - Select symbol
   - Choose "Limit" order type
   - Enter amount and price
   - Click "Buy" or "Sell"

3. **Stop Orders**
   - Select symbol
   - Choose "Stop Market" or "Stop Limit"
   - Enter trigger price
   - Enter limit price (for Stop Limit)
   - Click "Buy" or "Sell"

### Managing Positions

1. **Opening Positions**
   ```python
   # Example API usage
   position = await trading_bot.create_order(
       symbol="BTC/USD",
       side="buy",
       type="limit",
       amount=0.1,
       price=50000
   )
   ```

2. **Monitoring Positions**
   - View current positions in the Positions table
   - Monitor P&L in real-time
   - Set price alerts

3. **Closing Positions**
   - Click "Close" in the Positions table
   - Use the Trading Panel with "Close Position" option
   - Set take-profit/stop-loss orders

### Risk Management

1. **Position Sizing**
   - Fixed risk per trade
   - Percentage of equity
   - Kelly criterion
   - Custom sizing methods

2. **Stop Loss Strategies**
   - Fixed percentage
   - ATR-based
   - Volatility-based
   - Trailing stops

3. **Portfolio Management**
   - Maximum positions
   - Maximum drawdown
   - Daily loss limits
   - Correlation management

## Technical Analysis

### Chart Tools

1. **Drawing Tools**
   - Trend lines
   - Fibonacci retracements
   - Support/resistance levels
   - Price channels

2. **Technical Indicators**
   - Moving averages
   - RSI
   - MACD
   - Bollinger Bands
   - Custom indicators

3. **Chart Settings**
   - Timeframe selection
   - Chart type
   - Color schemes
   - Grid settings

### Order Book Analysis

1. **Depth View**
   - Price levels
   - Volume at price
   - Cumulative volume
   - Bid/ask imbalance

2. **Trade Flow**
   - Recent trades
   - Volume profile
   - Time and sales
   - Large orders

## Automation

### Trading Strategies

1. **Creating Strategies**
   ```python
   class SimpleStrategy(BaseStrategy):
       def __init__(self, params):
           self.ma_period = params.get('ma_period', 20)
           
       async def generate_signal(self, data):
           if data['close'] > data['ma']:
               return Signal.BUY
           return Signal.SELL
   ```

2. **Backtesting**
   ```python
   results = await backtest.run(
       strategy=SimpleStrategy,
       symbol="BTC/USD",
       timeframe="1h",
       start_date="2025-01-01",
       end_date="2025-02-23"
   )
   ```

3. **Live Trading**
   ```python
   bot = TradingBot(config)
   bot.add_strategy(SimpleStrategy({'ma_period': 20}))
   await bot.start()
   ```

### Alerts

1. **Price Alerts**
   - Set price targets
   - Break of support/resistance
   - Indicator crossovers
   - Custom conditions

2. **Risk Alerts**
   - Position size limits
   - Drawdown warnings
   - Loss limits
   - Exposure alerts

3. **System Alerts**
   - Connection status
   - Order execution
   - Error notifications
   - Performance issues

## Data Analysis

### Historical Data

1. **Data Download**
   ```python
   data = await exchange.get_candles(
       symbol="BTC/USD",
       timeframe="1h",
       start_time="2025-01-01",
       end_time="2025-02-23"
   )
   ```

2. **Data Analysis**
   ```python
   import pandas as pd
   
   df = pd.DataFrame(data)
   df['returns'] = df['close'].pct_change()
   df['volatility'] = df['returns'].rolling(20).std()
   ```

3. **Performance Analysis**
   - Equity curve
   - Drawdown analysis
   - Risk metrics
   - Trading statistics

### Market Analysis

1. **Volume Analysis**
   - Volume profile
   - VWAP
   - Volume delta
   - Large trades

2. **Volatility Analysis**
   - ATR
   - Bollinger Bands width
   - Historical volatility
   - Implied volatility

3. **Correlation Analysis**
   - Asset correlations
   - Market sectors
   - Risk factors
   - Portfolio optimization

## Configuration

### Trading Parameters

1. **Risk Settings**
   ```yaml
   risk:
     max_position_size: 0.1
     risk_per_trade: 0.01
     max_positions: 5
     max_drawdown: 0.1
   ```

2. **Exchange Settings**
   ```yaml
   exchange:
     name: ftx
     test_mode: false
     rate_limits:
       orders_per_second: 8
   ```

3. **Strategy Settings**
   ```yaml
   strategy:
     name: simple_ma
     params:
       ma_period: 20
       risk_reward: 2.0
   ```

### GUI Customization

1. **Layout**
   - Drag and drop panels
   - Save custom layouts
   - Reset to default
   - Full screen mode

2. **Theme**
   - Light/dark mode
   - Custom colors
   - Font settings
   - Chart styles

3. **Shortcuts**
   ```yaml
   shortcuts:
     cancel_all: Ctrl+Alt+C
     close_all: Ctrl+Alt+X
     save_layout: Ctrl+S
   ```

## Best Practices

### Risk Management

1. **Position Sizing**
   - Never risk more than 1-2% per trade
   - Consider correlation when sizing
   - Account for volatility
   - Use proper stops

2. **Portfolio Management**
   - Diversify across assets
   - Monitor total exposure
   - Regular rebalancing
   - Risk parity approach

3. **Emergency Procedures**
   - Kill switch
   - Emergency contacts
   - Backup procedures
   - Recovery plans

### System Maintenance

1. **Regular Tasks**
   - Update software
   - Backup data
   - Check logs
   - Verify connections

2. **Performance Optimization**
   - Monitor CPU/memory usage
   - Clean old data
   - Optimize database
   - Check network latency

3. **Error Handling**
   - Monitor error logs
   - Set up alerts
   - Document issues
   - Regular testing
