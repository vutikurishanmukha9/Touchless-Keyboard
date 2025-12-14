"""
Touchless Keyboard - Main Application

Single-hand gesture-controlled virtual keyboard with:
- Modern UI with gradient keys and glow effects
- Multiple color themes (Dark, Neon, Cyberpunk, Light)
- Shift key support for lowercase/symbols
- Gesture smoothing and FPS monitoring
"""

import cv2
import pyautogui
from cvzone.HandTrackingModule import HandDetector
from screeninfo import get_monitors
import time
import os
import pygame

# Import shared modules
from src.core.keyboard_utils import (
    draw_key, generate_keyboard_layout, draw_text_bar, 
    draw_status_bar, draw_glow_border
)
from src.core.gesture_handler import GestureDetector, HandCalibration
from src.utils.file_utils import save_text_to_file, copy_to_clipboard
from src.utils.performance_monitor import FPSCounter
from src.utils.exceptions import WebcamError, FileOperationError, ClipboardError
from src.utils.themes import get_theme, set_theme, get_available_themes

# === Sound Setup ===
pygame.mixer.init()
try:
    audio_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "clickSound.mp3")
    click_sound = pygame.mixer.Sound(audio_path)
except (pygame.error, FileNotFoundError):
    click_sound = None
    print(" Warning: clickSound.mp3 not found. Audio feedback disabled.")

# === Monitor Info ===
monitors = get_monitors()
screen_width, screen_height = monitors[0].width, monitors[0].height

# === Configuration ===
SHOW_FPS = True
FLASH_DURATION = 0.25
current_theme = 'dark'
available_themes = get_available_themes()

# === Initialize Components ===
calibration = HandCalibration()
calibration.load_calibration()

gesture_detector = GestureDetector(
    click_delay=0.5,
    use_smoothing=True,
    calibration=calibration
)

fps_counter = FPSCounter(update_interval=1.0)
keys = generate_keyboard_layout(start_x=40, start_y=90)

# === Webcam Setup ===
try:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(screen_width * 0.85))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(screen_height * 0.75))
    
    if not cap.isOpened():
        raise WebcamError("Cannot access webcam. Please check camera permissions.")
except Exception as e:
    raise WebcamError(f"Webcam initialization failed: {e}")

# === Hand Detector ===
detector = HandDetector(detectionCon=0.8)

# === State Variables ===
typed_text = ""
key_flash = {}
notification_text = ""
notification_time = 0
shift_active = False
hovered_key = None

# === Main Loop ===
print(" Touchless Keyboard started successfully!")
print(" Modern UI with theme support")
print(" Controls: 's' save | 'c' copy | 't' theme | ESC quit")

while True:
    success, img = cap.read()
    if not success:
        print(" Warning: Failed to read frame")
        break

    hands, img = detector.findHands(img, draw=False)
    current_time = time.time()
    theme = get_theme()
    
    # Update FPS
    current_fps = fps_counter.update() if SHOW_FPS else 0
    
    # Reset hover state
    hovered_key = None
    
    # Check for keyboard shortcuts
    key_press = cv2.waitKey(1)
    if key_press == ord('s'):
        try:
            if save_text_to_file(typed_text):
                notification_text = "Saved!"
                notification_time = current_time
        except FileOperationError as e:
            notification_text = f"Save failed"
            notification_time = current_time
    elif key_press == ord('c'):
        try:
            if copy_to_clipboard(typed_text):
                notification_text = "Copied!"
                notification_time = current_time
        except ClipboardError:
            notification_text = "Copy failed"
            notification_time = current_time
    elif key_press == ord('t'):
        # Cycle through themes
        idx = available_themes.index(current_theme)
        current_theme = available_themes[(idx + 1) % len(available_themes)]
        set_theme(current_theme)
        notification_text = f"Theme: {current_theme.title()}"
        notification_time = current_time
    elif key_press & 0xFF == 27:
        print(" ESC pressed. Closing...")
        break

    if hands:
        for hand in hands:
            lmList = hand['lmList']
            bbox = hand['bbox']
            bbox_x, bbox_y, bbox_w, bbox_h = bbox
            
            # Draw hand bounding box with theme color
            cv2.rectangle(img, (bbox_x, bbox_y), (bbox_x + bbox_w, bbox_y + bbox_h), 
                         theme['hand_bbox'], 2)

            # Get landmark positions
            thumb_tip = lmList[4]
            index_tip = lmList[8]

            # Visual feedback: line between fingers
            cv2.line(img, tuple(thumb_tip[:2]), tuple(index_tip[:2]), theme['glow_color'], 3)
            mid_x = (thumb_tip[0] + index_tip[0]) // 2
            mid_y = (thumb_tip[1] + index_tip[1]) // 2
            cv2.circle(img, (mid_x, mid_y), 10, theme['glow_color'], -1)

            # Gesture detection
            click_detected, click_distance = gesture_detector.detect_click(lmList, current_time)
            exit_detected, _ = gesture_detector.detect_exit(lmList)

            # Distance indicator
            dist_color = theme['indicator_ready'] if click_distance < gesture_detector.calibration.get_click_threshold() else theme['indicator_wait']
            cv2.putText(img, f"{int(click_distance)}px", (mid_x + 15, mid_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, dist_color, 2)

            if exit_detected:
                print(" Exit gesture detected.")
                cap.release()
                cv2.destroyAllWindows()
                exit()

            # Check which key is being hovered
            tip_x, tip_y = index_tip[0], index_tip[1]
            for key_x, key_y, key_w, key_h, label in keys:
                if key_x < tip_x < key_x + key_w and key_y < tip_y < key_y + key_h:
                    hovered_key = label
                    
                    if click_detected:
                        if click_sound:
                            click_sound.play()

                        # Handle special keys
                        if label == 'SHIFT':
                            shift_active = not shift_active
                            notification_text = "Shift: ON" if shift_active else "Shift: OFF"
                            notification_time = current_time
                        elif label == '__':
                            pyautogui.press('space')
                            typed_text += ' '
                        elif label == '<-':
                            pyautogui.press('backspace')
                            typed_text = typed_text[:-1] if typed_text else ''
                        elif label == 'ENTER':
                            pyautogui.press('enter')
                            typed_text += '\n'
                        elif label == 'TAB':
                            pyautogui.press('tab')
                            typed_text += '\t'
                        else:
                            # Apply shift for letters
                            char = label.lower() if not shift_active else label
                            pyautogui.press(char)
                            typed_text += char if not shift_active else label
                            
                            # Auto-disable shift after character
                            if shift_active and label.isalpha():
                                shift_active = False
                        
                        key_flash[label] = current_time
                    break

    # === Draw UI Elements ===
    # Text bar at top
    draw_text_bar(img, typed_text, screen_width, y_pos=15, theme_name=current_theme)

    # Draw all keys
    for key_x, key_y, key_w, key_h, key in keys:
        is_highlighted = key in key_flash and current_time - key_flash[key] < FLASH_DURATION
        is_hovered = key == hovered_key
        is_shift_key = key == 'SHIFT' and shift_active
        
        draw_key(img, (key_x, key_y), key, 
                highlight=is_highlighted or is_shift_key,
                hover=is_hovered,
                width=int(key_w), height=int(key_h),
                theme_name=current_theme)

    # Status bar
    notif = notification_text if current_time - notification_time < 2.0 else ""
    draw_status_bar(img, int(current_fps), current_theme, screen_width, screen_height, notif)

    # Instructions
    cv2.putText(img, "'s' save | 'c' copy | 't' theme | ESC exit", 
               (15, screen_height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    cv2.imshow("Touchless Keyboard", img)

cap.release()
cv2.destroyAllWindows()
print(" Application closed successfully!")
