# Trading Bot Configuration Guide

## Overview

The trading bot uses a combination of configuration files and environment variables to manage its settings. This guide explains all available configuration options and their effects on the system.

## Configuration Files

### Directory Structure

```
trading_bot/
├── config/
│   ├── exchange_config.yaml
│   ├── risk_config.yaml
│   ├── gui_config.yaml
│   └── logging_config.yaml
└── .env
```

## Exchange Configuration

Located in `config/exchange_config.yaml`

### Global Settings

```yaml
default_exchange: ftx
order_timeout: 30  # seconds
max_retries: 3
retry_delay: 5  # seconds
```

### Exchange-Specific Settings

```yaml
exchanges:
  ftx:
    # API Configuration
    api_url: https://ftx.com/api
    websocket_url: wss://ftx.com/ws/
    test_mode: false
    
    # Rate Limits
    rate_limits:
      orders_per_second: 8
      orders_per_day: 150000
      requests_per_minute: 1800
    
    # Trading Parameters
    min_order_size: 10.0  # USD
    max_order_size: 750000.0  # USD
    price_precision: 6
    quantity_precision: 8
    
    # Fees
    maker_fee: 0.0002  # 0.02%
    taker_fee: 0.0007  # 0.07%
    
    # Supported Order Types
    order_types:
      - LIMIT
      - MARKET
      - STOP
      - STOP_LIMIT
      - TRAILING_STOP
```

## Risk Management Configuration

Located in `config/risk_config.yaml`

### Position Sizing

```yaml
position_sizing:
  # Maximum position size as percentage of equity
  max_size: 0.1  # 10%
  
  # Risk per trade as percentage of equity
  risk_per_trade: 0.01  # 1%
  
  # Position sizing method
  method: fixed_risk  # Options: fixed_risk, equal_weight, kelly
  
  # Kelly Criterion settings
  kelly:
    fraction: 0.5  # Half-kelly for conservative sizing
    
  # Correlation adjustment
  correlation:
    enabled: true
    max_correlation: 0.7
    lookback_period: 30  # days
```

### Stop Loss

```yaml
stop_loss:
  # Default stop loss percentage
  default_stop: 0.02  # 2%
  
  # Trailing stop settings
  trailing_stop:
    enabled: true
    activation_percent: 0.01  # 1%
    trail_percent: 0.005  # 0.5%
    
  # Break even settings
  break_even:
    enabled: true
    trigger_percent: 0.01  # 1%
    offset: 0.001  # 0.1%
```

### Risk Limits

```yaml
risk_limits:
  # Maximum number of positions
  max_positions: 5
  
  # Maximum drawdown before trading stops
  max_drawdown: 0.1  # 10%
  
  # Daily loss limit
  daily_loss_limit: 0.05  # 5%
  
  # Maximum leverage
  max_leverage: 3
  
  # Exposure limits
  exposure:
    single_asset: 0.2  # 20%
    asset_class: 0.4  # 40%
    total: 0.8  # 80%
```

## GUI Configuration

Located in `config/gui_config.yaml`

### Window Settings

```yaml
window:
  title: "Trading Bot"
  width: 1280
  height: 800
  min_width: 800
  min_height: 600
  background_color: "#1E1E1E"
```

### Theme Settings

```yaml
theme:
  # Color Scheme
  colors:
    primary: "#007ACC"
    secondary: "#569CD6"
    success: "#6A9955"
    warning: "#CE9178"
    error: "#F44747"
    text_primary: "#D4D4D4"
    text_secondary: "#808080"
    
  # Font Settings
  fonts:
    main: "Segoe UI"
    monospace: "Consolas"
    sizes:
      small: 10
      normal: 12
      large: 14
      header: 16
```

### Layout Settings

```yaml
layout:
  # Main Areas
  areas:
    - trading
    - charts
    - orders
    - positions
    - logs
    
  # Default Layout
  default:
    trading:
      position: "left"
      width: 300
    charts:
      position: "center"
      height: "60%"
    orders:
      position: "right"
      width: 300
```

## Logging Configuration

Located in `config/logging_config.yaml`

### Log Levels

```yaml
levels:
  TRACE: 5
  DEBUG: 10
  INFO: 20
  SUCCESS: 25
  WARNING: 30
  ERROR: 40
  CRITICAL: 50
```

### Handlers

```yaml
handlers:
  # Console Handler
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    
  # File Handler
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    filename: logs/trading_bot.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
```

### Performance Logging

```yaml
performance:
  enabled: true
  interval: 60  # seconds
  metrics:
    - cpu_usage
    - memory_usage
    - disk_usage
    - network_io
```

## Environment Variables

Located in `.env`

### API Keys

```env
FTX_API_KEY=your_api_key
FTX_API_SECRET=your_api_secret
FTX_SUBACCOUNT=your_subaccount
```

### Risk Parameters

```env
MAX_POSITION_SIZE=0.1
RISK_PER_TRADE=0.01
MAX_POSITIONS=5
MAX_DRAWDOWN=0.1
```

### System Settings

```env
LOG_LEVEL=INFO
DATA_DIR=data
ENABLE_GPU=true
```

## Configuration Best Practices

### Security

1. **API Keys**
   - Never commit API keys to version control
   - Use environment variables for sensitive data
   - Regularly rotate API keys
   - Use read-only keys when possible

2. **Access Control**
   - Set proper file permissions
   - Use encrypted configuration files
   - Implement role-based access
   - Monitor access logs

### Performance

1. **Rate Limits**
   - Set conservative rate limits
   - Implement request queuing
   - Monitor API usage
   - Handle rate limit errors

2. **Resource Usage**
   - Configure log rotation
   - Set appropriate cache sizes
   - Monitor memory usage
   - Clean old data

### Maintenance

1. **Backups**
   - Regular configuration backups
   - Version control
   - Documentation
   - Recovery procedures

2. **Updates**
   - Regular review of settings
   - Update documentation
   - Test configuration changes
   - Maintain changelog

## Troubleshooting

### Common Issues

1. **Configuration Not Loading**
   - Check file permissions
   - Verify YAML syntax
   - Check file paths
   - Review error logs

2. **Performance Issues**
   - Review log levels
   - Check rate limits
   - Monitor resource usage
   - Optimize settings

3. **Connection Issues**
   - Verify API keys
   - Check network settings
   - Review timeout values
   - Monitor connection logs
