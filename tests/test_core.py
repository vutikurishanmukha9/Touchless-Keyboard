"""
Unit tests for Touchless Keyboard.

Run with: python -m pytest tests/ -v
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSettings:
    """Tests for settings module."""
    
    def test_load_settings_returns_defaults(self):
        """Test that loading settings returns default values."""
        from src.utils.settings import load_settings, DEFAULT_SETTINGS
        
        settings = load_settings()
        assert 'theme' in settings
        assert 'show_fps' in settings
        assert settings['theme'] == DEFAULT_SETTINGS['theme']
    
    def test_default_settings_has_required_keys(self):
        """Test that DEFAULT_SETTINGS has all required keys."""
        from src.utils.settings import DEFAULT_SETTINGS
        
        required_keys = ['theme', 'show_fps', 'click_delay', 'target_fps']
        for key in required_keys:
            assert key in DEFAULT_SETTINGS, f"Missing key: {key}"


class TestFileUtils:
    """Tests for file utilities."""
    
    def test_save_text_empty_returns_false(self):
        """Test that saving empty text returns False."""
        from src.utils.file_utils import save_text_to_file
        
        result = save_text_to_file("")
        assert result is False
    
    def test_save_text_creates_file(self):
        """Test that save_text_to_file creates a file."""
        from src.utils.file_utils import save_text_to_file
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            result = save_text_to_file("Hello World", filename="test.txt", directory=tmpdir)
            assert result is True
            assert os.path.exists(filepath)
    
    def test_sanitize_csv_value_escapes_formula(self):
        """Test that CSV sanitization escapes formula characters."""
        from src.utils.file_utils import sanitize_csv_value
        
        # Should escape values starting with =, +, -, @
        assert sanitize_csv_value("=cmd").startswith("'")
        assert sanitize_csv_value("+1234").startswith("'")
        assert sanitize_csv_value("@malicious").startswith("'")
        
        # Normal values should not be changed
        assert sanitize_csv_value("hello") == "hello"
        assert sanitize_csv_value("123") == "123"


class TestLogging:
    """Tests for logging configuration."""
    
    def test_logger_exists(self):
        """Test that logger is properly configured."""
        from src.utils.logging_config import logger
        
        assert logger is not None
        assert logger.name == "touchless_keyboard"
    
    def test_log_functions_exist(self):
        """Test that log helper functions exist."""
        from src.utils.logging_config import log_info, log_warning, log_error, log_debug
        
        # Should not raise
        log_info("Test info")
        log_warning("Test warning")


class TestThemes:
    """Tests for theme system."""
    
    def test_get_available_themes_returns_list(self):
        """Test that get_available_themes returns a non-empty list."""
        from src.utils.themes import get_available_themes
        
        themes = get_available_themes()
        assert isinstance(themes, list)
        assert len(themes) > 0
        assert 'dark' in themes
    
    def test_set_and_get_theme(self):
        """Test setting and getting theme."""
        from src.utils.themes import set_theme, get_theme
        
        set_theme('dark')
        theme = get_theme()
        assert isinstance(theme, dict)
        assert 'key_bg' in theme
        assert 'glow_color' in theme


class TestGestureHandler:
    """Tests for gesture detection."""
    
    def test_hand_calibration_defaults(self):
        """Test that HandCalibration has sensible defaults."""
        from src.core.gesture_handler import HandCalibration
        
        cal = HandCalibration()
        assert cal.click_threshold == 50
        assert cal.exit_threshold == 40
        assert cal.is_calibrated() is False
    
    def test_gesture_detector_creation(self):
        """Test that GestureDetector can be created."""
        from src.core.gesture_handler import GestureDetector, HandCalibration
        
        cal = HandCalibration()
        detector = GestureDetector(click_delay=0.5, use_smoothing=True, calibration=cal)
        
        assert detector is not None
        assert detector.click_delay == 0.5


class TestKeyboardUtils:
    """Tests for keyboard utilities."""
    
    def test_generate_keyboard_layout(self):
        """Test that keyboard layout generation works."""
        from src.core.keyboard_utils import generate_keyboard_layout
        
        keys = generate_keyboard_layout(start_x=50, start_y=100)
        
        assert isinstance(keys, list)
        assert len(keys) > 0
        
        # Each key should be (x, y, width, height, label)
        first_key = keys[0]
        assert len(first_key) == 5
    
    def test_clear_gradient_cache(self):
        """Test that cache clearing doesn't raise."""
        from src.core.keyboard_utils import clear_gradient_cache
        
        # Should not raise
        clear_gradient_cache()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
