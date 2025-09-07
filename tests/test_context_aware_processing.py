"""
Comprehensive tests for Context-Aware Processing Pipeline (Story 6.5).
Tests integration of Stories 6.1-6.4 through unified context-aware system.
"""

import unittest
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Test the processors
from processors.content_classifier import ContentClassifier, ContentClassification
from processors.context_pipeline import ContextAwarePipeline, ProcessingResult


class TestContentClassifier(unittest.TestCase):
    """Test content classification functionality."""
    
    def setUp(self):
        self.classifier = ContentClassifier()
    
    def test_mantra_classification(self):
        """Test mantra content detection."""
        # Test various mantra patterns
        test_cases = [
            ("Om namah shivaya", 'mantra', 0.85),
            ("Hare Krishna Hare Rama", 'mantra', 0.85),
            ("Om mani padme hum", 'mantra', 0.85),
            ("ॐ शान्ति शान्ति शान्ति:", 'mantra', 0.95),  # With Om symbol
        ]
        
        for text, expected_type, min_confidence in test_cases:
            with self.subTest(text=text):
                result = self.classifier.classify_content(text)
                self.assertEqual(result.content_type, expected_type)
                self.assertGreaterEqual(result.confidence, min_confidence)
                self.assertIn('sacred', result.specialized_processors)
    
    def test_verse_classification(self):
        """Test verse content detection."""
        test_cases = [
            ("योगस्थः कुरु कर्माणि | संगं त्यक्त्वा धनञ्जय ||", 'verse', 0.95),
            ("Chapter 2, Verse 47", 'verse', 0.80),
            ("This is from Bhagavad Gita 2.47", 'verse', 0.80),
            ("In the Upanishads it is written", 'verse', 0.80),
        ]
        
        for text, expected_type, min_confidence in test_cases:
            with self.subTest(text=text):
                result = self.classifier.classify_content(text)
                self.assertEqual(result.content_type, expected_type)
                self.assertGreaterEqual(result.confidence, min_confidence)
                self.assertIn('sacred', result.specialized_processors)
                self.assertIn('scripture', result.specialized_processors)
    
    def test_title_classification(self):
        """Test title content detection."""
        test_cases = [
            # These contain scripture references and should be classified as verses
            ("Chapter 2: The Yoga of Knowledge", 'verse', 0.80),  # Contains "Chapter" + scripture context
            ("The Bhagavad Gita Overview", 'verse', 0.80),        # Contains "Gita" (scripture name)
            # This is a proper title format
            ("1. Introduction to Vedanta", 'title', 0.75),        # Numbered title format
        ]
        
        for text, expected_type, min_confidence in test_cases:
            with self.subTest(text=text):
                result = self.classifier.classify_content(text)
                self.assertEqual(result.content_type, expected_type)
                self.assertGreaterEqual(result.confidence, min_confidence)
                # Check appropriate processor routing
                if expected_type == 'title':
                    self.assertIn('compound', result.specialized_processors)
                elif expected_type == 'verse':
                    self.assertIn('sacred', result.specialized_processors)
    
    def test_commentary_classification(self):
        """Test commentary content detection."""
        test_cases = [
            ("Here Krishna explains the meaning of yoga", 'commentary', 0.70),
            ("According to the interpretation of this verse", 'commentary', 0.70),
            ("This commentary explains the significance", 'commentary', 0.70),
        ]
        
        for text, expected_type, min_confidence in test_cases:
            with self.subTest(text=text):
                result = self.classifier.classify_content(text)
                self.assertEqual(result.content_type, expected_type)
                self.assertGreaterEqual(result.confidence, min_confidence)
                self.assertIn('compound', result.specialized_processors)
    
    def test_regular_classification(self):
        """Test regular text classification."""
        test_cases = [
            ("This is just regular English text", 'regular', 0.0),
            ("The weather is nice today", 'regular', 0.0),
        ]
        
        for text, expected_type, min_confidence in test_cases:
            with self.subTest(text=text):
                result = self.classifier.classify_content(text)
                self.assertEqual(result.content_type, expected_type)
                # Regular content should always use database processing
                self.assertIn('database', result.specialized_processors)
    
    def test_mixed_content_detection(self):
        """Test detection of content with multiple types."""
        mixed_text = "Chapter 2: Om namah shivaya - this explains the verse"
        result = self.classifier.classify_content(mixed_text)
        
        # Should detect mixed content
        self.assertTrue(result.content_type.startswith('mixed_'))
        self.assertGreater(result.confidence, 0.8)
        
        # Should include multiple processors
        processors = result.specialized_processors
        self.assertIn('compound', processors)
        self.assertIn('sacred', processors)
        self.assertIn('database', processors)
    
    def test_classification_performance(self):
        """Test classification performance requirements (<50ms per segment)."""
        test_texts = [
            "Om namah shivaya",
            "Chapter 2, Verse 47",
            "Regular English text",
            "योगस्थः कुरु कर्माणि | संगं त्यक्त्वा धनञ्जय ||",
        ]
        
        # Warm up
        for text in test_texts:
            self.classifier.classify_content(text)
        
        # Measure performance
        total_time = 0
        iterations = 100
        
        for _ in range(iterations):
            for text in test_texts:
                start = time.time()
                self.classifier.classify_content(text)
                total_time += time.time() - start
        
        avg_time_per_classification = total_time / (iterations * len(test_texts))
        
        # Should be under 50ms (0.05 seconds) per classification
        self.assertLess(avg_time_per_classification, 0.05,
                       f"Classification took {avg_time_per_classification:.3f}s, "
                       f"expected < 0.05s")


class TestContextAwarePipeline(unittest.TestCase):
    """Test context-aware pipeline orchestration."""
    
    def setUp(self):
        self.config = {
            'processing': {
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            },
            'database': {'enabled': False}  # Disable for testing
        }
        
        # Initialize pipeline with real implementation (it handles missing dependencies gracefully)
        self.pipeline = ContextAwarePipeline(self.config)
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly."""
        self.assertIsInstance(self.pipeline.classifier, ContentClassifier)
        self.assertIsInstance(self.pipeline.config, dict)
        self.assertEqual(self.pipeline.processing_stats['classifications'], 0)
    
    @patch('processors.context_pipeline.time.time')
    def test_segment_processing_flow(self, mock_time):
        """Test complete segment processing flow."""
        # Mock time for consistent testing
        mock_time.side_effect = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005]
        
        test_text = "Om namah shivaya"
        result = self.pipeline.process_segment(test_text)
        
        # Verify result structure
        self.assertIsInstance(result, ProcessingResult)
        self.assertEqual(result.original_text, test_text)
        self.assertIsInstance(result.processed_text, str)
        self.assertIsInstance(result.corrections_made, int)
        self.assertIsInstance(result.processing_time, float)
        self.assertIsInstance(result.content_type, str)
        self.assertIsInstance(result.confidence, float)
        self.assertIsInstance(result.corrections, list)
        self.assertIsInstance(result.metadata, dict)
    
    def test_processor_fallback(self):
        """Test graceful fallback when processors fail."""
        # Test with empty processors to trigger fallback
        self.pipeline._processors = {}
        
        test_text = "Test text"
        result = self.pipeline.process_segment(test_text)
        
        # Should still return a valid result
        self.assertEqual(result.original_text, test_text)
        self.assertIsInstance(result.processed_text, str)
    
    def test_processing_statistics(self):
        """Test processing statistics tracking."""
        test_texts = [
            "Om namah shivaya",  # mantra
            "Chapter 2, Verse 47",  # verse
            "Regular text"  # regular
        ]
        
        for text in test_texts:
            self.pipeline.process_segment(text)
        
        stats = self.pipeline.get_processing_stats()
        
        # Should track classifications
        self.assertEqual(stats['classifications'], 3)
        self.assertIn('by_type', stats)
        self.assertGreater(stats['avg_confidence'], 0.0)
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        test_text = "Test input text"
        result = self.pipeline.process_segment(test_text)
        
        # Should include quality metrics
        self.assertIn('quality_metrics', result.__dict__)
        quality_metrics = result.quality_metrics
        
        # Check required metrics
        self.assertIn('text_similarity', quality_metrics)
        self.assertIn('correction_density', quality_metrics)
        self.assertIn('processing_speed', quality_metrics)
        self.assertIn('avg_correction_confidence', quality_metrics)
        
        # Verify metric ranges
        self.assertGreaterEqual(quality_metrics['text_similarity'], 0.0)
        self.assertLessEqual(quality_metrics['text_similarity'], 1.0)
        self.assertGreaterEqual(quality_metrics['correction_density'], 0.0)
        self.assertGreaterEqual(quality_metrics['processing_speed'], 0.0)


class TestIntegrationWithMainProcessor(unittest.TestCase):
    """Test integration with main SanskritProcessor."""
    
    def setUp(self):
        self.lexicon_dir = Path("lexicons")
        
    def test_context_pipeline_integration(self):
        """Test that SanskritProcessor integrates with context pipeline."""
        from sanskrit_processor_v2 import SanskritProcessor
        
        processor = SanskritProcessor(self.lexicon_dir)
        
        # Test that context pipeline is available and working
        self.assertTrue(hasattr(processor, 'context_pipeline'))
        
        # Test basic processing integration
        result = processor.process_text("Om namah shivaya")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)  # (processed_text, correction_count)
        
        # Test detailed processing if available
        if hasattr(processor, 'process_segment_detailed'):
            from processors.context_pipeline import ProcessingResult
            detailed = processor.process_segment_detailed(type('obj', (object,), {'text': 'Om namah shivaya'})())
            self.assertIsInstance(detailed, ProcessingResult)
            self.assertTrue(hasattr(detailed, 'content_type'))
            self.assertEqual(detailed.content_type, 'mantra')
    
    def test_fallback_to_legacy_processing(self):
        """Test fallback behavior in context pipeline."""
        from sanskrit_processor_v2 import SanskritProcessor
        
        # Test that processor works even if some components aren't available
        processor = SanskritProcessor(self.lexicon_dir)
        
        # The processor should handle missing components gracefully
        # Test basic functionality still works
        result = processor.process_text("test text")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        
        # Test that context pipeline initializes with graceful fallbacks
        if processor.context_pipeline:
            # Test processing with potentially missing dependencies
            test_result = processor.context_pipeline.process_segment("Om namah shivaya")
            self.assertIsNotNone(test_result)


class TestPerformanceRequirements(unittest.TestCase):
    """Test performance requirements for Story 6.5."""
    
    def setUp(self):
        self.config = {
            'processing': {'fuzzy_matching': {'enabled': True}},
            'database': {'enabled': False}
        }
    
    def test_classification_speed_requirement(self):
        """Test <50ms classification requirement."""
        classifier = ContentClassifier()
        
        test_texts = [
            "Om namah shivaya",
            "Chapter 2, Verse 47",
            "Regular English text",
            "योगस्थः कुरु कर्माणि | संगं त्यक्त्वा धनञ्जय ||",
            "The Bhagavad Gita Chapter 2 explains karma yoga",
        ]
        
        # Warm up
        for text in test_texts:
            classifier.classify_content(text)
        
        # Measure performance
        start_time = time.time()
        for text in test_texts:
            classifier.classify_content(text)
        total_time = time.time() - start_time
        
        avg_time_per_classification = total_time / len(test_texts)
        
        # Should be under 50ms
        self.assertLess(avg_time_per_classification, 0.05,
                       f"Classification took {avg_time_per_classification:.3f}s, expected < 0.05s")
    
    def test_pipeline_throughput_requirement(self):
        """Test >1500 segments/second processing requirement."""
        pipeline = ContextAwarePipeline(self.config)
        
        # Simple test text
        test_text = "Test segment for throughput measurement"
        
        # Warm up
        for _ in range(10):
            pipeline.process_segment(test_text)
        
        # Measure throughput
        segment_count = 100
        start_time = time.time()
        
        for _ in range(segment_count):
            pipeline.process_segment(test_text)
        
        total_time = time.time() - start_time
        throughput = segment_count / total_time
        
        # Should exceed 1500 segments/second
        self.assertGreater(throughput, 1500,
                          f"Throughput was {throughput:.0f} segments/sec, expected > 1500")
    
    def test_memory_footprint_requirement(self):
        """Test <25MB additional memory footprint requirement."""
        import psutil
        import gc
        
        # Measure baseline memory
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Initialize context-aware components
        classifier = ContentClassifier()
        pipeline = ContextAwarePipeline(self.config)
        
        # Process some segments to initialize caches
        test_texts = [
            "Om namah shivaya",
            "Chapter 2, Verse 47", 
            "Regular text",
            "The Bhagavad Gita explanation"
        ] * 25  # 100 segments
        
        for text in test_texts:
            classifier.classify_content(text)
            pipeline.process_segment(text)
        
        # Measure memory after initialization
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory
        
        # Should be under 25MB additional footprint
        self.assertLess(memory_increase, 25,
                       f"Memory footprint increased by {memory_increase:.1f}MB, expected < 25MB")


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)