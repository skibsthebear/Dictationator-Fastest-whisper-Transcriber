"""
PySide6 GUI interface for Dictationer settings and control.

This module provides a comprehensive graphical user interface for configuring
Dictationer settings, managing device preferences, and controlling the main program.
"""

import sys
import os
import subprocess
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QTextEdit, QProgressBar, QMessageBox, QTabWidget,
    QSpacerItem, QSizePolicy, QFrame, QDialog, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal, QObject, QMutex
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

from .config import ConfigManager, DeviceDetector, ModelDetector, REFORMATTER_AVAILABLE, ReformattingMode
from .shortcut_recorder import ShortcutRecorderDialog


class ModelDownloadThread(QThread):
    """
    Thread for downloading Whisper models.
    
    Signals:
        progress_updated: Emitted with progress percentage (int).
        download_finished: Emitted when download completes successfully.
        download_error: Emitted with error message (str) when download fails.
        status_updated: Emitted with status message (str).
    """
    
    progress_updated = Signal(int)
    download_finished = Signal()
    download_error = Signal(str)
    status_updated = Signal(str)
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self.logger = logging.getLogger(f"{__name__}.ModelDownload")
    
    def run(self):
        """Download the specified model."""
        try:
            self.status_updated.emit(f"Initializing download for {self.model_name}...")
            self.progress_updated.emit(0)
            
            # Import WhisperModel here to avoid import issues
            from faster_whisper import WhisperModel
            
            self.status_updated.emit("Connecting to model repository...")
            self.progress_updated.emit(10)
            
            # Check if this is a standard faster-whisper model or HuggingFace model
            if "/" in self.model_name:
                # HuggingFace model - check if it's compatible
                self.status_updated.emit("Checking model compatibility...")
                self.progress_updated.emit(20)
                
                # Some HuggingFace models need to be downloaded with transformers first
                # then converted for faster-whisper usage
                try:
                    # Try direct faster-whisper loading first
                    self.status_updated.emit(f"Downloading {self.model_name} via faster-whisper...")
                    self.progress_updated.emit(40)
                    
                    model = WhisperModel(self.model_name, local_files_only=False)
                    
                    self.status_updated.emit("Verifying model integrity...")
                    self.progress_updated.emit(90)
                    
                    # Clean up model object
                    del model
                    
                except Exception as e:
                    # If faster-whisper can't handle it, try using transformers to download
                    self.logger.warning(f"faster-whisper failed, trying transformers approach: {e}")
                    self.status_updated.emit("Model requires transformers download...")
                    self.progress_updated.emit(50)
                    
                    # Download with transformers (this will cache it)
                    from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
                    
                    self.status_updated.emit("This might take a while... Model files are quite large (GB). Please check back in 30 minutes.")
                    self.progress_updated.emit(65)
                    
                    processor = AutoProcessor.from_pretrained(self.model_name)
                    
                    self.status_updated.emit("Downloading main model files... This is the largest part and may take 20-30 minutes.")
                    self.progress_updated.emit(70)
                    
                    model = AutoModelForSpeechSeq2Seq.from_pretrained(self.model_name)
                    
                    # Clean up
                    del processor, model
                    
                    self.status_updated.emit("Large model download complete! Model cached successfully.")
                    self.progress_updated.emit(95)
            else:
                # Standard faster-whisper model
                self.status_updated.emit(f"Downloading {self.model_name}...")
                self.progress_updated.emit(30)
                
                model = WhisperModel(self.model_name, local_files_only=False)
                
                self.status_updated.emit("Verifying model integrity...")
                self.progress_updated.emit(90)
                
                # Clean up model object
                del model
            
            self.status_updated.emit("Download completed successfully!")
            self.progress_updated.emit(100)
            self.download_finished.emit()
            
        except Exception as e:
            self.logger.error(f"Error downloading model {self.model_name}: {e}")
            self.download_error.emit(str(e))


class ModelDownloadDialog(QDialog):
    """
    Dialog for showing model download progress.
    """
    
    def __init__(self, model_name: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.download_thread = None
        self.setup_ui()
        self.start_download()
    
    def setup_ui(self):
        """Set up the download dialog UI."""
        self.setWindowTitle(f"Downloading {self.model_name}")
        self.setFixedSize(500, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"Downloading Whisper Model: {self.model_name}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Preparing download...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                background-color: #3c3c3c;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 2px;
            }
        """)
    
    def start_download(self):
        """Start the model download."""
        self.download_thread = ModelDownloadThread(self.model_name)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.status_updated.connect(self.update_status)
        self.download_thread.download_finished.connect(self.download_completed)
        self.download_thread.download_error.connect(self.download_failed)
        self.download_thread.start()
    
    def update_progress(self, value: int):
        """Update the progress bar."""
        self.progress_bar.setValue(value)
    
    def update_status(self, status: str):
        """Update the status label."""
        self.status_label.setText(status)
    
    def download_completed(self):
        """Handle successful download completion."""
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        self.status_label.setText("Download completed successfully!")
        
        # Emit signal to parent to refresh models
        if self.parent():
            if hasattr(self.parent(), 'refresh_models'):
                self.parent().refresh_models()
    
    def download_failed(self, error: str):
        """Handle download failure."""
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        self.status_label.setText(f"Download failed: {error}")
        self.progress_bar.setValue(0)
        
        QMessageBox.critical(self, "Download Failed", f"Failed to download {self.model_name}:\n\n{error}")
    
    def cancel_download(self):
        """Cancel the download."""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait(5000)  # Wait up to 5 seconds
        
        self.reject()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait(5000)
        event.accept()


class ProgramController(QObject):
    """
    Controller for starting and stopping the main Dictationer program.
    
    Signals:
        program_started: Emitted when program starts successfully.
        program_stopped: Emitted when program stops.
        program_error: Emitted when program encounters an error.
        output_received: Emitted when program output is received.
    """
    
    program_started = Signal()
    program_stopped = Signal()
    program_error = Signal(str)
    output_received = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.process: Optional[subprocess.Popen] = None
        self.logger = logging.getLogger(__name__)
    
    def start_program(self, config: Dict[str, Any]) -> bool:
        """
        Start the main Dictationer program with given configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary.
            
        Returns:
            bool: True if program started successfully, False otherwise.
        """
        if self.is_running():
            self.logger.warning("Program is already running")
            return False
        
        try:
            # Find the correct Python executable (venv or current)
            python_exe = self._find_python_executable()
            
            # Prepare environment variables from config
            env = os.environ.copy()  # Start with current environment
            env["DICTATIONER_HOTKEY"] = config.get("hotkey", "ctrl+win+shift+l")
            
            # Get the selected model name and ensure it's clean (no warning prefixes)
            model_name = config.get("whisper_model_size", "base")
            if model_name.startswith("[WARNING] "):
                model_name = model_name.replace("[WARNING] ", "")
            env["WHISPER_MODEL_SIZE"] = model_name
            
            env["OUTPUT_DIRECTORY"] = config.get("output_directory", "outputs")
            env["DEVICE_PREFERENCE"] = config.get("device_preference", "auto")
            
            # Start the main program - use the main.py file directly
            main_script = self._find_main_script()
            
            self.process = subprocess.Popen(
                [python_exe, main_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1,
                universal_newlines=True,
                cwd=Path.cwd()  # Set working directory
            )
            
            # Start output monitoring thread
            self._start_output_monitor()
            
            self.program_started.emit()
            self.logger.info(f"Main program started successfully using: {python_exe}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start program: {e}")
            self.program_error.emit(str(e))
            return False
    
    def _find_python_executable(self) -> str:
        """
        Find the correct Python executable to use.
        
        Prioritizes virtual environment Python over system Python.
        
        Returns:
            str: Path to Python executable.
        """
        import os
        from pathlib import Path
        
        # Check for venv directory in current working directory and parent directories
        current_dir = Path.cwd()
        for check_dir in [current_dir, current_dir.parent]:
            venv_dir = check_dir / "venv"
            if venv_dir.exists():
                # Windows
                venv_python = venv_dir / "Scripts" / "python.exe"
                if venv_python.exists():
                    self.logger.info(f"Found venv Python at: {venv_python}")
                    return str(venv_python)
                
                # Linux/Mac
                venv_python = venv_dir / "bin" / "python"
                if venv_python.exists():
                    self.logger.info(f"Found venv Python at: {venv_python}")
                    return str(venv_python)
        
        # Check for common virtual environment names
        for venv_name in ["venv_linux", "venv_windows", ".venv"]:
            for check_dir in [current_dir, current_dir.parent]:
                venv_dir = check_dir / venv_name
                if venv_dir.exists():
                    # Linux/Mac
                    venv_python = venv_dir / "bin" / "python"
                    if venv_python.exists():
                        self.logger.info(f"Found venv Python at: {venv_python}")
                        return str(venv_python)
                    
                    # Windows
                    venv_python = venv_dir / "Scripts" / "python.exe"
                    if venv_python.exists():
                        self.logger.info(f"Found venv Python at: {venv_python}")
                        return str(venv_python)
        
        # Check if we're already running in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.logger.info(f"Already running in virtual environment: {sys.executable}")
            return sys.executable
        
        # Fall back to current Python executable
        self.logger.warning(f"No virtual environment found, using current Python: {sys.executable}")
        return sys.executable
    
    def _find_main_script(self) -> str:
        """
        Find the main.py script to execute.
        
        Returns:
            str: Path to main.py script.
        """
        from pathlib import Path
        
        current_dir = Path.cwd()
        
        # Check for main.py in current directory
        main_script = current_dir / "main.py"
        if main_script.exists():
            self.logger.info(f"Found main script at: {main_script}")
            return str(main_script)
        
        # Check for main.py in src/dictationer/
        main_script = current_dir / "src" / "dictationer" / "main.py"
        if main_script.exists():
            self.logger.info(f"Found main script at: {main_script}")
            return str(main_script)
        
        # Fall back to relative path
        self.logger.warning("Main script not found, using relative path")
        return "main.py"
    
    def stop_program(self) -> bool:
        """
        Stop the main Dictationer program.
        
        Returns:
            bool: True if program stopped successfully, False otherwise.
        """
        if not self.is_running():
            return True
        
        try:
            self.process.terminate()
            
            # Wait for process to terminate
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
            
            self.process = None
            self.program_stopped.emit()
            self.logger.info("Main program stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop program: {e}")
            self.program_error.emit(str(e))
            return False
    
    def is_running(self) -> bool:
        """
        Check if the main program is currently running.
        
        Returns:
            bool: True if program is running, False otherwise.
        """
        if self.process is None:
            return False
        
        return self.process.poll() is None
    
    def _start_output_monitor(self) -> None:
        """Start monitoring program output in a separate thread."""
        def monitor_output():
            if self.process and self.process.stdout:
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        self.output_received.emit(line.strip())
                    if self.process.poll() is not None:
                        break
        
        thread = threading.Thread(target=monitor_output, daemon=True)
        thread.start()


class SettingsWidget(QWidget):
    """
    Widget for configuring Dictationer settings.
    
    Provides controls for all configuration options including
    device preferences, model settings, and hotkey configuration.
    """
    
    def __init__(self, config_manager: ConfigManager, program_controller: 'ProgramController' = None, main_gui: 'DictationerGUI' = None):
        super().__init__()
        self.config_manager = config_manager
        self.controller = program_controller
        self.main_gui = main_gui
        self.setup_ui()
        self.load_settings()
        if self.controller:
            self.setup_connections()
    
    def setup_ui(self) -> None:
        """Set up the settings user interface."""
        layout = QVBoxLayout(self)
        
        # Program Status Display
        status_group = QGroupBox("Program Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready to start! Go to Control tab to begin!")
        self.status_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px; padding: 10px;")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # Add some spacing after the warning
        layout.addSpacing(10)
        
        # Device Settings Group
        device_group = QGroupBox("Device Settings")
        device_layout = QGridLayout(device_group)
        
        device_layout.addWidget(QLabel("Device Preference:"), 0, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cpu", "gpu"])
        device_layout.addWidget(self.device_combo, 0, 1)
        
        # GPU Info Button
        self.gpu_info_btn = QPushButton("Check GPU Info")
        self.gpu_info_btn.clicked.connect(self.show_gpu_info)
        device_layout.addWidget(self.gpu_info_btn, 0, 2)
        
        layout.addWidget(device_group)
        
        # Model Settings Group
        model_group = QGroupBox("Model Settings")
        model_layout = QVBoxLayout(model_group)
        
        # Cached Models Section
        cached_section = QGroupBox("📦 Cached Models (Ready to Use)")
        cached_layout = QGridLayout(cached_section)
        
        cached_layout.addWidget(QLabel("Select Model:"), 0, 0)
        self.cached_model_combo = QComboBox()
        cached_layout.addWidget(self.cached_model_combo, 0, 1)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.refresh_models_btn = QPushButton("Refresh")
        self.refresh_models_btn.clicked.connect(self.refresh_models)
        self.refresh_models_btn.setMaximumWidth(100)
        buttons_layout.addWidget(self.refresh_models_btn)
        
        self.open_cache_btn = QPushButton("Models Folder")
        self.open_cache_btn.clicked.connect(self.open_models_folder)
        self.open_cache_btn.setMaximumWidth(120)
        self.open_cache_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: 1px solid #6c757d;
                padding: 6px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a6268;
                border-color: #5a6268;
            }
        """)
        buttons_layout.addWidget(self.open_cache_btn)
        
        cached_layout.addLayout(buttons_layout, 0, 2)
        
        model_layout.addWidget(cached_section)
        
        # HuggingFace Models Section
        hf_section = QGroupBox("🤗 Download HuggingFace Whisper Models")
        hf_layout = QVBoxLayout(hf_section)
        
        # Instructions
        instructions = QLabel("Enter a HuggingFace model card (e.g., distil-whisper/distil-large-v3.5):")
        instructions.setStyleSheet("color: #cccccc; margin-bottom: 5px;")
        hf_layout.addWidget(instructions)
        
        # Input row
        input_row = QHBoxLayout()
        
        self.hf_model_input = QLineEdit()
        self.hf_model_input.setPlaceholderText("distil-whisper/distil-large-v3.5")
        self.hf_model_input.returnPressed.connect(self.download_hf_model)
        input_row.addWidget(self.hf_model_input)
        
        self.hf_download_btn = QPushButton("⬇️ Download")
        self.hf_download_btn.clicked.connect(self.download_hf_model)
        self.hf_download_btn.setMaximumWidth(120)
        self.hf_download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 1px solid #2196F3;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #777777;
                border-color: #444444;
            }
        """)
        input_row.addWidget(self.hf_download_btn)
        
        hf_layout.addLayout(input_row)
        
        # Popular models suggestions
        suggestions_label = QLabel("💡 Popular models:")
        suggestions_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-top: 10px;")
        hf_layout.addWidget(suggestions_label)
        
        suggestions_widget = QWidget()
        suggestions_widget.setMinimumHeight(120)
        suggestions_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Create a centered horizontal layout
        suggestions_layout = QHBoxLayout(suggestions_widget)
        suggestions_layout.setContentsMargins(10, 10, 10, 10)
        suggestions_layout.setSpacing(15)
        
        popular_models = [
            ("distil-whisper/distil-large-v3", "⚡ Fast & Accurate", "Best for real-time transcription with good accuracy"),
            ("openai/whisper-large-v3-turbo", "🚀 Ultra Fast", "Fastest model, ideal for quick processing"), 
            ("openai/whisper-large-v3", "🎯 High Quality", "Most accurate, best for important recordings")
        ]
        
        # Add stretch at the beginning to center the cards
        suggestions_layout.addStretch()
        
        for model_id, title, description in popular_models:
            # Create a vertical card for each model
            model_card = QWidget()
            model_card.setFixedWidth(220)
            model_card.setStyleSheet("""
                QWidget {
                    background-color: #353535;
                    border: 1px solid #444;
                    border-radius: 8px;
                }
            """)
            model_card_layout = QVBoxLayout(model_card)
            model_card_layout.setContentsMargins(10, 10, 10, 10)
            model_card_layout.setSpacing(8)
            
            # Model title with emoji
            title_label = QLabel(title)
            title_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            model_card_layout.addWidget(title_label)
            
            # Model ID button  
            model_btn = QPushButton(model_id)
            # Use default parameter to capture model_id by value
            model_btn.clicked.connect(lambda checked=False, m=model_id: self.set_hf_model(m))
            model_btn.setMinimumHeight(28)
            model_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 5px 8px;
                    text-align: center;
                    font-size: 10px;
                    border-radius: 4px;
                    font-weight: 500;
                    min-height: 28px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #1565C0;
                }
            """)
            model_card_layout.addWidget(model_btn)
            
            # Add some vertical stretch to keep content at top
            model_card_layout.addStretch()
            
            suggestions_layout.addWidget(model_card)
        
        # Add stretch to keep cards compact
        suggestions_layout.addStretch()
        
        hf_layout.addWidget(suggestions_widget)
        model_layout.addWidget(hf_section)
        layout.addWidget(model_group)
        
        # Audio Settings Group
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QGridLayout(audio_group)
        
        audio_layout.addWidget(QLabel("Hotkey:"), 0, 0)
        hotkey_container = QHBoxLayout()
        self.hotkey_edit = QLineEdit()
        self.record_hotkey_btn = QPushButton("📹 Record")
        self.record_hotkey_btn.setMaximumWidth(80)
        self.record_hotkey_btn.clicked.connect(self.open_shortcut_recorder)
        hotkey_container.addWidget(self.hotkey_edit)
        hotkey_container.addWidget(self.record_hotkey_btn)
        audio_layout.addLayout(hotkey_container, 0, 1)
        
        audio_layout.addWidget(QLabel("Output Directory:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        audio_layout.addWidget(self.output_dir_edit, 1, 1)
        
        layout.addWidget(audio_group)
        
        # Reformatter Settings Group
        reformatter_group = QGroupBox("🔧 Text Reformatter (AI)")
        reformatter_layout = QGridLayout(reformatter_group)
        
        # Enable checkbox
        reformatter_layout.addWidget(QLabel("Enable:"), 0, 0)
        self.enable_reformatter_checkbox = QCheckBox("Enable Text Reformatter")
        reformatter_layout.addWidget(self.enable_reformatter_checkbox, 0, 1)
        
        # Hold duration spinbox
        reformatter_layout.addWidget(QLabel("Hold Duration (s):"), 1, 0)
        self.hold_duration_spin = QDoubleSpinBox()
        self.hold_duration_spin.setRange(1.0, 5.0)
        self.hold_duration_spin.setSingleStep(0.1)
        self.hold_duration_spin.setSuffix(" seconds")
        self.hold_duration_spin.setDecimals(1)
        reformatter_layout.addWidget(self.hold_duration_spin, 1, 1)
        
        # Info label
        info_label = QLabel("💡 Hold Ctrl for the specified duration to trigger text reformatting")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-top: 5px;")
        reformatter_layout.addWidget(info_label, 3, 0, 1, 2)
        
        layout.addWidget(reformatter_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Connect auto-save signals for all settings controls
        self.device_combo.currentTextChanged.connect(self.auto_save_settings)
        self.cached_model_combo.currentTextChanged.connect(self.auto_save_settings)
        self.hotkey_edit.textChanged.connect(self.auto_save_settings)
        self.output_dir_edit.textChanged.connect(self.auto_save_settings)
    
    def auto_save_settings(self):
        """Automatically save settings when any control changes."""
        # Use a timer to debounce rapid changes (like typing)
        if not hasattr(self, '_auto_save_timer'):
            self._auto_save_timer = QTimer()
            self._auto_save_timer.setSingleShot(True)
            self._auto_save_timer.timeout.connect(self._perform_auto_save)
        
        # Restart the timer (500ms delay to avoid saving on every keystroke)
        self._auto_save_timer.start(500)
    
    def _perform_auto_save(self):
        """Perform the actual auto-save operation."""
        self.config_manager.set("device_preference", self.device_combo.currentText())
        
        # Clean model name - remove warning prefix if present
        model_name = self.cached_model_combo.currentText()
        if model_name.startswith("[WARNING] "):
            model_name = model_name.replace("[WARNING] ", "")
        self.config_manager.set("whisper_model_size", model_name)
        
        self.config_manager.set("hotkey", self.hotkey_edit.text())
        self.config_manager.set("output_directory", self.output_dir_edit.text())
        # Always enable transcription and auto-paste - that's the core functionality
        self.config_manager.set("enable_transcription", True)
        self.config_manager.set("auto_paste", True)
        
        # Save config silently (no popup messages)
        success = self.config_manager.save_config()
        
        # Update status bar to show auto-save feedback
        main_window = self.window()  # Get the top-level window
        if hasattr(main_window, 'statusBar'):
            status_bar = main_window.statusBar()
            if success:
                status_bar.showMessage("Settings auto-saved", 2000)  # Show for 2 seconds
            else:
                status_bar.showMessage("WARNING: Auto-save failed", 3000)  # Show for 3 seconds
    
    def load_settings(self) -> None:
        """Load current settings into the UI."""
        config = self.config_manager.config
        
        # Device settings
        device_pref = config.get("device_preference", "auto")
        index = self.device_combo.findText(device_pref)
        if index >= 0:
            self.device_combo.setCurrentIndex(index)
        
        # Load cached models and set current selection
        self.refresh_models()
        model_size = config.get("whisper_model_size", "base")
        index = self.cached_model_combo.findText(model_size)
        if index >= 0:
            self.cached_model_combo.setCurrentIndex(index)
        
        # Audio settings
        self.hotkey_edit.setText(config.get("hotkey", "ctrl+win+shift+l"))
        self.output_dir_edit.setText(config.get("output_directory", "outputs"))
        
        # Reformatter settings
        self.enable_reformatter_checkbox.setChecked(config.get("enable_reformatter", False))
        
        
        # Set hold duration
        self.hold_duration_spin.setValue(config.get("reformatter_hold_duration", 2.0))
        
        # Update GPU info button based on detection
        self.update_gpu_button()
        
        # Update status display with current state
        if hasattr(self, 'main_gui'):
            self.update_status_with_reformatter()
    
    def save_settings(self) -> None:
        """Manually save current UI settings to configuration."""
        self.config_manager.set("device_preference", self.device_combo.currentText())
        
        # Clean model name - remove warning prefix if present
        model_name = self.cached_model_combo.currentText()
        if model_name.startswith("[WARNING] "):
            model_name = model_name.replace("[WARNING] ", "")
        self.config_manager.set("whisper_model_size", model_name)
        
        self.config_manager.set("hotkey", self.hotkey_edit.text())
        self.config_manager.set("output_directory", self.output_dir_edit.text())
        # Always enable transcription and auto-paste - that's the core functionality
        self.config_manager.set("enable_transcription", True)
        self.config_manager.set("auto_paste", True)
        
        # Reformatter settings
        self.config_manager.set("enable_reformatter", self.enable_reformatter_checkbox.isChecked())
        self.config_manager.set("reformatter_hold_duration", self.hold_duration_spin.value())
        
        # Update running reformatter if settings changed
        if self.main_gui and hasattr(self.main_gui, 'reformatter_controller') and self.main_gui.reformatter_controller:
            try:
                # Get new settings
                new_duration = self.hold_duration_spin.value()
                
                # Update hold duration
                self.main_gui.reformatter_controller.set_hold_duration(new_duration)
                
                print("✅ Reformatter hold duration updated live")
                
            except Exception as e:
                print(f"⚠️ Could not update running reformatter: {e}")
                # Continue with normal save - settings still saved to file
        
        if self.config_manager.save_config():
            QMessageBox.information(self, "Settings", "Settings saved successfully!")
        else:
            QMessageBox.warning(self, "Settings", "Failed to save settings!")
    
    def open_shortcut_recorder(self):
        """Open the shortcut recorder dialog."""
        dialog = ShortcutRecorderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recorded_shortcut = dialog.get_recorded_shortcut()
            if recorded_shortcut:
                self.hotkey_edit.setText(recorded_shortcut)
    
    def reset_settings(self) -> None:
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.config = self.config_manager.DEFAULT_CONFIG.copy()
            self.load_settings()
            QMessageBox.information(self, "Settings", "Settings reset to defaults!")
    
    def show_gpu_info(self) -> None:
        """Display detailed GPU information."""
        gpu_info = DeviceDetector.get_gpu_info()
        
        info_text = f"GPU Available: {gpu_info['available']}\n"
        info_text += f"Device Count: {gpu_info['device_count']}\n\n"
        
        for device in gpu_info["devices"]:
            info_text += f"Device {device['index']}: {device['name']}\n"
            info_text += f"  Total Memory: {device['memory_total'] / 1024**3:.1f} GB\n"
            info_text += f"  Reserved: {device['memory_reserved'] / 1024**3:.1f} GB\n"
            info_text += f"  Allocated: {device['memory_allocated'] / 1024**3:.1f} GB\n\n"
        
        if not gpu_info["available"]:
            info_text += "No GPU detected or PyTorch not available with CUDA support.\n"
            info_text += "CPU will be used for processing."
        
        QMessageBox.information(self, "GPU Information", info_text)
    
    def refresh_models(self) -> None:
        """Refresh the list of cached models with validation."""
        self.cached_model_combo.clear()
        
        # Get cached models
        cached_models = ModelDetector.get_cached_models()
        
        # Add only standard models that are actually cached
        standard_models = ["base", "small", "medium", "large", "tiny", "large-v1", "large-v2", "large-v3"]
        for model in standard_models:
            if model in cached_models:
                self.cached_model_combo.addItem(model)
                self.cached_model_combo.setItemData(
                    self.cached_model_combo.count()-1, 
                    f"Standard faster-whisper model: {model}", 
                    Qt.ItemDataRole.ToolTipRole
                )
        
        # Add cached HuggingFace models with validation
        if cached_models:
            hf_models = [m for m in cached_models if "/" in m]  # HuggingFace models have "/" in name
            
            for model in hf_models:
                # Validate each HuggingFace model
                validation = ModelDetector.validate_model_compatibility(model)
                if validation['valid']:
                    # Only add valid models to the dropdown
                    self.cached_model_combo.addItem(model)
                    self.cached_model_combo.setItemData(
                        self.cached_model_combo.count()-1,
                        f"VALID: {validation['reason']}",
                        Qt.ItemDataRole.ToolTipRole
                    )
                # Skip invalid models entirely - don't add them to the dropdown
                # This prevents users from selecting broken models and eliminates warning prefixes
        
        # If no models at all, add fallback and show debug info
        if self.cached_model_combo.count() == 0:
            self.cached_model_combo.addItem("base")
            self.cached_model_combo.setItemData(0, "Fallback model - will download when first used", Qt.ItemDataRole.ToolTipRole)
            
            # Add debug information for troubleshooting
            print(f"[DEBUG] No cached models found!")
            print(f"[DEBUG] Cached models detected: {cached_models}")
            
            import os
            from pathlib import Path
            cache_dir = os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")
            model_path = Path(cache_dir) / "hub"
            print(f"[DEBUG] Looking in cache directory: {model_path}")
            print(f"[DEBUG] Cache directory exists: {model_path.exists()}")
            if model_path.exists():
                dirs = [d.name for d in model_path.iterdir() if d.is_dir()]
                print(f"[DEBUG] Directories in cache: {dirs[:5]}...")  # Show first 5
    
    def set_hf_model(self, model_id: str) -> None:
        """Set the HuggingFace model input field to the selected model."""
        self.hf_model_input.setText(model_id)
    
    def download_hf_model(self) -> None:
        """Download a HuggingFace model from the input field."""
        model_name = self.hf_model_input.text().strip()
        
        if not model_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a HuggingFace model name (e.g., distil-whisper/distil-large-v3.5)")
            return
        
        # Basic validation for HuggingFace model format
        if "/" not in model_name:
            QMessageBox.warning(self, "Invalid Format", "Please use the format: organization/model-name\n\nExample: distil-whisper/distil-large-v3.5")
            return
        
        # Check if model is already cached
        if ModelDetector.is_model_cached(model_name):
            QMessageBox.information(self, "Model Already Downloaded", f"The model '{model_name}' is already downloaded and ready to use.")
            return
        
        # Disable download button during download
        self.hf_download_btn.setEnabled(False)
        self.hf_download_btn.setText("Downloading...")
        
        # Show download dialog
        dialog = ModelDownloadDialog(model_name, self)
        result = dialog.exec()
        
        # Re-enable download button
        self.hf_download_btn.setEnabled(True)
        self.hf_download_btn.setText("⬇️ Download")
        
        # Clear input field if download was successful
        if result == QDialog.DialogCode.Accepted:
            self.hf_model_input.clear()
            QMessageBox.information(self, "Download Complete", f"Model '{model_name}' has been downloaded successfully!\n\nIt should now appear in your cached models list.")
    
    def open_models_folder(self) -> None:
        """Open the models cache folder in Windows Explorer."""
        import os
        import subprocess
        from pathlib import Path
        
        try:
            # Get the HuggingFace cache directory
            cache_dir = os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")
            models_dir = Path(cache_dir) / "hub"
            
            # Create the directory if it doesn't exist
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Open in Windows Explorer (works on Windows)
            if os.name == 'nt':  # Windows
                os.startfile(str(models_dir))
            elif os.name == 'posix':  # macOS and Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(models_dir)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(models_dir)])
            else:
                # Fallback - just show the path
                QMessageBox.information(
                    self, 
                    "Models Folder Location", 
                    f"Models are stored in:\n{models_dir}\n\nYou can navigate to this folder manually."
                )
                
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error Opening Folder", 
                f"Could not open models folder: {e}\n\nModels are typically stored in:\n{Path.home() / '.cache' / 'huggingface' / 'hub'}"
            )
    
    def open_model_url(self, url: str) -> None:
        """Open model URL in default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open URL: {e}")
    
    def update_gpu_button(self) -> None:
        """Update GPU button based on detection results."""
        if DeviceDetector.detect_gpu():
            self.gpu_info_btn.setText("✓ GPU Available")
            self.gpu_info_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #4CAF50;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                    border-color: #45a049;
                }
            """)
        else:
            self.gpu_info_btn.setText("CPU Only")
            self.gpu_info_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: 1px solid #FF9800;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                    border-color: #F57C00;
                }
            """)
    
    def setup_connections(self) -> None:
        """Set up signal connections with the program controller."""
        if self.controller:
            self.controller.program_started.connect(self.on_program_started)
            self.controller.program_stopped.connect(self.on_program_stopped)
            self.controller.program_error.connect(self.on_program_error)
    
    def on_program_started(self) -> None:
        """Handle program started signal."""
        self.update_status_with_reformatter()
    
    def on_program_stopped(self) -> None:
        """Handle program stopped signal."""
        self.update_status_with_reformatter()
    
    def on_program_error(self, error: str) -> None:
        """Handle program error signal."""
        self.status_label.setText(f"Error: {error}")
        self.status_label.setStyleSheet("font-weight: bold; color: #ff5722; font-size: 14px; padding: 10px;")
    
    def update_status_with_reformatter(self) -> None:
        """Update status label to show both main system and reformatter status."""
        # Get main system status
        if self.controller and self.controller.is_running():
            main_status = "Recording System: Running"
            main_color = "#4CAF50"
        else:
            main_status = "Recording System: Ready"
            main_color = "#2196F3"
        
        # Get reformatter status
        if self.main_gui and self.main_gui.reformatter_controller:
            reformatter_status = "Reformatter: Active"
            reformatter_color = "#4CAF50"
        else:
            reformatter_status = "Reformatter: Inactive"
            reformatter_color = "#757575"
        
        # Combine status
        combined_status = f"{main_status} | {reformatter_status}"
        
        # Use main system color as primary, but show both
        self.status_label.setText(combined_status)
        self.status_label.setStyleSheet(f"font-weight: bold; color: {main_color}; font-size: 14px; padding: 10px;")


class ProgramControlWidget(QWidget):
    """
    Widget for controlling the main Dictationer program.
    
    Provides start/stop controls and real-time program output display.
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.controller = ProgramController()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self) -> None:
        """Set up the program control user interface."""
        layout = QVBoxLayout(self)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🎤 Start Recording System")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #4CAF50;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #777777;
                border-color: #444444;
            }
        """)
        self.start_btn.clicked.connect(self.start_program)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Recording System")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #f44336;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
                border-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #777777;
                border-color: #444444;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_program)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Status Display
        status_group = QGroupBox("Program Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready to start! Go to control tab to begin!")
        self.status_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # Output Display
        output_group = QGroupBox("Program Output")
        output_layout = QVBoxLayout(output_group)
        
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.document().setMaximumBlockCount(1000)  # Limit lines
        output_layout.addWidget(self.output_display)
        
        # Clear output button
        clear_btn = QPushButton("Clear Output")
        clear_btn.clicked.connect(self.output_display.clear)
        output_layout.addWidget(clear_btn)
        
        layout.addWidget(output_group)
    
    def setup_connections(self) -> None:
        """Set up signal connections."""
        self.controller.program_started.connect(self.on_program_started)
        self.controller.program_stopped.connect(self.on_program_stopped)
        self.controller.program_error.connect(self.on_program_error)
        self.controller.output_received.connect(self.on_output_received)
    
    def start_program(self) -> None:
        """Start the main program."""
        config = self.config_manager.config
        success = self.controller.start_program(config)
        
        if not success:
            QMessageBox.critical(
                self, "Error", 
                "Failed to start the recording system. Check the output for details."
            )
    
    def stop_program(self) -> None:
        """Stop the main program."""
        success = self.controller.stop_program()
        
        if not success:
            QMessageBox.warning(
                self, "Warning",
                "Failed to stop the recording system gracefully."
            )
    
    def on_program_started(self) -> None:
        """Handle program started signal."""
        self.status_label.setText("Recording System Running")
        self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.output_display.append("Recording system started successfully!")
    
    def on_program_stopped(self) -> None:
        """Handle program stopped signal."""
        self.status_label.setText("Recording System Stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: #f44336;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.output_display.append("Recording system stopped.")
    
    def on_program_error(self, error: str) -> None:
        """Handle program error signal."""
        self.status_label.setText("ERROR")
        self.status_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        self.output_display.append(f"Error: {error}")
    
    def on_output_received(self, output: str) -> None:
        """Handle program output signal."""
        self.output_display.append(output)
        
        # Auto-scroll to bottom
        cursor = self.output_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_display.setTextCursor(cursor)


class DictationerGUI(QMainWindow):
    """
    Main GUI window for Dictationer configuration and control.
    
    Provides a tabbed interface with settings configuration and
    program control functionality.
    """
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        # Reformatter controller instances
        self.reformatter_controller = None
        self.reformatter_thread = None
        self.setup_ui()
        self.setup_logging()
    
    def setup_ui(self) -> None:
        """Set up the main user interface."""
        self.setWindowTitle("Dictationer - Voice Recording System")
        self.setMinimumSize(1000, 800)
        self.resize(1000, 700)
        
        # Set window icon
        try:
            import os
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logo.png")
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
        except Exception:
            pass  # Silently fail if logo is not found
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Control tab (create first to get controller reference)
        self.control_widget = ProgramControlWidget(self.config_manager)
        
        # Settings tab (pass controller from control widget and main GUI reference)
        self.settings_widget = SettingsWidget(self.config_manager, self.control_widget.controller, self)
        tab_widget.addTab(self.settings_widget, "⚙️ Settings")
        
        # Add control tab second to maintain original order
        tab_widget.addTab(self.control_widget, "🎮 Control")
        
        layout.addWidget(tab_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Apply styling
        self.apply_styling()
        
        # Setup reformatter service
        self.setup_reformatter()
    
    def apply_styling(self) -> None:
        """Apply custom dark theme styling to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: white;
            }
            QWidget {
                background-color: #1e1e1e;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #2d2d2d;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: white;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
                color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #4a4a4a;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: white;
                selection-background-color: #2196F3;
            }
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #777777;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #777777;
                border-color: #444444;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: white;
                border-top: 1px solid #555555;
            }
        """)
    
    def setup_reformatter(self) -> None:
        """Initialize and start reformatter controller if enabled."""
        config = self.config_manager.config
        if config.get('enable_reformatter', False):
            self.start_reformatter_service()
    
    def start_reformatter_service(self) -> None:
        """Start reformatter controller in background thread."""
        try:
            from dictationer.reformatter.controller import ReformatterController
            from dictationer.reformatter.gemini import ReformattingMode
            
            # Get settings
            config = self.config_manager.config
            duration = config.get('reformatter_hold_duration', 2.0)
            
            # Always use grammar_fix mode
            mode = ReformattingMode.GRAMMAR_FIX
            
            # Create controller
            self.reformatter_controller = ReformatterController(
                hold_duration=duration
            )
            
            # Start in daemon thread
            self.reformatter_thread = threading.Thread(
                target=self.reformatter_controller.start,
                daemon=True,
                name="ReformatterService"
            )
            self.reformatter_thread.start()
            
            print("✅ Reformatter service started")
            # Update status display
            self.settings_widget.update_status_with_reformatter()
            
        except ImportError as e:
            error_msg = "Could not start reformatter service - missing dependencies."
            if "google" in str(e) or "generativeai" in str(e):
                detailed_msg = (
                    "The Google Generative AI package is not installed.\n\n"
                    "To install it, run:\n"
                    "pip install google-generativeai pydantic\n\n"
                    "Or install from requirements.txt if available."
                )
            elif "pydantic" in str(e):
                detailed_msg = (
                    "The Pydantic package is not installed.\n\n"
                    "To install it, run:\n"
                    "pip install pydantic\n\n"
                    "This package is required for AI response validation."
                )
            else:
                detailed_msg = f"Import error: {e}\n\nPlease check that all reformatter dependencies are installed."
            
            print(f"⚠️ {error_msg}")
            QMessageBox.warning(self, "Reformatter Service", f"{error_msg}\n\n{detailed_msg}")
            
        except ValueError as e:
            if "API key" in str(e) or "GEMINI_API_KEY" in str(e):
                error_msg = "Reformatter service requires a Gemini API key."
                detailed_msg = (
                    "No GEMINI_API_KEY found in environment variables.\n\n"
                    "To fix this:\n"
                    "1. Get a free API key from: https://aistudio.google.com/\n"
                    "2. Create a .env file in the project root\n"
                    "3. Add: GEMINI_API_KEY=your-api-key-here\n\n"
                    "Or set the GEMINI_API_KEY environment variable."
                )
            else:
                error_msg = "Invalid reformatter configuration."
                detailed_msg = f"Configuration error: {e}"
            
            print(f"⚠️ {error_msg}")
            QMessageBox.warning(self, "Reformatter Configuration", f"{error_msg}\n\n{detailed_msg}")
            
        except Exception as e:
            error_msg = "Unexpected error starting reformatter service."
            detailed_msg = f"Error details: {e}\n\nPlease check the console output for more information."
            print(f"⚠️ {error_msg}: {e}")
            QMessageBox.critical(self, "Reformatter Service Error", f"{error_msg}\n\n{detailed_msg}")
    
    def stop_reformatter_service(self) -> None:
        """Stop reformatter controller."""
        if self.reformatter_controller:
            self.reformatter_controller.stop()
            self.reformatter_controller = None
        if self.reformatter_thread:
            self.reformatter_thread = None
        print("🛑 Reformatter service stopped")
        # Update status display
        self.settings_widget.update_status_with_reformatter()
    
    def setup_logging(self) -> None:
        """Set up logging for the GUI."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Stop program if running
        if self.control_widget.controller.is_running():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "The recording system is still running. Stop it before exiting?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.control_widget.stop_program()
        
        # Stop reformatter service if running
        if self.reformatter_controller:
            self.stop_reformatter_service()
        
        event.accept()


def run_gui() -> None:
    """
    Run the Dictationer GUI application.
    
    This function creates and runs the PySide6 application with
    the main GUI window.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Dictationer")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon if available
    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass
    
    # Create and show main window
    window = DictationerGUI()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()