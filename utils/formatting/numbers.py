"""
Number formatting utilities
"""

from typing import Union, Optional
from decimal import Decimal, ROUND_HALF_UP

def format_number(
    number: Union[int, float, Decimal],
    decimals: Optional[int] = None,
    min_decimals: Optional[int] = None,
    max_decimals: Optional[int] = None,
    thousands_sep: str = ',',
    decimal_sep: str = '.',
    strip_trailing_zeros: bool = True,
    pad_zeros: bool = False
) -> str:
    """
    Format number with flexible precision and separators
    
    Args:
        number: Number to format
        decimals: Fixed number of decimal places
        min_decimals: Minimum decimal places
        max_decimals: Maximum decimal places
        thousands_sep: Thousands separator
        decimal_sep: Decimal separator
        strip_trailing_zeros: Remove trailing zeros
        pad_zeros: Pad with zeros to min_decimals
        
    Returns:
        Formatted number string
    """
    try:
        # Convert to Decimal for precise handling
        if not isinstance(number, Decimal):
            number = Decimal(str(number))
            
        # Handle fixed decimals
        if decimals is not None:
            number = Decimal(
                str(number.quantize(
                    Decimal('0.1') ** decimals,
                    rounding=ROUND_HALF_UP
                ))
            )
            
        # Handle min/max decimals
        elif max_decimals is not None or min_decimals is not None:
            min_dec = min_decimals or 0
            max_dec = max_decimals or min_dec
            
            # Round to max decimals
            number = Decimal(
                str(number.quantize(
                    Decimal('0.1') ** max_dec,
                    rounding=ROUND_HALF_UP
                ))
            )
            
        # Convert to string
        num_str = str(number)
        
        # Split integer and decimal parts
        if '.' in num_str:
            int_part, dec_part = num_str.split('.')
        else:
            int_part, dec_part = num_str, ''
            
        # Add thousands separator
        if thousands_sep:
            int_part = format_thousands(int_part, thousands_sep)
            
        # Handle decimal part
        if dec_part:
            if strip_trailing_zeros:
                dec_part = dec_part.rstrip('0')
                
            if min_decimals and pad_zeros:
                dec_part = dec_part.ljust(min_decimals, '0')
                
            if dec_part:
                return f"{int_part}{decimal_sep}{dec_part}"
                
        return int_part
        
    except Exception as e:
        return str(number)

def format_thousands(
    number: Union[str, int],
    separator: str = ','
) -> str:
    """
    Format number with thousands separator
    
    Args:
        number: Number to format
        separator: Thousands separator
        
    Returns:
        Formatted number string
    """
    try:
        # Convert to string and handle negative
        num_str = str(number)
        is_negative = num_str.startswith('-')
        if is_negative:
            num_str = num_str[1:]
            
        # Add separators
        result = ''
        for i, digit in enumerate(reversed(num_str)):
            if i > 0 and i % 3 == 0:
                result = separator + result
            result = digit + result
            
        return f"-{result}" if is_negative else result
        
    except Exception:
        return str(number)

def format_percentage(
    number: Union[int, float, Decimal],
    decimals: int = 2,
    include_sign: bool = False,
    include_space: bool = True
) -> str:
    """
    Format number as percentage
    
    Args:
        number: Number to format (0.1 = 10%)
        decimals: Decimal places
        include_sign: Include plus sign for positive
        include_space: Include space before %
        
    Returns:
        Formatted percentage string
    """
    try:
        # Convert to percentage
        percentage = Decimal(str(number)) * 100
        
        # Format number
        num_str = format_number(percentage, decimals=decimals)
        
        # Add sign
        if include_sign and not num_str.startswith('-'):
            num_str = f"+{num_str}"
            
        # Add symbol
        symbol = ' %' if include_space else '%'
        return f"{num_str}{symbol}"
        
    except Exception:
        return str(number)

def format_currency(
    amount: Union[int, float, Decimal],
    currency: str = 'USD',
    decimals: int = 2,
    symbol_first: bool = True,
    include_space: bool = True
) -> str:
    """
    Format amount as currency
    
    Args:
        amount: Amount to format
        currency: Currency code or symbol
        decimals: Decimal places
        symbol_first: Show symbol before amount
        include_space: Include space after/before symbol
        
    Returns:
        Formatted currency string
    """
    try:
        # Format number
        num_str = format_number(amount, decimals=decimals)
        
        # Add symbol
        space = ' ' if include_space else ''
        if symbol_first:
            return f"{currency}{space}{num_str}"
        return f"{num_str}{space}{currency}"
        
    except Exception:
        return str(amount)
