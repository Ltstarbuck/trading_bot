"""
Task scheduler for managing periodic and scheduled tasks
"""

from typing import Any, Dict, List, Optional, Union, Callable
import asyncio
from asyncio import Task
from datetime import datetime, timedelta
import time
import heapq
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
import pytz
from loguru import logger

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass(order=True)
class ScheduledTask:
    """Scheduled task container"""
    scheduled_time: datetime
    priority: TaskPriority = field(compare=False)
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    interval: Optional[timedelta] = field(default=None, compare=False)
    max_retries: int = field(default=3, compare=False)
    retry_delay: float = field(default=1.0, compare=False)
    timeout: Optional[float] = field(default=None, compare=False)
    
class TaskScheduler:
    """
    Advanced task scheduler with support for:
    - Periodic tasks
    - One-time scheduled tasks
    - Priority-based execution
    - Retry mechanisms
    - Task timeout
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        timezone: str = 'UTC'
    ):
        """
        Initialize task scheduler
        
        Args:
            max_workers: Maximum number of worker threads
            timezone: Default timezone for scheduling
        """
        self.max_workers = max_workers
        self.timezone = pytz.timezone(timezone)
        
        # Initialize task queues
        self.task_queue: List[ScheduledTask] = []
        self.periodic_tasks: Dict[str, ScheduledTask] = {}
        
        # Initialize worker pool
        self.thread_pool = ThreadPoolExecutor(
            max_workers=max_workers
        )
        
        # Initialize task tracking
        self.running_tasks: Dict[str, Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.task_errors: Dict[str, Exception] = {}
        
        # Initialize state
        self.running = False
        self.scheduler_task: Optional[Task] = None
        
    async def start(self) -> None:
        """Start the task scheduler"""
        try:
            if self.running:
                return
                
            self.running = True
            
            # Start scheduler loop
            self.scheduler_task = asyncio.create_task(
                self._scheduler_loop()
            )
            
            logger.info("Task scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            raise
            
    async def stop(self) -> None:
        """Stop the task scheduler"""
        try:
            if not self.running:
                return
                
            self.running = False
            
            # Cancel scheduler loop
            if self.scheduler_task:
                self.scheduler_task.cancel()
                try:
                    await self.scheduler_task
                except asyncio.CancelledError:
                    pass
                    
            # Cancel running tasks
            for task in self.running_tasks.values():
                task.cancel()
                
            # Wait for tasks to complete
            if self.running_tasks:
                await asyncio.gather(
                    *self.running_tasks.values(),
                    return_exceptions=True
                )
                
            # Clear task queues
            self.task_queue.clear()
            self.periodic_tasks.clear()
            self.running_tasks.clear()
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)
            
            logger.info("Task scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            raise
            
    def schedule_task(
        self,
        task_id: str,
        func: Callable,
        scheduled_time: Union[datetime, timedelta],
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None
    ) -> None:
        """
        Schedule a one-time task
        
        Args:
            task_id: Unique task identifier
            func: Task function to execute
            scheduled_time: When to execute the task
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            timeout: Task timeout in seconds
        """
        try:
            # Convert scheduled_time to datetime
            if isinstance(scheduled_time, timedelta):
                scheduled_time = (
                    datetime.now(self.timezone) + scheduled_time
                )
            elif isinstance(scheduled_time, datetime):
                if scheduled_time.tzinfo is None:
                    scheduled_time = self.timezone.localize(
                        scheduled_time
                    )
                    
            # Create task
            task = ScheduledTask(
                scheduled_time=scheduled_time,
                priority=priority,
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs or {},
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout
            )
            
            # Add to queue
            heapq.heappush(self.task_queue, task)
            
            logger.info(
                f"Scheduled task {task_id} for {scheduled_time}"
            )
            
        except Exception as e:
            logger.error(
                f"Error scheduling task {task_id}: {str(e)}"
            )
            raise
            
    def schedule_periodic_task(
        self,
        task_id: str,
        func: Callable,
        interval: timedelta,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        start_time: Optional[datetime] = None
    ) -> None:
        """
        Schedule a periodic task
        
        Args:
            task_id: Unique task identifier
            func: Task function to execute
            interval: Time between executions
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            timeout: Task timeout in seconds
            start_time: When to start the periodic task
        """
        try:
            # Set start time
            if start_time is None:
                start_time = datetime.now(self.timezone)
            elif start_time.tzinfo is None:
                start_time = self.timezone.localize(start_time)
                
            # Create task
            task = ScheduledTask(
                scheduled_time=start_time,
                priority=priority,
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs or {},
                interval=interval,
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout
            )
            
            # Add to periodic tasks
            self.periodic_tasks[task_id] = task
            
            # Add to queue
            heapq.heappush(self.task_queue, task)
            
            logger.info(
                f"Scheduled periodic task {task_id} "
                f"with interval {interval}"
            )
            
        except Exception as e:
            logger.error(
                f"Error scheduling periodic task {task_id}: {str(e)}"
            )
            raise
            
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was cancelled
        """
        try:
            # Remove from periodic tasks
            if task_id in self.periodic_tasks:
                del self.periodic_tasks[task_id]
                
            # Remove from task queue
            self.task_queue = [
                task for task in self.task_queue
                if task.task_id != task_id
            ]
            heapq.heapify(self.task_queue)
            
            # Cancel if running
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                
            logger.info(f"Cancelled task {task_id}")
            return True
            
        except Exception as e:
            logger.error(
                f"Error cancelling task {task_id}: {str(e)}"
            )
            return False
            
    def get_task_status(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get task status
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dictionary
        """
        status = {
            'scheduled': False,
            'running': False,
            'completed': False,
            'failed': False,
            'next_run': None,
            'result': None,
            'error': None
        }
        
        # Check if scheduled
        for task in self.task_queue:
            if task.task_id == task_id:
                status['scheduled'] = True
                status['next_run'] = task.scheduled_time
                break
                
        # Check if periodic
        if task_id in self.periodic_tasks:
            status['periodic'] = True
            
        # Check if running
        if task_id in self.running_tasks:
            status['running'] = True
            
        # Check result/error
        if task_id in self.task_results:
            status['completed'] = True
            status['result'] = self.task_results[task_id]
        elif task_id in self.task_errors:
            status['failed'] = True
            status['error'] = str(self.task_errors[task_id])
            
        return status
        
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        try:
            while self.running:
                now = datetime.now(self.timezone)
                
                # Process due tasks
                while (
                    self.task_queue and
                    self.task_queue[0].scheduled_time <= now
                ):
                    # Get next task
                    task = heapq.heappop(self.task_queue)
                    
                    # Schedule task execution
                    asyncio_task = asyncio.create_task(
                        self._execute_task(task)
                    )
                    self.running_tasks[task.task_id] = asyncio_task
                    
                    # Reschedule if periodic
                    if (
                        task.interval and
                        task.task_id in self.periodic_tasks
                    ):
                        next_task = ScheduledTask(
                            scheduled_time=task.scheduled_time + task.interval,
                            priority=task.priority,
                            task_id=task.task_id,
                            func=task.func,
                            args=task.args,
                            kwargs=task.kwargs,
                            interval=task.interval,
                            max_retries=task.max_retries,
                            retry_delay=task.retry_delay,
                            timeout=task.timeout
                        )
                        heapq.heappush(self.task_queue, next_task)
                        
                # Clean up completed tasks
                self._cleanup_tasks()
                
                # Sleep briefly
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in scheduler loop: {str(e)}")
            raise
            
    async def _execute_task(self, task: ScheduledTask) -> None:
        """
        Execute a scheduled task
        
        Args:
            task: Task to execute
        """
        retries = 0
        while retries <= task.max_retries:
            try:
                # Execute in thread pool
                loop = asyncio.get_event_loop()
                if task.timeout:
                    # Run with timeout
                    result = await asyncio.wait_for(
                        loop.run_in_executor(
                            self.thread_pool,
                            task.func,
                            *task.args,
                            **task.kwargs
                        ),
                        timeout=task.timeout
                    )
                else:
                    # Run without timeout
                    result = await loop.run_in_executor(
                        self.thread_pool,
                        task.func,
                        *task.args,
                        **task.kwargs
                    )
                    
                # Store result
                self.task_results[task.task_id] = result
                
                # Log success
                logger.info(f"Task {task.task_id} completed")
                break
                
            except Exception as e:
                retries += 1
                if retries <= task.max_retries:
                    # Retry after delay
                    logger.warning(
                        f"Task {task.task_id} failed, "
                        f"retrying ({retries}/{task.max_retries})"
                    )
                    await asyncio.sleep(task.retry_delay)
                else:
                    # Store error
                    self.task_errors[task.task_id] = e
                    logger.error(
                        f"Task {task.task_id} failed: {str(e)}"
                    )
                    
    def _cleanup_tasks(self) -> None:
        """Clean up completed tasks"""
        # Remove completed tasks
        completed = []
        for task_id, task in self.running_tasks.items():
            if task.done():
                completed.append(task_id)
                
        for task_id in completed:
            del self.running_tasks[task_id]
            
        # Clean up old results/errors
        now = datetime.now(self.timezone)
        cutoff = now - timedelta(hours=1)
        
        self.task_results = {
            task_id: result
            for task_id, result in self.task_results.items()
            if any(
                task.task_id == task_id
                for task in self.task_queue
            ) or task_id in self.periodic_tasks
        }
        
        self.task_errors = {
            task_id: error
            for task_id, error in self.task_errors.items()
            if any(
                task.task_id == task_id
                for task in self.task_queue
            ) or task_id in self.periodic_tasks
        }
