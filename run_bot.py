#!/usr/bin/env python3
"""
Trading Bot Entry Point
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional

from app import __version__
from app.core.logging import TradingBotLogger
from app.core.gui.main_window import MainWindow
from app.core.external.bot_interface import ExternalBotInterface
from PyQt5.QtWidgets import QApplication

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Trading Bot')
    parser.add_argument('--version', action='version',
                       version=f'Trading Bot v{__version__}')
    parser.add_argument('--config', type=str, default='config',
                       help='Path to config directory')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level')
    parser.add_argument('--no-gui', action='store_true',
                       help='Run without GUI')
    return parser.parse_args()

def setup_logging(config_dir: Path, log_level: str) -> TradingBotLogger:
    """Set up logging configuration"""
    config_file = config_dir / 'logging_config.yaml'
    logger = TradingBotLogger(config_file)
    logger.logger.setLevel(getattr(logging, log_level))
    return logger

def run_gui(config_dir: Path) -> Optional[int]:
    """Run the GUI application"""
    app = QApplication(sys.argv)
    window = MainWindow(config_dir)
    window.show()
    return app.exec_()

async def run_headless(config_dir: Path):
    """Run in headless mode"""
    # TODO: Implement headless mode
    pass

def main():
    """Main entry point"""
    # Parse arguments
    args = parse_args()
    config_dir = Path(args.config)
    
    # Setup logging
    logger = setup_logging(config_dir, args.log_level)
    logger.info(f"Starting Trading Bot v{__version__}")
    
    try:
        if args.no_gui:
            # Run in headless mode
            asyncio.run(run_headless(config_dir))
        else:
            # Run GUI
            sys.exit(run_gui(config_dir))
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
