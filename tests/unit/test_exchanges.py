"""
Unit tests for exchange implementations
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import MagicMock, patch
from aiohttp import ClientSession
from app.core.exchanges.ftx import FTXExchange

@pytest.fixture
def exchange_config():
    """Create exchange configuration"""
    return {
        'api_url': 'https://ftx.com/api',
        'websocket_url': 'wss://ftx.com/ws/',
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'rate_limits': {
            'requests_per_minute': 1800,
            'orders_per_second': 8,
            'orders_per_day': 150000
        }
    }

@pytest.fixture
def ftx_exchange(exchange_config):
    """Create FTX exchange instance"""
    return FTXExchange(exchange_config)

@pytest.mark.asyncio
async def test_get_server_time(ftx_exchange):
    """Test getting server time"""
    mock_response = {'result': 1614556800.123}
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        timestamp = await ftx_exchange._get_server_time()
        assert isinstance(timestamp, int)
        assert timestamp == 1614556800123

@pytest.mark.asyncio
async def test_generate_signature(ftx_exchange):
    """Test signature generation"""
    method = 'POST'
    path = '/orders'
    params = {'market': 'BTC/USD', 'side': 'buy', 'size': 1.0}
    
    path, data, headers = ftx_exchange._generate_signature(method, path, params)
    
    assert 'FTX-KEY' in headers
    assert 'FTX-SIGN' in headers
    assert 'FTX-TS' in headers
    assert headers['FTX-KEY'] == 'test_key'

@pytest.mark.asyncio
async def test_make_request(ftx_exchange):
    """Test making API request"""
    mock_response = {'result': {'price': 50000}}
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        result = await ftx_exchange._make_request('GET', '/markets/BTC/USD')
        assert result == {'price': 50000}

@pytest.mark.asyncio
async def test_get_ticker(ftx_exchange):
    """Test getting ticker data"""
    mock_response = {
        'result': {
            'name': 'BTC/USD',
            'last': 50000,
            'bid': 49990,
            'ask': 50010,
            'volume': 1000
        }
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        ticker = await ftx_exchange.get_ticker('BTC/USD')
        assert ticker['name'] == 'BTC/USD'
        assert ticker['last'] == 50000

@pytest.mark.asyncio
async def test_get_orderbook(ftx_exchange):
    """Test getting orderbook"""
    mock_response = {
        'result': {
            'bids': [[50000, 1.0], [49990, 2.0]],
            'asks': [[50010, 1.5], [50020, 2.5]]
        }
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        orderbook = await ftx_exchange.get_orderbook('BTC/USD')
        assert len(orderbook['bids']) == 2
        assert len(orderbook['asks']) == 2

@pytest.mark.asyncio
async def test_create_order(ftx_exchange):
    """Test order creation"""
    mock_response = {
        'result': {
            'id': '1234',
            'market': 'BTC/USD',
            'side': 'buy',
            'size': 1.0,
            'price': 50000
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        order = await ftx_exchange.create_order(
            'BTC/USD',
            'buy',
            'limit',
            Decimal('1.0'),
            Decimal('50000')
        )
        
        assert order['id'] == '1234'
        assert order['market'] == 'BTC/USD'
        assert order['side'] == 'buy'

@pytest.mark.asyncio
async def test_cancel_order(ftx_exchange):
    """Test order cancellation"""
    mock_response = {'result': 'success'}
    
    with patch('aiohttp.ClientSession.delete') as mock_delete:
        mock_delete.return_value.__aenter__.return_value.status = 200
        mock_delete.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        result = await ftx_exchange.cancel_order('1234')
        assert result == 'success'

@pytest.mark.asyncio
async def test_get_balance(ftx_exchange):
    """Test getting balance"""
    mock_response = {
        'result': [
            {'coin': 'BTC', 'free': 1.0, 'total': 2.0},
            {'coin': 'USD', 'free': 50000, 'total': 100000}
        ]
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        # Test specific currency
        btc_balance = await ftx_exchange.get_balance('BTC')
        assert btc_balance['coin'] == 'BTC'
        assert btc_balance['free'] == 1.0
        
        # Test all balances
        all_balances = await ftx_exchange.get_balance()
        assert len(all_balances) == 2

@pytest.mark.asyncio
async def test_get_positions(ftx_exchange):
    """Test getting positions"""
    mock_response = {
        'result': [
            {
                'future': 'BTC-PERP',
                'size': 1.0,
                'side': 'buy',
                'entryPrice': 50000,
                'unrealizedPnl': 1000
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        positions = await ftx_exchange.get_positions()
        assert len(positions) == 1
        assert positions[0]['future'] == 'BTC-PERP'
        assert positions[0]['size'] == 1.0

@pytest.mark.asyncio
async def test_error_handling(ftx_exchange):
    """Test error handling"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Test API error
        mock_get.return_value.__aenter__.return_value.status = 400
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: {'error': 'Invalid request'})
        
        with pytest.raises(Exception):
            await ftx_exchange.get_ticker('BTC/USD')
        
        # Test network error
        mock_get.side_effect = Exception('Network error')
        
        with pytest.raises(Exception):
            await ftx_exchange.get_ticker('BTC/USD')

@pytest.mark.asyncio
async def test_rate_limiting(ftx_exchange):
    """Test rate limiting"""
    mock_response = {'result': {'price': 50000}}
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: mock_response)
        
        # Make multiple requests quickly
        for _ in range(5):
            await ftx_exchange._make_request('GET', '/markets/BTC/USD')
        
        # Verify rate limit tracking
        assert ftx_exchange._request_count > 0
        assert ftx_exchange._last_request_time > 0
