"""
Text formatting utilities
"""

from typing import Optional, List, Dict, Any
import re
from textwrap import wrap

def truncate_text(
    text: str,
    max_length: int,
    suffix: str = '...',
    at_word_boundary: bool = True
) -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Truncation suffix
        at_word_boundary: Truncate at word boundary
        
    Returns:
        Truncated text
    """
    try:
        if len(text) <= max_length:
            return text
            
        # Adjust for suffix
        target_length = max_length - len(suffix)
        
        if at_word_boundary:
            # Find last space before target length
            last_space = text.rfind(' ', 0, target_length)
            if last_space > 0:
                return text[:last_space] + suffix
                
        return text[:target_length] + suffix
        
    except Exception:
        return text

def format_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    headers: Optional[Dict[str, str]] = None,
    alignment: Optional[Dict[str, str]] = None,
    min_width: Optional[Dict[str, int]] = None,
    max_width: Optional[Dict[str, int]] = None,
    padding: int = 1,
    header_separator: bool = True
) -> str:
    """
    Format data as ASCII table
    
    Args:
        data: List of dictionaries
        columns: Column order
        headers: Column headers
        alignment: Column alignments (left, right, center)
        min_width: Minimum column widths
        max_width: Maximum column widths
        padding: Cell padding
        header_separator: Add separator after header
        
    Returns:
        Formatted table string
    """
    try:
        if not data:
            return ''
            
        # Get columns if not specified
        if not columns:
            columns = list(data[0].keys())
            
        # Get headers if not specified
        if not headers:
            headers = {col: col for col in columns}
            
        # Get alignments
        alignments = alignment or {}
        
        # Calculate column widths
        widths = {}
        for col in columns:
            # Get content widths
            content_widths = [
                len(str(row.get(col, '')))
                for row in data
            ]
            header_width = len(headers.get(col, col))
            
            # Apply min/max constraints
            width = max(content_widths + [header_width])
            if min_width and col in min_width:
                width = max(width, min_width[col])
            if max_width and col in max_width:
                width = min(width, max_width[col])
                
            widths[col] = width
            
        # Build format strings
        formats = {}
        for col in columns:
            align = alignments.get(col, 'left')
            width = widths[col]
            
            if align == 'right':
                formats[col] = f"{{:>{width}}}"
            elif align == 'center':
                formats[col] = f"{{:^{width}}}"
            else:
                formats[col] = f"{{:<{width}}}"
                
        # Build separator
        separator = '+'.join(
            '-' * (widths[col] + padding * 2)
            for col in columns
        )
        separator = f"+{separator}+"
        
        # Build header
        header_cells = [
            formats[col].format(
                truncate_text(
                    headers.get(col, col),
                    widths[col]
                )
            )
            for col in columns
        ]
        header = f"|{' ' * padding}"
        header += f"{' ' * padding}|{' ' * padding}".join(header_cells)
        header += f"{' ' * padding}|"
        
        # Build rows
        rows = []
        for row in data:
            cells = [
                formats[col].format(
                    truncate_text(
                        str(row.get(col, '')),
                        widths[col]
                    )
                )
                for col in columns
            ]
            row_str = f"|{' ' * padding}"
            row_str += f"{' ' * padding}|{' ' * padding}".join(cells)
            row_str += f"{' ' * padding}|"
            rows.append(row_str)
            
        # Combine parts
        parts = [separator, header]
        if header_separator:
            parts.append(separator)
        parts.extend(rows)
        parts.append(separator)
        
        return '\n'.join(parts)
        
    except Exception:
        return str(data)

def format_list(
    items: List[Any],
    bullet: str = '•',
    indent: int = 2,
    wrap_width: Optional[int] = None
) -> str:
    """
    Format items as bullet list
    
    Args:
        items: List items
        bullet: Bullet character
        indent: Indentation spaces
        wrap_width: Text wrap width
        
    Returns:
        Formatted list string
    """
    try:
        if not items:
            return ''
            
        # Format items
        formatted = []
        for item in items:
            # Convert to string
            text = str(item)
            
            # Wrap text
            if wrap_width:
                wrapped = wrap(
                    text,
                    width=wrap_width,
                    initial_indent=f"{' ' * indent}{bullet} ",
                    subsequent_indent=f"{' ' * (indent + 2)}"
                )
                formatted.extend(wrapped)
            else:
                formatted.append(f"{' ' * indent}{bullet} {text}")
                
        return '\n'.join(formatted)
        
    except Exception:
        return str(items)

def format_key_value(
    data: Dict[str, Any],
    separator: str = ': ',
    indent: int = 0,
    sort_keys: bool = True,
    wrap_width: Optional[int] = None
) -> str:
    """
    Format dictionary as key-value pairs
    
    Args:
        data: Dictionary data
        separator: Key-value separator
        indent: Indentation spaces
        sort_keys: Sort by keys
        wrap_width: Value wrap width
        
    Returns:
        Formatted string
    """
    try:
        if not data:
            return ''
            
        # Get items
        items = list(data.items())
        if sort_keys:
            items.sort(key=lambda x: str(x[0]))
            
        # Format items
        formatted = []
        for key, value in items:
            # Convert to strings
            key_str = str(key)
            value_str = str(value)
            
            # Wrap value
            if wrap_width:
                wrapped = wrap(
                    value_str,
                    width=wrap_width,
                    initial_indent='',
                    subsequent_indent=' ' * (len(key_str) + len(separator))
                )
                value_str = '\n'.join(wrapped)
                
            # Add to output
            formatted.append(
                f"{' ' * indent}{key_str}{separator}{value_str}"
            )
            
        return '\n'.join(formatted)
        
    except Exception:
        return str(data)
