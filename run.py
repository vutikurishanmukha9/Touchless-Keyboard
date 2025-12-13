#!/usr/bin/env python3
"""
Touchless Keyboard Launcher

Simple script to run the Touchless Keyboard from the project root.

Usage:
    python run.py          # Run the standard keyboard
    python run.py --ai     # Run the AI version with dual-hand control
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def main():
    """Main entry point for the Touchless Keyboard."""
    if len(sys.argv) > 1 and sys.argv[1] == "--ai":
        print("Starting Touchless Keyboard (AI Version)...")
        from src.apps import virtual_keyboard_ai
    else:
        print("Starting Touchless Keyboard...")
        from src.apps import main


if __name__ == "__main__":
    main()
