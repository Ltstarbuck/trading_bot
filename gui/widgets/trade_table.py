"""
Trade Table Widget
Displays trading data in a sortable table format
"""

from typing import List, Any
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class TradeTable(QWidget):
    """Widget for displaying trading data in a table format"""
    
    # Signal emitted when a row is selected
    row_selected = pyqtSignal(int)
    
    def __init__(self, headers: List[str], parent: QWidget = None):
        """
        Initialize the trade table
        
        Args:
            headers: List of column headers
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        
        # Set column stretching
        header = self.table.horizontalHeader()
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        header.setStretchLastSection(True)
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
        
    def update_data(self, data: List[List[Any]]) -> None:
        """
        Update table data
        
        Args:
            data: List of rows, where each row is a list of values
        """
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                
                # Color coding for P&L columns
                if "P&L" in self.table.horizontalHeaderItem(col_idx).text():
                    try:
                        pnl = float(str(value).replace("$", "").replace(",", ""))
                        if pnl > 0:
                            item.setForeground(QColor("green"))
                        elif pnl < 0:
                            item.setForeground(QColor("red"))
                    except ValueError:
                        pass
                        
                self.table.setItem(row_idx, col_idx, item)
                
        self.table.setSortingEnabled(True)
        
    def get_selected_row_data(self) -> List[str]:
        """
        Get data from selected row
        
        Returns:
            List of values from selected row or empty list if no selection
        """
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return []
            
        row = selected_rows[0].row()
        return [
            self.table.item(row, col).text()
            for col in range(self.table.columnCount())
        ]
        
    def clear_selection(self) -> None:
        """Clear current selection"""
        self.table.clearSelection()
        
    def _on_selection_changed(self) -> None:
        """Handle row selection change"""
        selected_items = self.table.selectedItems()
        if selected_items:
            self.row_selected.emit(selected_items[0].row())
