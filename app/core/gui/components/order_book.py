"""
Order book widget for displaying market depth
"""

from typing import Dict, List
from decimal import Decimal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem,
                            QLabel, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush

class OrderBookWidget(QWidget):
    """Order book widget showing market depth"""
    
    def __init__(self):
        """Initialize order book widget"""
        super().__init__()
        
        # Initialize state
        self.current_symbol = ""
        self.depth = 20  # Number of price levels to show
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components"""
        # Header
        header_layout = QHBoxLayout()
        
        # Symbol label
        self.symbol_label = QLabel("")
        header_layout.addWidget(self.symbol_label)
        
        # Spread label
        self.spread_label = QLabel("Spread: -")
        header_layout.addWidget(self.spread_label)
        
        self.layout.addLayout(header_layout)
        
        # Create tables
        tables_layout = QHBoxLayout()
        
        # Bids table
        self.bids_table = QTableWidget()
        self.bids_table.setColumnCount(3)
        self.bids_table.setHorizontalHeaderLabels(
            ["Price", "Size", "Total"])
        self.bids_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        tables_layout.addWidget(self.bids_table)
        
        # Asks table
        self.asks_table = QTableWidget()
        self.asks_table.setColumnCount(3)
        self.asks_table.setHorizontalHeaderLabels(
            ["Price", "Size", "Total"])
        self.asks_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        tables_layout.addWidget(self.asks_table)
        
        self.layout.addLayout(tables_layout)
        
    def set_symbol(self, symbol: str):
        """Set current trading symbol"""
        self.current_symbol = symbol
        self.symbol_label.setText(symbol)
        
    def update_data(self, data: Dict):
        """Update order book data"""
        # Extract bids and asks
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        # Update tables
        self._update_bids(bids)
        self._update_asks(asks)
        
        # Update spread
        if bids and asks:
            spread = Decimal(asks[0][0]) - Decimal(bids[0][0])
            self.spread_label.setText(
                f"Spread: {spread:.8f}")
            
    def update_best_prices(self, bid: Decimal,
                          ask: Decimal):
        """Update best bid and ask prices"""
        # Update spread
        spread = ask - bid
        self.spread_label.setText(
            f"Spread: {spread:.8f}")
            
        # Highlight best prices
        self._highlight_price(self.bids_table, bid)
        self._highlight_price(self.asks_table, ask)
        
    def set_depth(self, depth: int):
        """Set order book depth"""
        self.depth = depth
        self.bids_table.setRowCount(depth)
        self.asks_table.setRowCount(depth)
        
    def _update_bids(self, bids: List):
        """Update bids table"""
        self.bids_table.setRowCount(min(len(bids), self.depth))
        
        total = Decimal('0')
        for i, (price, size) in enumerate(bids[:self.depth]):
            # Convert to Decimal
            price = Decimal(str(price))
            size = Decimal(str(size))
            total += size
            
            # Create items
            price_item = QTableWidgetItem(f"{price:.8f}")
            size_item = QTableWidgetItem(f"{size:.8f}")
            total_item = QTableWidgetItem(f"{total:.8f}")
            
            # Set items
            self.bids_table.setItem(i, 0, price_item)
            self.bids_table.setItem(i, 1, size_item)
            self.bids_table.setItem(i, 2, total_item)
            
            # Color background
            self._color_row(self.bids_table, i, True)
            
    def _update_asks(self, asks: List):
        """Update asks table"""
        self.asks_table.setRowCount(min(len(asks), self.depth))
        
        total = Decimal('0')
        for i, (price, size) in enumerate(asks[:self.depth]):
            # Convert to Decimal
            price = Decimal(str(price))
            size = Decimal(str(size))
            total += size
            
            # Create items
            price_item = QTableWidgetItem(f"{price:.8f}")
            size_item = QTableWidgetItem(f"{size:.8f}")
            total_item = QTableWidgetItem(f"{total:.8f}")
            
            # Set items
            self.asks_table.setItem(i, 0, price_item)
            self.asks_table.setItem(i, 1, size_item)
            self.asks_table.setItem(i, 2, total_item)
            
            # Color background
            self._color_row(self.asks_table, i, False)
            
    def _color_row(self, table: QTableWidget,
                   row: int, is_bid: bool):
        """Color table row based on bid/ask"""
        color = QColor(200, 255, 200) if is_bid else QColor(255, 200, 200)
        brush = QBrush(color)
        
        for col in range(3):
            item = table.item(row, col)
            if item:
                item.setBackground(brush)
                
    def _highlight_price(self, table: QTableWidget,
                         price: Decimal):
        """Highlight price level in table"""
        for row in range(table.rowCount()):
            price_item = table.item(row, 0)
            if price_item:
                item_price = Decimal(price_item.text())
                if item_price == price:
                    brush = QBrush(QColor(255, 255, 0))
                    price_item.setBackground(brush)
                    break
                    
    def clear(self):
        """Clear order book"""
        self.bids_table.setRowCount(0)
        self.asks_table.setRowCount(0)
        self.spread_label.setText("Spread: -")
        
    def get_best_prices(self) -> Dict:
        """Get best bid and ask prices"""
        best_bid = None
        best_ask = None
        
        if self.bids_table.rowCount() > 0:
            bid_item = self.bids_table.item(0, 0)
            if bid_item:
                best_bid = Decimal(bid_item.text())
                
        if self.asks_table.rowCount() > 0:
            ask_item = self.asks_table.item(0, 0)
            if ask_item:
                best_ask = Decimal(ask_item.text())
                
        return {
            'bid': best_bid,
            'ask': best_ask
        }
