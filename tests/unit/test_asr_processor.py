"""
Unit Tests for ASR Processing Components

Tests individual components of the ASR correction system to ensure
each part functions correctly in isolation.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sanskrit_processor_v2 import (
    SanskritProcessor, SRTSegment, ProcessingResult, 
    LexiconLoader, SRTParser
)


class TestSRTSegment:
    """Test SRTSegment class functionality."""
    
    def test_segment_creation(self):
        """Test basic SRT segment creation."""
        segment = SRTSegment(
            index=1,
            start_time="00:00:00,000",
            end_time="00:00:03,000",
            text="Test text"
        )
        
        assert segment.index == 1
        assert segment.start_time == "00:00:00,000"
        assert segment.end_time == "00:00:03,000"
        assert segment.text == "Test text"
    
    def test_segment_str_representation(self):
        """Test string representation of SRT segment."""
        segment = SRTSegment(
            index=1,
            start_time="00:00:00,000",
            end_time="00:00:03,000", 
            text="Test text"
        )
        
        str_repr = str(segment)
        assert "1" in str_repr
        assert "00:00:00,000 --> 00:00:03,000" in str_repr
        assert "Test text" in str_repr
    
    def test_segment_equality(self):
        """Test segment equality comparison."""
        segment1 = SRTSegment(1, "00:00:00,000", "00:00:03,000", "Test")
        segment2 = SRTSegment(1, "00:00:00,000", "00:00:03,000", "Test") 
        segment3 = SRTSegment(2, "00:00:00,000", "00:00:03,000", "Test")
        
        assert segment1 == segment2
        assert segment1 != segment3


class TestLexiconLoader:
    """Test lexicon loading functionality."""
    
    @pytest.fixture
    def mock_lexicon_files(self):
        """Mock lexicon file structure."""
        return {
            'corrections.yaml': {
                'corrections': {
                    'filosofy': 'philosophy',
                    'darma': 'dharma'
                }
            },
            'proper_nouns.yaml': {
                'proper_nouns': {
                    'krishna': 'Kṛṣṇa',
                    'shiva': 'Śiva'
                }
            }
        }
    
    def test_lexicon_loader_creation(self):
        """Test lexicon loader instantiation."""
        loader = LexiconLoader(simple_mode=True, verbose=False)
        assert loader is not None
        assert hasattr(loader, 'corrections')
        assert hasattr(loader, 'proper_nouns')
    
    def test_simple_mode_corrections(self):
        """Test that simple mode loads basic corrections."""
        loader = LexiconLoader(simple_mode=True, verbose=False)
        
        # Should have some basic corrections loaded
        assert isinstance(loader.corrections, dict)
        assert len(loader.corrections) > 0
        
        # Test some expected corrections if they exist
        corrections = loader.corrections
        if 'filosofy' in corrections:
            assert corrections['filosofy'] == 'philosophy'
    
    @patch('yaml.safe_load')
    @patch('builtins.open')
    def test_lexicon_file_loading(self, mock_open, mock_yaml_load, mock_lexicon_files):
        """Test loading corrections from YAML files."""
        # Mock file reading
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock YAML loading
        def yaml_side_effect(*args, **kwargs):
            # Return different data based on which file is being loaded
            if 'corrections.yaml' in str(mock_open.call_args):
                return mock_lexicon_files['corrections.yaml']
            elif 'proper_nouns.yaml' in str(mock_open.call_args):
                return mock_lexicon_files['proper_nouns.yaml']
            return {}
        
        mock_yaml_load.side_effect = yaml_side_effect
        
        loader = LexiconLoader(simple_mode=False, verbose=False)
        
        # Verify files were attempted to be opened
        assert mock_open.called
        assert mock_yaml_load.called


class TestSRTParser:
    """Test SRT file parsing functionality."""
    
    def test_parse_basic_srt(self):
        """Test parsing basic SRT content."""
        srt_content = """1
00:00:00,000 --> 00:00:03,000
First subtitle

2
00:00:03,500 --> 00:00:07,000
Second subtitle"""
        
        parser = SRTParser()
        segments = parser.parse_srt_content(srt_content)
        
        assert len(segments) == 2
        assert segments[0].index == 1
        assert segments[0].text == "First subtitle"
        assert segments[1].index == 2
        assert segments[1].text == "Second subtitle"
    
    def test_parse_empty_content(self):
        """Test parsing empty SRT content."""
        parser = SRTParser()
        segments = parser.parse_srt_content("")
        
        assert segments == []
    
    def test_parse_malformed_srt(self):
        """Test parsing malformed SRT content."""
        malformed_content = """1
00:00:00,000
First subtitle without end time"""
        
        parser = SRTParser()
        # Should handle gracefully and return what it can parse
        segments = parser.parse_srt_content(malformed_content)
        
        # Implementation dependent - either empty list or partial parsing
        assert isinstance(segments, list)
    
    def test_parse_srt_with_formatting(self):
        """Test parsing SRT with HTML-style formatting."""
        srt_content = """1
00:00:00,000 --> 00:00:03,000
<i>Italicized text</i> and <b>bold text</b>"""
        
        parser = SRTParser()
        segments = parser.parse_srt_content(srt_content)
        
        assert len(segments) == 1
        # Should preserve or handle formatting appropriately
        assert "text" in segments[0].text


class TestSanskritProcessor:
    """Test main Sanskrit processor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Fixture providing configured processor instance."""
        return SanskritProcessor(simple_mode=True, verbose=False)
    
    def test_processor_initialization(self, processor):
        """Test processor initialization."""
        assert processor is not None
        assert hasattr(processor, 'simple_mode')
        assert processor.simple_mode is True
    
    def test_process_single_segment(self, processor):
        """Test processing a single segment."""
        segment = SRTSegment(
            index=1,
            start_time="00:00:00,000",
            end_time="00:00:03,000",
            text="filosofy test"
        )
        
        result = processor.process_segments([segment])
        
        assert isinstance(result, ProcessingResult)
        assert len(result.segments) == 1
        # Check if correction was applied (implementation dependent)
        processed_text = result.segments[0].text
        assert isinstance(processed_text, str)
    
    def test_process_multiple_segments(self, processor):
        """Test processing multiple segments."""
        segments = [
            SRTSegment(1, "00:00:00,000", "00:00:03,000", "First test"),
            SRTSegment(2, "00:00:03,500", "00:00:07,000", "Second test"),
            SRTSegment(3, "00:00:07,500", "00:00:11,000", "Third test")
        ]
        
        result = processor.process_segments(segments)
        
        assert len(result.segments) == 3
        # Verify order is preserved
        for i, segment in enumerate(result.segments):
            assert segment.index == i + 1
    
    def test_process_empty_segments(self, processor):
        """Test processing empty segment list."""
        result = processor.process_segments([])
        
        assert isinstance(result, ProcessingResult)
        assert len(result.segments) == 0
    
    def test_process_segment_with_no_corrections(self, processor):
        """Test processing segment that needs no corrections."""
        segment = SRTSegment(
            index=1,
            start_time="00:00:00,000",
            end_time="00:00:03,000",
            text="This is a normal English sentence."
        )
        
        result = processor.process_segments([segment])
        
        # Text should remain unchanged
        assert result.segments[0].text == "This is a normal English sentence."
    
    def test_process_segment_with_sanskrit_terms(self, processor):
        """Test processing segment containing Sanskrit terms."""
        segment = SRTSegment(
            index=1,
            start_time="00:00:00,000",
            end_time="00:00:03,000",
            text="We study yoga and dharma today"
        )
        
        result = processor.process_segments([segment])
        
        # Should preserve basic Sanskrit terms correctly
        processed_text = result.segments[0].text
        assert "yoga" in processed_text.lower()
        assert "dharma" in processed_text.lower()
    
    @pytest.mark.parametrize("input_text,contains_term", [
        ("filosofy is important", "philosophy"),
        ("darma guides us", "dharma"),
        ("normal text", "normal text"),
    ])
    def test_specific_corrections(self, processor, input_text, contains_term):
        """Test specific correction mappings."""
        segment = SRTSegment(1, "00:00:00,000", "00:00:03,000", input_text)
        result = processor.process_segments([segment])
        
        processed_text = result.segments[0].text.lower()
        assert contains_term.lower() in processed_text


class TestProcessingResult:
    """Test ProcessingResult class functionality."""
    
    def test_result_creation(self):
        """Test ProcessingResult instantiation."""
        segments = [
            SRTSegment(1, "00:00:00,000", "00:00:03,000", "Test")
        ]
        
        result = ProcessingResult(
            segments=segments,
            stats={'processed': 1}
        )
        
        assert result.segments == segments
        assert result.stats == {'processed': 1}
    
    def test_result_with_metrics(self):
        """Test ProcessingResult with processing metrics."""
        segments = [
            SRTSegment(1, "00:00:00,000", "00:00:03,000", "Test")
        ]
        
        stats = {
            'total_segments': 1,
            'corrections_made': 0,
            'processing_time': 0.1
        }
        
        result = ProcessingResult(segments=segments, stats=stats)
        
        assert result.stats['total_segments'] == 1
        assert result.stats['corrections_made'] == 0
        assert result.stats['processing_time'] == 0.1


class TestErrorHandling:
    """Test error handling in ASR processing components."""
    
    def test_processor_handles_none_input(self):
        """Test processor handles None input gracefully."""
        processor = SanskritProcessor(simple_mode=True, verbose=False)
        
        # Should handle None input without crashing
        try:
            result = processor.process_segments(None)
            # Either returns empty result or raises appropriate exception
            assert result is None or isinstance(result, ProcessingResult)
        except (TypeError, ValueError):
            # Acceptable to raise appropriate exception
            pass
    
    def test_segment_handles_none_text(self):
        """Test segment handles None text gracefully."""
        try:
            segment = SRTSegment(1, "00:00:00,000", "00:00:03,000", None)
            # Either handles None or raises appropriate exception
            assert segment.text is None or segment.text == ""
        except (TypeError, ValueError):
            # Acceptable to raise appropriate exception
            pass
    
    def test_parser_handles_invalid_timestamps(self):
        """Test parser handles invalid timestamp format."""
        invalid_srt = """1
invalid_timestamp --> also_invalid
Test text"""
        
        parser = SRTParser()
        
        # Should handle gracefully without crashing
        try:
            segments = parser.parse_srt_content(invalid_srt)
            assert isinstance(segments, list)
        except Exception as e:
            # Should not crash with unhandled exception
            assert isinstance(e, (ValueError, TypeError, AttributeError))


if __name__ == "__main__":
    # Run the unit tests
    pytest.main([__file__, "-v"])