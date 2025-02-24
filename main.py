#!/usr/bin/env python3
"""
Trading Bot Entry Point
Initializes and runs the main application
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger
from PyQt5.QtWidgets import QApplication

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.gui.main_window import MainWindow
from app.config import ConfigManager
from app.core.exchanges.exchange_factory import ExchangeFactory
from app.core.portfolio.position_tracker import PositionTracker

def setup_logging():
    """Configure logging for the application"""
    log_path = project_root / "logs"
    log_path.mkdir(exist_ok=True)
    
    # Configure loguru logger
    logger.add(
        log_path / "live_trades/{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="INFO",
        filter=lambda record: "live_trade" in record["extra"]
    )
    logger.add(
        log_path / "paper_trades/{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="INFO",
        filter=lambda record: "paper_trade" in record["extra"]
    )
    logger.add(
        log_path / "debug.log",
        rotation="100 MB",
        retention="10 days",
        level="DEBUG"
    )

def main():
    """Main entry point for the trading bot"""
    # Setup logging
    setup_logging()
    logger.info("Starting trading bot...")

    # Initialize configuration
    config = ConfigManager()
    
    # Initialize Qt application
    app = QApplication(sys.argv)
    
    # Create main components
    exchange_factory = ExchangeFactory()
    position_tracker = PositionTracker()
    
    # Create and show main window
    main_window = MainWindow(config, exchange_factory, position_tracker)
    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
