"""
Quality Assurance - Issue Detection System
Lightweight issue detection for quality review prioritization.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class QualityIssue:
    """Represents a detected quality issue requiring review."""
    issue_type: str               # 'transcription', 'formatting', 'uncertainty'
    severity: str                 # 'critical', 'high', 'medium', 'low'  
    description: str              # Human-readable issue description
    timestamp_start: str          # SRT timestamp where issue occurs
    timestamp_end: str            # End timestamp
    context_text: str             # Surrounding text for context
    suggested_action: str         # What reviewer should consider
    confidence: float             # How certain we are this is an issue

class QualityIssueDetector:
    """
    Lightweight issue detection for quality review.
    Focuses on common patterns that need human attention.
    """
    
    def __init__(self) -> None:
        """Initialize detector with comprehensive issue patterns and validation.
        
        Sets up pattern matching for transcription errors, formatting issues,
        and Sanskrit-specific uncertainty detection with robust regex patterns.
        """
        # Common patterns that indicate potential transcription issues
        self.transcription_patterns = [
            r'\b\w{15,}\b',           # Very long words (likely transcription errors)
            r'[A-Z]{5,}',             # Long sequences of caps (OCR/transcription errors)
            r'\d{4,}',                # Long number sequences (timestamps leaked into text)
            r'[.,!?]{3,}',            # Repeated punctuation (uncertainty markers)
            r'[aeiouAEIOU]{4,}',      # Repeated vowels (speech elongation artifacts)
            r'\b[bcdfg-hj-np-tvwxyzBCDFG-HJ-NP-TVWXYZ]{4,}\b'  # Consonant clusters
        ]
        
        # Formatting issue patterns
        self.formatting_patterns = [
            r'^\s*[-*•]\s*',          # Bullet points (possibly misformatted)
            r'\[.*?\]',               # Bracketed content (stage directions/notes)
            r'\(.*?\)',               # Parenthetical content (possibly meta-text)
        ]
        
        # Sanskrit/Hindi specific patterns (enhanced)
        self.sanskrit_uncertainty_patterns = [
            r'[a-zA-Z]+[0-9]+[a-zA-Z]*',      # Mixed alphanumeric (OCR errors)
            r'\b[aeiouy]{3,}\b',              # Excessive vowel repetitions
            r'[\u0900-\u097F]+[a-zA-Z]+',      # Mixed Devanagari and Latin
            r'\b[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{5,}\b',  # Long consonant clusters
            r'[aeiou][aeiou][aeiou]',         # Triple vowel patterns (unusual)
        ]
        
    def detect_issues(self, segment: Any, confidence: Any) -> List[QualityIssue]:
        """
        Find potential quality issues in processed segment with comprehensive analysis.
        
        Args:
            segment: SRT segment with start_time, end_time, and text attributes
            confidence: ConfidenceMetrics object with component confidence scores
        
        Returns:
            List of QualityIssue objects describing detected problems
        
        Raises:
            ValueError: If segment or confidence is None or lacks required attributes
        """
        if segment is None:
            raise ValueError("Segment cannot be None")
        if confidence is None:
            raise ValueError("Confidence metrics cannot be None")
        
        # Validate required segment attributes
        required_attrs = ['start_time', 'end_time', 'text']
        for attr in required_attrs:
            if not hasattr(segment, attr):
                raise ValueError(f"Segment missing required attribute: {attr}")
        
        # Validate text content
        if not isinstance(segment.text, str):
            logger.warning(f"Invalid segment text type: {type(segment.text)}, converting to string")
            segment.text = str(segment.text) if segment.text is not None else ""
        
        logger.debug(f"Analyzing segment {segment.start_time}-{segment.end_time} with confidence {confidence.overall_confidence:.3f}")
        
        issues: List[QualityIssue] = []
        
        # Low confidence = review needed
        if confidence.overall_confidence < 0.7:
            severity = 'high' if confidence.overall_confidence < 0.5 else 'medium'
            issues.append(QualityIssue(
                issue_type='uncertainty',
                severity=severity,
                description=f'Low processing confidence ({confidence.overall_confidence:.2f})',
                timestamp_start=segment.start_time,
                timestamp_end=segment.end_time,
                context_text=self._truncate_text(segment.text, 100),
                suggested_action='Manual review recommended for accuracy',
                confidence=0.9
            ))
            
        # Component-specific confidence issues
        issues.extend(self._check_component_confidence(segment, confidence))
            
        # Potential transcription errors
        issues.extend(self._check_transcription_patterns(segment))
        
        # Formatting issues  
        issues.extend(self._check_formatting_issues(segment))
        
        # Sanskrit-specific uncertainty patterns
        issues.extend(self._check_sanskrit_patterns(segment))
        
        return issues
    
    def _check_component_confidence(self, segment, confidence) -> List[QualityIssue]:
        """Check for component-specific confidence issues."""
        issues = []
        
        if confidence.lexicon_confidence < 0.6:
            issues.append(QualityIssue(
                issue_type='uncertainty',
                severity='high',
                description=f'Low lexicon confidence ({confidence.lexicon_confidence:.2f})',
                timestamp_start=segment.start_time,
                timestamp_end=segment.end_time,
                context_text=self._truncate_text(segment.text, 100),
                suggested_action='Check Sanskrit/Hindi term corrections',
                confidence=0.85
            ))
            
        if confidence.sacred_confidence < 0.7:
            issues.append(QualityIssue(
                issue_type='formatting',
                severity='medium',
                description=f'Sacred content formatting concerns ({confidence.sacred_confidence:.2f})',
                timestamp_start=segment.start_time,
                timestamp_end=segment.end_time,
                context_text=self._truncate_text(segment.text, 100),
                suggested_action='Verify sacred symbols and verse formatting',
                confidence=0.8
            ))
            
        return issues
    
    def _check_transcription_patterns(self, segment) -> List[QualityIssue]:
        """Check for potential transcription error patterns."""
        issues = []
        
        for pattern in self.transcription_patterns:
            if re.search(pattern, segment.text):
                issues.append(QualityIssue(
                    issue_type='transcription',
                    severity='medium',
                    description='Potential transcription error pattern detected',
                    timestamp_start=segment.start_time,
                    timestamp_end=segment.end_time,
                    context_text=segment.text,
                    suggested_action='Check for garbled text or misheard words',
                    confidence=0.7
                ))
                break  # Only report one transcription issue per segment
                
        return issues
    
    def _check_formatting_issues(self, segment) -> List[QualityIssue]:
        """Check for formatting-related issues.""" 
        issues = []
        
        # Check for potential meta-text or stage directions
        for pattern in self.formatting_patterns:
            if re.search(pattern, segment.text):
                issues.append(QualityIssue(
                    issue_type='formatting',
                    severity='low',
                    description='Potential meta-text or formatting artifact',
                    timestamp_start=segment.start_time,
                    timestamp_end=segment.end_time,
                    context_text=self._truncate_text(segment.text, 80),
                    suggested_action='Review for non-speech content or formatting issues',
                    confidence=0.6
                ))
                break
                
        return issues
    
    def _check_sanskrit_patterns(self, segment) -> List[QualityIssue]:
        """Check for Sanskrit/Hindi-specific uncertainty patterns."""
        issues = []
        
        for pattern in self.sanskrit_uncertainty_patterns:
            if re.search(pattern, segment.text):
                issues.append(QualityIssue(
                    issue_type='uncertainty',
                    severity='medium',
                    description='Sanskrit/Hindi term recognition uncertainty',
                    timestamp_start=segment.start_time,
                    timestamp_end=segment.end_time,
                    context_text=self._truncate_text(segment.text, 100),
                    suggested_action='Verify Sanskrit/Hindi term spelling and context',
                    confidence=0.75
                ))
                break
                
        return issues
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Safely truncate text for context display with intelligent word boundaries.
        
        Args:
            text: Text to truncate
            max_length: Maximum length for truncated text
        
        Returns:
            Truncated text with ellipsis if needed
        
        Raises:
            ValueError: If max_length is less than 10 (too small for meaningful context)
        """
        if max_length < 10:
            raise ValueError("max_length must be at least 10 characters")
        
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        
        if len(text) <= max_length:
            return text
        
        # Try to truncate at word boundary for better readability
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:  # If we can save significant text
            return text[:last_space] + '...'
        
        return text[:max_length-3] + '...'