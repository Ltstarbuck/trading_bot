# Trading Bot API Documentation

## Core Components

### TradingBot

The main trading bot class that orchestrates all trading operations.

```python
class TradingBot:
    def __init__(self, config: Dict)
    async def start() -> None
    async def stop() -> None
    async def create_order(symbol: str, side: str, type: str, amount: Decimal,
                          price: Optional[Decimal] = None) -> Dict
    async def cancel_order(order_id: str) -> Dict
    async def get_positions() -> List[Dict]
    async def close_position(position_id: str) -> Dict
```

### Exchange Interface

Base interface for cryptocurrency exchanges.

```python
class BaseExchange:
    async def get_ticker(symbol: str) -> Dict
    async def get_orderbook(symbol: str, depth: int = 20) -> Dict
    async def get_recent_trades(symbol: str, limit: int = 100) -> List[Dict]
    async def get_candles(symbol: str, timeframe: str, limit: int = 100) -> List[Dict]
    async def get_balance(currency: Optional[str] = None) -> Dict
    async def get_positions() -> List[Dict]
    async def create_order(symbol: str, side: str, order_type: str,
                          amount: Decimal, price: Optional[Decimal] = None) -> Dict
    async def cancel_order(order_id: str) -> Dict
    async def get_order(order_id: str) -> Dict
```

### Risk Management

#### Risk Monitor

Monitors and enforces risk limits.

```python
class RiskMonitor:
    def update_portfolio_state(current_equity: Decimal, positions: Dict,
                             account_balance: Decimal) -> None
    def check_max_drawdown() -> bool
    def check_daily_loss() -> bool
    def check_position_limits() -> bool
    def check_leverage_limits() -> bool
```

#### Position Sizer

Calculates position sizes based on risk parameters.

```python
class PositionSizer:
    def calculate_position_size(available_balance: Decimal,
                              current_price: Decimal,
                              stop_loss: Optional[Decimal] = None,
                              method: str = 'fixed_risk') -> Decimal
    def adjust_for_correlation(base_size: Decimal, symbol: str,
                             open_positions: Dict) -> Decimal
    def adjust_for_volatility(base_size: Decimal, volatility: Decimal,
                            avg_volatility: Decimal) -> Decimal
```

#### Stop Loss Manager

Manages stop loss orders and trailing stops.

```python
class StopLossManager:
    def calculate_initial_stop(entry_price: Decimal, side: str,
                             method: str = 'fixed') -> Decimal
    def update_trailing_stop(position: Dict, current_price: Decimal) -> Optional[Decimal]
    def adjust_for_break_even(position: Dict,
                            current_price: Decimal) -> Optional[Decimal]
    def check_stop_loss(position: Dict, current_price: Decimal) -> bool
```

### Portfolio Management

#### Position Tracker

Tracks open positions and calculates P&L.

```python
class PositionTracker:
    def add_position(position_id: str, symbol: str, side: str,
                    amount: Decimal, entry_price: Decimal) -> None
    def remove_position(position_id: str) -> None
    def update_position_price(position_id: str,
                            current_price: Decimal) -> None
    def get_positions() -> List[Dict]
    def get_total_exposure() -> Decimal
    def get_total_pnl() -> Decimal
```

### External Bot Interface

Interface for external trading bots and signals.

```python
class ExternalBotInterface:
    async def start() -> None
    async def stop() -> None
    async def connect_bot(bot_id: str, connection_details: Dict) -> bool
    async def disconnect_bot(bot_id: str) -> None
    def add_recommendation(recommendation: BotRecommendation) -> None
    def get_recommendations(symbol: Optional[str] = None,
                          source: Optional[str] = None,
                          min_confidence: float = 0.0) -> List[BotRecommendation]
```

## GUI Components

### Main Window

Main application window.

```python
class MainWindow:
    def __init__()
    def save_layout() -> None
    def load_layout() -> None
    def switch_theme(theme: str) -> None
    async def process_ticker_update(data: Dict) -> None
    async def process_orderbook_update(data: Dict) -> None
    async def process_trade_update(data: Dict) -> None
```

### Trading Panel

Panel for creating and managing orders.

```python
class TradingPanel:
    def __init__()
    def set_symbol(symbol: str) -> None
    def get_order_details() -> Dict
    def clear_inputs() -> None
```

### Chart Widget

Displays price charts and technical indicators.

```python
class ChartWidget:
    def __init__()
    def set_symbol(symbol: str) -> None
    def set_timeframe(timeframe: str) -> None
    def update_data(candles: List[Dict]) -> None
    def add_indicator(name: str, params: Dict) -> None
```

## Configuration

### Exchange Configuration

```yaml
exchanges:
  ftx:
    api_url: str
    websocket_url: str
    rate_limits:
      requests_per_minute: int
      orders_per_second: int
      orders_per_day: int
    trading_params:
      min_order_size: float
      max_order_size: float
      price_precision: int
      quantity_precision: int
```

### Risk Configuration

```yaml
risk:
  max_position_size: float
  risk_per_trade: float
  max_positions: int
  max_drawdown: float
  daily_loss_limit: float
  leverage_limit: float
```

### GUI Configuration

```yaml
gui:
  window:
    title: str
    width: int
    height: int
  theme:
    colors: Dict[str, str]
    fonts: Dict[str, str]
  layout:
    areas: List[str]
    default: Dict[str, Dict]
```

## Event System

### Trading Events

```python
class OrderCreated:
    order_id: str
    symbol: str
    side: str
    type: str
    amount: Decimal
    price: Optional[Decimal]

class OrderFilled:
    order_id: str
    symbol: str
    amount: Decimal
    price: Decimal
    timestamp: datetime

class PositionOpened:
    position_id: str
    symbol: str
    side: str
    amount: Decimal
    entry_price: Decimal

class PositionClosed:
    position_id: str
    symbol: str
    amount: Decimal
    exit_price: Decimal
    pnl: Decimal
```

### Risk Events

```python
class RiskLimitBreached:
    limit_type: str
    current_value: float
    threshold: float
    timestamp: datetime

class StopLossTriggered:
    position_id: str
    symbol: str
    stop_price: Decimal
    timestamp: datetime
```

## Error Handling

### Trading Errors

```python
class InsufficientFunds(Exception):
    pass

class InvalidOrder(Exception):
    pass

class ExchangeError(Exception):
    pass

class RiskLimitError(Exception):
    pass
```

## Utilities

### Data Types

```python
class Candle:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

class OrderBook:
    bids: List[Tuple[Decimal, Decimal]]
    asks: List[Tuple[Decimal, Decimal]]

class Trade:
    id: str
    symbol: str
    side: str
    amount: Decimal
    price: Decimal
    timestamp: datetime
```

### Helper Functions

```python
def calculate_position_value(amount: Decimal, price: Decimal) -> Decimal
def calculate_pnl(entry_price: Decimal, exit_price: Decimal,
                 amount: Decimal, side: str) -> Decimal
def calculate_drawdown(equity_curve: List[Decimal]) -> Tuple[Decimal, Decimal]
def estimate_slippage(order_size: Decimal, orderbook: OrderBook) -> Decimal
```
