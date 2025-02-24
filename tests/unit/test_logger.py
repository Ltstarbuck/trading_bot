"""
Unit tests for the logging system
"""

import os
import pytest
from pathlib import Path
from app.core.logging import TradingBotLogger

@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def log_dir(tmp_path):
    """Create a temporary log directory"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def config_file(config_dir):
    """Create a test logging config file"""
    config_file = config_dir / "logging_config.yaml"
    config_file.write_text("""
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.FileHandler
    level: DEBUG
    formatter: standard
    filename: logs/test.log

loggers:
  '':
    level: INFO
    handlers: [console, file]
    """)
    return config_file

def test_logger_initialization(config_file, log_dir):
    """Test logger initialization"""
    logger = TradingBotLogger(config_file)
    assert logger is not None
    assert os.path.exists(log_dir / "test.log")

def test_logger_levels(config_file, log_dir):
    """Test different logging levels"""
    logger = TradingBotLogger(config_file)
    
    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Check log file contents
    log_file = log_dir / "test.log"
    assert log_file.exists()
    
    log_contents = log_file.read_text()
    assert "Debug message" in log_contents
    assert "Info message" in log_contents
    assert "Warning message" in log_contents
    assert "Error message" in log_contents

def test_logger_with_extra(config_file):
    """Test logging with extra context"""
    logger = TradingBotLogger(config_file)
    
    # Log with extra context
    logger.info("Trade executed", extra={
        "symbol": "BTC/USD",
        "side": "buy",
        "price": 50000,
        "amount": 0.1
    })

def test_logger_file_rotation(config_file, log_dir):
    """Test log file rotation"""
    config_file.write_text("""
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

handlers:
  rotating_file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: standard
    filename: logs/test.log
    maxBytes: 1024
    backupCount: 3

loggers:
  '':
    level: DEBUG
    handlers: [rotating_file]
    """)
    
    logger = TradingBotLogger(config_file)
    
    # Generate enough logs to trigger rotation
    for i in range(1000):
        logger.debug(f"Test message {i}" * 10)
    
    # Check rotated files exist
    assert (log_dir / "test.log").exists()
    assert (log_dir / "test.log.1").exists()
    assert (log_dir / "test.log.2").exists()
    assert (log_dir / "test.log.3").exists()

def test_logger_error_handling(config_file):
    """Test logger error handling"""
    # Test with invalid config
    invalid_config = config_file.parent / "invalid.yaml"
    invalid_config.write_text("invalid: yaml: content")
    
    with pytest.raises(Exception):
        TradingBotLogger(invalid_config)
    
    # Test with non-existent config
    with pytest.raises(FileNotFoundError):
        TradingBotLogger(Path("non_existent.yaml"))

def test_logger_trading_context(config_file):
    """Test logging in trading context"""
    logger = TradingBotLogger(config_file)
    
    # Log various trading events
    logger.info("Strategy signal generated", extra={
        "strategy": "MA_Cross",
        "signal": "BUY",
        "symbol": "BTC/USD"
    })
    
    logger.warning("Position size limit reached", extra={
        "symbol": "BTC/USD",
        "current_size": 0.5,
        "max_size": 0.4
    })
    
    logger.error("Order execution failed", extra={
        "symbol": "BTC/USD",
        "order_type": "LIMIT",
        "error": "Insufficient funds"
    })
