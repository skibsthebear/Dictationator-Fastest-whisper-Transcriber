"""
Audio processor module for the dictationer project.

This module provides functionality to monitor for new audio files and transcribe
them using faster-whisper. It integrates with the existing recording system to
automatically process files as they're created.
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from faster_whisper import WhisperModel

# Import ClipboardPaster for automatic pasting
try:
    from .paster import ClipboardPaster
    PASTER_AVAILABLE = True
except ImportError as e:
    PASTER_AVAILABLE = False
    _paster_import_error = str(e)


class AudioFileHandler(FileSystemEventHandler):
    """
    File system event handler for monitoring new audio files.
    
    This handler processes new .wav files that are created in the monitored
    directory, ensuring they are fully written before attempting transcription.
    """
    
    def __init__(self, processor: 'AudioProcessor'):
        """
        Initialize the file handler.
        
        Args:
            processor: The AudioProcessor instance to handle transcription.
        """
        self.processor = processor
        self.logger = logging.getLogger('AudioProcessor.FileHandler')
    
    def on_created(self, event):
        """
        Handle file creation events.
        
        Args:
            event: The file system event containing file information.
        """
        self.logger.debug(f"[HANDLER] File system event: {event}")
        print(f"[DEBUG] File system event: {event}")
        
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            file_path = event.src_path
            self.logger.info(f"[HANDLER] File created: {file_path}")
            print(f"[DEBUG] File created: {file_path}")
            
            # Only process .wav files
            if file_path.lower().endswith('.wav'):
                self.logger.info(f"[HANDLER] New audio file detected: {file_path}")
                print(f"[DEBUG] New audio file detected: {file_path}")
                
                # Wait for file to be fully written before processing
                self.logger.info(f"[HANDLER] Waiting for file completion: {file_path}")
                print(f"[DEBUG] Waiting for file completion: {file_path}")
                self._wait_for_file_completion(file_path)
                
                # Process the file in a separate thread to avoid blocking
                self.logger.info(f"[HANDLER] Starting transcription thread for: {file_path}")
                print(f"[DEBUG] Starting transcription thread for: {file_path}")
                
                transcription_thread = threading.Thread(
                    target=self.processor.transcribe_file,
                    args=(file_path,),
                    daemon=True,
                    name=f"Transcribe-{Path(file_path).name}"
                )
                transcription_thread.start()
                self.logger.info(f"[HANDLER] Transcription thread started with ID: {transcription_thread.ident}")
                print(f"[DEBUG] Transcription thread started with ID: {transcription_thread.ident}")
            else:
                self.logger.debug(f"[HANDLER] Ignoring non-WAV file: {file_path}")
                print(f"[DEBUG] Ignoring non-WAV file: {file_path}")
        else:
            self.logger.debug(f"[HANDLER] Ignoring directory or non-create event: {event}")
            print(f"[DEBUG] Ignoring directory or non-create event: {event}")
    
    def _wait_for_file_completion(self, file_path: str, timeout: int = 30):
        """
        Wait for a file to be completely written before processing.
        
        This method monitors the file size to ensure it's stable before
        attempting transcription, preventing issues with partially written files.
        
        Args:
            file_path: Path to the file to monitor.
            timeout: Maximum time to wait for file completion in seconds.
        """
        self.logger.debug(f"[HANDLER] Waiting for file completion: {file_path}")
        
        start_time = time.time()
        last_size = -1
        stable_count = 0
        
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(file_path)
                
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 3:  # File size stable for 3 checks
                        self.logger.debug(f"[HANDLER] File appears complete: {file_path}")
                        return
                else:
                    stable_count = 0
                    last_size = current_size
                
                time.sleep(0.5)  # Check every 500ms
                
            except (OSError, FileNotFoundError):
                # File might still be being written or moved
                time.sleep(0.5)
                continue
        
        self.logger.warning(f"[HANDLER] Timeout waiting for file completion: {file_path}")


class AudioProcessor:
    """
    Main audio processor class that handles transcription and file monitoring.
    
    This class integrates faster-whisper for transcription with watchdog for
    file system monitoring, automatically processing new audio files as they
    are created in the specified directory.
    """
    
    def __init__(self, model_size: str = "base", watch_directory: str = "outputs", auto_paste: bool = True):
        """
        Initialize the audio processor.
        
        Args:
            model_size: Size of the Whisper model to use (tiny, base, small, medium, large).
            watch_directory: Directory to monitor for new audio files.
            auto_paste: Whether to automatically paste transcribed text to clipboard.
        """
        self.model_size = model_size
        self.watch_directory = Path(watch_directory)
        self.auto_paste = auto_paste
        self.logger = self._setup_logging()
        
        self.logger.info(f"[PROCESSOR] Initializing AudioProcessor")
        self.logger.info(f"[PROCESSOR] Model size: {model_size}")
        self.logger.info(f"[PROCESSOR] Watch directory: {watch_directory}")
        self.logger.info(f"[PROCESSOR] Auto-paste enabled: {auto_paste}")
        
        # Initialize faster-whisper model
        self.logger.info(f"[PROCESSOR] Loading Whisper model: {model_size}")
        try:
            self.model = WhisperModel(
                model_size, 
                device="cpu", 
                compute_type="int8"
            )
            self.logger.info(f"[PROCESSOR] Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Failed to load Whisper model: {e}")
            raise
        
        # Set up file monitoring
        self.observer = Observer()
        self.file_handler = AudioFileHandler(self)
        self._monitoring = False
        
        # Initialize ClipboardPaster if auto-paste is enabled and available
        self.paster = None
        if self.auto_paste and PASTER_AVAILABLE:
            try:
                self.paster = ClipboardPaster()
                self.logger.info("[PROCESSOR] ClipboardPaster initialized successfully")
            except Exception as e:
                self.logger.error(f"[PROCESSOR] Failed to initialize ClipboardPaster: {e}")
                self.paster = None
                print(f"Warning: Auto-paste disabled due to initialization error: {e}")
        elif self.auto_paste and not PASTER_AVAILABLE:
            self.logger.warning(f"[PROCESSOR] ClipboardPaster not available: {_paster_import_error}")
            print(f"Warning: Auto-paste disabled - ClipboardPaster not available: {_paster_import_error}")
        
        # Ensure watch directory exists
        self.watch_directory.mkdir(exist_ok=True)
        self.logger.info(f"[PROCESSOR] Watch directory ready: {self.watch_directory}")
        
        self.logger.info(f"[PROCESSOR] AudioProcessor initialization complete")
        self.logger.info(f"[PROCESSOR] Auto-paste functionality: {'enabled' if self.paster else 'disabled'}")
    
    def transcribe_file(self, file_path: str) -> Optional[str]:
        """
        Transcribe an audio file using faster-whisper.
        
        Args:
            file_path: Path to the audio file to transcribe.
            
        Returns:
            The transcribed text, or None if transcription failed.
        """
        self.logger.info(f"[PROCESSOR] Starting transcription: {file_path}")
        
        try:
            # Verify file exists and is readable
            if not os.path.exists(file_path):
                self.logger.error(f"[PROCESSOR] File not found: {file_path}")
                return None
            
            file_size = os.path.getsize(file_path)
            self.logger.info(f"[PROCESSOR] File size: {file_size} bytes")
            
            if file_size == 0:
                self.logger.warning(f"[PROCESSOR] Empty file, skipping: {file_path}")
                return None
            
            # Perform transcription
            self.logger.info(f"[PROCESSOR] Running Whisper transcription...")
            segments, info = self.model.transcribe(file_path)
            
            # Log detected language
            self.logger.info(f"[PROCESSOR] Detected language: {info.language} (probability: {info.language_probability:.2f})")
            
            # Process and display results
            print("\n" + "=" * 60)
            print(f"TRANSCRIPTION RESULTS: {Path(file_path).name}")
            print("=" * 60)
            print(f"Language: {info.language} (confidence: {info.language_probability:.2f})")
            print(f"Duration: {info.duration:.2f} seconds")
            print("-" * 60)
            
            full_text = ""
            segment_count = 0
            
            for segment in segments:
                timestamp = f"[{segment.start:.2f}s -> {segment.end:.2f}s]"
                text = segment.text.strip()
                
                print(f"{timestamp} {text}")
                full_text += text + " "
                segment_count += 1
            
            print("-" * 60)
            print(f"Total segments: {segment_count}")
            print("=" * 60)
            print()
            
            self.logger.info(f"[PROCESSOR] Transcription completed successfully")
            self.logger.info(f"[PROCESSOR] Segments processed: {segment_count}")
            
            # Get the final transcribed text
            transcribed_text = full_text.strip()
            
            # Automatically paste the transcribed text if enabled
            if self.paster and transcribed_text:
                self.logger.info("[PROCESSOR] Starting automatic paste workflow")
                # Run pasting in a separate thread to avoid blocking
                paste_thread = threading.Thread(
                    target=self._paste_text_async,
                    args=(transcribed_text,),
                    daemon=True,
                    name=f"Paste-{Path(file_path).name}"
                )
                paste_thread.start()
                self.logger.info(f"[PROCESSOR] Paste thread started with ID: {paste_thread.ident}")
            elif self.auto_paste and not self.paster:
                self.logger.warning("[PROCESSOR] Auto-paste enabled but no paster available")
            elif not transcribed_text:
                self.logger.info("[PROCESSOR] No text to paste (empty transcription)")
            
            return transcribed_text
            
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Transcription failed for {file_path}: {e}")
            print(f"\nERROR: Failed to transcribe {Path(file_path).name}: {e}\n")
            return None
    
    def start_monitoring(self):
        """
        Start monitoring the watch directory for new audio files.
        """
        if self._monitoring:
            self.logger.warning("[PROCESSOR] Monitoring already active")
            return
        
        self.logger.info(f"[PROCESSOR] Starting file monitoring: {self.watch_directory}")
        print(f"[DEBUG] Starting file monitoring: {self.watch_directory}")
        
        # Verify watch directory exists and is accessible
        try:
            if not self.watch_directory.exists():
                self.logger.info(f"[PROCESSOR] Creating watch directory: {self.watch_directory}")
                print(f"[DEBUG] Creating watch directory: {self.watch_directory}")
                self.watch_directory.mkdir(parents=True, exist_ok=True)
            
            # Test directory access
            test_file = self.watch_directory / ".processor_test"
            test_file.touch()
            test_file.unlink()
            self.logger.info(f"[PROCESSOR] Directory access verified: {self.watch_directory}")
            print(f"[DEBUG] Directory access verified: {self.watch_directory}")
            
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Cannot access watch directory: {e}")
            print(f"[ERROR] Cannot access watch directory: {e}")
            raise
        
        try:
            self.logger.info(f"[PROCESSOR] Scheduling observer for: {str(self.watch_directory)}")
            print(f"[DEBUG] Scheduling observer for: {str(self.watch_directory)}")
            
            self.observer.schedule(
                self.file_handler, 
                str(self.watch_directory), 
                recursive=False
            )
            
            self.logger.info("[PROCESSOR] Starting observer...")
            print("[DEBUG] Starting observer...")
            self.observer.start()
            self._monitoring = True
            
            print(f"\n[SUCCESS] Audio Processor Started")
            print(f"Monitoring: {self.watch_directory}")
            print(f"Model: {self.model_size}")
            print("Waiting for new audio files...\n")
            
            self.logger.info("[PROCESSOR] File monitoring started successfully")
            print("[DEBUG] File monitoring started successfully")
            
            # Verify observer is running
            if not self.observer.is_alive():
                raise Exception("Observer failed to start properly")
            
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Failed to start monitoring: {e}")
            print(f"[ERROR] Failed to start monitoring: {e}")
            self._monitoring = False
            raise
    
    def stop_monitoring(self):
        """
        Stop monitoring and cleanup resources.
        """
        if not self._monitoring:
            self.logger.info("[PROCESSOR] Monitoring not active")
            return
        
        self.logger.info("[PROCESSOR] Stopping file monitoring")
        
        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self._monitoring = False
            
            print("Audio Processor stopped.")
            self.logger.info("[PROCESSOR] File monitoring stopped successfully")
            
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Error during monitoring shutdown: {e}")
    
    def is_monitoring(self) -> bool:
        """
        Check if file monitoring is currently active.
        
        Returns:
            True if monitoring is active, False otherwise.
        """
        return self._monitoring
    
    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging for the audio processor.
        
        Returns:
            Configured logger instance.
        """
        logger = logging.getLogger('AudioProcessor')
        
        # Only configure if not already configured
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
                datefmt='%H:%M:%S'
            )
            
            # Console handler for INFO and above
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            # File handler for DEBUG and above
            file_handler = logging.FileHandler('logs/audio_processor.log', mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _paste_text_async(self, text: str):
        """
        Paste text asynchronously in a separate thread.
        
        This method handles the complete paste workflow including error handling
        and logging, ensuring that paste failures don't affect transcription.
        
        Args:
            text: The text to paste to the active application.
        """
        self.logger.info(f"[PROCESSOR] Starting async paste for {len(text)} characters")
        
        try:
            if not self.paster:
                self.logger.error("[PROCESSOR] No paster available for async paste")
                return
            
            # Perform the paste operation
            success = self.paster.paste_text(text)
            
            if success:
                self.logger.info("[PROCESSOR] Text pasted successfully")
                print(f"[SUCCESS] Transcribed text automatically pasted ({len(text)} characters)")
            else:
                self.logger.warning("[PROCESSOR] Paste operation failed")
                print("[WARNING] Failed to paste transcribed text automatically")
                
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Error during async paste: {e}")
            print(f"[ERROR] Error pasting text: {e}")


def main():
    """
    Main function for testing the audio processor standalone.
    
    This standalone entry point allows testing the AudioProcessor
    independently of the main recording system. It provides:
    - Signal handling for clean shutdown
    - File monitoring setup and management
    - Error handling and logging
    - Graceful cleanup on exit
    
    The processor will monitor the 'outputs' directory for new audio files
    and automatically transcribe them using the 'base' Whisper model.
    """
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\nShutting down audio processor...")
        if 'processor' in locals():
            processor.stop_monitoring()
        sys.exit(0)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start processor
    try:
        processor = AudioProcessor(model_size="base", watch_directory="outputs", auto_paste=True)
        processor.start_monitoring()
        
        # Keep running until interrupted
        while processor.is_monitoring():
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'processor' in locals():
            processor.stop_monitoring()


if __name__ == "__main__":
    main()