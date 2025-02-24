"""
Notifications package
"""

from .base import (
    BaseNotificationHandler,
    NotificationPriority,
    NotificationType
)
from .email_handler import EmailNotificationHandler
from .telegram_handler import TelegramNotificationHandler
from .sound import SoundNotificationHandler, SoundType
from .visual import (
    VisualNotificationHandler,
    ToastPosition,
    ToastStyle
)
from .notification_manager import NotificationManager

__all__ = [
    'BaseNotificationHandler',
    'NotificationPriority',
    'NotificationType',
    'EmailNotificationHandler',
    'TelegramNotificationHandler',
    'SoundNotificationHandler',
    'SoundType',
    'VisualNotificationHandler',
    'ToastPosition',
    'ToastStyle',
    'NotificationManager'
]
