"""
Configuration file for Touchless Keyboard

This module contains all configuration constants for the virtual keyboard,
including screen dimensions, keyboard layout, gesture thresholds, and timing parameters.
"""

# === Screen Configuration ===
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# === Keyboard Layout Configuration ===
KEY_W, KEY_H = 60, 60  # Key width and height in pixels
GAP = 10  # Gap between keys in pixels

# Keyboard rows (QWERTY layout)
ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
KEYS = []

# Generate keyboard layout with centered rows
for row_i, row in enumerate(ROWS):
    row_len = len(row)
    total_width = row_len * KEY_W + (row_len - 1) * GAP
    start_x = (SCREEN_WIDTH - total_width) // 2
    y = SCREEN_HEIGHT - (3 - row_i) * (KEY_H + GAP) - 100
    for j, ch in enumerate(row):
        x = start_x + j * (KEY_W + GAP)
        KEYS.append({'key': ch, 'rect': (x, y, KEY_W, KEY_H)})

# Spacebar configuration
space_w = KEY_W * 5 + GAP * 4
space_x = (SCREEN_WIDTH - space_w) // 2
space_y = SCREEN_HEIGHT - KEY_H - 20
KEYS.append({'key': 'SPACE', 'rect': (space_x, space_y, space_w, KEY_H)})

# === Gesture Detection Thresholds ===
PINCH_THRESHOLD = 40  # Distance threshold for pinch gesture detection (pixels)
DWELL_TIME = 0.2  # Time to hover over key before activation (seconds)
DEBOUNCE_INTERVAL = 0.3  # Minimum time between consecutive key presses (seconds)

# === Hand Detection Configuration ===
DETECTION_CONFIDENCE = 0.8  # Confidence threshold for hand detection (0.0 - 1.0)
MAX_HANDS = 2  # Maximum number of hands to detect

# === UI Configuration ===
BORDER_RADIUS = 20  # Corner radius for rounded rectangles (pixels)
FLASH_DURATION = 0.3  # Duration of key flash animation (seconds)

# === Color Schemes (BGR format) ===
COLORS = {
    'key_default': (0, 0, 0),  # Black
    'key_highlight': (0, 255, 0),  # Green
    'key_pressed': (0, 255, 255),  # Yellow
    'text': (255, 255, 255),  # White
    'background': (50, 50, 50),  # Dark gray
    'hand_bbox': (0, 0, 255),  # Red
}
