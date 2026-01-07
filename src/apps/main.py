"""
Touchless Keyboard - Main Application

Single-hand gesture-controlled virtual keyboard with:
- Modern UI with gradient keys and glow effects
- Multiple color themes (Dark, Neon, Cyberpunk, Light)
- Shift key support for lowercase/symbols
- Gesture smoothing and FPS monitoring
- Robust error handling and resource management
"""

import cv2
import pyautogui
from cvzone.HandTrackingModule import HandDetector
from screeninfo import get_monitors
import time
import os
import sys

# Import shared modules
from src.core.keyboard_utils import (
    draw_key, generate_keyboard_layout, draw_text_bar, 
    draw_status_bar, draw_glow_border, clear_gradient_cache,
    toggle_layout, get_current_layout
)
from src.core.gesture_handler import GestureDetector, HandCalibration
from src.utils.file_utils import save_text_to_file, copy_to_clipboard
from src.utils.performance_monitor import FPSCounter
from src.utils.exceptions import WebcamError, FileOperationError, ClipboardError
from src.utils.themes import get_theme, set_theme, get_available_themes
from src.utils.logging_config import log_info, log_warning, log_error
from src.utils.settings import load_settings, update_setting
from src.core.calibration import run_calibration_mode

# === Configuration ===
WEBCAM_INDEX = int(os.environ.get('WEBCAM_INDEX', 0))  # Configurable via env var
TARGET_FPS = 30  # Frame rate limit
FLASH_DURATION = 0.25
KEY_FLASH_CLEANUP_INTERVAL = 5.0  # Clean old entries every 5 seconds
EXIT_GESTURE_HOLD_TIME = 1.5  # Must hold exit gesture for 1.5 seconds
HAND_CONFIDENCE_THRESHOLD = 0.7  # Minimum hand detection confidence

# === Sound Setup ===
click_sound = None
try:
    import pygame
    pygame.mixer.init()
    audio_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "clickSound.mp3")
    if os.path.exists(audio_path):
        click_sound = pygame.mixer.Sound(audio_path)
        log_info("Audio feedback enabled")
    else:
        log_warning("clickSound.mp3 not found. Audio feedback disabled.")
except Exception as e:
    log_warning(f"Pygame audio init failed: {e}. Audio feedback disabled.")


def cleanup_key_flash(key_flash: dict, current_time: float, max_age: float = 2.0) -> dict:
    """Remove old entries from key_flash dict to prevent memory leak."""
    return {k: v for k, v in key_flash.items() if current_time - v < max_age}


class TextHistory:
    """Manages text history for undo/redo functionality."""
    
    def __init__(self, max_history: int = 50):
        self.history = [""]
        self.position = 0
        self.max_history = max_history
    
    def push(self, text: str):
        """Add new text state to history."""
        # Remove any redo states
        self.history = self.history[:self.position + 1]
        self.history.append(text)
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.position += 1
    
    def undo(self) -> str:
        """Undo to previous state."""
        if self.position > 0:
            self.position -= 1
        return self.history[self.position]
    
    def redo(self) -> str:
        """Redo to next state."""
        if self.position < len(self.history) - 1:
            self.position += 1
        return self.history[self.position]
    
    def current(self) -> str:
        """Get current text state."""
        return self.history[self.position]


def draw_help_overlay(img, screen_width: int, screen_height: int):
    """Draw semi-transparent help overlay with keyboard controls."""
    # Semi-transparent background
    overlay = img.copy()
    cv2.rectangle(overlay, (50, 50), (screen_width - 50, screen_height - 100), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.9, img, 0.1, 0, img)
    
    # Title
    cv2.putText(img, "KEYBOARD SHORTCUTS", (screen_width // 2 - 180, 100),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
    
    # Controls list
    controls = [
        ("ESC", "Exit application"),
        ("h", "Toggle this help"),
        ("s", "Save text to file"),
        ("c", "Copy text to clipboard"),
        ("t", "Cycle themes"),
        ("n", "Toggle numpad"),
        ("k", "Calibrate gestures"),
        ("+/-", "Scale keyboard size"),
        ("u", "Undo"),
        ("r", "Redo"),
        ("[/]", "Adjust volume"),
    ]
    
    y = 160
    for key, desc in controls:
        cv2.putText(img, f"{key:>6}", (100, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
        cv2.putText(img, f"  {desc}", (200, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        y += 40
    
    # Footer
    cv2.putText(img, "Press 'h' to close", (screen_width // 2 - 100, screen_height - 130),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 1)


def main():
    """Main application entry point with proper resource management."""
    
    # === Monitor Info ===
    monitors = get_monitors()
    screen_width, screen_height = monitors[0].width, monitors[0].height
    
    # === State Variables ===
    # Load saved settings
    user_settings = load_settings()
    current_theme = user_settings.get('theme', 'dark')
    set_theme(current_theme)
    
    # Setup logging
    from src.utils.settings import get_log_file_path, get_setting
    from src.utils.logging_config import setup_logger
    import logging
    
    log_file = get_log_file_path()
    setup_logger(log_file=log_file)
    if log_file:
        log_info(f"Logging to file: {log_file}")
    
    available_themes = get_available_themes()
    typed_text = ""
    key_flash = {}
    notification_text = ""
    notification_time = 0
    shift_active = False
    caps_lock = False
    hovered_key = None
    last_cleanup_time = time.time()
    exit_gesture_start = None
    last_frame_time = time.time()
    keyboard_scale = 1.0
    help_visible = False
    volume = 0.7
    text_history = TextHistory(max_history=50)
    
    # Show theme on startup
    notification_text = f"Theme: {current_theme.title()} | Press 'h' for help"
    notification_time = time.time()
    
    # === Initialize Components ===
    calibration = HandCalibration()
    calibration.load_calibration()
    
    gesture_detector = GestureDetector(
        click_delay=user_settings.get('click_delay', 0.5),
        use_smoothing=True,
        smoothing_factor=user_settings.get('smoothing_factor', 0.5),
        calibration=calibration
    )
    
    fps_counter = FPSCounter(update_interval=1.0)
    
    # === Responsive Keyboard Layout ===
    base_key_size = min(screen_width // 18, screen_height // 12)
    key_size = max(60, min(95, base_key_size))
    key_gap = max(8, key_size // 10)
    keys = generate_keyboard_layout(start_x=30, start_y=85, 
                                    key_width=key_size, key_height=key_size, gap=key_gap)
    log_info(f"Keyboard layout: {key_size}px keys, gap {key_gap}px")
    
    # === Webcam Setup ===
    cap = None
    try:
        cap = cv2.VideoCapture(WEBCAM_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(screen_width * 0.85))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(screen_height * 0.75))
        
        if not cap.isOpened():
            raise WebcamError(f"Cannot access webcam at index {WEBCAM_INDEX}.")
        log_info(f"Webcam initialized at index {WEBCAM_INDEX}")
    except Exception as e:
        log_error(f"Webcam initialization failed: {e}")
        if cap:
            cap.release()
        raise WebcamError(f"Webcam initialization failed: {e}")
    
    # === Hand Detector ===
    detector = HandDetector(detectionCon=HAND_CONFIDENCE_THRESHOLD)
    
    log_info("Touchless Keyboard started successfully!")
    log_info("Controls: 's' save | 'c' copy | 't' theme | 'k' calibrate | ESC quit")
    
    try:
        while True:
            # === Frame Rate Limiting ===
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed < 1.0 / TARGET_FPS:
                time.sleep((1.0 / TARGET_FPS) - elapsed)
                current_time = time.time()
            last_frame_time = current_time
            
            # === Read Frame ===
            success, img = cap.read()
            if not success:
                log_warning("Failed to read frame from webcam")
                continue  # Try again instead of breaking
            
            # === Periodic Cleanup ===
            if current_time - last_cleanup_time > KEY_FLASH_CLEANUP_INTERVAL:
                key_flash = cleanup_key_flash(key_flash, current_time)
                last_cleanup_time = current_time
            
            # === Hand Detection ===
            hands, img = detector.findHands(img, draw=False)
            theme = get_theme()
            
            # Update FPS
            current_fps = fps_counter.update()
            
            # Reset hover state
            hovered_key = None
            
            # === Keyboard Shortcuts ===
            key_press = cv2.waitKey(1)
            if key_press == ord('s'):
                try:
                    if save_text_to_file(typed_text):
                        notification_text = "Saved!"
                        notification_time = current_time
                except FileOperationError:
                    notification_text = "Save failed"
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
                idx = available_themes.index(current_theme)
                current_theme = available_themes[(idx + 1) % len(available_themes)]
                set_theme(current_theme)
                clear_gradient_cache()  # Clear cached gradients for new theme
                update_setting('theme', current_theme)  # Save theme
                notification_text = f"Theme: {current_theme.title()}"
                notification_time = current_time
            elif key_press == ord('k'):
                log_info("Entering calibration mode...")
                new_calibration = run_calibration_mode(cap, screen_width, screen_height)
                if new_calibration:
                    calibration = new_calibration
                    gesture_detector.calibration = calibration
                    notification_text = "Calibration saved!"
                    notification_time = time.time()
            elif key_press == ord('n'):
                # Toggle numpad layout
                new_layout = toggle_layout()
                keys = generate_keyboard_layout(start_x=30, start_y=85, 
                                                key_width=int(key_size * keyboard_scale), 
                                                key_height=int(key_size * keyboard_scale), 
                                                gap=key_gap)
                notification_text = f"Layout: {new_layout.upper()}"
                notification_time = current_time
            elif key_press == ord('=') or key_press == ord('+'):
                # Increase keyboard size
                if keyboard_scale < 1.5:
                    keyboard_scale = min(1.5, keyboard_scale + 0.1)
                    keys = generate_keyboard_layout(start_x=30, start_y=85, 
                                                    key_width=int(key_size * keyboard_scale), 
                                                    key_height=int(key_size * keyboard_scale), 
                                                    gap=key_gap)
                    notification_text = f"Scale: {keyboard_scale:.1f}x"
                    notification_time = current_time
            elif key_press == ord('-'):
                # Decrease keyboard size
                if keyboard_scale > 0.8:
                    keyboard_scale = max(0.8, keyboard_scale - 0.1)
                    keys = generate_keyboard_layout(start_x=30, start_y=85, 
                                                    key_width=int(key_size * keyboard_scale), 
                                                    key_height=int(key_size * keyboard_scale), 
                                                    gap=key_gap)
                    notification_text = f"Scale: {keyboard_scale:.1f}x"
                    notification_time = current_time
            elif key_press == ord('h'):
                help_visible = not help_visible
            elif key_press == ord('u'):
                typed_text = text_history.undo()
                notification_text = "Undo"
                notification_time = current_time
            elif key_press == ord('r'):
                typed_text = text_history.redo()
                notification_text = "Redo"
                notification_time = current_time
            elif key_press == ord(']'):
                if volume < 1.0:
                    volume = min(1.0, volume + 0.1)
                    if click_sound: click_sound.set_volume(volume)
                    notification_text = f"Vol: {int(volume*100)}%"
                    notification_time = current_time
            elif key_press == ord('['):
                if volume > 0.0:
                    volume = max(0.0, volume - 0.1)
                    if click_sound: click_sound.set_volume(volume)
                    notification_text = f"Vol: {int(volume*100)}%"
                    notification_time = current_time
            elif key_press & 0xFF == 27:
                log_info("ESC pressed. Exiting...")
                break
            
            # === Process Hands ===
            if hands:
                # Reset smoothing buffer when hand reappears
                hand = hands[0]
                lmList = hand['lmList']
                bbox = hand['bbox']
                
                # Draw hand bounding box
                bbox_x, bbox_y, bbox_w, bbox_h = bbox
                cv2.rectangle(img, (bbox_x, bbox_y), (bbox_x + bbox_w, bbox_y + bbox_h), 
                             theme['hand_bbox'], 2)
                
                # Get landmark positions
                thumb_tip = lmList[4]
                index_tip = lmList[8]
                
                # Visual feedback
                cv2.line(img, tuple(thumb_tip[:2]), tuple(index_tip[:2]), theme['glow_color'], 3)
                mid_x = (thumb_tip[0] + index_tip[0]) // 2
                mid_y = (thumb_tip[1] + index_tip[1]) // 2
                cv2.circle(img, (mid_x, mid_y), 10, theme['glow_color'], -1)
                
                # Gesture detection
                click_detected, click_distance = gesture_detector.detect_click(lmList, current_time)
                exit_detected, _ = gesture_detector.detect_exit(lmList)
                
                # Distance indicator
                threshold = gesture_detector.calibration.get_click_threshold()
                dist_color = theme['indicator_ready'] if click_distance < threshold else theme['indicator_wait']
                cv2.putText(img, f"{int(click_distance)}px", (mid_x + 15, mid_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, dist_color, 2)
                
                # === Exit Gesture with Debounce ===
                if exit_detected:
                    if exit_gesture_start is None:
                        exit_gesture_start = current_time
                    elif current_time - exit_gesture_start >= EXIT_GESTURE_HOLD_TIME:
                        log_info("Exit gesture held. Exiting...")
                        break
                    else:
                        # Show countdown
                        remaining = EXIT_GESTURE_HOLD_TIME - (current_time - exit_gesture_start)
                        cv2.putText(img, f"Exit in {remaining:.1f}s", (mid_x - 40, mid_y - 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    exit_gesture_start = None  # Reset if gesture released
                
                # Check which key is being hovered
                tip_x, tip_y = index_tip[0], index_tip[1]
                for key_x, key_y, key_w, key_h, label in keys:
                    if key_x < tip_x < key_x + key_w and key_y < tip_y < key_y + key_h:
                        hovered_key = label
                        
                        if click_detected:
                            if click_sound:
                                try:
                                    click_sound.play()
                                except Exception:
                                    pass  # Ignore audio errors
                            
                            # Handle special keys
                            if label == 'SHIFT':
                                shift_active = not shift_active
                                notification_text = "Shift: ON" if shift_active else "Shift: OFF"
                                notification_time = current_time
                            elif label == '__':
                                pyautogui.press('space')
                                text_history.push(typed_text + ' ')
                                typed_text += ' '
                            elif label == '<-':
                                pyautogui.press('backspace')
                                if typed_text:
                                    text_history.push(typed_text[:-1])
                                    typed_text = typed_text[:-1]
                            elif label == 'ENTER':
                                pyautogui.press('enter')
                                text_history.push(typed_text + '\n')
                                typed_text += '\n'
                            elif label == 'TAB':
                                pyautogui.press('tab')
                                text_history.push(typed_text + '\t')
                                typed_text += '\t'
                            elif label == 'CAPS':
                                caps_lock = not caps_lock
                                notification_text = "CAPS: ON" if caps_lock else "CAPS: OFF"
                                notification_time = current_time
                            elif label == 'NUM':
                                new_layout = toggle_layout()
                                keys = generate_keyboard_layout(start_x=30, start_y=85, 
                                                                key_width=int(key_size * keyboard_scale), 
                                                                key_height=int(key_size * keyboard_scale), 
                                                                gap=key_gap)
                                notification_text = "Numpad Mode"
                                notification_time = current_time
                            elif label == 'ABC':
                                new_layout = toggle_layout()
                                keys = generate_keyboard_layout(start_x=30, start_y=85, 
                                                                key_width=int(key_size * keyboard_scale), 
                                                                key_height=int(key_size * keyboard_scale), 
                                                                gap=key_gap)
                                notification_text = "QWERTY Mode"
                                notification_time = current_time
                            elif label in ['+', '-', '*', '/']:
                                # Numpad operators
                                pyautogui.press(label)
                                text_history.push(typed_text + label)
                                typed_text += label
                            else:
                                # Regular character - apply caps/shift logic
                                use_upper = caps_lock or shift_active
                                char = label.upper() if use_upper else label.lower()
                                pyautogui.press(char.lower())  # pyautogui uses lowercase
                                text_history.push(typed_text + char)
                                typed_text += char
                                
                                # SHIFT auto-disables, CAPS persists
                                if shift_active and label.isalpha():
                                    shift_active = False
                            
                            key_flash[label] = current_time
                        break
            else:
                # Reset smoothing when hand disappears
                gesture_detector.reset_smoothing()
                exit_gesture_start = None
            
            # === Draw UI Elements ===
            draw_text_bar(img, typed_text, screen_width, y_pos=15, theme_name=current_theme)
            
            for key_x, key_y, key_w, key_h, key in keys:
                is_highlighted = key in key_flash and current_time - key_flash[key] < FLASH_DURATION
                is_hovered = key == hovered_key
                is_shift_key = key == 'SHIFT' and shift_active
                
                draw_key(img, (key_x, key_y), key, 
                        highlight=is_highlighted or is_shift_key,
                        hover=is_hovered,
                        width=int(key_w), height=int(key_h),
                        theme_name=current_theme)
            
            notif = notification_text if current_time - notification_time < 2.0 else ""
            draw_status_bar(img, int(current_fps), current_theme, screen_width, screen_height, notif)
            
            
            cv2.putText(img, "Press 'h' for help | ESC to exit", 
                       (15, screen_height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
            
            if help_visible:
                draw_help_overlay(img, screen_width, screen_height)
            
            cv2.imshow("Touchless Keyboard", img)
            
    except KeyboardInterrupt:
        log_info("Interrupted by user")
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        raise
    finally:
        # === Guaranteed Cleanup ===
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        log_info("Application closed. Resources released.")


if __name__ == "__main__":
    main()