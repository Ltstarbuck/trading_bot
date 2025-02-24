"""
Base notification handler
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from enum import Enum
from loguru import logger

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class NotificationType(Enum):
    """Notification types"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    TRADE = "trade"
    SYSTEM = "system"
    ALERT = "alert"

class BaseNotificationHandler(ABC):
    """Abstract base class for notification handlers"""
    
    def __init__(
        self,
        name: str,
        min_priority: NotificationPriority = NotificationPriority.NORMAL
    ):
        """
        Initialize notification handler
        
        Args:
            name: Handler name
            min_priority: Minimum priority level to process
        """
        self.name = name
        self.min_priority = min_priority
        
    @abstractmethod
    async def send_notification(
        self,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> bool:
        """
        Send notification
        
        Args:
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            **kwargs: Additional arguments
            
        Returns:
            True if sent successfully
        """
        pass
        
    @abstractmethod
    async def send_batch(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[bool]:
        """
        Send batch of notifications
        
        Args:
            notifications: List of notification dictionaries
            
        Returns:
            List of success flags
        """
        pass
        
    def should_send(
        self,
        priority: NotificationPriority
    ) -> bool:
        """Check if notification should be sent"""
        return priority.value >= self.min_priority.value
        
    def format_message(
        self,
        message: str,
        notification_type: NotificationType,
        **kwargs
    ) -> str:
        """Format notification message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add metadata
        metadata = {
            "timestamp": timestamp,
            "type": notification_type.value,
            **kwargs
        }
        
        # Format message
        formatted = f"[{timestamp}] {notification_type.value.upper()}: {message}"
        
        # Add metadata as JSON if present
        if kwargs:
            formatted += f"\nMetadata: {json.dumps(metadata, indent=2)}"
            
        return formatted
