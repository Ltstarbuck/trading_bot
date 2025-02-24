"""
Unit tests for position sizing strategies
"""

import pytest
from decimal import Decimal
from app.core.risk_management.position_sizing import PositionSizer

@pytest.fixture
def position_sizer():
    """Create position sizer instance"""
    config = {
        'max_position_size': 0.1,
        'risk_per_trade': 0.01,
        'max_positions': 5
    }
    return PositionSizer(config)

@pytest.fixture
def sample_open_positions():
    """Create sample open positions"""
    return {
        'pos1': type('Position', (), {
            'symbol': 'BTC/USD',
            'current_price': Decimal('50000'),
            'amount': Decimal('0.5')
        }),
        'pos2': type('Position', (), {
            'symbol': 'ETH/USD',
            'current_price': Decimal('3000'),
            'amount': Decimal('5')
        })
    }

def test_sizer_initialization(position_sizer):
    """Test position sizer initialization"""
    assert position_sizer.max_position_size == Decimal('0.1')
    assert position_sizer.risk_per_trade == Decimal('0.01')
    assert position_sizer.max_positions == 5

def test_fixed_risk_position_size(position_sizer):
    """Test fixed risk position sizing"""
    # Test long position
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('50000'),
        stop_loss=Decimal('49000'),
        method='fixed_risk'
    )
    
    # Expected size: (100000 * 0.01) / (50000 - 49000) = 2 BTC
    # But limited by max position size: 100000 * 0.1 / 50000 = 0.2 BTC
    assert size == Decimal('0.2')
    
    # Test short position with different stop
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('50000'),
        stop_loss=Decimal('51000'),
        method='fixed_risk'
    )
    
    assert size == Decimal('0.2')

def test_kelly_position_size(position_sizer):
    """Test Kelly Criterion position sizing"""
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('50000'),
        volatility=Decimal('0.02'),
        method='kelly'
    )
    
    # Should be less than max position size
    assert size <= Decimal('0.2')
    assert size > Decimal('0')
    
    # Test with high volatility
    high_vol_size = position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('50000'),
        volatility=Decimal('0.05'),
        method='kelly'
    )
    
    # Higher volatility should result in smaller position
    assert high_vol_size < size

def test_equal_weight_position_size(position_sizer):
    """Test equal weight position sizing"""
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('50000'),
        method='equal_weight'
    )
    
    # Expected size: (100000 / 5) / 50000 = 0.4
    # But limited by max position size: 100000 * 0.1 / 50000 = 0.2
    assert size == Decimal('0.2')

def test_correlation_adjustment(position_sizer, sample_open_positions):
    """Test correlation-based position adjustment"""
    base_size = Decimal('0.2')
    
    adjusted_size = position_sizer.adjust_for_correlation(
        base_size,
        'BTC/USD',
        sample_open_positions
    )
    
    # Should reduce size due to existing crypto exposure
    assert adjusted_size <= base_size
    
    # Test with different asset
    adjusted_size = position_sizer.adjust_for_correlation(
        base_size,
        'AAPL/USD',  # Stock instead of crypto
        sample_open_positions
    )
    
    # Should maintain size due to different asset class
    assert adjusted_size == base_size

def test_volatility_adjustment(position_sizer):
    """Test volatility-based position adjustment"""
    base_size = Decimal('0.2')
    
    # Test normal volatility
    adjusted_size = position_sizer.adjust_for_volatility(
        base_size,
        volatility=Decimal('0.02'),
        avg_volatility=Decimal('0.02')
    )
    
    assert adjusted_size == base_size
    
    # Test high volatility
    adjusted_size = position_sizer.adjust_for_volatility(
        base_size,
        volatility=Decimal('0.04'),
        avg_volatility=Decimal('0.02')
    )
    
    assert adjusted_size < base_size
    
    # Test low volatility
    adjusted_size = position_sizer.adjust_for_volatility(
        base_size,
        volatility=Decimal('0.01'),
        avg_volatility=Decimal('0.02')
    )
    
    assert adjusted_size > base_size

def test_max_position_size_limit(position_sizer):
    """Test maximum position size limit"""
    # Try to size a very large position
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('1000000'),
        current_price=Decimal('50000'),
        stop_loss=Decimal('49000'),
        method='fixed_risk'
    )
    
    # Should be limited to max size
    assert size == Decimal('0.2')  # 10% of 1M at 50k per BTC

def test_zero_balance_handling(position_sizer):
    """Test handling of zero balance"""
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('0'),
        current_price=Decimal('50000'),
        stop_loss=Decimal('49000'),
        method='fixed_risk'
    )
    
    assert size == Decimal('0')

def test_invalid_method_handling(position_sizer):
    """Test handling of invalid sizing method"""
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('50000'),
        stop_loss=Decimal('49000'),
        method='invalid_method'
    )
    
    # Should default to fixed risk method
    assert size == Decimal('0.2')

def test_zero_price_handling(position_sizer):
    """Test handling of zero price"""
    size = position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('0'),
        stop_loss=Decimal('0'),
        method='fixed_risk'
    )
    
    assert size == Decimal('0')
