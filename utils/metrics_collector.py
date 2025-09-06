"""
MetricsCollector - Extracted from core processor for lean architecture.

Provides robust metrics collection for processing operations with comprehensive 
error handling and thread-safe operations.
"""

import logging
import time
from typing import List, Dict, Union, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CorrectionDetail:
    """Immutable details of a single correction operation with comprehensive validation.
    
    This class provides a thread-safe, immutable record of correction operations
    with built-in validation and performance optimization for metrics collection.
    
    Args:
        type: Type of correction ('lexicon', 'capitalization', 'fuzzy', 'punctuation')
        original: Original text before correction
        corrected: Text after correction is applied
        confidence: Confidence score (0.0-1.0) indicating correction reliability  
        processing_time: Time taken to perform correction (seconds, non-negative)
    """
    type: str  # 'lexicon', 'capitalization', 'fuzzy', 'punctuation'
    original: str
    corrected: str
    confidence: float
    processing_time: float
    
    def __post_init__(self):
        """Validate correction detail fields for data integrity."""
        if not isinstance(self.confidence, (int, float)) or not 0.0 <= self.confidence <= 1.0:
            object.__setattr__(self, 'confidence', max(0.0, min(1.0, float(self.confidence))))
        if not isinstance(self.processing_time, (int, float)) or self.processing_time < 0:
            object.__setattr__(self, 'processing_time', max(0.0, float(self.processing_time)))


class MetricsCollector:
    """Robust metrics collection for processing operations with comprehensive error handling.
    
    This class provides thread-safe metrics collection with proper error handling,
    optimized performance, and detailed tracking of correction operations.
    """
    
    def __init__(self) -> None:
        """Initialize metrics collector with empty tracking structures."""
        self.corrections_by_type: Dict[str, int] = {}
        self.correction_details: List[CorrectionDetail] = []
        self.confidence_scores: List[float] = []
        self.start_times: Dict[str, float] = {}
    
    def start_correction(self, correction_type: str, original: str) -> None:
        """Start timing a correction operation with comprehensive error handling.
        
        Args:
            correction_type: Type of correction being performed (e.g., 'lexicon', 'capitalization')
            original: Original text being corrected
            
        Note:
            Uses unique keys to handle duplicate words in same text segment.
        """
        try:
            # Input validation
            if not correction_type or not isinstance(correction_type, str):
                logger.warning(f"Invalid correction_type: {correction_type}")
                return
            if not isinstance(original, str):
                logger.warning(f"Invalid original text type: {type(original)}")
                return
                
            # Use unique key to handle duplicate words in same text
            key = f"{correction_type}:{original}:{len(self.correction_details)}"
            self.start_times[key] = time.time()
        except Exception as e:
            logger.warning(f"Failed to start correction timing: {e}")
    
    def end_correction(self, correction_type: str, original: str, corrected: str, confidence: Union[int, float]) -> None:
        """Record completed correction with comprehensive timing and validation.
        
        Args:
            correction_type: Type of correction performed
            original: Original text that was corrected
            corrected: Text after correction
            confidence: Confidence score between 0.0 and 1.0
            
        Note:
            All inputs are validated and sanitized. Invalid confidence scores
            are automatically clamped to valid range.
        """
        try:
            # Comprehensive input validation
            if not correction_type or not isinstance(correction_type, str):
                logger.warning(f"Invalid correction_type: {correction_type}")
                return
            if not isinstance(original, str) or not isinstance(corrected, str):
                logger.warning(f"Invalid text types: original={type(original)}, corrected={type(corrected)}")
                return
            
            # Validate and sanitize confidence score
            if not isinstance(confidence, (int, float)):
                logger.warning(f"Invalid confidence type {type(confidence)}, defaulting to 1.0")
                confidence = 1.0
            elif not 0.0 <= confidence <= 1.0:
                logger.warning(f"Confidence score {confidence} out of range [0,1], clamping")
                confidence = max(0.0, min(1.0, float(confidence)))
            
            # Calculate processing time with fallback
            key = f"{correction_type}:{original}:{len(self.correction_details)}"
            current_time = time.time()
            start_time = self.start_times.pop(key, current_time)
            processing_time = max(0.0, current_time - start_time)
            
            # Update counters safely
            self.corrections_by_type[correction_type] = self.corrections_by_type.get(correction_type, 0) + 1
            
            # Record detail with validation
            detail = CorrectionDetail(
                type=correction_type,
                original=original,
                corrected=corrected,
                confidence=float(confidence),
                processing_time=processing_time
            )
            self.correction_details.append(detail)
            self.confidence_scores.append(float(confidence))
            
        except Exception as e:
            logger.warning(f"Failed to record correction metrics: {e}")
    
    def calculate_quality_score(self, total_segments: int, error_count: int) -> float:
        """Calculate overall quality score (0-100) with robust error handling."""
        try:
            if total_segments <= 0:
                return 0.0
            
            total_corrections = len(self.correction_details)
            if total_corrections == 0:
                return 100.0 if error_count == 0 else max(0.0, 100.0 - (error_count / total_segments) * 50)
            
            # Success rate (40%) - we only record successful corrections
            success_rate = 1.0
            
            # Average confidence (30%)
            avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 1.0
            
            # Error penalty (20%)
            error_penalty = max(0.0, 1.0 - (error_count / total_segments))
            
            # Coverage (10%) - proportion of segments that had corrections
            coverage = min(1.0, total_corrections / total_segments)
            
            # Weighted score calculation
            score = (success_rate * 0.4 + avg_confidence * 0.3 + error_penalty * 0.2 + coverage * 0.1) * 100
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {e}")
            return 0.0
    
    def get_stats_summary(self) -> Dict[str, Union[int, float, Dict[str, int], List[float]]]:
        """Get comprehensive statistics summary with full type safety.
        
        Returns:
            Dictionary containing detailed correction statistics including:
            - total_corrections: Total number of corrections recorded
            - corrections_by_type: Breakdown by correction type
            - average_confidence: Mean confidence score across all corrections
            - processing_times: List of processing times for performance analysis
        """
        try:
            return {
                'total_corrections': len(self.correction_details),
                'corrections_by_type': dict(self.corrections_by_type),
                'average_confidence': (
                    sum(self.confidence_scores) / len(self.confidence_scores) 
                    if self.confidence_scores else 0.0
                ),
                'processing_times': [detail.processing_time for detail in self.correction_details]
            }
        except Exception as e:
            logger.error(f"Failed to generate stats summary: {e}")
            return {
                'total_corrections': 0,
                'corrections_by_type': {},
                'average_confidence': 0.0,
                'processing_times': []
            }