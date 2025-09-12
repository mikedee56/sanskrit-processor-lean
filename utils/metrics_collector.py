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
    """Comprehensive metrics collection for processing operations with detailed reporting.
    
    This class provides thread-safe metrics collection with comprehensive error handling,
    optimized performance, detailed tracking of correction operations, performance analytics,
    and support for historical comparison.
    """
    
    def __init__(self) -> None:
        """Initialize metrics collector with comprehensive tracking structures."""
        # Basic correction tracking
        self.corrections_by_type: Dict[str, int] = {}
        self.correction_details: List[CorrectionDetail] = []
        self.confidence_scores: List[float] = []
        self.start_times: Dict[str, float] = {}
        
        # Enhanced tracking for Story 10.6
        self.correction_frequency: Dict[tuple, int] = {}  # (original, corrected) -> count
        self.sample_corrections: List[Dict[str, Union[str, float, int]]] = []
        self.processing_phases: Dict[str, float] = {}
        self.memory_snapshots: List[float] = []
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.segments_per_second: float = 0.0
        
        # Processing timeline
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.file_path: str = ""
        self.processing_mode: str = ""
        self.total_segments: int = 0
    
    def start_processing(self, file_path: str, mode: str, total_segments: int = 0) -> None:
        """Start processing with comprehensive initialization.
        
        Args:
            file_path: Path to file being processed
            mode: Processing mode (simple, enhanced, asr, etc.)
            total_segments: Expected number of segments
        """
        try:
            self.start_time = time.time()
            self.file_path = file_path
            self.processing_mode = mode
            self.total_segments = total_segments
            self._record_memory_snapshot()
        except Exception as e:
            logger.warning(f"Failed to start processing metrics: {e}")
    
    def start_phase(self, phase_name: str) -> None:
        """Start timing a processing phase (parsing, correction, output)."""
        try:
            self.start_times[f"phase_{phase_name}"] = time.time()
        except Exception as e:
            logger.warning(f"Failed to start phase timing: {e}")
    
    def end_phase(self, phase_name: str) -> None:
        """End timing a processing phase."""
        try:
            start_key = f"phase_{phase_name}"
            if start_key in self.start_times:
                elapsed = time.time() - self.start_times.pop(start_key)
                self.processing_phases[phase_name] = elapsed
                self._record_memory_snapshot()
        except Exception as e:
            logger.warning(f"Failed to end phase timing: {e}")
    
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
    
    def end_correction(self, correction_type: str, original: str, corrected: str, 
                      confidence: Union[int, float], segment_index: int = -1) -> None:
        """Record completed correction with comprehensive timing and validation.
        
        Args:
            correction_type: Type of correction performed
            original: Original text that was corrected
            corrected: Text after correction
            confidence: Confidence score between 0.0 and 1.0
            segment_index: Index of segment where correction occurred
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
            
            # Track frequency for top corrections
            correction_pair = (original, corrected)
            self.correction_frequency[correction_pair] = self.correction_frequency.get(correction_pair, 0) + 1
            
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
            
            # Sample collection for before/after examples (AC: 4)
            if len(self.sample_corrections) < 20:  # Keep top 20 samples
                self.sample_corrections.append({
                    'original': original,
                    'corrected': corrected,
                    'confidence': float(confidence),
                    'type': correction_type,
                    'segment': segment_index,
                    'processing_time': processing_time
                })
            
        except Exception as e:
            logger.warning(f"Failed to record correction metrics: {e}")
    
    def record_cache_hit(self) -> None:
        """Record a cache hit for performance tracking."""
        self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss for performance tracking."""
        self.cache_misses += 1
    
    def finish_processing(self, final_segment_count: int = None) -> None:
        """Complete processing with final metrics calculation."""
        try:
            self.end_time = time.time()
            if final_segment_count is not None:
                self.total_segments = final_segment_count
                
            # Calculate processing rate
            if self.start_time and self.end_time and self.total_segments > 0:
                total_time = self.end_time - self.start_time
                self.segments_per_second = self.total_segments / total_time if total_time > 0 else 0.0
                
            self._record_memory_snapshot()
        except Exception as e:
            logger.warning(f"Failed to finish processing metrics: {e}")
    
    def get_top_corrections(self, n: int = 10) -> List[tuple]:
        """Get top N most frequent corrections (AC: 2).
        
        Returns:
            List of tuples: ((original, corrected), count) sorted by frequency
        """
        try:
            return sorted(self.correction_frequency.items(), 
                         key=lambda x: x[1], reverse=True)[:n]
        except Exception as e:
            logger.warning(f"Failed to get top corrections: {e}")
            return []
    
    def get_confidence_distribution(self) -> Dict[str, int]:
        """Get confidence score distribution (AC: 3)."""
        try:
            ranges = {
                'high (0.9-1.0)': 0,
                'medium (0.7-0.9)': 0,
                'low (0.5-0.7)': 0,
                'very_low (<0.5)': 0
            }
            
            for confidence in self.confidence_scores:
                if confidence >= 0.9:
                    ranges['high (0.9-1.0)'] += 1
                elif confidence >= 0.7:
                    ranges['medium (0.7-0.9)'] += 1
                elif confidence >= 0.5:
                    ranges['low (0.5-0.7)'] += 1
                else:
                    ranges['very_low (<0.5)'] += 1
                    
            return ranges
        except Exception as e:
            logger.warning(f"Failed to get confidence distribution: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Union[float, int, Dict[str, float]]]:
        """Get comprehensive performance metrics (AC: 6)."""
        try:
            total_time = (self.end_time - self.start_time) if self.start_time and self.end_time else 0.0
            peak_memory = max(self.memory_snapshots) if self.memory_snapshots else 0.0
            avg_memory = sum(self.memory_snapshots) / len(self.memory_snapshots) if self.memory_snapshots else 0.0
            cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses)) * 100 if (self.cache_hits + self.cache_misses) > 0 else 0.0
            
            return {
                'total_processing_time': total_time,
                'segments_per_second': self.segments_per_second,
                'memory_usage': {
                    'peak_mb': peak_memory,
                    'average_mb': avg_memory
                },
                'cache_performance': {
                    'hit_rate_percent': cache_hit_rate,
                    'hits': self.cache_hits,
                    'misses': self.cache_misses
                },
                'processing_phases': self.processing_phases.copy()
            }
        except Exception as e:
            logger.warning(f"Failed to get performance metrics: {e}")
            return {}
    
    def get_sample_corrections(self, n: int = 10) -> List[Dict[str, Union[str, float, int]]]:
        """Get representative before/after correction samples (AC: 4)."""
        try:
            # Return diverse samples (different types and confidence levels)
            samples = []
            seen_types = set()
            
            # First pass: get one sample per correction type
            for sample in self.sample_corrections:
                if sample['type'] not in seen_types and len(samples) < n:
                    samples.append(sample)
                    seen_types.add(sample['type'])
            
            # Second pass: fill remaining slots with highest confidence
            remaining_samples = [s for s in self.sample_corrections if s not in samples]
            remaining_samples.sort(key=lambda x: x['confidence'], reverse=True)
            
            for sample in remaining_samples:
                if len(samples) >= n:
                    break
                samples.append(sample)
                
            return samples[:n]
        except Exception as e:
            logger.warning(f"Failed to get sample corrections: {e}")
            return []
    
    def _record_memory_snapshot(self) -> None:
        """Record current memory usage for tracking."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_snapshots.append(memory_mb)
        except ImportError:
            # psutil not available, skip memory tracking
            pass
        except Exception as e:
            logger.warning(f"Failed to record memory snapshot: {e}")
    
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
            - top_corrections: Most frequent corrections
            - confidence_distribution: Distribution of confidence scores
            - performance_metrics: Processing and resource metrics
        """
        try:
            return {
                'total_corrections': len(self.correction_details),
                'corrections_by_type': dict(self.corrections_by_type),
                'average_confidence': (
                    sum(self.confidence_scores) / len(self.confidence_scores) 
                    if self.confidence_scores else 0.0
                ),
                'processing_times': [detail.processing_time for detail in self.correction_details],
                'top_corrections': self.get_top_corrections(10),
                'confidence_distribution': self.get_confidence_distribution(),
                'performance_metrics': self.get_performance_metrics(),
                'sample_corrections': self.get_sample_corrections(10)
            }
        except Exception as e:
            logger.error(f"Failed to generate stats summary: {e}")
            return {
                'total_corrections': 0,
                'corrections_by_type': {},
                'average_confidence': 0.0,
                'processing_times': [],
                'top_corrections': [],
                'confidence_distribution': {},
                'performance_metrics': {},
                'sample_corrections': []
            }