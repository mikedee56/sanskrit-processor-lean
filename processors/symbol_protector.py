"""
Sacred Symbol Protector for preserving sacred symbols during text processing.

Prevents corruption of sacred symbols like |, ||, ॐ during lexicon corrections
by using placeholder replacement strategy.
"""

from typing import Dict, Tuple
from .sacred_classifier import SacredContentClassifier


class SacredSymbolProtector:
    """
    Simple symbol protection system for sacred content.
    Prevents corruption during text processing.
    """
    
    # Symbol protection mapping with unique placeholders
    SYMBOL_PROTECTION_MAP = {
        # Sacred punctuation
        "||": "__PIPE_DOUBLE__",   # Must come before single pipe
        "|": "__PIPE_SINGLE__",
        "।।": "__DANDA_DOUBLE__",
        "।": "__DANDA_SINGLE__",
        
        # Sacred symbols
        "ॐ": "__OM_SYMBOL__",
        "◦": "__SACRED_BULLET__",
        "○": "__SACRED_CIRCLE__",
        "★": "__SACRED_STAR__",
        "✦": "__SACRED_SPARKLE__",
        
        # Traditional spacing markers
        "   ": "__TRIPLE_SPACE__"  # Preserve significant spacing
    }
    
    def __init__(self):
        self.protected_symbols = self.SYMBOL_PROTECTION_MAP.copy()
        self.symbol_placeholders = {}
        
    def protect_symbols(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace sacred symbols with placeholders before processing.
        Returns (protected_text, restoration_map).
        """
        protected_text = text
        restoration_map = {}
        
        # Process symbols in order (longer patterns first to avoid conflicts)
        for symbol in sorted(self.protected_symbols.keys(), key=len, reverse=True):
            if symbol in text:
                placeholder = self.protected_symbols[symbol]
                protected_text = protected_text.replace(symbol, placeholder)
                restoration_map[placeholder] = symbol
                
        return protected_text, restoration_map
        
    def restore_symbols(self, text: str, restoration_map: Dict[str, str]) -> str:
        """Restore sacred symbols from placeholders."""
        restored_text = text
        for placeholder, symbol in restoration_map.items():
            restored_text = restored_text.replace(placeholder, symbol)
        return restored_text
    
    def is_sacred_symbol_present(self, text: str) -> bool:
        """Check if text contains any sacred symbols that need protection."""
        return any(symbol in text for symbol in self.protected_symbols.keys())
    
    def get_protected_symbols_in_text(self, text: str) -> list:
        """Return list of sacred symbols found in the text."""
        found_symbols = []
        for symbol in self.protected_symbols.keys():
            if symbol in text:
                found_symbols.append(symbol)
        return found_symbols