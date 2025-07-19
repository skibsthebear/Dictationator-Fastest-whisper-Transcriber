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
import subprocess
import sys
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

# Import status indicator
try:
    from .status_indicator import show_transcribing, hide_indicator
    STATUS_INDICATOR_AVAILABLE = True
except ImportError:
    STATUS_INDICATOR_AVAILABLE = False

# Import device configuration system
try:
    from .config import ConfigManager, DeviceDetector
    CONFIG_AVAILABLE = True
except ImportError as e:
    CONFIG_AVAILABLE = False
    _config_import_error = str(e)


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
    
    def __init__(self, model_size: str = "base", watch_directory: str = "outputs", auto_paste: bool = True, enable_file_monitoring: bool = True):
        """
        Initialize the audio processor.
        
        Args:
            model_size: Size of the Whisper model to use (tiny, base, small, medium, large).
            watch_directory: Directory to monitor for new audio files.
            auto_paste: Whether to automatically paste transcribed text to clipboard.
            enable_file_monitoring: Whether to enable file system monitoring (default: True).
        """
        # Store original model name for cache checking and type detection
        self.original_model_size = model_size
        self.model_size = model_size  # Will be normalized later during loading
            
        self.watch_directory = Path(watch_directory)
        self.auto_paste = auto_paste
        self.enable_file_monitoring = enable_file_monitoring
        
        if not hasattr(self, 'logger'):
            self.logger = self._setup_logging()
        
        self.logger.info(f"[PROCESSOR] Initializing AudioProcessor")
        self.logger.info(f"[PROCESSOR] Model size: {self.original_model_size}")
        self.logger.info(f"[PROCESSOR] Watch directory: {watch_directory}")
        self.logger.info(f"[PROCESSOR] Auto-paste enabled: {auto_paste}")
        self.logger.info(f"[PROCESSOR] File monitoring enabled: {enable_file_monitoring}")
        
        # Initialize device configuration
        self.device_config = None
        if CONFIG_AVAILABLE:
            try:
                config_manager = ConfigManager()
                self.device_config = config_manager.get_device_config()
                self.logger.info(f"[PROCESSOR] Device configuration loaded:")
                self.logger.info(f"[PROCESSOR] - Preference: {self.device_config['preference']}")
                self.logger.info(f"[PROCESSOR] - GPU Available: {self.device_config['gpu_available']}")
                self.logger.info(f"[PROCESSOR] - Use GPU: {self.device_config['use_gpu']}")
                self.logger.info(f"[PROCESSOR] - Device: {self.device_config['device']}")
                if self.device_config['gpu_available']:
                    gpu_info = self.device_config['gpu_info']
                    self.logger.info(f"[PROCESSOR] - GPU Count: {gpu_info['device_count']}")
                    for i, device in enumerate(gpu_info['devices']):
                        self.logger.info(f"[PROCESSOR] - GPU {i}: {device['name']}")
            except Exception as e:
                self.logger.warning(f"[PROCESSOR] Failed to load device configuration: {e}")
                self.device_config = {"use_gpu": False, "device": "cpu", "preference": "cpu"}
        else:
            self.logger.warning(f"[PROCESSOR] Device configuration not available: {_config_import_error}")
            self.device_config = {"use_gpu": False, "device": "cpu", "preference": "cpu"}
        
        # Check if model is cached (for HF models) - use original model name
        if "/" in self.original_model_size:
            try:
                from .config import ModelDetector
                is_cached = ModelDetector.is_model_cached(self.original_model_size)
                self.logger.info(f"[PROCESSOR] HuggingFace model cached: {is_cached}")
                if not is_cached:
                    self.logger.warning(f"[PROCESSOR] Model '{self.original_model_size}' may not be downloaded")
                    self.logger.warning(f"[PROCESSOR] Download model via GUI or use 'base' model instead")
            except ImportError:
                self.logger.warning("[PROCESSOR] ModelDetector not available for cache check")
        
        # Initialize faster-whisper model with enhanced loading
        try:
            self._load_whisper_model(self.original_model_size, self.device_config)
        except Exception as e:
            import traceback
            
            self.logger.error(f"[PROCESSOR] Model loading failed completely: {e}")
            self.logger.error(f"[PROCESSOR] Error type: {type(e).__name__}")
            self.logger.error(f"[PROCESSOR] Full traceback: {traceback.format_exc()}")
            
            # Check for specific error types and provide better messages
            if "charmap" in str(e) or "codec" in str(e) or "unicode" in str(e).lower():
                error_msg = f"Unicode encoding error loading model '{self.original_model_size}'. This is typically caused by emoji characters in model names. Use GUI instead of command line, or set PYTHONIOENCODING=utf-8"
                self.logger.error(f"[PROCESSOR] {error_msg}")
                raise Exception(error_msg)
            else:
                raise Exception(f"Failed to load Whisper model '{self.original_model_size}': {str(e)}")
        
        # Set up file monitoring (only if enabled)
        if self.enable_file_monitoring:
            self.observer = Observer()
            self.file_handler = AudioFileHandler(self)
            self._monitoring = False
        else:
            self.observer = None
            self.file_handler = None
            self._monitoring = False
            self.logger.info("[PROCESSOR] File monitoring disabled - using direct transcription mode only")
        
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
    
    def _convert_huggingface_model(self, model_name: str) -> Optional[str]:
        """
        Convert HuggingFace PyTorch model to CTranslate2 format for faster-whisper compatibility.
        
        Args:
            model_name: HuggingFace model name (e.g., "distil-whisper/distil-large-v3")
            
        Returns:
            Path to converted model directory, or None if conversion failed
        """
        self.logger.info(f"[PROCESSOR] Starting model conversion for: {model_name}")
        
        try:
            # Import required libraries for conversion
            try:
                import transformers
                from huggingface_hub import snapshot_download
                self.logger.info("[PROCESSOR] HuggingFace libraries available for conversion")
            except ImportError as e:
                self.logger.error(f"[PROCESSOR] Missing required libraries for conversion: {e}")
                self.logger.error("[PROCESSOR] Install with: pip install transformers huggingface_hub")
                return None
            
            # Check if ct2-transformers-converter is available
            try:
                result = subprocess.run([sys.executable, "-c", "import ctranslate2"],
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error("[PROCESSOR] CTranslate2 not available for conversion")
                    self.logger.error("[PROCESSOR] Install with: pip install ctranslate2")
                    return None
                self.logger.info("[PROCESSOR] CTranslate2 available for conversion")
            except Exception as e:
                self.logger.error(f"[PROCESSOR] Error checking CTranslate2: {e}")
                return None
            
            # Get HuggingFace cache directory
            from huggingface_hub import HfFolder
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            
            # Find the model directory
            model_dir_name = f"models--{model_name.replace('/', '--')}"
            model_cache_dir = Path(cache_dir) / model_dir_name
            
            if not model_cache_dir.exists():
                self.logger.error(f"[PROCESSOR] Model cache directory not found: {model_cache_dir}")
                return None
            
            # Find the snapshot directory (latest version)
            snapshots_dir = model_cache_dir / "snapshots"
            if not snapshots_dir.exists():
                self.logger.error(f"[PROCESSOR] Snapshots directory not found: {snapshots_dir}")
                return None
            
            # Get the latest snapshot
            snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
            if not snapshot_dirs:
                self.logger.error(f"[PROCESSOR] No snapshots found in: {snapshots_dir}")
                return None
            
            # Use the most recent snapshot
            latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
            self.logger.info(f"[PROCESSOR] Using snapshot: {latest_snapshot}")
            
            # Check if model.bin exists (CTranslate2 format)
            model_bin_path = latest_snapshot / "model.bin"
            if model_bin_path.exists():
                self.logger.info(f"[PROCESSOR] Model already in CTranslate2 format: {latest_snapshot}")
                return str(latest_snapshot)
            
            # Check if PyTorch model files exist
            pytorch_files = list(latest_snapshot.glob("*.bin")) + list(latest_snapshot.glob("*.safetensors"))
            if not pytorch_files:
                self.logger.error(f"[PROCESSOR] No PyTorch model files found in: {latest_snapshot}")
                return None
            
            self.logger.info(f"[PROCESSOR] Found PyTorch model files: {[f.name for f in pytorch_files]}")
            
            # Create conversion output directory
            converted_dir = latest_snapshot / "ct2_converted"
            if converted_dir.exists() and (converted_dir / "model.bin").exists():
                self.logger.info(f"[PROCESSOR] Using existing converted model: {converted_dir}")
                return str(converted_dir)
            
            # If directory exists but model.bin doesn't, we need to clean and reconvert
            if converted_dir.exists():
                self.logger.info(f"[PROCESSOR] Cleaning incomplete conversion directory: {converted_dir}")
                import shutil
                shutil.rmtree(converted_dir)
            
            converted_dir.mkdir(exist_ok=True)
            self.logger.info(f"[PROCESSOR] Created clean conversion directory: {converted_dir}")
            
            # Run the conversion using ct2-transformers-converter
            self.logger.info("[PROCESSOR] Starting model conversion process...")
            
            conversion_cmd = [
                "ct2-transformers-converter",
                "--model", str(latest_snapshot),
                "--output_dir", str(converted_dir),
                "--copy_files", "tokenizer.json", "preprocessor_config.json",
                "--quantization", "float16",
                "--force"
            ]
            
            self.logger.info(f"[PROCESSOR] Running conversion command: {' '.join(conversion_cmd)}")
            
            # Run conversion with timeout
            result = subprocess.run(
                conversion_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(latest_snapshot)
            )
            
            if result.returncode == 0:
                self.logger.info("[PROCESSOR] Model conversion completed successfully")
                self.logger.info(f"[PROCESSOR] Conversion output: {result.stdout}")
                
                # Verify the converted model has the required files
                if (converted_dir / "model.bin").exists():
                    self.logger.info(f"[PROCESSOR] Converted model ready: {converted_dir}")
                    return str(converted_dir)
                else:
                    self.logger.error("[PROCESSOR] Conversion completed but model.bin not found")
                    return None
            else:
                self.logger.error(f"[PROCESSOR] Model conversion failed: {result.stderr}")
                self.logger.error(f"[PROCESSOR] Conversion stdout: {result.stdout}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("[PROCESSOR] Model conversion timed out after 5 minutes")
            return None
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Error during model conversion: {e}")
            import traceback
            self.logger.error(f"[PROCESSOR] Conversion traceback: {traceback.format_exc()}")
            return None

    def _load_whisper_model(self, model_size: str, device_config: dict):
        """Load Whisper model with GPU/CUDA support and proper parameters based on model type."""
        # Store original model name for type detection and cache checking
        original_model_name = model_size
        
        self.logger.info(f"[PROCESSOR] Loading Whisper model: {original_model_name}")
        self.logger.info(f"[PROCESSOR] Device config: {device_config}")
        
        # COMMENTED OUT: Original loading strategies (preserved for reference)
        # try:
        #     # Detect model type
        #     if "/" in model_size:
        #         # HuggingFace model (e.g., "distil-whisper/distil-large-v3.5")
        #         self.logger.info(f"[PROCESSOR] Detected HuggingFace model: {model_size}")
        #
        #         # Check if model is cached
        #         try:
        #             from .config import ModelDetector
        #             is_cached = ModelDetector.is_model_cached(model_size)
        #             self.logger.info(f"[PROCESSOR] HuggingFace model cached: {is_cached}")
        #             if not is_cached:
        #                 self.logger.warning(f"[PROCESSOR] Model '{model_size}' may not be downloaded")
        #         except ImportError:
        #             self.logger.warning("[PROCESSOR] ModelDetector not available for cache check")
        #
        #         # Try different loading strategies for HF models
        #         loading_strategies = [
        #             {"device": "cpu", "compute_type": "int8", "local_files_only": False},
        #             {"device": "cpu", "compute_type": "float32", "local_files_only": False},
        #             {"device": "cpu", "compute_type": "int8", "local_files_only": True},
        #             {"device": "cpu", "compute_type": "float32", "local_files_only": True},
        #         ]
        #
        #         last_error = None
        #         for i, strategy in enumerate(loading_strategies):
        #             try:
        #                 self.logger.info(f"[PROCESSOR] Trying loading strategy {i+1}: {strategy}")
        #                 self.model = WhisperModel(model_size, **strategy)
        #                 self.logger.info(f"[PROCESSOR] Successfully loaded with strategy {i+1}")
        #                 self._log_model_info()
        #                 return
        #             except Exception as e:
        #                 last_error = e
        #                 self.logger.warning(f"[PROCESSOR] Strategy {i+1} failed: {e}")
        #
        #         # If all strategies failed, raise the last error
        #         if last_error:
        #             raise last_error
        #
        #     else:
        #         # Standard faster-whisper model (e.g., "base", "large")
        #         self.logger.info(f"[PROCESSOR] Detected standard model: {model_size}")
        #         self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        #         self.logger.info(f"[PROCESSOR] Standard model loaded successfully")
        #         self._log_model_info()
        
        # NEW GPU-AWARE LOADING IMPLEMENTATION
        try:
            # Determine device and compute type based on configuration
            use_gpu = device_config.get("use_gpu", False) if device_config else False
            device = device_config.get("device", "cpu") if device_config else "cpu"
            
            self.logger.info(f"[PROCESSOR] GPU-aware loading - Use GPU: {use_gpu}, Device: {device}")
            
            # Detect model type using original model name (before normalization)
            if "/" in original_model_name:
                # HuggingFace model (e.g., "distil-whisper/distil-large-v3")
                self.logger.info(f"[PROCESSOR] Detected HuggingFace model: {original_model_name}")
                
                # Check if model is cached using original name
                try:
                    from .config import ModelDetector
                    is_cached = ModelDetector.is_model_cached(original_model_name)
                    self.logger.info(f"[PROCESSOR] HuggingFace model cached: {is_cached}")
                    if not is_cached:
                        self.logger.warning(f"[PROCESSOR] Model '{original_model_name}' may not be downloaded")
                except ImportError:
                    self.logger.warning("[PROCESSOR] ModelDetector not available for cache check")
                
                # Use original model name directly - no normalization
                normalized_model_name = original_model_name
                self.logger.info(f"[PROCESSOR] Using exact model name for loading: '{original_model_name}'")
                
                # GPU-aware loading strategies for HuggingFace models
                if use_gpu and device == "cuda":
                    self.logger.info("[PROCESSOR] Attempting GPU loading with float16 precision")
                    loading_strategies = [
                        # GPU strategies with float16 for better performance
                        {"device": "cuda", "compute_type": "float16", "local_files_only": False},
                        {"device": "cuda", "compute_type": "float16", "local_files_only": True},
                        {"device": "cuda", "compute_type": "int8_float16", "local_files_only": False},
                        {"device": "cuda", "compute_type": "int8_float16", "local_files_only": True},
                        # Fallback to CPU if GPU fails
                        {"device": "cpu", "compute_type": "int8", "local_files_only": False},
                        {"device": "cpu", "compute_type": "float32", "local_files_only": False},
                        {"device": "cpu", "compute_type": "int8", "local_files_only": True},
                        {"device": "cpu", "compute_type": "float32", "local_files_only": True},
                    ]
                else:
                    self.logger.info("[PROCESSOR] Using CPU loading strategies")
                    loading_strategies = [
                        {"device": "cpu", "compute_type": "int8", "local_files_only": False},
                        {"device": "cpu", "compute_type": "float32", "local_files_only": False},
                        {"device": "cpu", "compute_type": "int8", "local_files_only": True},
                        {"device": "cpu", "compute_type": "float32", "local_files_only": True},
                    ]
                
                last_error = None
                model_to_load = original_model_name
                conversion_attempted = False
                
                for i, strategy in enumerate(loading_strategies):
                    try:
                        self.logger.info(f"[PROCESSOR] Trying loading strategy {i+1}: {strategy}")
                        self.model = WhisperModel(model_to_load, **strategy)
                        self.logger.info(f"[PROCESSOR] Successfully loaded with strategy {i+1}")
                        self._log_model_info()
                        return
                    except Exception as e:
                        last_error = e
                        self.logger.warning(f"[PROCESSOR] Strategy {i+1} failed: {e}")
                        
                        # Check if this is a model.bin missing error and we haven't tried conversion yet
                        if ("model.bin" in str(e) or "Unable to open file" in str(e)) and not conversion_attempted:
                            self.logger.info("[PROCESSOR] Detected missing model.bin - attempting model conversion")
                            converted_path = self._convert_huggingface_model(original_model_name)
                            if converted_path:
                                self.logger.info(f"[PROCESSOR] Model converted successfully, using: {converted_path}")
                                model_to_load = converted_path
                                conversion_attempted = True
                                # Retry this strategy with the converted model
                                try:
                                    self.logger.info(f"[PROCESSOR] Retrying strategy {i+1} with converted model")
                                    self.model = WhisperModel(model_to_load, **strategy)
                                    self.logger.info(f"[PROCESSOR] Successfully loaded converted model with strategy {i+1}")
                                    self._log_model_info()
                                    return
                                except Exception as retry_e:
                                    self.logger.warning(f"[PROCESSOR] Converted model also failed with strategy {i+1}: {retry_e}")
                                    last_error = retry_e
                            else:
                                self.logger.warning("[PROCESSOR] Model conversion failed, continuing with other strategies")
                                conversion_attempted = True
                        
                        # Log specific GPU-related errors
                        if "cuda" in str(e).lower() or "gpu" in str(e).lower():
                            self.logger.warning(f"[PROCESSOR] GPU-related error, will try CPU fallback")
                
                # If all strategies failed, raise the last error
                if last_error:
                    raise last_error
                    
            else:
                # Standard faster-whisper model (e.g., "base", "large")
                self.logger.info(f"[PROCESSOR] Detected standard model: {original_model_name}")
                
                # Use original model name directly - no normalization
                normalized_model_name = original_model_name
                self.logger.info(f"[PROCESSOR] Using exact model name for loading: '{original_model_name}'")
                
                if use_gpu and device == "cuda":
                    self.logger.info("[PROCESSOR] Loading standard model with GPU support")
                    try:
                        # Try GPU first with float16 for better performance
                        self.model = WhisperModel(original_model_name, device="cuda", compute_type="float16")
                        self.logger.info("[PROCESSOR] Standard model loaded successfully on GPU with float16")
                    except Exception as e:
                        self.logger.warning(f"[PROCESSOR] GPU loading failed, falling back to CPU: {e}")
                        # Fallback to CPU
                        self.model = WhisperModel(original_model_name, device="cpu", compute_type="int8")
                        self.logger.info("[PROCESSOR] Standard model loaded successfully on CPU (GPU fallback)")
                else:
                    self.logger.info("[PROCESSOR] Loading standard model on CPU")
                    self.model = WhisperModel(original_model_name, device="cpu", compute_type="int8")
                    self.logger.info("[PROCESSOR] Standard model loaded successfully on CPU")
                
                self._log_model_info()
                
        except Exception as e:
            self.logger.error(f"[PROCESSOR] Failed to load Whisper model '{original_model_name}': {e}")
            self.logger.error(f"[PROCESSOR] Error type: {type(e).__name__}")
            self.logger.error(f"[PROCESSOR] Detailed error: {str(e)}")
            
            # Try to provide helpful suggestions
            if "/" in original_model_name:
                self.logger.error(f"[PROCESSOR] HuggingFace model loading failed. Check if:")
                self.logger.error(f"[PROCESSOR] 1. Model exists: https://huggingface.co/{original_model_name}")
                self.logger.error(f"[PROCESSOR] 2. Model is compatible with faster-whisper")
                self.logger.error(f"[PROCESSOR] 3. Model was downloaded properly")
                self.logger.error(f"[PROCESSOR] 4. GPU drivers are properly installed (if using GPU)")
                self.logger.error(f"[PROCESSOR] 5. Try using a standard model like 'base' instead")
            else:
                self.logger.error(f"[PROCESSOR] Standard model loading failed")
                self.logger.error(f"[PROCESSOR] Try using 'base' model as fallback")
                if use_gpu:
                    self.logger.error(f"[PROCESSOR] GPU loading failed - check CUDA installation")
            
            raise
    
    def _log_model_info(self):
        """Log detailed model information for debugging."""
        try:
            if hasattr(self.model, 'model_size_or_path'):
                self.logger.info(f"[PROCESSOR] Model path/size: {self.model.model_size_or_path}")
            if hasattr(self.model, 'device'):
                self.logger.info(f"[PROCESSOR] Model device: {self.model.device}")
            if hasattr(self.model, 'compute_type'):
                self.logger.info(f"[PROCESSOR] Model compute type: {self.model.compute_type}")
            
            # Try to get model info
            if hasattr(self.model, 'model') and self.model.model:
                self.logger.info(f"[PROCESSOR] Model object type: {type(self.model.model)}")
            
        except Exception as e:
            self.logger.debug(f"[PROCESSOR] Could not log model info: {e}")
    
    def transcribe_file(self, file_path: str) -> Optional[str]:
        """
        Transcribe an audio file using faster-whisper.
        
        Args:
            file_path: Path to the audio file to transcribe.
            
        Returns:
            The transcribed text, or None if transcription failed.
        """
        self.logger.info(f"[PROCESSOR] Starting transcription: {file_path}")
        
        # Show transcribing indicator
        if STATUS_INDICATOR_AVAILABLE:
            try:
                show_transcribing()
                self.logger.info("[PROCESSOR] Transcribing indicator shown")
            except Exception as e:
                self.logger.error(f"[PROCESSOR] Failed to show transcribing indicator: {e}")
        
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
            
            # COMMENTED OUT: Original simple transcription call (preserved for reference)
            # segments, info = self.model.transcribe(file_path)
            
            # NEW: Enhanced transcription with Distil-Whisper parameters
            # These parameters are specifically optimized for Distil-Whisper models
            # but also work well with standard models
            self.logger.info(f"[PROCESSOR] Using enhanced transcription parameters:")
            self.logger.info(f"[PROCESSOR] - beam_size=5 (improved accuracy)")
            self.logger.info(f"[PROCESSOR] - language='en' (English optimization)")
            self.logger.info(f"[PROCESSOR] - condition_on_previous_text=False (better for distil models)")
            
            segments, info = self.model.transcribe(
                file_path,
                beam_size=5,
                language="en",
                condition_on_previous_text=False
            )
            
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
        finally:
            # Hide indicator when done
            if STATUS_INDICATOR_AVAILABLE:
                try:
                    hide_indicator()
                    self.logger.info("[PROCESSOR] Transcribing indicator hidden")
                except Exception as e:
                    self.logger.error(f"[PROCESSOR] Failed to hide transcribing indicator: {e}")
    
    def start_monitoring(self):
        """
        Start monitoring the watch directory for new audio files.
        """
        if not self.enable_file_monitoring:
            self.logger.warning("[PROCESSOR] File monitoring is disabled for this AudioProcessor instance")
            return
            
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
            print(f"Model: {self.original_model_size}")
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
        if not self.enable_file_monitoring or not self._monitoring:
            self.logger.info("[PROCESSOR] Monitoring not active or disabled")
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