"""
Calibration UI for Touchless Keyboard.

Provides interactive calibration mode with visual guidance for 
measuring hand size and setting adaptive gesture thresholds.
"""

import cv2
import time
import numpy as np
from typing import Optional, Tuple
from cvzone.HandTrackingModule import HandDetector

from src.core.gesture_handler import HandCalibration
from src.utils.logging_config import log_info, log_warning
from src.utils.themes import get_theme


class CalibrationUI:
    """
    Interactive calibration interface with visual guidance.
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize calibration UI.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.calibration = HandCalibration()
        self.detector = HandDetector(detectionCon=0.8)
        
        # Calibration state
        self.samples_needed = 30
        self.current_samples = 0
        self.is_complete = False
        self.countdown = 3
        self.countdown_start = None
        
    def draw_progress_bar(self, img, progress: float, y: int):
        """Draw calibration progress bar."""
        theme = get_theme()
        bar_width = int(self.screen_width * 0.6)
        bar_height = 30
        x = (self.screen_width - bar_width) // 2
        
        # Background
        cv2.rectangle(img, (x, y), (x + bar_width, y + bar_height), (50, 50, 50), -1)
        
        # Progress fill
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            cv2.rectangle(img, (x, y), (x + fill_width, y + bar_height), 
                         theme['indicator_ready'], -1)
        
        # Border
        cv2.rectangle(img, (x, y), (x + bar_width, y + bar_height), (100, 100, 100), 2)
        
        # Percentage text
        pct = int(progress * 100)
        cv2.putText(img, f"{pct}%", (x + bar_width + 15, y + 22),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def draw_hand_guide(self, img, hand_detected: bool):
        """Draw hand positioning guide."""
        theme = get_theme()
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # Draw target circle
        color = theme['indicator_ready'] if hand_detected else theme['indicator_wait']
        cv2.circle(img, (center_x, center_y), 150, color, 3)
        cv2.circle(img, (center_x, center_y), 100, color, 2)
        
        # Instructions
        if not hand_detected:
            text = "Position your hand in the circle"
            cv2.putText(img, text, (center_x - 200, center_y + 200),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    def draw_countdown(self, img, seconds: int):
        """Draw countdown before calibration starts."""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # Large countdown number
        cv2.putText(img, str(seconds), (center_x - 40, center_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 255), 5)
        
        cv2.putText(img, "Get Ready!", (center_x - 100, center_y - 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    
    def run_calibration(self, cap) -> bool:
        """
        Run the calibration process.
        
        Args:
            cap: OpenCV VideoCapture object
            
        Returns:
            True if calibration successful, False if cancelled
        """
        log_info("Starting calibration mode...")
        
        state = "countdown"  # countdown -> collecting -> complete
        countdown_start = time.time()
        
        while True:
            success, img = cap.read()
            if not success:
                log_warning("Failed to read frame during calibration")
                return False
            
            hands, img = self.detector.findHands(img, draw=True)
            theme = get_theme()
            
            # Title
            cv2.putText(img, "CALIBRATION MODE", (self.screen_width // 2 - 180, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, theme['glow_color'], 3)
            
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
                    # Reset countdown if no hand
                    countdown_start = time.time()
                    
            elif state == "collecting":
                self.draw_hand_guide(img, hand_detected)
                
                # Collect samples
                if hand_detected:
                    lmList = hands[0]['lmList']
                    self.calibration.add_calibration_sample(lmList)
                    self.current_samples += 1
                    
                    # Progress
                    progress = self.current_samples / self.samples_needed
                    self.draw_progress_bar(img, progress, self.screen_height - 100)
                    
                    cv2.putText(img, f"Collecting samples: {self.current_samples}/{self.samples_needed}",
                               (self.screen_width // 2 - 180, self.screen_height - 130),
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
                    
                    cv2.putText(img, "Press any key to continue...",
                               (self.screen_width // 2 - 150, self.screen_height // 2 + 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
                    
                    cv2.imshow("Calibration", img)
                    cv2.waitKey(2000)
                    cv2.destroyWindow("Calibration")
                    log_info("Calibration completed successfully!")
                    return True
                    
                except Exception as e:
                    log_warning(f"Calibration failed: {e}")
                    return False
            
            # Instructions
            cv2.putText(img, "Press ESC to cancel", (20, self.screen_height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
            
            cv2.imshow("Calibration", img)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                log_info("Calibration cancelled by user")
                cv2.destroyWindow("Calibration")
                return False
        
        return False


def run_calibration_mode(cap, screen_width: int, screen_height: int) -> Optional[HandCalibration]:
    """
    Run calibration and return calibrated HandCalibration object.
    
    Args:
        cap: OpenCV VideoCapture
        screen_width: Screen width
        screen_height: Screen height
    
    Returns:
        HandCalibration object if successful, None if cancelled
    """
    calibration_ui = CalibrationUI(screen_width, screen_height)
    success = calibration_ui.run_calibration(cap)
    
    if success:
        return calibration_ui.calibration
    return None
