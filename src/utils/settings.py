"""
User settings persistence for Touchless Keyboard.

Saves and loads user preferences (theme, etc.) across sessions.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging_config import log_info, log_warning

# Default settings
DEFAULT_SETTINGS = {
    'theme': 'dark',
    'show_fps': True,
    'click_delay': 0.5,
    'flash_duration': 0.25,
    'exit_hold_time': 1.5,
    'target_fps': 30,
}

SETTINGS_FILE = Path.home() / '.touchless_keyboard' / 'settings.json'


def _ensure_config_dir() -> bool:
    """Ensure config directory exists."""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def load_settings() -> Dict[str, Any]:
    """
    Load user settings from file.
    
    Returns:
        Dictionary of settings (uses defaults for missing keys)
    """
    settings = DEFAULT_SETTINGS.copy()
    
    if not SETTINGS_FILE.exists():
        return settings
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        
        # Merge saved settings with defaults
        for key, value in saved.items():
            if key in settings:
                settings[key] = value
        
        log_info(f"Loaded settings from {SETTINGS_FILE}")
        return settings
    except (json.JSONDecodeError, OSError):
        return settings


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save user settings to file.
    
    Args:
        settings: Dictionary of settings to save
        
    Returns:
        True if save successful
    """
    if not _ensure_config_dir():
        return False
    
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        log_info(f"Settings saved to {SETTINGS_FILE}")
        return True
    except OSError:
        log_warning("Failed to save settings")
        return False


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a single setting value.
    
    Args:
        key: Setting key
        default: Default value if not found
        
    Returns:
        Setting value or default
    """
    settings = load_settings()
    return settings.get(key, default)


def update_setting(key: str, value: Any) -> bool:
    """
    Update a single setting and save.
    
    Args:
        key: Setting key
        value: New value
        
    Returns:
        True if save successful
    """
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)
