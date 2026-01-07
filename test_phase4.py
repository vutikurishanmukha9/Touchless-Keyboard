
import os
from src.utils.settings import load_settings, update_setting, get_log_file_path
from src.utils.themes import get_theme, set_theme
from src.utils.logging_config import setup_logger, log_info

def test_phase_4():
    print("Testing Phase 4 features...")
    
    # 1. Test Logging Settings
    update_setting('log_to_file', True)
    log_path = get_log_file_path()
    assert log_path is not None, "Log path should be set"
    print(f"Log path: {log_path}")
    
    setup_logger(log_file=log_path)
    log_info("Phase 4 test log entry")
    
    assert os.path.exists(log_path), "Log file should exist"
    
    # 2. Test High Contrast Theme
    set_theme('high_contrast')
    theme = get_theme('high_contrast')
    assert theme['name'] == 'High Contrast'
    assert theme['key_bg'] == (0, 0, 0)
    print("High Contrast theme verified")
    
    # 3. Test Smoothing Factor Saving
    update_setting('smoothing_factor', 0.8)
    settings = load_settings()
    assert settings['smoothing_factor'] == 0.8
    print("Smoothing factor setting verified")
    
    # Clean up (disable file logging)
    update_setting('log_to_file', False)
    print("Phase 4 tests passed!")

if __name__ == "__main__":
    test_phase_4()
