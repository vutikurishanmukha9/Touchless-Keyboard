"""
Gesture detection and hand calibration for Touchless Keyboard.

This module provides gesture detection with smoothing, adaptive thresholds,
and hand calibration capabilities.
"""

import time
import json
from collections import deque
from typing import List, Tuple, Optional, Dict
from src.utils.exceptions import CalibrationError


class GestureSmoothing:
    """
    Smooth gesture distance measurements using moving average filter.
    
    Reduces jitter from hand tremor and improves gesture stability.
    """
    
    def __init__(self, window_size: int = 5):
        """
        Initialize gesture smoothing.
        
        Args:
            window_size: Number of frames to average (default: 5)
        """
        self.window_size = window_size
        self.distances = deque(maxlen=window_size)
    
    def smooth(self, distance: float) -> float:
        """
        Add new distance and return smoothed value.
        
        Args:
            distance: Current distance measurement
        
        Returns:
            Smoothed distance (moving average)
        """
        self.distances.append(distance)
        return sum(self.distances) / len(self.distances)
    
    def reset(self):
        """Clear the smoothing buffer."""
        self.distances.clear()
    
    def is_ready(self) -> bool:
        """Check if buffer is full and smoothing is stable."""
        return len(self.distances) == self.window_size


class HandCalibration:
    """
    Calibrate gesture thresholds based on hand size.
    
    Measures hand dimensions and calculates adaptive thresholds for
    more accurate gesture detection across different hand sizes and
    camera distances.
    """
    
    def __init__(self):
        """Initialize hand calibration."""
        self.hand_size = None
        self.click_threshold = 50  # default
        self.exit_threshold = 40   # default
        self.calibrated = False
        self.calibration_samples = []
    
    @staticmethod
    def calculate_distance(p1: List[float], p2: List[float]) -> float:
        """
        Calculate Euclidean distance between two points.
        
        Args:
            p1: First point [x, y, z]
            p2: Second point [x, y, z]
        
        Returns:
            Distance in pixels
        """
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
    
    def add_calibration_sample(self, hand_landmarks: List[List[float]]):
        """
        Add a hand sample for calibration.
        
        Args:
            hand_landmarks: List of 21 hand landmarks
        """
        # Measure hand size (thumb to pinky distance)
        thumb_base = hand_landmarks[2]   # Thumb MCP joint
        pinky_base = hand_landmarks[17]  # Pinky MCP joint
        hand_span = self.calculate_distance(thumb_base, pinky_base)
        
        self.calibration_samples.append(hand_span)
    
    def calibrate(self, num_samples: int = 30) -> bool:
        """
        Perform calibration using collected samples.
        
        Args:
            num_samples: Expected number of samples
        
        Returns:
            True if calibration successful
        
        Raises:
            CalibrationError: If calibration fails
        """
        if len(self.calibration_samples) < num_samples:
            raise CalibrationError(
                f"Insufficient samples: {len(self.calibration_samples)}/{num_samples}"
            )
        
        # Calculate average hand size
        self.hand_size = sum(self.calibration_samples) / len(self.calibration_samples)
        
        # Validate hand size is reasonable
        if self.hand_size < 50 or self.hand_size > 500:
            raise CalibrationError(
                f"Invalid hand size detected: {self.hand_size:.1f}px. "
                "Please ensure hand is clearly visible."
            )
        
        # Calculate adaptive thresholds (percentage of hand size)
        self.click_threshold = int(self.hand_size * 0.12)  # 12% of hand span
        self.exit_threshold = int(self.hand_size * 0.10)   # 10% of hand span
        
        # Ensure thresholds are within reasonable bounds
        self.click_threshold = max(30, min(70, self.click_threshold))
        self.exit_threshold = max(25, min(60, self.exit_threshold))
        
        self.calibrated = True
        print(f" Calibration complete!")
        print(f"   Hand size: {self.hand_size:.1f}px")
        print(f"   Click threshold: {self.click_threshold}px")
        print(f"   Exit threshold: {self.exit_threshold}px")
        
        return True
    
    def get_click_threshold(self) -> int:
        """Get current click threshold."""
        return self.click_threshold
    
    def get_exit_threshold(self) -> int:
        """Get current exit threshold."""
        return self.exit_threshold
    
    def is_calibrated(self) -> bool:
        """Check if calibration has been performed."""
        return self.calibrated
    
    def save_calibration(self, filename: str = "calibration.json"):
        """
        Save calibration data to file.
        
        Args:
            filename: Path to save calibration data
        """
        if not self.calibrated:
            print(" No calibration data to save")
            return
        
        data = {
            'hand_size': self.hand_size,
            'click_threshold': self.click_threshold,
            'exit_threshold': self.exit_threshold
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f" Calibration saved to {filename}")
        except Exception as e:
            print(f" Failed to save calibration: {e}")
    
    def load_calibration(self, filename: str = "calibration.json") -> bool:
        """
        Load calibration data from file.
        
        Args:
            filename: Path to calibration file
        
        Returns:
            True if load successful
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.hand_size = data['hand_size']
            self.click_threshold = data['click_threshold']
            self.exit_threshold = data['exit_threshold']
            self.calibrated = True
            
            print(f" Calibration loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f" Calibration file not found: {filename}")
            return False
        except Exception as e:
            print(f" Failed to load calibration: {e}")
            return False


class GestureDetector:
    """
    Unified gesture detection with smoothing and calibration support.
    
    Detects click and exit gestures with configurable thresholds,
    smoothing, and debouncing.
    """
    
    def __init__(self, click_delay: float = 0.7, use_smoothing: bool = True,
                 calibration: Optional[HandCalibration] = None):
        """
        Initialize gesture detector.
        
        Args:
            click_delay: Minimum time between clicks (seconds)
            use_smoothing: Enable gesture smoothing
            calibration: HandCalibration instance (creates default if None)
        """
        self.click_delay = click_delay
        self.last_click_time = 0
        self.use_smoothing = use_smoothing
        
        # Initialize smoothing
        self.click_smoother = GestureSmoothing(window_size=5) if use_smoothing else None
        self.exit_smoother = GestureSmoothing(window_size=5) if use_smoothing else None
        
        # Initialize calibration
        self.calibration = calibration if calibration else HandCalibration()
    
    @staticmethod
    def calculate_distance(p1: List[float], p2: List[float]) -> float:
        """Calculate Euclidean distance between two points."""
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
    
    def detect_click(self, hand_landmarks: List[List[float]], 
                    current_time: float) -> Tuple[bool, float]:
        """
        Detect click gesture (thumb-index pinch).
        
        Args:
            hand_landmarks: List of 21 hand landmarks
            current_time: Current timestamp
        
        Returns:
            Tuple of (click_detected, distance)
        """
        thumb_tip = hand_landmarks[4]
        index_tip = hand_landmarks[8]
        
        distance = self.calculate_distance(thumb_tip, index_tip)
        
        # Apply smoothing if enabled
        if self.use_smoothing and self.click_smoother:
            distance = self.click_smoother.smooth(distance)
        
        # Check if within threshold and debounce time has passed
        threshold = self.calibration.get_click_threshold()
        time_since_last_click = current_time - self.last_click_time
        
        if distance < threshold and time_since_last_click > self.click_delay:
            self.last_click_time = current_time
            return True, distance
        
        return False, distance
    
    def detect_exit(self, hand_landmarks: List[List[float]]) -> Tuple[bool, float]:
        """
        Detect exit gesture (thumb-middle pinch).
        
        Args:
            hand_landmarks: List of 21 hand landmarks
        
        Returns:
            Tuple of (exit_detected, distance)
        """
        thumb_tip = hand_landmarks[4]
        middle_tip = hand_landmarks[12]
        
        distance = self.calculate_distance(thumb_tip, middle_tip)
        
        # Apply smoothing if enabled
        if self.use_smoothing and self.exit_smoother:
            distance = self.exit_smoother.smooth(distance)
        
        # Check if within threshold
        threshold = self.calibration.get_exit_threshold()
        return distance < threshold, distance
    
    def reset_smoothing(self):
        """Reset all smoothing buffers."""
        if self.click_smoother:
            self.click_smoother.reset()
        if self.exit_smoother:
            self.exit_smoother.reset()
    
    def get_time_until_next_click(self, current_time: float) -> float:
        """
        Get remaining time until next click is allowed.
        
        Args:
            current_time: Current timestamp
        
        Returns:
            Seconds until next click (0 if ready)
        """
        elapsed = current_time - self.last_click_time
        remaining = self.click_delay - elapsed
        return max(0, remaining)
