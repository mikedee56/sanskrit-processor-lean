#!/usr/bin/env python3
"""
Test suite for extracted utilities to ensure functionality is preserved.
Tests MetricsCollector, ProcessingReporter, and SRTParser utilities.
"""

import unittest
import time
from utils.metrics_collector import MetricsCollector, CorrectionDetail
from utils.processing_reporter import ProcessingReporter, ProcessingResult, DetailedProcessingResult
from utils.srt_parser import SRTParser, SRTSegment


class TestMetricsCollector(unittest.TestCase):
    """Test MetricsCollector functionality."""
    
    def setUp(self):
        self.collector = MetricsCollector()
    
    def test_basic_correction_tracking(self):
        """Test basic correction tracking."""
        self.collector.start_correction("lexicon", "gita")
        time.sleep(0.01)  # Small delay for timing
        self.collector.end_correction("lexicon", "gita", "Gita", 0.95)
        
        self.assertEqual(len(self.collector.correction_details), 1)
        self.assertEqual(self.collector.corrections_by_type["lexicon"], 1)
        self.assertEqual(len(self.collector.confidence_scores), 1)
        self.assertEqual(self.collector.confidence_scores[0], 0.95)
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        # Add some corrections
        self.collector.end_correction("lexicon", "gita", "Gita", 0.9)
        self.collector.end_correction("capitalization", "yoga", "Yoga", 0.8)
        
        score = self.collector.calculate_quality_score(total_segments=10, error_count=1)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIsInstance(score, float)
    
    def test_correction_detail_validation(self):
        """Test CorrectionDetail validation."""
        detail = CorrectionDetail(
            type="lexicon",
            original="test",
            corrected="Test", 
            confidence=1.5,  # Invalid - should be clamped
            processing_time=-0.1  # Invalid - should be clamped
        )
        
        self.assertLessEqual(detail.confidence, 1.0)
        self.assertGreaterEqual(detail.processing_time, 0.0)


class TestProcessingReporter(unittest.TestCase):
    """Test ProcessingReporter functionality."""
    
    def test_basic_summary_generation(self):
        """Test basic summary generation."""
        result = ProcessingResult(
            segments_processed=100,
            corrections_made=25,
            processing_time=2.5,
            errors=[]
        )
        
        summary = ProcessingReporter.generate_summary(result)
        self.assertIn("Processing Complete", summary)
        self.assertIn("100", summary)
        self.assertIn("25", summary)
        self.assertIn("2.5", summary)
    
    def test_detailed_summary_generation(self):
        """Test detailed summary generation."""
        result = DetailedProcessingResult(
            segments_processed=100,
            corrections_made=25,
            processing_time=2.5,
            errors=[],
            corrections_by_type={"lexicon": 15, "capitalization": 10},
            confidence_scores=[0.9, 0.8, 0.85],
            quality_score=85.5
        )
        
        summary = ProcessingReporter.generate_summary(result, verbose=True)
        self.assertIn("Quality score: 86/100", summary)
        self.assertIn("Lexicon corrections: 15", summary)
        self.assertIn("Capitalization corrections: 10", summary)
    
    def test_json_export(self):
        """Test JSON export functionality."""
        result = ProcessingResult(
            segments_processed=50,
            corrections_made=10,
            processing_time=1.0,
            errors=[]
        )
        
        json_data = ProcessingReporter.export_json(result)
        self.assertEqual(json_data['segments_processed'], 50)
        self.assertEqual(json_data['corrections_made'], 10)
        self.assertEqual(json_data['processing_time'], 1.0)
        self.assertIn('timestamp', json_data)


class TestSRTParser(unittest.TestCase):
    """Test SRTParser functionality."""
    
    def test_srt_parsing(self):
        """Test SRT content parsing."""
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Welcome to the lecture

2
00:00:04,000 --> 00:00:06,000
About Bhagavad Gita"""
        
        segments = SRTParser.parse(srt_content)
        
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].index, 1)
        self.assertEqual(segments[0].text, "Welcome to the lecture")
        self.assertEqual(segments[1].index, 2)
        self.assertEqual(segments[1].text, "About Bhagavad Gita")
    
    def test_srt_generation(self):
        """Test SRT content generation."""
        segments = [
            SRTSegment(1, "00:00:01,000", "00:00:03,000", "Test segment"),
            SRTSegment(2, "00:00:04,000", "00:00:06,000", "Another segment")
        ]
        
        srt_content = SRTParser.to_srt(segments)
        
        self.assertIn("1", srt_content)
        self.assertIn("00:00:01,000 --> 00:00:03,000", srt_content)
        self.assertIn("Test segment", srt_content)
        self.assertIn("2", srt_content)
        self.assertIn("Another segment", srt_content)
    
    def test_malformed_srt_handling(self):
        """Test handling of malformed SRT content."""
        malformed_srt = """1
invalid timestamp
Text without proper format"""
        
        segments = SRTParser.parse(malformed_srt)
        # Should handle gracefully and return empty or filtered results
        self.assertIsInstance(segments, list)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that existing imports still work after extraction."""
    
    def test_core_imports(self):
        """Test that core processor still exports all necessary classes."""
        from sanskrit_processor_v2 import SRTSegment, ProcessingResult, SanskritProcessor
        from sanskrit_processor_v2 import MetricsCollector, ProcessingReporter, SRTParser
        
        # Test that classes can be instantiated
        segment = SRTSegment(1, "00:00:01,000", "00:00:02,000", "test")
        self.assertIsInstance(segment, SRTSegment)
        
        collector = MetricsCollector()
        self.assertIsInstance(collector, MetricsCollector)
        
        processor = SanskritProcessor()
        self.assertIsInstance(processor, SanskritProcessor)
    
    def test_utility_imports(self):
        """Test that utilities can be imported directly."""
        from utils.metrics_collector import MetricsCollector
        from utils.processing_reporter import ProcessingReporter
        from utils.srt_parser import SRTParser, SRTSegment
        
        # Test instantiation
        collector = MetricsCollector()
        self.assertIsInstance(collector, MetricsCollector)


if __name__ == "__main__":
    unittest.main()