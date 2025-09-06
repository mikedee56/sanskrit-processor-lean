"""
Sacred Content Classifier for detecting mantras, verses, and prayers.

Provides lightweight, rule-based classification to identify sacred content
that requires special formatting preservation during processing.
"""

import re
from typing import Tuple


class SacredContentClassifier:
    """
    Lightweight classifier for sacred content detection.
    Uses simple pattern matching for lean implementation.
    """
    
    MANTRA_INDICATORS = [
        "om", "aum", "ॐ", "hare", "krishna", "rama",
        "shanti", "śānti", "namah", "namaha", "svaha",
        "mani", "padme", "hum", "shiva", "śiva", "gaṇeśa"
    ]
    
    VERSE_INDICATORS = [
        "|", "||", "।", "।।", "chapter", "verse", 
        "shloka", "śloka", "adhyaya", "adhyāya"
    ]
    
    SACRED_SYMBOLS = {
        "|": "|",      # Preserve single pipe
        "||": "||",    # Preserve double pipe  
        "।": "।",      # Devanagari danda
        "।।": "।।",    # Devanagari double danda
        "ॐ": "ॐ",      # Om symbol
        "◦": "◦",      # Sacred bullet
        "○": "○",      # Sacred circle
        "★": "★",      # Sacred star
        "✦": "✦"       # Sacred sparkle
    }
    
    def classify_content(self, text: str) -> str:
        """
        Returns: 'mantra', 'verse', 'prayer', 'commentary', 'regular'
        Optimized for performance - fast path for regular content.
        """
        # Fast path: check for sacred symbols first (most common sacred indicator)
        if any(symbol in text for symbol in ['|', '||', '।', '।।', 'ॐ']):
            return 'verse' if any(pipe in text for pipe in ['|', '||', '।', '।।']) else 'mantra'
        
        # Fast path: if no sacred symbols and no obvious sacred words, likely regular
        text_lower = text.lower()
        if not any(word in text_lower for word in ['om', 'chapter', 'verse', 'mantra', 'hare']):
            return 'regular'
            
        # Slower path: detailed classification for potential sacred content
        mantra_count = sum(1 for indicator in self.MANTRA_INDICATORS if indicator in text_lower)
        if mantra_count >= 2:
            return 'mantra'
            
        # Check for verse indicators  
        if any(indicator in text_lower for indicator in self.VERSE_INDICATORS):
            return 'verse'
            
        return 'regular'
    
    def detect_sacred_content(self, text: str) -> Tuple[str, float]:
        """
        Lightweight sacred content detection with confidence score.
        Returns (content_type, confidence_score)
        """
        confidence = 0.0
        content_type = 'regular'
        
        # Sacred symbols = high confidence
        sacred_symbols_present = [symbol for symbol in self.SACRED_SYMBOLS if symbol in text]
        if sacred_symbols_present:
            content_type = 'verse' if any(pipe in text for pipe in ['|', '||', '।', '।।']) else 'mantra'
            confidence = 0.95
            
        # Multiple mantra keywords = medium confidence
        elif self._mantra_keyword_count(text) >= 2:
            content_type = 'mantra'
            confidence = 0.75
            
        # Verse structure indicators = medium confidence
        elif self._verse_structure_detected(text):
            content_type = 'verse'  
            confidence = 0.70
            
        return content_type, confidence
    
    def _mantra_keyword_count(self, text: str) -> int:
        """Count mantra indicator keywords in text."""
        text_lower = text.lower()
        return sum(1 for indicator in self.MANTRA_INDICATORS if indicator in text_lower)
    
    def _verse_structure_detected(self, text: str) -> bool:
        """Check if text has verse structure patterns."""
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in self.VERSE_INDICATORS)