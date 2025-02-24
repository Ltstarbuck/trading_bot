"""
Unit tests for stop loss management
"""

import pytest
from decimal import Decimal
from app.core.risk_management.stop_loss import StopLossManager

@pytest.fixture
def stop_loss_manager():
    """Create stop loss manager instance"""
    config = {
        'stop_loss_percent': 0.02,
        'trailing_stop_percent': 0.01,
        'atr_multiplier': 2.0,
        'break_even_trigger': 0.01
    }
    return StopLossManager(config)

@pytest.fixture
def sample_position():
    """Create sample position data"""
    return {
        'entry_price': Decimal('50000'),
        'stop_loss': Decimal('49000'),
        'side': 'long',
        'symbol': 'BTC/USD'
    }

def test_manager_initialization(stop_loss_manager):
    """Test manager initialization"""
    assert stop_loss_manager.default_stop_loss == Decimal('0.02')
    assert stop_loss_manager.trailing_stop == Decimal('0.01')
    assert stop_loss_manager.atr_multiplier == Decimal('2.0')
    assert stop_loss_manager.break_even_trigger == Decimal('0.01')

def test_fixed_stop_loss(stop_loss_manager):
    """Test fixed percentage stop loss"""
    # Test long position
    stop_price = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('50000'),
        side='long',
        method='fixed'
    )
    
    # Expected: 50000 * (1 - 0.02) = 49000
    assert stop_price == Decimal('49000')
    
    # Test short position
    stop_price = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('50000'),
        side='short',
        method='fixed'
    )
    
    # Expected: 50000 * (1 + 0.02) = 51000
    assert stop_price == Decimal('51000')

def test_atr_based_stop(stop_loss_manager):
    """Test ATR-based stop loss"""
    atr = Decimal('1000')  # $1000 ATR
    
    # Test long position
    stop_price = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('50000'),
        side='long',
        volatility=atr,
        method='atr'
    )
    
    # Expected: 50000 - (1000 * 2) = 48000
    assert stop_price == Decimal('48000')
    
    # Test with no ATR provided
    stop_price = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('50000'),
        side='long',
        volatility=None,
        method='atr'
    )
    
    # Should default to fixed percentage
    assert stop_price == Decimal('49000')

def test_volatility_based_stop(stop_loss_manager):
    """Test volatility-based stop loss"""
    volatility = Decimal('0.02')  # 2% volatility
    
    # Test long position
    stop_price = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('50000'),
        side='long',
        volatility=volatility,
        method='volatility'
    )
    
    # Expected: 50000 - (50000 * 0.02) = 49000
    assert stop_price == Decimal('49000')
    
    # Test with high volatility
    high_vol_stop = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('50000'),
        side='long',
        volatility=Decimal('0.04'),
        method='volatility'
    )
    
    # Higher volatility should result in wider stop
    assert high_vol_stop < stop_price

def test_trailing_stop_update(stop_loss_manager, sample_position):
    """Test trailing stop updates"""
    # Test long position profit
    new_stop = stop_loss_manager.update_trailing_stop(
        sample_position,
        Decimal('51000')  # Price moved up
    )
    
    # Should move stop up: 51000 * (1 - 0.01) = 50490
    assert new_stop > sample_position['stop_loss']
    assert new_stop == Decimal('50490')
    
    # Test price move down
    new_stop = stop_loss_manager.update_trailing_stop(
        sample_position,
        Decimal('49500')  # Price moved down
    )
    
    # Should keep original stop
    assert new_stop == sample_position['stop_loss']

def test_break_even_adjustment(stop_loss_manager, sample_position):
    """Test break even stop adjustment"""
    # Test insufficient profit
    new_stop = stop_loss_manager.adjust_for_break_even(
        sample_position,
        Decimal('50400')  # 0.8% profit
    )
    
    assert new_stop is None
    
    # Test sufficient profit
    new_stop = stop_loss_manager.adjust_for_break_even(
        sample_position,
        Decimal('50600')  # 1.2% profit
    )
    
    assert new_stop == sample_position['entry_price']

def test_stop_loss_check(stop_loss_manager, sample_position):
    """Test stop loss check"""
    # Test stop not hit
    assert not stop_loss_manager.check_stop_loss(
        sample_position,
        Decimal('49100')
    )
    
    # Test stop hit
    assert stop_loss_manager.check_stop_loss(
        sample_position,
        Decimal('48900')
    )
    
    # Test short position
    short_position = dict(sample_position)
    short_position['side'] = 'short'
    short_position['stop_loss'] = Decimal('51000')
    
    assert stop_loss_manager.check_stop_loss(
        short_position,
        Decimal('51100')
    )

def test_risk_reward_ratio(stop_loss_manager):
    """Test risk/reward ratio calculation"""
    ratio = stop_loss_manager.get_risk_reward_ratio(
        entry_price=Decimal('50000'),
        stop_loss=Decimal('49000'),
        take_profit=Decimal('53000'),
        side='long'
    )
    
    # Expected: (53000 - 50000) / (50000 - 49000) = 3.0
    assert ratio == Decimal('3')
    
    # Test short position
    ratio = stop_loss_manager.get_risk_reward_ratio(
        entry_price=Decimal('50000'),
        stop_loss=Decimal('51000'),
        take_profit=Decimal('47000'),
        side='short'
    )
    
    # Expected: (50000 - 47000) / (51000 - 50000) = 3.0
    assert ratio == Decimal('3')

def test_invalid_method_handling(stop_loss_manager):
    """Test handling of invalid stop loss method"""
    stop_price = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('50000'),
        side='long',
        method='invalid_method'
    )
    
    # Should default to fixed percentage
    assert stop_price == Decimal('49000')

def test_zero_price_handling(stop_loss_manager):
    """Test handling of zero price"""
    stop_price = stop_loss_manager.calculate_initial_stop(
        entry_price=Decimal('0'),
        side='long',
        method='fixed'
    )
    
    assert stop_price == Decimal('0')
