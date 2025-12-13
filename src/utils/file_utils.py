"""
File operations and clipboard management for Touchless Keyboard.

This module provides utilities for saving text to files and copying to clipboard
with proper error handling.
"""

import pyperclip
from datetime import datetime
from typing import Optional
from src.utils.exceptions import FileOperationError, ClipboardError


def save_text_to_file(text: str, filename: Optional[str] = None) -> bool:
    """
    Save typed text to a file with timestamp.
    
    Args:
        text: Text content to save
        filename: Optional custom filename (auto-generated if None)
    
    Returns:
        True if save successful, False otherwise
    
    Raises:
        FileOperationError: If file save fails
    """
    if not text:
        print(" No text to save!")
        return False
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"typed_text_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f" Text saved to {filename}")
        return True
    except IOError as e:
        raise FileOperationError(f"Failed to save file: {e}")
    except Exception as e:
        raise FileOperationError(f"Unexpected error saving file: {e}")


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
        print(" No text to copy!")
        return False
    
    try:
        pyperclip.copy(text)
        print(f" Copied {len(text)} characters to clipboard!")
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
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f" Loaded {len(content)} characters from {filename}")
        return content
    except FileNotFoundError:
        raise FileOperationError(f"File not found: {filename}")
    except IOError as e:
        raise FileOperationError(f"Failed to load file: {e}")
    except Exception as e:
        raise FileOperationError(f"Unexpected error loading file: {e}")
