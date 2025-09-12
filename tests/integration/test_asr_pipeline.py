"""
Integration Tests for ASR Processing Pipeline

Tests the complete end-to-end ASR correction pipeline to ensure
all components work together correctly.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sanskrit_processor_v2 import SanskritProcessor, SRTSegment
from utils.srt_parser import SRTParser


class TestASRPipelineIntegration:
    """Test complete ASR processing pipeline integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Provide temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_srt_content(self):
        """Provide sample SRT content with ASR errors."""
        return """1
00:00:00,000 --> 00:00:03,000
Welcome to the study of filosofy

2
00:00:03,500 --> 00:00:07,000
Today we learn about darma and krisna

3
00:00:07,500 --> 00:00:11,000
The BHAGAVAD GITA teaches us yoga

4
00:00:11,500 --> 00:00:15,000
Through pranayama we achieve samadhi"""
    
    def test_end_to_end_srt_processing(self, temp_dir, sample_srt_content):
        """Test complete SRT file processing pipeline."""
        # Create test input file
        input_file = temp_dir / "test_input.srt"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(sample_srt_content)
        
        # Process with simple mode
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        
        # Parse SRT content
        parser = SRTParser()
        segments = parser.parse_srt_file(str(input_file))
        
        # Process segments
        result = processor.process_segments(segments)
        
        # Verify processing results
        assert len(result.segments) == 4
        
        # Check specific corrections
        segment_texts = [seg.text for seg in result.segments]
        
        # filosofy should be corrected to philosophy
        assert any('philosophy' in text.lower() for text in segment_texts)
        
        # darma should be corrected to dharma
        assert any('dharma' in text.lower() for text in segment_texts)
        
        # Should preserve timing information
        for original_seg, processed_seg in zip(segments, result.segments):
            assert processed_seg.start_time == original_seg.start_time
            assert processed_seg.end_time == original_seg.end_time
            assert processed_seg.index == original_seg.index
    
    def test_pipeline_with_real_golden_dataset_sample(self, temp_dir):
        """Test pipeline with sample from golden dataset."""
        # Create test file using golden dataset examples
        golden_examples = [
            "In the study of filosofy we find darma",
            "The sage wasistha teaches about jnana", 
            "YOGA VASISTHA contains ancient wisdom",
            "Through pranayama we reach samadhi"
        ]
        
        srt_content = ""
        for i, text in enumerate(golden_examples, 1):
            start_sec = (i-1) * 4
            end_sec = start_sec + 3
            srt_content += f"{i}\n"
            srt_content += f"00:00:{start_sec:02d},000 --> 00:00:{end_sec:02d},000\n"
            srt_content += f"{text}\n\n"
        
        input_file = temp_dir / "golden_sample.srt"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        # Process pipeline
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        parser = SRTParser()
        
        segments = parser.parse_srt_file(str(input_file))
        result = processor.process_segments(segments)
        
        # Verify corrections were applied
        processed_texts = [seg.text for seg in result.segments]
        
        # Check that at least some corrections were made
        corrections_found = 0
        
        # Look for expected corrections
        expected_corrections = [
            ('filosofy', 'philosophy'),
            ('darma', 'dharma'),
            ('wasistha', 'vāsiṣṭha'),  # May be corrected
            ('jnana', 'jñāna'),       # May be corrected
            ('pranayama', 'prāṇāyāma'), # May be corrected
            ('samadhi', 'samādhi')     # May be corrected
        ]
        
        all_text = ' '.join(processed_texts).lower()
        
        for original, corrected in expected_corrections:
            if original in golden_examples[0].lower() and corrected.lower() in all_text:
                corrections_found += 1
        
        # Should have made at least some corrections
        assert corrections_found >= 1, f"Expected corrections not found in: {processed_texts}"
    
    def test_pipeline_error_handling(self, temp_dir):
        """Test pipeline handles errors gracefully."""
        # Test with malformed SRT
        malformed_srt = """1
Invalid timestamp format
Some text content

2
00:00:03,500 --> 00:00:07,000
Valid segment after malformed one"""
        
        input_file = temp_dir / "malformed.srt"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(malformed_srt)
        
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        parser = SRTParser()
        
        # Should handle gracefully without crashing
        try:
            segments = parser.parse_srt_file(str(input_file))
            result = processor.process_segments(segments)
            
            # Should return some result even with malformed input
            assert isinstance(result.segments, list)
            
        except Exception as e:
            # If it raises an exception, it should be a handled exception type
            assert isinstance(e, (ValueError, TypeError, AttributeError))
    
    def test_pipeline_preserves_formatting(self, temp_dir):
        """Test that pipeline preserves SRT formatting correctly."""
        formatted_srt = """1
00:00:00,000 --> 00:00:03,000
<i>Italicized filosofy text</i>

2
00:00:03,500 --> 00:00:07,000
<b>Bold darma content</b> with normal text"""
        
        input_file = temp_dir / "formatted.srt" 
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(formatted_srt)
        
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        parser = SRTParser()
        
        segments = parser.parse_srt_file(str(input_file))
        result = processor.process_segments(segments)
        
        # Should preserve HTML formatting tags
        processed_texts = [seg.text for seg in result.segments]
        
        assert any('<i>' in text and '</i>' in text for text in processed_texts)
        assert any('<b>' in text and '</b>' in text for text in processed_texts)
    
    def test_pipeline_performance_integration(self, temp_dir):
        """Test pipeline performance with realistic file size."""
        # Generate medium-sized test file
        segments_count = 200
        srt_content = ""
        
        test_phrases = [
            "The study of filosofy and darma",
            "Ancient wisdom from wasistha", 
            "Teachings of krisna in bhagavat",
            "Practice of pranayama and yoga",
            "Path to moksha through sadhana"
        ]
        
        for i in range(1, segments_count + 1):
            start_sec = (i-1) * 3
            end_sec = start_sec + 2
            
            minutes = start_sec // 60
            seconds = start_sec % 60
            end_minutes = end_sec // 60
            end_seconds = end_sec % 60
            
            text = test_phrases[(i-1) % len(test_phrases)]
            
            srt_content += f"{i}\n"
            srt_content += f"00:{minutes:02d}:{seconds:02d},000 --> 00:{end_minutes:02d}:{end_seconds:02d},000\n"
            srt_content += f"{text}\n\n"
        
        input_file = temp_dir / "performance_test.srt"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        # Time the processing
        import time
        
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        parser = SRTParser()
        
        start_time = time.time()
        segments = parser.parse_srt_file(str(input_file))
        parsing_time = time.time() - start_time
        
        start_time = time.time()
        result = processor.process_segments(segments)
        processing_time = time.time() - start_time
        
        # Performance assertions
        assert len(result.segments) == segments_count
        assert parsing_time < 1.0, f"Parsing took {parsing_time:.2f}s, should be < 1.0s"
        assert processing_time < 5.0, f"Processing took {processing_time:.2f}s, should be < 5.0s"
        
        processing_speed = len(result.segments) / processing_time
        assert processing_speed > 50, f"Processing speed {processing_speed:.1f} segments/sec below 50/sec"
    
    def test_pipeline_output_format_consistency(self, temp_dir):
        """Test that pipeline maintains consistent output format."""
        input_srt = """1
00:00:00,000 --> 00:00:03,000
Test filosofy content

2
00:00:03,500 --> 00:00:07,000
More darma material"""
        
        input_file = temp_dir / "consistency_test.srt"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(input_srt)
        
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        parser = SRTParser()
        
        segments = parser.parse_srt_file(str(input_file))
        result = processor.process_segments(segments)
        
        # Write output and verify format
        output_file = temp_dir / "output.srt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for segment in result.segments:
                f.write(f"{segment.index}\n")
                f.write(f"{segment.start_time} --> {segment.end_time}\n") 
                f.write(f"{segment.text}\n\n")
        
        # Re-parse output to verify format consistency
        output_segments = parser.parse_srt_file(str(output_file))
        
        assert len(output_segments) == len(result.segments)
        
        for original, reparsed in zip(result.segments, output_segments):
            assert original.index == reparsed.index
            assert original.start_time == reparsed.start_time
            assert original.end_time == reparsed.end_time
            assert original.text == reparsed.text


class TestConfigurationIntegration:
    """Test integration with different configuration modes."""
    
    def test_simple_mode_integration(self):
        """Test simple mode configuration integration."""
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        
        # Simple mode should work with basic corrections
        segment = SRTSegment(1, "00:00:00,000", "00:00:03,000", "Test filosofy")
        result = processor.process_segments([segment])
        
        assert len(result.segments) == 1
        # Should work without external dependencies
        assert isinstance(result.segments[0].text, str)
    
    def test_configuration_error_handling(self):
        """Test handling of configuration errors."""
        # Test with invalid configuration
        try:
            processor = SanskritProcessor(simple_mode=False, verbose=False)
            
            # Should either work or fail gracefully
            segment = SRTSegment(1, "00:00:00,000", "00:00:03,000", "Test")
            result = processor.process_segments([segment])
            
            assert isinstance(result.segments, list)
            
        except Exception as e:
            # Should be a configuration-related error, not a crash
            assert 'config' in str(e).lower() or 'mode' in str(e).lower()


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])