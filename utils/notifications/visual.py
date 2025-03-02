"""
Visual notification handler for desktop notifications and toast messages
"""

from typing import Any, Dict, List, Optional, Union
import os
import asyncio
from enum import Enum
import win32gui
import win32con
import win32api
from win32api import GetSystemMetrics
import win10toast
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import tempfile
from loguru import logger

from .base import (
    BaseNotificationHandler,
    NotificationPriority,
    NotificationType
)

class ToastPosition(Enum):
    """Toast notification positions"""
    TOP_RIGHT = "top_right"
    TOP_LEFT = "top_left"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    CENTER = "center"

class ToastStyle(Enum):
    """Toast notification styles"""
    DEFAULT = "default"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class VisualNotificationHandler(BaseNotificationHandler):
    """Visual notification handler"""
    
    def __init__(
        self,
        app_name: str = "Trading Bot",
        icon_path: Optional[str] = None,
        min_priority: NotificationPriority = NotificationPriority.NORMAL,
        default_duration: int = 5,  # seconds
        default_position: ToastPosition = ToastPosition.TOP_RIGHT,
        max_queue_size: int = 10,
        font_path: Optional[str] = None
    ):
        """
        Initialize visual handler
        
        Args:
            app_name: Application name
            icon_path: Path to notification icon
            min_priority: Minimum priority level
            default_duration: Default notification duration
            default_position: Default notification position
            max_queue_size: Maximum notification queue size
            font_path: Path to custom font
        """
        super().__init__("visual", min_priority)
        self.app_name = app_name
        self.icon_path = icon_path
        self.default_duration = default_duration
        self.default_position = default_position
        
        # Initialize notification queue
        self.notification_queue: asyncio.Queue = asyncio.Queue(
            maxsize=max_queue_size
        )
        
        # Initialize toast notifier
        self.toaster = win10toast.ToastNotifier()
        
        # Initialize style mapping
        self.style_mapping = {
            NotificationType.ALERT: ToastStyle.WARNING,
            NotificationType.ERROR: ToastStyle.ERROR,
            NotificationType.INFO: ToastStyle.INFO,
            NotificationType.WARNING: ToastStyle.WARNING,
            NotificationType.TRADE: ToastStyle.SUCCESS,
            NotificationType.SYSTEM: ToastStyle.DEFAULT
        }
        
        # Load font
        self.font_path = font_path or os.path.join(
            os.environ.get('WINDIR', ''),
            'Fonts',
            'segoeui.ttf'
        )
        
        # Initialize display task
        self.display_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Track active notifications
        self.active_notifications: Dict[int, Dict] = {}
        self.next_notification_id = 1
        
    async def start(self) -> None:
        """Start notification display"""
        if self.running:
            return
            
        self.running = True
        self.display_task = asyncio.create_task(
            self._notification_display()
        )
        logger.info("Visual notification handler started")
        
    async def stop(self) -> None:
        """Stop notification display"""
        if not self.running:
            return
            
        self.running = False
        if self.display_task:
            self.display_task.cancel()
            try:
                await self.display_task
            except asyncio.CancelledError:
                pass
                
        # Clear active notifications
        for notification_id in list(self.active_notifications.keys()):
            self._remove_notification(notification_id)
            
        logger.info("Visual notification handler stopped")
        
    async def send_notification(
        self,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        title: Optional[str] = None,
        duration: Optional[int] = None,
        position: Optional[ToastPosition] = None,
        style: Optional[ToastStyle] = None,
        icon: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send visual notification
        
        Args:
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            title: Notification title
            duration: Display duration
            position: Display position
            style: Toast style
            icon: Custom icon path
            **kwargs: Additional arguments
            
        Returns:
            True if queued successfully
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
            
            # Queue notification
            try:
                await self.notification_queue.put({
                    'message': formatted_message,
                    'title': title or self.app_name,
                    'duration': duration or self.default_duration,
                    'position': position or self.default_position,
                    'style': style or self.style_mapping[notification_type],
                    'icon': icon or self.icon_path,
                    'priority': priority,
                    'timestamp': datetime.now()
                })
                return True
                
            except asyncio.QueueFull:
                logger.warning("Notification queue is full")
                return False
                
        except Exception as e:
            logger.error(f"Error sending visual notification: {str(e)}")
            return False
            
    async def send_batch(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[bool]:
        """
        Send batch of visual notifications
        
        Args:
            notifications: List of notification dictionaries
            
        Returns:
            List of success flags
        """
        results = []
        
        try:
            # Process notifications in order
            for notification in notifications:
                success = await self.send_notification(
                    notification['message'],
                    notification['type'],
                    notification.get(
                        'priority',
                        NotificationPriority.NORMAL
                    ),
                    **notification.get('kwargs', {})
                )
                results.append(success)
                
            return results
            
        except Exception as e:
            logger.error(
                f"Error processing batch visual notifications: {str(e)}"
            )
            return [False] * len(notifications)
            
    async def _notification_display(self) -> None:
        """Notification display loop"""
        try:
            while self.running:
                try:
                    # Get next notification
                    notification = await self.notification_queue.get()
                    
                    # Display notification
                    await self._display_notification(notification)
                    
                    self.notification_queue.task_done()
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error displaying notification: {str(e)}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error in notification display: {str(e)}")
            
    async def _display_notification(
        self,
        notification: Dict[str, Any]
    ) -> None:
        """
        Display notification
        
        Args:
            notification: Notification data
        """
        try:
            # Get notification ID
            notification_id = self.next_notification_id
            self.next_notification_id += 1
            
            # Create notification window
            notification['window'] = self._create_notification_window(
                notification_id,
                notification
            )
            
            # Store active notification
            self.active_notifications[notification_id] = notification
            
            # Schedule removal
            asyncio.create_task(
                self._schedule_notification_removal(
                    notification_id,
                    notification['duration']
                )
            )
            
        except Exception as e:
            logger.error(f"Error displaying notification: {str(e)}")
            
    def _create_notification_window(
        self,
        notification_id: int,
        notification: Dict[str, Any]
    ) -> int:
        """
        Create notification window
        
        Args:
            notification_id: Notification ID
            notification: Notification data
            
        Returns:
            Window handle
        """
        try:
            # Calculate window position
            screen_width = GetSystemMetrics(0)
            screen_height = GetSystemMetrics(1)
            window_width = 300
            window_height = 100
            
            if notification['position'] == ToastPosition.TOP_RIGHT:
                x = screen_width - window_width - 20
                y = 20 + (window_height + 10) * len(self.active_notifications)
            elif notification['position'] == ToastPosition.TOP_LEFT:
                x = 20
                y = 20 + (window_height + 10) * len(self.active_notifications)
            elif notification['position'] == ToastPosition.BOTTOM_RIGHT:
                x = screen_width - window_width - 20
                y = screen_height - window_height - 20
            elif notification['position'] == ToastPosition.BOTTOM_LEFT:
                x = 20
                y = screen_height - window_height - 20
            else:  # center
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                
            # Create window class
            wc = win32gui.WNDCLASS()
            wc.lpszClassName = f"Toast{notification_id}"
            wc.hbrBackground = win32gui.GetStockObject(0)
            wc.lpfnWndProc = self._window_proc
            win32gui.RegisterClass(wc)
            
            # Create window
            hwnd = win32gui.CreateWindowEx(
                win32con.WS_EX_TOPMOST | win32con.WS_EX_LAYERED,
                wc.lpszClassName,
                notification['title'],
                win32con.WS_POPUP,
                x, y, window_width, window_height,
                0, 0, 0, None
            )
            
            # Create notification image
            image = self._create_notification_image(
                notification,
                window_width,
                window_height
            )
            
            # Display window
            self._update_layered_window(hwnd, image)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            
            return hwnd
            
        except Exception as e:
            logger.error(f"Error creating notification window: {str(e)}")
            return 0
            
    def _create_notification_image(
        self,
        notification: Dict[str, Any],
        width: int,
        height: int
    ) -> Image:
        """
        Create notification image
        
        Args:
            notification: Notification data
            width: Image width
            height: Image height
            
        Returns:
            PIL Image
        """
        try:
            # Create image
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Load font
            title_font = ImageFont.truetype(self.font_path, 14)
            message_font = ImageFont.truetype(self.font_path, 12)
            
            # Get style colors
            if notification['style'] == ToastStyle.SUCCESS:
                bg_color = (76, 175, 80, 230)
            elif notification['style'] == ToastStyle.ERROR:
                bg_color = (244, 67, 54, 230)
            elif notification['style'] == ToastStyle.WARNING:
                bg_color = (255, 152, 0, 230)
            elif notification['style'] == ToastStyle.INFO:
                bg_color = (33, 150, 243, 230)
            else:
                bg_color = (97, 97, 97, 230)
                
            # Draw background
            draw.rectangle(
                [0, 0, width, height],
                fill=bg_color,
                outline=(255, 255, 255, 50)
            )
            
            # Draw title
            draw.text(
                (10, 10),
                notification['title'],
                font=title_font,
                fill=(255, 255, 255, 255)
            )
            
            # Draw message
            draw.text(
                (10, 35),
                notification['message'],
                font=message_font,
                fill=(255, 255, 255, 230)
            )
            
            return image
            
        except Exception as e:
            logger.error(f"Error creating notification image: {str(e)}")
            return Image.new('RGBA', (width, height), (0, 0, 0, 0))
            
    def _update_layered_window(
        self,
        hwnd: int,
        image: Image
    ) -> None:
        """
        Update layered window
        
        Args:
            hwnd: Window handle
            image: PIL Image
        """
        try:
            # Convert image to bitmap
            width, height = image.size
            bitmap_str = image.tobytes('raw', 'BGRA')
            
            # Create device context
            hdcScreen = win32gui.GetDC(0)
            hdcWindow = win32gui.CreateCompatibleDC(hdcScreen)
            
            # Create bitmap
            hbmp = win32gui.CreateBitmap(
                width,
                height,
                1,
                32,
                None
            )
            win32gui.SelectObject(hdcWindow, hbmp)
            
            # Copy image to bitmap
            win32gui.SetBitmapBits(
                hbmp,
                len(bitmap_str),
                bitmap_str
            )
            
            # Update window
            win32gui.UpdateLayeredWindow(
                hwnd,
                hdcScreen,
                (0, 0),
                (width, height),
                hdcWindow,
                (0, 0),
                0,
                (win32con.AC_SRC_OVER, 0, 255, win32con.AC_SRC_ALPHA),
                win32con.ULW_ALPHA
            )
            
            # Clean up
            win32gui.DeleteObject(hbmp)
            win32gui.DeleteDC(hdcWindow)
            win32gui.ReleaseDC(0, hdcScreen)
            
        except Exception as e:
            logger.error(f"Error updating layered window: {str(e)}")
            
    async def _schedule_notification_removal(
        self,
        notification_id: int,
        duration: int
    ) -> None:
        """
        Schedule notification removal
        
        Args:
            notification_id: Notification ID
            duration: Display duration
        """
        try:
            await asyncio.sleep(duration)
            self._remove_notification(notification_id)
            
        except asyncio.CancelledError:
            self._remove_notification(notification_id)
        except Exception as e:
            logger.error(
                f"Error scheduling notification removal: {str(e)}"
            )
            
    def _remove_notification(self, notification_id: int) -> None:
        """
        Remove notification
        
        Args:
            notification_id: Notification ID
        """
        try:
            if notification_id in self.active_notifications:
                notification = self.active_notifications[notification_id]
                
                # Destroy window
                if 'window' in notification:
                    win32gui.DestroyWindow(notification['window'])
                    
                # Remove from active notifications
                del self.active_notifications[notification_id]
                
                # Unregister window class
                win32gui.UnregisterClass(
                    f"Toast{notification_id}",
                    None
                )
                
        except Exception as e:
            logger.error(f"Error removing notification: {str(e)}")
            
    def _window_proc(
        self,
        hwnd: int,
        msg: int,
        wparam: int,
        lparam: int
    ) -> int:
        """Window procedure"""
        try:
            if msg == win32con.WM_DESTROY:
                win32gui.PostQuitMessage(0)
                return 0
                
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
            
        except Exception as e:
            logger.error(f"Error in window procedure: {str(e)}")
            return 0
