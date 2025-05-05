import os
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import uuid

def generate_unique_id() -> str:
    """
    Generate a unique ID using UUID4.
    
    Returns:
        A unique string ID
    """
    return str(uuid.uuid4())

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove invalid characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        The sanitized filename
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    return sanitized

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object as a string.
    
    Args:
        dt: The datetime object to format
        format_str: The format string to use
        
    Returns:
        The formatted datetime string
    """
    return dt.strftime(format_str)

def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse a datetime string into a datetime object.
    
    Args:
        dt_str: The datetime string to parse
        format_str: The format string to use
        
    Returns:
        The parsed datetime object
    """
    return datetime.strptime(dt_str, format_str)

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: The path to the directory
    """
    os.makedirs(directory_path, exist_ok=True)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        file_path: The path to the JSON file
        
    Returns:
        The loaded JSON data
    """
    with open(file_path, "r") as f:
        return json.load(f)

def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to a JSON file.
    
    Args:
        file_path: The path to the JSON file
        data: The data to save
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: The text to truncate
        max_length: The maximum length
        suffix: The suffix to add if truncated
        
    Returns:
        The truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
