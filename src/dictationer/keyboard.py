"""
Keyboard recorder module that detects Ctrl+Win+Shift+L hotkey.

This module monitors keyboard input and toggles a recording state
when the specified key combination is pressed.
"""

import keyboard
import threading
import logging
import time
from typing import Callable, Optional


class KeyboardRecorder:
    """
    Monitors keyboard for specific hotkey combination.
    
    Attributes:
        recording_state (bool): Current recording state.
        hotkey (str): The key combination to monitor.
        callback (Optional[Callable]): Function to call when state changes.
    """
    
    def __init__(self, hotkey: str = "ctrl+win+shift+l"):
        """
        Initialize keyboard recorder.
        
        Args:
            hotkey (str): Key combination to monitor. Defaults to "ctrl+win+shift+l".
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"[KEYBOARD] Initializing KeyboardRecorder with hotkey: {hotkey}")
        
        self.recording_state = False
        self.hotkey = hotkey
        self.callback: Optional[Callable[[bool], None]] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._thread_lock = threading.Lock()
        
        self.logger.info("[KEYBOARD] KeyboardRecorder initialization complete")
    
    def toggle_recording(self):
        """Toggle recording state and trigger callback if set."""
        with self._thread_lock:
            self.logger.info(f"[KEYBOARD] Hotkey detected! Current state: {self.recording_state}")
            self.recording_state = not self.recording_state
            new_state = "ON" if self.recording_state else "OFF"
            self.logger.info(f"[KEYBOARD] Recording state toggled to: {new_state}")
            print(f"Recording state: {new_state}")
            
            if self.callback:
                self.logger.info("[KEYBOARD] Calling callback function with new state")
                try:
                    self.callback(self.recording_state)
                    self.logger.info("[KEYBOARD] Callback executed successfully")
                except Exception as e:
                    self.logger.error(f"[KEYBOARD] Error in callback execution: {e}")
            else:
                self.logger.warning("[KEYBOARD] No callback function set")
    
    def set_callback(self, callback: Callable[[bool], None]):
        """
        Set callback function for state changes.
        
        Args:
            callback (Callable): Function that takes recording state as parameter.
        """
        self.logger.info("[KEYBOARD] Setting callback function")
        self.callback = callback
        self.logger.info("[KEYBOARD] Callback function set successfully")
    
    def start(self):
        """Start monitoring keyboard in a separate thread."""
        with self._thread_lock:
            if self._running:
                self.logger.warning("[KEYBOARD] Keyboard monitoring already running")
                return
            
            self.logger.info("[KEYBOARD] Starting keyboard monitoring thread")
            self._running = True
            self._thread = threading.Thread(
                target=self._monitor_keyboard, 
                daemon=True, 
                name="KeyboardMonitor"
            )
            self._thread.start()
            self.logger.info(f"[KEYBOARD] Thread started with ID: {self._thread.ident}")
            print(f"Keyboard monitoring started. Press {self.hotkey} to toggle recording.")
            self.logger.info("[KEYBOARD] Keyboard monitoring initialization complete")
    
    def _monitor_keyboard(self):
        """
        Monitor keyboard for hotkey press in dedicated thread.
        
        This method implements the core keyboard monitoring loop:
        - Registers global hotkey hooks with the system
        - Maintains monitoring state in background thread
        - Handles keyboard events and exceptions
        - Provides graceful shutdown capabilities
        
        The monitoring continues until _running flag is set to False.
        Uses small sleep intervals to prevent busy waiting while maintaining responsiveness.
        """
        self.logger.info("[KEYBOARD] Entering keyboard monitoring thread")
        
        try:
            # Register hotkey
            self.logger.info(f"[KEYBOARD] Registering hotkey: {self.hotkey}")
            keyboard.add_hotkey(self.hotkey, self.toggle_recording)
            self.logger.info("[KEYBOARD] Hotkey registered successfully")
            
            # Keep thread alive while monitoring
            self.logger.info("[KEYBOARD] Starting keyboard event loop")
            while self._running:
                try:
                    time.sleep(0.1)  # Small sleep to prevent busy waiting
                except Exception as e:
                    self.logger.error(f"[KEYBOARD] Error in monitoring loop: {e}")
                    break
            
            self.logger.info("[KEYBOARD] Exiting keyboard monitoring loop")
            
        except Exception as e:
            self.logger.error(f"[KEYBOARD] Critical error in keyboard monitoring: {e}")
        finally:
            self.logger.info("[KEYBOARD] Keyboard monitoring thread ending")
    
    def stop(self):
        """Stop monitoring keyboard."""
        self.logger.info("[KEYBOARD] Stopping keyboard monitoring")
        
        with self._thread_lock:
            self._running = False
            
            if self._thread and self._thread.is_alive():
                self.logger.info(f"[KEYBOARD] Waiting for thread {self._thread.ident} to finish")
                self._thread.join(timeout=2.0)
                
                if self._thread.is_alive():
                    self.logger.warning("[KEYBOARD] Thread did not stop gracefully")
                else:
                    self.logger.info("[KEYBOARD] Thread stopped successfully")
            
            try:
                keyboard.unhook_all()
                self.logger.info("[KEYBOARD] All keyboard hooks removed")
            except Exception as e:
                self.logger.error(f"[KEYBOARD] Error removing hooks: {e}")
            
            print("Keyboard monitoring stopped.")
            self.logger.info("[KEYBOARD] Keyboard monitoring fully stopped")
    
    def get_state(self) -> bool:
        """
        Get current recording state.
        
        Returns:
            bool: Current recording state.
        """
        with self._thread_lock:
            self.logger.debug(f"[KEYBOARD] State requested: {self.recording_state}")
            return self.recording_state