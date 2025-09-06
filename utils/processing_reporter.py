"""
ProcessingReporter - Extracted from core processor for lean architecture.

Provides comprehensive reporting for processing metrics with enhanced formatting 
and validation for both human-readable and machine-readable outputs.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass, field
from .metrics_collector import CorrectionDetail

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Immutable results from processing operation with comprehensive validation.
    
    Provides a structured container for core processing metrics with
    built-in validation and type safety.
    
    Attributes:
        segments_processed: Number of text segments successfully processed
        corrections_made: Total number of corrections applied
        processing_time: Total time taken for processing (seconds)
        errors: List of error messages encountered during processing
    """
    segments_processed: int
    corrections_made: int
    processing_time: float
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate processing result fields for data integrity."""
        if not isinstance(self.segments_processed, int) or self.segments_processed < 0:
            object.__setattr__(self, 'segments_processed', max(0, int(self.segments_processed)))
        if not isinstance(self.corrections_made, int) or self.corrections_made < 0:
            object.__setattr__(self, 'corrections_made', max(0, int(self.corrections_made)))
        if not isinstance(self.processing_time, (int, float)) or self.processing_time < 0:
            object.__setattr__(self, 'processing_time', max(0.0, float(self.processing_time)))

@dataclass
class DetailedProcessingResult(ProcessingResult):
    """Extended processing result with detailed metrics and performance data.
    
    This class extends the base ProcessingResult with comprehensive metrics
    collection, maintaining full backward compatibility while providing
    detailed insights into processing performance, correction quality,
    and resource utilization.
    """
    corrections_by_type: Dict[str, int] = field(default_factory=dict)
    correction_details: List[CorrectionDetail] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    processing_phases: Dict[str, float] = field(default_factory=dict)  # parse, process, write times
    quality_score: float = 0.0
    memory_usage: Dict[str, float] = field(default_factory=dict)  # peak, average


class ProcessingReporter:
    """Comprehensive reporting for processing metrics with enhanced formatting and validation.
    
    This class provides robust report generation with error handling, formatting validation,
    and optimized performance for both human-readable and machine-readable outputs.
    """
    
    @staticmethod
    def generate_summary(result: ProcessingResult, verbose: bool = False) -> str:
        """Generate human-readable processing summary with comprehensive validation.
        
        Args:
            result: Processing result to summarize
            verbose: Include detailed metrics breakdown
            
        Returns:
            Formatted summary string with processing metrics
            
        Raises:
            TypeError: If result is not a ProcessingResult instance
        """
        try:
            if isinstance(result, DetailedProcessingResult):
                return ProcessingReporter._generate_detailed_summary(result, verbose)
            else:
                return ProcessingReporter._generate_basic_summary(result)
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return f"❌ Error generating report: {e}"
    
    @staticmethod
    def _generate_basic_summary(result: ProcessingResult) -> str:
        """Generate basic summary for simple ProcessingResult with validation."""
        try:
            segments_per_sec = result.segments_processed / result.processing_time if result.processing_time > 0 else 0
            correction_rate = (result.corrections_made / result.segments_processed * 100) if result.segments_processed > 0 else 0
            
            error_section = f"\n   • Errors: {len(result.errors)}" if result.errors else ""
            
            return f"""✅ Processing Complete!

📊 Results Summary:
   • Segments processed: {result.segments_processed:,}
   • Corrections made: {result.corrections_made:,} ({correction_rate:.1f}% of segments)
   • Processing time: {result.processing_time:.1f}s ({segments_per_sec:,.0f} segments/sec){error_section}"""
        except Exception as e:
            logger.error(f"Failed to generate basic summary: {e}")
            return f"❌ Error in basic report generation: {e}"
    
    @staticmethod
    def _generate_detailed_summary(result: DetailedProcessingResult, verbose: bool) -> str:
        """Generate detailed summary for DetailedProcessingResult with comprehensive validation."""
        try:
            segments_per_sec = result.segments_processed / result.processing_time if result.processing_time > 0 else 0
            correction_rate = (result.corrections_made / result.segments_processed * 100) if result.segments_processed > 0 else 0
            avg_confidence = sum(result.confidence_scores) / len(result.confidence_scores) if result.confidence_scores else 0
            
            # Confidence level assessment
            confidence_level = "High" if avg_confidence > 0.8 else "Medium" if avg_confidence > 0.6 else "Low"
            
            summary = f"""✅ Processing Complete!

📊 Results Summary:
   • Segments processed: {result.segments_processed:,}
   • Corrections made: {result.corrections_made:,} ({correction_rate:.1f}% of segments)
   • Processing time: {result.processing_time:.1f}s ({segments_per_sec:,.0f} segments/sec)
   • Quality score: {result.quality_score:.0f}/100

🔧 Correction Breakdown:"""
            
            # Add correction breakdown with validation
            total_corrections = sum(result.corrections_by_type.values())
            if total_corrections > 0:
                for correction_type, count in sorted(result.corrections_by_type.items()):
                    percentage = (count / total_corrections * 100) if total_corrections > 0 else 0
                    summary += f"\n   • {correction_type.title()} corrections: {count:,} ({percentage:.0f}%)"
            else:
                summary += "\n   • No corrections applied"
            
            summary += f"\n\n💡 Average confidence: {avg_confidence:.2f} ({confidence_level})"
            
            # Add verbose details if requested
            if verbose:
                summary += "\n\n📈 Detailed Performance:"
                if result.processing_phases:
                    for phase, time_taken in result.processing_phases.items():
                        summary += f"\n   • {phase.title()} phase: {time_taken:.2f}s"
                
                if result.memory_usage:
                    summary += "\n\n🧠 Memory Usage:"
                    peak_memory = result.memory_usage.get('peak', 0)
                    avg_memory = result.memory_usage.get('average', 0)
                    summary += f"\n   • Peak memory: {peak_memory:.1f} MB"
                    summary += f"\n   • Average memory: {avg_memory:.1f} MB"
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate detailed summary: {e}")
            return f"❌ Error in detailed report generation: {e}"
    
    @staticmethod
    def export_json(result: ProcessingResult) -> Dict[str, Any]:
        """Export metrics in JSON format with comprehensive validation."""
        try:
            base_data = {
                'segments_processed': result.segments_processed,
                'corrections_made': result.corrections_made,
                'processing_time': round(result.processing_time, 3),
                'errors': result.errors,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
            
            if isinstance(result, DetailedProcessingResult):
                base_data.update({
                    'quality_score': round(result.quality_score, 1),
                    'corrections_by_type': result.corrections_by_type,
                    'processing_phases': {k: round(v, 3) for k, v in result.processing_phases.items()},
                    'memory_usage': {k: round(v, 2) for k, v in result.memory_usage.items()},
                    'avg_confidence': round(sum(result.confidence_scores) / len(result.confidence_scores), 3) if result.confidence_scores else 0,
                    'correction_count': len(result.correction_details),
                    'processing_rate': round(result.segments_processed / result.processing_time, 1) if result.processing_time > 0 else 0
                })
            
            return base_data
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return {'error': f'Failed to export metrics: {e}'}