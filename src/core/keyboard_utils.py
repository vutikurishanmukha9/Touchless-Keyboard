"""
Keyboard rendering utilities for Touchless Keyboard.

This module provides functions for drawing keyboard keys and managing keyboard layout.
"""

import cv2
from typing import List, Tuple

# Keyboard layout configuration
KEYBOARD_SYMBOLS = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '<-'],
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '!'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'"],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '?'],
    ['__', 'ENTER', 'TAB']
]


def draw_rounded_rect(img, top_left: Tuple[int, int], bottom_right: Tuple[int, int], 
                      radius: int = 20, color: Tuple[int, int, int] = (0, 0, 0), 
                      thickness: int = -1):
    """
    Draw a rounded rectangle on the image with alpha blending.
    
    Args:
        img (np.ndarray): Input image to draw on
        top_left: (x, y) coordinates of top-left corner
        bottom_right: (x, y) coordinates of bottom-right corner
        radius: Corner radius in pixels (default: 20)
        color: BGR color tuple (default: black)
        thickness: Line thickness, -1 for filled (default: -1)
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    overlay = img.copy()
    
    # Draw rectangles and circles to form rounded rectangle
    cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    cv2.circle(overlay, (x1 + radius, y1 + radius), radius, color, thickness)
    cv2.circle(overlay, (x2 - radius, y1 + radius), radius, color, thickness)
    cv2.circle(overlay, (x1 + radius, y2 - radius), radius, color, thickness)
    cv2.circle(overlay, (x2 - radius, y2 - radius), radius, color, thickness)
    
    # Alpha blend
    cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)


def draw_key(img, pos: Tuple[int, int], text: str, highlight: bool = False, 
             width: int = 90, height: int = 90):
    """
    Draw a single keyboard key with text.
    
    Args:
        img (np.ndarray): Input image to draw on
        pos: (x, y) position of top-left corner
        text: Text to display on the key
        highlight: Whether to highlight the key (default: False)
        width: Key width in pixels (default: 90)
        height: Key height in pixels (default: 90)
    """
    x, y = pos
    w, h = width, height
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Adjust font size based on text length
    if len(text) > 3:
        font_scale = 1.2
        thickness = 3
    elif len(text) == 2:
        font_scale = 1.5
        thickness = 3
    else:
        font_scale = 2
        thickness = 4
    
    text_color = (255, 255, 255)
    key_color = (0, 255, 0) if highlight else (0, 0, 0)

    # Draw key background
    draw_rounded_rect(img, (x, y), (x + w, y + h), radius=20, color=key_color, thickness=-1)
    
    # Draw text centered on key
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, font_scale, text_color, thickness)


def generate_keyboard_layout(start_x: int = 50, start_y: int = 100, 
                            key_width: int = 90, key_height: int = 90, 
                            gap: int = 20) -> List[Tuple[int, int, int, int, str]]:
    """
    Generate keyboard key positions and dimensions.
    
    Args:
        start_x: Starting X position (default: 50)
        start_y: Starting Y position (default: 100)
        key_width: Width of standard keys (default: 90)
        key_height: Height of keys (default: 90)
        gap: Gap between keys (default: 20)
    
    Returns:
        List of tuples: (x, y, width, height, label)
    """
    keys = []
    
    for row_index, row in enumerate(KEYBOARD_SYMBOLS):
        row_start_x = start_x + row_index * 40  # Offset each row
        y = start_y + row_index * (key_height + gap)
        
        for col_index, key in enumerate(row):
            x = row_start_x + col_index * (key_width + gap)
            
            # Make special keys wider
            if key in ['__', 'ENTER', 'TAB']:
                w = key_width * 2 if key == '__' else key_width * 1.5
                keys.append((x, y, w, key_height, key))
            else:
                keys.append((x, y, key_width, key_height, key))
    
    return keys


def draw_text_bar(img, text: str, screen_width: int, y_pos: int = 20):
    """
    Draw the text preview bar at the top of the screen.
    
    Args:
        img: Image to draw on
        text: Text to display
        screen_width: Screen width for calculating bar width
        y_pos: Y position of the bar (default: 20)
    """
    text_bar_width = int(screen_width * 0.8)
    draw_rounded_rect(img, (50, y_pos), (50 + text_bar_width, y_pos + 60), 
                     radius=20, color=(50, 50, 50), thickness=-1)
    
    # Display text (replace newlines/tabs with spaces for display)
    display_text = text.replace('\n', ' ').replace('\t', ' ')
    cv2.putText(img, display_text[-60:], (60, y_pos + 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 3)
