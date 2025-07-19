# 🛠️ Development Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Code Standards](#code-standards)
4. [Testing](#testing)
5. [Debugging](#debugging)
6. [Performance](#performance)
7. [Contributing](#contributing)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (recommended: 3.10+)
- **Git** for version control
- **Virtual environment** support
- **Audio device** with microphone access

### System Dependencies

#### Windows
```bash
# Install Microsoft Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Audio system requirements
# Ensure microphone permissions are granted
```

#### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    portaudio19-dev \
    python3-dev \
    python3-venv \
    build-essential

# For X11 keyboard hooks
sudo apt-get install -y \
    xorg-dev \
    libx11-dev
```

#### macOS
```bash
# Install Homebrew dependencies
brew install portaudio

# Grant accessibility permissions
# System Preferences → Security & Privacy → Accessibility
# Add Terminal and your IDE
```

### Quick Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd dictationer

# 2. Create virtual environment
python -m venv venv_linux
source venv_linux/bin/activate  # Linux/macOS
# or venv_linux\Scripts\activate  # Windows

# 3. Install in development mode
pip install -e .[dev]

# 4. Verify installation
python -m pytest --version
python -c "import dictationer; print('✓ Installation successful')"
```

---

## 🔧 Development Environment

### IDE Configuration

#### VS Code (Recommended)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv_linux/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".mypy_cache": true,
        ".pytest_cache": true,
        "outputs/": true,
        "logs/": true
    }
}
```

#### PyCharm
```yaml
# Configure in Settings → Project → Python Interpreter
# Set to: ./venv_linux/bin/python

# Code Style → Python
# Set line length: 88
# Enable Black formatting

# Tools → Python Integrated Tools
# Default test runner: pytest
```

### Environment Variables

```bash
# Development configuration
export DICTATIONER_DEV_MODE=true
export DICTATIONER_LOG_LEVEL=DEBUG
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Testing configuration
export PYTEST_CURRENT_TEST=true
export TESTING_MODE=true

# Optional: Model configuration
export WHISPER_MODEL_SIZE=tiny  # Faster testing
export WHISPER_CACHE_DIR=/tmp/whisper_cache
```

### Directory Structure Setup

```bash
# Ensure required directories exist
mkdir -p logs outputs tests/fixtures docs examples

# Set up git hooks (optional)
pre-commit install  # If using pre-commit
```

---

## 📏 Code Standards

### Code Quality Tools

#### Black (Code Formatting)
```bash
# Format all code
black src/ tests/ *.py

# Check formatting without changes
black --check src/ tests/

# Configuration in pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
```

#### MyPy (Type Checking)
```bash
# Type check all code
mypy src/

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
disallow_untyped_defs = true
```

#### Flake8 (Linting)
```bash
# Lint all code
flake8 src/ tests/

# Configuration in .flake8 or pyproject.toml
[flake8]
max-line-length = 88
extend-ignore = E203, W503
```

### Coding Conventions

#### Function Design
```python
def well_designed_function(
    required_param: str,
    optional_param: Optional[int] = None,
    *args: Any,
    **kwargs: Any
) -> Tuple[bool, str]:
    """
    Example of well-designed function following project standards.
    
    Args:
        required_param: Description of required parameter
        optional_param: Description of optional parameter
        *args: Variable positional arguments
        **kwargs: Variable keyword arguments
    
    Returns:
        Tuple containing success status and result message
        
    Raises:
        ValueError: When required_param is empty
        TypeError: When optional_param is negative
    """
    if not required_param:
        raise ValueError("Required parameter cannot be empty")
    
    if optional_param is not None and optional_param < 0:
        raise TypeError("Optional parameter must be non-negative")
    
    # Implementation here
    return True, "Success"
```

#### Class Design
```python
class ExampleComponent:
    """
    Example component following project architecture patterns.
    
    This class demonstrates the standard patterns used throughout
    the dictationer codebase including:
    - Proper initialization
    - Thread-safe operations
    - Comprehensive logging
    - Graceful cleanup
    
    Attributes:
        name: Component name for identification
        is_active: Whether the component is currently active
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the component with configuration."""
        self.name = name
        self.is_active = False
        self._config = config or {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.logger.info(f"Initialized {self.name}")
    
    def start(self) -> bool:
        """Start the component operations."""
        with self._lock:
            if self.is_active:
                self.logger.warning(f"{self.name} already active")
                return False
            
            try:
                # Component-specific startup logic
                self.is_active = True
                self.logger.info(f"{self.name} started successfully")
                return True
            except Exception as e:
                self.logger.error(f"Failed to start {self.name}: {e}")
                return False
    
    def stop(self) -> None:
        """Stop the component operations gracefully."""
        with self._lock:
            if not self.is_active:
                return
            
            try:
                # Component-specific cleanup logic
                self.is_active = False
                self.logger.info(f"{self.name} stopped successfully")
            except Exception as e:
                self.logger.error(f"Error stopping {self.name}: {e}")
```

#### Error Handling Patterns
```python
# Pattern 1: Specific exception handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    return None
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise

# Pattern 2: Resource cleanup
resource = None
try:
    resource = acquire_resource()
    result = use_resource(resource)
    return result
except Exception as e:
    logger.error(f"Resource operation failed: {e}")
    raise
finally:
    if resource:
        release_resource(resource)

# Pattern 3: Graceful degradation
def feature_with_fallback():
    try:
        return advanced_feature()
    except AdvancedFeatureError:
        logger.warning("Advanced feature unavailable, using fallback")
        return basic_feature()
```

---

## 🧪 Testing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_main.py             # RecordingController tests
├── test_audio.py            # AudioRecorder tests
├── test_keyboard.py         # KeyboardRecorder tests
├── test_processor.py        # AudioProcessor tests
├── test_paster.py           # ClipboardPaster tests
├── integration/             # Integration tests
│   ├── test_full_workflow.py
│   └── test_component_interaction.py
├── fixtures/                # Test data and mock files
│   ├── audio/
│   │   ├── test_recording.wav
│   │   └── empty_file.wav
│   └── configs/
│       └── test_config.json
└── utils/                   # Test utilities
    ├── helpers.py
    └── mocks.py
```

### Writing Tests

#### Basic Test Pattern
```python
import pytest
from unittest.mock import Mock, patch
from dictationer.audio import AudioRecorder

class TestAudioRecorder:
    """Test suite for AudioRecorder class."""
    
    def test_initialization_with_defaults(self):
        """Test AudioRecorder initialization with default parameters."""
        recorder = AudioRecorder()
        assert recorder.output_file == "recording.wav"
        assert recorder.sample_rate == 16000
        assert recorder.channels == 1
        assert not recorder.is_recording()
    
    def test_initialization_with_custom_params(self):
        """Test AudioRecorder initialization with custom parameters."""
        recorder = AudioRecorder(
            output_file="custom.wav",
            enable_transcription=False
        )
        assert recorder.output_file == "custom.wav"
        assert not recorder.enable_transcription
    
    @patch('dictationer.audio.pyaudio.PyAudio')
    def test_start_recording_success(self, mock_pyaudio):
        """Test successful recording start."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        assert recorder.is_recording()
        mock_pyaudio.assert_called_once()
    
    def test_start_recording_already_active(self):
        """Test starting recording when already recording."""
        recorder = AudioRecorder()
        recorder._recording = True  # Simulate active recording
        
        recorder.start_recording()
        # Should handle gracefully without error
    
    @pytest.mark.asyncio
    async def test_async_recording_workflow(self):
        """Test asynchronous recording workflow."""
        recorder = AudioRecorder()
        
        # Start recording
        recorder.start_recording()
        await asyncio.sleep(0.1)  # Simulate short recording
        
        # Stop recording
        recorder.stop_recording()
        assert not recorder.is_recording()
```

#### Integration Test Pattern
```python
class TestFullWorkflow:
    """Integration tests for complete recording workflow."""
    
    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory for tests."""
        output_dir = tmp_path / "test_outputs"
        output_dir.mkdir()
        return output_dir
    
    def test_complete_recording_and_transcription(self, temp_output_dir):
        """Test complete workflow from recording to transcription."""
        output_file = temp_output_dir / "test_recording.wav"
        
        controller = RecordingController(
            output_file=str(output_file),
            enable_transcription=True,
            model_size="tiny"  # Fastest for testing
        )
        
        # Simulate recording workflow
        controller.audio.start_recording()
        time.sleep(0.5)  # Short recording
        controller.audio.stop_recording()
        
        # Verify file creation
        assert output_file.exists()
        assert output_file.stat().st_size > 0
```

#### Mock and Fixture Patterns
```python
# conftest.py
@pytest.fixture
def mock_audio_device():
    """Mock PyAudio device for testing without real audio hardware."""
    with patch('pyaudio.PyAudio') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        mock_instance.open.return_value = Mock()
        yield mock_instance

@pytest.fixture
def sample_audio_data():
    """Provide sample audio data for testing."""
    # Generate 1 second of silent audio data
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    return b'\x00\x00' * samples

@pytest.fixture
def test_recording_file(tmp_path, sample_audio_data):
    """Create a test WAV file."""
    test_file = tmp_path / "test.wav"
    
    import wave
    with wave.open(str(test_file), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(sample_audio_data)
    
    return test_file
```

### Running Tests

#### Basic Test Commands
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_audio.py

# Run specific test function
pytest tests/test_audio.py::TestAudioRecorder::test_initialization

# Run tests matching pattern
pytest -k "test_recording"
```

#### Coverage Analysis
```bash
# Run tests with coverage
pytest --cov=src/dictationer

# Generate HTML coverage report
pytest --cov=src/dictationer --cov-report=html

# Generate XML coverage report (for CI)
pytest --cov=src/dictationer --cov-report=xml

# Check coverage threshold
pytest --cov=src/dictationer --cov-fail-under=80
```

#### Performance Testing
```bash
# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Profile test execution
pytest --profile --profile-svg

# Memory usage testing
pytest --memory-profiler
```

### Test Categories

#### Unit Tests
- Test individual functions and methods
- Use mocks for external dependencies
- Fast execution (< 1 second each)
- High coverage of edge cases

#### Integration Tests
- Test component interactions
- Use real dependencies where safe
- Moderate execution time (< 10 seconds each)
- Focus on workflow validation

#### System Tests
- Test complete user scenarios
- Use real audio hardware (when available)
- Longer execution time (< 60 seconds each)
- End-to-end validation

---

## 🐛 Debugging

### Logging Configuration

#### Development Logging Setup
```python
import logging

# Configure comprehensive logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)

# Enable specific logger debugging
logging.getLogger('dictationer.audio').setLevel(logging.DEBUG)
logging.getLogger('dictationer.processor').setLevel(logging.DEBUG)
```

#### Interactive Debugging
```python
# Add breakpoints for debugging
import pdb; pdb.set_trace()

# Or use IPython debugger
import ipdb; ipdb.set_trace()

# Add conditional breakpoints
if some_condition:
    import pdb; pdb.set_trace()
```

### Common Issues and Solutions

#### Audio Device Problems
```python
# Debug audio device availability
import pyaudio

def debug_audio_devices():
    p = pyaudio.PyAudio()
    print(f"Available audio devices: {p.get_device_count()}")
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"Device {i}: {info['name']} - Inputs: {info['maxInputChannels']}")
    
    try:
        default_input = p.get_default_input_device_info()
        print(f"Default input device: {default_input['name']}")
    except OSError as e:
        print(f"No default input device: {e}")
    
    p.terminate()

debug_audio_devices()
```

#### Keyboard Hook Issues
```python
# Debug keyboard hook registration
import keyboard

def debug_keyboard_hooks():
    try:
        # Test simple key detection
        print("Testing keyboard access...")
        keyboard.add_hotkey('ctrl+shift+t', lambda: print("Test hotkey works!"))
        print("Keyboard hooks working correctly")
    except Exception as e:
        print(f"Keyboard hook error: {e}")
        print("Try running as administrator (Windows) or check permissions")

debug_keyboard_hooks()
```

#### Threading Issues
```python
# Debug thread states and locks
import threading

def debug_threading_state(component):
    """Debug threading state for any component."""
    print(f"Active threads: {threading.active_count()}")
    for thread in threading.enumerate():
        print(f"  {thread.name}: {'alive' if thread.is_alive() else 'dead'}")
    
    if hasattr(component, '_thread_lock'):
        print(f"Component lock acquired: {component._thread_lock.locked()}")
```

### Performance Debugging

#### Memory Usage Monitoring
```python
import psutil
import tracemalloc

def monitor_memory_usage():
    """Monitor memory usage during development."""
    process = psutil.Process()
    
    print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    print(f"CPU usage: {process.cpu_percent()}%")
    
    # Detailed memory tracking
    tracemalloc.start()
    # ... run code ...
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    tracemalloc.stop()
```

#### Performance Profiling
```python
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    """Profile a specific function's performance."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
    
    return result
```

---

## ⚡ Performance

### Optimization Guidelines

#### Audio Processing
```python
# Optimize audio chunk size for your system
optimal_chunk_size = 1024  # Start with this
# Experiment with: 512, 1024, 2048, 4096

# Use appropriate audio format
audio_format = pyaudio.paInt16  # 16-bit is usually optimal

# Consider buffer management
max_buffer_size = 100  # frames
if len(frames_buffer) > max_buffer_size:
    frames_buffer = frames_buffer[-max_buffer_size:]
```

#### Transcription Performance
```python
# Choose appropriate Whisper model for your needs
model_performance = {
    'tiny': {'speed': 'fastest', 'accuracy': 'lowest', 'memory': '~39MB'},
    'base': {'speed': 'fast', 'accuracy': 'good', 'memory': '~74MB'},
    'small': {'speed': 'medium', 'accuracy': 'better', 'memory': '~244MB'},
    'medium': {'speed': 'slow', 'accuracy': 'high', 'memory': '~769MB'},
    'large-v3': {'speed': 'slowest', 'accuracy': 'highest', 'memory': '~1550MB'}
}

# Use CPU vs GPU based on availability
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"
```

#### Threading Optimization
```python
# Use appropriate thread counts
import os
max_threads = min(4, os.cpu_count())  # Don't oversubscribe

# Optimize sleep intervals
monitoring_interval = 0.1  # 100ms for responsive monitoring
status_interval = 2.0      # 2s for status updates
```

### Benchmarking

#### Create Performance Benchmarks
```python
import time
import statistics

def benchmark_recording_performance():
    """Benchmark audio recording performance."""
    durations = []
    
    for i in range(10):
        recorder = AudioRecorder()
        
        start_time = time.time()
        recorder.start_recording()
        time.sleep(1.0)  # 1 second recording
        recorder.stop_recording()
        end_time = time.time()
        
        durations.append(end_time - start_time)
    
    print(f"Average recording time: {statistics.mean(durations):.3f}s")
    print(f"Standard deviation: {statistics.stdev(durations):.3f}s")

def benchmark_transcription_performance():
    """Benchmark transcription performance."""
    processor = AudioProcessor(model_size="base")
    
    start_time = time.time()
    result = processor.transcribe_file("test_audio.wav")
    end_time = time.time()
    
    print(f"Transcription time: {end_time - start_time:.3f}s")
    print(f"Result length: {len(result) if result else 0} characters")
```

---

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/dictationer.git
   cd dictationer
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up Development Environment**
   ```bash
   python -m venv venv_linux
   source venv_linux/bin/activate
   pip install -e .[dev]
   ```

4. **Make Changes**
   - Follow code standards
   - Add comprehensive tests
   - Update documentation

5. **Run Quality Checks**
   ```bash
   # Format code
   black src/ tests/
   
   # Type checking
   mypy src/
   
   # Linting
   flake8 src/ tests/
   
   # Run tests
   pytest --cov=src/dictationer
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

7. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Code Review Guidelines

#### For Authors
- Write clear commit messages
- Include tests for new functionality
- Update documentation
- Ensure all checks pass
- Respond to feedback promptly

#### For Reviewers
- Check code functionality and design
- Verify test coverage
- Review documentation updates
- Test locally when possible
- Provide constructive feedback

### Release Process

1. **Update Version**
   ```python
   # src/dictationer/__init__.py
   __version__ = "1.1.0"
   ```

2. **Update Changelog**
   ```markdown
   ## Version 1.1.0 (2025-XX-XX)
   - Added new feature X
   - Fixed bug Y
   - Improved performance of Z
   ```

3. **Create Release**
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

4. **Build and Publish**
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

---

**Last Updated**: 2025-07-19  
**Document Version**: 1.0  
**Next Review**: 2025-08-19