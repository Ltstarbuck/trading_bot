"""
Logging system for the trading bot
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler
import yaml

class TradingBotLogger:
    """Custom logger for the trading bot"""
    
    def __init__(self, config_path: str):
        """Initialize logger with configuration"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        
    def _load_config(self, config_path: str) -> dict:
        """Load logging configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading logging config: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> dict:
        """Get default logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'detailed': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': 'logs/trading_bot.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                },
                'error_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                    'filename': 'logs/error.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                }
            },
            'loggers': {
                'trading_bot': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file', 'error_file'],
                    'propagate': False
                }
            }
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logger with handlers"""
        # Create logger
        logger = logging.getLogger('trading_bot')
        logger.setLevel(logging.DEBUG)
        
        # Create log directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Add handlers
        self._add_console_handler(logger)
        self._add_file_handler(logger)
        self._add_error_handler(logger)
        
        return logger
        
    def _add_console_handler(self,
                           logger: logging.Logger):
        """Add console handler to logger"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    def _add_file_handler(self,
                         logger: logging.Logger):
        """Add file handler to logger"""
        handler = RotatingFileHandler(
            'logs/trading_bot.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    def _add_error_handler(self,
                          logger: logging.Logger):
        """Add error file handler to logger"""
        handler = RotatingFileHandler(
            'logs/error.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    def debug(self, message: str,
              *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)
        
    def info(self, message: str,
             *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)
        
    def warning(self, message: str,
                *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)
        
    def error(self, message: str,
              *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)
        
    def critical(self, message: str,
                 *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)
        
    def exception(self, message: str,
                  *args, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)
        
class TradeLogger:
    """Logger specifically for trade-related events"""
    
    def __init__(self, logger: TradingBotLogger):
        """Initialize trade logger"""
        self.logger = logger
        
    def log_order_created(self, order: dict):
        """Log order creation"""
        self.logger.info(
            f"Order created: {order['id']} "
            f"({order['symbol']} {order['side']} "
            f"{order['amount']} @ {order.get('price', 'MARKET')})")
            
    def log_order_filled(self, order: dict):
        """Log order fill"""
        self.logger.info(
            f"Order filled: {order['id']} "
            f"({order['symbol']} {order['side']} "
            f"{order['amount']} @ {order['price']})")
            
    def log_order_cancelled(self, order: dict):
        """Log order cancellation"""
        self.logger.info(
            f"Order cancelled: {order['id']}")
            
    def log_position_opened(self, position: dict):
        """Log position opening"""
        self.logger.info(
            f"Position opened: {position['symbol']} "
            f"{position['side']} {position['size']} "
            f"@ {position['entry_price']}")
            
    def log_position_closed(self, position: dict):
        """Log position closing"""
        self.logger.info(
            f"Position closed: {position['symbol']} "
            f"P&L: ${position['realized_pnl']:.2f}")
            
    def log_stop_loss_hit(self, position: dict):
        """Log stop loss trigger"""
        self.logger.warning(
            f"Stop loss hit: {position['symbol']} "
            f"P&L: ${position['realized_pnl']:.2f}")
            
    def log_take_profit_hit(self, position: dict):
        """Log take profit trigger"""
        self.logger.info(
            f"Take profit hit: {position['symbol']} "
            f"P&L: ${position['realized_pnl']:.2f}")
            
class RiskLogger:
    """Logger specifically for risk-related events"""
    
    def __init__(self, logger: TradingBotLogger):
        """Initialize risk logger"""
        self.logger = logger
        
    def log_risk_limit_exceeded(self,
                               limit_type: str,
                               current: float,
                               max_allowed: float):
        """Log risk limit violation"""
        self.logger.warning(
            f"Risk limit exceeded: {limit_type} "
            f"(Current: {current:.2f}, Max: {max_allowed:.2f})")
            
    def log_drawdown_warning(self,
                            drawdown: float,
                            threshold: float):
        """Log drawdown warning"""
        self.logger.warning(
            f"Drawdown warning: {drawdown:.2f}% "
            f"(Threshold: {threshold:.2f}%)")
            
    def log_exposure_warning(self,
                            symbol: str,
                            exposure: float,
                            limit: float):
        """Log exposure warning"""
        self.logger.warning(
            f"High exposure warning: {symbol} "
            f"(Current: {exposure:.2f}%, Limit: {limit:.2f}%)")
            
    def log_correlation_warning(self,
                               symbols: list,
                               correlation: float,
                               threshold: float):
        """Log correlation warning"""
        self.logger.warning(
            f"High correlation warning: {symbols} "
            f"(Correlation: {correlation:.2f}, "
            f"Threshold: {threshold:.2f})")
            
class PerformanceLogger:
    """Logger specifically for performance metrics"""
    
    def __init__(self, logger: TradingBotLogger):
        """Initialize performance logger"""
        self.logger = logger
        
    def log_latency(self,
                    operation: str,
                    latency_ms: float):
        """Log operation latency"""
        self.logger.debug(
            f"Latency - {operation}: {latency_ms:.2f}ms")
            
    def log_memory_usage(self,
                         usage_mb: float):
        """Log memory usage"""
        self.logger.debug(
            f"Memory usage: {usage_mb:.2f}MB")
            
    def log_cpu_usage(self,
                      usage_percent: float):
        """Log CPU usage"""
        self.logger.debug(
            f"CPU usage: {usage_percent:.2f}%")
            
    def log_api_usage(self,
                      endpoint: str,
                      calls: int,
                      limit: int):
        """Log API usage"""
        self.logger.debug(
            f"API usage - {endpoint}: "
            f"{calls}/{limit} calls")
