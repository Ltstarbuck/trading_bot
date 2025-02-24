"""
Integration tests for trading flow
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import MagicMock, patch
from app.core.trading_bot import TradingBot
from app.core.exchanges.ftx import FTXExchange
from app.core.risk_management.risk_monitor import RiskMonitor
from app.core.risk_management.position_sizing import PositionSizer
from app.core.risk_management.stop_loss import StopLossManager
from app.core.portfolio.position_tracker import PositionTracker

@pytest.fixture
def config():
    """Create test configuration"""
    return {
        'exchange': {
            'name': 'ftx',
            'api_url': 'https://ftx.com/api',
            'websocket_url': 'wss://ftx.com/ws/',
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'rate_limits': {
                'requests_per_minute': 1800,
                'orders_per_second': 8,
                'orders_per_day': 150000
            }
        },
        'risk': {
            'max_position_size': 0.1,
            'risk_per_trade': 0.01,
            'max_positions': 5,
            'max_drawdown': 0.1,
            'daily_loss_limit': 0.05
        },
        'trading': {
            'symbols': ['BTC/USD', 'ETH/USD'],
            'timeframes': ['1m', '5m', '1h'],
            'default_amount': 0.01
        }
    }

@pytest.fixture
def trading_bot(config):
    """Create trading bot instance"""
    return TradingBot(config)

@pytest.mark.asyncio
async def test_full_trading_cycle(trading_bot):
    """Test complete trading cycle"""
    # Mock exchange responses
    mock_ticker = {
        'name': 'BTC/USD',
        'last': 50000,
        'bid': 49990,
        'ask': 50010,
        'volume': 1000
    }
    
    mock_balance = [
        {'coin': 'USD', 'free': 100000, 'total': 100000},
        {'coin': 'BTC', 'free': 1.0, 'total': 1.0}
    ]
    
    mock_order = {
        'id': '1234',
        'market': 'BTC/USD',
        'side': 'buy',
        'size': 0.1,
        'price': 50000,
        'status': 'closed'
    }
    
    # Patch exchange methods
    with patch.object(trading_bot.exchange, 'get_ticker',
                     return_value=mock_ticker), \
         patch.object(trading_bot.exchange, 'get_balance',
                     return_value=mock_balance), \
         patch.object(trading_bot.exchange, 'create_order',
                     return_value=mock_order), \
         patch.object(trading_bot.exchange, 'get_order',
                     return_value=mock_order):
        
        # Start trading bot
        await trading_bot.start()
        
        # Create and execute trade
        trade_params = {
            'symbol': 'BTC/USD',
            'side': 'buy',
            'type': 'limit',
            'amount': Decimal('0.1'),
            'price': Decimal('50000')
        }
        
        order = await trading_bot.create_order(**trade_params)
        
        # Verify order creation
        assert order['id'] == '1234'
        assert order['market'] == 'BTC/USD'
        assert order['side'] == 'buy'
        
        # Check position tracking
        positions = trading_bot.position_tracker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == 'BTC/USD'
        assert positions[0].amount == Decimal('0.1')
        
        # Stop trading bot
        await trading_bot.stop()

@pytest.mark.asyncio
async def test_risk_management_integration(trading_bot):
    """Test risk management integration"""
    # Mock current portfolio state
    mock_equity = Decimal('100000')
    mock_positions = {
        'pos1': {
            'symbol': 'BTC/USD',
            'side': 'long',
            'amount': Decimal('0.5'),
            'entry_price': Decimal('50000'),
            'current_price': Decimal('49000')
        }
    }
    
    # Update risk monitor
    trading_bot.risk_monitor.update_portfolio_state(
        mock_equity,
        mock_positions,
        Decimal('100000')
    )
    
    # Check risk limits
    assert not trading_bot.risk_monitor.check_max_drawdown()
    assert not trading_bot.risk_monitor.check_daily_loss()
    
    # Test position sizing
    size = trading_bot.position_sizer.calculate_position_size(
        available_balance=Decimal('100000'),
        current_price=Decimal('50000'),
        stop_loss=Decimal('49000'),
        method='fixed_risk'
    )
    
    assert size <= Decimal('0.2')  # Max position size limit

@pytest.mark.asyncio
async def test_multiple_position_management(trading_bot):
    """Test managing multiple positions"""
    # Mock positions
    positions = {
        'pos1': {
            'symbol': 'BTC/USD',
            'side': 'long',
            'amount': Decimal('0.5'),
            'entry_price': Decimal('50000'),
            'current_price': Decimal('51000')
        },
        'pos2': {
            'symbol': 'ETH/USD',
            'side': 'short',
            'amount': Decimal('5'),
            'entry_price': Decimal('3000'),
            'current_price': Decimal('2900')
        }
    }
    
    # Add positions to tracker
    for pos_id, pos_data in positions.items():
        trading_bot.position_tracker.add_position(
            pos_id,
            pos_data['symbol'],
            pos_data['side'],
            pos_data['amount'],
            pos_data['entry_price']
        )
    
    # Update position prices
    for pos_id, pos_data in positions.items():
        trading_bot.position_tracker.update_position_price(
            pos_id,
            pos_data['current_price']
        )
    
    # Check position tracking
    tracked_positions = trading_bot.position_tracker.get_positions()
    assert len(tracked_positions) == 2
    
    # Verify P&L calculation
    total_pnl = sum(pos.unrealized_pnl for pos in tracked_positions)
    assert total_pnl > 0

@pytest.mark.asyncio
async def test_error_handling(trading_bot):
    """Test error handling in trading flow"""
    # Mock exchange error
    with patch.object(
        trading_bot.exchange,
        'create_order',
        side_effect=Exception('API error')
    ):
        # Attempt to create order
        with pytest.raises(Exception):
            await trading_bot.create_order(
                symbol='BTC/USD',
                side='buy',
                type='limit',
                amount=Decimal('0.1'),
                price=Decimal('50000')
            )
        
        # Check error handling
        assert trading_bot.error_count > 0

@pytest.mark.asyncio
async def test_position_lifecycle(trading_bot):
    """Test complete position lifecycle"""
    # Mock exchange responses
    mock_responses = {
        'get_ticker': {'last': 50000},
        'create_order': {
            'id': '1234',
            'market': 'BTC/USD',
            'side': 'buy',
            'size': 0.1,
            'price': 50000,
            'status': 'closed'
        },
        'get_balance': [
            {'coin': 'USD', 'free': 100000, 'total': 100000}
        ]
    }
    
    with patch.multiple(
        trading_bot.exchange,
        get_ticker=MagicMock(return_value=mock_responses['get_ticker']),
        create_order=MagicMock(return_value=mock_responses['create_order']),
        get_balance=MagicMock(return_value=mock_responses['get_balance'])
    ):
        # Open position
        entry_order = await trading_bot.create_order(
            symbol='BTC/USD',
            side='buy',
            type='limit',
            amount=Decimal('0.1'),
            price=Decimal('50000')
        )
        
        # Update position
        trading_bot.position_tracker.update_position_price(
            entry_order['id'],
            Decimal('51000')
        )
        
        # Close position
        exit_order = await trading_bot.create_order(
            symbol='BTC/USD',
            side='sell',
            type='limit',
            amount=Decimal('0.1'),
            price=Decimal('51000')
        )
        
        # Verify position closure
        positions = trading_bot.position_tracker.get_positions()
        assert len(positions) == 0

@pytest.mark.asyncio
async def test_risk_limit_enforcement(trading_bot):
    """Test enforcement of risk limits"""
    # Set up initial state
    trading_bot.risk_monitor.update_portfolio_state(
        Decimal('100000'),  # equity
        {},  # positions
        Decimal('100000')  # account_balance
    )
    
    # Try to open position exceeding risk limits
    with pytest.raises(Exception):
        size = trading_bot.position_sizer.calculate_position_size(
            available_balance=Decimal('100000'),
            current_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
            method='fixed_risk'
        )
        
        # This should exceed max position size
        await trading_bot.create_order(
            symbol='BTC/USD',
            side='buy',
            type='limit',
            amount=size * Decimal('2'),  # Exceed max size
            price=Decimal('50000')
        )
