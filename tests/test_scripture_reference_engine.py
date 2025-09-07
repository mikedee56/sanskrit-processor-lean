"""
Tests for Scripture Reference Engine
Story 6.4 validation tests

Test Coverage:
- Verse recognition accuracy
- Performance requirements
- Reference formatting
- Database operations
"""

import unittest
import time
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripture.verse_engine import ScriptureReferenceEngine, ScriptureReference
from scripture.reference_formatter import ReferenceFormatter


class TestScriptureReferenceEngine(unittest.TestCase):
    """Test scripture verse recognition functionality."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "test_verses.db"
        self.engine = ScriptureReferenceEngine(self.temp_db)
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_db.exists():
            self.temp_db.unlink()
        self.temp_db.parent.rmdir()
    
    def test_verse_recognition_bhagavad_gita(self):
        """Test Bhagavad Gītā verse recognition accuracy."""
        # Test exact match
        exact_text = "You have a right to perform your prescribed duty, but not to the fruits of action."
        references = self.engine.identify_verses(exact_text)
        
        self.assertGreater(len(references), 0, "Should find verse references")
        self.assertEqual(references[0].source, "Bhagavad Gītā")
        self.assertEqual(references[0].chapter, 2)
        self.assertEqual(references[0].verse, 47)
        self.assertGreater(references[0].confidence, 0.7, "Confidence should be high for exact match")
    
    def test_verse_recognition_partial_match(self):
        """Test partial verse recognition accuracy."""
        # Test partial match
        partial_text = "One who is not disturbed in mind even amidst miseries and free from attachment and fear."
        references = self.engine.identify_verses(partial_text, threshold=0.6)
        
        self.assertGreater(len(references), 0, "Should find partial matches")
        if references:
            self.assertGreater(references[0].confidence, 0.6, "Should meet minimum threshold")
            self.assertEqual(references[0].source, "Bhagavad Gītā")
    
    def test_verse_recognition_no_match(self):
        """Test that non-scriptural text returns no matches."""
        non_scriptural_text = "Today is a beautiful day with nice weather and blue skies."
        references = self.engine.identify_verses(non_scriptural_text)
        
        self.assertEqual(len(references), 0, "Should not match non-scriptural text")
    
    def test_performance_requirements(self):
        """Test that verse recognition meets performance requirements (<100ms)."""
        test_text = "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions."
        
        # Test performance
        start_time = time.time()
        for _ in range(10):
            references = self.engine.identify_verses(test_text)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        self.assertLess(avg_time, 0.1, f"Average processing time {avg_time:.3f}s exceeds 100ms requirement")
        
        # Verify functionality
        self.assertGreater(len(references), 0, "Should find references in performance test")
    
    def test_confidence_scoring(self):
        """Test confidence scoring accuracy."""
        # High confidence match
        high_conf_text = "You have a right to perform your prescribed duty, but not to the fruits of action."
        refs = self.engine.identify_verses(high_conf_text)
        if refs:
            self.assertGreaterEqual(refs[0].confidence, 0.8, "High match should have high confidence")
        
        # Lower confidence match
        low_conf_text = "duty and action without attachment"
        refs = self.engine.identify_verses(low_conf_text, threshold=0.5)
        if refs:
            self.assertLess(refs[0].confidence, 0.8, "Partial match should have lower confidence")
    
    def test_multiple_verse_handling(self):
        """Test handling of text with multiple potential verses."""
        multi_verse_text = """
        You have a right to perform your duty, but not to the fruits. 
        One who is not disturbed in mind amidst miseries is called a sage.
        Abandon all varieties of religion and surrender unto the Supreme.
        """
        
        references = self.engine.identify_verses(multi_verse_text)
        
        # Should return top matches (max 3)
        self.assertLessEqual(len(references), 3, "Should limit to top 3 matches")
        
        # Should be sorted by confidence
        if len(references) > 1:
            self.assertGreaterEqual(references[0].confidence, references[1].confidence,
                                   "Results should be sorted by confidence")


class TestReferenceFormatter(unittest.TestCase):
    """Test scripture reference formatting functionality."""
    
    def setUp(self):
        """Set up test formatter and sample reference."""
        self.formatter = ReferenceFormatter()
        self.sample_ref = ScriptureReference(
            source="Bhagavad Gītā",
            chapter=2,
            verse=47,
            matched_text="You have a right to perform your duty",
            confidence=0.85,
            citation="Bhagavad Gītā 2.47"
        )
    
    def test_standard_citation_formatting(self):
        """Test standard citation format."""
        citation = self.formatter.format_citation(self.sample_ref)
        self.assertEqual(citation, "Bhagavad Gītā 2.47")
    
    def test_abbreviated_citation_formatting(self):
        """Test abbreviated citation format."""
        citation = self.formatter.format_citation(self.sample_ref, 'abbreviated')
        self.assertEqual(citation, "BG 2:47")
    
    def test_multiple_citations_formatting(self):
        """Test formatting of multiple citations."""
        ref2 = ScriptureReference(
            source="Bhagavad Gītā",
            chapter=18,
            verse=66,
            matched_text="surrender unto Me",
            confidence=0.92,
            citation="Bhagavad Gītā 18.66"
        )
        
        citations = self.formatter.format_multiple_citations([self.sample_ref, ref2])
        expected = "Bhagavad Gītā 2.47, Bhagavad Gītā 18.66"
        self.assertEqual(citations, expected)
    
    def test_json_metadata_output(self):
        """Test JSON metadata generation."""
        metadata = self.formatter.to_json_metadata([self.sample_ref])
        
        self.assertIn('scripture_references', metadata)
        self.assertEqual(metadata['reference_count'], 1)
        self.assertEqual(metadata['highest_confidence'], 0.85)
        
        ref_data = metadata['scripture_references'][0]
        self.assertEqual(ref_data['source'], "Bhagavad Gītā")
        self.assertEqual(ref_data['chapter'], 2)
        self.assertEqual(ref_data['verse'], 47)
        self.assertEqual(ref_data['confidence'], 0.85)
    
    def test_srt_metadata_formatting(self):
        """Test SRT metadata comment formatting."""
        srt_metadata = self.formatter.format_for_srt_metadata([self.sample_ref])
        expected = "<!-- Scripture: Bhagavad Gītā 2.47 (confidence: 0.85) -->"
        self.assertEqual(srt_metadata, expected)
    
    def test_empty_references_handling(self):
        """Test handling of empty reference lists."""
        self.assertEqual(self.formatter.format_multiple_citations([]), "")
        self.assertEqual(self.formatter.format_for_srt_metadata([]), "")
        
        metadata = self.formatter.to_json_metadata([])
        self.assertEqual(metadata['reference_count'], 0)
        self.assertEqual(len(metadata['scripture_references']), 0)


class TestScriptureIntegration(unittest.TestCase):
    """Integration tests for complete scripture reference workflow."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "integration_verses.db"
        self.engine = ScriptureReferenceEngine(self.temp_db)
        self.formatter = ReferenceFormatter()
    
    def tearDown(self):
        """Clean up integration test environment."""
        if self.temp_db.exists():
            self.temp_db.unlink()
        self.temp_db.parent.rmdir()
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from text input to formatted output."""
        # Input text with scriptural content
        input_text = "You have a right to perform your prescribed duty, but never be attached to the fruits of action."
        
        # Step 1: Identify verses
        references = self.engine.identify_verses(input_text)
        self.assertGreater(len(references), 0, "Should identify verse references")
        
        # Step 2: Format citations
        citations = self.formatter.format_multiple_citations(references)
        self.assertIn("Bhagavad Gītā", citations, "Should include source name")
        
        # Step 3: Generate JSON metadata
        json_metadata = self.formatter.to_json_metadata(references)
        self.assertIn('scripture_references', json_metadata)
        self.assertGreater(json_metadata['reference_count'], 0)
        
        # Step 4: Generate SRT metadata
        srt_metadata = self.formatter.format_for_srt_metadata(references)
        self.assertTrue(srt_metadata.startswith("<!--"), "Should be HTML comment format")
        self.assertTrue(srt_metadata.endswith("-->"), "Should be HTML comment format")
    
    def test_performance_integration(self):
        """Test performance of complete workflow."""
        input_texts = [
            "You have a right to perform your duty, but not to the fruits of action.",
            "One who is not disturbed in mind even amidst miseries is called a sage.",
            "Abandon all varieties of religion and surrender unto the Supreme Lord.",
        ]
        
        start_time = time.time()
        
        for text in input_texts:
            references = self.engine.identify_verses(text)
            if references:
                citations = self.formatter.format_multiple_citations(references)
                json_metadata = self.formatter.to_json_metadata(references)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should process 3 texts in well under 300ms (100ms each)
        self.assertLess(total_time, 0.3, f"Integration workflow too slow: {total_time:.3f}s")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)