"""
Custom exceptions for Touchless Keyboard application.

This module defines a hierarchy of custom exceptions for better error handling
and more specific error messages throughout the application.
"""


class TouchlessKeyboardError(Exception):
    """Base exception for all Touchless Keyboard errors."""
    pass


class WebcamError(TouchlessKeyboardError):
    """Raised when webcam cannot be accessed or initialized."""
    pass


class AudioError(TouchlessKeyboardError):
    """Raised when audio file cannot be loaded or played."""
    pass


class CalibrationError(TouchlessKeyboardError):
    """Raised when hand calibration fails."""
    pass


class FileOperationError(TouchlessKeyboardError):
    """Raised when file save/load operations fail."""
    pass


class ClipboardError(TouchlessKeyboardError):
    """Raised when clipboard operations fail."""
    pass
