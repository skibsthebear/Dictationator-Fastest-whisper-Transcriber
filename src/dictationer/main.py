"""
Main controller for the voice recording system.

This module coordinates the keyboard monitoring and audio recording
functionality, allowing users to start/stop recording with a hotkey.
"""

import signal
import sys
import time
import logging
import threading
from datetime import datetime
from .keyboard import KeyboardRecorder
from .audio import AudioRecorder


class RecordingController:
    """
    Main controller that coordinates keyboard and audio recording.
    
    Attributes:
        keyboard (KeyboardRecorder): Handles hotkey detection.
        audio (AudioRecorder): Handles audio recording.
    """
    
    def __init__(self, output_file: str = "recording.wav", hotkey: str = "ctrl+win+shift+l",
                 enable_transcription: bool = True, model_size: str = "base", auto_paste: bool = True):
        """
        Initialize recording controller.
        
        Args:
            output_file (str): Path for output WAV file.
            hotkey (str): Hotkey combination for toggling recording.
            enable_transcription (bool): Whether to enable automatic transcription.
            model_size (str): Whisper model size for transcription.
            auto_paste (bool): Whether to automatically paste transcribed text.
        """
        # Set up logging first
        self.logger = self._setup_logging()
        self.logger.info("[MAIN] Initializing RecordingController")
        self.logger.info(f"[MAIN] Configuration - Output: {output_file}, Hotkey: {hotkey}")
        self.logger.info(f"[MAIN] Transcription - Enabled: {enable_transcription}, Model: {model_size}")
        self.logger.info(f"[MAIN] Auto-paste - Enabled: {auto_paste}")
        
        # Initialize components
        self.logger.info("[MAIN] Creating keyboard recorder")
        self.keyboard = KeyboardRecorder(hotkey=hotkey)
        
        self.logger.info("[MAIN] Creating audio recorder")
        self.audio = AudioRecorder(
            output_file=output_file,
            enable_transcription=enable_transcription,
            model_size=model_size,
            auto_paste=auto_paste
        )
        
        # Set up callback for keyboard state changes
        self.logger.info("[MAIN] Setting up keyboard callback")
        self.keyboard.set_callback(self.audio.toggle_recording)
        
        # Flag for clean shutdown
        self._running = True
        self._shutdown_lock = threading.Lock()
        
        self.logger.info("[MAIN] RecordingController initialization complete")
    
    def start(self):
        """Start the recording system."""
        self.logger.info("[MAIN] Starting recording system")
        
        print("Starting Voice Recording System")
        print("=" * 50)
        print(f"Hotkey: {self.keyboard.hotkey}")
        print(f"Output: {self.audio.output_file}")
        print("=" * 50)
        print("Press hotkey to start/stop recording")
        print("Press Ctrl+C to exit")
        print()
        
        # Start keyboard monitoring
        self.logger.info("[MAIN] Starting keyboard monitoring")
        self.keyboard.start()
        
        # Start status monitoring thread
        self.logger.info("[MAIN] Starting status monitoring thread")
        status_thread = threading.Thread(
            target=self._monitor_status, 
            daemon=True, 
            name="StatusMonitor"
        )
        status_thread.start()
        self.logger.info(f"[MAIN] Status thread started with ID: {status_thread.ident}")
        
        try:
            # Keep main thread alive
            self.logger.info("[MAIN] Entering main loop")
            while self._running:
                time.sleep(0.5)  # Increased sleep for less CPU usage
        
        except KeyboardInterrupt:
            self.logger.info("[MAIN] Keyboard interrupt received")
            print("\nShutting down...")
        
        finally:
            self.logger.info("[MAIN] Starting shutdown process")
            self.stop()
    
    def stop(self):
        """Stop the recording system gracefully."""
        with self._shutdown_lock:
            if not self._running:
                self.logger.info("[MAIN] System already stopping")
                return
                
            self.logger.info("[MAIN] Initiating graceful shutdown")
            self._running = False
            
            # Stop recording if active
            if self.audio.is_recording():
                self.logger.info("[MAIN] Stopping active recording")
                print("Stopping active recording...")
                self.audio.stop_recording()
                self.logger.info("[MAIN] Active recording stopped")
            
            # Stop keyboard monitoring
            self.logger.info("[MAIN] Stopping keyboard monitoring")
            self.keyboard.stop()
            
            # Clean up audio resources
            self.logger.info("[MAIN] Cleaning up audio resources")
            self.audio.cleanup()
            
            print("Recording system stopped.")
            self.logger.info("[MAIN] Recording system shutdown complete")
    
    def _monitor_status(self):
        """Monitor system status in background thread."""
        self.logger.info("[STATUS] Status monitoring thread started")
        
        last_recording_state = False
        
        while self._running:
            try:
                current_recording = self.audio.is_recording()
                
                # Log state changes
                if current_recording != last_recording_state:
                    self.logger.info(f"[STATUS] Recording state changed: {last_recording_state} -> {current_recording}")
                    last_recording_state = current_recording
                
                # Sleep before next check
                time.sleep(2.0)
                
            except Exception as e:
                self.logger.error(f"[STATUS] Error in status monitoring: {e}")
                time.sleep(1.0)
        
        self.logger.info("[STATUS] Status monitoring thread ending")
    
    def _setup_logging(self):
        """Set up comprehensive logging for debugging."""
        # Create logger
        logger = logging.getLogger('VoiceRecorder')
        logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler for INFO and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        logger.addHandler(console_handler)
        
        # Ensure logs directory exists
        import os
        os.makedirs('logs', exist_ok=True)
        
        # File handler for DEBUG and above
        file_handler = logging.FileHandler('logs/voice_recorder_debug.log', mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"[MAIN] Logging initialized at {datetime.now()}")
        return logger


def signal_handler(sig, frame):
    """
    Handle interrupt signal for clean shutdown.
    
    Args:
        sig: Signal number that was received
        frame: Current stack frame (unused)
    """
    logger = logging.getLogger('VoiceRecorder')
    logger.info(f"[SIGNAL] Received signal {sig}")
    print("\nReceived interrupt signal...")
    sys.exit(0)


def main():
    """
    Main entry point for the recording system.
    
    Initializes the complete voice recording and transcription system with:
    - Signal handling for graceful shutdown
    - Configuration loading from environment or config files
    - Error handling and logging
    - Directory setup for outputs
    
    The function will run indefinitely until interrupted by the user
    or a critical error occurs.
    
    Raises:
        SystemExit: On critical errors or user interruption
    """
    # Set up signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("Voice Recording System - Enhanced Threading & Logging")
    print("=" * 60)
    print(f"Starting at: {datetime.now()}")
    print()
    
    # Load configuration
    try:
        from .config import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.config
        print(f"Configuration loaded: {config_manager.config_file}")
    except ImportError:
        # Fallback to default configuration if config module not available
        config = {
            "hotkey": "ctrl+win+shift+l",
            "whisper_model_size": "base",
            "output_directory": "outputs",
            "enable_transcription": True,
            "auto_paste": True
        }
        print("Using default configuration")
    
    # Ensure outputs directory exists
    import os
    output_dir = config.get("output_directory", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create and start controller
    try:
        controller = RecordingController(
            output_file=os.path.join(output_dir, "recording.wav"),
            hotkey=config.get("hotkey", "ctrl+win+shift+l"),
            enable_transcription=config.get("enable_transcription", True),
            model_size=config.get("whisper_model_size", "base"),
            auto_paste=config.get("auto_paste", True)
        )
        
        controller.start()
        
    except Exception as e:
        import traceback
        
        logger = logging.getLogger('VoiceRecorder')
        logger.error(f"[MAIN] Critical error in main: {e}")
        logger.error(f"[MAIN] Error type: {type(e).__name__}")
        logger.error(f"[MAIN] Full traceback: {traceback.format_exc()}")
        
        print(f"Critical Error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide specific guidance for common issues
        if "charmap" in str(e) or "codec" in str(e) or "unicode" in str(e).lower():
            print("\n=== UNICODE ENCODING ERROR DETECTED ===")
            print("This error is caused by Windows console encoding issues with Unicode characters.")
            print("\nRecommended Solutions:")
            print("1. Use PowerShell instead of Command Prompt")
            print("2. Set encoding: set PYTHONIOENCODING=utf-8")
            print("3. Use the GUI launcher: start_gui.bat")
            print("4. Remove emoji characters from model names in settings")
            print("\nFull error details saved to: logs/voice_recorder_debug.log")
        else:
            print(f"\nFull error details saved to: logs/voice_recorder_debug.log")
        
        sys.exit(1)


if __name__ == "__main__":
    main()