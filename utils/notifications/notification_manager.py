"""
Notification manager for handling multiple notification channels
"""

from typing import Any, Dict, List, Optional, Type
import asyncio
from loguru import logger

from .base import (
    BaseNotificationHandler,
    NotificationPriority,
    NotificationType
)
from .email_handler import EmailNotificationHandler
from .telegram_handler import TelegramNotificationHandler

class NotificationManager:
    """
    Manages multiple notification handlers and coordinates
    notification delivery across channels
    """
    
    def __init__(self):
        """Initialize notification manager"""
        self.handlers: Dict[str, BaseNotificationHandler] = {}
        
    def add_handler(
        self,
        handler: BaseNotificationHandler
    ) -> None:
        """
        Add notification handler
        
        Args:
            handler: Notification handler instance
        """
        self.handlers[handler.name] = handler
        logger.info(f"Added notification handler: {handler.name}")
        
    def remove_handler(self, name: str) -> None:
        """
        Remove notification handler
        
        Args:
            name: Handler name
        """
        if name in self.handlers:
            del self.handlers[name]
            logger.info(f"Removed notification handler: {name}")
            
    async def notify(
        self,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        handlers: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, bool]:
        """
        Send notification through specified handlers
        
        Args:
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            handlers: List of handler names (None for all)
            **kwargs: Additional arguments
            
        Returns:
            Dictionary of handler names and success flags
        """
        results = {}
        
        try:
            # Get handlers to use
            target_handlers = (
                [
                    h for name, h in self.handlers.items()
                    if name in handlers
                ]
                if handlers
                else list(self.handlers.values())
            )
            
            # Send notifications concurrently
            tasks = [
                handler.send_notification(
                    message,
                    notification_type,
                    priority,
                    **kwargs
                )
                for handler in target_handlers
            ]
            
            if tasks:
                results_list = await asyncio.gather(
                    *tasks,
                    return_exceptions=True
                )
                
                # Process results
                for handler, result in zip(
                    target_handlers,
                    results_list
                ):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Error in handler {handler.name}: {str(result)}"
                        )
                        results[handler.name] = False
                    else:
                        results[handler.name] = result
                        
            return results
            
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
            return {
                handler.name: False
                for handler in target_handlers
            }
            
    async def notify_batch(
        self,
        notifications: List[Dict[str, Any]],
        handlers: Optional[List[str]] = None
    ) -> Dict[str, List[bool]]:
        """
        Send batch of notifications
        
        Args:
            notifications: List of notification dictionaries
            handlers: List of handler names (None for all)
            
        Returns:
            Dictionary of handler names and lists of success flags
        """
        results = {}
        
        try:
            # Get handlers to use
            target_handlers = (
                [
                    h for name, h in self.handlers.items()
                    if name in handlers
                ]
                if handlers
                else list(self.handlers.values())
            )
            
            # Send notifications concurrently
            tasks = [
                handler.send_batch(notifications)
                for handler in target_handlers
            ]
            
            if tasks:
                results_list = await asyncio.gather(
                    *tasks,
                    return_exceptions=True
                )
                
                # Process results
                for handler, result in zip(
                    target_handlers,
                    results_list
                ):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Error in handler {handler.name}: {str(result)}"
                        )
                        results[handler.name] = [False] * len(notifications)
                    else:
                        results[handler.name] = result
                        
            return results
            
        except Exception as e:
            logger.error(f"Error sending batch notifications: {str(e)}")
            return {
                handler.name: [False] * len(notifications)
                for handler in target_handlers
            }
            
    def get_handler(
        self,
        name: str
    ) -> Optional[BaseNotificationHandler]:
        """
        Get notification handler by name
        
        Args:
            name: Handler name
            
        Returns:
            Handler instance if found
        """
        return self.handlers.get(name)
        
    def get_handlers(
        self,
        handler_type: Optional[Type[BaseNotificationHandler]] = None
    ) -> List[BaseNotificationHandler]:
        """
        Get all handlers of specified type
        
        Args:
            handler_type: Handler type to filter by
            
        Returns:
            List of handler instances
        """
        if handler_type:
            return [
                h for h in self.handlers.values()
                if isinstance(h, handler_type)
            ]
        return list(self.handlers.values())
