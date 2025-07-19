"""
Status indicator module for dictationer project.

Provides a floating, transparent window that displays the current state
(Recording/Transcribing) near the cursor position using PySide6.
"""

import sys
import os
import subprocess
import time
import logging
import json
import tempfile
from typing import Optional
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class IndicatorState(Enum):
    """States for the status indicator."""
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    HIDDEN = "hidden"


class StatusIndicator:
    """
    Main status indicator controller.
    
    Manages the status window in a separate process.
    """
    
    def __init__(self):
        """Initialize the status indicator."""
        self._process: Optional[subprocess.Popen] = None
        self._state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self._state_file_path = self._state_file.name
        self._state_file.close()
        
        logger.info(f"[INDICATOR] StatusIndicator initialized with state file: {self._state_file_path}")
    
    def show(self, state: IndicatorState):
        """
        Show the indicator with the specified state.
        
        Args:
            state: The state to display (RECORDING or TRANSCRIBING)
        """
        if state == IndicatorState.HIDDEN:
            self.hide()
            return
        
        logger.info(f"[INDICATOR] Showing indicator with state: {state.value}")
        
        # Write state to file
        self._write_state(state)
        
        if self._process is None or self._process.poll() is not None:
            # Start new process
            script_path = Path(__file__).parent / "status_window.py"
            self._process = subprocess.Popen(
                [sys.executable, str(script_path), self._state_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"[INDICATOR] Started status window process with PID: {self._process.pid}")
    
    def hide(self):
        """Hide the indicator window."""
        logger.info("[INDICATOR] Hiding indicator")
        
        # Write hidden state
        self._write_state(IndicatorState.HIDDEN)
        
        # Give process time to exit gracefully
        time.sleep(0.1)
        
        # Force kill if still running
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
            logger.info("[INDICATOR] Status window process terminated")
    
    def update_state(self, state: IndicatorState):
        """
        Update the indicator state (change color and text).
        
        Args:
            state: The new state to display
        """
        if state == IndicatorState.HIDDEN:
            self.hide()
            return
        
        logger.info(f"[INDICATOR] Updating state to: {state.value}")
        
        # Write new state
        self._write_state(state)
        
        # Start process if not running
        if self._process is None or self._process.poll() is not None:
            self.show(state)
    
    def _write_state(self, state: IndicatorState):
        """Write state to the shared file."""
        try:
            with open(self._state_file_path, 'w') as f:
                json.dump({"state": state.value}, f)
        except Exception as e:
            logger.error(f"[INDICATOR] Error writing state: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.hide()
        try:
            if os.path.exists(self._state_file_path):
                os.unlink(self._state_file_path)
        except:
            pass


# Global instance for easy access
_indicator_instance: Optional[StatusIndicator] = None


def get_status_indicator() -> StatusIndicator:
    """Get or create the global status indicator instance."""
    global _indicator_instance
    if _indicator_instance is None:
        _indicator_instance = StatusIndicator()
    return _indicator_instance


def show_recording():
    """Show the recording indicator."""
    indicator = get_status_indicator()
    indicator.show(IndicatorState.RECORDING)


def show_transcribing():
    """Show the transcribing indicator."""
    indicator = get_status_indicator()
    indicator.update_state(IndicatorState.TRANSCRIBING)


def hide_indicator():
    """Hide the status indicator."""
    indicator = get_status_indicator()
    indicator.hide()