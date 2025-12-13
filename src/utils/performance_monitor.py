"""
Performance monitoring utilities for Touchless Keyboard.

This module provides FPS counting and performance tracking functionality.
"""

import time
from typing import Optional


class FPSCounter:
    """
    Real-time FPS counter with rolling average calculation.
    
    Attributes:
        update_interval (float): How often to update FPS (seconds)
        fps (float): Current FPS value
    """
    
    def __init__(self, update_interval: float = 1.0):
        """
        Initialize FPS counter.
        
        Args:
            update_interval: Time between FPS updates in seconds (default: 1.0)
        """
        self.update_interval = update_interval
        self.frame_count = 0
        self.fps = 0.0
        self.last_update = time.time()
    
    def update(self) -> float:
        """
        Update frame count and calculate FPS if interval has passed.
        
        Returns:
            Current FPS value
        """
        self.frame_count += 1
        current_time = time.time()
        
        elapsed = current_time - self.last_update
        if elapsed >= self.update_interval:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_update = current_time
        
        return self.fps
    
    def get_fps(self) -> float:
        """Get current FPS value without updating."""
        return self.fps
    
    def reset(self):
        """Reset the FPS counter."""
        self.frame_count = 0
        self.fps = 0.0
        self.last_update = time.time()


class PerformanceLogger:
    """
    Optional performance logger for tracking metrics over time.
    
    Can log FPS, frame times, and other performance metrics to a file.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize performance logger.
        
        Args:
            log_file: Path to log file (None to disable logging)
        """
        self.log_file = log_file
        self.enabled = log_file is not None
        self.metrics = []
    
    def log_frame(self, fps: float, frame_time: float):
        """
        Log frame performance metrics.
        
        Args:
            fps: Current FPS
            frame_time: Time taken to process frame (ms)
        """
        if not self.enabled:
            return
        
        timestamp = time.time()
        self.metrics.append({
            'timestamp': timestamp,
            'fps': fps,
            'frame_time': frame_time
        })
    
    def save_to_file(self):
        """Save collected metrics to file."""
        if not self.enabled or not self.metrics:
            return
        
        try:
            with open(self.log_file, 'w') as f:
                f.write("timestamp,fps,frame_time_ms\n")
                for metric in self.metrics:
                    f.write(f"{metric['timestamp']},{metric['fps']},{metric['frame_time']}\n")
            print(f" Performance metrics saved to {self.log_file}")
        except Exception as e:
            print(f" Failed to save performance metrics: {e}")
    
    def get_average_fps(self) -> float:
        """Calculate average FPS from collected metrics."""
        if not self.metrics:
            return 0.0
        return sum(m['fps'] for m in self.metrics) / len(self.metrics)
