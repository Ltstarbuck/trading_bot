"""
Logging utilities
"""

import sys
from typing import Optional
from pathlib import Path
import logging
from loguru import logger

def setup_logging(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    rotation: str = "1 day",
    retention: str = "1 week"
) -> None:
    """
    Configure logging
    
    Args:
        log_file: Optional log file path
        log_level: Logging level
        rotation: Log rotation interval
        retention: Log retention period
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(log_path),
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )

class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages toward loguru
    This allows existing libraries to work with loguru
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Intercept log record
        
        Args:
            record: Log record
        """
        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
            
        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
            
        logger.opt(
            depth=depth,
            exception=record.exc_info
        ).log(level, record.getMessage())

def setup_library_logging():
    """Configure standard library logging to use loguru"""
    # Remove existing handlers
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Update handler for commonly used libraries
    for name in [
        "asyncio",
        "urllib3",
        "websockets",
        "ccxt",
        "requests"
    ]:
        logging.getLogger(name).handlers = [InterceptHandler()]
