"""
Main window implementation for the trading bot GUI
"""

import sys
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                            QDockWidget, QMenuBar, QMenu, QAction, QStatusBar, QComboBox, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QByteArray
from .components.trading_panel import TradingPanel
from .components.chart_widget import ChartWidget
from .components.order_book import OrderBookWidget
from .components.position_table import PositionTableWidget
import mplfinance as mpf
import pandas as pd

class MainWindow(QMainWindow):
    """Main window for the trading bot application"""
    
    # Signals for real-time updates
    ticker_updated = pyqtSignal(dict)
    orderbook_updated = pyqtSignal(dict)
    trade_updated = pyqtSignal(dict)
    
    def __init__(self, config_dir):
        """Initialize main window"""
        super().__init__()
        self.config_dir = config_dir
        self.default_state = QByteArray()  # Initialize default_state
        self.securities_info = {
            "BTC": {
                "exchange": "Binance",
                "prices": {
                    "Binance": 50000,
                    "Coinbase": 50500,
                    "Kraken": 49800
                }
            },
            "ETH": {
                "exchange": "Coinbase",
                "prices": {
                    "Binance": 4000,
                    "Coinbase": 4050,
                    "Kraken": 3980
                }
            }
        }
        self.font_size = 16  # Store the default font size
        self.initUI()
        
        # Load settings
        self.settings = QSettings('TradingBot', 'MainWindow')
        
        # Initialize components
        self._init_components()
        self._init_menu_bar()
        self._init_status_bar()
        self._init_dock_widgets()
        self._init_shortcuts()
        
        # Load saved layout
        self.load_layout()
        
    def initUI(self):
        self.setWindowTitle('Trading Bot')
        self.setGeometry(100, 100, 1800, 800)  # Adjust width and height as needed
        
        font = self.font()
        font.setPointSize(self.font_size)
        self.setFont(font)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        self.layout.addLayout(controls_layout)

        # Trading mode selector
        trading_mode_label = QLabel("Trading Mode:")
        self.trading_mode_selector = QComboBox()
        self.trading_mode_selector.addItems(["Live Trading", "Paper Trading"])
        controls_layout.addWidget(trading_mode_label)
        controls_layout.addWidget(self.trading_mode_selector)

        # Connect the selection change signal
        self.trading_mode_selector.currentTextChanged.connect(self.on_trading_mode_change)

    def on_trading_mode_change(self, mode):
        if mode == "Live Trading":
            # Logic for live trading
            print("Switched to Live Trading")
        else:
            # Logic for paper trading
            print("Switched to Paper Trading")

    def _init_components(self):
        """Initialize GUI components"""
        # Create components
        self.trading_panel = TradingPanel()
        self.chart_widget = ChartWidget()
        self.order_book = OrderBookWidget()
        self.position_table = PositionTableWidget()
        
        # Connect signals
        self.trading_panel.order_submitted.connect(self._handle_order_submission)
        self.ticker_updated.connect(self._handle_ticker_update)
        self.orderbook_updated.connect(self._handle_orderbook_update)
        self.trade_updated.connect(self._handle_trade_update)
        
    def _init_menu_bar(self):
        """Initialize menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu('File')
        file_menu.addAction('Save Layout', self.save_layout)
        file_menu.addAction('Load Layout', self.load_layout)
        file_menu.addAction('Reset Layout', self.reset_layout)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        
        # View menu
        view_menu = menu_bar.addMenu('View')
        view_menu.addAction('Dark Theme',
                          lambda: self.switch_theme('dark'))
        view_menu.addAction('Light Theme',
                          lambda: self.switch_theme('light'))
        
        # Trading menu
        trading_menu = menu_bar.addMenu('Trading')
        self.cancel_all_orders_action = QAction('Cancel All Orders', self)
        self.close_all_positions_action = QAction('Close All Positions', self)
        trading_menu.addAction(self.cancel_all_orders_action)
        trading_menu.addAction(self.close_all_positions_action)
        
    def _init_status_bar(self):
        """Initialize status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Add status indicators
        self.connection_status = QWidget()
        self.connection_status.setFixedSize(16, 16)
        status_bar.addPermanentWidget(self.connection_status)
        
    def _init_dock_widgets(self):
        """Initialize dock widgets"""
        # Trading panel dock
        trading_dock = QDockWidget("Trading", self)
        trading_dock.setWidget(self.trading_panel)
        trading_dock.setAllowedAreas(Qt.LeftDockWidgetArea |
                                   Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, trading_dock)
        
        # Order book dock
        orderbook_dock = QDockWidget("Order Book", self)
        orderbook_dock.setWidget(self.order_book)
        orderbook_dock.setAllowedAreas(Qt.LeftDockWidgetArea |
                                     Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, orderbook_dock)
        
        # Position table dock
        position_dock = QDockWidget("Positions", self)
        position_dock.setWidget(self.position_table)
        position_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, position_dock)
        
    def _init_shortcuts(self):
        """Initialize keyboard shortcuts"""
        # Cancel all orders: Ctrl+Alt+C
        self.cancel_all_orders_action.setShortcut('Ctrl+Alt+C')
        
        # Close all positions: Ctrl+Alt+X
        self.close_all_positions_action.setShortcut('Ctrl+Alt+X')
        
    def save_layout(self):
        """Save current window layout"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        
    def load_layout(self):
        """Load saved window layout"""
        geometry = self.settings.value('geometry')
        state = self.settings.value('windowState')
        
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
            
    def reset_layout(self):
        """Reset to default layout"""
        self.resize(1280, 800)
        self.restoreState(self.default_state)
        
    def switch_theme(self, theme: str):
        """Switch between light and dark themes"""
        if theme == 'dark':
            self.setStyleSheet(self._get_dark_theme())
        else:
            self.setStyleSheet(self._get_light_theme())
        font = self.font()
        font.setPointSize(self.font_size)
        self.setFont(font)
            
    def _get_dark_theme(self) -> str:
        """Get dark theme stylesheet"""
        return """
            QMainWindow {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
            QMenuBar {
                background-color: #252526;
                color: #D4D4D4;
            }
            QStatusBar {
                background-color: #252526;
                color: #D4D4D4;
            }
        """
        
    def _get_light_theme(self) -> str:
        """Get light theme stylesheet"""
        return """
            QMainWindow {
                background-color: #FFFFFF;
                color: #000000;
            }
            QWidget {
                background-color: #FFFFFF;
                color: #000000;
            }
            QMenuBar {
                background-color: #F0F0F0;
                color: #000000;
            }
            QStatusBar {
                background-color: #F0F0F0;
                color: #000000;
            }
        """
        
    async def _handle_order_submission(self, order: Dict):
        """Handle order submission from trading panel"""
        try:
            # Create order
            result = await self.trading_bot.create_order(**order)
            
            # Update UI
            self.status_bar.showMessage(
                f"Order created: {result['id']}", 5000)
            
        except Exception as e:
            self.status_bar.showMessage(
                f"Order error: {str(e)}", 5000)
            
    async def _handle_ticker_update(self, data: Dict):
        """Handle ticker updates"""
        # Update chart
        self.chart_widget.update_price(
            Decimal(data['price']),
            datetime.fromtimestamp(data['timestamp'])
        )
        
        # Update order book
        self.order_book.update_best_prices(
            Decimal(data['bid']),
            Decimal(data['ask'])
        )
        
    async def _handle_orderbook_update(self, data: Dict):
        """Handle orderbook updates"""
        self.order_book.update_data(data)
        
    async def _handle_trade_update(self, data: Dict):
        """Handle trade updates"""
        # Update position table
        self.position_table.update_position(
            data['symbol'],
            Decimal(data['price'])
        )
        
        # Update chart
        self.chart_widget.add_trade(
            Decimal(data['price']),
            Decimal(data['amount']),
            data['side'],
            datetime.fromtimestamp(data['timestamp'])
        )

    def plot_candlestick_chart(self, data):
        # Create a DataFrame
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        # Plot the candlestick chart
        mpf.plot(df, type='candle', style='charles', title='Candlestick Chart', volume=False)

    def show_candlestick_chart(self):
        # Example data
        data = [
            {'Date': '2022-01-01', 'Open': 100, 'High': 120, 'Low': 90, 'Close': 110},
            {'Date': '2022-01-02', 'Open': 110, 'High': 130, 'Low': 100, 'Close': 120},
            {'Date': '2022-01-03', 'Open': 120, 'High': 140, 'Low': 110, 'Close': 130},
        ]
        self.plot_candlestick_chart(data)

    def display_security_info(self):
        for symbol, info in self.securities_info.items():
            print(f"{symbol} bought on {info['exchange']} at prices: {info['prices']}")

    def display_exchange_and_prices(self):
        for symbol, info in self.securities_info.items():
            print(f"{symbol}: {info['exchange']} - {info['prices']}")

# Example usage
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow("config_dir")
    window.show_candlestick_chart()
    window.display_security_info()
    window.display_exchange_and_prices()
    sys.exit(app.exec_())
