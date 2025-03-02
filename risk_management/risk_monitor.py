"""
Risk Monitoring System
Monitors trading risk metrics and generates alerts
"""

from decimal import Decimal
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum
import json
from loguru import logger

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Trading alert information"""
    level: AlertLevel
    message: str
    metric: str
    value: Decimal
    threshold: Decimal
    timestamp: datetime

class RiskMonitor:
    """Monitors trading risk metrics and generates alerts"""
    
    def __init__(self, config: Dict):
        """
        Initialize risk monitor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Risk limits
        self.max_drawdown = Decimal(str(config.get('max_drawdown', 0.1)))
        self.max_daily_loss = Decimal(str(config.get('max_daily_loss', 0.05)))
        self.max_position_size = Decimal(str(config.get('max_position_size', 0.2)))
        self.max_leverage = Decimal(str(config.get('max_leverage', 3.0)))
        self.max_concentration = Decimal(str(config.get('max_concentration', 0.3)))
        
        # Alert thresholds (percentage of limit)
        self.warning_threshold = Decimal(str(config.get('warning_threshold', 0.8)))
        self.critical_threshold = Decimal(str(config.get('critical_threshold', 0.95)))
        
        # State tracking
        self.peak_equity = Decimal('0')
        self.daily_high = Decimal('0')
        self.daily_low = Decimal('0')
        self.daily_start = Decimal('0')
        self.last_reset = datetime.now()
        
        # Alert tracking
        self.active_alerts: Set[str] = set()
        self.alert_history: List[Alert] = []
        
        # Alert callbacks
        self.alert_callbacks: List = []
        
    async def start(self) -> None:
        """Start risk monitoring"""
        logger.info("Starting risk monitoring")
        # Start monitoring tasks
        asyncio.create_task(self._monitor_daily_reset())
        
    def register_alert_callback(self, callback) -> None:
        """Register callback for alerts"""
        self.alert_callbacks.append(callback)
        
    def update_portfolio_state(
        self,
        current_equity: Decimal,
        positions: Dict,
        account_balance: Decimal
    ) -> None:
        """
        Update portfolio state and check risk metrics
        
        Args:
            current_equity: Current portfolio equity
            positions: Open positions
            account_balance: Account balance
        """
        try:
            # Update tracking values
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
                
            if self.daily_high == Decimal('0') or current_equity > self.daily_high:
                self.daily_high = current_equity
                
            if self.daily_low == Decimal('0') or current_equity < self.daily_low:
                self.daily_low = current_equity
                
            if self.daily_start == Decimal('0'):
                self.daily_start = current_equity
                
            # Check risk metrics
            self._check_drawdown(current_equity)
            self._check_daily_loss(current_equity)
            self._check_position_sizes(positions, account_balance)
            self._check_leverage(positions, account_balance)
            self._check_concentration(positions, account_balance)
            
        except Exception as e:
            logger.error(f"Error updating portfolio state: {str(e)}")
            
    def _check_drawdown(self, current_equity: Decimal) -> None:
        """Check maximum drawdown"""
        if self.peak_equity == Decimal('0'):
            return
            
        drawdown = (self.peak_equity - current_equity) / self.peak_equity
        
        if drawdown > self.max_drawdown:
            self._create_alert(
                AlertLevel.CRITICAL,
                "Maximum drawdown exceeded",
                "drawdown",
                drawdown,
                self.max_drawdown
            )
        elif drawdown > self.max_drawdown * self.warning_threshold:
            self._create_alert(
                AlertLevel.WARNING,
                "Approaching maximum drawdown",
                "drawdown",
                drawdown,
                self.max_drawdown
            )
            
    def _check_daily_loss(self, current_equity: Decimal) -> None:
        """Check daily loss limit"""
        if self.daily_start == Decimal('0'):
            return
            
        daily_return = (current_equity - self.daily_start) / self.daily_start
        
        if daily_return < -self.max_daily_loss:
            self._create_alert(
                AlertLevel.CRITICAL,
                "Maximum daily loss exceeded",
                "daily_loss",
                -daily_return,
                self.max_daily_loss
            )
        elif daily_return < -self.max_daily_loss * self.warning_threshold:
            self._create_alert(
                AlertLevel.WARNING,
                "Approaching maximum daily loss",
                "daily_loss",
                -daily_return,
                self.max_daily_loss
            )
            
    def _check_position_sizes(
        self,
        positions: Dict,
        account_balance: Decimal
    ) -> None:
        """Check individual position sizes"""
        for pos_id, position in positions.items():
            position_value = position.current_price * position.amount
            position_size = position_value / account_balance
            
            if position_size > self.max_position_size:
                self._create_alert(
                    AlertLevel.CRITICAL,
                    f"Position size exceeded for {position.symbol}",
                    "position_size",
                    position_size,
                    self.max_position_size
                )
            elif position_size > self.max_position_size * self.warning_threshold:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"Large position size for {position.symbol}",
                    "position_size",
                    position_size,
                    self.max_position_size
                )
                
    def _check_leverage(
        self,
        positions: Dict,
        account_balance: Decimal
    ) -> None:
        """Check total leverage"""
        total_exposure = sum(
            pos.current_price * pos.amount
            for pos in positions.values()
        )
        
        leverage = total_exposure / account_balance
        
        if leverage > self.max_leverage:
            self._create_alert(
                AlertLevel.CRITICAL,
                "Maximum leverage exceeded",
                "leverage",
                leverage,
                self.max_leverage
            )
        elif leverage > self.max_leverage * self.warning_threshold:
            self._create_alert(
                AlertLevel.WARNING,
                "Approaching maximum leverage",
                "leverage",
                leverage,
                self.max_leverage
            )
            
    def _check_concentration(
        self,
        positions: Dict,
        account_balance: Decimal
    ) -> None:
        """Check asset concentration"""
        # Group positions by symbol
        symbol_exposure = {}
        for position in positions.values():
            symbol = position.symbol
            value = position.current_price * position.amount
            
            if symbol in symbol_exposure:
                symbol_exposure[symbol] += value
            else:
                symbol_exposure[symbol] = value
                
        # Check concentration for each symbol
        for symbol, exposure in symbol_exposure.items():
            concentration = exposure / account_balance
            
            if concentration > self.max_concentration:
                self._create_alert(
                    AlertLevel.CRITICAL,
                    f"High concentration in {symbol}",
                    "concentration",
                    concentration,
                    self.max_concentration
                )
            elif concentration > self.max_concentration * self.warning_threshold:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"Increasing concentration in {symbol}",
                    "concentration",
                    concentration,
                    self.max_concentration
                )
                
    def _create_alert(
        self,
        level: AlertLevel,
        message: str,
        metric: str,
        value: Decimal,
        threshold: Decimal
    ) -> None:
        """Create and process new alert"""
        # Create alert key
        alert_key = f"{level.value}_{metric}"
        
        # Check if alert is already active
        if alert_key in self.active_alerts:
            return
            
        # Create alert
        alert = Alert(
            level=level,
            message=message,
            metric=metric,
            value=value,
            threshold=threshold,
            timestamp=datetime.now()
        )
        
        # Add to tracking
        self.active_alerts.add(alert_key)
        self.alert_history.append(alert)
        
        # Log alert
        log_message = (
            f"{level.value.upper()}: {message} "
            f"(Current: {value:.2%}, Limit: {threshold:.2%})"
        )
        if level == AlertLevel.CRITICAL:
            logger.critical(log_message)
        elif level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {str(e)}")
                
    async def _monitor_daily_reset(self) -> None:
        """Monitor for daily reset"""
        while True:
            now = datetime.now()
            
            # Check if we need to reset daily tracking
            if (now - self.last_reset).days > 0:
                self._reset_daily_tracking()
                
            # Sleep until next check
            await asyncio.sleep(60)  # Check every minute
            
    def _reset_daily_tracking(self) -> None:
        """Reset daily tracking values"""
        self.daily_high = Decimal('0')
        self.daily_low = Decimal('0')
        self.daily_start = Decimal('0')
        self.last_reset = datetime.now()
        self.active_alerts.clear()
        
        logger.info("Reset daily risk tracking")
