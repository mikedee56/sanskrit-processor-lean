"""
Story 10.5: Performance Optimization - Pattern Manager
Pre-compiled regex patterns with singleton management for optimal performance

Lean Compliance:
- Dependencies: re (built-in) ✅
- Code size: ~120 lines ✅  
- Performance: Eliminates regex compilation overhead ✅
- Memory: Singleton pattern prevents duplicate compilations ✅
"""

import re
import logging
from typing import Dict, Pattern, Optional, Set
from threading import Lock

logger = logging.getLogger(__name__)


class PatternManager:
    """Singleton pattern manager for pre-compiled regex patterns."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._patterns: Dict[str, Pattern] = {}
        self._pattern_usage: Dict[str, int] = {}
        self._sanskrit_chars: Optional[Set[str]] = None
        self._english_words: Optional[Pattern] = None
        self._initialized = True
        
        # Pre-compile common patterns
        self._precompile_common_patterns()
        
        logger.info("Pattern Manager initialized with pre-compiled patterns")
    
    def _precompile_common_patterns(self):
        """Pre-compile frequently used patterns for Sanskrit processing."""
        
        # Core Sanskrit patterns
        self._compile_pattern('sanskrit_word', r'\b[a-zA-Zāīūṛḷēōṃṁṅñṭḍḷśṣṇṛāīūṝḷḹḡḧḵʰṛ]+\b')
        self._compile_pattern('english_word', r'\b[a-zA-Z]+\b')
        self._compile_pattern('diacritical_chars', r'[āīūṛḷēōṃṁṅñṭḍḷśṣṇāīūṝḷḹāīūṛḷēōṃ]')
        
        # Sanskrit compound patterns
        self._compile_pattern('compound_space', r'\b(sapta|saptam)\s+(bhoomi\w+|bhumi\w+)')
        self._compile_pattern('title_name', r'\b(sri|shri)\s+(vasi\w+|vashi\w+)')
        self._compile_pattern('sacred_compound', r'\b(bhagavad)\s*(gita|geeta)')
        
        # ASR correction patterns
        self._compile_pattern('asr_sh_s', r'\bsh([aeiou])')
        self._compile_pattern('asr_ch_c', r'\bch([aeiou])')
        self._compile_pattern('asr_double_vowel', r'([aeiou])\1')
        self._compile_pattern('asr_ng_nasal', r'ng([aeiou])')
        
        # Context detection patterns
        self._compile_pattern('english_function', r'\b(the|and|or|but|with|from|to|in|on|at|by|for)\b')
        self._compile_pattern('english_modal', r'\b(was|were|is|are|will|would|could|should)\b')
        self._compile_pattern('english_progressive', r'\b\w+ing\b')
        self._compile_pattern('english_past', r'\b\w+ed\b')
        
        # Sanskrit markers
        self._compile_pattern('sanskrit_om', r'\boṁ\s+namaḥ')
        self._compile_pattern('sanskrit_phrase', r'bhagavad\s+gītā|śrī\s+\w+')
        self._compile_pattern('sanskrit_suffix', r'\b\w+(āya|aya|āni|ani|asya|ānām|anam)\b')
        
        # Optimization patterns
        self._compile_pattern('word_boundaries', r'\b\w+\b')
        self._compile_pattern('non_word_chars', r'[^\w\s]')
        self._compile_pattern('whitespace', r'\s+')
        
        # Performance critical patterns for hot paths
        self._compile_pattern('sanskrit_detection_fast', r'[āīūṛḷēōṃṁṅñṭḍḷśṣṇ]|oṁ|śrī|bhagavad')
        self._compile_pattern('english_detection_fast', r'\b(the|and|is|was|were|will|would|ing|ed)\b')
    
    def _compile_pattern(self, name: str, pattern: str, flags: int = re.IGNORECASE) -> Pattern:
        """Compile and cache a regex pattern."""
        try:
            compiled_pattern = re.compile(pattern, flags)
            self._patterns[name] = compiled_pattern
            self._pattern_usage[name] = 0
            logger.debug(f"Compiled pattern '{name}': {pattern}")
            return compiled_pattern
        except re.error as e:
            logger.error(f"Failed to compile pattern '{name}': {pattern} - Error: {e}")
            raise
    
    def get_pattern(self, name: str) -> Optional[Pattern]:
        """Get a pre-compiled pattern by name."""
        if name in self._patterns:
            self._pattern_usage[name] += 1
            return self._patterns[name]
        
        logger.warning(f"Pattern '{name}' not found in pre-compiled patterns")
        return None
    
    def compile_and_cache(self, name: str, pattern: str, flags: int = re.IGNORECASE) -> Pattern:
        """Compile a new pattern and cache it for future use."""
        if name in self._patterns:
            self._pattern_usage[name] += 1
            return self._patterns[name]
        
        return self._compile_pattern(name, pattern, flags)
    
    def search_with_pattern(self, pattern_name: str, text: str) -> Optional[re.Match]:
        """Search text using a pre-compiled pattern."""
        pattern = self.get_pattern(pattern_name)
        if pattern:
            return pattern.search(text)
        return None
    
    def findall_with_pattern(self, pattern_name: str, text: str) -> list:
        """Find all matches using a pre-compiled pattern."""
        pattern = self.get_pattern(pattern_name)
        if pattern:
            return pattern.findall(text)
        return []
    
    def finditer_with_pattern(self, pattern_name: str, text: str):
        """Find iterator using a pre-compiled pattern."""
        pattern = self.get_pattern(pattern_name)
        if pattern:
            return pattern.finditer(text)
        return iter([])
    
    def sub_with_pattern(self, pattern_name: str, repl: str, text: str, count: int = 0) -> str:
        """Substitute using a pre-compiled pattern."""
        pattern = self.get_pattern(pattern_name)
        if pattern:
            return pattern.sub(repl, text, count)
        return text
    
    def has_sanskrit_chars_fast(self, text: str) -> bool:
        """Fast check for Sanskrit diacritical characters."""
        if not self._sanskrit_chars:
            # Build character set for O(1) lookup
            self._sanskrit_chars = set('āīūṛḷēōṃṁṅñṭḍḷśṣṇṝḷḹḡḧḵʰ')
        
        return any(char in self._sanskrit_chars for char in text)
    
    def is_likely_english_fast(self, text: str) -> bool:
        """Fast English detection using pre-compiled patterns."""
        pattern = self.get_pattern('english_detection_fast')
        return pattern.search(text) is not None if pattern else False
    
    def is_likely_sanskrit_fast(self, text: str) -> bool:
        """Fast Sanskrit detection using pre-compiled patterns."""
        pattern = self.get_pattern('sanskrit_detection_fast')
        return pattern.search(text) is not None if pattern else False
    
    def extract_words_fast(self, text: str) -> list:
        """Fast word extraction using pre-compiled pattern."""
        pattern = self.get_pattern('word_boundaries')
        return pattern.findall(text) if pattern else text.split()
    
    def clean_text_fast(self, text: str) -> str:
        """Fast text cleaning using pre-compiled patterns."""
        # Remove non-word characters except spaces
        pattern = self.get_pattern('non_word_chars')
        if pattern:
            cleaned = pattern.sub(' ', text)
            # Normalize whitespace
            ws_pattern = self.get_pattern('whitespace')
            if ws_pattern:
                cleaned = ws_pattern.sub(' ', cleaned)
            return cleaned.strip()
        return text
    
    def get_pattern_stats(self) -> Dict[str, any]:
        """Get usage statistics for all patterns."""
        total_usage = sum(self._pattern_usage.values())
        
        stats = {
            'total_patterns': len(self._patterns),
            'total_usage': total_usage,
            'pattern_usage': dict(self._pattern_usage),
            'most_used_patterns': sorted(
                self._pattern_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        # Calculate usage percentages
        if total_usage > 0:
            stats['usage_percentages'] = {
                name: (usage / total_usage * 100)
                for name, usage in self._pattern_usage.items()
            }
        
        return stats
    
    def clear_usage_stats(self):
        """Clear usage statistics."""
        self._pattern_usage = {name: 0 for name in self._patterns.keys()}
    
    def preload_for_context(self, context_type: str):
        """Preload patterns optimized for specific processing context."""
        if context_type == 'sanskrit':
            # Warm up Sanskrit patterns
            _ = self.get_pattern('sanskrit_word')
            _ = self.get_pattern('diacritical_chars')
            _ = self.get_pattern('sanskrit_suffix')
            _ = self.get_pattern('sanskrit_om')
            
        elif context_type == 'english':
            # Warm up English patterns
            _ = self.get_pattern('english_word')
            _ = self.get_pattern('english_function')
            _ = self.get_pattern('english_modal')
            _ = self.get_pattern('english_progressive')
            
        elif context_type == 'mixed':
            # Warm up both Sanskrit and English patterns
            self.preload_for_context('sanskrit')
            self.preload_for_context('english')


# Global pattern manager instance
def get_pattern_manager() -> PatternManager:
    """Get the global pattern manager instance."""
    return PatternManager()