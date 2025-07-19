"""
Voice Recording System - Dictationer

A voice recording system with keyboard hotkey control and threaded architecture.
"""

__version__ = "1.0.0"
__author__ = "Voice Recording System"

from .main import RecordingController

__all__ = ["RecordingController"]