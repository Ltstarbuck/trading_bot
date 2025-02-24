"""
Unit tests for GUI components
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from app.gui.main_window import MainWindow
from app.gui.components.trading_panel import TradingPanel
from app.gui.components.chart_widget import ChartWidget
from app.gui.components.order_book import OrderBookWidget
from app.gui.components.position_table import PositionTableWidget

@pytest.fixture
def app():
    """Create QApplication instance"""
    return QApplication([])

@pytest.fixture
def main_window(app):
    """Create main window instance"""
    return MainWindow()

@pytest.fixture
def trading_panel():
    """Create trading panel instance"""
    return TradingPanel()

@pytest.fixture
def chart_widget():
    """Create chart widget instance"""
    return ChartWidget()

@pytest.fixture
def order_book():
    """Create order book widget instance"""
    return OrderBookWidget()

@pytest.fixture
def position_table():
    """Create position table widget instance"""
    return PositionTableWidget()

def test_main_window_initialization(main_window):
    """Test main window initialization"""
    assert isinstance(main_window, QMainWindow)
    assert main_window.windowTitle() == "Trading Bot"
    assert main_window.isVisible() is False

def test_main_window_components(main_window):
    """Test main window components"""
    # Check central widget
    assert main_window.centralWidget() is not None
    
    # Check menu bar
    menu_bar = main_window.menuBar()
    assert menu_bar is not None
    assert len(menu_bar.actions()) > 0
    
    # Check status bar
    status_bar = main_window.statusBar()
    assert status_bar is not None

def test_trading_panel_initialization(trading_panel):
    """Test trading panel initialization"""
    # Check default values
    assert trading_panel.current_symbol == ""
    assert trading_panel.order_type.currentText() == "Market"
    assert trading_panel.side.currentText() == "Buy"
    
    # Check widgets
    assert trading_panel.symbol_selector is not None
    assert trading_panel.order_type is not None
    assert trading_panel.side is not None
    assert trading_panel.amount is not None
    assert trading_panel.price is not None

def test_trading_panel_order_creation(trading_panel):
    """Test order creation in trading panel"""
    # Set up mock order handler
    mock_handler = MagicMock()
    trading_panel.order_submitted.connect(mock_handler)
    
    # Fill order details
    trading_panel.symbol_selector.setCurrentText("BTC/USD")
    trading_panel.order_type.setCurrentText("Limit")
    trading_panel.side.setCurrentText("Buy")
    trading_panel.amount.setValue(1.0)
    trading_panel.price.setValue(50000.0)
    
    # Submit order
    QTest.mouseClick(trading_panel.submit_button, Qt.LeftButton)
    
    # Check if handler was called with correct parameters
    mock_handler.assert_called_once()
    order = mock_handler.call_args[0][0]
    assert order['symbol'] == "BTC/USD"
    assert order['type'] == "Limit"
    assert order['side'] == "Buy"
    assert order['amount'] == 1.0
    assert order['price'] == 50000.0

def test_chart_widget_initialization(chart_widget):
    """Test chart widget initialization"""
    assert chart_widget.symbol == ""
    assert chart_widget.timeframe == "1m"
    assert chart_widget.chart_type == "candlestick"

def test_chart_widget_update(chart_widget):
    """Test chart data update"""
    # Mock candle data
    candles = [
        {'time': '2025-02-23T18:30:00', 'open': 50000, 'high': 50100,
         'low': 49900, 'close': 50050, 'volume': 100},
        {'time': '2025-02-23T18:31:00', 'open': 50050, 'high': 50150,
         'low': 49950, 'close': 50100, 'volume': 120}
    ]
    
    # Update chart
    chart_widget.update_data(candles)
    
    # Check if data was updated
    assert len(chart_widget.candle_data) == 2
    assert chart_widget.candle_data[-1]['close'] == 50100

def test_order_book_initialization(order_book):
    """Test order book widget initialization"""
    assert order_book.symbol == ""
    assert len(order_book.bids) == 0
    assert len(order_book.asks) == 0

def test_order_book_update(order_book):
    """Test order book update"""
    # Mock order book data
    data = {
        'bids': [[50000, 1.0], [49990, 2.0]],
        'asks': [[50010, 1.5], [50020, 2.5]]
    }
    
    # Update order book
    order_book.update_data(data)
    
    # Check if data was updated
    assert len(order_book.bids) == 2
    assert len(order_book.asks) == 2
    assert order_book.bids[0] == [50000, 1.0]
    assert order_book.asks[0] == [50010, 1.5]

def test_position_table_initialization(position_table):
    """Test position table initialization"""
    assert position_table.rowCount() == 0
    headers = [position_table.horizontalHeaderItem(i).text()
              for i in range(position_table.columnCount())]
    assert "Symbol" in headers
    assert "Side" in headers
    assert "Amount" in headers
    assert "Entry Price" in headers
    assert "Current Price" in headers
    assert "P&L" in headers

def test_position_table_update(position_table):
    """Test position table update"""
    # Mock position data
    positions = [
        {
            'symbol': 'BTC/USD',
            'side': 'long',
            'amount': 1.0,
            'entry_price': 50000,
            'current_price': 51000,
            'pnl': 1000
        }
    ]
    
    # Update table
    position_table.update_data(positions)
    
    # Check if data was updated
    assert position_table.rowCount() == 1
    assert position_table.item(0, 0).text() == 'BTC/USD'
    assert position_table.item(0, 1).text() == 'long'
    assert float(position_table.item(0, 2).text()) == 1.0

def test_keyboard_shortcuts(main_window):
    """Test keyboard shortcuts"""
    # Mock handlers
    mock_cancel_orders = MagicMock()
    mock_close_positions = MagicMock()
    
    # Set up shortcuts
    main_window.cancel_all_orders_action.triggered.connect(mock_cancel_orders)
    main_window.close_all_positions_action.triggered.connect(mock_close_positions)
    
    # Simulate keyboard shortcuts
    QTest.keyClick(main_window, Qt.Key_C, Qt.ControlModifier | Qt.AltModifier)
    QTest.keyClick(main_window, Qt.Key_X, Qt.ControlModifier | Qt.AltModifier)
    
    # Check if handlers were called
    mock_cancel_orders.assert_called_once()
    mock_close_positions.assert_called_once()

def test_theme_switching(main_window):
    """Test theme switching"""
    # Get initial theme
    initial_style = main_window.styleSheet()
    
    # Switch theme
    main_window.switch_theme('dark')
    dark_style = main_window.styleSheet()
    
    main_window.switch_theme('light')
    light_style = main_window.styleSheet()
    
    # Check if styles are different
    assert dark_style != light_style

def test_layout_saving(main_window):
    """Test layout saving and loading"""
    # Save current layout
    main_window.save_layout()
    
    # Modify layout
    main_window.resize(1000, 800)
    
    # Load saved layout
    main_window.load_layout()
    
    # Check if layout was restored
    assert main_window.size().width() == 1280
    assert main_window.size().height() == 800

@pytest.mark.asyncio
async def test_real_time_updates(main_window):
    """Test real-time data updates"""
    # Mock update handlers
    mock_ticker_handler = MagicMock()
    mock_orderbook_handler = MagicMock()
    mock_trade_handler = MagicMock()
    
    # Connect handlers
    main_window.ticker_updated.connect(mock_ticker_handler)
    main_window.orderbook_updated.connect(mock_orderbook_handler)
    main_window.trade_updated.connect(mock_trade_handler)
    
    # Simulate real-time updates
    await main_window.process_ticker_update({'symbol': 'BTC/USD', 'price': 50000})
    await main_window.process_orderbook_update({
        'symbol': 'BTC/USD',
        'bids': [[50000, 1.0]],
        'asks': [[50010, 1.5]]
    })
    await main_window.process_trade_update({
        'symbol': 'BTC/USD',
        'price': 50000,
        'amount': 1.0,
        'side': 'buy'
    })
    
    # Check if handlers were called
    mock_ticker_handler.assert_called_once()
    mock_orderbook_handler.assert_called_once()
    mock_trade_handler.assert_called_once()
