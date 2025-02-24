"""
Unit tests for liquidity monitoring system
"""

import pytest
from decimal import Decimal
from datetime import datetime
from app.core.risk_management.liquidity_monitor import LiquidityMonitor

@pytest.fixture
def liquidity_monitor():
    """Create liquidity monitor instance"""
    config = {
        'min_liquidity_ratio': 3.0,
        'max_slippage': 0.01,
        'volume_window': 24,
        'liquidity_threshold': 1000.0
    }
    return LiquidityMonitor(config)

@pytest.fixture
def sample_orderbook():
    """Create sample orderbook data"""
    return {
        'bids': [
            [Decimal('50000'), Decimal('1.0')],
            [Decimal('49900'), Decimal('2.0')],
            [Decimal('49800'), Decimal('3.0')]
        ],
        'asks': [
            [Decimal('50100'), Decimal('1.5')],
            [Decimal('50200'), Decimal('2.5')],
            [Decimal('50300'), Decimal('3.5')]
        ]
    }

def test_monitor_initialization(liquidity_monitor):
    """Test monitor initialization"""
    assert liquidity_monitor.min_liquidity_ratio == Decimal('3.0')
    assert liquidity_monitor.max_slippage == Decimal('0.01')
    assert liquidity_monitor.volume_window == 24
    assert liquidity_monitor.liquidity_threshold == Decimal('1000.0')

def test_check_liquidity(liquidity_monitor, sample_orderbook):
    """Test liquidity check"""
    # Test with small order
    result = liquidity_monitor.check_liquidity(
        'BTC/USD',
        Decimal('0.5'),
        sample_orderbook,
        Decimal('100')
    )
    
    assert result['is_liquid'] is True
    assert 'spread' in result
    assert 'depth' in result
    assert 'volume_ratio' in result
    assert 'estimated_slippage' in result
    assert 'timestamp' in result
    
    # Test with large order
    result = liquidity_monitor.check_liquidity(
        'BTC/USD',
        Decimal('5.0'),
        sample_orderbook,
        Decimal('100')
    )
    
    assert result['is_liquid'] is False

def test_optimal_order_size(liquidity_monitor, sample_orderbook):
    """Test optimal order size calculation"""
    # Test with normal conditions
    optimal_size = liquidity_monitor.get_optimal_order_size(
        'BTC/USD',
        Decimal('1.0'),
        sample_orderbook,
        Decimal('100')
    )
    
    assert optimal_size <= Decimal('1.0')
    assert optimal_size > Decimal('0')
    
    # Test with low liquidity
    optimal_size = liquidity_monitor.get_optimal_order_size(
        'BTC/USD',
        Decimal('10.0'),
        sample_orderbook,
        Decimal('50')
    )
    
    assert optimal_size < Decimal('10.0')

def test_order_splitting(liquidity_monitor, sample_orderbook):
    """Test order splitting logic"""
    # Test small order (shouldn't split)
    splits = liquidity_monitor.should_split_order(
        Decimal('0.5'),
        sample_orderbook,
        Decimal('100')
    )
    
    assert splits is None
    
    # Test large order (should split)
    splits = liquidity_monitor.should_split_order(
        Decimal('5.0'),
        sample_orderbook,
        Decimal('100')
    )
    
    assert splits is not None
    assert len(splits) > 1
    assert sum(splits) == Decimal('5.0')

def test_spread_calculation(liquidity_monitor, sample_orderbook):
    """Test spread calculation"""
    spread = liquidity_monitor._calculate_spread(sample_orderbook)
    
    # Expected spread: (50100 - 50000) / 50050 ≈ 0.002
    assert Decimal('0.001') < spread < Decimal('0.003')
    
    # Test with empty orderbook
    empty_orderbook = {'bids': [], 'asks': []}
    spread = liquidity_monitor._calculate_spread(empty_orderbook)
    assert spread == Decimal('999')

def test_depth_calculation(liquidity_monitor, sample_orderbook):
    """Test market depth calculation"""
    depth = liquidity_monitor._calculate_depth(
        sample_orderbook,
        Decimal('1.0')
    )
    
    # Should have sufficient depth for 1.0 BTC
    assert depth >= liquidity_monitor.min_liquidity_ratio
    
    # Test with large order
    depth = liquidity_monitor._calculate_depth(
        sample_orderbook,
        Decimal('10.0')
    )
    
    # Should have insufficient depth
    assert depth < liquidity_monitor.min_liquidity_ratio

def test_slippage_estimation(liquidity_monitor, sample_orderbook):
    """Test slippage estimation"""
    # Test small order
    slippage = liquidity_monitor._estimate_slippage(
        Decimal('0.5'),
        sample_orderbook
    )
    
    assert slippage < liquidity_monitor.max_slippage
    
    # Test large order
    slippage = liquidity_monitor._estimate_slippage(
        Decimal('5.0'),
        sample_orderbook
    )
    
    assert slippage > liquidity_monitor.max_slippage

def test_volume_ratio(liquidity_monitor):
    """Test volume ratio calculation"""
    ratio = liquidity_monitor._calculate_volume_ratio(
        Decimal('10'),
        Decimal('1000')
    )
    
    assert ratio == Decimal('0.01')
    
    # Test with zero volume
    ratio = liquidity_monitor._calculate_volume_ratio(
        Decimal('10'),
        Decimal('0')
    )
    
    assert ratio == Decimal('999')

def test_liquidity_cache(liquidity_monitor):
    """Test liquidity cache functionality"""
    symbol = 'BTC/USD'
    spread = Decimal('0.001')
    depth = Decimal('5.0')
    volume_ratio = Decimal('0.01')
    
    # Update cache
    liquidity_monitor.update_liquidity_cache(
        symbol,
        spread,
        depth,
        volume_ratio
    )
    
    # Check cache contents
    cache = liquidity_monitor.liquidity_cache[symbol]
    assert cache['spread'] == spread
    assert cache['depth'] == depth
    assert cache['volume_ratio'] == volume_ratio
    assert isinstance(cache['timestamp'], datetime)
