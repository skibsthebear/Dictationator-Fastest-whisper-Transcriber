"""
Reformatter status window subprocess.

This runs as a separate process to display formatting status.
"""

import sys
import json
import time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtGui import QPainter, QBrush, QColor, QPainterPath, QFont, QCursor


class ReformatterStatusWindow(QWidget):
    """
    Custom transparent window showing formatting status.
    """
    
    def __init__(self, state_file_path: str):
        super().__init__()
        self.state_file_path = state_file_path
        self.current_state = "hidden"
        
        # UI Configuration (before init_ui)
        self.background_color = QColor(68, 68, 255, 230)  # Blue with alpha
        self.text = "Formatting now..."
        
        self.init_ui()
        
        # Position offset from cursor
        self.position_offset = (20, 20)
        
        # State monitoring
        self.state_timer = QTimer()
        self.state_timer.timeout.connect(self.check_state)
        self.state_timer.start(100)  # Check every 100ms
    
    def init_ui(self):
        """Initialize the UI elements."""
        # Window flags for borderless, always-on-top window
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        
        # Enable transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Set fixed size (wider for longer text)
        self.setFixedSize(120, 20)
        
        # Create label
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; background: transparent;")
        font = QFont("Arial", 9, QFont.Bold)
        self.label.setFont(font)
        self.label.setGeometry(0, 0, 120, 20)
        self.label.setText(self.text)
    
    def paintEvent(self, event):
        """Custom paint event for rounded rectangle background."""
        if self.current_state == "hidden":
            return
        
        # Safety checks
        if not self.isVisible() or self.width() <= 0 or self.height() <= 0:
            return
        
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
                
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Create rounded rectangle path
            path = QPainterPath()
            rect = QRect(0, 0, self.width(), self.height())
            path.addRoundedRect(rect, 10, 10)
            
            # Fill with blue color
            painter.fillPath(path, QBrush(self.background_color))
            
            painter.end()
        except Exception as e:
            # Silently ignore paint errors
            pass
    
    def check_state(self):
        """Check state file for updates."""
        try:
            with open(self.state_file_path, 'r') as f:
                data = json.load(f)
                new_state = data.get('state', 'hidden')
                
                if new_state != self.current_state:
                    self.update_state(new_state)
                    
        except Exception:
            # File might not exist yet or be temporarily inaccessible
            pass
    
    def update_state(self, new_state: str):
        """Update the window state."""
        self.current_state = new_state
        
        if new_state == "hidden":
            self.hide()
            # Add a small delay before quitting to ensure cleanup
            QTimer.singleShot(100, QApplication.quit)
        elif new_state == "formatting":
            if not self.isVisible():
                self.show()
                self.set_position()  # Set initial position
            # Only trigger repaint if window is visible
            if self.isVisible():
                self.update()  # Trigger repaint
    
    def set_position(self):
        """Set window position at cursor location (once)."""
        try:
            # Get cursor position
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() + self.position_offset[0]
            y = cursor_pos.y() + self.position_offset[1]
            
            # Ensure window stays on screen
            screen = QApplication.primaryScreen().geometry()
            if x + self.width() > screen.width():
                x = screen.width() - self.width() - 10
            if y + self.height() > screen.height():
                y = screen.height() - self.height() - 10
            
            # Set position
            self.move(x, y)
            
        except Exception:
            pass  # Ignore errors in position setting


def main():
    """Main entry point for the reformatter status window process."""
    if len(sys.argv) < 2:
        print("Error: State file path required")
        sys.exit(1)
    
    state_file_path = sys.argv[1]
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create and show window
    window = ReformatterStatusWindow(state_file_path)
    
    # Check initial state
    window.check_state()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()