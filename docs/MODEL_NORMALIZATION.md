# Model Name Normalization System

## Overview

The model name normalization system automatically converts HuggingFace model repository names to faster-whisper compatible format, making the system more user-friendly by allowing users to copy model names directly from HuggingFace model cards.

## Features

- **Transparent Normalization**: Automatically converts HuggingFace format names before model loading
- **Backward Compatibility**: Existing normalized names continue to work unchanged
- **Comprehensive Logging**: Clear logging of normalization process for debugging
- **Configuration Integration**: Automatic normalization when saving/loading model preferences
- **Cache Compatibility**: Works with both original and normalized names for model caching

## Supported Conversions

### Distil-Whisper Models
- `distil-whisper/distil-large-v3` → `distil-large-v3`
- `distil-whisper/distil-large-v3.5` → `distil-large-v3.5`
- `distil-whisper/distil-medium.en` → `distil-medium.en`
- `distil-whisper/distil-small.en` → `distil-small.en`

### OpenAI Whisper Models
- `openai/whisper-large-v3` → `large-v3`
- `openai/whisper-large-v3-turbo` → `large-v3-turbo`
- `openai/whisper-base` → `base`
- `openai/whisper-small` → `small`
- `openai/whisper-medium` → `medium`

### Standard Models (Unchanged)
- `base` → `base`
- `large` → `large`
- `large-v3` → `large-v3`
- `tiny` → `tiny`
- `small` → `small`
- `medium` → `medium`

### Custom Models (Unchanged)
- `custom-org/custom-model` → `custom-org/custom-model`
- `microsoft/whisper-custom` → `microsoft/whisper-custom`

## Implementation Details

### Core Function

The normalization is handled by the [`normalize_model_name()`](../src/dictationer/config.py:449) function in [`config.py`](../src/dictationer/config.py):

```python
def normalize_model_name(model_name: str) -> str:
    """
    Normalize HuggingFace model names to faster-whisper compatible format.
    
    Examples:
        distil-whisper/distil-large-v3 -> distil-large-v3
        openai/whisper-large-v3 -> large-v3
        base -> base (unchanged)
    """
```

### Integration Points

1. **AudioProcessor Initialization**: [`AudioProcessor.__init__()`](../src/dictationer/processor.py:155)
   - Normalizes model names before storing and loading
   - Logs original vs normalized names for transparency

2. **Model Loading**: [`AudioProcessor._load_whisper_model()`](../src/dictationer/processor.py:262)
   - Ensures normalized names are used for actual model loading
   - Provides clear logging of the normalization process

3. **Configuration System**: [`ConfigManager.set()`](../src/dictationer/config.py:209)
   - Automatically normalizes model names when saving preferences
   - Logs normalization for user awareness

4. **Model Detection**: [`ModelDetector.is_model_cached()`](../src/dictationer/config.py:376)
   - Checks cache using both original and normalized names
   - Ensures compatibility with existing cached models

5. **Audio Recording**: [`AudioRecorder.__init__()`](../src/dictationer/audio.py:67)
   - Normalizes model names before passing to AudioProcessor
   - Maintains consistency across the entire system

## Usage Examples

### Direct Usage
```python
from dictationer.config import normalize_model_name

# HuggingFace format names
normalized = normalize_model_name("distil-whisper/distil-large-v3")
print(normalized)  # Output: "distil-large-v3"

normalized = normalize_model_name("openai/whisper-large-v3")
print(normalized)  # Output: "large-v3"

# Standard names remain unchanged
normalized = normalize_model_name("base")
print(normalized)  # Output: "base"
```

### AudioProcessor Usage
```python
from dictationer.processor import AudioProcessor

# Both formats work identically
processor1 = AudioProcessor(model_size="distil-whisper/distil-large-v3")
processor2 = AudioProcessor(model_size="distil-large-v3")

# Both will use the normalized name "distil-large-v3" internally
print(processor1.model_size)  # Output: "distil-large-v3"
print(processor2.model_size)  # Output: "distil-large-v3"
```

### Configuration Usage
```python
from dictationer.config import ConfigManager

config = ConfigManager()

# Set using HuggingFace format
config.set("whisper_model_size", "distil-whisper/distil-large-v3")

# Retrieved as normalized format
model = config.get("whisper_model_size")
print(model)  # Output: "distil-large-v3"
```

## Logging

The system provides comprehensive logging of the normalization process:

```
[PROCESSOR] Model name normalized: 'distil-whisper/distil-large-v3' -> 'distil-large-v3'
[PROCESSOR] Original model: distil-whisper/distil-large-v3
[PROCESSOR] Normalized model: distil-large-v3
[PROCESSOR] Model name normalized for loading: 'distil-whisper/distil-large-v3' -> 'distil-large-v3'
```

## Error Handling

- **Invalid Input**: Non-string inputs are returned unchanged
- **Malformed Names**: Names that don't follow expected patterns are preserved
- **Import Errors**: If normalization function is unavailable, original names are used
- **Edge Cases**: Empty strings, multiple slashes, and other edge cases are handled gracefully

## Testing

The implementation includes comprehensive test suites:

1. **[`test_model_normalization.py`](../test_model_normalization.py)**: Tests the core normalization function
2. **[`test_backward_compatibility.py`](../test_backward_compatibility.py)**: Verifies backward compatibility

Run tests with:
```bash
python test_model_normalization.py
python test_backward_compatibility.py
```

## Benefits

1. **User-Friendly**: Users can copy model names directly from HuggingFace
2. **Transparent**: Clear logging shows what normalization occurred
3. **Compatible**: Works with existing model names and configurations
4. **Consistent**: Ensures the same model name format throughout the system
5. **Robust**: Handles edge cases and errors gracefully

## Future Enhancements

- Support for additional model repositories
- GUI integration for model name validation
- Automatic model availability checking
- Enhanced error messages for unsupported formats