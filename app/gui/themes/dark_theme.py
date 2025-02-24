"""
Dark theme styling
"""

DARK_THEME = {
    # Main colors
    'primary': '#1976D2',
    'secondary': '#424242',
    'accent': '#82B1FF',
    'error': '#FF5252',
    'warning': '#FFC107',
    'success': '#4CAF50',
    
    # Background colors
    'background': '#121212',
    'surface': '#1E1E1E',
    'card': '#242424',
    'dialog': '#2D2D2D',
    
    # Text colors
    'text_primary': '#FFFFFF',
    'text_secondary': 'rgba(255, 255, 255, 0.7)',
    'text_disabled': 'rgba(255, 255, 255, 0.5)',
    'text_hint': 'rgba(255, 255, 255, 0.5)',
    
    # Border colors
    'border': 'rgba(255, 255, 255, 0.12)',
    'divider': 'rgba(255, 255, 255, 0.12)',
    
    # Chart colors
    'chart_up': '#00C853',
    'chart_down': '#FF1744',
    'chart_grid': 'rgba(255, 255, 255, 0.1)',
    'chart_text': 'rgba(255, 255, 255, 0.7)',
    
    # Trading specific
    'profit': '#00C853',
    'loss': '#FF1744',
    'neutral': '#9E9E9E',
    
    # Gradients
    'gradient_primary': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2196F3, stop:1 #1976D2)',
    'gradient_success': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66BB6A, stop:1 #4CAF50)',
    'gradient_error': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF5252, stop:1 #F44336)',
}

DARK_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: %(background)s;
    color: %(text_primary)s;
}

/* Menu Bar */
QMenuBar {
    background-color: %(surface)s;
    color: %(text_primary)s;
    border-bottom: 1px solid %(border)s;
}

QMenuBar::item:selected {
    background-color: %(primary)s;
}

/* Menu */
QMenu {
    background-color: %(surface)s;
    color: %(text_primary)s;
    border: 1px solid %(border)s;
}

QMenu::item:selected {
    background-color: %(primary)s;
}

/* Push Button */
QPushButton {
    background-color: %(primary)s;
    color: %(text_primary)s;
    border: none;
    padding: 5px 15px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: %(accent)s;
}

QPushButton:pressed {
    background-color: %(secondary)s;
}

QPushButton:disabled {
    background-color: %(secondary)s;
    color: %(text_disabled)s;
}

/* Line Edit */
QLineEdit {
    background-color: %(surface)s;
    color: %(text_primary)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 5px;
}

QLineEdit:focus {
    border: 2px solid %(primary)s;
}

/* Combo Box */
QComboBox {
    background-color: %(surface)s;
    color: %(text_primary)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 5px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(resources/icons/down_arrow.png);
    width: 12px;
    height: 12px;
}

/* Table Widget */
QTableWidget {
    background-color: %(surface)s;
    color: %(text_primary)s;
    gridline-color: %(border)s;
    border: none;
}

QTableWidget::item:selected {
    background-color: %(primary)s;
}

QHeaderView::section {
    background-color: %(card)s;
    color: %(text_primary)s;
    border: none;
    padding: 5px;
}

/* Scroll Bar */
QScrollBar:vertical {
    background-color: %(surface)s;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: %(secondary)s;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: %(primary)s;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid %(border)s;
    background-color: %(surface)s;
}

QTabBar::tab {
    background-color: %(surface)s;
    color: %(text_primary)s;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: %(primary)s;
}

/* Group Box */
QGroupBox {
    background-color: %(surface)s;
    color: %(text_primary)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    margin-top: 1em;
}

QGroupBox::title {
    color: %(text_primary)s;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
}

/* Progress Bar */
QProgressBar {
    background-color: %(surface)s;
    color: %(text_primary)s;
    border: none;
    border-radius: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: %(primary)s;
    border-radius: 4px;
}
""" % DARK_THEME
