"""
Keyboard rendering utilities for Touchless Keyboard.

This module provides functions for drawing keyboard keys with modern UI effects
including gradients, glow effects, and theme support.
Includes gradient caching for improved performance.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from src.utils.themes import get_theme, create_gradient

# Keyboard layout configurations
KEYBOARD_SYMBOLS = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '<-'],
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '!'],
    ['CAPS', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';'],
    ['SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '?'],
    ['__', 'ENTER', 'TAB', 'NUM']
]

# Numeric keypad layout
NUMPAD_SYMBOLS = [
    ['7', '8', '9', '/'],
    ['4', '5', '6', '*'],
    ['1', '2', '3', '-'],
    ['0', '.', '<-', '+'],
    ['ENTER', 'ABC']
]

# Current layout mode
_current_layout = 'qwerty'  # 'qwerty' or 'numpad'


def get_current_layout() -> str:
    """Get current keyboard layout mode."""
    return _current_layout


def set_layout(layout: str):
    """Set keyboard layout mode ('qwerty' or 'numpad')."""
    global _current_layout
    if layout in ('qwerty', 'numpad'):
        _current_layout = layout


def toggle_layout():
    """Toggle between QWERTY and numpad layouts."""
    global _current_layout
    _current_layout = 'numpad' if _current_layout == 'qwerty' else 'qwerty'
    return _current_layout

# === Gradient Cache ===
# Cache gradients by (height, width, color_top, color_bottom) to avoid recreating them every frame
_gradient_cache: Dict[tuple, np.ndarray] = {}
_mask_cache: Dict[tuple, np.ndarray] = {}
MAX_CACHE_SIZE = 100


def _get_cached_gradient(h: int, w: int, color_top: tuple, color_bottom: tuple) -> np.ndarray:
    """Get gradient from cache or create and cache it."""
    key = (h, w, color_top, color_bottom)
    
    if key not in _gradient_cache:
        # Clear cache if too large
        if len(_gradient_cache) > MAX_CACHE_SIZE:
            _gradient_cache.clear()
        _gradient_cache[key] = create_gradient(h, w, color_top, color_bottom)
    
    return _gradient_cache[key]


def _get_cached_mask(h: int, w: int, radius: int) -> np.ndarray:
    """Get rounded rectangle mask from cache or create and cache it."""
    key = (h, w, radius)
    
    if key not in _mask_cache:
        if len(_mask_cache) > MAX_CACHE_SIZE:
            _mask_cache.clear()
        
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.rectangle(mask, (radius, 0), (w - radius, h), 255, -1)
        cv2.rectangle(mask, (0, radius), (w, h - radius), 255, -1)
        cv2.circle(mask, (radius, radius), radius, 255, -1)
        cv2.circle(mask, (w - radius, radius), radius, 255, -1)
        cv2.circle(mask, (radius, h - radius), radius, 255, -1)
        cv2.circle(mask, (w - radius, h - radius), radius, 255, -1)
        
        _mask_cache[key] = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
    
    return _mask_cache[key]


def clear_gradient_cache():
    """Clear gradient and mask caches (call when theme changes)."""
    _gradient_cache.clear()
    _mask_cache.clear()


def draw_rounded_rect_gradient(img, top_left: Tuple[int, int], bottom_right: Tuple[int, int],
                               radius: int = 15, color_top: Tuple[int, int, int] = None,
                               color_bottom: Tuple[int, int, int] = None,
                               alpha: float = 0.85):
    """
    Draw a rounded rectangle with vertical gradient (cached for performance).
    """
    theme = get_theme()
    if color_top is None:
        color_top = theme['key_bg']
    if color_bottom is None:
        color_bottom = theme['key_bg_gradient']
    
    x1, y1 = top_left
    x2, y2 = bottom_right
    w = x2 - x1
    h = y2 - y1
    
    if w <= 0 or h <= 0:
        return
    
    # Get cached gradient and mask
    gradient = _get_cached_gradient(h, w, color_top, color_bottom)
    mask_3ch = _get_cached_mask(h, w, radius)
    
    # Blend with original image
    roi = img[y1:y2, x1:x2]
    if roi.shape[:2] == gradient.shape[:2]:
        blended = (gradient * mask_3ch * alpha + roi * (1 - mask_3ch * alpha)).astype(np.uint8)
        img[y1:y2, x1:x2] = blended


def draw_glow_border(img, top_left: Tuple[int, int], bottom_right: Tuple[int, int],
                     color: Tuple[int, int, int] = None, thickness: int = 3,
                     glow_size: int = 8):
    """
    Draw a glowing border around a rectangle.
    
    Args:
        img: Input image
        top_left: (x, y) top-left corner
        bottom_right: (x, y) bottom-right corner
        color: Glow color (BGR)
        thickness: Border thickness
        glow_size: Size of glow effect
    """
    theme = get_theme()
    if color is None:
        color = theme['glow_color']
    
    x1, y1 = top_left
    x2, y2 = bottom_right
    
    # Draw outer glow layers (fading)
    for i in range(glow_size, 0, -2):
        alpha = 0.1 * (glow_size - i) / glow_size
        overlay = img.copy()
        cv2.rectangle(overlay, (x1 - i, y1 - i), (x2 + i, y2 + i), color, 2)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    # Draw solid border
    cv2.rectangle(img, top_left, bottom_right, color, thickness)


def draw_key(img, pos: Tuple[int, int], text: str, highlight: bool = False,
             hover: bool = False, width: int = 90, height: int = 90,
             theme_name: str = None):
    """
    Draw a single keyboard key with gradient and optional glow effects.
    
    Args:
        img: Input image to draw on
        pos: (x, y) position of top-left corner
        text: Text to display on the key
        highlight: Whether key was just pressed (flash effect)
        hover: Whether finger is hovering over key
        width: Key width in pixels
        height: Key height in pixels
        theme_name: Optional theme override
    """
    theme = get_theme(theme_name)
    x, y = pos
    w, h = width, height
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Determine colors based on state
    if highlight:
        color_top = theme['key_pressed']
        color_bottom = tuple(max(0, c - 50) for c in theme['key_pressed'])
    elif hover:
        color_top = theme['key_hover']
        color_bottom = tuple(max(0, c - 30) for c in theme['key_hover'])
    else:
        color_top = theme['key_bg']
        color_bottom = theme['key_bg_gradient']
    
    # Draw gradient background
    draw_rounded_rect_gradient(img, (x, y), (x + w, y + h), radius=12,
                               color_top=color_top, color_bottom=color_bottom)
    
    # Add glow effect on hover
    if hover:
        draw_glow_border(img, (x, y), (x + w, y + h), theme['glow_color'])
    
    # Adjust font size based on text length
    if len(text) > 4:
        font_scale = 0.8
        thickness = 2
    elif len(text) > 2:
        font_scale = 1.0
        thickness = 2
    elif len(text) == 2:
        font_scale = 1.3
        thickness = 3
    else:
        font_scale = 1.8
        thickness = 3
    
    # Draw text centered on key
    text_color = theme['key_text']
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, font_scale, text_color, thickness)


def draw_rounded_rect(img, top_left: Tuple[int, int], bottom_right: Tuple[int, int],
                      radius: int = 20, color: Tuple[int, int, int] = (0, 0, 0),
                      thickness: int = -1):
    """
    Draw a rounded rectangle (legacy function for compatibility).
    """
    draw_rounded_rect_gradient(img, top_left, bottom_right, radius,
                               color_top=color, color_bottom=color)


def generate_keyboard_layout(start_x: int = 50, start_y: int = 100,
                            key_width: int = 85, key_height: int = 85,
                            gap: int = 12, layout: str = None) -> List[Tuple[int, int, int, int, str]]:
    """
    Generate keyboard key positions and dimensions.
    
    Args:
        start_x: Starting X position
        start_y: Starting Y position
        key_width: Width of standard keys
        key_height: Height of keys
        gap: Gap between keys
        layout: 'qwerty' or 'numpad' (uses current if None)
    
    Returns:
        List of tuples: (x, y, width, height, label)
    """
    if layout is None:
        layout = _current_layout
    
    symbols = KEYBOARD_SYMBOLS if layout == 'qwerty' else NUMPAD_SYMBOLS
    keys = []
    
    for row_index, row in enumerate(symbols):
        # Center each row with staggered offset (only for qwerty)
        row_offset = row_index * 25 if layout == 'qwerty' else 0
        y = start_y + row_index * (key_height + gap)
        
        current_x = start_x + row_offset
        
        for col_index, key in enumerate(row):
            # Calculate key width first
            if key == '__':
                w = int(key_width * 2.5)
            elif key in ['ENTER', 'SHIFT', 'CAPS']:
                w = int(key_width * 1.5)
            elif key in ['TAB', 'NUM', 'ABC']:
                w = int(key_width * 1.2)
            else:
                w = key_width
                
            keys.append((current_x, y, w, key_height, key))
            
            # Update x for next key
            current_x += w + gap
    
    return keys


def draw_text_bar(img, text: str, screen_width: int, y_pos: int = 20,
                  theme_name: str = None):
    """
    Draw the text preview bar at the top of the screen.
    Shows last ~70 characters with scroll indicator if truncated.
    """
    theme = get_theme(theme_name)
    text_bar_width = int(screen_width * 0.85)
    bar_height = 55
    
    # Draw gradient background
    draw_rounded_rect_gradient(img, (40, y_pos), (40 + text_bar_width, y_pos + bar_height),
                               radius=10, color_top=theme['text_bar_bg'],
                               color_bottom=tuple(max(0, c - 20) for c in theme['text_bar_bg']))
    
    # Display text (replace newlines/tabs for display)
    display_text = text.replace('\n', '↵ ').replace('\t', '→   ')
    
    # Calculate max chars based on screen width
    max_chars = min(70, text_bar_width // 14)
    is_truncated = len(display_text) > max_chars
    
    if is_truncated:
        display_text = '◀ ' + display_text[-(max_chars - 2):]
    
    # Main text
    cv2.putText(img, display_text, (55, y_pos + 38),
               cv2.FONT_HERSHEY_SIMPLEX, 0.9, theme['text_bar_text'], 2)
    
    # Character count (top right of bar)
    char_count = f"{len(text)} chars"
    cv2.putText(img, char_count, (text_bar_width - 80, y_pos + 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)


def draw_status_bar(img, fps: int, theme_name: str, screen_width: int,
                    screen_height: int, notification: str = ""):
    """
    Draw status bar at bottom of screen.
    
    Args:
        img: Image to draw on
        fps: Current FPS
        theme_name: Active theme name
        screen_width: Screen width
        screen_height: Screen height
        notification: Optional notification text
    """
    theme = get_theme(theme_name)
    y = screen_height - 40
    
    # FPS indicator
    cv2.putText(img, f"FPS: {fps}", (15, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, theme['indicator_ready'], 2)
    
    # Theme indicator
    cv2.putText(img, f"Theme: {theme_name.title()}", (screen_width - 180, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, theme['key_text'], 2)
    
    # Notification
    if notification:
        cv2.putText(img, notification, (screen_width // 2 - 100, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme['indicator_ready'], 2)
