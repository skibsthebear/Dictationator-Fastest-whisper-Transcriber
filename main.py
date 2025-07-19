"""
Entry point script for the Dictationer voice recording system.

This script provides a simple entry point that imports and runs
the main functionality from the dictationer package.
"""

import sys
import os

# Add the src directory to the Python path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dictationer.main import main

if __name__ == "__main__":
    main()