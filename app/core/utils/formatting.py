"""
Formatting utilities
"""

from typing import Dict, Optional, Union
from decimal import Decimal
import json
from datetime import datetime

def format_decimal(
    value: Decimal,
    precision: int = 8,
    strip_zeros: bool = True
) -> str:
    """
    Format decimal value
    
    Args:
        value: Decimal value
        precision: Decimal precision
        strip_zeros: Remove trailing zeros
        
    Returns:
        Formatted string
    """
    formatted = f"{value:.{precision}f}"
    if strip_zeros:
        formatted = formatted.rstrip('0').rstrip('.')
    return formatted

def format_price(
    price: Decimal,
    precision: Optional[int] = None
) -> str:
    """
    Format price with appropriate precision
    
    Args:
        price: Price value
        precision: Optional fixed precision
        
    Returns:
        Formatted price string
    """
    if precision is None:
        # Determine precision based on price magnitude
        if price >= 1000:
            precision = 2
        elif price >= 1:
            precision = 4
        else:
            precision = 8
    
    return format_decimal(price, precision)

def format_amount(
    amount: Decimal,
    precision: int = 8
) -> str:
    """
    Format token amount
    
    Args:
        amount: Token amount
        precision: Decimal precision
        
    Returns:
        Formatted amount string
    """
    return format_decimal(amount, precision)

def format_percentage(
    value: Decimal,
    precision: int = 2,
    include_sign: bool = True
) -> str:
    """
    Format percentage value
    
    Args:
        value: Decimal value
        precision: Decimal precision
        include_sign: Include plus sign for positive values
        
    Returns:
        Formatted percentage string
    """
    formatted = format_decimal(value, precision)
    if include_sign and value > 0:
        formatted = f"+{formatted}"
    return f"{formatted}%"

def format_timestamp(
    timestamp: Union[datetime, float, int],
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format timestamp
    
    Args:
        timestamp: Timestamp value
        format_str: DateTime format string
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, (float, int)):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = timestamp
    return dt.strftime(format_str)

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder with Decimal support"""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def format_json(
    data: Dict,
    indent: Optional[int] = 2
) -> str:
    """
    Format JSON with Decimal support
    
    Args:
        data: Data to format
        indent: JSON indentation
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(
        data,
        cls=DecimalEncoder,
        indent=indent
    )
