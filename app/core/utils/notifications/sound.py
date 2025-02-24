"""
Sound notification handler for playing audio alerts
"""

from typing import Any, Dict, List, Optional, Union
import os
import asyncio
from enum import Enum
import winsound
from loguru import logger

from .base import (
    BaseNotificationHandler,
    NotificationPriority,
    NotificationType
)

class SoundType(Enum):
    """Predefined sound types"""
    ALERT = "alert.wav"
    ERROR = "error.wav"
    SUCCESS = "success.wav"
    WARNING = "warning.wav"
    TRADE = "trade.wav"
    INFO = "info.wav"

class SoundNotificationHandler(BaseNotificationHandler):
    """Sound notification handler"""
    
    def __init__(
        self,
        sound_dir: str,
        min_priority: NotificationPriority = NotificationPriority.NORMAL,
        default_duration: int = 1000,  # milliseconds
        default_repeat: int = 1,
        max_queue_size: int = 10
    ):
        """
        Initialize sound handler
        
        Args:
            sound_dir: Directory containing sound files
            min_priority: Minimum priority level
            default_duration: Default sound duration
            default_repeat: Default repeat count
            max_queue_size: Maximum sound queue size
        """
        super().__init__("sound", min_priority)
        self.sound_dir = sound_dir
        self.default_duration = default_duration
        self.default_repeat = default_repeat
        
        # Initialize sound queue
        self.sound_queue: asyncio.Queue = asyncio.Queue(
            maxsize=max_queue_size
        )
        
        # Initialize sound mapping
        self.sound_mapping = {
            NotificationType.ALERT: SoundType.ALERT,
            NotificationType.ERROR: SoundType.ERROR,
            NotificationType.INFO: SoundType.INFO,
            NotificationType.WARNING: SoundType.WARNING,
            NotificationType.TRADE: SoundType.TRADE,
            NotificationType.SYSTEM: SoundType.INFO
        }
        
        # Initialize player task
        self.player_task: Optional[asyncio.Task] = None
        self.running = False
        
    async def start(self) -> None:
        """Start sound player"""
        if self.running:
            return
            
        self.running = True
        self.player_task = asyncio.create_task(
            self._sound_player()
        )
        logger.info("Sound notification handler started")
        
    async def stop(self) -> None:
        """Stop sound player"""
        if not self.running:
            return
            
        self.running = False
        if self.player_task:
            self.player_task.cancel()
            try:
                await self.player_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Sound notification handler stopped")
        
    async def send_notification(
        self,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        sound_file: Optional[str] = None,
        duration: Optional[int] = None,
        repeat: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Send sound notification
        
        Args:
            message: Notification message (unused)
            notification_type: Type of notification
            priority: Priority level
            sound_file: Custom sound file
            duration: Sound duration
            repeat: Repeat count
            **kwargs: Additional arguments
            
        Returns:
            True if queued successfully
        """
        try:
            if not self.should_send(priority):
                return False
                
            # Get sound file
            if sound_file:
                sound_path = os.path.join(
                    self.sound_dir,
                    sound_file
                )
            else:
                sound_type = self.sound_mapping[notification_type]
                sound_path = os.path.join(
                    self.sound_dir,
                    sound_type.value
                )
                
            # Validate sound file
            if not os.path.exists(sound_path):
                logger.error(f"Sound file not found: {sound_path}")
                return False
                
            # Queue sound
            try:
                await self.sound_queue.put({
                    'file': sound_path,
                    'duration': duration or self.default_duration,
                    'repeat': repeat or self.default_repeat,
                    'priority': priority
                })
                return True
                
            except asyncio.QueueFull:
                logger.warning("Sound queue is full")
                return False
                
        except Exception as e:
            logger.error(f"Error sending sound notification: {str(e)}")
            return False
            
    async def send_batch(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[bool]:
        """
        Send batch of sound notifications
        
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
                f"Error processing batch sound notifications: {str(e)}"
            )
            return [False] * len(notifications)
            
    async def _sound_player(self) -> None:
        """Sound player loop"""
        try:
            while self.running:
                try:
                    # Get next sound
                    sound = await self.sound_queue.get()
                    
                    # Play sound
                    await self._play_sound(
                        sound['file'],
                        sound['duration'],
                        sound['repeat']
                    )
                    
                    self.sound_queue.task_done()
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error playing sound: {str(e)}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error in sound player: {str(e)}")
            
    async def _play_sound(
        self,
        sound_file: str,
        duration: int,
        repeat: int
    ) -> None:
        """
        Play sound file
        
        Args:
            sound_file: Path to sound file
            duration: Sound duration
            repeat: Repeat count
        """
        try:
            # Play sound in thread to avoid blocking
            loop = asyncio.get_event_loop()
            
            for _ in range(repeat):
                await loop.run_in_executor(
                    None,
                    winsound.PlaySound,
                    sound_file,
                    winsound.SND_FILENAME
                )
                
                if repeat > 1:
                    await asyncio.sleep(duration / 1000)
                    
        except Exception as e:
            logger.error(f"Error playing sound file: {str(e)}")
            
    def clear_queue(self) -> None:
        """Clear sound queue"""
        while not self.sound_queue.empty():
            try:
                self.sound_queue.get_nowait()
                self.sound_queue.task_done()
            except asyncio.QueueEmpty:
                break
