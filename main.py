import cv2
import pyautogui
from cvzone.HandTrackingModule import HandDetector
from screeninfo import get_monitors
import time
import pygame
import pyperclip
from datetime import datetime

# === Sound Setup ===
pygame.mixer.init()
try:
    click_sound = pygame.mixer.Sound("clickSound.mp3")
except (pygame.error, FileNotFoundError):
    print("⚠️ Warning: clickSound.mp3 not found. Audio feedback disabled.")
    click_sound = None

# === Rounded Rectangle Helper ===
def draw_rounded_rect(img, top_left, bottom_right, radius=20, color=(0, 0, 0), thickness=-1):
    """
    Draw a rounded rectangle on the image with optimized rendering.
    
    Args:
        img (np.ndarray): Input image to draw on
        top_left (tuple): (x, y) coordinates of top-left corner
        bottom_right (tuple): (x, y) coordinates of bottom-right corner
        radius (int): Corner radius in pixels (default: 20)
        color (tuple): BGR color tuple (default: black)
        thickness (int): Line thickness, -1 for filled (default: -1)
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    overlay = img.copy()
    cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    cv2.circle(overlay, (x1 + radius, y1 + radius), radius, color, thickness)
    cv2.circle(overlay, (x2 - radius, y1 + radius), radius, color, thickness)
    cv2.circle(overlay, (x1 + radius, y2 - radius), radius, color, thickness)
    cv2.circle(overlay, (x2 - radius, y2 - radius), radius, color, thickness)
    cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)

# === Draw a Key ===
def draw_key(img, pos, text, highlight=False, width=90, height=90):
    """
    Draw a single keyboard key with text.
    
    Args:
        img (np.ndarray): Input image to draw on
        pos (tuple): (x, y) position of top-left corner
        text (str): Text to display on the key
        highlight (bool): Whether to highlight the key (default: False)
        width (int): Key width (default: 90)
        height (int): Key height (default: 90)
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

    draw_rounded_rect(img, (x, y), (x + w, y + h), radius=20, color=key_color, thickness=-1)
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, font_scale, text_color, thickness)

# === Save and Copy Functions ===
def save_text_to_file(text):
    """Save typed text to a file with timestamp."""
    if not text:
        print("⚠️ No text to save!")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"typed_text_{timestamp}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Text saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

def copy_to_clipboard(text):
    """Copy text to clipboard."""
    if not text:
        print("⚠️ No text to copy!")
        return False
    
    try:
        pyperclip.copy(text)
        print(f"✅ Copied {len(text)} characters to clipboard!")
        return True
    except Exception as e:
        print(f"❌ Error copying to clipboard: {e}")
        return False

# === Monitor Info ===
monitors = get_monitors()
screen_width, screen_height = monitors[0].width, monitors[0].height

# === Configuration Constants ===
CLICK_THRESHOLD = 50  # Standardized click detection threshold (pixels)
EXIT_THRESHOLD = 40   # Exit gesture threshold (pixels)
CLICK_DELAY = 0.7     # Delay between clicks (seconds)
FLASH_DURATION = 0.3  # Key flash animation duration (seconds)

# === Keyboard Layout with Special Keys ===
symbols = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '<-'],
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '!'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'"],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '?'],
    ['__', 'ENTER', 'TAB']
]

keys = []
key_width, key_height = 90, 90
gap = 20
start_x, start_y = 50, 100

for row_index, row in enumerate(symbols):
    row_start_x = start_x + row_index * 40
    y = start_y + row_index * (key_height + gap)
    for col_index, key in enumerate(row):
        x = row_start_x + col_index * (key_width + gap)
        # Make special keys wider
        if key in ['__', 'ENTER', 'TAB']:
            w = key_width * 2 if key == '__' else key_width * 1.5
            keys.append((x, y, w, key_height, key))
        else:
            keys.append((x, y, key_width, key_height, key))

# === Webcam Setup ===
cap = cv2.VideoCapture(0)  # change index if needed
cap.set(3, screen_width * 0.85)
cap.set(4, screen_height * 0.75)
if not cap.isOpened():
    print("❌ Error: Could not open webcam. Please check your camera connection.")
    exit()

# === Hand Detector ===
detector = HandDetector(detectionCon=0.8)
last_click_time = 0
typed_text = ""
key_flash = {}
notification_text = ""
notification_time = 0

# === Main Loop ===
print("✅ Touchless Keyboard started successfully!")
print("👉 Gestures: Pinch thumb+index to click, thumb+middle to exit")
print("⌨️ Shortcuts: Press 's' to save, 'c' to copy, ESC to quit")

while True:
    success, img = cap.read()
    if not success:
        print("⚠️ Warning: Failed to read frame from webcam")
        break

    hands, img = detector.findHands(img, draw=False)
    current_time = time.time()
    clickRegistered = False
    
    # Check for keyboard shortcuts
    key_press = cv2.waitKey(1)
    if key_press == ord('s'):
        if save_text_to_file(typed_text):
            notification_text = "✅ Saved to file!"
            notification_time = current_time
    elif key_press == ord('c'):
        if copy_to_clipboard(typed_text):
            notification_text = "✅ Copied to clipboard!"
            notification_time = current_time
    elif key_press & 0xFF == 27:
        print("⌨️ ESC pressed. Closing application...")
        break

    if hands:
        for hand in hands:
            lmList = hand['lmList']
            bbox = hand['bbox']
            bbox_x, bbox_y, bbox_w, bbox_h = bbox
            cv2.rectangle(img, (bbox_x, bbox_y), (bbox_x + bbox_w, bbox_y + bbox_h), (0, 0, 255), 2)

            thumb_tip = lmList[4]
            index_tip = lmList[8]
            dist_thumb_index = ((thumb_tip[0] - index_tip[0])**2 + (thumb_tip[1] - index_tip[1])**2)**0.5

            # === Visual Feedback: Draw line between fingers ===
            cv2.line(img, tuple(thumb_tip[:2]), tuple(index_tip[:2]), (255, 0, 255), 3)
            
            # Draw circle at midpoint
            mid_x = (thumb_tip[0] + index_tip[0]) // 2
            mid_y = (thumb_tip[1] + index_tip[1]) // 2
            cv2.circle(img, (mid_x, mid_y), 8, (255, 0, 255), -1)

            # === Visual Feedback: Distance indicator ===
            cv2.putText(img, f"Distance: {int(dist_thumb_index)}px", 
                       (10, screen_height - 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # === Visual Feedback: Click Ready indicator ===
            if dist_thumb_index < CLICK_THRESHOLD:
                cv2.putText(img, "CLICK READY!", 
                           (10, screen_height - 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                
                # Show countdown for click delay
                time_since_last_click = current_time - last_click_time
                if time_since_last_click < CLICK_DELAY:
                    remaining = CLICK_DELAY - time_since_last_click
                    cv2.putText(img, f"Wait: {remaining:.1f}s", 
                               (10, screen_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            # Click detection
            if dist_thumb_index < CLICK_THRESHOLD and (current_time - last_click_time) > CLICK_DELAY:
                clickRegistered = True
                last_click_time = current_time

            # Exit gesture
            middle_tip = lmList[12]
            dist_thumb_middle = ((thumb_tip[0] - middle_tip[0])**2 + (thumb_tip[1] - middle_tip[1])**2)**0.5
            if dist_thumb_middle < EXIT_THRESHOLD:
                print("👋 Exit gesture detected. Closing application...")
                cap.release()
                cv2.destroyAllWindows()
                exit()

            # Check which key is being hovered
            tip_x, tip_y = index_tip[0], index_tip[1]
            for key_x, key_y, key_w, key_h, label in keys:
                if key_x < tip_x < key_x + key_w and key_y < tip_y < key_y + key_h:
                    draw_rounded_rect(img, (key_x, key_y), (key_x + key_w, key_y + key_h), 
                                    radius=20, color=(0, 255, 0), thickness=4)
                    if clickRegistered:
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
                        clickRegistered = False

    # === Display Top Bar with Typed Text ===
    text_bar_width = int(screen_width * 0.8)
    draw_rounded_rect(img, (50, 20), (50 + text_bar_width, 80), radius=20, color=(50, 50, 50), thickness=-1)
    
    # Display text (replace newlines with spaces for display)
    display_text = typed_text.replace('\n', ' ').replace('\t', ' ')
    cv2.putText(img, display_text[-60:], (60, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 3)

    # === Display Notification ===
    if notification_text and (current_time - notification_time) < 2.0:
        cv2.putText(img, notification_text, 
                   (screen_width - 400, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

    # === Display Instructions ===
    cv2.putText(img, "Press 's' to save | 'c' to copy | ESC to exit", 
               (10, screen_height - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # === Draw All Keys ===
    for key_x, key_y, key_w, key_h, key in keys:
        highlight = key in key_flash and current_time - key_flash[key] < FLASH_DURATION
        draw_key(img, (key_x, key_y), key, highlight=highlight, width=int(key_w), height=int(key_h))

    cv2.imshow("Gesture Keyboard", img)

cap.release()
cv2.destroyAllWindows()
print("✅ Application closed successfully!")
