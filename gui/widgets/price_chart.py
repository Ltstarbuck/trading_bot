"""
Price Chart Widget
Interactive price chart using Plotly
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal

class PriceChart(QWidget):
    """Interactive price chart widget"""
    
    # Signals
    timeframe_changed = pyqtSignal(str)
    symbol_changed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize price chart widget"""
        super().__init__(parent)
        
        # Initialize variables
        self.current_symbol = ""
        self.current_timeframe = "1h"
        self.data: List[Dict] = []
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Symbol selector
        self.symbol_selector = QComboBox()
        self.symbol_selector.currentTextChanged.connect(self._on_symbol_changed)
        controls_layout.addWidget(self.symbol_selector)
        
        # Timeframe selector
        self.timeframe_selector = QComboBox()
        self.timeframe_selector.addItems(["1m", "5m", "15m", "1h", "4h", "1d"])
        self.timeframe_selector.setCurrentText("1h")
        self.timeframe_selector.currentTextChanged.connect(self._on_timeframe_changed)
        controls_layout.addWidget(self.timeframe_selector)
        
        # Indicators
        self.indicator_selector = QComboBox()
        self.indicator_selector.addItems(["None", "MA", "EMA", "RSI", "MACD"])
        self.indicator_selector.currentTextChanged.connect(self._on_indicator_changed)
        controls_layout.addWidget(self.indicator_selector)
        
        layout.addLayout(controls_layout)
        
        # Create web view for Plotly
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Initialize empty chart
        self._create_empty_chart()
        
    def update_data(
        self,
        ohlcv_data: List[Dict],
        symbol: str,
        positions: Optional[List[Dict]] = None
    ) -> None:
        """
        Update chart with new data
        
        Args:
            ohlcv_data: List of OHLCV candle data
            symbol: Trading pair symbol
            positions: Optional list of position entry/exit points
        """
        self.data = ohlcv_data
        self.current_symbol = symbol
        
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3]
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=[d['timestamp'] for d in ohlcv_data],
                open=[d['open'] for d in ohlcv_data],
                high=[d['high'] for d in ohlcv_data],
                low=[d['low'] for d in ohlcv_data],
                close=[d['close'] for d in ohlcv_data],
                name="OHLCV"
            ),
            row=1, col=1
        )
        
        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=[d['timestamp'] for d in ohlcv_data],
                y=[d['volume'] for d in ohlcv_data],
                name="Volume"
            ),
            row=2, col=1
        )
        
        # Add position markers if provided
        if positions:
            for pos in positions:
                # Entry point
                fig.add_trace(
                    go.Scatter(
                        x=[pos['entry_time']],
                        y=[pos['entry_price']],
                        mode='markers',
                        marker=dict(
                            symbol='triangle-up' if pos['side'] == 'long' else 'triangle-down',
                            size=12,
                            color='green' if pos['side'] == 'long' else 'red'
                        ),
                        name=f"{pos['side'].capitalize()} Entry"
                    ),
                    row=1, col=1
                )
                
                # Exit point if position is closed
                if pos.get('exit_time'):
                    fig.add_trace(
                        go.Scatter(
                            x=[pos['exit_time']],
                            y=[pos['exit_price']],
                            mode='markers',
                            marker=dict(
                                symbol='x',
                                size=12,
                                color='red' if pos['side'] == 'long' else 'green'
                            ),
                            name=f"{pos['side'].capitalize()} Exit"
                        ),
                        row=1, col=1
                    )
                    
        # Update layout
        fig.update_layout(
            title=f"{symbol} - {self.current_timeframe}",
            xaxis_title="Time",
            yaxis_title="Price",
            yaxis2_title="Volume",
            showlegend=True,
            height=600,
            xaxis_rangeslider_visible=False
        )
        
        # Make it interactive
        fig.update_layout(hovermode='x unified')
        
        # Convert to HTML and display
        html = fig.to_html(include_plotlyjs='cdn')
        self.web_view.setHtml(html)
        
    def update_symbols(self, symbols: List[str]) -> None:
        """Update available symbols"""
        current = self.symbol_selector.currentText()
        self.symbol_selector.clear()
        self.symbol_selector.addItems(symbols)
        
        # Restore previous selection if still available
        if current in symbols:
            self.symbol_selector.setCurrentText(current)
            
    def _create_empty_chart(self) -> None:
        """Create empty chart"""
        fig = go.Figure()
        fig.update_layout(
            title="No data available",
            xaxis_title="Time",
            yaxis_title="Price",
            height=600
        )
        html = fig.to_html(include_plotlyjs='cdn')
        self.web_view.setHtml(html)
        
    def _on_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change"""
        self.current_symbol = symbol
        self.symbol_changed.emit(symbol)
        
    def _on_timeframe_changed(self, timeframe: str) -> None:
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        
    def _on_indicator_changed(self, indicator: str) -> None:
        """Handle indicator change"""
        if not self.data:
            return
            
        # Recalculate indicators and update chart
        self.update_data(self.data, self.current_symbol)
