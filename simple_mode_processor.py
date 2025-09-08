#!/usr/bin/env python3
"""
Simple Mode Sanskrit Processor - Maximum Performance
Minimal feature set focused purely on speed

Optimizations:
- YAML-only lexicon (no database overhead)
- No proper noun processing
- No compound processing
- Pre-compiled correction dictionary
- Minimal string operations
"""

import re
import time
import yaml
from pathlib import Path
from typing import Tuple, Dict, List


class SimpleModeProcessor:
    """Ultra-fast processor with minimal features."""
    
    def __init__(self, lexicon_dir: Path):
        """Initialize with pre-loaded corrections dictionary."""
        # Load only corrections.yaml (fastest)
        corrections_file = lexicon_dir / 'corrections.yaml'
        self.corrections_dict = {}
        
        if corrections_file.exists():
            with open(corrections_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                # Pre-process into simple dict for O(1) lookups
                for entry in data.get('entries', []):
                    original = entry.get('original_term', '').lower()
                    if original:
                        self.corrections_dict[original] = entry.get('original_term', '')
                        # Add variations
                        for variation in entry.get('variations', []):
                            self.corrections_dict[variation.lower()] = entry.get('original_term', '')
        
        # Pre-compile patterns
        self._word_boundary = re.compile(r'\b\w+\b')
        self._whitespace = re.compile(r'\s+')
        
        print(f"Loaded {len(self.corrections_dict)} correction entries")
    
    def process_text_simple(self, text: str) -> Tuple[str, int]:
        """Ultra-simple text processing."""
        corrections = 0
        
        # Normalize whitespace
        text = self._whitespace.sub(' ', text.strip())
        
        # Process word by word with minimal overhead
        words = text.split()
        result_words = []
        
        for word in words:
            clean_word = word.strip('.,!?;:"()[]{}').lower()
            if clean_word in self.corrections_dict:
                # Apply correction, preserve capitalization
                corrected = self.corrections_dict[clean_word]
                if word[0].isupper():
                    corrected = corrected.capitalize()
                result_words.append(corrected)
                corrections += 1
            else:
                result_words.append(word)
        
        return ' '.join(result_words), corrections
    
    def benchmark_simple_mode():
        """Benchmark simple mode processor."""
        print('=== Simple Mode Processor Benchmark ===')
        
        processor = SimpleModeProcessor(Path('lexicons'))
        
        # Test segments - mix of Sanskrit and English
        test_segments = [
            'This is a simple test segment',
            'krishna speaks about yoga and dharma', 
            'Om meditation practice',
            'The gita teaches about yoga',
            'In vrindavan gopas play',
            'vedanta philosophy teachings',
            'maharshi teaches inquiry',
            'upanishads contain wisdom',
            'yoga means union consciousness',
            'Simple English text without Sanskrit terms'
        ]
        
        # Measure performance with large batch
        start_time = time.time()
        total_corrections = 0
        
        for _ in range(50):  # 500 total segments
            for segment in test_segments:
                result, corrections = processor.process_text_simple(segment)
                total_corrections += corrections
        
        end_time = time.time()
        
        processing_time = end_time - start_time
        segment_count = len(test_segments) * 50
        segments_per_second = segment_count / processing_time
        
        print(f'Segments processed: {segment_count}')
        print(f'Total corrections: {total_corrections}')
        print(f'Processing time: {processing_time:.4f} seconds')
        print(f'Performance: {segments_per_second:.2f} segments/second')
        print(f'Target: 2,600 segments/second')
        
        gap = 2600 / segments_per_second
        print(f'Performance gap: {gap:.1f}x slower than target')
        
        # Check acceptance criteria
        if gap < 10:
            print('✅ SUCCESS: Gap under 10x (AC2 met)')
        else:
            print(f'❌ Need {gap/10:.1f}x more improvement for AC2')
            
        if segments_per_second >= 2000:
            print('✅ SUCCESS: Above 2,000 segments/second (AC1 met)')  
        else:
            print(f'❌ Need {2000/segments_per_second:.1f}x improvement for AC1')
        
        return segments_per_second


def benchmark_simple_mode():
    """Benchmark simple mode processor."""
    print('=== Simple Mode Processor Benchmark ===')
    
    processor = SimpleModeProcessor(Path('lexicons'))
    
    # Test segments - mix of Sanskrit and English
    test_segments = [
        'This is a simple test segment',
        'krishna speaks about yoga and dharma', 
        'Om meditation practice',
        'The gita teaches about yoga',
        'In vrindavan gopas play',
        'vedanta philosophy teachings',
        'maharshi teaches inquiry',
        'upanishads contain wisdom',
        'yoga means union consciousness',
        'Simple English text without Sanskrit terms'
    ]
    
    # Measure performance with large batch
    start_time = time.time()
    total_corrections = 0
    
    for _ in range(50):  # 500 total segments
        for segment in test_segments:
            result, corrections = processor.process_text_simple(segment)
            total_corrections += corrections
    
    end_time = time.time()
    
    processing_time = end_time - start_time
    segment_count = len(test_segments) * 50
    segments_per_second = segment_count / processing_time
    
    print(f'Segments processed: {segment_count}')
    print(f'Total corrections: {total_corrections}')
    print(f'Processing time: {processing_time:.4f} seconds')
    print(f'Performance: {segments_per_second:.2f} segments/second')
    print(f'Target: 2,600 segments/second')
    
    gap = 2600 / segments_per_second
    print(f'Performance gap: {gap:.1f}x slower than target')
    
    # Check acceptance criteria
    if gap < 10:
        print('✅ SUCCESS: Gap under 10x (AC2 met)')
    else:
        print(f'❌ Need {gap/10:.1f}x more improvement for AC2')
        
    if segments_per_second >= 2000:
        print('✅ SUCCESS: Above 2,000 segments/second (AC1 met)')  
    else:
        print(f'❌ Need {2000/segments_per_second:.1f}x improvement for AC1')
    
    return segments_per_second


if __name__ == "__main__":
    benchmark_simple_mode()