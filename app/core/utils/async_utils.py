"""
Async utilities
"""

import asyncio
from typing import Any, Callable, Optional, TypeVar
from functools import wraps
import signal
from contextlib import asynccontextmanager
from loguru import logger

T = TypeVar('T')

def async_retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry async function decorator
    
    Args:
        retries: Maximum retry attempts
        delay: Initial delay between retries
        backoff: Delay multiplier for each retry
        exceptions: Exceptions to catch
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        break
                        
                    logger.warning(
                        f"Retry {attempt + 1}/{retries} for {func.__name__}: {str(e)}"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    
            raise last_exception
            
        return wrapper
    return decorator

class AsyncRateLimiter:
    """Rate limiter for async functions"""
    
    def __init__(
        self,
        calls: int,
        period: float,
        burst: Optional[int] = None
    ):
        """
        Initialize rate limiter
        
        Args:
            calls: Number of calls allowed
            period: Time period in seconds
            burst: Optional burst limit
        """
        self.calls = calls
        self.period = period
        self.burst = burst or calls
        self._tokens = self.burst
        self._last_update = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()
        
    async def acquire(self):
        """Acquire rate limit token"""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            
            # Replenish tokens
            elapsed = now - self._last_update
            self._tokens = min(
                self.burst,
                self._tokens + elapsed * (self.calls / self.period)
            )
            self._last_update = now
            
            # Check if we can proceed
            if self._tokens < 1:
                wait_time = (1 - self._tokens) * (self.period / self.calls)
                await asyncio.sleep(wait_time)
                self._tokens = 1
                
            self._tokens -= 1

class AsyncEventEmitter:
    """Async event emitter"""
    
    def __init__(self):
        """Initialize event emitter"""
        self._handlers = {}
        
    def on(
        self,
        event: str,
        handler: Callable[..., Any]
    ) -> None:
        """Register event handler"""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
        
    def off(
        self,
        event: str,
        handler: Callable[..., Any]
    ) -> None:
        """Remove event handler"""
        if event in self._handlers:
            self._handlers[event].remove(handler)
            
    async def emit(
        self,
        event: str,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Emit event to handlers"""
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(*args, **kwargs)
                    else:
                        handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler: {str(e)}")

@asynccontextmanager
async def handle_shutdown():
    """Handle graceful shutdown"""
    loop = asyncio.get_event_loop()
    
    # Set up signal handlers
    signals = (signal.SIGTERM, signal.SIGINT)
    handlers = {sig: loop.add_signal_handler(
        sig,
        lambda s=sig: asyncio.create_task(shutdown(loop, sig))
    ) for sig in signals}
    
    try:
        yield
    finally:
        # Restore signal handlers
        for sig, handler in handlers.items():
            loop.remove_signal_handler(sig)

async def shutdown(loop: asyncio.AbstractEventLoop, signal: int):
    """
    Shutdown coroutines gracefully
    
    Args:
        loop: Event loop
        signal: Signal number
    """
    logger.info(f"Received exit signal {signal.name}")
    
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
        
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
