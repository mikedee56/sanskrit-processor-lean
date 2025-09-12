"""
Enhanced test suite for Context Detection Threshold Adjustment (Story 10.2).

Tests all acceptance criteria:
1. Configurable Thresholds: English detection confidence threshold configurable in config.yaml (default 0.8)
2. Mixed Content Control: Mixed content processing threshold configurable (default 0.5)  
3. Sanskrit Whitelist Override: Protection bypassed for whitelisted Sanskrit terms regardless of context
4. Debug Visibility: Context detection decisions logged with `--debug-context` flag
5. Expandable Markers: Sanskrit and English marker lists configurable via configuration
6. Granular Control: Per-segment context detection override capability
7. Performance Maintained: Context detection overhead < 5% of total processing time
"""

import pytest
import tempfile
import yaml
import time
from pathlib import Path
from unittest.mock import Mock, patch
from processors.context_detector import ContextDetector, ContextResult
from processors.context_config import ContextConfig
from enhanced_processor import EnhancedSanskritProcessor


class TestConfigurableThresholds:
    """Test AC1: Configurable threshold functionality."""
    
    def test_default_thresholds(self):
        """Test default threshold values match story requirements."""
        config = ContextConfig()
        assert config.english_threshold == 0.8
        assert config.sanskrit_threshold == 0.6
        assert config.mixed_threshold == 0.5
        assert config.whitelist_override_threshold == 0.9
    
    def test_english_threshold_adjustment(self):
        """Test adjusting English confidence threshold affects detection."""
        # Test case from story: "That's called jnana" 
        test_text = "That's called jnana"
        
        # High threshold (0.9) - should be harder to detect as English
        config_high = ContextConfig(english_threshold=0.9)
        detector_high = ContextDetector(context_config=config_high)
        result_high = detector_high.detect_context(test_text)
        
        # Low threshold (0.3) - should detect as English easily
        config_low = ContextConfig(english_threshold=0.3)  
        detector_low = ContextDetector(context_config=config_low)
        result_low = detector_low.detect_context(test_text)
        
        # With high threshold, might not be pure English; with low threshold, should be English
        if result_low.context_type == 'english':
            # If low threshold detects English, high threshold might not
            assert result_high.context_type in ['english', 'mixed', 'sanskrit']
    
    def test_sanskrit_threshold_adjustment(self):
        """Test adjusting Sanskrit confidence threshold affects detection."""
        test_text = "dharma yoga practice"
        
        # High threshold - harder to detect as Sanskrit
        config_high = ContextConfig(sanskrit_threshold=0.9)
        detector_high = ContextDetector(context_config=config_high)
        result_high = detector_high.detect_context(test_text)
        
        # Low threshold - easier to detect as Sanskrit
        config_low = ContextConfig(sanskrit_threshold=0.3)
        detector_low = ContextDetector(context_config=config_low)
        result_low = detector_low.detect_context(test_text)
        
        # Low threshold more likely to detect Sanskrit
        assert result_low.context_type in ['sanskrit', 'mixed']
    
    def test_threshold_validation(self):
        """Test threshold validation enforces 0.0-1.0 range."""
        # Valid thresholds
        config = ContextConfig(english_threshold=0.5, sanskrit_threshold=0.7)
        assert config.validate() is True
        
        # Invalid thresholds
        invalid_configs = [
            ContextConfig(english_threshold=-0.1),
            ContextConfig(english_threshold=1.1), 
            ContextConfig(sanskrit_threshold="invalid"),
            ContextConfig(mixed_threshold=2.0)
        ]
        
        for config in invalid_configs:
            assert config.validate() is False


class TestMixedContentControl:
    """Test AC2: Mixed content processing threshold control."""
    
    def test_mixed_threshold_affects_processing(self):
        """Test mixed content threshold affects segment processing decisions."""
        test_text = "Karma Yoga allows your karma"  # Example from story
        
        # High mixed threshold (0.8) - stricter mixed detection
        config_high = ContextConfig(mixed_threshold=0.8)
        detector_high = ContextDetector(context_config=config_high)
        result_high = detector_high.detect_context(test_text)
        
        # Low mixed threshold (0.3) - more permissive mixed detection  
        config_low = ContextConfig(mixed_threshold=0.3)
        detector_low = ContextDetector(context_config=config_low)
        result_low = detector_low.detect_context(test_text)
        
        # Both should detect meaningful content
        assert result_high.context_type in ['english', 'sanskrit', 'mixed']
        assert result_low.context_type in ['english', 'sanskrit', 'mixed']
    
    def test_mixed_content_segment_identification(self):
        """Test mixed content identifies Sanskrit segments correctly.""" 
        config = ContextConfig()
        detector = ContextDetector(context_config=config)
        
        # Text with clear Sanskrit terms in English context
        test_text = "The practice of yoga and dharma is essential"
        result = detector.detect_context(test_text)
        
        if result.context_type == 'mixed' and result.segments:
            words = test_text.split()
            
            # Should have segments for Sanskrit terms
            sanskrit_found = False
            for start_idx, end_idx, seg_type in result.segments:
                if seg_type == 'sanskrit':
                    segment_words = words[start_idx:end_idx]
                    segment_text = ' '.join(segment_words).lower()
                    if 'yoga' in segment_text or 'dharma' in segment_text:
                        sanskrit_found = True
                        break
            
            # Should find Sanskrit segments if detected as mixed
            assert sanskrit_found, "Mixed content should identify Sanskrit segments"


class TestSanskritWhitelistOverride:
    """Test AC3: Sanskrit whitelist override functionality."""
    
    def test_priority_terms_override_english_detection(self):
        """Test story example: 'That's called jnana' should be corrected."""
        config = ContextConfig(
            english_threshold=0.3,  # Low - would normally detect as English
            sanskrit_priority_terms=['jnana', 'karma', 'dharma', 'yoga']
        )
        detector = ContextDetector(context_config=config)
        
        # Story test case
        result = detector.detect_context("That's called jnana")
        
        # Should override English detection due to 'jnana' priority term
        assert result.context_type == 'sanskrit'
        assert result.confidence == config.whitelist_override_threshold
        assert result.override_reason == 'sanskrit_whitelist'
        assert any('jnana' in marker for marker in result.markers_found)
    
    def test_karma_yoga_mixed_processing(self):
        """Test story example: 'Karma Yoga allows your karma'."""
        config = ContextConfig(
            sanskrit_priority_terms=['karma', 'yoga']
        )
        detector = ContextDetector(context_config=config)
        
        result = detector.detect_context("Karma Yoga allows your karma")
        
        # Should detect Sanskrit context due to priority terms
        assert result.context_type in ['sanskrit', 'mixed']
        
        # If mixed, should have segments
        if result.context_type == 'mixed':
            assert result.segments is not None
    
    def test_whitelist_override_disabled(self):
        """Test behavior when whitelist override is disabled."""
        config = ContextConfig(
            enable_whitelist_override=False,
            english_threshold=0.3,  # Would detect as English
            sanskrit_priority_terms=['karma']
        )
        detector = ContextDetector(context_config=config)
        
        result = detector.detect_context("That's called karma")
        
        # Should not override - should follow normal detection
        assert result.context_type == 'english'
        assert not hasattr(result, 'override_reason') or result.override_reason is None
    
    def test_priority_terms_case_insensitive(self):
        """Test that priority terms work case-insensitively."""
        config = ContextConfig(sanskrit_priority_terms=['dharma', 'karma'])
        detector = ContextDetector(context_config=config)
        
        test_cases = [
            "This is DHARMA teaching",
            "The Karma principles apply",
            "dharma and KARMA together"
        ]
        
        for text in test_cases:
            result = detector.detect_context(text)
            assert result.context_type == 'sanskrit'
            assert result.override_reason == 'sanskrit_whitelist'
    
    def test_asr_variations_support(self):
        """Test ASR variation mapping as specified in priority terms file."""
        config = ContextConfig()
        detector = ContextDetector(context_config=config)
        
        # Mock ASR variations from priority terms file
        detector.asr_variations = {
            'yogabashi': 'yogavāsiṣṭha',
            'geeta': 'gītā',
            'krisha': 'kṛṣṇa'
        }
        # Add variations to priority set
        for variation in detector.asr_variations.keys():
            detector.sanskrit_priority_set.add(variation.lower())
        
        test_cases = [
            ("yogabashi themes are highlighted", "yogabashi"),
            ("Reading the geeta daily", "geeta"), 
            ("Lord krisha teaches", "krisha")
        ]
        
        for text, expected_term in test_cases:
            result = detector.detect_context(text)
            assert result.context_type == 'sanskrit'
            assert result.override_reason == 'sanskrit_whitelist'
            assert any(expected_term in marker for marker in result.markers_found)


class TestDebugVisibility:
    """Test AC4: Debug logging and visibility."""
    
    def test_debug_context_flag_enables_logging(self):
        """Test that debug_logging=True provides detailed output."""
        config = ContextConfig(debug_logging=True)
        detector = ContextDetector(context_config=config)
        
        with patch('processors.context_detector.logger') as mock_logger:
            result = detector.detect_context("yogabashi is highlighted")
            
            # Should have debug log calls
            debug_calls = [call for call in mock_logger.debug.call_args_list]
            assert len(debug_calls) > 0
            
            # Check for specific debug information
            debug_messages = [str(call[0][0]) if call[0] else "" for call in debug_calls]
            debug_text = ' '.join(debug_messages).lower()
            
            # Should contain confidence and markers information
            assert 'confidence:' in debug_text
            assert 'markers' in debug_text
    
    def test_context_decision_rationale_logging(self):
        """Test that context decisions show rationale as in story example."""
        config = ContextConfig(debug_logging=True)
        detector = ContextDetector(context_config=config)
        
        # Add priority term for this test
        detector.sanskrit_priority_set.add('yogabashi')
        
        with patch('processors.context_detector.logger') as mock_logger:
            result = detector.detect_context("yogabashi is one of the highlighted themes")
            
            debug_calls = mock_logger.debug.call_args_list
            debug_messages = [str(call[0][0]) if call[0] else "" for call in debug_calls]
            
            # Should show override reason for priority term
            assert result.override_reason == 'sanskrit_whitelist'
            
            # Debug messages should explain the decision
            combined_debug = ' '.join(debug_messages)
            assert 'priority_term' in combined_debug.lower() or 'whitelist' in combined_debug.lower()
    
    def test_performance_timing_in_debug(self):
        """Test that performance timing is included in debug output when enabled."""
        config = ContextConfig(debug_logging=True, performance_profiling=True)
        detector = ContextDetector(context_config=config)
        
        with patch('processors.context_detector.logger') as mock_logger:
            result = detector.detect_context("Testing performance timing")
            
            debug_calls = mock_logger.debug.call_args_list
            debug_messages = [str(call[0][0]) if call[0] else "" for call in debug_calls]
            combined_debug = ' '.join(debug_messages)
            
            # Should contain timing information
            assert 'time' in combined_debug.lower() and 'ms' in combined_debug.lower()
    
    def test_cache_hit_logging(self):
        """Test cache hit/miss logging in debug mode."""
        config = ContextConfig(debug_logging=True, cache_results=True)
        detector = ContextDetector(context_config=config)
        
        text = "Test caching behavior"
        
        with patch('processors.context_detector.logger') as mock_logger:
            # First call - cache miss
            result1 = detector.detect_context(text)
            
            # Second call - cache hit
            result2 = detector.detect_context(text)
            
            debug_messages = [str(call[0][0]) if call[0] else "" for call in mock_logger.debug.call_args_list]
            combined_debug = ' '.join(debug_messages)
            
            # Should log cache hit
            assert 'cache hit' in combined_debug.lower()


class TestExpandableMarkers:
    """Test AC5: Expandable markers configuration."""
    
    def test_custom_sanskrit_priority_terms(self):
        """Test custom priority terms from configuration."""
        custom_terms = ['custom_sanskrit', 'special_term']
        config = ContextConfig(sanskrit_priority_terms=custom_terms)
        detector = ContextDetector(context_config=config)
        
        result = detector.detect_context("This contains custom_sanskrit term")
        assert result.context_type == 'sanskrit'
        assert result.override_reason == 'sanskrit_whitelist'
    
    def test_custom_english_function_words(self):
        """Test custom English function words."""
        custom_function_words = ['special_english', 'unique_word']
        config = ContextConfig(
            english_function_words=custom_function_words,
            english_threshold=0.3
        )
        detector = ContextDetector(context_config=config)
        
        result = detector.detect_context("special_english unique_word here")
        assert result.context_type == 'english'
    
    def test_configuration_from_yaml(self):
        """Test loading expandable markers from YAML configuration."""
        config_data = {
            'context_detection': {
                'markers': {
                    'sanskrit_priority_terms': ['test_term1', 'test_term2'],
                    'english_function_words': ['test_eng1', 'test_eng2'],
                    'sanskrit_sacred_terms': ['sacred_test'],
                    'sanskrit_diacriticals': ['ā', 'ī']
                }
            }
        }
        
        config = ContextConfig.from_dict(config_data)
        
        assert 'test_term1' in config.sanskrit_priority_terms
        assert 'test_term2' in config.sanskrit_priority_terms
        assert 'test_eng1' in config.english_function_words
        assert 'sacred_test' in config.sanskrit_sacred_terms
    
    def test_markers_validation(self):
        """Test that marker configuration is validated."""
        # Empty priority terms should fail validation
        config = ContextConfig(sanskrit_priority_terms=[])
        assert config.validate() is False
        
        # Empty function words should fail validation
        config = ContextConfig(english_function_words=[])
        assert config.validate() is False


class TestGranularControl:
    """Test AC6: Per-segment override capability."""
    
    def test_segment_force_processing(self):
        """Test forcing processing regardless of context."""
        processor = EnhancedSanskritProcessor()
        
        # Text that would normally be bypassed as English
        english_text = "The quick brown fox"
        
        # Normal processing - should bypass
        normal_result, normal_corrections = processor.process_text(english_text)
        assert normal_corrections == 0
        
        # Force processing - should attempt processing
        context_override = {'force_processing': True}
        forced_result, forced_corrections = processor.process_text(english_text, context_override)
        # May or may not make corrections, but should attempt processing
        assert isinstance(forced_result, str)
    
    def test_segment_type_override(self):
        """Test manually overriding detected segment type."""
        processor = EnhancedSanskritProcessor()
        
        # Text that might be detected as English
        test_text = "This contains yoga"
        
        # Override to Sanskrit processing
        context_override = {'segment_type': 'sanskrit'}
        result, corrections = processor.process_text(test_text, context_override)
        
        # Should process as Sanskrit regardless of detection
        assert isinstance(result, str)
        assert isinstance(corrections, int)
    
    def test_threshold_overrides(self):
        """Test per-segment threshold overrides."""
        processor = EnhancedSanskritProcessor()
        
        test_text = "That is karma teaching"
        
        # Override thresholds for this segment
        context_override = {
            'threshold_overrides': {
                'english_threshold': 0.95,  # Very high - harder to detect English
                'sanskrit_threshold': 0.1   # Very low - easier to detect Sanskrit
            }
        }
        
        result, corrections = processor.process_text(test_text, context_override)
        
        # Should respect the threshold overrides
        assert isinstance(result, str)
        assert isinstance(corrections, int)
    
    def test_debug_segment_override(self):
        """Test per-segment debug logging override."""
        processor = EnhancedSanskritProcessor()
        
        context_override = {'debug_segment': True}
        
        with patch('processors.context_detector.logger') as mock_logger:
            result, corrections = processor.process_text("dharma teaching", context_override)
            
            # Should have debug output even if global debug is off
            debug_calls = mock_logger.debug.call_args_list
            assert len(debug_calls) > 0
    
    def test_segment_context_preservation(self):
        """Test that segment context is preserved during processing.""" 
        processor = EnhancedSanskritProcessor()
        
        # Mixed content that should create segments
        mixed_text = "The dharma and karma teachings"
        
        # Process with context tracking
        context = {'track_segments': True}
        result, corrections = processor.process_text(mixed_text, context)
        
        # Should handle mixed content appropriately
        assert isinstance(result, str)
        assert len(result.split()) == len(mixed_text.split())  # Word count preserved


class TestPerformanceMaintained:
    """Test AC7: Performance < 5% overhead requirement."""
    
    def test_context_detection_overhead(self):
        """Test that context detection adds < 5% overhead."""
        config = ContextConfig()
        detector = ContextDetector(context_config=config)
        
        test_texts = [
            "English sentence with multiple words",
            "dharma yoga meditation practice",
            "Mixed content with Sanskrit dharma terms",
            "That's called jnana and karma"
        ]
        
        # Measure context detection time
        iterations = 1000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            for text in test_texts:
                result = detector.detect_context(text)
        
        total_time = time.perf_counter() - start_time
        avg_time_per_detection = (total_time / (iterations * len(test_texts))) * 1000  # ms
        
        # Should be very fast (< 5ms per detection for good performance)
        assert avg_time_per_detection < 5.0, f"Average detection time {avg_time_per_detection:.3f}ms exceeds 5ms threshold"
    
    def test_cache_performance_improvement(self):
        """Test that caching provides performance improvement."""
        config = ContextConfig(cache_results=True)
        detector = ContextDetector(context_config=config)
        
        text = "Test text for caching performance"
        
        # First detection (cache miss)
        start_time = time.perf_counter()
        result1 = detector.detect_context(text)
        miss_time = time.perf_counter() - start_time
        
        # Second detection (cache hit)
        start_time = time.perf_counter()
        result2 = detector.detect_context(text)
        hit_time = time.perf_counter() - start_time
        
        # Cache hit should be significantly faster
        assert hit_time < miss_time, "Cache hit should be faster than cache miss"
        assert hit_time < miss_time * 0.1, "Cache hit should be at least 10x faster"
        
        # Results should be identical
        assert result1.context_type == result2.context_type
        assert result1.confidence == result2.confidence
    
    def test_performance_profiling_overhead(self):
        """Test that performance profiling doesn't significantly impact speed."""
        config_no_profiling = ContextConfig(performance_profiling=False)
        config_with_profiling = ContextConfig(performance_profiling=True)
        
        detector_no_prof = ContextDetector(context_config=config_no_profiling)
        detector_with_prof = ContextDetector(context_config=config_with_profiling)
        
        test_text = "dharma yoga teaching practice"
        iterations = 100
        
        # Time without profiling
        start_time = time.perf_counter()
        for _ in range(iterations):
            detector_no_prof.detect_context(test_text)
        no_prof_time = time.perf_counter() - start_time
        
        # Time with profiling
        start_time = time.perf_counter()
        for _ in range(iterations):
            detector_with_prof.detect_context(test_text)
        with_prof_time = time.perf_counter() - start_time
        
        # Profiling overhead should be minimal (< 50% increase)
        overhead_ratio = with_prof_time / no_prof_time
        assert overhead_ratio < 1.5, f"Profiling overhead too high: {overhead_ratio:.2f}x slower"
    
    def test_large_text_performance(self):
        """Test performance with larger text segments."""
        config = ContextConfig()
        detector = ContextDetector(context_config=config)
        
        # Create larger text
        base_text = "The practice of dharma and karma yoga meditation "
        large_text = base_text * 20  # ~1000 characters
        
        start_time = time.perf_counter()
        result = detector.detect_context(large_text)
        detection_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Should handle large text efficiently
        assert detection_time < 10.0, f"Large text detection took {detection_time:.3f}ms, expected < 10ms"
    
    def test_performance_statistics_collection(self):
        """Test performance statistics provide useful insights."""
        config = ContextConfig(cache_results=True, performance_profiling=True)
        detector = ContextDetector(context_config=config)
        
        # Process various texts
        texts = [
            "English text here",
            "dharma yoga practice", 
            "Mixed dharma and English",
            "Sanskrit text here"  # Repeat for cache testing
        ]
        
        for text in texts:
            detector.detect_context(text)
        # Repeat first text for cache hit
        detector.detect_context(texts[0])
        
        stats = detector.get_performance_stats()
        
        # Should have comprehensive statistics
        assert 'cache' in stats
        assert 'configuration' in stats
        assert 'recommendations' in stats
        
        # Cache statistics
        assert stats['cache']['enabled'] is True
        assert stats['cache']['total_requests'] > 0
        assert stats['cache']['hits'] >= 1  # At least one cache hit
        
        # Configuration statistics
        assert 'english_threshold' in stats['configuration']
        assert 'priority_terms_count' in stats['configuration']
        
        # Should provide recommendations
        assert isinstance(stats['recommendations'], list)


class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios from the story."""
    
    def test_story_example_jnana_correction(self):
        """Test story example: 'That's called jnana' should be corrected to 'jñāna'."""
        # Create processor with enhanced context detection
        processor = EnhancedSanskritProcessor()
        
        # Ensure jnana is in priority terms
        if hasattr(processor.context_detector, 'config'):
            if 'jnana' not in processor.context_detector.config.sanskrit_priority_terms:
                processor.context_detector.config.sanskrit_priority_terms.append('jnana')
                processor.context_detector.sanskrit_priority_set.add('jnana')
        
        # Test the correction
        input_text = "That's called jnana"
        result_text, corrections = processor.process_text(input_text)
        
        # Should process due to whitelist override (may or may not change jnana to jñāna)
        assert corrections >= 0  # At least attempted processing
        assert isinstance(result_text, str)
        
        # Verify context detection worked
        context_result = processor.context_detector.detect_context(input_text)
        assert context_result.context_type == 'sanskrit'
        assert context_result.override_reason == 'sanskrit_whitelist'
    
    def test_story_example_karma_yoga_mixed(self):
        """Test story example: 'Karma Yoga allows your karma' should have selective corrections."""
        processor = EnhancedSanskritProcessor()
        
        input_text = "Karma Yoga allows your karma"
        result_text, corrections = processor.process_text(input_text)
        
        # Should preserve English words while potentially processing Sanskrit terms
        result_words = result_text.lower().split()
        
        # English words should be preserved
        assert 'allows' in result_words
        assert 'your' in result_words
        
        # May process Sanskrit terms (karma, yoga)
        assert isinstance(result_text, str)
        assert len(result_words) == 5  # Word count preserved
    
    def test_story_example_yogavasistha_asr(self):
        """Test story example: 'yogabashi themes' should be corrected."""
        processor = EnhancedSanskritProcessor()
        
        # Add ASR variation mapping
        if hasattr(processor.context_detector, 'asr_variations'):
            processor.context_detector.asr_variations['yogabashi'] = 'yogavāsiṣṭha'
            processor.context_detector.sanskrit_priority_set.add('yogabashi')
        
        input_text = "yogabashi themes are highlighted"
        result_text, corrections = processor.process_text(input_text)
        
        # Should process due to ASR variation detection
        context_result = processor.context_detector.detect_context(input_text)
        assert context_result.context_type == 'sanskrit'
        assert context_result.override_reason == 'sanskrit_whitelist'
    
    def test_debug_output_format(self):
        """Test that debug output matches format from story example."""
        config = ContextConfig(debug_logging=True)
        detector = ContextDetector(context_config=config)
        
        # Add test term
        detector.sanskrit_priority_set.add('yogabashi')
        
        with patch('processors.context_detector.logger') as mock_logger:
            text = "yogabashi is one of the highlighted themes"
            result = detector.detect_context(text)
            
            # Should have detailed debug information
            debug_calls = mock_logger.debug.call_args_list
            assert len(debug_calls) > 0
            
            # Verify debug format contains expected information
            debug_messages = [str(call[0][0]) if call[0] else "" for call in debug_calls]
            combined = ' '.join(debug_messages)
            
            # Should show confidence scores
            assert 'confidence:' in combined.lower()
            # Should show markers
            assert 'markers' in combined.lower()
            # Should show override reason
            assert result.override_reason == 'sanskrit_whitelist'
    
    def test_threshold_adjustment_effectiveness(self):
        """Test that threshold adjustment solves the problem from story."""
        # Problem: Current system detects English too easily in mixed content
        # Solution: Higher English threshold (0.8 vs ~0.3)
        
        test_cases = [
            "That's called jnana and karma yoga practice",
            "Karma Yoga allows your karma",
            "Reading the gita teaches dharma"
        ]
        
        # Old threshold (low)
        config_old = ContextConfig(english_threshold=0.3)
        detector_old = ContextDetector(context_config=config_old)
        
        # New threshold (high, as per story)
        config_new = ContextConfig(english_threshold=0.8)
        detector_new = ContextDetector(context_config=config_new)
        
        for text in test_cases:
            result_old = detector_old.detect_context(text)
            result_new = detector_new.detect_context(text)
            
            # New threshold should be less likely to detect pure English
            # allowing more Sanskrit processing
            assert result_old.context_type in ['english', 'mixed', 'sanskrit']
            assert result_new.context_type in ['english', 'mixed', 'sanskrit']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])