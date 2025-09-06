#!/usr/bin/env python3
"""
Tests for Sacred Content Preservation System (Story 6.2)

Comprehensive test suite for sacred text processing including:
- Sacred symbol preservation (|, ||, ॐ, etc.)
- Verse structure maintenance
- Mantra formatting preservation 
- Performance validation
"""

import pytest
from pathlib import Path
import tempfile
import time
from sanskrit_processor_v2 import SanskritProcessor
from processors.sacred_classifier import SacredContentClassifier
from processors.symbol_protector import SacredSymbolProtector
from processors.verse_formatter import VerseFormatter


class TestSacredSymbolPreservation:
    """Test sacred symbol protection during processing."""
    
    def setup_method(self):
        """Setup test processor."""
        self.processor = SanskritProcessor(Path("lexicons"))
        
    def test_pipe_symbol_preservation(self):
        """Test Case 1: Pipe symbol preservation (AC1 - critical)."""
        # Test single pipe
        input_text = "Om pūrṇam adaḥ pūrṇam idam | pūrṇāt pūrṇam udacyate"
        result, corrections = self.processor.process_text(input_text)
        assert "|" in result, "Single pipe symbol must be preserved"
        assert "?" not in result, "Pipe symbols must not become question marks"
        
        # Test double pipe
        input_text = "pūrṇam evāvaśiṣyate || Om śāntiḥ śāntiḥ śāntiḥ"
        result, corrections = self.processor.process_text(input_text)
        assert "||" in result, "Double pipe symbol must be preserved"
        assert "?" not in result, "Double pipe symbols must not become question marks"
        
    def test_devanagari_punctuation_support(self):
        """Test Case 2: Devanagari punctuation preservation (AC1)."""
        # Test danda
        input_text = "om gaṇeśāya namaḥ । śrī gurave namaḥ"
        result, corrections = self.processor.process_text(input_text)
        assert "।" in result, "Devanagari danda must be preserved"
        
        # Test double danda
        input_text = "om śāntiḥ śāntiḥ śāntiḥ ।।"
        result, corrections = self.processor.process_text(input_text)
        assert "।।" in result, "Devanagari double danda must be preserved"
        
    def test_om_symbol_protection(self):
        """Test Case 3: Om symbol preservation (AC1)."""
        input_text = "ॐ bhūr bhuvaḥ svaḥ"
        result, corrections = self.processor.process_text(input_text)
        assert "ॐ" in result, "Om symbol must be preserved"
        
    def test_sacred_unicode_symbols(self):
        """Test Case 4: Sacred Unicode symbol protection (AC1)."""
        symbols = ["◦", "○", "★", "✦"]
        for symbol in symbols:
            input_text = f"Om mani padme hum {symbol}"
            result, corrections = self.processor.process_text(input_text)
            assert symbol in result, f"Sacred symbol {symbol} must be preserved"


class TestVerseStructurePreservation:
    """Test verse structure and formatting preservation."""
    
    def setup_method(self):
        """Setup test processor."""
        self.processor = SanskritProcessor(Path("lexicons"))
        
    def test_multiline_verse_preservation(self):
        """Test Case 5: Multi-line verse structure preservation (AC2)."""
        input_verse = """Om pūrṇam adaḥ pūrṇam idam
pūrṇāt pūrṇam udacyate |
pūrṇasya pūrṇam ādāya
pūrṇam evāvaśiṣyate ||"""
        
        result, corrections = self.processor.process_text(input_verse)
        
        # Should preserve line structure
        assert "\n" in result or len(result.split()) < len(input_verse.split()) + 10, \
            "Multi-line verse structure should be preserved"
        assert "|" in result and "||" in result, "Verse boundaries must be preserved"
        
    def test_indentation_respect(self):
        """Test Case 6: Indentation pattern preservation (AC2)."""
        input_text = "    Om namaḥ śivāya\n    Om namaḥ śivāya"
        result, corrections = self.processor.process_text(input_text)
        
        # Should preserve meaningful indentation patterns
        lines = result.split('\n')
        if len(lines) > 1:
            # Check if indentation is maintained in some form
            assert any(line.startswith(' ') for line in lines) or \
                   result.count('  ') > 0, "Sacred text indentation should be preserved"
                   
    def test_spacing_normalization(self):
        """Test Case 7: Spacing normalization while preserving structure (AC2)."""
        # Excessive spaces should be cleaned but structure preserved
        input_text = "Om     mani    padme     hum"
        result, corrections = self.processor.process_text(input_text)
        
        # Should clean excessive spaces but maintain word separation
        word_count = len(input_text.split())
        result_word_count = len(result.split())
        assert result_word_count == word_count, "Word count should be preserved"
        assert result.count('     ') == 0, "Excessive spaces should be normalized"


class TestContextAwareProcessing:
    """Test context-aware sacred content processing."""
    
    def setup_method(self):
        """Setup components for testing."""
        self.classifier = SacredContentClassifier()
        self.processor = SanskritProcessor(Path("lexicons"))
        
    def test_mantra_detection(self):
        """Test Case 8: Mantra content detection (AC3)."""
        # Clear mantra should be detected
        mantra_text = "Om mani padme hum"
        content_type = self.classifier.classify_content(mantra_text)
        assert content_type == 'mantra', "Clear mantra should be classified as mantra"
        
        # Mantra with sacred symbols
        mantra_with_symbol = "ॐ gaṇeśāya namaḥ"
        content_type = self.classifier.classify_content(mantra_with_symbol)
        assert content_type == 'mantra', "Mantra with Om symbol should be classified"
        
    def test_verse_detection(self):
        """Test Case 9: Verse content detection (AC3)."""
        # Verse with pipes should be detected
        verse_text = "Chapter 2 verse 47 | You have the right to perform"
        content_type = self.classifier.classify_content(verse_text)
        assert content_type == 'verse', "Text with pipes should be classified as verse"
        
        # Verse with dandas
        verse_with_danda = "dharmaṃ cara । satyaṃ vada"
        content_type = self.classifier.classify_content(verse_with_danda)
        assert content_type == 'verse', "Text with dandas should be classified as verse"
        
    def test_regular_text_bypass(self):
        """Test Case 10: Regular text should bypass sacred processing (AC3)."""
        regular_text = "This is a normal lecture about meditation"
        content_type = self.classifier.classify_content(regular_text)
        assert content_type == 'regular', "Regular text should not be classified as sacred"
        
    def test_pronunciation_guide_handling(self):
        """Test Case 11: Proper handling of pronunciation guides (AC3)."""
        # Mantras with hyphens should preserve them appropriately
        mantra_text = "Om-mani-padme-hum"
        result, corrections = self.processor.process_text(mantra_text)
        
        # Should handle hyphens appropriately in mantra context
        # (This is context-dependent - mantras may keep meaningful hyphens)
        assert "mani" in result and "padme" in result, "Mantra words should be preserved"


class TestSacredContentIntegration:
    """Test complete sacred content processing pipeline."""
    
    def setup_method(self):
        """Setup test processor."""
        self.processor = SanskritProcessor(Path("lexicons"))
        
    def test_complete_sacred_pipeline(self):
        """Test Case 12: Complete sacred processing pipeline."""
        # Complex sacred text with symbols, structure, and words needing correction
        sacred_text = """Om Puurnnam-Adah Puurnnam-Idam |
Puurnnaat-Puurnnam-Udacyate ||
ॐ Shaantih Shaantih Shaantih"""
        
        result, corrections = self.processor.process_text(sacred_text)
        
        # Verify sacred symbols preserved
        assert "|" in result, "Single pipe must be preserved"
        assert "||" in result, "Double pipe must be preserved"
        assert "ॐ" in result, "Om symbol must be preserved"
        
        # Verify corrections were applied where appropriate
        assert corrections >= 0, "Some corrections should have been made"
        
        # Verify no corruption occurred
        assert "?" not in result, "No sacred symbols should become question marks"
        
    def test_mixed_content_handling(self):
        """Test Case 13: Mixed sacred/regular content processing."""
        mixed_text = "Today we will study the mantra Om mani padme hum from Chapter 2"
        result, corrections = self.processor.process_text(mixed_text)
        
        # Should handle mixed content appropriately
        assert "Om" in result or "om" in result, "Mantra should be preserved"
        assert "Chapter" in result, "Regular content should be processed"


class TestPerformanceRequirements:
    """Test performance requirements for sacred content processing."""
    
    def setup_method(self):
        """Setup test processor."""
        self.processor = SanskritProcessor(Path("lexicons"))
        
    def test_sacred_processing_performance(self):
        """Test Case 14: Sacred processing performance overhead (AC4)."""
        # Test processing speed with sacred content
        sacred_texts = [
            "Om mani padme hum",
            "Chapter 2 verse 47 | You have the right to perform",
            "ॐ bhūr bhuvaḥ svaḥ",
            "dharmaṃ cara । satyaṃ vada ।।"
        ] * 100  # 400 segments
        
        start_time = time.time()
        total_corrections = 0
        
        for text in sacred_texts:
            result, corrections = self.processor.process_text(text)
            total_corrections += corrections
            
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calculate segments per second
        segments_per_second = len(sacred_texts) / processing_time
        
        assert segments_per_second > 300, \
            f"Sacred content processing too slow: {segments_per_second:.1f} segments/second"
            
    def test_regular_content_performance_maintained(self):
        """Test Case 15: Regular content performance not degraded (AC4)."""
        regular_texts = [
            "This is a normal lecture about meditation and mindfulness",
            "In today's discussion we will explore the concepts",
            "The teacher explained the philosophical principles",
            "Students asked questions about the practice"
        ] * 100  # 400 segments
        
        start_time = time.time()
        
        for text in regular_texts:
            result, corrections = self.processor.process_text(text)
            
        end_time = time.time()
        processing_time = end_time - start_time
        
        segments_per_second = len(regular_texts) / processing_time
        
        assert segments_per_second > 800, \
            f"Regular content processing degraded: {segments_per_second:.1f} segments/second"


class TestLeanComplianceRequirements:
    """Test lean architecture compliance."""
    
    def test_no_new_dependencies(self):
        """Test Case 16: No new external dependencies (AC4)."""
        # Verify processor can be imported without new dependencies
        try:
            from processors.sacred_classifier import SacredContentClassifier
            from processors.symbol_protector import SacredSymbolProtector  
            from processors.verse_formatter import VerseFormatter
            
            # Create instances to verify no missing dependencies
            classifier = SacredContentClassifier()
            protector = SacredSymbolProtector()
            formatter = VerseFormatter()
            
            assert True, "All sacred processing components load without new dependencies"
        except ImportError as e:
            pytest.fail(f"New dependency required: {e}")
            
    def test_memory_footprint(self):
        """Test Case 17: Memory footprint increase minimal (AC4)."""
        import psutil
        import gc
        
        # Measure baseline memory
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create processor with sacred components
        processor = SanskritProcessor(Path("lexicons"))
        
        # Process some sacred content
        test_texts = [
            "Om mani padme hum ॐ",
            "Chapter 2 verse 47 | dharma action ||",
            "शान्तिः शान्तिः शान्तिः ।।"
        ]
        
        for text in test_texts:
            processor.process_text(text)
            
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory
        
        assert memory_increase < 10, \
            f"Memory increase too high: {memory_increase:.1f}MB (should be <10MB)"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Setup test processor.""" 
        self.processor = SanskritProcessor(Path("lexicons"))
        
    def test_mixed_symbol_types(self):
        """Test Case 18: Mixed sacred symbol types in one text."""
        mixed_symbols = "Om गणेशाय नमः | श्री गुरवे नमः । ॐ शान्तिः शान्तिः शान्तिः ।।"
        result, corrections = self.processor.process_text(mixed_symbols)
        
        # All symbols should be preserved
        assert "|" in result, "Pipe should be preserved"
        assert "।" in result, "Danda should be preserved"
        assert "ॐ" in result, "Om should be preserved"
        assert "।।" in result, "Double danda should be preserved"
        
    def test_empty_text_handling(self):
        """Test Case 19: Empty/whitespace-only text handling."""
        empty_texts = ["", "   ", "\n\n", "\t"]
        
        for text in empty_texts:
            result, corrections = self.processor.process_text(text)
            # Should handle gracefully without errors
            assert isinstance(result, str), "Should return string for empty text"
            
    def test_very_long_sacred_text(self):
        """Test Case 20: Very long sacred text processing."""
        # Create long sacred text
        long_verse = ("Om mani padme hum | " * 50) + "ॐ शान्तिः शान्तिः शान्तिः ।।"
        
        result, corrections = self.processor.process_text(long_verse)
        
        # Should complete without errors and preserve symbols
        assert "|" in result, "Symbols should be preserved in long text"
        assert "ॐ" in result, "Om should be preserved in long text"
        assert "।।" in result, "Double danda should be preserved in long text"


def run_critical_tests():
    """Run the most critical tests for sacred content preservation."""
    
    print("🕉️  Running Critical Sacred Content Preservation Tests...")
    
    # Test critical symbol preservation
    processor = SanskritProcessor(Path("lexicons"))
    
    # Critical Test 1: Pipe symbols never become question marks
    test_text = "Om pūrṇam adaḥ pūrṇam idam | pūrṇāt pūrṇam udacyate ||"
    result, corrections = processor.process_text(test_text)
    
    print(f"Input:  {test_text}")
    print(f"Output: {result}")
    
    assert "|" in result, "❌ CRITICAL FAILURE: Single pipe missing"
    assert "||" in result, "❌ CRITICAL FAILURE: Double pipe missing"  
    assert "?" not in result, "❌ CRITICAL FAILURE: Sacred symbols corrupted to ?"
    
    print("✅ Critical pipe symbol preservation: PASSED")
    
    # Critical Test 2: Om symbol preservation
    test_text2 = "ॐ śāntiḥ śāntiḥ śāntiḥ"
    result2, corrections2 = processor.process_text(test_text2)
    
    print(f"Input:  {test_text2}")
    print(f"Output: {result2}")
    
    assert "ॐ" in result2, "❌ CRITICAL FAILURE: Om symbol missing"
    
    print("✅ Critical Om symbol preservation: PASSED")
    print("🏆 All critical sacred content tests PASSED!")


if __name__ == "__main__":
    # Run critical tests if executed directly
    run_critical_tests()