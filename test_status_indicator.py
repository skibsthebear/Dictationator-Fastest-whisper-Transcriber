#!/usr/bin/env python3
"""
Test script for the status indicator functionality.
"""

import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dictationer.status_indicator import show_recording, show_transcribing, hide_indicator

def test_status_indicator():
    """Test the status indicator with different states."""
    print("Testing Status Indicator...")
    print("The indicator will appear near your cursor position")
    print()
    
    try:
        # Test 1: Show recording state
        print("1. Showing RECORDING indicator (red)...")
        show_recording()
        time.sleep(3)
        
        # Test 2: Switch to transcribing state
        print("2. Switching to TRANSCRIBING indicator (blue)...")
        show_transcribing()
        time.sleep(3)
        
        # Test 3: Hide indicator
        print("3. Hiding indicator...")
        hide_indicator()
        time.sleep(1)
        
        # Test 4: Show and hide quickly
        print("4. Testing quick show/hide cycle...")
        show_recording()
        time.sleep(1)
        hide_indicator()
        time.sleep(0.5)
        
        # Test 5: Multiple show/hide cycles
        print("5. Testing multiple show/hide cycles...")
        for i in range(3):
            show_recording()
            time.sleep(0.5)
            show_transcribing()
            time.sleep(0.5)
            hide_indicator()
            time.sleep(0.2)
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_status_indicator()