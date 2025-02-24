"""
Unit tests for external bot interface
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
import json
import websockets
from unittest.mock import MagicMock, patch
from app.core.external.bot_interface import BotRecommendation, ExternalBotInterface

@pytest.fixture
def bot_interface():
    """Create bot interface instance"""
    return ExternalBotInterface()

@pytest.fixture
def sample_recommendation():
    """Create sample trading recommendation"""
    return BotRecommendation(
        symbol='BTC/USD',
        action='buy',
        source='test_bot',
        confidence=0.8,
        timestamp=datetime.now(),
        metadata={'strategy': 'trend_following'}
    )

def test_recommendation_creation(sample_recommendation):
    """Test recommendation creation"""
    assert sample_recommendation.symbol == 'BTC/USD'
    assert sample_recommendation.action == 'buy'
    assert sample_recommendation.source == 'test_bot'
    assert sample_recommendation.confidence == 0.8
    assert isinstance(sample_recommendation.timestamp, datetime)
    assert sample_recommendation.metadata['strategy'] == 'trend_following'

def test_recommendation_serialization(sample_recommendation):
    """Test recommendation serialization"""
    # Convert to dict
    data = sample_recommendation.to_dict()
    
    assert isinstance(data, dict)
    assert data['symbol'] == 'BTC/USD'
    assert data['action'] == 'buy'
    assert isinstance(data['timestamp'], str)
    
    # Convert back to recommendation
    rec = BotRecommendation.from_dict(data)
    
    assert rec.symbol == sample_recommendation.symbol
    assert rec.action == sample_recommendation.action
    assert rec.confidence == sample_recommendation.confidence

@pytest.mark.asyncio
async def test_interface_lifecycle(bot_interface):
    """Test interface start/stop lifecycle"""
    await bot_interface.start()
    assert bot_interface._running is True
    
    await bot_interface.stop()
    assert bot_interface._running is False
    assert len(bot_interface.websocket_clients) == 0

@pytest.mark.asyncio
async def test_bot_connection(bot_interface):
    """Test bot connection management"""
    connection_details = {
        'protocol': 'ws',
        'uri': 'ws://test.local:8080'
    }
    
    # Mock websockets.connect
    mock_ws = MagicMock()
    mock_ws.close = asyncio.coroutine(lambda: None)
    
    with patch('websockets.connect', return_value=mock_ws):
        # Connect bot
        success = await bot_interface.connect_bot('test_bot', connection_details)
        assert success is True
        assert 'test_bot' in bot_interface.connected_bots
        assert 'test_bot' in bot_interface.websocket_clients
        
        # Disconnect bot
        await bot_interface.disconnect_bot('test_bot')
        assert 'test_bot' not in bot_interface.connected_bots
        assert 'test_bot' not in bot_interface.websocket_clients

def test_recommendation_management(bot_interface, sample_recommendation):
    """Test recommendation management"""
    # Add recommendation
    bot_interface.add_recommendation(sample_recommendation)
    assert len(bot_interface.recommendations) == 1
    
    # Get recommendations
    recs = bot_interface.get_recommendations(
        symbol='BTC/USD',
        source='test_bot',
        min_confidence=0.7
    )
    assert len(recs) == 1
    assert recs[0].symbol == 'BTC/USD'
    
    # Test filtering
    recs = bot_interface.get_recommendations(
        symbol='ETH/USD'  # Different symbol
    )
    assert len(recs) == 0
    
    recs = bot_interface.get_recommendations(
        min_confidence=0.9  # Higher confidence threshold
    )
    assert len(recs) == 0

def test_recommendation_aging(bot_interface):
    """Test recommendation aging and cleanup"""
    old_rec = BotRecommendation(
        symbol='BTC/USD',
        action='buy',
        source='test_bot',
        confidence=0.8,
        timestamp=datetime.now() - timedelta(hours=2),
        metadata={}
    )
    
    new_rec = BotRecommendation(
        symbol='ETH/USD',
        action='sell',
        source='test_bot',
        confidence=0.9,
        timestamp=datetime.now(),
        metadata={}
    )
    
    # Add recommendations
    bot_interface.add_recommendation(old_rec)
    bot_interface.add_recommendation(new_rec)
    
    # Get recent recommendations
    recs = bot_interface.get_recommendations(max_age_minutes=60)
    assert len(recs) == 1
    assert recs[0].symbol == 'ETH/USD'

@pytest.mark.asyncio
async def test_websocket_recommendation_handling(bot_interface):
    """Test handling of websocket recommendations"""
    mock_ws = MagicMock()
    recommendation_data = {
        'symbol': 'BTC/USD',
        'action': 'buy',
        'confidence': 0.8,
        'metadata': {'strategy': 'momentum'}
    }
    
    # Mock receive function
    async def mock_recv():
        return json.dumps(recommendation_data)
    mock_ws.recv = mock_recv
    
    # Start listening task
    task = asyncio.create_task(
        bot_interface._listen_for_recommendations('test_bot', mock_ws)
    )
    
    # Wait briefly for processing
    await asyncio.sleep(0.1)
    
    # Check recommendation was added
    recs = bot_interface.get_recommendations(symbol='BTC/USD')
    assert len(recs) == 1
    assert recs[0].symbol == 'BTC/USD'
    assert recs[0].action == 'buy'
    
    # Clean up
    bot_interface._running = False
    await task

@pytest.mark.asyncio
async def test_connection_error_handling(bot_interface):
    """Test handling of connection errors"""
    connection_details = {
        'protocol': 'ws',
        'uri': 'ws://invalid:8080'
    }
    
    # Test connection failure
    success = await bot_interface.connect_bot('test_bot', connection_details)
    assert success is False
    assert 'test_bot' not in bot_interface.connected_bots

@pytest.mark.asyncio
async def test_websocket_error_handling(bot_interface):
    """Test handling of websocket errors"""
    mock_ws = MagicMock()
    
    # Mock receive function that raises an error
    async def mock_recv():
        raise websockets.exceptions.ConnectionClosed(1000, "Normal closure")
    mock_ws.recv = mock_recv
    
    # Start listening task
    task = asyncio.create_task(
        bot_interface._listen_for_recommendations('test_bot', mock_ws)
    )
    
    # Wait briefly for processing
    await asyncio.sleep(0.1)
    
    # Check that no recommendations were added
    assert len(bot_interface.recommendations) == 0
    
    # Clean up
    bot_interface._running = False
    await task

def test_invalid_recommendation_data(bot_interface):
    """Test handling of invalid recommendation data"""
    # Missing required fields
    invalid_rec = {
        'symbol': 'BTC/USD',
        # Missing 'action'
        'source': 'test_bot',
        'timestamp': datetime.now().isoformat()
    }
    
    with pytest.raises(KeyError):
        BotRecommendation.from_dict(invalid_rec)
    
    # Invalid confidence value
    invalid_rec = BotRecommendation(
        symbol='BTC/USD',
        action='buy',
        source='test_bot',
        confidence=1.5,  # Should be between 0 and 1
        timestamp=datetime.now(),
        metadata={}
    )
    
    bot_interface.add_recommendation(invalid_rec)
    
    # Should not be returned when filtering for valid confidence
    recs = bot_interface.get_recommendations(
        symbol='BTC/USD',
        min_confidence=0.0,
        max_age_minutes=60
    )
    assert len(recs) == 0
