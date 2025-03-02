"""
Trading Bot Application Package
"""

from .core.exchanges import ExchangeFactory
from .core.gui.main_window import MainWindow
from .core.logging import TradingBotLogger
from .core.portfolio import PositionTracker
from .core.risk_management import RiskMonitor, PositionSizer, StopLossManager
from .core.strategies import BaseStrategy, Signal

__version__ = '1.0.0'

__all__ = [
    'ExchangeFactory',
    'MainWindow',
    'TradingBotLogger',
    'PositionTracker',
    'RiskMonitor',
    'PositionSizer',
    'StopLossManager',
    'BaseStrategy',
    'Signal'
]
