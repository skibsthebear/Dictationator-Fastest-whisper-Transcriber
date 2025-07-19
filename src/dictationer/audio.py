"""
Audio recorder module using PyAudio.

This module handles audio recording functionality, saving recordings
as WAV files with 16-bit depth and 16kHz sample rate.
"""

import pyaudio
import wave
import threading
import time
import logging
from typing import Optional
import os

# Import status indicator
try:
    from .status_indicator import show_recording, show_transcribing, hide_indicator
    STATUS_INDICATOR_AVAILABLE = True
except ImportError as e:
    STATUS_INDICATOR_AVAILABLE = False
    print(f"[DEBUG] Status indicator not available: {e}")

# Import AudioProcessor for automatic transcription
try:
    from .processor import AudioProcessor
    PROCESSOR_AVAILABLE = True
    print("[DEBUG] AudioProcessor import: SUCCESS")
except ImportError as e:
    PROCESSOR_AVAILABLE = False
    _processor_import_error = str(e)
    print(f"[DEBUG] AudioProcessor import: FAILED - {e}")

# Test individual dependencies
print("[DEBUG] Testing processor dependencies...")
try:
    from faster_whisper import WhisperModel
    print("[DEBUG] faster-whisper: OK")
except ImportError as e:
    print(f"[DEBUG] faster-whisper: FAILED - {e}")

try:
    from watchdog.observers import Observer
    print("[DEBUG] watchdog: OK")
except ImportError as e:
    print(f"[DEBUG] watchdog: FAILED - {e}")

try:
    from .paster import ClipboardPaster
    print("[DEBUG] paster: OK")
except ImportError as e:
    print(f"[DEBUG] paster: FAILED - {e}")


class AudioRecorder:
    """
    Handles audio recording using PyAudio.
    
    Attributes:
        sample_rate (int): Audio sample rate in Hz.
        channels (int): Number of audio channels.
        chunk_size (int): Size of audio chunks to read.
        format (int): PyAudio format for audio data.
        output_file (str): Path to output WAV file.
    """
    
    def __init__(self, output_file: str = "recording.wav", enable_transcription: bool = True, model_size: str = "base", auto_paste: bool = True):
        """
        Initialize audio recorder.
        
        Args:
            output_file (str): Path for output WAV file. Defaults to "recording.wav".
            enable_transcription (bool): Whether to enable automatic transcription. Defaults to True.
            model_size (str): Whisper model size for transcription. Defaults to "base".
            auto_paste (bool): Whether to automatically paste transcribed text. Defaults to True.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"[AUDIO] Initializing AudioRecorder with output: {output_file}")
        
        self.sample_rate = 16000  # 16kHz
        self.channels = 1  # Mono recording
        self.chunk_size = 1024
        self.format = pyaudio.paInt16  # 16-bit
        self.output_file = output_file
        self.enable_transcription = enable_transcription
        self.auto_paste = auto_paste
        
        self._recording = False
        self._thread: Optional[threading.Thread] = None
        self._frames = []
        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._thread_lock = threading.Lock()
        
        # Initialize AudioProcessor for transcription if available and enabled
        self.processor = None
        
        self.logger.info(f"[AUDIO] Processor initialization check:")
        self.logger.info(f"[AUDIO] - enable_transcription: {self.enable_transcription}")
        self.logger.info(f"[AUDIO] - PROCESSOR_AVAILABLE: {PROCESSOR_AVAILABLE}")
        print(f"[DEBUG] enable_transcription: {self.enable_transcription}")
        print(f"[DEBUG] PROCESSOR_AVAILABLE: {PROCESSOR_AVAILABLE}")
        
        if self.enable_transcription and PROCESSOR_AVAILABLE:
            try:
                # Use exact model name without normalization
                original_model_size = model_size
                self.logger.info(f"[AUDIO] Using exact model name: '{model_size}'")
                print(f"[DEBUG] Using exact model name: '{model_size}'")
                
                self.logger.info(f"[AUDIO] Initializing AudioProcessor with model: {model_size}")
                print(f"[DEBUG] Initializing AudioProcessor with model: {model_size}")
                
                # Check if HuggingFace model is available (using normalized name)
                if "/" in model_size:
                    try:
                        from .config import ModelDetector
                        if not ModelDetector.is_model_cached(model_size):
                            self.logger.warning(f"[AUDIO] HuggingFace model '{model_size}' not found in cache")
                            print(f"[WARNING] Model '{model_size}' not found in cache")
                            print(f"[WARNING] This may cause loading to fail or be very slow")
                    except ImportError:
                        self.logger.warning("[AUDIO] ModelDetector not available for cache check")
                
                # Extract directory from output_file for processor watch directory
                output_dir = os.path.dirname(self.output_file) or "outputs"
                self.logger.info(f"[AUDIO] Watch directory: {output_dir}")
                print(f"[DEBUG] Watch directory: {output_dir}")
                
                # Create processor instance with file monitoring DISABLED
                # We'll use direct transcription calls instead to avoid dual processing
                self.processor = AudioProcessor(
                    model_size=model_size, 
                    watch_directory=output_dir, 
                    auto_paste=self.auto_paste, 
                    enable_file_monitoring=False
                )
                self.logger.info("[AUDIO] AudioProcessor created successfully")
                print("[DEBUG] AudioProcessor created successfully")
                self.logger.info("[AUDIO] Using direct transcription mode (no file monitoring)")
                print("[DEBUG] Using direct transcription mode (no file monitoring)")
                
            except Exception as e:
                import traceback
                
                # Enhanced error logging with full details
                error_traceback = traceback.format_exc()
                self.logger.error(f"[AUDIO] Failed to initialize AudioProcessor: {e}")
                self.logger.error(f"[AUDIO] Error type: {type(e).__name__}")
                self.logger.error(f"[AUDIO] Model causing error: '{model_size}'")
                self.logger.error(f"[AUDIO] Full traceback: {error_traceback}")
                
                print(f"[ERROR] AudioProcessor initialization failed: {e}")
                print(f"[ERROR] Error type: {type(e).__name__}")
                print(f"[ERROR] Model: '{model_size}'")
                
                # Check for specific error types and provide targeted guidance
                error_str = str(e).lower()
                if "charmap" in error_str or "codec" in error_str or "unicode" in error_str:
                    print(f"\n=== UNICODE ENCODING ERROR DETECTED ===")
                    print(f"[CAUSE] Windows console cannot display Unicode characters (emojis) in model names")
                    print(f"[ISSUE] Model name likely contains emoji characters from GUI validation")
                    print(f"[SOLUTIONS]:")
                    print(f"  1. Use Windows PowerShell instead of Command Prompt")
                    print(f"  2. Set encoding: set PYTHONIOENCODING=utf-8") 
                    print(f"  3. Use GUI launcher: start_gui.bat (recommended)")
                    print(f"  4. Switch to 'base' model in settings to avoid HuggingFace models")
                    print(f"  5. Check settings file: config/settings.json for emoji characters")
                    print(f"========================================\n")
                    self.logger.error(f"[AUDIO] Unicode encoding error - Windows console cannot handle emojis in model names")
                    self.logger.error(f"[AUDIO] This is typically caused by [WARNING] prefix added to invalid models in GUI")
                elif "/" in model_size:
                    print(f"\n=== HUGGINGFACE MODEL ERROR ===")
                    print(f"[MODEL] HuggingFace model: '{model_size}'")
                    print(f"[SOLUTIONS]:")
                    print(f"  1. Download model via GUI Settings tab first")
                    print(f"  2. Switch to 'base' model in settings") 
                    print(f"  3. Check model compatibility with faster-whisper")
                    print(f"  4. Verify model exists: https://huggingface.co/{model_size}")
                    print(f"===============================\n")
                    self.logger.error(f"[AUDIO] HuggingFace model '{model_size}' failed to load")
                    self.logger.error(f"[AUDIO] Try downloading via GUI or use 'base' model")
                else:
                    print(f"\n=== STANDARD MODEL ERROR ===")
                    print(f"[MODEL] Standard model: '{model_size}'")
                    print(f"[SOLUTIONS]:")
                    print(f"  1. Try 'base' model as fallback")
                    print(f"  2. Check faster-whisper installation")
                    print(f"  3. Verify model name is correct")
                    print(f"=============================\n")
                    self.logger.error(f"[AUDIO] Standard model '{model_size}' failed to load")
                
                # Log detailed information for debugging
                self.logger.error(f"[AUDIO] === DEBUGGING INFORMATION ===")
                self.logger.error(f"[AUDIO] Output directory: {output_dir}")
                self.logger.error(f"[AUDIO] Enable transcription: {self.enable_transcription}")
                self.logger.error(f"[AUDIO] Auto paste: {self.auto_paste}")
                self.logger.error(f"[AUDIO] PROCESSOR_AVAILABLE: {PROCESSOR_AVAILABLE}")
                
                self.processor = None
                print(f"[WARNING] Transcription disabled due to model loading error")
                print(f"[DEBUG] Full error details logged to: logs/voice_recorder_debug.log")
                print(f"[DEBUG] Check logs/audio_processor.log for AudioProcessor-specific errors")
                
        elif self.enable_transcription and not PROCESSOR_AVAILABLE:
            self.logger.warning(f"[AUDIO] AudioProcessor not available: {_processor_import_error}")
            print(f"[ERROR] AudioProcessor not available: {_processor_import_error}")
            print(f"Warning: Transcription disabled - AudioProcessor not available: {_processor_import_error}")
            
        elif not self.enable_transcription:
            self.logger.info("[AUDIO] Transcription disabled by configuration")
            print("[DEBUG] Transcription disabled by configuration")
        
        self.logger.info("[AUDIO] AudioRecorder initialization complete")
        self.logger.info(f"[AUDIO] Audio settings - Sample rate: {self.sample_rate}Hz, Channels: {self.channels}, Chunk size: {self.chunk_size}")
        self.logger.info(f"[AUDIO] Transcription enabled: {self.enable_transcription and self.processor is not None}")
        self.logger.info(f"[AUDIO] Auto-paste enabled: {self.auto_paste and self.processor is not None and getattr(self.processor, 'paster', None) is not None}")
    
    def start_recording(self):
        """Start recording audio in a separate thread."""
        with self._thread_lock:
            if self._recording:
                self.logger.warning("[AUDIO] Already recording, ignoring start request")
                print("Already recording...")
                return
            
            self.logger.info("[AUDIO] Starting audio recording")
            self._recording = True
            self._frames = []  # Clear previous recording
            self.logger.info("[AUDIO] Cleared previous recording frames")
            
            self._thread = threading.Thread(
                target=self._record, 
                daemon=True, 
                name="AudioRecorder"
            )
            self._thread.start()
            self.logger.info(f"[AUDIO] Recording thread started with ID: {self._thread.ident}")
            print(f"Recording started... Output will be saved to {self.output_file}")
            
            # Show recording indicator
            if STATUS_INDICATOR_AVAILABLE:
                try:
                    show_recording()
                    self.logger.info("[AUDIO] Recording indicator shown")
                except Exception as e:
                    self.logger.error(f"[AUDIO] Failed to show recording indicator: {e}")
    
    def stop_recording(self):
        """Stop recording and save to file."""
        with self._thread_lock:
            if not self._recording:
                self.logger.warning("[AUDIO] Not currently recording, ignoring stop request")
                print("Not currently recording...")
                return
            
            self.logger.info("[AUDIO] Stopping audio recording")
            self._recording = False
            
            # Wait for recording thread to finish
            if self._thread and self._thread.is_alive():
                self.logger.info(f"[AUDIO] Waiting for recording thread {self._thread.ident} to finish")
                self._thread.join(timeout=3.0)
                
                if self._thread.is_alive():
                    self.logger.warning("[AUDIO] Recording thread did not stop gracefully")
                else:
                    self.logger.info("[AUDIO] Recording thread stopped successfully")
            
            # Save recording
            self.logger.info("[AUDIO] Saving recorded audio")
            self._save_recording()
            print(f"Recording stopped and saved to {self.output_file}")
            self.logger.info("[AUDIO] Recording stop process complete")
            
            # Hide recording indicator, will show transcribing if needed
            if STATUS_INDICATOR_AVAILABLE:
                try:
                    hide_indicator()
                    self.logger.info("[AUDIO] Recording indicator hidden")
                except Exception as e:
                    self.logger.error(f"[AUDIO] Failed to hide recording indicator: {e}")
    
    def _record(self):
        """
        Record audio from microphone in dedicated thread.
        
        This method runs the core audio recording loop, handling:
        - PyAudio initialization and configuration
        - Audio stream management
        - Real-time audio data capture
        - Error handling and recovery
        - Resource cleanup
        
        The recording continues until _recording flag is set to False.
        Audio data is stored in _frames list for later processing.
        """
        self.logger.info("[AUDIO] Entering recording thread")
        
        try:
            # Initialize PyAudio
            self.logger.info("[AUDIO] Initializing PyAudio")
            self._audio = pyaudio.PyAudio()
            self.logger.info("[AUDIO] PyAudio initialized successfully")
            
            # Open stream
            self.logger.info(f"[AUDIO] Opening audio stream - Format: {self.format}, Channels: {self.channels}, Rate: {self.sample_rate}")
            self._stream = self._audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            self.logger.info("[AUDIO] Audio stream opened successfully")
            
            print("Recording audio...")
            self.logger.info("[AUDIO] Starting audio capture loop")
            
            frame_count = 0
            # Record audio chunks
            while self._recording:
                try:
                    data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                    self._frames.append(data)
                    frame_count += 1
                    
                    if frame_count % 100 == 0:  # Log every 100 frames (~1 second at 16kHz)
                        self.logger.debug(f"[AUDIO] Captured {frame_count} frames")
                        
                except Exception as e:
                    self.logger.error(f"[AUDIO] Error reading audio chunk: {e}")
                    break
            
            self.logger.info(f"[AUDIO] Recording loop ended. Total frames captured: {frame_count}")
            
        except Exception as e:
            self.logger.error(f"[AUDIO] Critical error in recording: {e}")
            print(f"Error initializing audio: {e}")
            self._recording = False
        
        finally:
            # Clean up
            self.logger.info("[AUDIO] Cleaning up audio resources")
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                    self.logger.info("[AUDIO] Audio stream closed")
                except Exception as e:
                    self.logger.error(f"[AUDIO] Error closing stream: {e}")
                    
            if self._audio:
                try:
                    self._audio.terminate()
                    self.logger.info("[AUDIO] PyAudio terminated")
                except Exception as e:
                    self.logger.error(f"[AUDIO] Error terminating PyAudio: {e}")
            
            self.logger.info("[AUDIO] Recording thread ending")
    
    def _save_recording(self):
        """
        Save recorded frames to WAV file with proper formatting.
        
        This method handles the complete file saving workflow:
        - Directory creation if needed
        - WAV file format configuration (16-bit, 16kHz, mono)
        - Audio data concatenation and writing
        - Duration calculation and logging
        - Automatic transcription initiation if enabled
        
        The saved file follows WAV format standards and is immediately
        available for transcription processing.
        """
        self.logger.info("[AUDIO] Starting save process")
        
        if not self._frames:
            self.logger.warning("[AUDIO] No audio data to save")
            print("No audio data to save.")
            return
        
        self.logger.info(f"[AUDIO] Saving {len(self._frames)} frames to {self.output_file}")
        
        try:
            # Ensure directory exists
            output_dir = os.path.dirname(self.output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                self.logger.info(f"[AUDIO] Ensured directory exists: {output_dir}")
            
            # Calculate recording duration
            duration = len(self._frames) * self.chunk_size / self.sample_rate
            self.logger.info(f"[AUDIO] Recording duration: {duration:.2f} seconds")
            
            # Open WAV file for writing
            self.logger.info("[AUDIO] Opening WAV file for writing")
            with wave.open(self.output_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                
                # Join and write frames
                audio_data = b''.join(self._frames)
                wf.writeframes(audio_data)
                self.logger.info(f"[AUDIO] Written {len(audio_data)} bytes to WAV file")
            
            self.logger.info(f"[AUDIO] File saved successfully: {self.output_file}")
            print(f"Audio saved: {len(self._frames)} frames, approximately {duration:.2f} seconds")
            
            # Start transcription immediately if processor is available
            if self.processor is not None:
                self.logger.info("[AUDIO] Starting direct transcription")
                print("[DEBUG] Starting direct transcription")
                transcription_thread = threading.Thread(
                    target=self._transcribe_recording,
                    args=(self.output_file,),
                    daemon=True,
                    name=f"Transcribe-{os.path.basename(self.output_file)}"
                )
                transcription_thread.start()
                self.logger.info(f"[AUDIO] Transcription thread started with ID: {transcription_thread.ident}")
            else:
                self.logger.info("[AUDIO] No processor available - skipping transcription")
                print("[DEBUG] No processor available - skipping transcription")
        
        except Exception as e:
            self.logger.error(f"[AUDIO] Error saving recording: {e}")
            print(f"Error saving recording: {e}")
    
    def is_recording(self) -> bool:
        """
        Check if currently recording.
        
        Returns:
            bool: True if recording, False otherwise.
        """
        with self._thread_lock:
            self.logger.debug(f"[AUDIO] Recording status requested: {self._recording}")
            return self._recording
    
    def toggle_recording(self, state: bool):
        """
        Toggle recording based on state.
        
        Args:
            state (bool): True to start recording, False to stop.
        """
        self.logger.info(f"[AUDIO] Toggle recording called with state: {state}")
        
        if state and not self._recording:
            self.logger.info("[AUDIO] State is True and not recording - starting recording")
            self.start_recording()
        elif not state and self._recording:
            self.logger.info("[AUDIO] State is False and currently recording - stopping recording")
            self.stop_recording()
        else:
            self.logger.info(f"[AUDIO] No action needed - state: {state}, recording: {self._recording}")
    
    def _transcribe_recording(self, file_path: str):
        """
        Transcribe a recording file using the AudioProcessor.
        
        This method runs in a separate thread to avoid blocking the main recording workflow.
        
        Args:
            file_path (str): Path to the audio file to transcribe.
        """
        self.logger.info(f"[AUDIO] Starting transcription for: {file_path}")
        
        try:
            if self.processor is None:
                self.logger.warning("[AUDIO] No processor available for transcription")
                return
            
            # Call the processor's transcribe_file method
            result = self.processor.transcribe_file(file_path)
            
            if result:
                self.logger.info(f"[AUDIO] Transcription completed successfully for: {file_path}")
                print(f"\nTranscription completed for: {os.path.basename(file_path)}")
            else:
                self.logger.warning(f"[AUDIO] Transcription returned no result for: {file_path}")
                print(f"\nTranscription failed for: {os.path.basename(file_path)}")
                
        except Exception as e:
            self.logger.error(f"[AUDIO] Error during transcription of {file_path}: {e}")
            print(f"\nTranscription error for {os.path.basename(file_path)}: {e}")
    
    def cleanup(self):
        """
        Clean up resources including stopping the audio processor monitoring.
        """
        self.logger.info("[AUDIO] Starting cleanup process")
        
        # Stop any active recording
        if self._recording:
            self.logger.info("[AUDIO] Stopping active recording during cleanup")
            self.stop_recording()
        
        # Clean up processor if available
        if self.processor is not None:
            try:
                self.logger.info("[AUDIO] Cleaning up processor")
                # Only stop monitoring if it was started (which it won't be in our simplified architecture)
                if hasattr(self.processor, '_monitoring') and self.processor._monitoring:
                    self.processor.stop_monitoring()
                    self.logger.info("[AUDIO] Processor monitoring stopped successfully")
                else:
                    self.logger.info("[AUDIO] No active monitoring to stop")
            except Exception as e:
                self.logger.error(f"[AUDIO] Error during processor cleanup: {e}")
        
        self.logger.info("[AUDIO] Cleanup completed")
    
    def __del__(self):
        """Destructor to ensure cleanup when object is destroyed."""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction