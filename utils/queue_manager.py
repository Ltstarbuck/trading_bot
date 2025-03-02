"""
Queue management utilities for handling async message queues and event processing
"""

from typing import Any, Dict, List, Optional, Union, Callable
import asyncio
from asyncio import Queue, QueueEmpty, QueueFull
from collections import defaultdict
import time
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

class QueueManager:
    """
    Manages multiple message queues with priority support and event processing
    """
    
    def __init__(
        self,
        max_queue_size: int = 1000,
        num_workers: int = 4,
        batch_size: int = 100,
        batch_timeout: float = 0.1,
        retry_limit: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize queue manager
        
        Args:
            max_queue_size: Maximum size for each queue
            num_workers: Number of worker threads
            batch_size: Maximum batch size for processing
            batch_timeout: Timeout for batch processing
            retry_limit: Maximum number of retries
            retry_delay: Delay between retries
        """
        self.max_queue_size = max_queue_size
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        
        # Initialize queues
        self.queues: Dict[str, Queue] = {}
        self.priority_queues: Dict[str, Dict[int, Queue]] = {}
        
        # Initialize handlers
        self.handlers: Dict[str, Callable] = {}
        self.batch_handlers: Dict[str, Callable] = {}
        
        # Initialize worker pools
        self.thread_pool = ThreadPoolExecutor(
            max_workers=num_workers
        )
        
        # Initialize monitoring
        self.queue_stats: Dict[str, Dict] = defaultdict(
            lambda: {
                'enqueued': 0,
                'processed': 0,
                'errors': 0,
                'retries': 0
            }
        )
        
        # Initialize state
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
    async def start(self) -> None:
        """Start queue processing"""
        try:
            if self.running:
                return
                
            self.running = True
            
            # Start worker tasks
            for queue_name in self.queues:
                task = asyncio.create_task(
                    self._process_queue(queue_name)
                )
                self.tasks.append(task)
                
            # Start priority queue workers
            for queue_name in self.priority_queues:
                task = asyncio.create_task(
                    self._process_priority_queue(queue_name)
                )
                self.tasks.append(task)
                
            logger.info("Queue manager started")
            
        except Exception as e:
            logger.error(f"Error starting queue manager: {str(e)}")
            raise
            
    async def stop(self) -> None:
        """Stop queue processing"""
        try:
            if not self.running:
                return
                
            self.running = False
            
            # Cancel all tasks
            for task in self.tasks:
                task.cancel()
                
            # Wait for tasks to complete
            await asyncio.gather(
                *self.tasks,
                return_exceptions=True
            )
            
            # Clear tasks
            self.tasks.clear()
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)
            
            logger.info("Queue manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping queue manager: {str(e)}")
            raise
            
    def register_queue(
        self,
        queue_name: str,
        handler: Optional[Callable] = None,
        batch_handler: Optional[Callable] = None,
        priority_levels: Optional[List[int]] = None
    ) -> None:
        """
        Register a new queue
        
        Args:
            queue_name: Name of the queue
            handler: Message handler function
            batch_handler: Batch message handler function
            priority_levels: List of priority levels
        """
        try:
            if priority_levels:
                # Create priority queues
                self.priority_queues[queue_name] = {
                    level: Queue(maxsize=self.max_queue_size)
                    for level in priority_levels
                }
            else:
                # Create regular queue
                self.queues[queue_name] = Queue(
                    maxsize=self.max_queue_size
                )
                
            # Register handlers
            if handler:
                self.handlers[queue_name] = handler
            if batch_handler:
                self.batch_handlers[queue_name] = batch_handler
                
            logger.info(f"Registered queue: {queue_name}")
            
        except Exception as e:
            logger.error(
                f"Error registering queue {queue_name}: {str(e)}"
            )
            raise
            
    async def enqueue(
        self,
        queue_name: str,
        message: Any,
        priority: Optional[int] = None
    ) -> bool:
        """
        Enqueue a message
        
        Args:
            queue_name: Name of the queue
            message: Message to enqueue
            priority: Priority level (if using priority queue)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if priority is not None:
                # Use priority queue
                if queue_name not in self.priority_queues:
                    raise ValueError(
                        f"Priority queue {queue_name} not found"
                    )
                if priority not in self.priority_queues[queue_name]:
                    raise ValueError(
                        f"Invalid priority level {priority}"
                    )
                    
                await self.priority_queues[
                    queue_name
                ][priority].put(message)
            else:
                # Use regular queue
                if queue_name not in self.queues:
                    raise ValueError(
                        f"Queue {queue_name} not found"
                    )
                    
                await self.queues[queue_name].put(message)
                
            # Update stats
            self.queue_stats[queue_name]['enqueued'] += 1
            
            return True
            
        except QueueFull:
            logger.warning(
                f"Queue {queue_name} is full"
            )
            return False
        except Exception as e:
            logger.error(
                f"Error enqueuing to {queue_name}: {str(e)}"
            )
            return False
            
    async def _process_queue(self, queue_name: str) -> None:
        """Process messages from a regular queue"""
        try:
            queue = self.queues[queue_name]
            handler = self.handlers.get(queue_name)
            batch_handler = self.batch_handlers.get(queue_name)
            
            while self.running:
                try:
                    if batch_handler:
                        # Batch processing
                        await self._process_batch(
                            queue_name,
                            queue,
                            batch_handler
                        )
                    elif handler:
                        # Single message processing
                        message = await queue.get()
                        await self._process_message(
                            queue_name,
                            message,
                            handler
                        )
                        queue.task_done()
                    else:
                        # No handler registered
                        await asyncio.sleep(0.1)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        f"Error processing queue {queue_name}: {str(e)}"
                    )
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(
                f"Fatal error in queue {queue_name}: {str(e)}"
            )
            
    async def _process_priority_queue(
        self,
        queue_name: str
    ) -> None:
        """Process messages from a priority queue"""
        try:
            priority_queues = self.priority_queues[queue_name]
            handler = self.handlers.get(queue_name)
            batch_handler = self.batch_handlers.get(queue_name)
            
            while self.running:
                try:
                    # Process queues in priority order
                    for priority in sorted(
                        priority_queues.keys(),
                        reverse=True
                    ):
                        queue = priority_queues[priority]
                        
                        if batch_handler:
                            # Batch processing
                            await self._process_batch(
                                queue_name,
                                queue,
                                batch_handler
                            )
                        elif handler:
                            # Try to get message
                            try:
                                message = queue.get_nowait()
                                await self._process_message(
                                    queue_name,
                                    message,
                                    handler
                                )
                                queue.task_done()
                            except QueueEmpty:
                                continue
                                
                    # Small delay between priority checks
                    await asyncio.sleep(0.01)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        f"Error processing priority queue {queue_name}: {str(e)}"
                    )
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(
                f"Fatal error in priority queue {queue_name}: {str(e)}"
            )
            
    async def _process_batch(
        self,
        queue_name: str,
        queue: Queue,
        handler: Callable
    ) -> None:
        """Process a batch of messages"""
        try:
            batch = []
            start_time = time.time()
            
            while len(batch) < self.batch_size:
                try:
                    # Try to get message
                    message = queue.get_nowait()
                    batch.append(message)
                    queue.task_done()
                except QueueEmpty:
                    break
                    
                # Check timeout
                if time.time() - start_time > self.batch_timeout:
                    break
                    
            if batch:
                # Process batch
                await self._process_message(
                    queue_name,
                    batch,
                    handler
                )
                
        except Exception as e:
            logger.error(
                f"Error processing batch for {queue_name}: {str(e)}"
            )
            
    async def _process_message(
        self,
        queue_name: str,
        message: Any,
        handler: Callable
    ) -> None:
        """Process a single message or batch"""
        retries = 0
        while retries < self.retry_limit:
            try:
                # Execute handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.thread_pool,
                    handler,
                    message
                )
                
                # Update stats
                self.queue_stats[queue_name]['processed'] += (
                    len(message) if isinstance(message, list)
                    else 1
                )
                break
                
            except Exception as e:
                retries += 1
                self.queue_stats[queue_name]['retries'] += 1
                
                if retries == self.retry_limit:
                    logger.error(
                        f"Failed to process message after {retries} "
                        f"retries for {queue_name}: {str(e)}"
                    )
                    self.queue_stats[queue_name]['errors'] += 1
                else:
                    await asyncio.sleep(self.retry_delay)
                    
    def get_queue_stats(self) -> Dict[str, Dict]:
        """Get queue statistics"""
        stats = {}
        
        for queue_name, queue in self.queues.items():
            stats[queue_name] = {
                'size': queue.qsize(),
                **self.queue_stats[queue_name]
            }
            
        for queue_name, priority_queues in self.priority_queues.items():
            stats[queue_name] = {
                'size': sum(
                    q.qsize() for q in priority_queues.values()
                ),
                'priority_sizes': {
                    priority: queue.qsize()
                    for priority, queue in priority_queues.items()
                },
                **self.queue_stats[queue_name]
            }
            
        return stats
        
    def clear_queue(self, queue_name: str) -> None:
        """
        Clear all messages from a queue
        
        Args:
            queue_name: Name of the queue
        """
        try:
            if queue_name in self.queues:
                while not self.queues[queue_name].empty():
                    try:
                        self.queues[queue_name].get_nowait()
                        self.queues[queue_name].task_done()
                    except QueueEmpty:
                        break
            elif queue_name in self.priority_queues:
                for queue in self.priority_queues[queue_name].values():
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                            queue.task_done()
                        except QueueEmpty:
                            break
                            
            logger.info(f"Cleared queue: {queue_name}")
            
        except Exception as e:
            logger.error(
                f"Error clearing queue {queue_name}: {str(e)}"
            )
            
    async def wait_for_queue(
        self,
        queue_name: str,
        timeout: Optional[float] = None
    ) -> None:
        """
        Wait for a queue to be empty
        
        Args:
            queue_name: Name of the queue
            timeout: Timeout in seconds
        """
        try:
            start_time = time.time()
            
            while True:
                if queue_name in self.queues:
                    if self.queues[queue_name].empty():
                        break
                elif queue_name in self.priority_queues:
                    if all(
                        q.empty()
                        for q in self.priority_queues[
                            queue_name
                        ].values()
                    ):
                        break
                else:
                    raise ValueError(
                        f"Queue {queue_name} not found"
                    )
                    
                if timeout and time.time() - start_time > timeout:
                    raise TimeoutError(
                        f"Timeout waiting for queue {queue_name}"
                    )
                    
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(
                f"Error waiting for queue {queue_name}: {str(e)}"
            )
            raise
