#!/usr/bin/env python3
"""
Reformatter - Detects when Ctrl key is held for more than 2 seconds and shows status.

This script uses threading and the keyboard module to monitor the Ctrl key
and shows a status window when triggered.
"""

import keyboard
import threading
import time
import subprocess
import sys
import json
import tempfile
import os
from pathlib import Path
from typing import Optional

# Import the Gemini reformatter
try:
    # Try relative import first (when used as module)
    from .gemini import GeminiReformatter, ReformattingMode
    GEMINI_AVAILABLE = True
    print("[DEBUG] Successfully imported Gemini reformatter (relative)")
except ImportError as e:
    try:
        # Try absolute import (when run standalone)
        import sys
        src_path = Path(__file__).parent.parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        from dictationer.reformatter.gemini import GeminiReformatter, ReformattingMode
        GEMINI_AVAILABLE = True
        print("[DEBUG] Successfully imported Gemini reformatter (absolute)")
    except ImportError as e2:
        print(f"[DEBUG] Failed to import Gemini reformatter: {e2}")
        GEMINI_AVAILABLE = False
        GeminiReformatter = None
        ReformattingMode = None


class ReformatterController:
    """Detects when Ctrl key is held for more than 2 seconds and manages status window."""
    
    def __init__(self, hold_duration=2.0):
        """
        Initialize the detector.
        
        Args:
            hold_duration (float): Time in seconds Ctrl must be held.
        """
        self.hold_duration = hold_duration
        self.ctrl_pressed = False
        self.press_start_time = None
        self.timer_thread = None
        self.running = True
        self.monitoring_hotkey = True  # Controls whether to monitor Ctrl presses
        self._monitoring_disabled_warned = False  # Flag to prevent spam messages
        self.lock = threading.Lock()
        
        # Status window management
        self._process: Optional[subprocess.Popen] = None
        self._state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self._state_file_path = self._state_file.name
        self._state_file.close()
        self._write_state("hidden")
        
        # Gemini reformatter
        self.gemini_reformatter = None
        if GEMINI_AVAILABLE:
            try:
                # Always use GRAMMAR_FIX mode
                self.gemini_reformatter = GeminiReformatter(
                    mode=ReformattingMode.GRAMMAR_FIX,
                    show_status_callback=self._show_status_window,
                    hide_status_callback=self._hide_status_window
                )
                print(f"✅ Gemini reformatter initialized with grammar fix mode")
            except Exception as e:
                print(f"⚠️  Gemini reformatter unavailable: {e}")
                print("   Status window will still work, but no text reformatting")
        else:
            print("⚠️  Gemini reformatter not available (missing dependencies)")
            print("   Status window will still work, but no text reformatting")
    
    def on_ctrl_press(self, event):
        """Called when Ctrl key is pressed down."""
        if event.event_type == keyboard.KEY_DOWN and event.name == 'ctrl':
            # Check if monitoring is enabled
            if not self.monitoring_hotkey:
                if not self._monitoring_disabled_warned:
                    print("🔒 Hotkey monitoring disabled - reformatting in progress")
                    self._monitoring_disabled_warned = True
                return
                
            with self.lock:
                if not self.ctrl_pressed:
                    self.ctrl_pressed = True
                    self.press_start_time = time.time()
                    print(f"Ctrl pressed - holding for {self.hold_duration}s to trigger...")
                    
                    # Start timer thread
                    self.timer_thread = threading.Thread(target=self.check_hold_duration)
                    self.timer_thread.daemon = True
                    self.timer_thread.start()
    
    def on_ctrl_release(self, event):
        """Called when Ctrl key is released."""
        if event.event_type == keyboard.KEY_UP and event.name == 'ctrl':
            with self.lock:
                if self.ctrl_pressed:
                    hold_time = time.time() - self.press_start_time
                    print(f"Ctrl released after {hold_time:.2f}s")
                    self.ctrl_pressed = False
                    self.press_start_time = None
    
    def check_hold_duration(self):
        """Check if Ctrl is held for the required duration."""
        # Sleep for the hold duration
        time.sleep(self.hold_duration)
        
        # Check if Ctrl is still pressed after the duration
        with self.lock:
            if self.ctrl_pressed and self.press_start_time:
                current_hold_time = time.time() - self.press_start_time
                if current_hold_time >= self.hold_duration:
                    print("✨ Hotkey detected! Ctrl held for 2+ seconds")
                    self._trigger_reformatting()
                    # Reset state
                    self.ctrl_pressed = False
                    self.press_start_time = None
    
    def start(self):
        """Start monitoring for Ctrl key hold."""
        print(f"Monitoring Ctrl key... Hold for {self.hold_duration}s to trigger.")
        print("Press Ctrl+C to exit.\n")
        
        # Hook keyboard events
        keyboard.hook_key('ctrl', self.on_ctrl_press, suppress=False)
        keyboard.hook_key('ctrl', self.on_ctrl_release, suppress=False)
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping detector...")
            self.stop()
    
    def _write_state(self, state: str):
        """Write state to the shared file."""
        try:
            with open(self._state_file_path, 'w') as f:
                json.dump({"state": state}, f)
        except Exception as e:
            print(f"Error writing state: {e}")
    
    def _trigger_reformatting(self):
        """Trigger Gemini reformatting with status window callbacks."""
        print("🔄 Starting reformatting process...")
        
        # Disable hotkey monitoring during reformatting
        self.monitoring_hotkey = False
        print("🔒 Hotkey monitoring disabled")
        
        # Start Gemini reformatting in a separate thread (so it doesn't block)
        # Status window will be controlled by Gemini callbacks
        if self.gemini_reformatter:
            def run_gemini_reformatting():
                try:
                    print("📤 Processing text with Gemini...")
                    success = self.gemini_reformatter.process()
                    if success:
                        print("✅ Text reformatted and pasted successfully!")
                    else:
                        print("❌ Reformatting failed")
                except Exception as e:
                    print(f"❌ Reformatting error: {e}")
                finally:
                    # Re-enable hotkey monitoring after Gemini completes
                    self.monitoring_hotkey = True
                    self._monitoring_disabled_warned = False  # Reset warning flag
                    print("🔓 Hotkey monitoring re-enabled")
            
            # Run in background thread
            gemini_thread = threading.Thread(target=run_gemini_reformatting, daemon=True)
            gemini_thread.start()
        else:
            print("⚠️  No Gemini reformatter available - showing status only")
            # Re-enable hotkey monitoring immediately if no Gemini processing
            self.monitoring_hotkey = True
            self._monitoring_disabled_warned = False  # Reset warning flag
            print("🔓 Hotkey monitoring re-enabled")

    def _show_status_window(self):
        """Show the formatting status window."""
        print("Showing formatting status window...")
        
        # Write visible state
        self._write_state("formatting")
        
        # Start window process if not running
        if self._process is None or self._process.poll() is not None:
            script_path = Path(__file__).parent / "status_window.py"
            self._process = subprocess.Popen(
                [sys.executable, str(script_path), self._state_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"Started status window process with PID: {self._process.pid}")
        
        # Window will be hidden via callback from Gemini (no auto-timer)
    
    def _hide_status_window(self):
        """Hide the status window."""
        print("Hiding formatting status window...")
        
        # Write hidden state
        self._write_state("hidden")
        
        # Give process time to exit gracefully
        time.sleep(0.2)
        
        # Force kill if still running
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
            print("Status window process terminated")
    
    def stop(self):
        """Stop the detector."""
        self.running = False
        keyboard.unhook_all()
        self._hide_status_window()
        
        # Cleanup state file
        try:
            if os.path.exists(self._state_file_path):
                os.unlink(self._state_file_path)
        except:
            pass
        
        print("Detector stopped.")

    def set_hold_duration(self, duration):
        """Change the hold duration for Ctrl key detection."""
        self.hold_duration = duration
        print(f"🔧 Hold duration changed to: {duration}s")


def main():
    """Main function to run the Reformatter controller."""
    controller = ReformatterController(hold_duration=2.0)
    controller.start()


if __name__ == "__main__":
    main()