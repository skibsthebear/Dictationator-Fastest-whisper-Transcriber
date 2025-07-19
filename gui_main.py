#!/usr/bin/env python3
"""
GUI Entry Point for Dictationer Voice Recording System.

This is the main entry point that loads the PySide6 GUI interface
before initializing the core recording system. It provides a
settings interface and program control functionality.

Usage:
    python gui_main.py

The GUI allows users to:
- Configure device preferences (CPU/GPU)
- Select Whisper model size
- Set hotkey combinations
- Configure output directories
- Start/stop the recording system
- Monitor program output in real-time
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path for development
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

# Import and run the GUI
try:
    from dictationer.gui import run_gui
    
    def main():
        """
        Main entry point for the GUI application.
        
        This function serves as the primary entry point that:
        1. Sets up the Python path for the dictationer package
        2. Ensures all dependencies are available
        3. Launches the PySide6 GUI interface
        4. Handles any startup errors gracefully
        
        The GUI will load before any recording functionality is initialized,
        allowing users to configure settings before starting the system.
        """
        print("🎤 Dictationer - Voice Recording System")
        print("=" * 50)
        print("Starting GUI interface...")
        print("Please configure your settings before starting the recording system.")
        print()
        
        # Ensure required directories exist
        for directory in ['config', 'outputs', 'logs']:
            dir_path = current_dir / directory
            dir_path.mkdir(exist_ok=True)
        
        # Launch GUI
        run_gui()

    if __name__ == "__main__":
        main()

except ImportError as e:
    print("❌ Error: Failed to import required modules")
    print(f"Details: {e}")
    print()
    print("Please make sure all dependencies are installed:")
    print("  pip install PySide6 torch python-dotenv")
    print()
    print("Or install the full package with:")
    print("  pip install -e .")
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error starting GUI: {e}")
    print()
    print("Please check the installation and try again.")
    print("If the problem persists, check the logs directory for more details.")
    sys.exit(1)