"""
Time formatting utilities
"""

from typing import Optional, Union
from datetime import datetime, timedelta
import pytz
from zoneinfo import ZoneInfo

def format_timestamp(
    timestamp: Union[int, float, datetime],
    timezone: Optional[str] = None,
    format_str: Optional[str] = None,
    include_tz: bool = False,
    include_ms: bool = False
) -> str:
    """
    Format timestamp
    
    Args:
        timestamp: Unix timestamp or datetime
        timezone: Target timezone
        format_str: Custom format string
        include_tz: Include timezone
        include_ms: Include milliseconds
        
    Returns:
        Formatted timestamp string
    """
    try:
        # Convert to datetime
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = timestamp
            
        # Convert timezone
        if timezone:
            try:
                tz = ZoneInfo(timezone)
            except Exception:
                tz = pytz.timezone(timezone)
            dt = dt.astimezone(tz)
            
        # Use default format if none provided
        if not format_str:
            if include_ms:
                format_str = '%Y-%m-%d %H:%M:%S.%f'
            else:
                format_str = '%Y-%m-%d %H:%M:%S'
                
            if include_tz:
                format_str += ' %z'
                
        return dt.strftime(format_str)
        
    except Exception:
        return str(timestamp)

def format_duration(
    duration: Union[int, float, timedelta],
    include_ms: bool = False,
    short_format: bool = False,
    max_units: int = 2
) -> str:
    """
    Format duration
    
    Args:
        duration: Seconds or timedelta
        include_ms: Include milliseconds
        short_format: Use short unit names
        max_units: Maximum number of units to show
        
    Returns:
        Formatted duration string
    """
    try:
        # Convert to timedelta
        if isinstance(duration, (int, float)):
            td = timedelta(seconds=duration)
        else:
            td = duration
            
        # Extract components
        total_seconds = int(td.total_seconds())
        ms = int(td.microseconds / 1000)
        
        days = total_seconds // (24 * 3600)
        remaining = total_seconds % (24 * 3600)
        hours = remaining // 3600
        remaining = remaining % 3600
        minutes = remaining // 60
        seconds = remaining % 60
        
        # Format components
        components = []
        
        if days > 0:
            unit = 'd' if short_format else ' days'
            components.append(f"{days}{unit}")
            
        if hours > 0:
            unit = 'h' if short_format else ' hours'
            components.append(f"{hours}{unit}")
            
        if minutes > 0:
            unit = 'm' if short_format else ' minutes'
            components.append(f"{minutes}{unit}")
            
        if seconds > 0 or not components:
            unit = 's' if short_format else ' seconds'
            if include_ms and ms > 0:
                components.append(f"{seconds}.{ms:03d}{unit}")
            else:
                components.append(f"{seconds}{unit}")
                
        # Combine components
        return ' '.join(components[:max_units])
        
    except Exception:
        return str(duration)

def format_relative_time(
    timestamp: Union[int, float, datetime],
    reference: Optional[Union[int, float, datetime]] = None,
    short_format: bool = False,
    include_suffix: bool = True
) -> str:
    """
    Format relative time
    
    Args:
        timestamp: Target timestamp
        reference: Reference timestamp (now if None)
        short_format: Use short format
        include_suffix: Include ago/from now
        
    Returns:
        Formatted relative time string
    """
    try:
        # Convert to datetime
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = timestamp
            
        # Get reference time
        if reference is None:
            ref_dt = datetime.now()
        elif isinstance(reference, (int, float)):
            ref_dt = datetime.fromtimestamp(reference)
        else:
            ref_dt = reference
            
        # Calculate difference
        diff = ref_dt - dt
        is_past = diff.total_seconds() > 0
        diff = abs(diff)
        
        # Format duration
        duration = format_duration(
            diff,
            short_format=short_format,
            max_units=1
        )
        
        # Add suffix
        if include_suffix:
            if is_past:
                suffix = ' ago'
            else:
                suffix = ' from now'
                
            if short_format:
                return f"{duration}"
            return f"{duration}{suffix}"
            
        return duration
        
    except Exception:
        return str(timestamp)

def format_trading_time(
    timestamp: Union[int, float, datetime],
    timezone: Optional[str] = None,
    include_seconds: bool = True,
    include_date: bool = True
) -> str:
    """
    Format timestamp for trading display
    
    Args:
        timestamp: Timestamp to format
        timezone: Target timezone
        include_seconds: Include seconds
        include_date: Include date
        
    Returns:
        Formatted trading time string
    """
    try:
        # Convert to datetime
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = timestamp
            
        # Convert timezone
        if timezone:
            try:
                tz = ZoneInfo(timezone)
            except Exception:
                tz = pytz.timezone(timezone)
            dt = dt.astimezone(tz)
            
        # Build format string
        if include_date:
            format_str = '%Y-%m-%d '
        else:
            format_str = ''
            
        if include_seconds:
            format_str += '%H:%M:%S'
        else:
            format_str += '%H:%M'
            
        return dt.strftime(format_str)
        
    except Exception:
        return str(timestamp)
