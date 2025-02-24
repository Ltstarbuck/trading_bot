"""
Telegram notification handler
"""

from typing import Any, Dict, List, Optional
import aiohttp
from loguru import logger

from .base import (
    BaseNotificationHandler,
    NotificationPriority,
    NotificationType
)

class TelegramNotificationHandler(BaseNotificationHandler):
    """Telegram notification handler"""
    
    def __init__(
        self,
        bot_token: str,
        chat_ids: List[str],
        min_priority: NotificationPriority = NotificationPriority.NORMAL,
        api_base: str = "https://api.telegram.org"
    ):
        """
        Initialize Telegram handler
        
        Args:
            bot_token: Telegram bot token
            chat_ids: List of chat IDs to send to
            min_priority: Minimum priority level
            api_base: Telegram API base URL
        """
        super().__init__("telegram", min_priority)
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.api_base = api_base
        
    async def send_notification(
        self,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        parse_mode: str = "HTML",
        **kwargs
    ) -> bool:
        """
        Send Telegram notification
        
        Args:
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            parse_mode: Message parse mode
            **kwargs: Additional arguments
            
        Returns:
            True if sent successfully
        """
        try:
            if not self.should_send(priority):
                return False
                
            # Format message
            formatted_message = self.format_message(
                message,
                notification_type,
                **kwargs
            )
            
            # Send to all chats
            success = True
            async with aiohttp.ClientSession() as session:
                for chat_id in self.chat_ids:
                    if not await self._send_message(
                        session,
                        chat_id,
                        formatted_message,
                        parse_mode
                    ):
                        success = False
                        
            return success
            
        except Exception as e:
            logger.error(
                f"Error sending Telegram notification: {str(e)}"
            )
            return False
            
    async def send_batch(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[bool]:
        """
        Send batch of Telegram notifications
        
        Args:
            notifications: List of notification dictionaries
            
        Returns:
            List of success flags
        """
        results = []
        
        try:
            # Group notifications by priority
            priority_groups: Dict[
                NotificationPriority,
                List[Dict]
            ] = {}
            
            for notification in notifications:
                priority = notification.get(
                    'priority',
                    NotificationPriority.NORMAL
                )
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(notification)
                
            # Send notifications by priority
            async with aiohttp.ClientSession() as session:
                for priority in sorted(
                    priority_groups.keys(),
                    key=lambda x: x.value,
                    reverse=True
                ):
                    if not self.should_send(priority):
                        results.extend(
                            [False] * len(priority_groups[priority])
                        )
                        continue
                        
                    # Create combined message
                    messages = []
                    for notification in priority_groups[priority]:
                        message = self.format_message(
                            notification['message'],
                            notification['type'],
                            **notification.get('kwargs', {})
                        )
                        messages.append(message)
                        
                    combined_message = "\n\n".join(messages)
                    
                    # Send to all chats
                    success = True
                    for chat_id in self.chat_ids:
                        if not await self._send_message(
                            session,
                            chat_id,
                            combined_message,
                            "HTML"
                        ):
                            success = False
                            
                    results.extend(
                        [success] * len(priority_groups[priority])
                    )
                    
            return results
            
        except Exception as e:
            logger.error(
                f"Error processing batch Telegram notifications: {str(e)}"
            )
            return [False] * len(notifications)
            
    async def _send_message(
        self,
        session: aiohttp.ClientSession,
        chat_id: str,
        message: str,
        parse_mode: str
    ) -> bool:
        """Send message via Telegram API"""
        try:
            url = f"{self.api_base}/bot{self.bot_token}/sendMessage"
            
            async with session.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode
                }
            ) as response:
                if response.status == 200:
                    logger.info(
                        f"Sent Telegram notification to chat {chat_id}"
                    )
                    return True
                else:
                    logger.error(
                        f"Error sending Telegram notification: "
                        f"Status {response.status}"
                    )
                    return False
                    
        except Exception as e:
            logger.error(
                f"Error sending Telegram message: {str(e)}"
            )
            return False
