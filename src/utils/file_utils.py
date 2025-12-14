"""
File operations and clipboard management for Touchless Keyboard.

This module provides utilities for saving text to files and copying to clipboard
with proper error handling, logging, and cross-platform path support.
"""

import os
import pyperclip
from datetime import datetime
from pathlib import Path
from typing import Optional
from src.utils.exceptions import FileOperationError, ClipboardError
from src.utils.logging_config import log_info, log_warning


def get_safe_path(filename: str, base_dir: Optional[str] = None) -> Path:
    """
    Get a safe, cross-platform file path.
    
    Args:
        filename: Filename (can include subdirectories)
        base_dir: Optional base directory (defaults to current working directory)
    
    Returns:
        Path object for the file
    """
    if base_dir:
        base = Path(base_dir)
    else:
        base = Path.cwd()
    
    # Sanitize filename - remove potentially dangerous characters
    safe_name = "".join(c for c in filename if c.isalnum() or c in '._- ')
    
    return base / safe_name


def save_text_to_file(text: str, filename: Optional[str] = None, 
                      directory: Optional[str] = None) -> bool:
    """
    Save typed text to a file with timestamp.
    
    Args:
        text: Text content to save
        filename: Optional custom filename (auto-generated if None)
        directory: Optional directory to save in
    
    Returns:
        True if save successful, False otherwise
    
    Raises:
        FileOperationError: If file save fails
    """
    if not text:
        log_warning("No text to save")
        return False
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"typed_text_{timestamp}.txt"
    
    try:
        if directory:
            filepath = Path(directory) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
        else:
            filepath = Path(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        log_info(f"Text saved to {filepath}")
        return True
    except PermissionError:
        raise FileOperationError(f"Permission denied: {filename}")
    except OSError as e:
        raise FileOperationError(f"Failed to save file: {e}")


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard.
    
    Args:
        text: Text content to copy
    
    Returns:
        True if copy successful, False otherwise
    
    Raises:
        ClipboardError: If clipboard operation fails
    """
    if not text:
        log_warning("No text to copy")
        return False
    
    try:
        pyperclip.copy(text)
        log_info(f"Copied {len(text)} characters to clipboard")
        return True
    except Exception as e:
        raise ClipboardError(f"Failed to copy to clipboard: {e}")


def load_text_from_file(filename: str) -> Optional[str]:
    """
    Load text from a file.
    
    Args:
        filename: Path to file to load
    
    Returns:
        File contents as string, or None if failed
    
    Raises:
        FileOperationError: If file load fails
    """
    filepath = Path(filename)
    
    if not filepath.exists():
        raise FileOperationError(f"File not found: {filename}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        log_info(f"Loaded {len(content)} characters from {filename}")
        return content
    except PermissionError:
        raise FileOperationError(f"Permission denied: {filename}")
    except OSError as e:
        raise FileOperationError(f"Failed to load file: {e}")


def sanitize_csv_value(value: str) -> str:
    """
    Sanitize a value for safe CSV writing.
    Prevents CSV injection attacks.
    
    Args:
        value: Raw value to sanitize
        
    Returns:
        Sanitized value safe for CSV
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove characters that could be used for formula injection
    dangerous_chars = ['=', '+', '-', '@', '\t', '\r', '\n']
    
    result = value
    for char in dangerous_chars:
        if result.startswith(char):
            result = "'" + result  # Escape by prefixing with single quote
            break
    
    # Escape quotes
    result = result.replace('"', '""')
    
    return result
