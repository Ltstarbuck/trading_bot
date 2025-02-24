"""
Theme management
"""

from typing import Dict, Optional
from enum import Enum
from PyQt6.QtWidgets import QApplication
from .dark_theme import DARK_THEME, DARK_STYLESHEET
from .light_theme import LIGHT_THEME, LIGHT_STYLESHEET

class Theme(Enum):
    """Available themes"""
    DARK = 'dark'
    LIGHT = 'light'

class ThemeManager:
    """Manages application theming"""
    
    def __init__(self):
        """Initialize theme manager"""
        self._current_theme = Theme.DARK
        self._themes = {
            Theme.DARK: (DARK_THEME, DARK_STYLESHEET),
            Theme.LIGHT: (LIGHT_THEME, LIGHT_STYLESHEET)
        }
        
    @property
    def current_theme(self) -> Theme:
        """Get current theme"""
        return self._current_theme
        
    @property
    def theme_colors(self) -> Dict:
        """Get current theme colors"""
        return self._themes[self._current_theme][0]
        
    @property
    def stylesheet(self) -> str:
        """Get current theme stylesheet"""
        return self._themes[self._current_theme][1]
        
    def set_theme(self, theme: Theme) -> None:
        """
        Set application theme
        
        Args:
            theme: Theme to set
        """
        if theme not in Theme:
            raise ValueError(f"Invalid theme: {theme}")
            
        self._current_theme = theme
        
        # Update application stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.stylesheet)
            
    def get_color(self, color_name: str) -> Optional[str]:
        """
        Get color from current theme
        
        Args:
            color_name: Name of color
            
        Returns:
            Color value or None if not found
        """
        return self.theme_colors.get(color_name)
        
    def is_dark_theme(self) -> bool:
        """Check if dark theme is active"""
        return self._current_theme == Theme.DARK
