"""
Unit tests for risk monitoring system
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.core.risk_management.risk_monitor import RiskMonitor, AlertLevel, Alert

@pytest.fixture
def risk_monitor():
    """Create risk monitor instance"""
    config = {
        'max_drawdown': 0.1,
        'max_daily_loss': 0.05,
        'max_position_size': 0.2,
        'max_leverage': 3.0,
        'max_concentration': 0.3,
        'warning_threshold': 0.8,
        'critical_threshold': 0.95
    }
    return RiskMonitor(config)

@pytest.fixture
def sample_position():
    """Create sample position data"""
    return {
        'pos1': type('Position', (), {
            'symbol': 'BTC/USD',
            'current_price': Decimal('50000'),
            'amount': Decimal('1')
        })
    }

def test_monitor_initialization(risk_monitor):
    """Test monitor initialization"""
    assert risk_monitor.max_drawdown == Decimal('0.1')
    assert risk_monitor.max_daily_loss == Decimal('0.05')
    assert risk_monitor.max_position_size == Decimal('0.2')
    assert risk_monitor.max_leverage == Decimal('3.0')
    assert risk_monitor.max_concentration == Decimal('0.3')
    assert risk_monitor.warning_threshold == Decimal('0.8')
    assert risk_monitor.critical_threshold == Decimal('0.95')

def test_drawdown_monitoring(risk_monitor):
    """Test drawdown monitoring"""
    # Set initial equity peak
    risk_monitor.peak_equity = Decimal('100000')
    
    # Test warning level
    current_equity = Decimal('92000')  # 8% drawdown
    risk_monitor.update_portfolio_state(current_equity, {}, Decimal('92000'))
    assert any(
        alert.level == AlertLevel.WARNING and alert.metric == 'drawdown'
        for alert in risk_monitor.alert_history
    )
    
    # Test critical level
    current_equity = Decimal('89000')  # 11% drawdown
    risk_monitor.update_portfolio_state(current_equity, {}, Decimal('89000'))
    assert any(
        alert.level == AlertLevel.CRITICAL and alert.metric == 'drawdown'
        for alert in risk_monitor.alert_history
    )

def test_daily_loss_monitoring(risk_monitor):
    """Test daily loss monitoring"""
    # Set daily start equity
    risk_monitor.daily_start = Decimal('100000')
    
    # Test warning level
    current_equity = Decimal('96000')  # 4% loss
    risk_monitor.update_portfolio_state(current_equity, {}, Decimal('96000'))
    assert any(
        alert.level == AlertLevel.WARNING and alert.metric == 'daily_loss'
        for alert in risk_monitor.alert_history
    )
    
    # Test critical level
    current_equity = Decimal('94000')  # 6% loss
    risk_monitor.update_portfolio_state(current_equity, {}, Decimal('94000'))
    assert any(
        alert.level == AlertLevel.CRITICAL and alert.metric == 'daily_loss'
        for alert in risk_monitor.alert_history
    )

def test_position_size_monitoring(risk_monitor, sample_position):
    """Test position size monitoring"""
    account_balance = Decimal('200000')
    
    # Test warning level
    sample_position['pos1'].amount = Decimal('0.8')  # 20% of account
    risk_monitor.update_portfolio_state(
        account_balance,
        sample_position,
        account_balance
    )
    assert any(
        alert.level == AlertLevel.WARNING and alert.metric == 'position_size'
        for alert in risk_monitor.alert_history
    )
    
    # Test critical level
    sample_position['pos1'].amount = Decimal('1.0')  # 25% of account
    risk_monitor.update_portfolio_state(
        account_balance,
        sample_position,
        account_balance
    )
    assert any(
        alert.level == AlertLevel.CRITICAL and alert.metric == 'position_size'
        for alert in risk_monitor.alert_history
    )

def test_leverage_monitoring(risk_monitor, sample_position):
    """Test leverage monitoring"""
    account_balance = Decimal('100000')
    
    # Test warning level
    sample_position['pos1'].amount = Decimal('5.0')  # 2.5x leverage
    risk_monitor.update_portfolio_state(
        account_balance,
        sample_position,
        account_balance
    )
    assert any(
        alert.level == AlertLevel.WARNING and alert.metric == 'leverage'
        for alert in risk_monitor.alert_history
    )
    
    # Test critical level
    sample_position['pos1'].amount = Decimal('7.0')  # 3.5x leverage
    risk_monitor.update_portfolio_state(
        account_balance,
        sample_position,
        account_balance
    )
    assert any(
        alert.level == AlertLevel.CRITICAL and alert.metric == 'leverage'
        for alert in risk_monitor.alert_history
    )

def test_concentration_monitoring(risk_monitor, sample_position):
    """Test concentration monitoring"""
    account_balance = Decimal('200000')
    
    # Test warning level
    sample_position['pos1'].amount = Decimal('1.0')  # 25% concentration
    risk_monitor.update_portfolio_state(
        account_balance,
        sample_position,
        account_balance
    )
    assert any(
        alert.level == AlertLevel.WARNING and alert.metric == 'concentration'
        for alert in risk_monitor.alert_history
    )
    
    # Test critical level
    sample_position['pos1'].amount = Decimal('1.5')  # 37.5% concentration
    risk_monitor.update_portfolio_state(
        account_balance,
        sample_position,
        account_balance
    )
    assert any(
        alert.level == AlertLevel.CRITICAL and alert.metric == 'concentration'
        for alert in risk_monitor.alert_history
    )

def test_alert_callbacks(risk_monitor):
    """Test alert callback functionality"""
    alerts_received = []
    
    def alert_callback(alert):
        alerts_received.append(alert)
        
    # Register callback
    risk_monitor.register_alert_callback(alert_callback)
    
    # Trigger alert
    risk_monitor.peak_equity = Decimal('100000')
    current_equity = Decimal('89000')  # 11% drawdown
    risk_monitor.update_portfolio_state(current_equity, {}, Decimal('89000'))
    
    assert len(alerts_received) > 0
    assert isinstance(alerts_received[0], Alert)
    assert alerts_received[0].level == AlertLevel.CRITICAL
    assert alerts_received[0].metric == 'drawdown'

def test_daily_reset(risk_monitor):
    """Test daily tracking reset"""
    # Set initial values
    risk_monitor.daily_start = Decimal('100000')
    risk_monitor.daily_high = Decimal('105000')
    risk_monitor.daily_low = Decimal('95000')
    risk_monitor.last_reset = datetime.now() - timedelta(days=1, minutes=1)
    
    # Trigger reset
    risk_monitor._reset_daily_tracking()
    
    assert risk_monitor.daily_start == Decimal('0')
    assert risk_monitor.daily_high == Decimal('0')
    assert risk_monitor.daily_low == Decimal('0')
    assert len(risk_monitor.active_alerts) == 0
