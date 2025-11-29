"""
Touchless Keyboard - AI Version (Refactored)

Dual-hand gesture-controlled virtual keyboard with ML data collection:
- Left hand: Click and exit gestures
- Right hand: Cursor navigation
- Gesture smoothing for stability
- FPS monitoring
- Adaptive thresholds via calibration
- ML gesture data logging
"""

import cv2
import pyautogui
from cvzone.HandTrackingModule import HandDetector
from screeninfo import get_monitors
import time
import pygame
import csv
import os

# Import shared modules
from keyboard_utils import draw_key, generate_keyboard_layout, draw_text_bar, draw_rounded_rect
from gesture_handler import GestureDetector, HandCalibration
from file_utils import save_text_to_file, copy_to_clipboard
from performance_monitor import FPSCounter
from exceptions import WebcamError, AudioError, FileOperationError, ClipboardError

# === Sound Setup ===
pygame.mixer.init()
try:
    click_sound = pygame.mixer.Sound("clickSound.mp3")
except (pygame.error, FileNotFoundError):
    click_sound = None
    print(" Warning: clickSound.mp3 not found. Audio feedback disabled.")

# === Save landmark data for ML training ===
def save_landmark_data(lmList, label):
    """Save hand landmark data to CSV for ML training."""
    if lmList:
        with open("gesture_data.csv", "a", newline="") as f:
            writer = csv.writer(f)
            row = [coord for point in lmList for coord in point[:3]]  # x, y, z
            row.append(label)
            writer.writerow(row)
            print(f" Gesture data saved: {label}")

# === Monitor Setup ===
monitors = get_monitors()
screen_width, screen_height = monitors[0].width, monitors[0].height

# === Configuration ===
SHOW_FPS = True
FLASH_DURATION = 0.3

# === Initialize Components ===
calibration = HandCalibration()
calibration.load_calibration()

# Gesture detector with faster click delay for AI version
gesture_detector = GestureDetector(
    click_delay=0.5,
    use_smoothing=True,
    calibration=calibration
)

fps_counter = FPSCounter(update_interval=1.0)
keys = generate_keyboard_layout(start_x=50, start_y=150)

# === Webcam ===
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
exit_flag = False
notification_text = ""
notification_time = 0

print(" Virtual Keyboard with AI Gesture Logging started!")
print(" Left hand: Click (thumb+index), Exit (thumb+middle)")
print(" Right hand: Hover over keys")
print(" Press 'c' to save click data, 'm' for move, 'e' for exit")
print(" Press 's' to save text, 'x' to copy, ESC to quit")

while not exit_flag:
    success, img = cap.read()
    if not success:
        print(" Warning: Failed to read frame from webcam")
        break

    hands, img = detector.findHands(img, draw=False)
    current_time = time.time()
    
    # Update FPS
    if SHOW_FPS:
        current_fps = fps_counter.update()
    
    # Consolidate keyboard input
    key = cv2.waitKey(1)
    
    # Save/copy shortcuts
    if key == ord('s'):
        try:
            if save_text_to_file(typed_text):
                notification_text = " Saved to file!"
                notification_time = current_time
        except FileOperationError as e:
            notification_text = f" {e}"
            notification_time = current_time
    elif key == ord('x'):
        try:
            if copy_to_clipboard(typed_text):
                notification_text = " Copied to clipboard!"
                notification_time = current_time
        except ClipboardError as e:
            notification_text = f" {e}"
            notification_time = current_time
    elif key & 0xFF == 27:
        print(" ESC pressed. Closing application...")
        break

    if hands:
        for hand in hands:
            lmList = hand['lmList']
            bbox = hand['bbox']
            bbox_x, bbox_y, bbox_w, bbox_h = bbox
            cv2.rectangle(img, (bbox_x, bbox_y), (bbox_x + bbox_w, bbox_y + bbox_h), (0, 0, 255), 2)

            # Save gesture data if user presses a key
            if key == ord('c'):
                save_landmark_data(lmList, 'click')
            elif key == ord('m'):
                save_landmark_data(lmList, 'move')
            elif key == ord('e'):
                save_landmark_data(lmList, 'exit')

            # === LEFT HAND: Detect gestures ===
            if hand['type'] == "Left":
                thumb_tip = lmList[4]
                index_tip = lmList[8]
                
                # Visual feedback
                cv2.line(img, tuple(thumb_tip[:2]), tuple(index_tip[:2]), (255, 0, 255), 3)
                mid_x = (thumb_tip[0] + index_tip[0]) // 2
                mid_y = (thumb_tip[1] + index_tip[1]) // 2
                cv2.circle(img, (mid_x, mid_y), 8, (255, 0, 255), -1)
                
                # Gesture detection with smoothing
                click_detected, click_distance = gesture_detector.detect_click(lmList, current_time)
                exit_detected, exit_distance = gesture_detector.detect_exit(lmList)
                
                # Distance indicator
                cv2.putText(img, f"L-Distance: {int(click_distance)}px", 
                           (10, screen_height - 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Click ready indicator
                if click_distance < gesture_detector.calibration.get_click_threshold():
                    cv2.putText(img, "CLICK READY!", 
                               (10, screen_height - 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                    
                    remaining = gesture_detector.get_time_until_next_click(current_time)
                    if remaining > 0:
                        cv2.putText(img, f"Wait: {remaining:.1f}s", 
                                   (10, screen_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                
                if exit_detected:
                    print(" Exit gesture detected. Closing application...")
                    exit_flag = True
                    break

            # === RIGHT HAND: Cursor hovering ===
            if hand["type"] == "Right":
                index_tip = lmList[8]
                tip_x, tip_y = index_tip[0], index_tip[1]
                
                # Draw pointer circle
                cv2.circle(img, (tip_x, tip_y), 15, (0, 255, 255), -1)
                
                for key_x, key_y, key_w, key_h, label in keys:
                    if key_x < tip_x < key_x + key_w and key_y < tip_y < key_y + key_h:
                        draw_rounded_rect(img, (key_x, key_y), (key_x + key_w, key_y + key_h), 
                                        radius=20, color=(0, 255, 0), thickness=4)
                        
                        # Check if left hand clicked
                        if 'click_detected' in locals() and click_detected:
                            if click_sound:
                                click_sound.play()
                            
                            if label == '__':
                                pyautogui.press('space')
                                typed_text += ' '
                            elif label == '<-':
                                pyautogui.press('backspace')
                                typed_text = typed_text[:-1] if len(typed_text) > 0 else ''
                            elif label == 'ENTER':
                                pyautogui.press('enter')
                                typed_text += '\n'
                            elif label == 'TAB':
                                pyautogui.press('tab')
                                typed_text += '\t'
                            else:
                                pyautogui.press(label.lower())
                                typed_text += label
                            
                            key_flash[label] = current_time

    # === Display Text Bar ===
    draw_text_bar(img, typed_text, screen_width, y_pos=30)

    # === Display FPS Counter ===
    if SHOW_FPS:
        cv2.putText(img, f"FPS: {int(current_fps)}", 
                   (screen_width - 150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

    # === Display Notification ===
    if notification_text and (current_time - notification_time) < 2.0:
        cv2.putText(img, notification_text, 
                   (screen_width - 400, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

    # === Display Instructions ===
    cv2.putText(img, "L-Hand: Click | R-Hand: Navigate | 's' save | 'x' copy | ESC exit", 
               (10, screen_height - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # === Draw Keys ===
    for key_x, key_y, key_w, key_h, key_label in keys:
        is_flashing = key_label in key_flash and current_time - key_flash[key_label] < FLASH_DURATION
        draw_key(img, (key_x, key_y), key_label, highlight=is_flashing, width=int(key_w), height=int(key_h))

    cv2.imshow(" Virtual Keyboard with AI Gesture Logging", img)

cap.release()
cv2.destroyAllWindows()
print(" Application closed successfully!")
