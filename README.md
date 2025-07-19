# 🎤 Dictationer - Advanced Voice Recording & Transcription System

**Effortlessly capture and transcribe your thoughts with intelligent voice recording and powerful AI.**

<div align="center">
  <img src="logo.png" alt="Dictationer Logo" width="200" height="200">
</div>

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A professional voice recording system with **PySide6 GUI**, real-time transcription, intelligent hotkey control, and automatic text pasting. Features both command-line and graphical interfaces with robust threaded architecture for seamless performance.

## ✨ Key Features

### 🚀 Core Functionality
- **🖥️ Modern GUI Interface**: Intuitive PySide6 interface for seamless configuration and control.
- **🔥 Global Hotkey Support**: Instantly toggle recording with customizable keyboard shortcuts.
- **🎵 High-Quality Audio Recording**: Professional WAV output (16-bit depth, 16kHz sample rate).
- **🤖 Real-time Transcription**: Accurate speech-to-text powered by HuggingFace Whisper models.
- **📋 Intelligent Text Pasting**: Automatic clipboard management and text insertion.
- **🖱️ Program Controls**: GUI buttons for start/stop with real-time status indicators.

### ⚡ Advanced Capabilities
- **💻 GPU/CUDA Acceleration**: Optimized performance with NVIDIA GPUs using float16 precision.
- **🔄 Automatic Model Conversion**: Seamlessly converts HuggingFace PyTorch models to CTranslate2 format for faster-whisper compatibility.
- **⚡ Optimized Distil-Whisper**: Integrates Distil-Whisper models with enhanced parameters (`beam_size=5`, `language='en'`, `condition_on_previous_text=False`) for improved accuracy and speed.
- **⚙️ Smart Configuration**: GUI-based settings with automatic GPU detection and model management.
- **⚡ Threaded Architecture**: Non-blocking operations and real-time status monitoring.
- **🛡️ Thread Safety**: Robust concurrent operation handling with proper locking mechanisms.
- **📊 Comprehensive Logging**: Detailed debugging and monitoring logs for issue diagnosis.
- **🔄 Graceful Shutdown**: Clean handling of interrupts and system termination.
- **📦 Model Management**: Download and manage any HuggingFace Whisper model directly from the GUI.


## 📦 Installation

### Quick Start (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd dictationer

# Create virtual environment
python -m venv venv
# Windows: Use venv\Scripts\activate
# Linux/macOS: Use source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch GUI (Recommended)
./start_gui.bat    # Windows
./start_gui.sh     # Linux/macOS

## ⌨️ Setting Up Your Hotkey (Important!)

**⚠️ CRITICAL: The hotkey format must be EXACTLY correct or it won't work!**

### Quick Setup Steps

1. **Launch the GUI:**
   ```bash
   ./start_gui.bat    # Windows
   ./start_gui.sh     # Linux/macOS
   ```

2. **Configure Your Hotkey:**
   - Go to **Settings** tab
   - Find **Audio Settings** → **Hotkey** field
   - Enter your hotkey in the exact format: `ctrl+win+shift+l`

3. **Format Requirements:**
   - **Lowercase letters only**: `ctrl` not `Ctrl`
   - **Plus signs with no spaces**: `ctrl+alt+r` not `ctrl + alt + r`
   - **Use exact modifier names**: `ctrl`, `alt`, `shift`, `win`

### ✅ Valid Examples
```
ctrl+win+shift+l     ✓ Default hotkey
ctrl+alt+r           ✓ Simple combination  
shift+f1             ✓ Function key combo
ctrl+shift+space     ✓ With space key
```

### ❌ Common Mistakes
```
Ctrl+Win+Shift+L     ✗ Uppercase letters
ctrl + alt + r       ✗ Spaces around plus signs
control+alt+r        ✗ Wrong modifier name
ctrl-alt-r           ✗ Wrong separator
```

### 🧪 Testing Your Hotkey
After setting your hotkey in the GUI:
1. Click **Start Program** button
2. Try pressing your hotkey combination
3. Look for "Recording state: ON/OFF" message in the log output
4. If nothing happens, check the format and try again

**💡 Tip**: The default `ctrl+win+shift+l` is tested to work reliably across platforms!

### 🔧 System Requirements
- **CPU**: Capable of running base or small Whisper models.
- **GPU**: **Highly recommended** for optimal performance, especially with larger models. Supports NVIDIA GPUs with CUDA.

#### Core Dependencies
```bash
# Audio Recording & Processing
pyaudio          # High-quality audio capture
faster-whisper   # Advanced speech recognition engine
watchdog         # File system event monitoring

# System & Utilities
keyboard         # Global hotkey detection
pyperclip       # Clipboard automation
python-dotenv    # Environment variable management

# GUI Framework (v1.1+)
PySide6          # Modern GUI toolkit

# AI & GPU Acceleration
transformers     # HuggingFace model integration
torch            # PyTorch for GPU support (install with CUDA)
ctranslate2     # For optimized model inference
```

#### Development Dependencies
```bash
# Testing and code quality
pytest>=6.0     # Unit testing framework
pytest-cov      # Coverage reporting
black           # Code formatting
mypy            # Type checking
flake8          # Linting
```

### 🖥️ Platform-Specific Setup

#### Windows
```bash
# Install Microsoft Visual C++ Build Tools if needed
# Run as administrator for keyboard hook permissions
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev
pip install dictationer
```

#### macOS
```bash
brew install portaudio
pip install dictationer
# Grant accessibility permissions when prompted
```

## 🚀 Usage

### 🖥️ GUI Interface (Recommended)

#### Quick Start
```bash
# Launch GUI with proper virtual environment
./start_gui.bat    # Windows
./start_gui.sh     # Linux/macOS

# Or manually activate and run
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
python gui_main.py
```

#### GUI Features
- **🎛️ Settings Configuration**: Device selection (CPU/GPU), model selection, hotkey customization
- **📦 Model Download**: Download any HuggingFace Whisper model with progress tracking
- **📁 Model Management**: View cached models and open models folder
- **🎮 Program Control**: Start/Stop the main recording program with real-time status
- **📊 Live Logs**: Real-time log output with scrolling display


#### Advanced Configuration
```bash
# Custom hotkey and output
python main.py --output "recordings/session.wav"

# Use different Whisper model
python main.py  # Configure via GUI or config files
```

## 🤝 Contributions

We welcome contributions from the community! This project has huge potential and there are many exciting features we'd love to add:

### 🌟 High-Impact Contribution Ideas

#### ⌨️ **Hotkey Recorder Widget**
- **What**: Add a "Record Hotkey" button in GUI that captures key presses and auto-formats them correctly
- **Why**: Current hotkey format is error-prone and causes silent failures for users
- **Impact**: Eliminates the #1 setup frustration and improves user experience dramatically

#### 🍎 **macOS Support & Testing**
- **What**: Thorough testing and optimization for macOS users
- **Why**: Many users want native macOS support with proper accessibility permissions
- **Impact**: Expands user base significantly

#### 🌐 **OpenAI Whisper API Integration**
- **What**: Add support for OpenAI's official Whisper API as an alternative to local processing
- **Why**: Cloud processing for users without powerful hardware
- **Impact**: Makes transcription accessible to everyone

#### 🔌 **Plugin Architecture**
- **What**: Create a plugin system for custom transcription processors
- **Why**: Allow community to add new AI models and processing pipelines
- **Impact**: Extensible platform for innovation

#### 🎨 **Advanced UI Features**
- **What**: System tray support, real-time waveform display, custom themes
- **Why**: Better user experience and professional polish
- **Impact**: More intuitive and visually appealing

#### 🌍 **Multi-Language Support**
- **What**: UI translations and language-specific optimizations
- **Why**: Global accessibility for non-English users
- **Impact**: Worldwide adoption

#### 🔧 **Advanced Integrations**
- **What**: IDE plugins (VS Code, IntelliJ), browser extensions, mobile companion apps
- **Why**: Seamless workflow integration
- **Impact**: Professional productivity boost

### 📋 How to Contribute

1. **🍴 Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/dictationer.git
   cd dictationer
   ```

2. **🌱 Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

3. **🛠️ Make Your Changes**
   - Follow the coding standards in `docs/PLANNING.md`
   - Add tests for new functionality
   - Update documentation

4. **✅ Test Thoroughly**
   ```bash
   # Run existing tests
   pytest
   
   # Test your feature manually
   ./start_gui.bat  # or .sh
   ```

5. **📤 Submit a Pull Request**
   - Clear description of changes
   - Reference any related issues
   - Include screenshots for UI changes

### 💡 Contribution Guidelines

- **🎯 Start Small**: Begin with documentation improvements or bug fixes
- **📖 Read the Docs**: Check `docs/PLANNING.md` for architecture details
- **💬 Discuss First**: Open an issue for major features before implementing
- **🧪 Test Everything**: Ensure cross-platform compatibility
- **📝 Document Changes**: Update README and docs as needed

## 💖 Donations

If Dictationer has made your life easier and saved you time, I'd be incredibly grateful for a small donation! ✨

Creating and maintaining open-source projects like this takes countless hours of development, testing, debugging, and support. Your contribution helps me:

- 🚀 **Keep innovating** with new features and improvements
- 🐛 **Fix bugs** and provide ongoing support
- 💻 **Buy better hardware** for testing across different platforms
- ☕ **Stay caffeinated** during those late-night coding sessions!

### 🎁 Ways to Support

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://paypal.me/joygraphs?country.x=AU&locale.x=en_AU)

### 🌟 Other Ways to Help

Even if you can't donate, there are other amazing ways to support the project:

- ⭐ **Star the repository** - helps others discover the project
- 🐛 **Report bugs** - help make it better for everyone
- 📖 **Improve documentation** - share your knowledge
- 💬 **Spread the word** - tell your friends and colleagues
- 🧪 **Test on different platforms** - especially macOS users!

### 💌 A Personal Note

Every donation, no matter how small, means the world to me. It's not just about the money - it's knowing that something I built is genuinely helping people in their daily work and life. Whether you're a student taking notes, a professional writing documentation, or someone with accessibility needs, your support motivates me to keep building amazing tools for everyone.

**Thank you for being awesome!** 🙏

### 🐍 Programmatic API

#### Basic Recording
```python
from dictationer import RecordingController

# Simple recording with defaults
controller = RecordingController()
controller.start()
```

#### Advanced Configuration
```python
from dictationer import RecordingController

# Customized recording setup
controller = RecordingController(
    output_file="outputs/meeting_notes.wav",
    hotkey="ctrl+alt+r",
    enable_transcription=True,
    model_size="base",
    auto_paste=True
)

# Start the recording system
controller.start()

# Access individual components
if controller.audio.is_recording():
    print("Currently recording...")

# Graceful shutdown
controller.stop()
```

#### Component-Level Access
```python
from dictationer.audio import AudioRecorder
from dictationer.processor import AudioProcessor
from dictationer.paster import ClipboardPaster

# Individual component usage
audio = AudioRecorder("output.wav")
audio.start_recording()
# ... perform operations
audio.stop_recording()

# Transcription processor
processor = AudioProcessor(model_size="base", watch_directory="outputs")
processor.start_monitoring()

# Clipboard operations
paster = ClipboardPaster()
success = paster.paste_text("Hello, world!")
```

## 📁 Project Architecture

```
dictationer/
├── 📦 src/dictationer/           # Main package source
│   ├── 🔧 __init__.py            # Package exports & version
│   ├── 🎛️ main.py               # RecordingController (orchestrator)
│   ├── ⌨️ keyboard.py            # KeyboardRecorder (hotkey detection)
│   ├── 🎵 audio.py              # AudioRecorder (audio capture)
│   ├── 🤖 processor.py          # AudioProcessor (transcription)
│   ├── 📋 paster.py             # ClipboardPaster (text automation)
│   ├── 🖥️ gui.py                # PySide6 GUI interface
│   └── ⚙️ config.py             # Configuration management
├── 📚 docs/                      # Documentation
│   ├── 🏗️ PLANNING.md           # Architecture & design
│   ├── 📋 TASK.md               # Task management
│   └── 📖 API.md                # API documentation
├── 🧪 tests/                     # Unit tests
├── 📊 logs/                      # Application logs
├── 🎵 outputs/                   # Recording outputs
├── 🔧 config/                    # Configuration files
├── 🚀 main.py                    # CLI entry point
├── 🖥️ gui_main.py               # GUI entry point
├── 🏃 start_gui.bat             # Windows GUI launcher
├── 🏃 start_gui.sh              # Linux/macOS GUI launcher
├── ⚙️ pyproject.toml             # Package configuration
├── 📦 requirements.txt           # Dependencies
└── 📖 README.md                 # This file
```

### 🧩 Module Overview

| Module | Purpose | Key Features |
|--------|---------|--------------|
| **main.py** | System orchestrator | Lifecycle management, signal handling, logging |
| **keyboard.py** | Hotkey detection | Global shortcuts, thread-safe state management |
| **audio.py** | Audio recording | PyAudio integration, WAV output, threading |
| **processor.py** | Speech-to-text | Whisper models, direct transcription, batch processing |
| **paster.py** | Text automation | Clipboard management, keyboard simulation |
| **gui.py** | GUI interface | PySide6 interface, model downloads, program control |
| **config.py** | Configuration | Settings management, device detection, model caching |

## ⚙️ Configuration

### 📋 Default Settings

| Setting | Default Value | Description |
|---------|---------------|-------------|
| **Hotkey** | `ctrl+win+shift+l` | Global shortcut to toggle recording |
| **Audio Format** | WAV (16-bit, 16kHz, Mono) | High-quality audio output |
| **Output Directory** | `outputs/` | Recording storage location |
| **Log Directory** | `logs/` | Debug and monitoring logs |
| **Whisper Model** | `base` | Speech recognition model |
| **Auto-paste** | `True` | Automatic text insertion |

### 🎛️ Customization Options

#### Environment Variables
```bash
# Set custom defaults
export DICTATIONER_HOTKEY="ctrl+shift+r"
export WHISPER_MODEL_SIZE="large-v3"
export OUTPUT_DIRECTORY="recordings"
```

#### Programmatic Configuration
```python
controller = RecordingController(
    output_file="meetings/2025-07-19_team_meeting.wav",
    hotkey="ctrl+alt+r",
    enable_transcription=True,
    model_size="large-v3",
    auto_paste=False
)
```

#### Configuration File (Future)
```yaml
# dictationer.yml
audio:
  sample_rate: 16000
  channels: 1
  format: "wav"
  
transcription:
  model_size: "base"
  language: "auto"
  auto_paste: true
  
hotkeys:
  toggle_recording: "ctrl+win+shift+l"
  emergency_stop: "ctrl+win+shift+x"
```

### ⌨️ Hotkey Configuration

**⚠️ FORMAT CRITICAL**: The Python `keyboard` module is **very sensitive** to hotkey format. Even small deviations will cause complete failure!

#### Required Format Rules

1. **Lowercase only**: `ctrl`, `alt`, `shift`, `win` (never `Ctrl`, `Alt`, etc.)
2. **No spaces around plus signs**: `ctrl+alt+r` (never `ctrl + alt + r`)
3. **Exact modifier names**: `ctrl` not `control`, `win` not `windows`
4. **Plus sign separator**: Use `+` only (never `-`, `_`, or spaces)

#### Supported Keys
- **Modifiers**: `ctrl`, `alt`, `shift`, `win`
- **Letters**: `a-z` (lowercase only)
- **Numbers**: `0-9`
- **Function**: `f1-f12`
- **Special**: `space`, `enter`, `esc`, `tab`, `backspace`

#### Hotkey Examples
```python
# ✅ CORRECT - These will work
"ctrl+shift+r"           # Ctrl + Shift + R
"alt+f1"                 # Alt + F1
"ctrl+win+shift+l"       # Ctrl + Win + Shift + L (default)
"ctrl+alt+space"         # Ctrl + Alt + Space
"shift+f10"              # Shift + F10
"win+alt+d"              # Windows + Alt + D

# ❌ WRONG - These will fail silently
"Ctrl+Shift+R"           # Uppercase modifiers
"ctrl + shift + r"       # Spaces around plus signs
"control+shift+r"        # Wrong modifier name
"ctrl-shift-r"           # Wrong separator
"CTRL+SHIFT+R"           # All uppercase
```

#### Format Validation Tips

1. **Test immediately**: After setting a hotkey, test it right away
2. **Check logs**: Look for "Recording state: ON/OFF" messages when pressing keys
3. **Use defaults first**: Try `ctrl+win+shift+l` to verify basic functionality
4. **No silent failures**: The keyboard module won't warn you about invalid formats

#### Platform Considerations
- **Windows**: All combinations supported (run as administrator for global hooks)
- **Linux**: May require X11 permissions for global hooks
- **macOS**: Requires accessibility permissions for global keyboard access

#### Troubleshooting Invalid Hotkeys

If your hotkey doesn't work:
1. **Check format exactly** against the rules above
2. **Try the default**: `ctrl+win+shift+l` should always work
3. **Look at logs**: No "Recording state" messages = bad format
4. **Test modifiers**: Some combinations may conflict with system shortcuts

## 📊 Logging & Monitoring

### Log Structure
The application creates comprehensive logs for debugging and monitoring:

| Log File | Level | Purpose |
|----------|-------|---------|
| **Console** | INFO+ | Real-time user feedback |
| **voice_recorder_debug.log** | DEBUG+ | Main system operations |
| **audio_processor.log** | DEBUG+ | Transcription and processing |

### Log Format
```
HH:MM:SS | LEVEL    | MODULE          | MESSAGE
14:30:25 | INFO     | AudioRecorder   | Recording started...
14:30:30 | DEBUG    | AudioProcessor  | Transcription completed
```

### Monitoring Features
- **Real-time Status**: Recording state and system health
- **Performance Metrics**: Processing times and resource usage
- **Error Tracking**: Detailed exception handling and recovery
- **Thread Monitoring**: Multi-threaded operation tracking

## 🛠️ Development

### 🚀 Quick Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd dictationer
python -m venv venv_linux
source venv_linux/bin/activate  # Linux/macOS

# Install with development tools
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/dictationer --cov-report=html

# Run specific test categories
pytest tests/test_audio.py -v
pytest -k "test_recording" -v
```

### 🎨 Code Quality

```bash
# Format code (required before commit)
black src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/

# Run all quality checks
make lint  # or equivalent script
```

### 📋 Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
2. **Write Tests**: Add tests for new functionality
3. **Implement Feature**: Follow coding standards and patterns
4. **Run Quality Checks**: Ensure all checks pass
5. **Update Documentation**: Add/update relevant docs
6. **Submit PR**: Include tests and documentation

## 🔧 Troubleshooting

### 🚨 Common Issues & Solutions

#### Virtual Environment Issues
```bash
# Problem: "No module named 'faster_whisper'" or similar import errors
# Solution: Make sure you're using the virtual environment

# Windows
venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS  
source venv/bin/activate
pip install -r requirements.txt

# Always use the launcher scripts for GUI
./start_gui.bat    # Windows
./start_gui.sh     # Linux/macOS
```

#### GPU Detection Problems
```bash
# Problem: GPU not detected even when available
# Solution: Ensure PyTorch is installed with CUDA support

# Check current PyTorch installation
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Install PyTorch with CUDA (Windows/Linux)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CPU-only systems
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### Model Download Failures
```bash
# Problem: Model download fails or gets stuck
# Solution: Clear cache and retry

# Clear HuggingFace cache
rm -rf ~/.cache/huggingface/
# Windows: rmdir /s "%USERPROFILE%\.cache\huggingface"

# Test model download manually
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"

# For network issues, try different model names:
# - openai/whisper-base
# - openai/whisper-large-v3
# - distil-whisper/distil-large-v3
```

#### Audio Recording Issues
```bash
# Problem: "No audio input device" or microphone not working
# Solution: Check audio device permissions and availability

# List available audio devices
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f'{i}: {info[\"name\"]} - Inputs: {info[\"maxInputChannels\"]}')
"

# Test microphone access
python -c "
import pyaudio
p = pyaudio.PyAudio()
try:
    info = p.get_default_input_device_info()
    print(f'Default microphone: {info[\"name\"]} - OK')
except:
    print('No default microphone found')
"
```

#### PyAudio Installation Problems
```bash
# Windows - Install Microsoft Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Then: pip install pyaudio

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev build-essential
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Alternative: Use conda
conda install pyaudio
```

#### Keyboard Hook Permissions
```bash
# Windows - Run as administrator (required for global hotkeys)
# Right-click Command Prompt → "Run as administrator"
# Or run GUI from elevated terminal

# Linux - Add user to input group
sudo usermod -a -G input $USER
# Logout and login again

# macOS - Grant accessibility permissions
# System Preferences → Security & Privacy → Privacy → Accessibility
# Add Terminal or your IDE to allowed applications
```

#### Hotkey Not Working / Not Responding
```bash
# Problem: Hotkey doesn't trigger recording, no response when pressed
# Solution: Check format and test systematically

# 1. Verify exact format in GUI settings
# Open GUI → Settings → Audio Settings → Hotkey field
# Should look exactly like: ctrl+win+shift+l

# 2. Common format issues to check:
echo "Checking common hotkey format problems..."

# ❌ Wrong: Uppercase letters
# "Ctrl+Win+Shift+L" 

# ❌ Wrong: Spaces around plus signs  
# "ctrl + win + shift + l"

# ❌ Wrong: Different modifier names
# "control+windows+shift+l"

# ❌ Wrong: Different separators
# "ctrl-win-shift-l" or "ctrl_win_shift_l"

# ✅ Correct format:
# "ctrl+win+shift+l"

# 3. Test with known working hotkey
# Set hotkey to exactly: ctrl+win+shift+l
# This is the tested default that should work

# 4. Check for conflicts with system shortcuts
# Try a simple combination like: ctrl+alt+f1
# Some complex combinations may conflict with OS hotkeys

# 5. Verify program is running and listening
# In GUI logs, look for:
# "[KEYBOARD] Hotkey registered successfully"
# "[KEYBOARD] Starting keyboard event loop"

# 6. Test hotkey detection manually
python -c "
import keyboard
print('Testing hotkey detection...')
print('Press Ctrl+Alt+T to test (or your hotkey)')
try:
    keyboard.wait('ctrl+alt+t')
    print('✅ Hotkey detected successfully!')
    print('Your format is correct, check Dictationer settings')
except Exception as e:
    print(f'❌ Hotkey detection failed: {e}')
    print('Check format and admin permissions')
"

# 7. Platform-specific debugging
# Windows: Ensure running as administrator
# Linux: Check X11 permissions and input group membership
# macOS: Verify accessibility permissions granted
```

#### Transcription Not Working
```bash
# Problem: Recording works but no transcription appears
# Solution: Check processor initialization

# Verify dependencies are installed correctly
python -c "
try:
    from faster_whisper import WhisperModel
    print('faster-whisper: OK')
except Exception as e:
    print(f'faster-whisper: FAILED - {e}')

try:
    from watchdog.observers import Observer
    print('watchdog: OK')
except Exception as e:
    print(f'watchdog: FAILED - {e}')
"

# Check if audio files are being created
ls -la outputs/  # Should show .wav files after recording

# Manually test transcription
python -c "
from src.dictationer.processor import AudioProcessor
processor = AudioProcessor('base', 'outputs', True)
result = processor.transcribe_file('outputs/recording.wav')
print(f'Transcription result: {result}')
"
```

#### Unicode/Encoding Errors
```bash
# Problem: 'charmap' codec errors in Windows console
# Solution: Use UTF-8 encoding

# Set environment variable (Windows)
set PYTHONIOENCODING=utf-8

# Or use PowerShell instead of Command Prompt
# All GUI launchers handle this automatically
```

#### GUI Won't Start
```bash
# Problem: GUI fails to launch or crashes immediately
# Solution: Check PySide6 installation and dependencies

# Verify PySide6 installation
python -c "
try:
    from PySide6.QtWidgets import QApplication
    print('PySide6: OK')
except Exception as e:
    print(f'PySide6: FAILED - {e}')
    print('Install with: pip install PySide6')
"

# Check if display is available (Linux)
echo $DISPLAY  # Should show :0 or similar

# For headless systems, use Xvfb
sudo apt-get install xvfb
xvfb-run python gui_main.py
```

#### Performance Issues
```bash
# Problem: Slow transcription or high CPU usage
# Solution: Optimize model and device settings

# Use smaller model for faster processing
# In GUI: Select "tiny" or "base" instead of "large"

# Enable GPU if available
# GUI will auto-detect, or manually verify:
python -c "
import torch
if torch.cuda.is_available():
    print(f'GPU available: {torch.cuda.get_device_name()}')
    print('Enable GPU in GUI settings for faster processing')
else:
    print('No GPU available, using CPU')
"

# For very slow systems, disable real-time transcription
# Edit config/settings.json: "enable_transcription": false
```

### 🔍 Debug Mode & Logging

#### Enable Detailed Logging
```bash
# Check log files for errors
tail -f logs/voice_recorder_debug.log
tail -f logs/audio_processor.log

# Look for specific error patterns
grep -i error logs/*.log
grep -i failed logs/*.log
grep -i exception logs/*.log
```

#### Manual Component Testing
```bash
# Test individual components

# 1. Test audio recording
python -c "
from src.dictationer.audio import AudioRecorder
recorder = AudioRecorder('test.wav')
print('Press Enter to start recording...')
input()
recorder.start_recording()
input('Press Enter to stop...')
recorder.stop_recording()
print('Check test.wav file')
"

# 2. Test transcription
python -c "
from src.dictationer.processor import AudioProcessor
processor = AudioProcessor()
result = processor.transcribe_file('test.wav')
print(f'Result: {result}')
"

# 3. Test clipboard pasting
python -c "
from src.dictationer.paster import ClipboardPaster
paster = ClipboardPaster()
success = paster.paste_text('Test message')
print(f'Paste success: {success}')
"
```

### 📞 Getting Help

If you're still experiencing issues:

1. **Check log files** in the `logs/` directory for detailed error messages
2. **Run GUI launcher scripts** (`start_gui.bat`/`start_gui.sh`) instead of calling Python directly
3. **Verify virtual environment** is activated and all dependencies are installed
4. **Test components individually** using the manual testing scripts above
5. **Check system requirements** (microphone access, admin permissions, etc.)

For additional support:
- 📖 **Read**: `docs/PLANNING.md` for architecture details  
- 🐛 **Report bugs**: Create an issue with log files and error messages
- 💡 **Feature requests**: Describe your use case and requirements

### 🔍 Debug Mode

#### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export DICTATIONER_LOG_LEVEL=DEBUG
```

#### Log Analysis
```bash
# Real-time log monitoring
tail -f logs/voice_recorder_debug.log

# Search for specific issues
grep ERROR logs/*.log
grep "CRITICAL\|FATAL" logs/*.log
```

#### Performance Debugging
```python
# Enable performance profiling
controller = RecordingController(profile_performance=True)

# Check system resources
import psutil
print(f"CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%")
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🌟 Ways to Contribute
- 🐛 **Bug Reports**: Report issues with detailed reproduction steps
- 💡 **Feature Requests**: Suggest new features or improvements
- 📖 **Documentation**: Improve docs, tutorials, or examples
- 🧪 **Testing**: Add tests or improve test coverage
- 💻 **Code**: Fix bugs or implement new features

### 📋 Contribution Guidelines

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/dictationer.git
   cd dictationer
   ```

2. **Setup Development Environment**
   ```bash
   python -m venv venv_linux
   source venv_linux/bin/activate
   pip install -e .[dev]
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make Changes**
   - Follow the coding standards in `docs/PLANNING.md`
   - Add tests for new functionality
   - Update documentation as needed

5. **Quality Checks**
   ```bash
   black src/ tests/          # Format code
   mypy src/                  # Type checking
   pytest --cov=src/dictationer  # Run tests
   ```

6. **Submit Pull Request**
   - Include clear description of changes
   - Reference any related issues
   - Ensure all checks pass

### 📝 Code of Conduct
- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow

## 📄 License

**MIT License** - see [LICENSE](LICENSE) file for details.

## 📚 Documentation

- 🏗️ **[Architecture & PRD](docs/PLANNING.md)** - System design, requirements, and architecture overview
- 📋 **[Task Management](docs/TASK.md)** - Project roadmap and tasks
- 📖 **[API Reference](docs/API.md)** - Detailed API documentation
- 🛠️ **[Development Guide](docs/DEVELOPMENT.md)** - Setup, standards, testing, and debugging

## 🆕 Changelog

### Version 1.1.0 (2025-07-19) - GUI Release
- 🖥️ **PySide6 GUI Interface**: Complete graphical user interface with modern design
- 🎛️ **Settings Management**: GUI-based configuration with device detection
- 📦 **Model Download Manager**: Download any HuggingFace Whisper model with progress tracking
- 🔧 **Configuration System**: JSON-based settings with automatic GPU detection
- 🚀 **Launcher Scripts**: Cross-platform GUI launchers with proper virtual environment handling
- 🎮 **Program Control**: Start/Stop main program from GUI with real-time status
- 📊 **Live Log Display**: Real-time log output with scrolling and filtering
- 📁 **Model Cache Access**: Direct access to model storage folder
- 🛠️ **Simplified Architecture**: Removed dual processing paths for better reliability
- 🔍 **Enhanced Debugging**: Comprehensive logging and error handling
- 📚 **Complete Documentation**: Updated docs with troubleshooting guide

### Version 1.0.0 (2025-07-19) - Initial Release
- ✨ **Initial Release**: Complete voice recording and transcription system
- 🏗️ **Modular Architecture**: Clean separation of concerns with threaded design
- 🎵 **High-Quality Audio**: 16-bit WAV recording with PyAudio integration
- 🤖 **Advanced Transcription**: Faster-Whisper integration with multiple model sizes
- 📋 **Smart Text Pasting**: Intelligent clipboard management and automation
- ⌨️ **Global Hotkeys**: Configurable keyboard shortcuts for system control
- 📊 **Comprehensive Logging**: Detailed monitoring and debugging capabilities
- 🛡️ **Thread Safety**: Robust concurrent operation handling
- 📦 **Professional Packaging**: Proper Python package structure and installation

### Upcoming in 1.2.0
- 🧪 **Unit Testing**: Comprehensive test suite with 90% coverage
- 🎨 **System Tray**: Background operation with system tray controls
- 🌐 **Cross-Platform**: Enhanced macOS and Linux support
- 🔊 **Audio Formats**: Support for MP3, FLAC, and other audio formats

---

<div align="center">

**Made with ❤️ for the voice recording community**

[⭐ Star this repo](https://github.com/yourusername/dictationer) • [🐛 Report Bug](https://github.com/yourusername/dictationer/issues) • [💡 Request Feature](https://github.com/yourusername/dictationer/issues)

</div>