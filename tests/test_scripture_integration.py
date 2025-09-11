"""
Tests for Scripture API Integration Fixes
Story 9.2 validation tests

Test Coverage:
- English content protection (AC: 1, 3)
- Sanskrit-only processing (AC: 1)
- Length validation (AC: 2)
- Content preservation (AC: 3, 4)
- Enhancement only (AC: 4)
- Segment limits (AC: 5)
- High confidence thresholds (AC: 6)
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from collections import namedtuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_processor import EnhancedSanskritProcessor


# Mock Scripture Response for testing
ScriptureMatch = namedtuple('ScriptureMatch', ['transliteration', 'confidence', 'verse_reference'])


class TestScriptureIntegrationFixes(unittest.TestCase):
    """Test scripture API integration fixes for Story 9.2."""
    
    def setUp(self):
        """Set up test environment with mocked external services."""
        # Mock the processor initialization to avoid dependency issues
        with patch('enhanced_processor.EnhancedSanskritProcessor.__init__', return_value=None):
            self.processor = EnhancedSanskritProcessor()
        
        # Set up minimal required attributes for testing
        self.processor.config = {
            'processing': {
                'enable_scripture_lookup': True,
                'enable_systematic_matching': False,
                'enable_compound_processing': False,
                'enable_semantic_analysis': False
            }
        }
        
        # Mock external services to avoid actual API calls
        self.processor.external_services = Mock()
        self.processor.external_services.api_lookup_scripture = Mock()
        
        # Mock other dependencies
        self.processor.systematic_matcher = None
        self.processor.compound_processor = None
        self.processor.prayer_recognizer = None
        self.processor.external_clients = None
        
        # Mock all required attributes from base class
        self.processor.use_context_pipeline = False
        self.processor.context_pipeline = None
        self.processor.lexicons = Mock()
        self.processor.lexicon_cache = Mock()
        
        # Mock the parent class process_text method to return input unchanged
        def mock_parent_process_text(text):
            return text, 0
        
        # Use patch to mock the super().process_text call
        self.super_process_text_patcher = patch.object(
            type(self.processor).__bases__[0], 'process_text', side_effect=mock_parent_process_text
        )
        self.super_process_text_patcher.start()
        
        # Set default mock return value to None to avoid comparison issues
        self.processor.external_services.api_lookup_scripture.return_value = None
    
    def tearDown(self):
        """Clean up patches."""
        if hasattr(self, 'super_process_text_patcher'):
            self.super_process_text_patcher.stop()
    
    def test_english_content_protection(self):
        """Test that English content is never replaced (AC: 1, 3)."""
        # Test Case 1: Pure English explanation should remain unchanged
        english_text = "then you worship Sarasvatī Devī. If you want to succeed in business"
        
        # Should not call API for English-only content
        processed, corrections = self.processor._process_sanskrit_segment(english_text)
        
        self.assertEqual(processed, english_text, "English text should remain unchanged")
        self.processor.external_services.api_lookup_scripture.assert_not_called()
        
        # Test Case 2: Long English explanation should be unchanged
        long_english = "given a bigger extension, as well as read the whole Bālakāṇḍa and tell in four"
        
        processed, corrections = self.processor._process_sanskrit_segment(long_english)
        
        self.assertEqual(processed, long_english, "Long English text should remain unchanged")
    
    def test_sanskrit_only_processing(self):
        """Test that only texts with Sanskrit diacriticals are processed (AC: 1)."""
        # Test Case 1: Text without diacriticals should be skipped
        no_diacriticals = "Bhagavad Gita teaches dharma"
        
        processed, corrections = self.processor._process_sanskrit_segment(no_diacriticals)
        
        self.processor.external_services.api_lookup_scripture.assert_not_called()
        
        # Test Case 2: Text with Sanskrit diacriticals should be processed
        with_diacriticals = "Bhagavad Gītā teaches dharma"
        
        # Mock successful API response
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="Bhagavad Gītā teaches dharma",
            confidence=0.95,
            verse_reference="BG 1.1"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(with_diacriticals)
        
        # Should call API for Sanskrit text with diacriticals
        self.processor.external_services.api_lookup_scripture.assert_called_once()
    
    def test_word_count_limit(self):
        """Test that segments over 8 words are skipped (AC: 5)."""
        # Test Case: 9-word Sanskrit phrase should be skipped (changed to 9 to be clearly > 8)
        long_sanskrit = "oṁ namo bhagavate vāsudevāya kṛṣṇa govinda hare murāre he"  # 10 words
        
        processed, corrections = self.processor._process_sanskrit_segment(long_sanskrit)
        
        # Should not call API for text over 8 words
        self.processor.external_services.api_lookup_scripture.assert_not_called()
        
        # Test Case: 5-word Sanskrit phrase should be processed
        short_sanskrit = "oṁ namo bhagavate vāsudevāya kṛṣṇa"  # 5 words
        
        # Mock successful API response
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="oṁ namo bhagavate vāsudevāya kṛṣṇa",
            confidence=0.95,
            verse_reference="Mantra"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(short_sanskrit)
        
        # Should call API for short Sanskrit text
        self.processor.external_services.api_lookup_scripture.assert_called()
    
    def test_length_validation(self):
        """Test that API responses with inappropriate length are rejected (AC: 2)."""
        sanskrit_text = "dharma kṣetre"
        
        # Test Case 1: Response too long should be rejected
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="dharma kṣetre kurukṣetre samavetā yuyutsavaḥ māmakāḥ pāṇḍavāś caiva kim akurvata sañjaya",
            confidence=0.95,
            verse_reference="BG 1.1"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should reject due to length difference
        self.assertEqual(processed, sanskrit_text, "Should reject response that's too long")
        
        # Test Case 2: Appropriate length response should be accepted
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="dharma-kṣetre",
            confidence=0.95,
            verse_reference="BG 1.1"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should accept appropriate length response
        self.assertEqual(processed, "dharma-kṣetre")
    
    def test_confidence_threshold(self):
        """Test that confidence threshold of 0.9 is enforced (AC: 6)."""
        sanskrit_text = "gītā"
        
        # Test Case 1: Confidence 0.85 should be rejected
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="Gītā",
            confidence=0.85,
            verse_reference="BG"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should reject due to low confidence
        self.assertEqual(processed, sanskrit_text, "Should reject low confidence match")
        self.assertEqual(corrections, 0, "No corrections for low confidence")
        
        # Reset mock for next test
        self.processor.external_services.api_lookup_scripture.reset_mock()
        
        # Test Case 2: Confidence 0.95 should be accepted
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="Gītā",
            confidence=0.95,
            verse_reference="BG"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should accept high confidence match and apply enhancement
        self.assertEqual(processed, "Gītā", "Should accept and apply high confidence enhancement")
        self.assertEqual(corrections, 1, "Should count as one correction")
        self.processor.external_services.api_lookup_scripture.assert_called_with(sanskrit_text)
    
    def test_content_preservation(self):
        """Test that core meaning is preserved in enhancements (AC: 3, 4)."""
        sanskrit_text = "dharma gītā"
        
        # Test Case 1: Response missing key terms should be rejected
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="karma yoga",  # Doesn't preserve original terms
            confidence=0.95,
            verse_reference="BG 2.47"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should reject due to poor term preservation (0% preservation ratio)
        self.assertEqual(processed, sanskrit_text, "Should reject response missing key terms")
        self.assertEqual(corrections, 0, "No corrections should be applied for rejected content")
        
        # Reset mock for next test
        self.processor.external_services.api_lookup_scripture.reset_mock()
        
        # Test Case 2: Response preserving key terms should be accepted
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="dharma Gītā",  # Preserves both key terms with proper capitalization
            confidence=0.95,
            verse_reference="BG"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should accept response preserving terms - now that verse pattern detection is fixed
        self.assertEqual(processed, "dharma Gītā", "Should accept response preserving key terms")
        self.assertEqual(corrections, 1, "Should count as one correction")
        self.processor.external_services.api_lookup_scripture.assert_called_with(sanskrit_text)
    
    def test_verse_injection_protection(self):
        """Test protection against verse injection (AC: 3)."""
        sanskrit_text = "gītā"
        
        # Test Case 1: Multi-line response (verse) should be rejected
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="dharma-kṣetre kuru-kṣetre\nsamavetā yuyutsavaḥ",
            confidence=0.95,
            verse_reference="BG 1.1"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should reject multi-line response
        self.assertEqual(processed, sanskrit_text, "Should reject multi-line verse response")
        
        # Test Case 2: Response with verse patterns should be rejected
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="As stated in Bhagavad Gītā verse 2.47",
            confidence=0.95,
            verse_reference="BG 2.47"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should reject response with verse patterns
        self.assertEqual(processed, sanskrit_text, "Should reject response with verse patterns")
    
    def test_english_word_detection(self):
        """Test enhanced English word detection and blocking."""
        # Test with mixed content containing common English words
        mixed_text = "the dharma of gītā"  # Contains 'the' and 'of'
        
        processed, corrections = self.processor._process_sanskrit_segment(mixed_text)
        
        # Should not call API due to English words
        self.processor.external_services.api_lookup_scripture.assert_not_called()
        
        # Test with specific problematic words from the story
        problematic_text = "worship Sarasvatī when succeed business"
        
        processed, corrections = self.processor._process_sanskrit_segment(problematic_text)
        
        # Should not call API due to English words
        self.processor.external_services.api_lookup_scripture.assert_not_called()
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test Case 1: Empty string
        processed, corrections = self.processor._process_sanskrit_segment("")
        self.assertEqual(processed, "")
        
        # Test Case 2: Only punctuation
        processed, corrections = self.processor._process_sanskrit_segment("... !!!")
        self.assertEqual(processed, "... !!!")
        
        # Test Case 3: API returns None
        self.processor.external_services.api_lookup_scripture.return_value = None
        processed, corrections = self.processor._process_sanskrit_segment("gītā")
        self.assertEqual(processed, "gītā")
        
        # Test Case 4: API raises exception
        self.processor.external_services.api_lookup_scripture.side_effect = Exception("API Error")
        processed, corrections = self.processor._process_sanskrit_segment("gītā")
        self.assertEqual(processed, "gītā", "Should handle API errors gracefully")
    
    def test_successful_enhancement_scenario(self):
        """Test successful Sanskrit term enhancement scenario."""
        # Perfect case: Sanskrit text with diacriticals, appropriate response
        sanskrit_text = "Bhagavad Gītā"
        
        # Mock ideal API response that's different from input to show enhancement
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="Bhagavad-gītā",  # Different format but preserves core terms
            confidence=0.98,
            verse_reference="Title"
        )
        
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should accept and apply enhancement - now that verse pattern detection is fixed
        self.assertEqual(processed, "Bhagavad-gītā", "Should apply valid enhancement")
        self.assertEqual(corrections, 1, "Should count as one correction")
        self.processor.external_services.api_lookup_scripture.assert_called_with(sanskrit_text)
    
    def test_logging_scenarios(self):
        """Test that appropriate logging occurs for different scenarios."""
        # This test verifies logging behavior described in the story
        
        # Test rejection logging
        sanskrit_text = "long text without any diacriticals at all here"
        
        with patch('enhanced_processor.logger') as mock_logger:
            processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
            
            # Should log why scripture lookup was skipped
            mock_logger.debug.assert_called()
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            # Should contain rejection reason in debug logs
            rejection_logged = any("Scripture lookup skipped" in msg for msg in debug_calls)
            self.assertTrue(rejection_logged, "Should log scripture lookup rejection reason")

    def test_integration_with_srt_workflow(self):
        """Integration test with real SRT processing workflow."""
        # Test that scripture processing integrates properly with SRT workflow
        sanskrit_text = "Bhagavad Gītā teaches dharma"
        
        # Mock a realistic API response
        self.processor.external_services.api_lookup_scripture.return_value = ScriptureMatch(
            transliteration="Bhagavad-gītā teaches dharma",
            confidence=0.92,
            verse_reference="Philosophy"
        )
        
        # Test processing through the full pipeline
        processed, corrections = self.processor._process_sanskrit_segment(sanskrit_text)
        
        # Should enhance the Sanskrit terms appropriately
        self.assertEqual(processed, "Bhagavad-gītā teaches dharma")
        self.assertEqual(corrections, 1, "Should apply one enhancement")
        
        # Verify API was called with correct parameters
        self.processor.external_services.api_lookup_scripture.assert_called_with(sanskrit_text)
        
        # Test that problematic content is still rejected
        problematic_text = "then you worship Sarasvatī Devī"
        processed2, corrections2 = self.processor._process_sanskrit_segment(problematic_text)
        
        # Should remain unchanged due to English words
        self.assertEqual(processed2, problematic_text)
        self.assertEqual(corrections2, 0, "No enhancements for English content")


class TestScriptureConfigIntegration(unittest.TestCase):
    """Test configuration integration for scripture processing."""
    
    def test_scripture_lookup_disabled(self):
        """Test that scripture lookup can be disabled via configuration."""
        # Mock processor initialization
        with patch('enhanced_processor.EnhancedSanskritProcessor.__init__', return_value=None):
            processor = EnhancedSanskritProcessor()
        
        # Mock disabled config
        processor.config = {'processing': {'enable_scripture_lookup': False}}
        processor.external_services = Mock()
        processor.systematic_matcher = None
        processor.compound_processor = None
        processor.prayer_recognizer = None
        processor.external_clients = None
        processor.use_context_pipeline = False
        processor.context_pipeline = None
        processor.lexicons = Mock()
        processor.lexicon_cache = Mock()
        
        # Mock parent process_text method
        with patch.object(type(processor).__bases__[0], 'process_text', return_value=("gītā", 0)):
            sanskrit_text = "gītā"
            processed, corrections = processor._process_sanskrit_segment(sanskrit_text)
            
            # Should not call API when disabled
            processor.external_services.api_lookup_scripture.assert_not_called()
    
    def test_missing_external_services(self):
        """Test behavior when external services are not available."""
        # Mock processor initialization
        with patch('enhanced_processor.EnhancedSanskritProcessor.__init__', return_value=None):
            processor = EnhancedSanskritProcessor()
        
        # No external services configured
        processor.external_services = None
        processor.external_clients = None
        processor.config = {'processing': {'enable_scripture_lookup': True}}
        processor.systematic_matcher = None
        processor.compound_processor = None
        processor.prayer_recognizer = None
        processor.use_context_pipeline = False
        processor.context_pipeline = None
        processor.lexicons = Mock()
        processor.lexicon_cache = Mock()
        
        # Mock parent process_text method
        with patch.object(type(processor).__bases__[0], 'process_text', return_value=("gītā", 0)):
            sanskrit_text = "gītā"
            
            # Should handle gracefully without external services
            processed, corrections = processor._process_sanskrit_segment(sanskrit_text)
            
            # Should return original text unchanged
            self.assertEqual(processed, sanskrit_text)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)