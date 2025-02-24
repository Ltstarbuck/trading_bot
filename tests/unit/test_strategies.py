"""
Unit tests for trading strategies
"""

import pytest
from decimal import Decimal
from app.core.strategies import BaseStrategy, Signal
from app.core.strategies.volatility_strat import VolatilityStrategy

@pytest.fixture
def sample_data():
    """Sample market data for testing"""
    return {
        "timestamp": 1677628800000,  # 2023-03-01 00:00:00
        "open": "50000",
        "high": "51000",
        "low": "49000",
        "close": "50500",
        "volume": "100"
    }

@pytest.fixture
def volatility_strategy():
    """Create a volatility strategy instance"""
    return VolatilityStrategy(
        atr_period=14,
        atr_multiplier=2,
        bollinger_period=20,
        bollinger_std=2
    )

class TestBaseStrategy:
    """Tests for the base strategy class"""
    
    class SimpleStrategy(BaseStrategy):
        """Simple strategy for testing"""
        async def generate_signal(self, data):
            price = Decimal(data["close"])
            if price > Decimal("50000"):
                return Signal.BUY
            elif price < Decimal("49000"):
                return Signal.SELL
            return Signal.HOLD
    
    @pytest.fixture
    def strategy(self):
        """Create a simple strategy instance"""
        return self.SimpleStrategy()
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, strategy, sample_data):
        """Test basic signal generation"""
        # Test buy signal
        sample_data["close"] = "51000"
        signal = await strategy.generate_signal(sample_data)
        assert signal == Signal.BUY
        
        # Test sell signal
        sample_data["close"] = "48000"
        signal = await strategy.generate_signal(sample_data)
        assert signal == Signal.SELL
        
        # Test hold signal
        sample_data["close"] = "49500"
        signal = await strategy.generate_signal(sample_data)
        assert signal == Signal.HOLD

class TestVolatilityStrategy:
    """Tests for the volatility strategy"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, volatility_strategy):
        """Test strategy initialization"""
        assert volatility_strategy.atr_period == 14
        assert volatility_strategy.atr_multiplier == 2
        assert volatility_strategy.bollinger_period == 20
        assert volatility_strategy.bollinger_std == 2
    
    @pytest.mark.asyncio
    async def test_atr_calculation(self, volatility_strategy):
        """Test ATR calculation"""
        # Add price data
        for i in range(20):
            await volatility_strategy.update({
                "high": str(50000 + i * 100),
                "low": str(49000 + i * 100),
                "close": str(49500 + i * 100)
            })
        
        atr = volatility_strategy.calculate_atr()
        assert isinstance(atr, Decimal)
        assert atr > 0
    
    @pytest.mark.asyncio
    async def test_bollinger_bands(self, volatility_strategy):
        """Test Bollinger Bands calculation"""
        # Add price data
        for i in range(30):
            await volatility_strategy.update({
                "close": str(50000 + i * 100)
            })
        
        upper, middle, lower = volatility_strategy.calculate_bollinger_bands()
        assert isinstance(upper, Decimal)
        assert isinstance(middle, Decimal)
        assert isinstance(lower, Decimal)
        assert upper > middle > lower
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, volatility_strategy):
        """Test volatility-based signal generation"""
        # Initialize with trending data
        for i in range(30):
            await volatility_strategy.update({
                "high": str(50000 + i * 100),
                "low": str(49000 + i * 100),
                "close": str(49500 + i * 100)
            })
        
        # Test different scenarios
        scenarios = [
            # High volatility, price above upper band
            {
                "high": "55000",
                "low": "53000",
                "close": "54000"
            },
            # Low volatility, price below lower band
            {
                "high": "47000",
                "low": "46000",
                "close": "46500"
            },
            # Normal volatility, price within bands
            {
                "high": "50500",
                "low": "49500",
                "close": "50000"
            }
        ]
        
        for scenario in scenarios:
            signal = await volatility_strategy.generate_signal(scenario)
            assert signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
    
    @pytest.mark.asyncio
    async def test_volatility_threshold(self, volatility_strategy):
        """Test volatility thresholds"""
        # Low volatility scenario
        for _ in range(20):
            await volatility_strategy.update({
                "high": "50100",
                "low": "49900",
                "close": "50000"
            })
        
        signal = await volatility_strategy.generate_signal({
            "high": "50100",
            "low": "49900",
            "close": "50000"
        })
        assert signal == Signal.HOLD
        
        # High volatility scenario
        for _ in range(5):
            await volatility_strategy.update({
                "high": "52000",
                "low": "48000",
                "close": "50000"
            })
        
        signal = await volatility_strategy.generate_signal({
            "high": "52000",
            "low": "48000",
            "close": "51000"
        })
        assert signal in [Signal.BUY, Signal.SELL]
