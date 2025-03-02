"""
Trading panel component for order creation and management
"""

from typing import Dict, Optional
from decimal import Decimal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QComboBox, QDoubleSpinBox, QPushButton,
                            QFormLayout, QFrame)
from PyQt5.QtCore import pyqtSignal

class TradingPanel(QWidget):
    """Trading panel widget for order creation"""
    
    # Signal emitted when order is submitted
    order_submitted = pyqtSignal(dict)
    
    def __init__(self):
        """Initialize trading panel"""
        super().__init__()
        
        # Initialize state
        self.current_symbol = ""
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components"""
        # Symbol selector
        symbol_layout = QHBoxLayout()
        symbol_label = QLabel("Symbol:")
        self.symbol_selector = QComboBox()
        symbol_layout.addWidget(symbol_label)
        symbol_layout.addWidget(self.symbol_selector)
        self.layout.addLayout(symbol_layout)
        
        # Order type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        self.order_type = QComboBox()
        self.order_type.addItems(["Market", "Limit", "Stop", "Stop Limit"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.order_type)
        self.layout.addLayout(type_layout)
        
        # Side selector
        side_layout = QHBoxLayout()
        side_label = QLabel("Side:")
        self.side = QComboBox()
        self.side.addItems(["Buy", "Sell"])
        side_layout.addWidget(side_label)
        side_layout.addWidget(self.side)
        self.layout.addLayout(side_layout)
        
        # Amount input
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        self.amount = QDoubleSpinBox()
        self.amount.setDecimals(8)
        self.amount.setRange(0, 1000000)
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount)
        self.layout.addLayout(amount_layout)
        
        # Price input
        price_layout = QHBoxLayout()
        price_label = QLabel("Price:")
        self.price = QDoubleSpinBox()
        self.price.setDecimals(2)
        self.price.setRange(0, 1000000)
        price_layout.addWidget(price_label)
        price_layout.addWidget(self.price)
        self.layout.addLayout(price_layout)
        
        # Stop price input (for stop orders)
        stop_price_layout = QHBoxLayout()
        stop_price_label = QLabel("Stop Price:")
        self.stop_price = QDoubleSpinBox()
        self.stop_price.setDecimals(2)
        self.stop_price.setRange(0, 1000000)
        self.stop_price.setEnabled(False)
        stop_price_layout.addWidget(stop_price_label)
        stop_price_layout.addWidget(self.stop_price)
        self.layout.addLayout(stop_price_layout)
        
        # Submit button
        self.submit_button = QPushButton("Submit Order")
        self.submit_button.clicked.connect(self._submit_order)
        self.layout.addWidget(self.submit_button)
        
        # Add stretch to bottom
        self.layout.addStretch()
        
        # Connect signals
        self.order_type.currentTextChanged.connect(self._handle_type_change)
        self.symbol_selector.currentTextChanged.connect(self._handle_symbol_change)
        
    def set_symbols(self, symbols: list):
        """Set available trading symbols"""
        self.symbol_selector.clear()
        self.symbol_selector.addItems(symbols)
        
    def set_current_price(self, price: Decimal):
        """Set current price for the selected symbol"""
        self.price.setValue(float(price))
        
    def _handle_type_change(self, order_type: str):
        """Handle order type changes"""
        # Enable/disable price input based on order type
        self.price.setEnabled(order_type != "Market")
        
        # Enable/disable stop price input for stop orders
        self.stop_price.setEnabled(
            order_type in ["Stop", "Stop Limit"])
        
    def _handle_symbol_change(self, symbol: str):
        """Handle symbol changes"""
        self.current_symbol = symbol
        
    def _submit_order(self):
        """Submit order with current parameters"""
        # Get order parameters
        order = {
            'symbol': self.current_symbol,
            'side': self.side.currentText().lower(),
            'type': self.order_type.currentText().lower(),
            'amount': Decimal(str(self.amount.value()))
        }
        
        # Add price for limit orders
        if order['type'] != 'market':
            order['price'] = Decimal(str(self.price.value()))
            
        # Add stop price for stop orders
        if order['type'] in ['stop', 'stop_limit']:
            order['stop_price'] = Decimal(str(self.stop_price.value()))
            
        # Emit order
        self.order_submitted.emit(order)
        
    def clear_inputs(self):
        """Clear all input fields"""
        self.amount.setValue(0)
        self.price.setValue(0)
        self.stop_price.setValue(0)
        
    def set_order_defaults(self, defaults: Dict):
        """Set default values for order parameters"""
        if 'amount' in defaults:
            self.amount.setValue(float(defaults['amount']))
        if 'price' in defaults:
            self.price.setValue(float(defaults['price']))
            
    def enable_trading(self, enabled: bool):
        """Enable or disable trading"""
        self.submit_button.setEnabled(enabled)
        
    def get_order_details(self) -> Dict:
        """Get current order details"""
        return {
            'symbol': self.current_symbol,
            'side': self.side.currentText().lower(),
            'type': self.order_type.currentText().lower(),
            'amount': Decimal(str(self.amount.value())),
            'price': Decimal(str(self.price.value()))
            if self.price.isEnabled() else None,
            'stop_price': Decimal(str(self.stop_price.value()))
            if self.stop_price.isEnabled() else None
        }
