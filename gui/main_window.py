"""
Main Application Window
"""

import sys
from decimal import Decimal
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from loguru import logger
import asyncio

from ..config import ConfigManager
from ..core.exchanges.exchange_factory import ExchangeFactory
from ..core.portfolio.position_tracker import PositionTracker
from .widgets.price_chart import PriceChart
from .widgets.trade_table import TradeTable
from .widgets.control_panel import ControlPanel

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(
        self,
        config: ConfigManager,
        exchange_factory: ExchangeFactory,
        position_tracker: PositionTracker,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.config = config
        self.exchange_factory = exchange_factory
        self.position_tracker = position_tracker
        
        self.setWindowTitle("Advanced Trading Bot")
        self.setMinimumSize(1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create top section
        self._create_top_section(layout)
        
        # Create middle section with tabs
        self._create_middle_section(layout)
        
        # Create bottom section
        self._create_bottom_section(layout)
        
        # Initialize data update timer
        self._init_update_timer()
        
    def _create_top_section(self, parent_layout: QVBoxLayout) -> None:
        """Create top section of the GUI"""
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        
        # Mode selection buttons
        mode_group = QWidget()
        mode_layout = QHBoxLayout(mode_group)
        
        self.live_button = QPushButton("Live Trading")
        self.paper_button = QPushButton("Paper Trading")
        self.live_button.setCheckable(True)
        self.paper_button.setCheckable(True)
        self.paper_button.setChecked(True)  # Default to paper trading
        
        mode_layout.addWidget(self.live_button)
        mode_layout.addWidget(self.paper_button)
        
        # Connect mode buttons
        self.live_button.clicked.connect(self._on_live_mode_clicked)
        self.paper_button.clicked.connect(self._on_paper_mode_clicked)
        
        # Stats display
        stats_group = QWidget()
        stats_layout = QHBoxLayout(stats_group)
        
        self.daily_trades_label = QLabel("Daily Trades: 0")
        self.weekly_trades_label = QLabel("Weekly Trades: 0")
        self.daily_pnl_label = QLabel("Daily P&L: $0.00")
        self.total_pnl_label = QLabel("Total P&L: $0.00")
        self.liquid_balance_label = QLabel("Available: $0.00")
        
        stats_layout.addWidget(self.daily_trades_label)
        stats_layout.addWidget(self.weekly_trades_label)
        stats_layout.addWidget(self.daily_pnl_label)
        stats_layout.addWidget(self.total_pnl_label)
        stats_layout.addWidget(self.liquid_balance_label)
        
        # Add to top layout
        top_layout.addWidget(mode_group)
        top_layout.addStretch()
        top_layout.addWidget(stats_group)
        
        parent_layout.addWidget(top_widget)
        
    def _create_middle_section(self, parent_layout: QVBoxLayout) -> None:
        """Create middle section with tabs"""
        tab_widget = QTabWidget()
        
        # Recommendations tab
        self.recommendations_table = TradeTable(
            ["Symbol", "Source", "Signal", "Volatility", "Price", "Volume"]
        )
        tab_widget.addTab(self.recommendations_table, "Recommendations")
        
        # Active positions tab
        self.active_positions_table = TradeTable([
            "Symbol", "Side", "Entry Price", "Current Price",
            "Amount", "P&L", "Stop Loss", "Age"
        ])
        tab_widget.addTab(self.active_positions_table, "Active Positions")
        
        # Closed positions tab
        self.closed_positions_table = TradeTable([
            "Symbol", "Side", "Entry Price", "Exit Price",
            "Amount", "P&L", "Duration", "Fees"
        ])
        tab_widget.addTab(self.closed_positions_table, "Closed Positions")
        
        # Add chart
        self.price_chart = PriceChart()
        tab_widget.addTab(self.price_chart, "Charts")
        
        parent_layout.addWidget(tab_widget)
        
    def _create_bottom_section(self, parent_layout: QVBoxLayout) -> None:
        """Create bottom section with controls"""
        self.control_panel = ControlPanel(self.config)
        parent_layout.addWidget(self.control_panel)
        
        # Connect control panel signals
        self.control_panel.strategy_changed.connect(self._on_strategy_changed)
        self.control_panel.security_type_changed.connect(self._on_security_type_changed)
        self.control_panel.position_limit_changed.connect(self._on_position_limit_changed)
        self.control_panel.investment_limit_changed.connect(self._on_investment_limit_changed)
        self.control_panel.stop_loss_changed.connect(self._on_stop_loss_changed)
        
    def _init_update_timer(self) -> None:
        """Initialize data update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(5000)  # Update every 5 seconds
        
    def _update_data(self) -> None:
        """Update all dynamic data"""
        try:
            # Update position data
            self._update_positions()
            
            # Update statistics
            self._update_statistics()
            
            # Update recommendations
            self._update_recommendations()
            
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}")
            
    def _update_positions(self) -> None:
        """Update position tables"""
        # Update active positions
        active_positions = self.position_tracker.get_all_positions()
        self.active_positions_table.update_data([
            self._format_position_data(pos) for pos in active_positions
        ])
        
        # Update closed positions
        closed_positions = self.position_tracker.get_closed_positions()
        self.closed_positions_table.update_data([
            self._format_closed_position_data(pos) for pos in closed_positions
        ])
        
    def _update_statistics(self) -> None:
        """Update statistical displays"""
        # Update P&L displays
        total_pnl = self.position_tracker.get_total_pnl()
        self.total_pnl_label.setText(f"Total P&L: ${total_pnl:.2f}")
        
        # Color code based on profit/loss
        if total_pnl > 0:
            self.total_pnl_label.setStyleSheet("color: green")
        elif total_pnl < 0:
            self.total_pnl_label.setStyleSheet("color: red")
        else:
            self.total_pnl_label.setStyleSheet("")
            
    def _update_recommendations(self) -> None:
        """Update recommendation table"""
        # This would be updated with actual bot recommendations
        pass
        
    def _format_position_data(self, position) -> List:
        """Format position data for display"""
        return [
            position.symbol,
            position.side,
            f"${float(position.entry_price):.2f}",
            f"${float(position.current_price):.2f}",
            f"{float(position.amount):.4f}",
            f"${float(position.unrealized_pnl):.2f}",
            f"${float(position.stop_loss):.2f}",
            str(position.entry_time)
        ]
        
    def _format_closed_position_data(self, position) -> List:
        """Format closed position data for display"""
        duration = position.exit_time - position.entry_time
        return [
            position.symbol,
            position.side,
            f"${float(position.entry_price):.2f}",
            f"${float(position.current_price):.2f}",
            f"{float(position.amount):.4f}",
            f"${float(position.realized_pnl):.2f}",
            str(duration),
            f"${float(position.fees):.2f}"
        ]
        
    def _on_live_mode_clicked(self) -> None:
        """Handle live mode button click"""
        if self.live_button.isChecked():
            self.paper_button.setChecked(False)
            # Implement live mode logic
            logger.info("Switching to live trading mode")
            
    def _on_paper_mode_clicked(self) -> None:
        """Handle paper mode button click"""
        if self.paper_button.isChecked():
            self.live_button.setChecked(False)
            # Implement paper mode logic
            logger.info("Switching to paper trading mode")
            
    def _on_strategy_changed(self, strategy: str) -> None:
        """Handle strategy change"""
        logger.info(f"Strategy changed to: {strategy}")
        
    def _on_security_type_changed(self, security_type: str) -> None:
        """Handle security type change"""
        logger.info(f"Security type changed to: {security_type}")
        
    def _on_position_limit_changed(self, limit: int) -> None:
        """Handle position limit change"""
        logger.info(f"Position limit changed to: {limit}")
        
    def _on_investment_limit_changed(self, limit: float) -> None:
        """Handle investment limit change"""
        logger.info(f"Investment limit changed to: ${limit}")
        
    def _on_stop_loss_changed(self, stop_loss: float) -> None:
        """Handle stop loss change"""
        logger.info(f"Stop loss changed to: {stop_loss}%")
