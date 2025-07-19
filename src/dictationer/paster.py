"""
Clipboard paster module for dictationer project.

This module provides clipboard operations and keyboard simulation
for automatically pasting transcribed text.
"""

import pyperclip
import keyboard
import time
import logging
from typing import Optional

# Module-level logger for consistent logging across all paster operations
logger = logging.getLogger(__name__)


class ClipboardPaster:
    """
    Manages clipboard operations and keyboard simulation for pasting text.
    
    This class provides a complete workflow for safely pasting text by:
    1. Saving the current clipboard content
    2. Setting new text to clipboard
    3. Simulating Ctrl+V paste operation
    4. Restoring the original clipboard content
    """
    
    def __init__(self):
        """Initialize the ClipboardPaster."""
        self._saved_clipboard: Optional[str] = None
        logger.debug("ClipboardPaster initialized")
    
    def save_clipboard(self) -> bool:
        """
        Save the current clipboard content.
        
        Returns:
            bool: True if clipboard was saved successfully, False otherwise
        """
        try:
            self._saved_clipboard = pyperclip.paste()
            logger.debug(f"Clipboard saved: {len(self._saved_clipboard or '')} characters")
            return True
        except Exception as e:
            logger.error(f"Failed to save clipboard: {e}")
            self._saved_clipboard = None
            return False
    
    def set_clipboard(self, text: str) -> bool:
        """
        Set new text to clipboard.
        
        Args:
            text: The text to set to clipboard
            
        Returns:
            bool: True if clipboard was set successfully, False otherwise
        """
        try:
            pyperclip.copy(text)
            logger.debug(f"Clipboard set with {len(text)} characters")
            return True
        except Exception as e:
            logger.error(f"Failed to set clipboard: {e}")
            return False
    
    def restore_clipboard(self) -> bool:
        """
        Restore the previously saved clipboard content.
        
        Returns:
            bool: True if clipboard was restored successfully, False otherwise
        """
        if self._saved_clipboard is None:
            logger.warning("No saved clipboard content to restore")
            return False
        
        try:
            pyperclip.copy(self._saved_clipboard)
            logger.debug("Clipboard restored")
            return True
        except Exception as e:
            logger.error(f"Failed to restore clipboard: {e}")
            return False
    
    def simulate_paste(self) -> bool:
        """
        Send Ctrl+V keyboard combination to simulate paste operation.
        
        Returns:
            bool: True if paste simulation was successful, False otherwise
        """
        try:
            # Small delay to ensure clipboard is ready
            time.sleep(0.1)
            keyboard.send('ctrl+v')
            logger.debug("Paste simulation sent (Ctrl+V)")
            return True
        except Exception as e:
            logger.error(f"Failed to simulate paste: {e}")
            return False
    
    def paste_text(self, text: str, restore_delay: float = 0.5) -> bool:
        """
        Complete workflow: save clipboard, set text, paste, and restore clipboard.
        
        Args:
            text: The text to paste
            restore_delay: Delay in seconds before restoring clipboard (default: 0.5)
            
        Returns:
            bool: True if the complete workflow was successful, False otherwise
        """
        if not text:
            logger.warning("Empty text provided for pasting")
            return False
        
        logger.info(f"Starting paste workflow for {len(text)} characters")
        
        # Step 1: Save current clipboard
        if not self.save_clipboard():
            logger.error("Failed to save clipboard, aborting paste workflow")
            return False
        
        # Step 2: Set new text to clipboard
        if not self.set_clipboard(text):
            logger.error("Failed to set clipboard, aborting paste workflow")
            return False
        
        # Step 3: Simulate paste operation
        if not self.simulate_paste():
            logger.error("Failed to simulate paste")
            # Still try to restore clipboard
            self.restore_clipboard()
            return False
        
        # Step 4: Wait and restore original clipboard
        if restore_delay > 0:
            time.sleep(restore_delay)
        
        if not self.restore_clipboard():
            logger.warning("Failed to restore original clipboard content")
            # Don't return False here as the paste operation was successful
        
        logger.info("Paste workflow completed successfully")
        return True


def create_paster() -> ClipboardPaster:
    """
    Factory function to create a ClipboardPaster instance.
    
    Returns:
        ClipboardPaster: A new instance of ClipboardPaster
    """
    return ClipboardPaster()


# Convenience functions for direct usage
def paste_text_simple(text: str) -> bool:
    """
    Simple function to paste text using default settings.
    
    Args:
        text: The text to paste
        
    Returns:
        bool: True if paste was successful, False otherwise
    """
    paster = create_paster()
    return paster.paste_text(text)


def check_dependencies() -> bool:
    """
    Check if all required dependencies are available.
    
    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    try:
        import pyperclip
        import keyboard
        logger.info("All paster dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False


if __name__ == "__main__":
    # Simple test when run directly
    logging.basicConfig(level=logging.DEBUG)
    
    if not check_dependencies():
        print("Missing required dependencies!")
        exit(1)
    
    # Test the paster
    test_text = "Hello, this is a test from dictationer paster!"
    paster = create_paster()
    
    print(f"Testing paste with text: '{test_text}'")
    success = paster.paste_text(test_text)
    print(f"Paste test {'succeeded' if success else 'failed'}")