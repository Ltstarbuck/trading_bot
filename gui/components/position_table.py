"""
Position table widget for displaying open positions
"""

from typing import Dict, Optional
from decimal import Decimal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem,
                            QPushButton, QLabel, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

class PositionTableWidget(QWidget):
    """Position table showing open positions"""
    
    # Signals
    position_closed = pyqtSignal(str)  # symbol
    stop_loss_changed = pyqtSignal(str, Decimal)  # symbol, price
    take_profit_changed = pyqtSignal(str, Decimal)  # symbol, price
    
    def __init__(self):
        """Initialize position table widget"""
        super().__init__()
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components"""
        # Header
        header_layout = QHBoxLayout()
        
        # Total P&L label
        self.total_pnl_label = QLabel("Total P&L: $0.00")
        header_layout.addWidget(self.total_pnl_label)
        
        # Close all button
        self.close_all_button = QPushButton("Close All")
        self.close_all_button.clicked.connect(self._close_all_positions)
        header_layout.addWidget(self.close_all_button)
        
        self.layout.addLayout(header_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Symbol",
            "Side",
            "Size",
            "Entry Price",
            "Current Price",
            "Stop Loss",
            "Take Profit",
            "P&L",
            "P&L %",
            "Actions"
        ])
        
        # Set column stretch
        header = self.table.horizontalHeader()
        for i in range(10):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
            
        self.layout.addWidget(self.table)
        
    def add_position(self, position: Dict):
        """Add new position to table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Create items
        symbol_item = QTableWidgetItem(position['symbol'])
        side_item = QTableWidgetItem(position['side'].upper())
        size_item = QTableWidgetItem(
            f"{float(position['size']):.8f}")
        entry_price_item = QTableWidgetItem(
            f"{float(position['entry_price']):.8f}")
        current_price_item = QTableWidgetItem(
            f"{float(position['current_price']):.8f}")
        stop_loss_item = QTableWidgetItem(
            f"{float(position['stop_loss']):.8f}"
            if position.get('stop_loss') else "-")
        take_profit_item = QTableWidgetItem(
            f"{float(position['take_profit']):.8f}"
            if position.get('take_profit') else "-")
        
        # Calculate P&L
        entry_price = Decimal(str(position['entry_price']))
        current_price = Decimal(str(position['current_price']))
        size = Decimal(str(position['size']))
        
        pnl = (current_price - entry_price) * size
        if position['side'] == 'sell':
            pnl = -pnl
            
        pnl_pct = (pnl / (entry_price * size)) * 100
        
        pnl_item = QTableWidgetItem(f"${float(pnl):.2f}")
        pnl_pct_item = QTableWidgetItem(f"{float(pnl_pct):.2f}%")
        
        # Color P&L cells
        if pnl > 0:
            pnl_item.setBackground(QBrush(QColor(200, 255, 200)))
            pnl_pct_item.setBackground(QBrush(QColor(200, 255, 200)))
        elif pnl < 0:
            pnl_item.setBackground(QBrush(QColor(255, 200, 200)))
            pnl_pct_item.setBackground(QBrush(QColor(255, 200, 200)))
            
        # Create close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(
            lambda: self._close_position(position['symbol']))
            
        # Set items
        self.table.setItem(row, 0, symbol_item)
        self.table.setItem(row, 1, side_item)
        self.table.setItem(row, 2, size_item)
        self.table.setItem(row, 3, entry_price_item)
        self.table.setItem(row, 4, current_price_item)
        self.table.setItem(row, 5, stop_loss_item)
        self.table.setItem(row, 6, take_profit_item)
        self.table.setItem(row, 7, pnl_item)
        self.table.setItem(row, 8, pnl_pct_item)
        self.table.setCellWidget(row, 9, close_button)
        
        # Update total P&L
        self._update_total_pnl()
        
    def update_position(self, symbol: str,
                       current_price: Decimal):
        """Update position with new price"""
        for row in range(self.table.rowCount()):
            symbol_item = self.table.item(row, 0)
            if symbol_item and symbol_item.text() == symbol:
                # Update current price
                self.table.item(row, 4).setText(
                    f"{float(current_price):.8f}")
                
                # Update P&L
                entry_price = Decimal(
                    self.table.item(row, 3).text())
                size = Decimal(
                    self.table.item(row, 2).text())
                side = self.table.item(row, 1).text().lower()
                
                pnl = (current_price - entry_price) * size
                if side == 'sell':
                    pnl = -pnl
                    
                pnl_pct = (pnl / (entry_price * size)) * 100
                
                pnl_item = self.table.item(row, 7)
                pnl_item.setText(f"${float(pnl):.2f}")
                
                pnl_pct_item = self.table.item(row, 8)
                pnl_pct_item.setText(f"{float(pnl_pct):.2f}%")
                
                # Update colors
                color = QColor(200, 255, 200) if pnl > 0 \
                    else QColor(255, 200, 200)
                pnl_item.setBackground(QBrush(color))
                pnl_pct_item.setBackground(QBrush(color))
                
                break
                
        # Update total P&L
        self._update_total_pnl()
        
    def remove_position(self, symbol: str):
        """Remove position from table"""
        for row in range(self.table.rowCount()):
            symbol_item = self.table.item(row, 0)
            if symbol_item and symbol_item.text() == symbol:
                self.table.removeRow(row)
                break
                
        # Update total P&L
        self._update_total_pnl()
        
    def _close_position(self, symbol: str):
        """Close single position"""
        self.position_closed.emit(symbol)
        
    def _close_all_positions(self):
        """Close all positions"""
        for row in range(self.table.rowCount()):
            symbol = self.table.item(row, 0).text()
            self.position_closed.emit(symbol)
            
    def _update_total_pnl(self):
        """Update total P&L label"""
        total_pnl = Decimal('0')
        
        for row in range(self.table.rowCount()):
            pnl_text = self.table.item(row, 7).text()
            pnl = Decimal(pnl_text.replace('$', ''))
            total_pnl += pnl
            
        self.total_pnl_label.setText(
            f"Total P&L: ${float(total_pnl):.2f}")
            
        # Color label based on P&L
        if total_pnl > 0:
            self.total_pnl_label.setStyleSheet(
                "color: green;")
        elif total_pnl < 0:
            self.total_pnl_label.setStyleSheet(
                "color: red;")
        else:
            self.total_pnl_label.setStyleSheet("")
            
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position details by symbol"""
        for row in range(self.table.rowCount()):
            symbol_item = self.table.item(row, 0)
            if symbol_item and symbol_item.text() == symbol:
                return {
                    'symbol': symbol,
                    'side': self.table.item(row, 1).text().lower(),
                    'size': Decimal(
                        self.table.item(row, 2).text()),
                    'entry_price': Decimal(
                        self.table.item(row, 3).text()),
                    'current_price': Decimal(
                        self.table.item(row, 4).text()),
                    'stop_loss': Decimal(
                        self.table.item(row, 5).text())
                        if self.table.item(row, 5).text() != "-"
                        else None,
                    'take_profit': Decimal(
                        self.table.item(row, 6).text())
                        if self.table.item(row, 6).text() != "-"
                        else None
                }
        return None
