#!/usr/bin/env python3
"""
Test script to verify virtual environment setup and GPU detection.
"""

import sys
from pathlib import Path

print("Virtual Environment Test")
print("=" * 50)

# Check Python executable
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# Check if we're in a virtual environment
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("[OK] Running in virtual environment")
    print(f"   Base prefix: {sys.base_prefix}")
    print(f"   Current prefix: {sys.prefix}")
else:
    print("[ERROR] NOT running in virtual environment")

print()

# Test PyTorch import
print("Testing PyTorch...")
try:
    import torch
    print(f"[OK] PyTorch imported successfully")
    print(f"   Version: {torch.__version__}")
    print(f"   Location: {torch.__file__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"   CUDA version: {torch.version.cuda}")
        print(f"   GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("   No CUDA GPUs detected")
        
except ImportError as e:
    print(f"[ERROR] PyTorch import failed: {e}")

print()

# Test other dependencies
dependencies = [
    "PySide6",
    "faster_whisper", 
    "transformers",
    "python-dotenv"
]

print("Testing other dependencies...")
for dep in dependencies:
    try:
        __import__(dep.replace("-", "_"))
        print(f"[OK] {dep} - Available")
    except ImportError as e:
        print(f"[ERROR] {dep} - MISSING: {e}")

print()
print("Test complete!")