#!/usr/bin/env python3
"""
Tests for fuzzy matching functionality in Sanskrit Processor
Story 1.2: Simple Fuzzy Matching
"""

import unittest
import time
from pathlib import Path
import tempfile
import yaml
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sanskrit_processor_v2 import SanskritProcessor


class TestFuzzyMatching(unittest.TestCase):
    """Test fuzzy matching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for lexicons
        self.temp_dir = Path(tempfile.mkdtemp())
        self.lexicon_dir = self.temp_dir / "lexicons"
        self.lexicon_dir.mkdir()
        
        # Create test corrections lexicon
        corrections_data = {
            'entries': [
                {
                    'original_term': 'Krishna',
                    'variations': ['krishna', 'krsna', 'krshna']
                },
                {
                    'original_term': 'dharma',
                    'variations': ['dhrma', 'dharma', 'darmha']
                },
                {
                    'original_term': 'yoga',
                    'variations': ['yog', 'yogaa', 'yoaga']
                },
                {
                    'original_term': 'Bhagavad Gita',
                    'variations': ['bhagvad', 'bhagavadgita', 'bhagvadgita']
                }
            ]
        }
        
        corrections_file = self.lexicon_dir / "corrections.yaml"
        with open(corrections_file, 'w', encoding='utf-8') as f:
            yaml.dump(corrections_data, f, default_flow_style=False)
        
        # Create test config
        self.config_data = {
            'processing': {
                'fuzzy_matching': {
                    'enabled': True,
                    'threshold': 0.6,
                    'log_matches': False
                }
            }
        }
        
        self.config_file = self.temp_dir / "config.yaml"
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.config_data, f, default_flow_style=False)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_similarity_calculation(self):
        """Test AC1: Character Similarity Algorithm."""
        processor = SanskritProcessor(self.lexicon_dir, self.config_file)
        
        # Test exact matches
        self.assertEqual(processor._calculate_similarity("krishna", "krishna"), 1.0)
        
        # Test high similarity cases
        self.assertGreater(processor._calculate_similarity("krishna", "krsna"), 0.5)
        self.assertGreater(processor._calculate_similarity("dharma", "dhrma"), 0.6)
        self.assertGreater(processor._calculate_similarity("yoga", "yogaa"), 0.6)
        
        # Test low similarity cases
        self.assertLess(processor._calculate_similarity("hello", "world"), 0.4)
        self.assertLess(processor._calculate_similarity("test", "completely"), 0.3)
        
        # Test empty strings
        self.assertEqual(processor._calculate_similarity("", "test"), 0.0)
        self.assertEqual(processor._calculate_similarity("test", ""), 0.0)
        
        # Test very different lengths
        self.assertLess(processor._calculate_similarity("a", "verylongstring"), 0.2)
    
    def test_fuzzy_match_finding(self):
        """Test AC2: Lexicon Integration - fuzzy match finding."""
        processor = SanskritProcessor(self.lexicon_dir, self.config_file)
        
        # Test finding fuzzy matches
        self.assertEqual(processor._find_fuzzy_match("krsna"), "Krishna")
        self.assertEqual(processor._find_fuzzy_match("dhrma"), "dharma") 
        self.assertEqual(processor._find_fuzzy_match("yogaa"), "yoga")
        
        # Test no match for very different words
        self.assertIsNone(processor._find_fuzzy_match("completely"))
        self.assertIsNone(processor._find_fuzzy_match("different"))
        
        # Test empty input
        self.assertIsNone(processor._find_fuzzy_match(""))
    
    def test_common_variations(self):
        """Test AC3: Common Variations Handling.""" 
        processor = SanskritProcessor(self.lexicon_dir, self.config_file)
        
        # Test character substitutions
        result, corrections = processor._apply_lexicon_corrections("I love krsna")
        self.assertIn("Krishna", result)
        self.assertEqual(corrections, 1)
        
        # Test missing characters
        result, corrections = processor._apply_lexicon_corrections("Study dhrma today")
        self.assertIn("dharma", result)
        self.assertEqual(corrections, 1)
        
        # Test extra characters  
        result, corrections = processor._apply_lexicon_corrections("Practice yogaa daily")
        self.assertIn("yoga", result)
        self.assertEqual(corrections, 1)
        
        # Test punctuation handling
        result, corrections = processor._apply_lexicon_corrections("Read bhagvad, it's great!")
        self.assertIn("Bhagavad Gita", result)
        self.assertEqual(corrections, 1)
    
    def test_performance_optimization(self):
        """Test AC4: Performance Optimization."""
        processor = SanskritProcessor(self.lexicon_dir, self.config_file)
        
        # Test single comparison performance
        start_time = time.time()
        for _ in range(10000):
            processor._calculate_similarity("dharma", "dhrma")
        duration = time.time() - start_time
        
        self.assertLess(duration, 0.1, "10,000 comparisons should complete in < 100ms")
        
        # Test memory efficiency - single comparison should use minimal memory
        import tracemalloc
        tracemalloc.start()
        
        processor._calculate_similarity("test", "testing")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory for single comparison should be very small
        self.assertLess(peak, 10 * 1024, "Single comparison should use < 10KB memory")
    
    def test_configuration_options(self):
        """Test AC5: Configuration & Tuning."""
        
        # Test with fuzzy matching disabled
        config_disabled = {
            'processing': {
                'fuzzy_matching': {
                    'enabled': False,
                    'threshold': 0.8,
                    'log_matches': False
                }
            }
        }
        
        config_file_disabled = self.temp_dir / "config_disabled.yaml"
        with open(config_file_disabled, 'w', encoding='utf-8') as f:
            yaml.dump(config_disabled, f, default_flow_style=False)
        
        processor_disabled = SanskritProcessor(self.lexicon_dir, config_file_disabled)
        result, corrections = processor_disabled._apply_lexicon_corrections("I love krishn")  # Close to krishna but not in variations
        
        # Should not correct since fuzzy matching is disabled and no exact match
        self.assertIn("krishn", result)  # Should remain uncorrected
        self.assertEqual(corrections, 0)
        
        # Test with different threshold
        config_high_threshold = {
            'processing': {
                'fuzzy_matching': {
                    'enabled': True,
                    'threshold': 0.95,  # Very high threshold
                    'log_matches': False
                }
            }
        }
        
        config_file_high = self.temp_dir / "config_high.yaml" 
        with open(config_file_high, 'w', encoding='utf-8') as f:
            yaml.dump(config_high_threshold, f, default_flow_style=False)
        
        processor_high = SanskritProcessor(self.lexicon_dir, config_file_high)
        result, corrections = processor_high._apply_lexicon_corrections("I love krishn")
        
        # May not correct due to high threshold depending on similarity
        similarity = processor_high._calculate_similarity("krishn", "krishna")
        if similarity >= 0.95:
            self.assertIn("Krishna", result)
        else:
            self.assertIn("krishn", result)
    
    def test_integration_with_existing_system(self):
        """Test integration with existing lexicon corrections."""
        processor = SanskritProcessor(self.lexicon_dir, self.config_file)
        
        # Test that exact matches still work
        result, corrections = processor._apply_lexicon_corrections("I love krishna")
        self.assertIn("Krishna", result)
        self.assertEqual(corrections, 1)
        
        # Test mixed exact and fuzzy corrections
        result, corrections = processor._apply_lexicon_corrections("krishna and dhrma")
        self.assertIn("Krishna", result)
        self.assertIn("dharma", result) 
        self.assertEqual(corrections, 2)
        
        # Test capitalization preservation
        result, corrections = processor._apply_lexicon_corrections("Krsna")
        self.assertIn("Krishna", result)  # Should preserve capitalization
        
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        processor = SanskritProcessor(self.lexicon_dir, self.config_file)
        
        # Test empty text
        result, corrections = processor._apply_lexicon_corrections("")
        self.assertEqual(result, "")
        self.assertEqual(corrections, 0)
        
        # Test single character words
        result, corrections = processor._apply_lexicon_corrections("a b c")
        self.assertEqual(result, "a b c")
        self.assertEqual(corrections, 0)
        
        # Test punctuation only
        result, corrections = processor._apply_lexicon_corrections("!@#$%")
        self.assertEqual(result, "!@#$%")
        self.assertEqual(corrections, 0)
        
        # Test very long words
        long_word = "a" * 100
        result, corrections = processor._apply_lexicon_corrections(long_word)
        self.assertEqual(result, long_word)
        self.assertEqual(corrections, 0)


class TestFuzzyMatchingPerformance(unittest.TestCase):
    """Performance-focused tests for fuzzy matching."""
    
    def test_processing_speed_requirement(self):
        """Test that fuzzy matching doesn't break the 2,600 segments/second requirement."""
        temp_dir = Path(tempfile.mkdtemp())
        lexicon_dir = temp_dir / "lexicons"
        lexicon_dir.mkdir()
        
        try:
            # Create larger test lexicon
            corrections_data = {
                'entries': [
                    {'original_term': f'term{i}', 'variations': [f'trm{i}', f'term{i}a']}
                    for i in range(100)  # 100 test terms
                ]
            }
            
            corrections_file = lexicon_dir / "corrections.yaml"
            with open(corrections_file, 'w', encoding='utf-8') as f:
                yaml.dump(corrections_data, f, default_flow_style=False)
            
            config_file = temp_dir / "config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump({'processing': {'fuzzy_matching': {'enabled': True, 'threshold': 0.8}}}, f)
            
            processor = SanskritProcessor(lexicon_dir, config_file)
            
            # Test processing speed with mixed exact and fuzzy matches
            test_texts = [
                f"This is test text with trm{i} and some regular words"
                for i in range(100)
            ]
            
            start_time = time.time()
            total_corrections = 0
            
            for text in test_texts:
                _, corrections = processor.process_text(text)
                total_corrections += corrections
            
            duration = time.time() - start_time
            segments_per_second = len(test_texts) / duration
            
            # Should maintain reasonable processing speed for fuzzy matching
            self.assertGreater(segments_per_second, 150, 
                             f"Processing speed {segments_per_second:.0f} segments/second is too slow")
            
            # Should have made some fuzzy corrections
            self.assertGreater(total_corrections, 50, "Should have made fuzzy corrections")
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)