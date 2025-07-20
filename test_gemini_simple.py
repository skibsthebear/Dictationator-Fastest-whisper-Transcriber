#!/usr/bin/env python3
"""Simple standalone test for Gemini reformatter."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed, using system environment variables")

def main():
    """Test the Gemini reformatter directly."""
    
    # Simple dependency check
    try:
        from dictationer.reformatter.gemini import GeminiReformatter, ReformattingMode
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you've installed: pip install google-generativeai pydantic")
        return
    
    # Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("No GEMINI_API_KEY found!")
        print("Either:")
        print("1. Copy sample.env to .env and add your key")
        print("2. Set GEMINI_API_KEY environment variable")
        return
    
    # Test with sample text
    test_text = "this is a test text with bad grammer and no puncutation it should be fixed by gemini"
    
    print("Testing Gemini Reformatter")
    print("=" * 40)
    print(f"Original text: {test_text}")
    print()
    
    try:
        # Create reformatter
        reformatter = GeminiReformatter(mode=ReformattingMode.GRAMMAR_FIX)
        
        # Test the API call directly (without clipboard stuff)
        print("Sending to Gemini...")
        reformatted = reformatter.reformat_with_gemini(test_text)
        
        if reformatted:
            print("✅ Success!")
            print(f"Reformatted: {reformatted}")
        else:
            print("❌ Failed - check logs")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()