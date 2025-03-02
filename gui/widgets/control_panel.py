"""
Control Panel Widget
Bottom panel containing trading controls and settings
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from ..config import ConfigManager

class ControlPanel(QWidget):
    """Control panel for trading settings"""
    
    # Signals for settings changes
    strategy_changed = pyqtSignal(str)
    security_type_changed = pyqtSignal(str)
    position_limit_changed = pyqtSignal(int)
    investment_limit_changed = pyqtSignal(float)
    stop_loss_changed = pyqtSignal(float)
    
    def __init__(self, config: ConfigManager, parent: Optional[QWidget] = None):
        """Initialize control panel"""
        super().__init__(parent)
        
        self.config = config
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # Strategy section
        strategy_group = self._create_group("Strategy")
        strategy_layout = QVBoxLayout(strategy_group)
        
        self.strategy_selector = QComboBox()
        self.strategy_selector.addItems([
            "Volatility Based",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Custom"
        ])
        self.strategy_selector.currentTextChanged.connect(
            lambda x: self.strategy_changed.emit(x)
        )
        strategy_layout.addWidget(self.strategy_selector)
        
        layout.addWidget(strategy_group)
        
        # Security type section
        security_group = self._create_group("Security Type")
        security_layout = QVBoxLayout(security_group)
        
        self.security_selector = QComboBox()
        self.security_selector.addItems([
            "Cryptocurrency",
            "Stocks",
            "Futures"
        ])
        self.security_selector.currentTextChanged.connect(
            lambda x: self.security_type_changed.emit(x)
        )
        security_layout.addWidget(self.security_selector)
        
        layout.addWidget(security_group)
        
        # Position limits section
        position_group = self._create_group("Position Limits")
        position_layout = QVBoxLayout(position_group)
        
        # Number of positions
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Max Positions:"))
        self.position_spin = QSpinBox()
        self.position_spin.setRange(1, 20)
        self.position_spin.setValue(5)
        self.position_spin.valueChanged.connect(
            lambda x: self.position_limit_changed.emit(x)
        )
        pos_layout.addWidget(self.position_spin)
        position_layout.addLayout(pos_layout)
        
        # Investment per position
        inv_layout = QHBoxLayout()
        inv_layout.addWidget(QLabel("Max Investment:"))
        self.investment_spin = QDoubleSpinBox()
        self.investment_spin.setRange(0, 1000000)
        self.investment_spin.setValue(1000)
        self.investment_spin.setPrefix("$")
        self.investment_spin.valueChanged.connect(
            lambda x: self.investment_limit_changed.emit(x)
        )
        inv_layout.addWidget(self.investment_spin)
        position_layout.addLayout(inv_layout)
        
        layout.addWidget(position_group)
        
        # Risk management section
        risk_group = self._create_group("Risk Management")
        risk_layout = QVBoxLayout(risk_group)
        
        # Stop loss
        stop_layout = QHBoxLayout()
        stop_layout.addWidget(QLabel("Stop Loss:"))
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(0.1, 20)
        self.stop_loss_spin.setValue(2)
        self.stop_loss_spin.setSuffix("%")
        self.stop_loss_spin.valueChanged.connect(
            lambda x: self.stop_loss_changed.emit(x)
        )
        stop_layout.addWidget(self.stop_loss_spin)
        risk_layout.addLayout(stop_layout)
        
        # Trailing stop
        trail_layout = QHBoxLayout()
        trail_layout.addWidget(QLabel("Trailing Stop:"))
        self.trailing_stop_spin = QDoubleSpinBox()
        self.trailing_stop_spin.setRange(0.1, 10)
        self.trailing_stop_spin.setValue(1)
        self.trailing_stop_spin.setSuffix("%")
        trail_layout.addWidget(self.trailing_stop_spin)
        risk_layout.addLayout(trail_layout)
        
        layout.addWidget(risk_group)
        
        # Action buttons section
        action_group = self._create_group("Actions")
        action_layout = QVBoxLayout(action_group)
        
        self.pause_button = QPushButton("Pause Trading")
        self.pause_button.setCheckable(True)
        action_layout.addWidget(self.pause_button)
        
        self.emergency_button = QPushButton("Emergency Stop")
        self.emergency_button.setStyleSheet("background-color: red; color: white;")
        action_layout.addWidget(self.emergency_button)
        
        layout.addWidget(action_group)
        
        # Load initial values from config
        self._load_config()
        
        # Connect action buttons
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.emergency_button.clicked.connect(self._on_emergency_clicked)
        
    def _create_group(self, title: str) -> QFrame:
        """Create a styled group frame"""
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        group.setLineWidth(1)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)
        
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        return group
        
    def _load_config(self) -> None:
        """Load values from config"""
        config = self.config.get_config()
        
        # Set values from config
        self.position_spin.setValue(config.trading.max_positions)
        self.stop_loss_spin.setValue(config.trading.stop_loss_percent * 100)
        self.trailing_stop_spin.setValue(config.trading.trailing_stop_percent * 100)
        
    def _on_pause_clicked(self, checked: bool) -> None:
        """Handle pause button click"""
        if checked:
            self.pause_button.setText("Resume Trading")
        else:
            self.pause_button.setText("Pause Trading")
            
    def _on_emergency_clicked(self) -> None:
        """Handle emergency stop button click"""
        # Implement emergency stop logic here
        pass
        
    def get_settings(self) -> dict:
        """Get current control panel settings"""
        return {
            'strategy': self.strategy_selector.currentText(),
            'security_type': self.security_selector.currentText(),
            'max_positions': self.position_spin.value(),
            'max_investment': self.investment_spin.value(),
            'stop_loss': self.stop_loss_spin.value(),
            'trailing_stop': self.trailing_stop_spin.value(),
            'is_paused': self.pause_button.isChecked()
        }
