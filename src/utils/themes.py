"""
Theme system for Touchless Keyboard.

Provides color themes and visual styling for the keyboard interface.
"""

import numpy as np
from typing import Dict, Tuple, Any


# Theme definitions
THEMES = {
    'dark': {
        'name': 'Dark',
        'key_bg': (30, 30, 30),           # Dark gray
        'key_bg_gradient': (60, 60, 60),  # Lighter gray for gradient
        'key_hover': (0, 150, 0),         # Green
        'key_pressed': (0, 255, 0),       # Bright green
        'key_text': (255, 255, 255),      # White
        'glow_color': (0, 255, 100),      # Green glow
        'text_bar_bg': (40, 40, 40),      # Dark gray
        'text_bar_text': (255, 255, 255), # White
        'hand_bbox': (0, 0, 255),         # Red
        'indicator_ready': (0, 255, 0),   # Green
        'indicator_wait': (0, 165, 255),  # Orange
    },
    'neon': {
        'name': 'Neon',
        'key_bg': (20, 10, 30),           # Dark purple
        'key_bg_gradient': (40, 20, 60),  # Lighter purple
        'key_hover': (255, 0, 255),       # Magenta
        'key_pressed': (255, 100, 255),   # Light magenta
        'key_text': (0, 255, 255),        # Cyan
        'glow_color': (255, 0, 255),      # Magenta glow
        'text_bar_bg': (30, 15, 45),      # Dark purple
        'text_bar_text': (0, 255, 255),   # Cyan
        'hand_bbox': (255, 0, 255),       # Magenta
        'indicator_ready': (0, 255, 255), # Cyan
        'indicator_wait': (255, 100, 0),  # Orange
    },
    'cyberpunk': {
        'name': 'Cyberpunk',
        'key_bg': (15, 15, 25),           # Dark blue-black
        'key_bg_gradient': (30, 30, 50),  # Lighter blue
        'key_hover': (0, 200, 255),       # Cyan
        'key_pressed': (255, 255, 0),     # Yellow
        'key_text': (255, 200, 50),       # Gold
        'glow_color': (0, 255, 255),      # Cyan glow
        'text_bar_bg': (20, 20, 35),      # Dark blue
        'text_bar_text': (255, 200, 50),  # Gold
        'hand_bbox': (0, 200, 255),       # Cyan
        'indicator_ready': (255, 255, 0), # Yellow
        'indicator_wait': (0, 150, 255),  # Blue
    },
    'light': {
        'name': 'Light',
        'key_bg': (220, 220, 225),        # Light gray
        'key_bg_gradient': (245, 245, 250), # Almost white
        'key_hover': (100, 200, 100),     # Light green
        'key_pressed': (50, 180, 50),     # Green
        'key_text': (30, 30, 30),         # Dark gray
        'glow_color': (100, 255, 100),    # Light green glow
        'text_bar_bg': (240, 240, 245),   # Very light gray
        'text_bar_text': (30, 30, 30),    # Dark gray
        'hand_bbox': (200, 50, 50),       # Dark red
        'indicator_ready': (50, 180, 50), # Green
        'indicator_wait': (255, 150, 50), # Orange
    },
    'high_contrast': {
        'name': 'High Contrast',
        'key_bg': (0, 0, 0),              # Pure Black
        'key_bg_gradient': (0, 0, 0),     # Pure Black
        'key_hover': (255, 255, 255),     # Pure White
        'key_pressed': (0, 255, 255),     # Yellow
        'key_text': (255, 255, 255),      # Pure White
        'glow_color': (255, 255, 0),      # Yellow glow
        'text_bar_bg': (0, 0, 0),         # Pure Black
        'text_bar_text': (255, 255, 0),   # Yellow
        'hand_bbox': (255, 255, 255),     # White
        'indicator_ready': (0, 255, 0),   # Green
        'indicator_wait': (255, 0, 0),    # Red
    },
}

# Current active theme
_current_theme = 'dark'


def get_theme(theme_name: str = None) -> Dict[str, Any]:
    """
    Get theme colors by name.
    
    Args:
        theme_name: Theme name ('dark', 'neon', 'cyberpunk', 'light')
                   If None, returns current active theme.
    
    Returns:
        Dictionary of color values
    """
    name = theme_name or _current_theme
    return THEMES.get(name, THEMES['dark'])


def set_theme(theme_name: str) -> bool:
    """
    Set the active theme.
    
    Args:
        theme_name: Theme name to activate
    
    Returns:
        True if theme was set successfully
    """
    global _current_theme
    if theme_name in THEMES:
        _current_theme = theme_name
        return True
    return False


def get_available_themes() -> list:
    """Get list of available theme names."""
    return list(THEMES.keys())


def create_gradient(height: int, width: int, 
                   color_top: Tuple[int, int, int], 
                   color_bottom: Tuple[int, int, int]) -> np.ndarray:
    """
    Create a vertical gradient image.
    
    Args:
        height: Image height
        width: Image width
        color_top: BGR color at top
        color_bottom: BGR color at bottom
    
    Returns:
        NumPy array with gradient
    """
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        ratio = y / max(height - 1, 1)
        b = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        r = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        gradient[y, :] = (b, g, r)
    
    return gradient


def apply_glow(img: np.ndarray, x: int, y: int, w: int, h: int, 
               color: Tuple[int, int, int], intensity: float = 0.5) -> np.ndarray:
    """
    Apply glow effect around a rectangle.
    
    Args:
        img: Input image
        x, y: Top-left corner
        w, h: Width and height
        color: Glow color (BGR)
        intensity: Glow intensity (0.0 - 1.0)
    
    Returns:
        Image with glow applied
    """
    import cv2
    
    # Create glow mask
    glow_size = 15
    mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.float32)
    
    # Draw filled rectangle on mask
    cv2.rectangle(mask, (x - glow_size, y - glow_size), 
                  (x + w + glow_size, y + h + glow_size), 1.0, -1)
    cv2.rectangle(mask, (x, y), (x + w, y + h), 0.0, -1)
    
    # Blur the mask for soft glow
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    
    # Apply glow color
    glow_layer = np.zeros_like(img, dtype=np.float32)
    glow_layer[:, :, 0] = mask * color[0]
    glow_layer[:, :, 1] = mask * color[1]
    glow_layer[:, :, 2] = mask * color[2]
    
    # Blend with original image
    result = img.astype(np.float32) + glow_layer * intensity
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    return result
