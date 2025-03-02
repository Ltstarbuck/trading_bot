"""
Validation utilities
"""

from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
import re
from datetime import datetime

def validate_decimal(
    value: Union[str, float, int, Decimal],
    min_value: Optional[Decimal] = None,
    max_value: Optional[Decimal] = None
) -> Decimal:
    """
    Validate and convert to Decimal
    
    Args:
        value: Value to convert
        min_value: Optional minimum value
        max_value: Optional maximum value
        
    Returns:
        Validated Decimal value
        
    Raises:
        ValueError: If validation fails
    """
    try:
        # Convert to Decimal
        if isinstance(value, str):
            decimal_value = Decimal(value)
        elif isinstance(value, (float, int)):
            decimal_value = Decimal(str(value))
        elif isinstance(value, Decimal):
            decimal_value = value
        else:
            raise ValueError(f"Cannot convert {type(value)} to Decimal")
            
        # Check bounds
        if min_value is not None and decimal_value < min_value:
            raise ValueError(f"Value {decimal_value} below minimum {min_value}")
        if max_value is not None and decimal_value > max_value:
            raise ValueError(f"Value {decimal_value} above maximum {max_value}")
            
        return decimal_value
        
    except Exception as e:
        raise ValueError(f"Invalid decimal value: {str(e)}")

def validate_trading_pair(pair: str) -> bool:
    """
    Validate trading pair format
    
    Args:
        pair: Trading pair (e.g. 'BTC/USDT')
        
    Returns:
        True if valid
    """
    pattern = r'^[A-Z0-9]+/[A-Z0-9]+$'
    return bool(re.match(pattern, pair))

def validate_timeframe(timeframe: str) -> bool:
    """
    Validate timeframe format
    
    Args:
        timeframe: Time interval (e.g. '1m', '5m', '1h', '1d')
        
    Returns:
        True if valid
    """
    pattern = r'^[1-9][0-9]*[mhdwM]$'
    return bool(re.match(pattern, timeframe))

def validate_iso_timestamp(timestamp: str) -> bool:
    """
    Validate ISO timestamp format
    
    Args:
        timestamp: ISO format timestamp
        
    Returns:
        True if valid
    """
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def validate_api_credentials(
    credentials: Dict[str, str],
    required_fields: List[str]
) -> bool:
    """
    Validate API credentials
    
    Args:
        credentials: Credential dictionary
        required_fields: Required field names
        
    Returns:
        True if valid
    """
    return all(
        field in credentials and credentials[field]
        for field in required_fields
    )
