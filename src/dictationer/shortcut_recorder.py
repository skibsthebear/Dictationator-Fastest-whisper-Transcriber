"""
Keyboard shortcut recorder dialog for Dictationer.

This module provides a GUI dialog that captures keyboard shortcuts
and formats them correctly for the Python keyboard module.
"""

import keyboard
import threading
import time
import logging
from typing import List, Optional, Set
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QTextEdit, QMessageBox
)
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QFont


class ShortcutRecorderThread(QThread):
    """
    Thread for recording keyboard shortcuts.
    
    Signals:
        keys_changed: Emitted when the current key combination changes.
        recording_finished: Emitted when recording is complete with the final shortcut.
    """
    
    keys_changed = Signal(str)
    recording_finished = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.ShortcutRecorder")
        self.is_recording = False
        self.pressed_keys: Set[str] = set()
        self.final_shortcut = ""
        self._lock = threading.Lock()
        
    def start_recording(self):
        """Start recording keyboard shortcuts."""
        with self._lock:
            if self.is_recording:
                return
            self.is_recording = True
            self.pressed_keys.clear()
            self.final_shortcut = ""
            self.start()
    
    def stop_recording(self):
        """Stop recording keyboard shortcuts."""
        with self._lock:
            self.is_recording = False
            
    def run(self):
        """Main recording loop."""
        self.logger.info("[SHORTCUT_RECORDER] Starting keyboard recording")
        
        try:
            # Hook keyboard events
            keyboard.on_press(self._on_key_press)
            keyboard.on_release(self._on_key_release)
            
            # Recording loop
            while self.is_recording:
                time.sleep(0.05)  # Small sleep to prevent busy waiting
                
            # Generate final shortcut when recording stops
            if self.pressed_keys:
                self.final_shortcut = self._format_shortcut(self.pressed_keys)
                self.recording_finished.emit(self.final_shortcut)
            
        except Exception as e:
            self.logger.error(f"[SHORTCUT_RECORDER] Error in recording: {e}")
        finally:
            try:
                keyboard.unhook_all()
            except:
                pass
            self.logger.info("[SHORTCUT_RECORDER] Recording stopped")
    
    def _on_key_press(self, event):
        """Handle key press events."""
        if not self.is_recording:
            return
            
        key_name = self._normalize_key_name(event.name)
        if key_name:
            self.pressed_keys.add(key_name)
            current_combo = self._format_shortcut(self.pressed_keys)
            self.keys_changed.emit(current_combo)
    
    def _on_key_release(self, event):
        """Handle key release events."""
        if not self.is_recording:
            return
            
        # Remove released keys from the set
        key_name = self._normalize_key_name(event.name)
        if key_name and key_name in self.pressed_keys:
            self.pressed_keys.discard(key_name)
            current_combo = self._format_shortcut(self.pressed_keys)
            self.keys_changed.emit(current_combo)
    
    def _normalize_key_name(self, key_name: str) -> Optional[str]:
        """
        Normalize key names to the format expected by the keyboard module.
        
        Args:
            key_name: Raw key name from keyboard event
            
        Returns:
            Normalized key name or None if invalid
        """
        # Map common variations to standard names
        key_mapping = {
            'left ctrl': 'ctrl',
            'right ctrl': 'ctrl',
            'left alt': 'alt',
            'right alt': 'alt', 
            'left shift': 'shift',
            'right shift': 'shift',
            'left windows': 'win',
            'right windows': 'win',
            'cmd': 'win',  # macOS command key
            'left cmd': 'win',
            'right cmd': 'win',
        }
        
        # Normalize to lowercase
        normalized = key_name.lower()
        
        # Apply mappings
        if normalized in key_mapping:
            return key_mapping[normalized]
        
        # Handle special cases
        if normalized in ['ctrl', 'alt', 'shift', 'win']:
            return normalized
        elif normalized.startswith('f') and normalized[1:].isdigit():
            return normalized  # Function keys f1-f12
        elif len(normalized) == 1 and normalized.isalnum():
            return normalized  # Single letters/numbers
        elif normalized in ['space', 'enter', 'esc', 'tab', 'backspace']:
            return normalized  # Special keys
        
        return None
    
    def _format_shortcut(self, keys: Set[str]) -> str:
        """
        Format a set of keys into the correct shortcut string.
        
        Args:
            keys: Set of normalized key names
            
        Returns:
            Formatted shortcut string (e.g., "ctrl+alt+r")
        """
        if not keys:
            return ""
        
        # Define modifier order for consistent formatting
        modifier_order = ['ctrl', 'alt', 'shift', 'win']
        
        modifiers = []
        regular_keys = []
        
        for key in keys:
            if key in modifier_order:
                modifiers.append(key)
            else:
                regular_keys.append(key)
        
        # Sort modifiers by the defined order
        modifiers.sort(key=lambda x: modifier_order.index(x))
        
        # Combine modifiers and regular keys
        all_keys = modifiers + sorted(regular_keys)
        
        return '+'.join(all_keys)


class ShortcutRecorderDialog(QDialog):
    """
    Dialog for recording keyboard shortcuts.
    
    Provides a user-friendly interface for capturing keyboard combinations
    and formatting them correctly for the keyboard module.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.ShortcutRecorderDialog")
        self.recorded_shortcut = ""
        self.recorder_thread = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Record Keyboard Shortcut")
        self.setModal(True)
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "1. Click 'Start Recording'\n"
            "2. Press and hold your desired key combination\n"
            "3. Click 'Stop Recording' when done\n"
            "4. Click 'Use This Shortcut' to save\n\n"
            "Examples:\n"
            "• Hold Ctrl+Alt then press R\n"
            "• Hold Ctrl+Shift then press F1\n"
            "• Hold Win+Alt then press Space"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #ccc; padding: 10px;")
        layout.addWidget(instructions)
        
        # Current shortcut display
        self.shortcut_label = QLabel("Press keys to record...")
        self.shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.shortcut_label.setFont(font)
        self.shortcut_label.setStyleSheet(
            "QLabel { "
            "border: 2px dashed #555; "
            "padding: 20px; "
            "margin: 10px; "
            "background-color: #404040; "
            "color: white; "
            "}"
        )
        layout.addWidget(self.shortcut_label)
        
        # Recording status
        self.status_label = QLabel("Click 'Start Recording' to begin")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #bbb; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)
        
        self.use_button = QPushButton("Use This Shortcut")
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(self.accept)
        button_layout.addWidget(self.use_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666;
                border-color: #444;
            }
        """)
    
    def setup_connections(self):
        """Setup signal connections."""
        pass  # Connections are set up when thread is created
    
    def toggle_recording(self):
        """Toggle recording state."""
        if self.recorder_thread and self.recorder_thread.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start recording keyboard shortcuts."""
        self.logger.info("[SHORTCUT_RECORDER] Starting shortcut recording")
        
        # Create and setup recorder thread
        self.recorder_thread = ShortcutRecorderThread()
        self.recorder_thread.keys_changed.connect(self.on_keys_changed)
        self.recorder_thread.recording_finished.connect(self.on_recording_finished)
        
        # Update UI
        self.record_button.setText("Stop Recording")
        self.status_label.setText("🔴 Recording... Press your key combination")
        self.shortcut_label.setText("Waiting for keys...")
        self.use_button.setEnabled(False)
        
        # Start recording
        self.recorder_thread.start_recording()
    
    def stop_recording(self):
        """Stop recording keyboard shortcuts."""
        self.logger.info("[SHORTCUT_RECORDER] Stopping shortcut recording")
        
        if self.recorder_thread:
            self.recorder_thread.stop_recording()
            self.recorder_thread.wait(2000)  # Wait up to 2 seconds for thread to finish
        
        self.record_button.setText("Start Recording")
        self.status_label.setText("Recording stopped")
    
    def on_keys_changed(self, shortcut: str):
        """Handle keys changed signal."""
        if shortcut:
            self.shortcut_label.setText(f"Current: {shortcut}")
        else:
            self.shortcut_label.setText("Press keys...")
    
    def on_recording_finished(self, shortcut: str):
        """Handle recording finished signal."""
        self.logger.info(f"[SHORTCUT_RECORDER] Recording finished: {shortcut}")
        
        self.recorded_shortcut = shortcut
        
        if shortcut:
            self.shortcut_label.setText(f"✅ Recorded: {shortcut}")
            self.status_label.setText("Recording complete! Click 'Use This Shortcut' to apply.")
            self.use_button.setEnabled(True)
        else:
            self.shortcut_label.setText("❌ No valid shortcut recorded")
            self.status_label.setText("No valid keys captured. Try again.")
        
        self.record_button.setText("Start Recording")
    
    def get_recorded_shortcut(self) -> str:
        """Get the recorded shortcut string."""
        return self.recorded_shortcut
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.recorder_thread and self.recorder_thread.is_recording:
            self.recorder_thread.stop_recording()
            self.recorder_thread.wait(1000)
        
        super().closeEvent(event)