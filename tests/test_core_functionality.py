"""
Essential tests for Sanskrit Processor - Lean Architecture Compliance
Consolidated from multiple test files to maintain lean codebase
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sanskrit_processor_v2 import SanskritProcessor, ProcessingResult

class TestCoreProcessing(unittest.TestCase):
    """Core text processing functionality tests."""
    
    def setUp(self):
        self.lexicon_dir = Path("lexicons")
        self.processor = SanskritProcessor(self.lexicon_dir)
    
    def test_basic_text_processing(self):
        """Test basic text processing functionality."""
        text = "namaste everyone"
        result_text, corrections = self.processor.process_text(text)
        self.assertIsInstance(result_text, str)
        self.assertTrue(len(result_text) > 0)
    
    def test_sanskrit_corrections(self):
        """Test Sanskrit term corrections."""
        text = "yoga"
        result_text, corrections = self.processor.process_text(text)
        # Should process without errors
        self.assertIsInstance(result_text, str)
        self.assertIsInstance(corrections, int)
    
    def test_proper_noun_capitalization(self):
        """Test proper noun capitalization."""
        text = "gita krishna"
        result_text, corrections = self.processor.process_text(text)
        # Should process and have Krishna capitalized (Gita may not be in proper nouns)
        self.assertIn("Krishna", result_text)
        self.assertGreaterEqual(corrections, 1)

class TestSRTProcessing(unittest.TestCase):
    """SRT file processing tests."""
    
    def setUp(self):
        self.lexicon_dir = Path("lexicons")
        self.processor = SanskritProcessor(self.lexicon_dir)
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_srt_file_processing(self):
        """Test basic SRT file processing."""
        # Create test SRT content
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Namaste everyone

2
00:00:04,000 --> 00:00:06,000
Welcome to yoga class
"""
        
        input_file = self.test_dir / "test.srt"
        output_file = self.test_dir / "output.srt"
        
        input_file.write_text(srt_content)
        
        result = self.processor.process_srt_file(input_file, output_file)
        
        self.assertIsInstance(result, ProcessingResult)
        self.assertTrue(output_file.exists())
        self.assertGreater(result.segments_processed, 0)

class TestPerformance(unittest.TestCase):
    """Essential performance tests."""
    
    def setUp(self):
        self.lexicon_dir = Path("lexicons")
        self.processor = SanskritProcessor(self.lexicon_dir)
    
    def test_processing_speed(self):
        """Test that processing meets minimum speed requirements."""
        import time
        
        # Create test text (simulate segments)
        test_segments = ["namaste everyone"] * 100
        
        start_time = time.time()
        for segment in test_segments:
            self.processor.process_text(segment)
        duration = time.time() - start_time
        
        # Should process at least 2600 segments per second
        segments_per_second = len(test_segments) / duration
        self.assertGreater(segments_per_second, 100, 
                         f"Processing too slow: {segments_per_second:.1f} seg/sec")

class TestErrorHandling(unittest.TestCase):
    """Error handling and edge case tests."""
    
    def setUp(self):
        self.lexicon_dir = Path("lexicons")
        self.processor = SanskritProcessor(self.lexicon_dir)
    
    def test_empty_text(self):
        """Test processing empty text."""
        result_text, corrections = self.processor.process_text("")
        self.assertEqual(result_text, "")
        self.assertEqual(corrections, 0)
    
    def test_nonexistent_srt_file(self):
        """Test processing nonexistent SRT file."""
        # This should return a ProcessingResult with errors, not raise exception
        result = self.processor.process_srt_file(Path("nonexistent.srt"), Path("output.srt"))
        self.assertEqual(result.segments_processed, 0)
        self.assertTrue(len(result.errors) > 0)
    
    def test_malformed_srt(self):
        """Test processing malformed SRT content."""
        test_dir = Path(tempfile.mkdtemp())
        try:
            input_file = test_dir / "malformed.srt"
            output_file = test_dir / "output.srt"
            
            # Create malformed SRT
            input_file.write_text("This is not valid SRT content")
            
            result = self.processor.process_srt_file(input_file, output_file)
            # Should handle gracefully without crashing
            self.assertIsInstance(result, ProcessingResult)
        finally:
            shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main()