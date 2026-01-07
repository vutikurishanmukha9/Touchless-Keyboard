"""
Logging configuration for Touchless Keyboard.

Provides structured logging with configurable levels and output formats.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


def setup_logger(name: str = "touchless_keyboard", 
                 level: int = logging.INFO,
                 log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up and return a configured logger.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
    
    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        from logging.handlers import RotatingFileHandler
        # 1MB max size, keep 3 backup files
        file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=3)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default application logger
logger = setup_logger()


def log_info(message: str):
    """Log info message."""
    logger.info(message)


def log_warning(message: str):
    """Log warning message."""
    logger.warning(message)


def log_error(message: str):
    """Log error message."""
    logger.error(message)


def log_debug(message: str):
    """Log debug message."""
    logger.debug(message)


def set_log_level(level: str):
    """
    Set logging level.
    
    Args:
        level: 'DEBUG', 'INFO', 'WARNING', or 'ERROR'
    """
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    if level.upper() in levels:
        logger.setLevel(levels[level.upper()])
        for handler in logger.handlers:
            handler.setLevel(levels[level.upper()])
