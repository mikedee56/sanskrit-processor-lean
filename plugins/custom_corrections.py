"""
Custom Corrections Plugin
Simple function-based plugin for domain-specific text corrections

SECURITY: This plugin follows security best practices:
- No external file access or network requests
- Input validation and safe string operations only
- Graceful error handling without system exposure
"""
import re

def custom_corrections_plugin(text: str) -> str:
    """
    Apply custom domain-specific corrections.
    This is a simple function-based plugin following lean architecture and security guidelines.
    """
    try:
        # Input validation for security
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Example custom corrections - safe static data only
        corrections = {
            'arjun': 'Arjuna',
            'krishn': 'Krishna', 
            'bhagvad': 'Bhagavad',
            'geeta': 'Gita',
            'vedant': 'Vedanta',
            'upanishad': 'Upanishads'
        }
        
        result = text
        for incorrect, correct in corrections.items():
            # Use word boundaries to avoid partial matches - secure regex
            pattern = r'\b' + re.escape(incorrect) + r'\b'
            result = re.sub(pattern, correct, result, flags=re.IGNORECASE)
        
        return result
    except Exception:
        # Security: Always return original text on any error
        return text