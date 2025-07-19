# 📖 Dictationer API Documentation

## Table of Contents

1. [Overview](#overview)
2. [RecordingController](#recordingcontroller)
3. [AudioRecorder](#audiorecorder)
4. [KeyboardRecorder](#keyboardrecorder)
5. [AudioProcessor](#audioprocessor)
6. [ClipboardPaster](#clipboardpaster)
7. [Examples](#examples)
8. [Error Handling](#error-handling)

---

## Overview

The Dictationer API provides a comprehensive set of classes and methods for voice recording, transcription, and text automation. The system is built with a modular architecture that allows for both high-level orchestration and low-level component control.

### Core Components

```python
from dictationer import RecordingController
from dictationer.audio import AudioRecorder
from dictationer.keyboard import KeyboardRecorder
from dictationer.processor import AudioProcessor
from dictationer.paster import ClipboardPaster
```

---

## RecordingController

The main orchestrator class that coordinates all system components.

### Class Definition

```python
class RecordingController:
    """
    Main controller that coordinates keyboard and audio recording.
    
    Attributes:
        keyboard (KeyboardRecorder): Handles hotkey detection.
        audio (AudioRecorder): Handles audio recording.
    """
```

### Constructor

```python
def __init__(
    self, 
    output_file: str = "recording.wav", 
    hotkey: str = "ctrl+win+shift+l",
    enable_transcription: bool = True, 
    model_size: str = "base", 
    auto_paste: bool = True
) -> None
```

**Parameters:**
- `output_file` (str): Path for output WAV file. Default: "recording.wav"
- `hotkey` (str): Hotkey combination for toggling recording. Default: "ctrl+win+shift+l"
- `enable_transcription` (bool): Whether to enable automatic transcription. Default: True
- `model_size` (str): Whisper model size for transcription. Default: "base"
- `auto_paste` (bool): Whether to automatically paste transcribed text. Default: True

**Example:**
```python
controller = RecordingController(
    output_file="outputs/meeting_notes.wav",
    hotkey="ctrl+shift+r",
    enable_transcription=True,
    model_size="large-v3",
    auto_paste=False
)
```

### Methods

#### start()

```python
def start(self) -> None
```

Start the recording system with all components.

**Behavior:**
- Initializes keyboard monitoring
- Starts status monitoring thread
- Displays user instructions
- Handles graceful shutdown on interruption

**Example:**
```python
controller = RecordingController()
controller.start()  # Runs until interrupted
```

#### stop()

```python
def stop(self) -> None
```

Stop the recording system gracefully.

**Behavior:**
- Stops any active recording
- Terminates keyboard monitoring
- Cleans up all threads and resources
- Thread-safe operation with locking

**Example:**
```python
controller.stop()  # Clean shutdown
```

### Properties

#### keyboard

Access to the KeyboardRecorder instance.

```python
keyboard_state = controller.keyboard.get_state()
```

#### audio

Access to the AudioRecorder instance.

```python
is_recording = controller.audio.is_recording()
```

---

## AudioRecorder

Handles audio recording functionality using PyAudio.

### Class Definition

```python
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
```

### Constructor

```python
def __init__(
    self, 
    output_file: str = "recording.wav", 
    enable_transcription: bool = True, 
    model_size: str = "base", 
    auto_paste: bool = True
) -> None
```

**Parameters:**
- `output_file` (str): Path for output WAV file. Default: "recording.wav"
- `enable_transcription` (bool): Enable automatic transcription. Default: True
- `model_size` (str): Whisper model size. Default: "base"
- `auto_paste` (bool): Enable automatic text pasting. Default: True

**Audio Settings:**
- Sample Rate: 16kHz (16000 Hz)
- Channels: 1 (Mono)
- Bit Depth: 16-bit
- Format: WAV

### Methods

#### start_recording()

```python
def start_recording(self) -> None
```

Start recording audio in a separate thread.

**Behavior:**
- Thread-safe operation with locking
- Clears previous recording data
- Creates dedicated recording thread
- Provides console feedback

**Example:**
```python
audio = AudioRecorder("session.wav")
audio.start_recording()
```

#### stop_recording()

```python
def stop_recording(self) -> None
```

Stop recording and save to file.

**Behavior:**
- Thread-safe termination
- Waits for recording thread completion
- Saves audio data to WAV file
- Initiates transcription if enabled

**Example:**
```python
audio.stop_recording()
```

#### is_recording()

```python
def is_recording(self) -> bool
```

Check if currently recording.

**Returns:**
- `bool`: True if recording is active, False otherwise

**Example:**
```python
if audio.is_recording():
    print("Recording in progress...")
```

#### toggle_recording()

```python
def toggle_recording(self, state: bool) -> None
```

Toggle recording based on state.

**Parameters:**
- `state` (bool): True to start recording, False to stop

**Example:**
```python
audio.toggle_recording(True)   # Start recording
audio.toggle_recording(False)  # Stop recording
```

---

## KeyboardRecorder

Monitors keyboard for specific hotkey combinations.

### Class Definition

```python
class KeyboardRecorder:
    """
    Monitors keyboard for specific hotkey combination.
    
    Attributes:
        recording_state (bool): Current recording state.
        hotkey (str): The key combination to monitor.
        callback (Optional[Callable]): Function to call when state changes.
    """
```

### Constructor

```python
def __init__(self, hotkey: str = "ctrl+win+shift+l") -> None
```

**Parameters:**
- `hotkey` (str): Key combination to monitor. Default: "ctrl+win+shift+l"

**Supported Key Formats:**
- Modifiers: `ctrl`, `alt`, `shift`, `win`
- Letters: `a-z`
- Numbers: `0-9`
- Function keys: `f1-f12`
- Special keys: `space`, `enter`, `esc`

### Methods

#### start()

```python
def start(self) -> None
```

Start monitoring keyboard in a separate thread.

**Behavior:**
- Creates dedicated monitoring thread
- Registers global hotkey hook
- Thread-safe operation

**Example:**
```python
keyboard = KeyboardRecorder("ctrl+shift+r")
keyboard.start()
```

#### stop()

```python
def stop(self) -> None
```

Stop monitoring keyboard.

**Behavior:**
- Removes keyboard hooks
- Terminates monitoring thread
- Clean resource cleanup

**Example:**
```python
keyboard.stop()
```

#### set_callback()

```python
def set_callback(self, callback: Callable[[bool], None]) -> None
```

Set callback function for state changes.

**Parameters:**
- `callback` (Callable): Function that takes recording state as parameter

**Example:**
```python
def on_state_change(is_recording):
    print(f"Recording: {'ON' if is_recording else 'OFF'}")

keyboard.set_callback(on_state_change)
```

#### get_state()

```python
def get_state(self) -> bool
```

Get current recording state.

**Returns:**
- `bool`: Current recording state

**Example:**
```python
current_state = keyboard.get_state()
```

#### toggle_recording()

```python
def toggle_recording(self) -> None
```

Toggle recording state and trigger callback.

**Behavior:**
- Thread-safe state toggle
- Executes registered callback
- Provides console feedback

---

## AudioProcessor

Handles speech-to-text conversion and file monitoring.

### Class Definition

```python
class AudioProcessor:
    """
    Main audio processor class that handles transcription and file monitoring.
    
    This class integrates faster-whisper for transcription with watchdog for
    file system monitoring, automatically processing new audio files as they
    are created in the specified directory.
    """
```

### Constructor

```python
def __init__(
    self, 
    model_size: str = "base", 
    watch_directory: str = "outputs", 
    auto_paste: bool = True
) -> None
```

**Parameters:**
- `model_size` (str): Whisper model size. Options: "tiny", "base", "small", "medium", "large", "large-v2", "large-v3"
- `watch_directory` (str): Directory to monitor for new audio files. Default: "outputs"
- `auto_paste` (bool): Enable automatic text pasting. Default: True

**Model Performance:**
- **tiny**: Fastest, lowest accuracy (~39 MB)
- **base**: Good balance (~74 MB)
- **small**: Better accuracy (~244 MB) 
- **medium**: High accuracy (~769 MB)
- **large-v3**: Best accuracy (~1550 MB)

### Methods

#### transcribe_file()

```python
def transcribe_file(self, file_path: str) -> Optional[str]
```

Transcribe an audio file using faster-whisper.

**Parameters:**
- `file_path` (str): Path to the audio file to transcribe

**Returns:**
- `Optional[str]`: Transcribed text, or None if transcription failed

**Example:**
```python
processor = AudioProcessor(model_size="base")
text = processor.transcribe_file("recording.wav")
if text:
    print(f"Transcription: {text}")
```

#### start_monitoring()

```python
def start_monitoring(self) -> None
```

Start monitoring the watch directory for new audio files.

**Behavior:**
- Uses Watchdog for file system monitoring
- Automatically processes new .wav files
- Runs transcription in separate threads

**Example:**
```python
processor = AudioProcessor(watch_directory="recordings")
processor.start_monitoring()
```

#### stop_monitoring()

```python
def stop_monitoring(self) -> None
```

Stop monitoring and cleanup resources.

**Example:**
```python
processor.stop_monitoring()
```

#### is_monitoring()

```python
def is_monitoring(self) -> bool
```

Check if file monitoring is currently active.

**Returns:**
- `bool`: True if monitoring is active, False otherwise

---

## ClipboardPaster

Manages clipboard operations and keyboard simulation.

### Class Definition

```python
class ClipboardPaster:
    """
    Manages clipboard operations and keyboard simulation for pasting text.
    
    This class provides a complete workflow for safely pasting text by:
    1. Saving the current clipboard content
    2. Setting new text to clipboard
    3. Simulating Ctrl+V paste operation
    4. Restoring the original clipboard content
    """
```

### Constructor

```python
def __init__(self) -> None
```

Initialize the ClipboardPaster.

### Methods

#### paste_text()

```python
def paste_text(self, text: str, restore_delay: float = 0.5) -> bool
```

Complete workflow: save clipboard, set text, paste, and restore clipboard.

**Parameters:**
- `text` (str): The text to paste
- `restore_delay` (float): Delay in seconds before restoring clipboard. Default: 0.5

**Returns:**
- `bool`: True if the complete workflow was successful, False otherwise

**Example:**
```python
paster = ClipboardPaster()
success = paster.paste_text("Hello, world!")
if success:
    print("Text pasted successfully")
```

#### save_clipboard()

```python
def save_clipboard(self) -> bool
```

Save the current clipboard content.

**Returns:**
- `bool`: True if clipboard was saved successfully, False otherwise

#### set_clipboard()

```python
def set_clipboard(self, text: str) -> bool
```

Set new text to clipboard.

**Parameters:**
- `text` (str): The text to set to clipboard

**Returns:**
- `bool`: True if clipboard was set successfully, False otherwise

#### restore_clipboard()

```python
def restore_clipboard(self) -> bool
```

Restore the previously saved clipboard content.

**Returns:**
- `bool`: True if clipboard was restored successfully, False otherwise

#### simulate_paste()

```python
def simulate_paste(self) -> bool
```

Send Ctrl+V keyboard combination to simulate paste operation.

**Returns:**
- `bool`: True if paste simulation was successful, False otherwise

---

## Examples

### Basic Recording

```python
from dictationer import RecordingController

# Simple recording with defaults
controller = RecordingController()
controller.start()
```

### Custom Configuration

```python
controller = RecordingController(
    output_file="meetings/team_standup.wav",
    hotkey="ctrl+alt+r",
    enable_transcription=True,
    model_size="large-v3",
    auto_paste=False
)
controller.start()
```

### Component-Level Usage

```python
from dictationer.audio import AudioRecorder
from dictationer.processor import AudioProcessor

# Manual audio recording
audio = AudioRecorder("manual_recording.wav")
audio.start_recording()
# ... do something
audio.stop_recording()

# Standalone transcription
processor = AudioProcessor(model_size="base")
text = processor.transcribe_file("manual_recording.wav")
print(text)
```

### Clipboard Automation

```python
from dictationer.paster import ClipboardPaster

paster = ClipboardPaster()

# Simple paste
paster.paste_text("Hello from Dictationer!")

# Manual workflow
paster.save_clipboard()
paster.set_clipboard("Custom text")
paster.simulate_paste()
paster.restore_clipboard()
```

### Event-Driven Processing

```python
from dictationer.keyboard import KeyboardRecorder

def on_recording_state_change(is_recording):
    if is_recording:
        print("🔴 Recording started")
    else:
        print("⏹️ Recording stopped")

keyboard = KeyboardRecorder("ctrl+shift+r")
keyboard.set_callback(on_recording_state_change)
keyboard.start()
```

---

## Error Handling

### Common Exceptions

#### AudioDeviceError
Raised when audio device cannot be accessed.

```python
try:
    audio = AudioRecorder()
    audio.start_recording()
except Exception as e:
    print(f"Audio device error: {e}")
```

#### TranscriptionError
Raised when transcription fails.

```python
try:
    processor = AudioProcessor()
    text = processor.transcribe_file("audio.wav")
except Exception as e:
    print(f"Transcription failed: {e}")
```

#### KeyboardHookError
Raised when keyboard hooks cannot be registered.

```python
try:
    keyboard = KeyboardRecorder()
    keyboard.start()
except Exception as e:
    print(f"Keyboard hook error: {e}")
```

### Error Recovery Patterns

#### Graceful Degradation

```python
controller = RecordingController(
    enable_transcription=True,
    auto_paste=True
)

# System will continue working even if transcription fails
controller.start()
```

#### Retry Logic

```python
import time

def reliable_transcription(file_path, max_retries=3):
    processor = AudioProcessor()
    
    for attempt in range(max_retries):
        try:
            return processor.transcribe_file(file_path)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return None
```

#### Resource Cleanup

```python
controller = None
try:
    controller = RecordingController()
    controller.start()
except KeyboardInterrupt:
    print("Interrupted by user")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    if controller:
        controller.stop()
```

---

## Threading Considerations

### Thread Safety

All major operations are thread-safe:

- **AudioRecorder**: Uses locks for recording state
- **KeyboardRecorder**: Thread-safe state management
- **RecordingController**: Coordinated shutdown handling

### Performance Tips

```python
# Use appropriate model size for your hardware
processor = AudioProcessor(
    model_size="base"  # Good balance for most systems
)

# Optimize for real-time processing
controller = RecordingController(
    enable_transcription=True,  # Process in background
    auto_paste=True            # Immediate results
)
```

### Memory Management

```python
# Clean shutdown to prevent memory leaks
try:
    controller.start()
finally:
    controller.stop()  # Always cleanup
```

---

**Last Updated**: 2025-07-19  
**API Version**: 1.0.0  
**Compatible Python**: 3.8+