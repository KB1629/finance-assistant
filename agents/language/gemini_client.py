"""
Gemini API Client for Language Processing
"""

import os
import google.generativeai as genai
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("gemini_client")

class GeminiClient:
    """Client for Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client.
        
        Args:
            api_key: Gemini API key
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 1.5 Flash model (free tier)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info("Gemini client initialized successfully")
    
    def chat_completion(self, messages: list, **kwargs) -> str:
        """Generate chat completion using Gemini.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (ignored for compatibility)
            
        Returns:
            Generated response text
        """
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("Gemini returned empty response")
                return "I apologize, but I'm having trouble generating a response right now."
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"I'm experiencing technical difficulties: {e}"
    
    def _convert_messages_to_prompt(self, messages: list) -> str:
        """Convert OpenAI-style messages to Gemini prompt format.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System Instructions: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def is_available(self) -> bool:
        """Check if Gemini API is available.
        
        Returns:
            True if API key is configured
        """
        return bool(self.api_key)

# Global client instance
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client instance.
    
    Returns:
        GeminiClient instance
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client

def chat_completion(messages: list, **kwargs) -> str:
    """Convenience function for chat completion.
    
    Args:
        messages: List of message dictionaries
        **kwargs: Additional parameters
        
    Returns:
        Generated response text
    """
    client = get_gemini_client()
    return client.chat_completion(messages, **kwargs) 