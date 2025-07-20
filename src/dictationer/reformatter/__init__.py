"""
Reformatter module for dictationer.

Provides text reformatting functionality triggered by holding Ctrl key.
"""

from .controller import ReformatterController

# Import Gemini reformatter if available
try:
    from .gemini import GeminiReformatter, ReformattingMode
    GEMINI_AVAILABLE = True
    __all__ = ["ReformatterController", "GeminiReformatter", "ReformattingMode"]
except ImportError:
    GEMINI_AVAILABLE = False
    __all__ = ["ReformatterController"]