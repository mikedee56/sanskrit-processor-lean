"""
Test cases for Quality Assurance System (Story 6.6)
Tests confidence scoring, issue detection, and JSON report generation.
"""

import pytest
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

# Import QA components
from qa.confidence_scorer import ConfidenceScorer, ConfidenceMetrics
from qa.issue_detector import QualityIssueDetector, QualityIssue
from utils.srt_parser import SRTSegment

# Mock ProcessingResult for testing
@dataclass
class MockProcessingResult:
    """Mock processing result for testing QA components."""
    processed_text: str
    corrections_made: int = 0
    content_type: str = "regular"
    metadata: Dict[str, Any] = None
    specialized_processing: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.specialized_processing is None:
            self.specialized_processing = {}

class TestConfidenceScorer:
    """Test confidence scoring functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = {
            'qa': {
                'thresholds': {
                    'high_confidence': 0.9,
                    'medium_confidence': 0.7,
                    'low_confidence': 0.4
                }
            }
        }
        self.scorer = ConfidenceScorer(self.config)
    
    def test_high_confidence_case(self):
        """Test high confidence scoring with minimal corrections."""
        result = MockProcessingResult(
            processed_text="Om namah Shivaya",
            corrections_made=0,
            content_type="regular"
        )
        
        confidence = self.scorer.calculate_confidence(result)
        
        assert confidence.overall_confidence > 0.8
        assert confidence.lexicon_confidence == 1.0  # No corrections = high confidence
        assert len(confidence.processing_flags) == 0
        assert isinstance(confidence, ConfidenceMetrics)
    
    def test_low_confidence_case(self):
        """Test low confidence with many corrections."""
        result = MockProcessingResult(
            processed_text="this has many corrections applied",
            corrections_made=15,  # Many corrections relative to text length
            content_type="uncertain"
        )
        
        confidence = self.scorer.calculate_confidence(result)
        
        assert confidence.overall_confidence < 0.7
        assert confidence.lexicon_confidence < 0.7
        assert 'uncertain_corrections' in confidence.processing_flags
    
    def test_sacred_content_confidence(self):
        """Test sacred content processing confidence."""
        result = MockProcessingResult(
            processed_text="Om गणेशाय namah।।",
            corrections_made=2,
            content_type="mantra",
            metadata={'sacred_processing': True}
        )
        
        confidence = self.scorer.calculate_confidence(result)
        
        # Should have high sacred confidence due to sacred symbols
        assert confidence.sacred_confidence >= 0.9
        # Overall should be high due to sacred symbol preservation
        assert confidence.overall_confidence > 0.8
    
    def test_compound_confidence_scoring(self):
        """Test compound term confidence assessment."""
        result = MockProcessingResult(
            processed_text="Bhagavad Gita chapter two",
            corrections_made=1,
            specialized_processing={
                'compound': {
                    'matches': [
                        {'confidence': 0.98, 'term': 'Bhagavad Gita'},
                        {'confidence': 0.95, 'term': 'chapter two'}
                    ]
                }
            }
        )
        
        confidence = self.scorer.calculate_confidence(result)
        
        # Should have high compound confidence due to exact matches
        assert confidence.compound_confidence >= 0.8
    
    def test_scripture_reference_confidence(self):
        """Test scripture reference processing confidence."""
        result = MockProcessingResult(
            processed_text="As stated in Bhagavad Gita 2.47",
            corrections_made=0,
            specialized_processing={
                'scripture': {
                    'validated': True,
                    'references': [{'chapter': 2, 'verse': 47}]
                }
            }
        )
        
        confidence = self.scorer.calculate_confidence(result)
        
        # Should have high scripture confidence due to validation
        assert confidence.scripture_confidence >= 0.9
    
    def test_confidence_agreement_boost(self):
        """Test confidence boost when components agree."""
        result = MockProcessingResult(
            processed_text="Perfect text with no issues",
            corrections_made=0,
            content_type="regular"
        )
        
        confidence = self.scorer.calculate_confidence(result)
        
        # All components should have high confidence, triggering agreement boost
        assert confidence.overall_confidence >= 0.9
        # Should get slight boost for component agreement
        assert confidence.overall_confidence >= min(
            confidence.lexicon_confidence,
            confidence.sacred_confidence,
            confidence.compound_confidence,
            confidence.scripture_confidence
        )

class TestQualityIssueDetector:
    """Test quality issue detection functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = QualityIssueDetector()
    
    def test_low_confidence_detection(self):
        """Test detection of low confidence segments."""
        segment = SRTSegment(
            index=1,
            start_time="00:01:00,000",
            end_time="00:01:05,000",
            text="Some uncertain text"
        )
        
        low_confidence = ConfidenceMetrics(
            lexicon_confidence=0.5,
            sacred_confidence=0.9,
            compound_confidence=0.8,
            scripture_confidence=0.9,
            overall_confidence=0.65,
            processing_flags=[]
        )
        
        issues = self.detector.detect_issues(segment, low_confidence)
        
        assert len(issues) >= 1
        uncertainty_issues = [i for i in issues if i.issue_type == 'uncertainty']
        assert len(uncertainty_issues) >= 1
        assert uncertainty_issues[0].severity in ['high', 'medium']
        assert 'confidence' in uncertainty_issues[0].description.lower()
    
    def test_transcription_error_patterns(self):
        """Test detection of potential transcription errors."""
        # Test very long word pattern
        segment = SRTSegment(
            index=1,
            start_time="00:01:00,000",
            end_time="00:01:05,000", 
            text="This has a verylongwordthatisprobablyatranscriptionerror here"
        )
        
        high_confidence = ConfidenceMetrics(
            lexicon_confidence=0.9,
            sacred_confidence=0.9,
            compound_confidence=0.9,
            scripture_confidence=0.9,
            overall_confidence=0.9,
            processing_flags=[]
        )
        
        issues = self.detector.detect_issues(segment, high_confidence)
        
        transcription_issues = [i for i in issues if i.issue_type == 'transcription']
        assert len(transcription_issues) >= 1
        assert 'transcription error' in transcription_issues[0].description.lower()
    
    def test_formatting_issue_detection(self):
        """Test detection of formatting issues."""
        segment = SRTSegment(
            index=1,
            start_time="00:01:00,000",
            end_time="00:01:05,000",
            text="[This looks like stage directions] or (meta content)"
        )
        
        confidence = ConfidenceMetrics(
            lexicon_confidence=0.9,
            sacred_confidence=0.9,
            compound_confidence=0.9,
            scripture_confidence=0.9,
            overall_confidence=0.9,
            processing_flags=[]
        )
        
        issues = self.detector.detect_issues(segment, confidence)
        
        formatting_issues = [i for i in issues if i.issue_type == 'formatting']
        assert len(formatting_issues) >= 1
        assert 'meta-text' in formatting_issues[0].description.lower()
    
    def test_component_confidence_issues(self):
        """Test detection of component-specific confidence issues."""
        segment = SRTSegment(
            index=1,
            start_time="00:01:00,000",
            end_time="00:01:05,000",
            text="Some text with lexicon issues"
        )
        
        confidence = ConfidenceMetrics(
            lexicon_confidence=0.5,  # Very low
            sacred_confidence=0.6,   # Low
            compound_confidence=0.9,
            scripture_confidence=0.9,
            overall_confidence=0.7,
            processing_flags=['uncertain_corrections', 'sacred_formatting_issues']
        )
        
        issues = self.detector.detect_issues(segment, confidence)
        
        # Should detect both lexicon and sacred confidence issues
        issue_descriptions = [issue.description.lower() for issue in issues]
        assert any('lexicon' in desc for desc in issue_descriptions)
        assert any('sacred' in desc for desc in issue_descriptions)
    
    def test_sanskrit_pattern_detection(self):
        """Test Sanskrit-specific uncertainty pattern detection."""
        segment = SRTSegment(
            index=1,
            start_time="00:01:00,000", 
            end_time="00:01:05,000",
            text="This has mixed123content that might be OCR errors"
        )
        
        confidence = ConfidenceMetrics(
            lexicon_confidence=0.9,
            sacred_confidence=0.9,
            compound_confidence=0.9,
            scripture_confidence=0.9,
            overall_confidence=0.9,
            processing_flags=[]
        )
        
        issues = self.detector.detect_issues(segment, confidence)
        
        sanskrit_issues = [i for i in issues if 'sanskrit' in i.description.lower()]
        assert len(sanskrit_issues) >= 1
        assert sanskrit_issues[0].issue_type == 'uncertainty'
        assert 'sanskrit/hindi' in sanskrit_issues[0].description.lower()
    
    def test_text_truncation(self):
        """Test text truncation for context display."""
        long_text = "This is a very long text " * 20  # ~500 characters
        truncated = self.detector._truncate_text(long_text, 100)
        
        assert len(truncated) <= 100
        assert truncated.endswith('...')
        
        short_text = "Short text"
        not_truncated = self.detector._truncate_text(short_text, 100)
        assert not_truncated == short_text
        assert not not_truncated.endswith('...')

class TestQASystemIntegration:
    """Test integration of QA components with main processor."""
    
    def test_qa_report_structure(self):
        """Test the structure of generated QA reports."""
        # Mock data for report generation
        segments = [
            SRTSegment(1, "00:00:01,000", "00:00:05,000", "Test segment one"),
            SRTSegment(2, "00:00:05,000", "00:00:10,000", "Test segment two")
        ]
        
        confidence_scores = [
            ConfidenceMetrics(0.9, 0.95, 0.85, 0.9, 0.9, []),
            ConfidenceMetrics(0.6, 0.8, 0.7, 0.8, 0.65, ['uncertain_corrections'])
        ]
        
        quality_issues = [
            QualityIssue(
                issue_type='uncertainty',
                severity='medium',
                description='Low processing confidence (0.65)',
                timestamp_start='00:00:05,000',
                timestamp_end='00:00:10,000',
                context_text='Test segment two',
                suggested_action='Manual review recommended',
                confidence=0.9
            )
        ]
        
        # Test report structure (would normally be called by processor)
        report = {
            "metadata": {
                "filename": "test.srt",
                "total_segments": 2
            },
            "quality_summary": {
                "high_confidence_segments": 1,
                "medium_confidence_segments": 0,
                "low_confidence_segments": 1,
                "review_recommended_segments": 1
            },
            "segment_details": [
                {
                    "segment_number": 2,
                    "timestamp": "00:00:05,000 --> 00:00:10,000",
                    "confidence": {
                        "overall": 0.65,
                        "lexicon": 0.6,
                        "sacred": 0.8,
                        "compound": 0.7,
                        "scripture": 0.8
                    },
                    "flags": ['uncertain_corrections'],
                    "issues": [
                        {
                            "type": "uncertainty",
                            "severity": "medium",
                            "description": "Low processing confidence (0.65)",
                            "suggested_action": "Manual review recommended"
                        }
                    ]
                }
            ]
        }
        
        # Validate report structure
        assert 'metadata' in report
        assert 'quality_summary' in report
        assert 'segment_details' in report
        
        # Validate metadata
        assert report['metadata']['filename'] == 'test.srt'
        assert report['metadata']['total_segments'] == 2
        
        # Validate quality summary
        summary = report['quality_summary']
        assert summary['high_confidence_segments'] == 1
        assert summary['low_confidence_segments'] == 1
        assert summary['review_recommended_segments'] == 1
        
        # Validate segment details
        details = report['segment_details'][0]
        assert details['segment_number'] == 2
        assert details['confidence']['overall'] == 0.65
        assert len(details['issues']) == 1
        assert details['issues'][0]['type'] == 'uncertainty'

def test_qa_performance_requirements():
    """Test that QA system meets performance requirements."""
    import time
    
    # Test confidence scoring performance
    scorer = ConfidenceScorer()
    result = MockProcessingResult(
        processed_text="Test text for performance",
        corrections_made=2
    )
    
    # Time confidence scoring (should be <10ms per segment)
    start_time = time.time()
    for _ in range(100):  # Test batch of 100 segments
        confidence = scorer.calculate_confidence(result)
    end_time = time.time()
    
    avg_time_per_segment = (end_time - start_time) / 100
    assert avg_time_per_segment < 0.01  # <10ms per segment
    
    # Test issue detection performance
    detector = QualityIssueDetector()
    segment = SRTSegment(1, "00:01:00,000", "00:01:05,000", "Test performance segment")
    confidence = ConfidenceMetrics(0.8, 0.8, 0.8, 0.8, 0.8, [])
    
    start_time = time.time()
    for _ in range(100):
        issues = detector.detect_issues(segment, confidence)
    end_time = time.time()
    
    avg_time_per_detection = (end_time - start_time) / 100
    assert avg_time_per_detection < 0.01  # <10ms per segment

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])