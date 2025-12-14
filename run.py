#!/usr/bin/env python3
"""
Touchless Keyboard Launcher

Simple script to run the Touchless Keyboard from the project root.
Handles proper module imports and error reporting.

Usage:
    python run.py          # Run the standard keyboard
    python run.py --ai     # Run the AI version with dual-hand control
    
Environment Variables:
    WEBCAM_INDEX=1         # Use webcam at index 1 instead of default 0
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def main():
    """Main entry point for the Touchless Keyboard."""
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--ai":
            print("Starting Touchless Keyboard (AI Version)...")
            from src.apps import virtual_keyboard_ai
            # AI version may still use module-level execution
        else:
            print("Starting Touchless Keyboard...")
            from src.apps.main import main as keyboard_main
            keyboard_main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
