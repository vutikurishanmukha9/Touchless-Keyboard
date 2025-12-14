"""
Utility modules for configuration, exceptions, file operations, and performance monitoring.
"""

from src.utils.config import *
from src.utils.exceptions import (
    TouchlessKeyboardError,
    WebcamError,
    AudioError,
    CalibrationError,
    FileOperationError,
    ClipboardError
)
from src.utils.file_utils import save_text_to_file, copy_to_clipboard, load_text_from_file
from src.utils.performance_monitor import FPSCounter, PerformanceLogger
from src.utils.themes import get_theme, set_theme, get_available_themes, THEMES

__all__ = [
    # Exceptions
    'TouchlessKeyboardError',
    'WebcamError',
    'AudioError',
    'CalibrationError',
    'FileOperationError',
    'ClipboardError',
    # File utilities
    'save_text_to_file',
    'copy_to_clipboard',
    'load_text_from_file',
    # Performance
    'FPSCounter',
    'PerformanceLogger',
    # Themes
    'get_theme',
    'set_theme',
    'get_available_themes',
    'THEMES'
]
