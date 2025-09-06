"""
Template Plugin for Sanskrit Processor
Shows the pattern for creating lean function-based plugins

SECURITY NOTICE: Plugins execute arbitrary Python code. Only use plugins from trusted sources.
Plugin security guidelines:
- Never import untrusted modules or execute external commands
- Validate all inputs before processing  
- Use only safe string operations and regex
- Always handle exceptions gracefully
- Avoid file I/O, network requests, or system calls unless absolutely necessary
"""

def template_plugin(text: str) -> str:
    """
    Template plugin showing the simple function-based pattern.
    
    Plugin functions must:
    1. Take text as input (str)
    2. Return processed text (str) 
    3. Handle errors gracefully (don't raise exceptions)
    4. Follow naming convention: {plugin_name}_plugin
    5. Follow security guidelines above
    
    Args:
        text: Input text to process
        
    Returns:
        Processed text (or original if error occurs)
    """
    try:
        # Input validation for security
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Example: Convert "om" to "Om" at start of sentences
        import re
        result = re.sub(r'\bom\b', 'Om', text, flags=re.IGNORECASE)
        return result
    except Exception:
        # Always return original text on error (fail-safe)
        return text