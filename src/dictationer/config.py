"""
Configuration management module for Dictationer.

This module handles application settings, GPU/CPU detection,
and configuration persistence for the GUI interface.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

try:
    import torch
    TORCH_AVAILABLE = True
    # Debug: Print torch info when imported
    import sys
    print(f"[DEBUG] Using Python from: {sys.executable}")
    print(f"[DEBUG] PyTorch version: {torch.__version__}")
    print(f"[DEBUG] PyTorch location: {torch.__file__}")
    print(f"[DEBUG] CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[DEBUG] CUDA version: {torch.version.cuda}")
        print(f"[DEBUG] GPU count: {torch.cuda.device_count()}")
except ImportError as e:
    TORCH_AVAILABLE = False
    torch = None
    import sys
    print(f"[DEBUG] Using Python from: {sys.executable}")
    print(f"[ERROR] PyTorch not available: {e}")

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None


class DeviceDetector:
    """
    Device detection utility for GPU/CPU selection.
    
    Provides methods to detect available hardware and determine
    the best device for processing tasks.
    """
    
    @staticmethod
    def detect_gpu() -> bool:
        """
        Detect if GPU is available for processing.
        
        Returns:
            bool: True if GPU is available and functional, False otherwise.
        """
        if not TORCH_AVAILABLE:
            return False
            
        try:
            if torch.cuda.is_available():
                # Test basic GPU functionality
                device = torch.device('cuda')
                test_tensor = torch.tensor([1.0], device=device)
                return True
        except Exception:
            pass
            
        return False
    
    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        """
        Get detailed GPU information.
        
        Returns:
            Dict[str, Any]: GPU information including name, memory, etc.
        """
        info = {
            "available": False,
            "device_count": 0,
            "devices": []
        }
        
        if not TORCH_AVAILABLE:
            return info
            
        try:
            if torch.cuda.is_available():
                info["available"] = True
                info["device_count"] = torch.cuda.device_count()
                
                for i in range(info["device_count"]):
                    device_info = {
                        "index": i,
                        "name": torch.cuda.get_device_name(i),
                        "memory_total": torch.cuda.get_device_properties(i).total_memory,
                        "memory_reserved": torch.cuda.memory_reserved(i),
                        "memory_allocated": torch.cuda.memory_allocated(i)
                    }
                    info["devices"].append(device_info)
        except Exception as e:
            logging.warning(f"Error getting GPU info: {e}")
            
        return info


class ConfigManager:
    """
    Application configuration manager.
    
    Handles loading, saving, and managing application settings
    with support for environment variables and persistent storage.
    """
    
    DEFAULT_CONFIG = {
        "device_preference": "auto",  # auto, cpu, gpu
        "whisper_model_size": "base",
        "hotkey": "ctrl+win+shift+l",
        "output_directory": "outputs",
        "enable_transcription": True,
        "auto_paste": True,
        "log_level": "INFO"
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file (str, optional): Path to configuration file.
                                       Defaults to 'config/settings.json'.
        """
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Set config file path
        if config_file is None:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "settings.json"
        
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load existing configuration
        self.load_config()
        
        # Override with environment variables
        self._load_env_overrides()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict[str, Any]: Loaded configuration dictionary.
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                    self.logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        else:
            self.logger.info("No config file found, using defaults")
            
        return self.config
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key (str): Configuration key.
            default (Any): Default value if key not found.
            
        Returns:
            Any: Configuration value.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key (str): Configuration key.
            value (Any): Value to set.
        """
        self.config[key] = value
        self.logger.debug(f"Config updated: {key} = {value}")
    
    def get_device_config(self) -> Dict[str, Any]:
        """
        Get device configuration with detection results.
        
        Returns:
            Dict[str, Any]: Device configuration including detection results.
        """
        device_info = DeviceDetector.get_gpu_info()
        preference = self.get("device_preference", "auto")
        
        # Determine actual device to use
        if preference == "auto":
            use_gpu = device_info["available"]
        elif preference == "gpu":
            use_gpu = device_info["available"]
        else:
            use_gpu = False
        
        return {
            "preference": preference,
            "gpu_available": device_info["available"],
            "gpu_info": device_info,
            "use_gpu": use_gpu,
            "device": "cuda" if use_gpu else "cpu"
        }
    
    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mapping = {
            "DICTATIONER_HOTKEY": "hotkey",
            "WHISPER_MODEL_SIZE": "whisper_model_size",
            "OUTPUT_DIRECTORY": "output_directory",
            "DEVICE_PREFERENCE": "device_preference",
            "LOG_LEVEL": "log_level"
        }
        
        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Convert boolean strings
                if env_value.lower() in ('true', 'false'):
                    env_value = env_value.lower() == 'true'
                
                self.config[config_key] = env_value
                self.logger.debug(f"Config override from env: {config_key} = {env_value}")


def get_default_config() -> ConfigManager:
    """
    Get default configuration manager instance.
    
    Returns:
        ConfigManager: Default configuration manager.
    """
    return ConfigManager()


class ModelDetector:
    """
    Model detection utility for Whisper models.
    
    Provides methods to detect cached models and available downloadable models.
    """
    
    # Standard Whisper model sizes (supported by faster-whisper)
    STANDARD_MODELS = [
        "tiny", "tiny.en", "base", "base.en", "small", "small.en", 
        "medium", "medium.en", "large", "large-v1", "large-v2", "large-v3",
        "distil-small.en", "distil-medium.en", "distil-large-v2", "distil-large-v3"
    ]
    
    # Recommended downloadable models
    DOWNLOADABLE_MODELS = [
        {
            "name": "openai/whisper-large-v3-turbo",
            "display_name": "Whisper Large V3 Turbo",
            "url": "https://huggingface.co/openai/whisper-large-v3-turbo",
            "description": "Latest OpenAI Whisper model - fastest large model",
            "type": "huggingface"
        },
        {
            "name": "distil-whisper/distil-large-v3", 
            "display_name": "Distil Whisper Large V3",
            "url": "https://huggingface.co/distil-whisper/distil-large-v3",
            "description": "Distilled version - faster inference, good quality",
            "type": "huggingface"
        }
    ]
    
    @staticmethod
    def get_cached_models() -> list:
        """
        Get list of cached Whisper models by checking the HuggingFace cache directory.
        
        Returns:
            list: List of cached model names.
        """
        cached_models = []
        
        try:
            import os
            from pathlib import Path
            
            # Check HuggingFace cache directory
            cache_dir = os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")
            model_path = Path(cache_dir) / "hub"
            
            if not model_path.exists():
                return cached_models
            
            # Search for model directories
            for item in model_path.iterdir():
                if not item.is_dir():
                    continue
                
                dir_name = item.name
                
                # Handle HuggingFace cache format: models--org--model-name
                if "models--" in dir_name and "whisper" in dir_name.lower():
                    # Extract model name from cache directory
                    parts = dir_name.replace("models--", "").split("--")
                    if len(parts) >= 2:
                        model_name = "/".join(parts)
                        
                        # Check if the model has actual files (not just refs)
                        snapshots_dir = item / "snapshots"
                        if snapshots_dir.exists() and any(snapshots_dir.iterdir()):
                            cached_models.append(model_name)
                
                # Also check for standard model names that might be cached differently
                elif any(std_model in dir_name.lower() for std_model in ModelDetector.STANDARD_MODELS):
                    for std_model in ModelDetector.STANDARD_MODELS:
                        if std_model in dir_name.lower() and std_model not in cached_models:
                            # Verify it has actual content
                            snapshots_dir = item / "snapshots"
                            if snapshots_dir.exists() and any(snapshots_dir.iterdir()):
                                cached_models.append(std_model)
                                break
        
        except Exception as e:
            # If there's any error checking cache, just return what we have
            pass
        
        return sorted(list(set(cached_models)))  # Remove duplicates and sort
    
    @staticmethod
    def get_downloadable_models() -> list:
        """
        Get list of recommended downloadable models.
        
        Returns:
            list: List of downloadable model info dictionaries.
        """
        return ModelDetector.DOWNLOADABLE_MODELS.copy()
    
    @staticmethod
    def is_model_cached(model_name: str) -> bool:
        """
        Check if a specific model is cached.
        
        Args:
            model_name (str): Name of the model to check.
            
        Returns:
            bool: True if model is cached, False otherwise.
        """
        cached_models = ModelDetector.get_cached_models()
        return model_name in cached_models


def detect_optimal_device() -> str:
    """
    Detect optimal device for processing.
    
    Returns:
        str: Optimal device ('cuda' or 'cpu').
    """
    if DeviceDetector.detect_gpu():
        return "cuda"
    return "cpu"