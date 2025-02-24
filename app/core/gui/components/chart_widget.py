"""
Chart widget for displaying price data and technical indicators
"""

from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
import pyqtgraph as pg
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QComboBox, QPushButton, QLabel)
from PyQt5.QtCore import Qt

class ChartWidget(QWidget):
    """Interactive chart widget for price visualization"""
    
    def __init__(self):
        """Initialize chart widget"""
        super().__init__()
        
        # Initialize state
        self.current_symbol = ""
        self.current_timeframe = "1m"
        self.indicators = {}
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components"""
        # Controls
        controls_layout = QHBoxLayout()
        
        # Timeframe selector
        timeframe_label = QLabel("Timeframe:")
        self.timeframe_selector = QComboBox()
        self.timeframe_selector.addItems(
            ["1m", "5m", "15m", "1h", "4h", "1d"])
        controls_layout.addWidget(timeframe_label)
        controls_layout.addWidget(self.timeframe_selector)
        
        # Chart type selector
        type_label = QLabel("Type:")
        self.chart_type = QComboBox()
        self.chart_type.addItems(
            ["Line", "Area"])
        controls_layout.addWidget(type_label)
        controls_layout.addWidget(self.chart_type)
        
        # Add indicator button
        self.add_indicator = QPushButton("Add Indicator")
        controls_layout.addWidget(self.add_indicator)
        
        # Add stretch to right
        controls_layout.addStretch()
        
        self.layout.addLayout(controls_layout)
        
        # Create chart
        self.chart = pg.PlotWidget()
        self.chart.showGrid(x=True, y=True)
        self.chart.setBackground('w')
        self.layout.addWidget(self.chart)
        
        # Create price series
        self.price_series = pg.PlotDataItem(pen='b')
        self.chart.addItem(self.price_series)
        
        # Create volume bars
        self.volume_axis = pg.ViewBox()
        self.chart.scene().addItem(self.volume_axis)
        self.volume_bars = pg.BarGraphItem(x0=[0], width=0.8, height=[0])
        self.volume_axis.addItem(self.volume_bars)
        
        # Connect signals
        self.timeframe_selector.currentTextChanged.connect(
            self._handle_timeframe_change)
        self.chart_type.currentTextChanged.connect(
            self._handle_type_change)
        self.add_indicator.clicked.connect(
            self._add_indicator_dialog)
            
    def set_data(self, data: List[Dict]):
        """Set chart data"""
        # Extract OHLCV data
        timestamps = [d['timestamp'] for d in data]
        opens = [float(d['open']) for d in data]
        highs = [float(d['high']) for d in data]
        lows = [float(d['low']) for d in data]
        closes = [float(d['close']) for d in data]
        volumes = [float(d['volume']) for d in data]
        
        # Update line series
        if self.chart_type.currentText() in ["Line", "Area"]:
            self.price_series.setData(
                x=timestamps,
                y=closes
            )
            
        # Update volume bars
        self.volume_bars.setOpts(
            x0=timestamps,
            height=volumes,
            width=0.8
        )
        
        # Update indicators
        self._update_indicators(data)
        
    def update_price(self, price: Decimal,
                    timestamp: datetime):
        """Update latest price"""
        # Add price to series
        self.price_series.setData(
            x=self.price_series.xData + [timestamp.timestamp()],
            y=self.price_series.yData + [float(price)]
        )
        
    def add_trade(self, price: Decimal,
                  amount: Decimal,
                  side: str,
                  timestamp: datetime):
        """Add trade marker to chart"""
        # Create scatter point
        color = 'g' if side == 'buy' else 'r'
        scatter = pg.ScatterPlotItem(
            x=[timestamp.timestamp()],
            y=[float(price)],
            symbol='o',
            pen=color,
            brush=color
        )
        self.chart.addItem(scatter)
        
    def add_indicator(self, name: str,
                     indicator_type: str,
                     params: Dict):
        """Add technical indicator"""
        # Create indicator
        indicator = self._create_indicator(
            indicator_type, params)
            
        # Add to chart
        self.indicators[name] = indicator
        self.chart.addItem(indicator)
        
    def remove_indicator(self, name: str):
        """Remove technical indicator"""
        if name in self.indicators:
            self.chart.removeItem(self.indicators[name])
            del self.indicators[name]
            
    def _handle_timeframe_change(self, timeframe: str):
        """Handle timeframe changes"""
        self.current_timeframe = timeframe
        # Emit signal to request new data
        
    def _handle_type_change(self, chart_type: str):
        """Handle chart type changes"""
        # Show/hide components based on type
        self.price_series.setVisible(
            chart_type in ["Line", "Area"])
            
    def _add_indicator_dialog(self):
        """Show dialog to add indicator"""
        # TODO: Implement indicator dialog
        pass
        
    def _create_indicator(self, indicator_type: str,
                         params: Dict) -> pg.PlotDataItem:
        """Create technical indicator"""
        if indicator_type == "MA":
            return self._create_moving_average(params)
        elif indicator_type == "BB":
            return self._create_bollinger_bands(params)
        elif indicator_type == "RSI":
            return self._create_rsi(params)
            
    def _create_moving_average(self,
                             params: Dict) -> pg.PlotDataItem:
        """Create moving average indicator"""
        return pg.PlotDataItem(pen='r')
        
    def _create_bollinger_bands(self,
                              params: Dict) -> pg.PlotDataItem:
        """Create Bollinger Bands indicator"""
        return pg.PlotDataItem(pen='g')
        
    def _create_rsi(self,
                    params: Dict) -> pg.PlotDataItem:
        """Create RSI indicator"""
        return pg.PlotDataItem(pen='b')
        
    def _update_indicators(self, data: List[Dict]):
        """Update all indicators with new data"""
        for name, indicator in self.indicators.items():
            # Calculate and update indicator values
            pass
