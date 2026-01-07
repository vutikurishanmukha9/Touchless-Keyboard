"""
Touchless Keyboard - AI Version

Dual-hand gesture-controlled virtual keyboard with ML data collection:
- Left hand: Click and exit gestures
- Right hand: Cursor navigation
- Modern UI with themes and gradient keys
- Robust error handling and resource management
- ML gesture data logging
"""

import cv2
import pyautogui
from cvzone.HandTrackingModule import HandDetector
from screeninfo import get_monitors
import time
import os
import sys
import csv
from pathlib import Path

# Import shared modules
from src.core.keyboard_utils import (
    draw_key, generate_keyboard_layout, draw_text_bar, 
    draw_status_bar, clear_gradient_cache
)
from src.core.gesture_handler import GestureDetector, HandCalibration
from src.utils.file_utils import save_text_to_file, copy_to_clipboard, sanitize_csv_value
from src.utils.performance_monitor import FPSCounter
from src.utils.exceptions import WebcamError, FileOperationError, ClipboardError
from src.utils.themes import get_theme, set_theme, get_available_themes
from src.utils.logging_config import log_info, log_warning, log_error
from src.utils.settings import load_settings, update_setting
from src.core.calibration import run_calibration_mode

# === Configuration ===
WEBCAM_INDEX = int(os.environ.get('WEBCAM_INDEX', 0))
TARGET_FPS = 30
FLASH_DURATION = 0.25
KEY_FLASH_CLEANUP_INTERVAL = 5.0
EXIT_GESTURE_HOLD_TIME = 1.5
HAND_CONFIDENCE_THRESHOLD = 0.7

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
        log_warning("clickSound.mp3 not found. Audio disabled.")
except Exception as e:
    log_warning(f"Pygame audio init failed: {e}")


def save_landmark_data(lmList, label: str) -> bool:
    """
    Save hand landmark data to CSV for ML training.
    Includes input sanitization to prevent CSV injection.
    """
    if not lmList or len(lmList) != 21:
        return False
    
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    data_path = data_dir / "gesture_data.csv"
    
    try:
        with open(data_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            row = [coord for point in lmList for coord in point[:3]]
            row.append(sanitize_csv_value(label))
            writer.writerow(row)
        log_info(f"Gesture data saved: {label}")
        return True
    except Exception as e:
        log_warning(f"Failed to save gesture data: {e}")
        return False


def cleanup_key_flash(key_flash: dict, current_time: float, max_age: float = 2.0) -> dict:
    """Remove old entries from key_flash dict."""
    return {k: v for k, v in key_flash.items() if current_time - v < max_age}


def main():
    """Main application entry point with proper resource management."""
    
    # === Monitor Info ===
    monitors = get_monitors()
    screen_width, screen_height = monitors[0].width, monitors[0].height
    
    # === Load Settings ===
    user_settings = load_settings()
    current_theme = user_settings.get('theme', 'dark')
    set_theme(current_theme)
    available_themes = get_available_themes()
    
    # === State Variables ===
    typed_text = ""
    key_flash = {}
    notification_text = ""
    notification_time = 0
    shift_active = False
    last_cleanup_time = time.time()
    exit_gesture_start = None
    last_frame_time = time.time()
    click_detected = False
    
    # === Initialize Components ===
    calibration = HandCalibration()
    calibration.load_calibration()
    
    gesture_detector = GestureDetector(
        click_delay=0.5,
        use_smoothing=True,
        calibration=calibration
    )
    
    fps_counter = FPSCounter(update_interval=1.0)
    
    # === Responsive Keyboard Layout ===
    base_key_size = min(screen_width // 18, screen_height // 12)
    key_size = max(60, min(95, base_key_size))
    key_gap = max(8, key_size // 10)
    keys = generate_keyboard_layout(start_x=30, start_y=85, 
                                    key_width=key_size, key_height=key_size, gap=key_gap)
    log_info(f"AI Keyboard: {key_size}px keys, gap {key_gap}px")
    
    # === Webcam Setup ===
    cap = None
    try:
        cap = cv2.VideoCapture(WEBCAM_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(screen_width * 0.85))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(screen_height * 0.75))
        
        if not cap.isOpened():
            raise WebcamError(f"Cannot access webcam at index {WEBCAM_INDEX}")
        log_info(f"Webcam initialized at index {WEBCAM_INDEX}")
    except Exception as e:
        log_error(f"Webcam initialization failed: {e}")
        if cap:
            cap.release()
        raise WebcamError(f"Webcam initialization failed: {e}")
    
    # === Hand Detector ===
    detector = HandDetector(detectionCon=HAND_CONFIDENCE_THRESHOLD)
    
    log_info("AI Keyboard started! Left hand: gestures | Right hand: navigate")
    log_info("Controls: 's' save | 'c' copy | 't' theme | 'k' calibrate | ESC quit")
    log_info("ML logging: Press 'l' + gesture to log landmark data")
    
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
                log_warning("Failed to read frame")
                continue
            
            # === Periodic Cleanup ===
            if current_time - last_cleanup_time > KEY_FLASH_CLEANUP_INTERVAL:
                key_flash = cleanup_key_flash(key_flash, current_time)
                last_cleanup_time = current_time
            
            # === Hand Detection ===
            hands, img = detector.findHands(img, draw=False)
            theme = get_theme()
            current_fps = fps_counter.update()
            
            # Reset click state each frame
            click_detected = False
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
                clear_gradient_cache()
                update_setting('theme', current_theme)
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
            elif key_press & 0xFF == 27:
                log_info("ESC pressed. Exiting...")
                break
            
            # === Process Hands ===
            left_hand = None
            right_hand = None
            
            for hand in hands:
                if hand['type'] == 'Left':
                    left_hand = hand
                elif hand['type'] == 'Right':
                    right_hand = hand
            
            # === LEFT HAND: Gesture Detection ===
            if left_hand:
                lmList = left_hand['lmList']
                bbox = left_hand['bbox']
                
                # Draw bounding box
                bbox_x, bbox_y, bbox_w, bbox_h = bbox
                cv2.rectangle(img, (bbox_x, bbox_y), (bbox_x + bbox_w, bbox_y + bbox_h), 
                             theme['glow_color'], 2)
                
                # Visual feedback
                thumb_tip = lmList[4]
                index_tip = lmList[8]
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
                cv2.putText(img, f"L: {int(click_distance)}px", (mid_x + 15, mid_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, dist_color, 2)
                
                # ML data logging
                if key_press == ord('l'):
                    if click_detected:
                        save_landmark_data(lmList, 'click')
                    elif exit_detected:
                        save_landmark_data(lmList, 'exit')
                    else:
                        save_landmark_data(lmList, 'idle')
                
                # Exit gesture with debounce
                if exit_detected:
                    if exit_gesture_start is None:
                        exit_gesture_start = current_time
                    elif current_time - exit_gesture_start >= EXIT_GESTURE_HOLD_TIME:
                        log_info("Exit gesture held. Exiting...")
                        break
                    else:
                        remaining = EXIT_GESTURE_HOLD_TIME - (current_time - exit_gesture_start)
                        cv2.putText(img, f"Exit in {remaining:.1f}s", (mid_x - 40, mid_y - 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    exit_gesture_start = None
            else:
                gesture_detector.reset_smoothing()
                exit_gesture_start = None
            
            # === RIGHT HAND: Navigation ===
            if right_hand:
                lmList = right_hand['lmList']
                index_tip = lmList[8]
                tip_x, tip_y = index_tip[0], index_tip[1]
                
                # Draw pointer
                cv2.circle(img, (tip_x, tip_y), 15, (0, 255, 255), -1)
                
                for key_x, key_y, key_w, key_h, label in keys:
                    if key_x < tip_x < key_x + key_w and key_y < tip_y < key_y + key_h:
                        hovered_key = label
                        
                        if click_detected:
                            if click_sound:
                                try:
                                    click_sound.play()
                                except Exception:
                                    pass
                            
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
                                char = label.lower() if not shift_active else label
                                pyautogui.press(char)
                                typed_text += char if not shift_active else label
                                if shift_active and label.isalpha():
                                    shift_active = False
                            
                            key_flash[label] = current_time
                        break
            
            # === Draw UI ===
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
            
            cv2.putText(img, "AI Mode: Left=gestures | Right=navigate | 'l' log data", 
                       (15, screen_height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
            
            cv2.imshow("AI Touchless Keyboard", img)
            
    except KeyboardInterrupt:
        log_info("Interrupted by user")
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        raise
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        log_info("AI Keyboard closed. Resources released.")


if __name__ == "__main__":
    main()
