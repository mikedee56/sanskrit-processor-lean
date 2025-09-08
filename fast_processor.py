#!/usr/bin/env python3
"""
Fast Sanskrit Processor - Performance Mode
Streamlined implementation focused on speed over features

Key optimizations:
- Skip sacred content classification  
- Skip plugin execution
- Simplified lexicon processing
- Batch word processing
- Pre-compiled regex patterns
"""

import re
import time
from pathlib import Path
from typing import Tuple, Dict, List
from lexicons.hybrid_lexicon_loader import HybridLexiconLoader


class FastSanskritProcessor:
    """High-performance Sanskrit processor with minimal features."""
    
    def __init__(self, lexicon_dir: Path):
        """Initialize with essential components only."""
        self.lexicon_dir = lexicon_dir
        
        # Load lexicon with database support
        config = {'database': {'enabled': True, 'path': 'data/sanskrit_terms.db'}}
        self.lexicon_loader = HybridLexiconLoader(lexicon_dir, config)
        
        # Pre-compile regex patterns for performance
        self._word_pattern = re.compile(r'\b\w+\b')
        self._whitespace_pattern = re.compile(r'[ \t]+')
        
        # Cache for frequently accessed terms
        self._term_cache = {}
        
    def process_text(self, text: str) -> Tuple[str, int]:
        """Fast text processing - optimized for speed."""
        corrections = 0
        
        # Normalize whitespace (single pass)
        text = self._whitespace_pattern.sub(' ', text).strip()
        
        # Split into words and process in batch
        words = text.split()
        processed_words = []
        
        for word in words:
            # Process word with punctuation preservation
            processed_word = self._process_word_fast(word)
            processed_words.append(processed_word)
            if processed_word != word:
                corrections += 1
        
        return ' '.join(processed_words), corrections
    
    def _process_word_fast(self, word: str) -> str:
        """Ultra-fast word processing with aggressive caching."""
        # Check cache first - most important optimization
        if word in self._term_cache:
            return self._term_cache[word]
        
        # Quick check - if no lowercase letters, skip processing
        if not any(c.islower() for c in word):
            self._term_cache[word] = word
            return word
        
        # Extract word without punctuation (optimized)
        if word.isalpha():
            # Pure alphabetic word - no punctuation
            prefix, clean_word, suffix = '', word, ''
        else:
            # Has punctuation - use regex
            match = re.match(r'^(\W*?)(\w+)(\W*?)$', word)
            if not match:
                self._term_cache[word] = word
                return word
            prefix, clean_word, suffix = match.groups()
        
        clean_lower = clean_word.lower()
        
        # Try corrections first (most common) - optimized lookups
        try:
            if clean_lower in self.lexicon_loader.corrections:
                entry = self.lexicon_loader.corrections[clean_lower]
                corrected = entry.get('original_term', clean_word)
                # Preserve original capitalization pattern
                if clean_word[0].isupper() and not corrected[0].isupper():
                    corrected = corrected.capitalize()
                result = prefix + corrected + suffix
            # Try proper nouns
            elif clean_lower in self.lexicon_loader.proper_nouns:
                entry = self.lexicon_loader.proper_nouns[clean_lower]
                corrected = entry.get('term', clean_word)
                result = prefix + corrected + suffix
            else:
                result = word
        except (KeyError, AttributeError):
            # Fallback for any lookup errors
            result = word
        
        # Cache result (limit cache size to prevent memory issues)
        if len(self._term_cache) < 5000:
            self._term_cache[word] = result
        return result
    
    def process_batch(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Process multiple texts in batch for better performance."""
        return [self.process_text(text) for text in texts]
    
    def get_stats(self) -> Dict:
        """Get processing statistics."""
        return {
            'cache_size': len(self._term_cache),
            'lexicon_stats': self.lexicon_loader.get_stats() if hasattr(self.lexicon_loader, 'get_stats') else {}
        }


def benchmark_fast_processor():
    """Benchmark the fast processor."""
    print('=== Fast Processor Benchmark ===')
    
    processor = FastSanskritProcessor(Path('lexicons'))
    
    # Test segments
    test_segments = [
        'This is a simple test segment',
        'srimad bhagavatam chapter 1 verse 1', 
        'krishna speaks about yoga and dharma',
        'Om namah shivaya meditation practice',
        'The bhagavad gita teaches about karma yoga',
        'In vrindavan krishna plays with gopas',
        'Advaita vedanta philosophy by adi shankara',
        'Sri ramana maharshi teaches self inquiry',
        'The upanishads contain ancient wisdom', 
        'Yoga means union of individual and universal consciousness'
    ]
    
    # Warm up
    for segment in test_segments[:2]:
        processor.process_text(segment)
    
    # Measure performance with larger batch
    start_time = time.time()
    results = processor.process_batch(test_segments * 20)  # 200 segments
    end_time = time.time()
    
    processing_time = end_time - start_time
    segment_count = len(test_segments) * 20
    total_corrections = sum(corrections for _, corrections in results)
    segments_per_second = segment_count / processing_time
    
    print(f'Segments processed: {segment_count}')
    print(f'Total corrections: {total_corrections}')
    print(f'Processing time: {processing_time:.4f} seconds')
    print(f'Performance: {segments_per_second:.2f} segments/second')
    print(f'Target: 2,600 segments/second')
    
    gap = 2600 / segments_per_second
    print(f'Performance gap: {gap:.1f}x slower than target')
    
    if gap < 10:
        print('✅ SUCCESS: Gap under 10x (AC2 met)')
    else:
        print(f'❌ Need {gap/10:.1f}x more improvement for AC2')
        
    if segments_per_second >= 2000:
        print('✅ SUCCESS: Above 2,000 segments/second (AC1 met)')
    else:
        print(f'❌ Need {2000/segments_per_second:.1f}x improvement for AC1')
    
    print(f'Cache stats: {processor.get_stats()}')
    processor.lexicon_loader.close()
    
    return segments_per_second


if __name__ == "__main__":
    benchmark_fast_processor()