"""
Email notification handler
"""

from typing import Any, Dict, List, Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

from .base import (
    BaseNotificationHandler,
    NotificationPriority,
    NotificationType
)

class EmailNotificationHandler(BaseNotificationHandler):
    """Email notification handler"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True,
        min_priority: NotificationPriority = NotificationPriority.NORMAL
    ):
        """
        Initialize email handler
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: Sender email
            to_emails: List of recipient emails
            use_tls: Whether to use TLS
            min_priority: Minimum priority level
        """
        super().__init__("email", min_priority)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls
        
    async def send_notification(
        self,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        subject: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send email notification
        
        Args:
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            subject: Email subject
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
            
            # Create email
            email = self._create_email(
                formatted_message,
                subject or f"{notification_type.value.upper()} Notification"
            )
            
            # Send email
            await self._send_email(email)
            
            logger.info(
                f"Sent email notification to {', '.join(self.to_emails)}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
            
    async def send_batch(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[bool]:
        """
        Send batch of email notifications
        
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
                
                # Create and send email
                email = self._create_email(
                    combined_message,
                    f"Batch Notifications - Priority {priority.name}"
                )
                
                try:
                    await self._send_email(email)
                    results.extend(
                        [True] * len(priority_groups[priority])
                    )
                    logger.info(
                        f"Sent batch email notification to "
                        f"{', '.join(self.to_emails)}"
                    )
                except Exception as e:
                    results.extend(
                        [False] * len(priority_groups[priority])
                    )
                    logger.error(
                        f"Error sending batch email notification: {str(e)}"
                    )
                    
            return results
            
        except Exception as e:
            logger.error(
                f"Error processing batch email notifications: {str(e)}"
            )
            return [False] * len(notifications)
            
    def _create_email(
        self,
        message: str,
        subject: str
    ) -> MIMEMultipart:
        """Create email message"""
        email = MIMEMultipart()
        email['From'] = self.from_email
        email['To'] = ', '.join(self.to_emails)
        email['Subject'] = subject
        
        # Add message body
        email.attach(MIMEText(message, 'plain'))
        
        return email
        
    async def _send_email(self, email: MIMEMultipart) -> None:
        """Send email via SMTP"""
        async with aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            use_tls=self.use_tls
        ) as smtp:
            await smtp.login(self.username, self.password)
            await smtp.send_message(email)
