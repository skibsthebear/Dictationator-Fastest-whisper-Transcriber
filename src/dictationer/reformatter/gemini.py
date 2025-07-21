#!/usr/bin/env python3
"""
Gemini-powered text reformatter for dictationer.

This module integrates with Google's Gemini API to reformat selected text
using AI, then pastes the reformatted version.
"""

import os
import time
import json
import logging
import keyboard
import pyperclip
from typing import Optional, Dict, Any
from enum import Enum
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from the project root (3 levels up from this file)
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(env_path)
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Import the ClipboardPaster from dictationer
try:
    # Try relative import (when used as module)
    from ..paster import ClipboardPaster
except ImportError:
    # Try absolute import (when run standalone)
    import sys
    from pathlib import Path
    # Add the src directory to path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from dictationer.paster import ClipboardPaster

# Google Generative AI
try:
    import google.generativeai as genai
    from pydantic import BaseModel
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    BaseModel = None

logger = logging.getLogger(__name__)


class ReformattingMode(Enum):
    """Different modes for text reformatting."""
    GRAMMAR_FIX = "grammar_fix"
    FORMAL_TONE = "formal_tone"
    CASUAL_TONE = "casual_tone"
    BULLET_POINTS = "bullet_points"
    PARAGRAPH = "paragraph"
    CONCISE = "concise"
    ELABORATE = "elaborate"


# Pydantic schema for structured response
class FormattedTextResponse(BaseModel):
    """Schema for Gemini's formatted text response."""
    formatted_text: str


class GeminiReformatter:
    """Reformats text using Google's Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, mode: ReformattingMode = ReformattingMode.GRAMMAR_FIX, 
                 show_status_callback=None, hide_status_callback=None):
        """
        Initialize the Gemini reformatter.
        
        Args:
            api_key: Google API key for Gemini. If None, will try to get from GEMINI_API_KEY env var
            mode: The reformatting mode to use
            show_status_callback: Function to call when showing status window
            hide_status_callback: Function to call when hiding status window
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai and pydantic packages not installed. Run: pip install google-generativeai pydantic")
        
        # Get API key
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No Gemini API key found. Either:\n"
                "1. Create a .env file with GEMINI_API_KEY=your-key-here, or\n"
                "2. Set GEMINI_API_KEY environment variable, or\n"
                "3. Pass api_key parameter to constructor\n"
                "Get your API key from: https://aistudio.google.com/"
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Initialize components
        self.mode = mode
        self.paster = ClipboardPaster()
        self._original_clipboard = None
        
        # Status window callbacks
        self.show_status_callback = show_status_callback
        self.hide_status_callback = hide_status_callback
        
        logger.info(f"GeminiReformatter initialized with mode: {mode.value}")
    
    def get_prompt(self, text: str, mode: ReformattingMode) -> str:
        """
        Get the appropriate prompt for the reformatting mode.
        
        Args:
            text: The text to reformat
            mode: The reformatting mode
            
        Returns:
            The prompt to send to Gemini
        """
        prompts = {
            ReformattingMode.GRAMMAR_FIX: f"""Fix the grammar and spelling in the following text. 
Keep the same tone and style, just correct any errors. If you detect a long paragraph make sure your reponse has spacing and line breaks with best practices
Respond with a JSON object containing the corrected text in the 'formatted_text' field.

Text to fix:
{text}""",

            ReformattingMode.FORMAL_TONE: f"""Rewrite the following text in a formal, professional tone.
Respond with a JSON object containing the formal text in the 'formatted_text' field.

Text to reformat:
{text}""",

            ReformattingMode.CASUAL_TONE: f"""Rewrite the following text in a casual, friendly tone.
Respond with a JSON object containing the casual text in the 'formatted_text' field.

Text to reformat:
{text}""",

            ReformattingMode.BULLET_POINTS: f"""Convert the following text into clear bullet points.
Respond with a JSON object containing the bullet points in the 'formatted_text' field.

Text to convert:
{text}""",

            ReformattingMode.PARAGRAPH: f"""Convert the following text into a well-structured paragraph.
Respond with a JSON object containing the paragraph in the 'formatted_text' field.

Text to convert:
{text}""",

            ReformattingMode.CONCISE: f"""Make the following text more concise while keeping the main points.
Respond with a JSON object containing the concise text in the 'formatted_text' field.

Text to shorten:
{text}""",

            ReformattingMode.ELABORATE: f"""Elaborate on the following text with more detail and explanation.
Respond with a JSON object containing the elaborated text in the 'formatted_text' field.

Text to elaborate:
{text}"""
        }
        
        return prompts.get(mode, prompts[ReformattingMode.GRAMMAR_FIX])
    
    def copy_selected_text(self) -> Optional[str]:
        """
        Copy currently selected text using Ctrl+C.
        
        Returns:
            The copied text, or None if failed
        """
        try:
            # Save original clipboard first
            self._original_clipboard = pyperclip.paste()
            logger.debug(f"Saved original clipboard: {len(self._original_clipboard or '')} chars")
            
            # Clear clipboard to ensure we get fresh copy
            pyperclip.copy("")
            time.sleep(0.1)
            
            # Trigger Ctrl+C to copy selected text
            keyboard.send('ctrl+c')
            logger.debug("Sent Ctrl+C")
            
            # Wait for clipboard to update
            time.sleep(0.2)
            
            # Get the copied text
            copied_text = pyperclip.paste()
            
            if not copied_text:
                logger.warning("No text was copied (clipboard empty)")
                # Restore original clipboard
                if self._original_clipboard:
                    pyperclip.copy(self._original_clipboard)
                return None
            
            logger.info(f"Copied {len(copied_text)} characters")
            return copied_text
            
        except Exception as e:
            logger.error(f"Failed to copy selected text: {e}")
            # Try to restore original clipboard
            if self._original_clipboard:
                try:
                    pyperclip.copy(self._original_clipboard)
                except:
                    pass
            return None
    
    def reformat_with_gemini(self, text: str) -> Optional[str]:
        """
        Send text to Gemini API for reformatting.
        
        Args:
            text: The text to reformat
            
        Returns:
            The reformatted text, or None if failed
        """
        try:
            # Generate prompt
            prompt = self.get_prompt(text, self.mode)
            
            logger.info(f"Sending text to Gemini for {self.mode.value} reformatting...")
            
            # Show status window before API call
            if self.show_status_callback:
                self.show_status_callback()
            
            # Generate response using the correct API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=FormattedTextResponse
                )
            )
            
            # Extract the formatted text using structured response
            if hasattr(response, 'parsed') and response.parsed:
                # Use the structured response
                reformatted = response.parsed.formatted_text
                logger.info(f"Successfully reformatted text: {len(reformatted)} chars")
                return reformatted
            else:
                # Fallback to text parsing if structured response fails
                logger.warning("No structured response, trying to parse JSON manually")
                response_text = response.text.strip()
                logger.debug(f"Raw Gemini response: {response_text}")
                
                # Sometimes Gemini adds markdown code blocks, remove them
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                data = json.loads(response_text)
                reformatted = data.get("formatted_text", "")
                
                if not reformatted:
                    logger.error("No 'formatted_text' field in Gemini response")
                    return None
                
                logger.info(f"Successfully reformatted text: {len(reformatted)} chars")
                return reformatted
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
        finally:
            # Hide status window after API call completes (success or failure)
            if self.hide_status_callback:
                self.hide_status_callback()
    
    def process(self) -> bool:
        """
        Complete reformatting workflow:
        1. Copy selected text
        2. Send to Gemini for reformatting
        3. Paste reformatted text
        4. Restore original clipboard
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting Gemini reformatting process...")
        
        # Step 1: Copy selected text
        selected_text = self.copy_selected_text()
        if not selected_text:
            logger.error("No text selected or copy failed")
            return False
        
        # Step 2: Send to Gemini
        reformatted_text = self.reformat_with_gemini(selected_text)
        if not reformatted_text:
            logger.error("Gemini reformatting failed")
            # Restore original clipboard
            if self._original_clipboard:
                pyperclip.copy(self._original_clipboard)
            return False
        
        # Step 3: Use ClipboardPaster to paste the reformatted text
        # The paster will handle clipboard restoration
        success = self.paster.paste_text(reformatted_text, restore_delay=0.5)
        
        if success:
            logger.info("Successfully pasted reformatted text")
        else:
            logger.error("Failed to paste reformatted text")
        
        # Step 4: Ensure original clipboard is restored
        # (ClipboardPaster should handle this, but let's be safe)
        if self._original_clipboard and not success:
            try:
                pyperclip.copy(self._original_clipboard)
            except:
                pass
        
        return success
    
    def set_mode(self, mode: ReformattingMode):
        """Change the reformatting mode."""
        self.mode = mode
        logger.info(f"Reformatting mode changed to: {mode.value}")


def main():
    """Test the Gemini reformatter."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: Please set GEMINI_API_KEY environment variable")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    try:
        # Create reformatter
        reformatter = GeminiReformatter(mode=ReformattingMode.GRAMMAR_FIX)
        
        print("Gemini Reformatter Test")
        print("=" * 50)
        print("1. Select some text in any application")
        print("2. Press Enter here to reformat it")
        print("3. The reformatted text will be pasted automatically")
        print()
        print("Available modes:")
        for mode in ReformattingMode:
            print(f"  - {mode.value}")
        print()
        
        input("Press Enter when ready (make sure text is selected)...")
        
        # Process
        if reformatter.process():
            print("✅ Reformatting completed successfully!")
        else:
            print("❌ Reformatting failed!")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()