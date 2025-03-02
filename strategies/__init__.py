"""
Trading strategies and algorithms
"""

from .base_strategy import BaseStrategy, Signal
from .volatility_strat import VolatilityStrategy

__all__ = [
    'BaseStrategy',
    'Signal',
    'VolatilityStrategy'
]
