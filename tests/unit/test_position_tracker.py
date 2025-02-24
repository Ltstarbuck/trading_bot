"""
Unit tests for position tracker
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.portfolio.position_tracker import Position, PositionTracker

@pytest.fixture
def position_tracker():
    """Create position tracker instance"""
    return PositionTracker()

@pytest.fixture
def sample_position():
    """Create sample position"""
    return Position(
        symbol="BTC/USD",
        entry_price=Decimal("50000"),
        amount=Decimal("1"),
        side="long",
        stop_loss=Decimal("49000"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance",
        fees=Decimal("10")
    )

def test_position_creation(sample_position):
    """Test position creation"""
    assert sample_position.symbol == "BTC/USD"
    assert sample_position.entry_price == Decimal("50000")
    assert sample_position.amount == Decimal("1")
    assert sample_position.side == "long"
    assert sample_position.stop_loss == Decimal("49000")
    assert sample_position.trailing_stop == Decimal("0.02")
    assert sample_position.exchange_id == "binance"
    assert sample_position.fees == Decimal("10")
    assert sample_position.status == "open"
    assert isinstance(sample_position.entry_time, datetime)
    assert sample_position.exit_time is None

def test_position_update_price(sample_position):
    """Test position price updates"""
    # Test price increase
    stop_triggered = sample_position.update_price(Decimal("51000"))
    assert not stop_triggered
    assert sample_position.current_price == Decimal("51000")
    assert sample_position.highest_price == Decimal("51000")
    assert sample_position.unrealized_pnl == Decimal("990")  # 1000 profit - 10 fees
    
    # Test price decrease
    stop_triggered = sample_position.update_price(Decimal("49500"))
    assert not stop_triggered
    assert sample_position.current_price == Decimal("49500")
    assert sample_position.highest_price == Decimal("51000")
    assert sample_position.unrealized_pnl == Decimal("-510")  # 500 loss - 10 fees
    
    # Test stop loss trigger
    stop_triggered = sample_position.update_price(Decimal("48000"))
    assert stop_triggered

def test_position_close(sample_position):
    """Test position closing"""
    # Close position with profit
    sample_position.close(Decimal("51000"), Decimal("10"))
    assert sample_position.status == "closed"
    assert sample_position.current_price == Decimal("51000")
    assert sample_position.realized_pnl == Decimal("980")  # 1000 profit - 20 fees
    assert isinstance(sample_position.exit_time, datetime)
    
def test_tracker_open_position(position_tracker):
    """Test opening position"""
    position = position_tracker.open_position(
        symbol="ETH/USD",
        entry_price=Decimal("3000"),
        amount=Decimal("2"),
        side="long",
        stop_loss=Decimal("2900"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance",
        fees=Decimal("5")
    )
    
    assert len(position_tracker.positions) == 1
    assert position.symbol == "ETH/USD"
    assert position_tracker.get_position(position.position_id) == position

def test_tracker_close_position(position_tracker):
    """Test closing position"""
    # Open position
    position = position_tracker.open_position(
        symbol="ETH/USD",
        entry_price=Decimal("3000"),
        amount=Decimal("2"),
        side="long",
        stop_loss=Decimal("2900"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance",
        fees=Decimal("5")
    )
    
    # Close position
    closed_position = position_tracker.close_position(
        position.position_id,
        Decimal("3100"),
        Decimal("5")
    )
    
    assert len(position_tracker.positions) == 0
    assert len(position_tracker.closed_positions) == 1
    assert closed_position.realized_pnl == Decimal("190")  # 200 profit - 10 fees

def test_tracker_get_positions(position_tracker):
    """Test getting positions"""
    # Open multiple positions
    position1 = position_tracker.open_position(
        symbol="BTC/USD",
        entry_price=Decimal("50000"),
        amount=Decimal("1"),
        side="long",
        stop_loss=Decimal("49000"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance"
    )
    
    position2 = position_tracker.open_position(
        symbol="ETH/USD",
        entry_price=Decimal("3000"),
        amount=Decimal("2"),
        side="long",
        stop_loss=Decimal("2900"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance"
    )
    
    # Test getting all positions
    all_positions = position_tracker.get_all_positions()
    assert len(all_positions) == 2
    
    # Test getting positions by symbol
    btc_positions = position_tracker.get_positions_by_symbol("BTC/USD")
    assert len(btc_positions) == 1
    assert btc_positions[0].symbol == "BTC/USD"

def test_tracker_pnl_calculation(position_tracker):
    """Test P&L calculations"""
    # Open position
    position = position_tracker.open_position(
        symbol="BTC/USD",
        entry_price=Decimal("50000"),
        amount=Decimal("1"),
        side="long",
        stop_loss=Decimal("49000"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance",
        fees=Decimal("10")
    )
    
    # Update price
    position.update_price(Decimal("51000"))
    
    # Check unrealized P&L
    assert position_tracker.get_total_pnl() == Decimal("990")  # 1000 profit - 10 fees
    
    # Close position
    position_tracker.close_position(
        position.position_id,
        Decimal("51000"),
        Decimal("10")
    )
    
    # Check realized P&L
    assert position_tracker.get_total_pnl() == Decimal("980")  # 1000 profit - 20 fees

def test_tracker_position_value(position_tracker):
    """Test position value calculation"""
    # Open positions
    position_tracker.open_position(
        symbol="BTC/USD",
        entry_price=Decimal("50000"),
        amount=Decimal("1"),
        side="long",
        stop_loss=Decimal("49000"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance"
    )
    
    position_tracker.open_position(
        symbol="ETH/USD",
        entry_price=Decimal("3000"),
        amount=Decimal("2"),
        side="long",
        stop_loss=Decimal("2900"),
        trailing_stop=Decimal("0.02"),
        exchange_id="binance"
    )
    
    # Update prices
    for position in position_tracker.get_all_positions():
        if position.symbol == "BTC/USD":
            position.update_price(Decimal("51000"))
        else:
            position.update_price(Decimal("3100"))
            
    # Check total position value
    expected_value = Decimal("51000") + (Decimal("3100") * Decimal("2"))
    assert position_tracker.get_position_value() == expected_value
