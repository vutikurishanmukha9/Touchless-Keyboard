"""
Calibration UI for Touchless Keyboard.

Provides interactive calibration mode with visual guidance for 
measuring hand size and setting adaptive gesture thresholds.
Includes timeout protection and sample validation.
"""

import cv2
import time
import numpy as np
from typing import Optional, List
from cvzone.HandTrackingModule import HandDetector

from src.core.gesture_handler import HandCalibration
from src.utils.logging_config import log_info, log_warning
from src.utils.themes import get_theme

# Configuration
CALIBRATION_TIMEOUT = 60.0  # Max seconds for calibration
SAMPLES_NEEDED = 30
MIN_HAND_SIZE = 50  # Minimum valid hand span in pixels
MAX_HAND_SIZE = 500  # Maximum valid hand span in pixels


def validate_sample(hand_landmarks: List[List[float]]) -> bool:
    """
    Validate that a hand sample is reasonable.
    
    Args:
        hand_landmarks: 21 hand landmarks
        
    Returns:
        True if sample is valid
    """
    if len(hand_landmarks) != 21:
        return False
    
    # Check hand span is reasonable
    thumb_base = hand_landmarks[2]
    pinky_base = hand_landmarks[17]
    span = ((thumb_base[0] - pinky_base[0])**2 + (thumb_base[1] - pinky_base[1])**2)**0.5
    
    return MIN_HAND_SIZE <= span <= MAX_HAND_SIZE


class CalibrationUI:
    """
    Interactive calibration interface with visual guidance.
    Includes timeout protection to prevent infinite loops.
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize calibration UI."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.calibration = HandCalibration()
        self.detector = HandDetector(detectionCon=0.8)
        
        # State
        self.samples_needed = SAMPLES_NEEDED
        self.current_samples = 0
        self.start_time = None
        self.valid_samples = []
        
    def draw_progress_bar(self, img, progress: float, y: int):
        """Draw calibration progress bar."""
        theme = get_theme()
        bar_width = int(self.screen_width * 0.6)
        bar_height = 30
        x = (self.screen_width - bar_width) // 2
        
        cv2.rectangle(img, (x, y), (x + bar_width, y + bar_height), (50, 50, 50), -1)
        
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            cv2.rectangle(img, (x, y), (x + fill_width, y + bar_height), 
                         theme['indicator_ready'], -1)
        
        cv2.rectangle(img, (x, y), (x + bar_width, y + bar_height), (100, 100, 100), 2)
        
        pct = int(progress * 100)
        cv2.putText(img, f"{pct}%", (x + bar_width + 15, y + 22),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def draw_hand_guide(self, img, hand_detected: bool):
        """Draw hand positioning guide."""
        theme = get_theme()
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        color = theme['indicator_ready'] if hand_detected else theme['indicator_wait']
        cv2.circle(img, (center_x, center_y), 150, color, 3)
        cv2.circle(img, (center_x, center_y), 100, color, 2)
        
        if not hand_detected:
            cv2.putText(img, "Position your hand in the circle", 
                       (center_x - 200, center_y + 200),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    def draw_countdown(self, img, seconds: int):
        """Draw countdown before calibration starts."""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        cv2.putText(img, str(seconds), (center_x - 40, center_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 255), 5)
        cv2.putText(img, "Get Ready!", (center_x - 100, center_y - 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    
    def draw_timeout_warning(self, img, remaining: float):
        """Draw timeout warning."""
        cv2.putText(img, f"Timeout in: {int(remaining)}s", 
                   (self.screen_width - 200, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
    
    def run_calibration(self, cap) -> bool:
        """
        Run the calibration process with timeout protection.
        
        Args:
            cap: OpenCV VideoCapture object
            
        Returns:
            True if calibration successful, False if cancelled/timeout
        """
        log_info("Starting calibration mode...")
        
        state = "countdown"
        countdown_start = time.time()
        self.start_time = time.time()
        
        try:
            while True:
                # Check timeout
                elapsed_total = time.time() - self.start_time
                if elapsed_total > CALIBRATION_TIMEOUT:
                    log_warning(f"Calibration timed out after {CALIBRATION_TIMEOUT}s")
                    cv2.destroyWindow("Calibration")
                    return False
                
                success, img = cap.read()
                if not success:
                    log_warning("Failed to read frame during calibration")
                    continue
                
                hands, img = self.detector.findHands(img, draw=True)
                theme = get_theme()
                
                # Title and timeout
                cv2.putText(img, "CALIBRATION MODE", (self.screen_width // 2 - 180, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, theme['glow_color'], 3)
                self.draw_timeout_warning(img, CALIBRATION_TIMEOUT - elapsed_total)
                
                hand_detected = len(hands) > 0
                
                if state == "countdown":
                    elapsed = time.time() - countdown_start
                    remaining = max(0, 3 - int(elapsed))
                    
                    self.draw_hand_guide(img, hand_detected)
                    self.draw_countdown(img, remaining)
                    
                    if elapsed >= 3 and hand_detected:
                        state = "collecting"
                        log_info("Starting sample collection...")
                    elif elapsed >= 3:
                        countdown_start = time.time()
                        
                elif state == "collecting":
                    self.draw_hand_guide(img, hand_detected)
                    
                    if hand_detected:
                        lmList = hands[0]['lmList']
                        
                        # Validate sample before adding
                        if validate_sample(lmList):
                            self.calibration.add_calibration_sample(lmList)
                            self.current_samples += 1
                        else:
                            cv2.putText(img, "Invalid sample - hold steady",
                                       (self.screen_width // 2 - 150, self.screen_height - 160),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                        
                        progress = self.current_samples / self.samples_needed
                        self.draw_progress_bar(img, progress, self.screen_height - 100)
                        
                        cv2.putText(img, f"Samples: {self.current_samples}/{self.samples_needed}",
                                   (self.screen_width // 2 - 100, self.screen_height - 130),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        
                        if self.current_samples >= self.samples_needed:
                            state = "complete"
                    else:
                        cv2.putText(img, "Hand lost! Keep it visible",
                                   (self.screen_width // 2 - 150, self.screen_height - 130),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
                elif state == "complete":
                    try:
                        self.calibration.calibrate(self.samples_needed)
                        self.calibration.save_calibration()
                        
                        cv2.putText(img, "CALIBRATION COMPLETE!", 
                                   (self.screen_width // 2 - 220, self.screen_height // 2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                        
                        cv2.putText(img, f"Click threshold: {self.calibration.click_threshold}px",
                                   (self.screen_width // 2 - 150, self.screen_height // 2 + 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        
                        cv2.imshow("Calibration", img)
                        cv2.waitKey(2000)
                        cv2.destroyWindow("Calibration")
                        log_info("Calibration completed successfully!")
                        return True
                        
                    except Exception as e:
                        log_warning(f"Calibration failed: {e}")
                        cv2.destroyWindow("Calibration")
                        return False
                
                cv2.putText(img, "Press ESC to cancel", (20, self.screen_height - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
                
                cv2.imshow("Calibration", img)
                
                if cv2.waitKey(1) & 0xFF == 27:
                    log_info("Calibration cancelled by user")
                    cv2.destroyWindow("Calibration")
                    return False
                    
        except Exception as e:
            log_warning(f"Calibration error: {e}")
            try:
                cv2.destroyWindow("Calibration")
            except:
                pass
            return False


def run_calibration_mode(cap, screen_width: int, screen_height: int) -> Optional[HandCalibration]:
    """
    Run calibration and return calibrated HandCalibration object.
    
    Args:
        cap: OpenCV VideoCapture
        screen_width: Screen width
        screen_height: Screen height
    
    Returns:
        HandCalibration object if successful, None if cancelled/timeout
    """
    calibration_ui = CalibrationUI(screen_width, screen_height)
    success = calibration_ui.run_calibration(cap)
    
    if success:
        return calibration_ui.calibration
    return None
