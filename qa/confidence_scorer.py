"""
Quality Assurance - Confidence Scoring System
Lean confidence scoring for Sanskrit SRT processing quality assessment.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConfidenceMetrics:
    """Comprehensive confidence metrics for quality assessment."""
    lexicon_confidence: float      # How confident in lexicon corrections
    sacred_confidence: float       # Sacred content preservation confidence  
    compound_confidence: float     # Compound term recognition confidence
    scripture_confidence: float    # Scripture reference confidence
    overall_confidence: float      # Aggregated final confidence
    processing_flags: List[str] = field(default_factory=list)  # Quality concern flags

class ConfidenceScorer:
    """
    Lean confidence scoring system for quality assurance.
    Aggregates confidence from all processing components with rule-based logic.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize scorer with configurable thresholds and validation.
        
        Args:
            config: Configuration dictionary with QA thresholds and settings.
                   If None, uses sensible defaults.
        
        Raises:
            ValueError: If configuration contains invalid threshold values.
        """
        self.config = config or {}
        
        # Validate and set thresholds with defensive programming
        default_thresholds = {
            'high_confidence': 0.9,
            'medium_confidence': 0.7,
            'low_confidence': 0.4
        }
        
        qa_config = self.config.get('qa', {})
        self.thresholds = qa_config.get('thresholds', default_thresholds)
        
        # Validate threshold values
        for name, value in self.thresholds.items():
            if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                logger.warning(f"Invalid threshold {name}={value}, using default")
                self.thresholds[name] = default_thresholds.get(name, 0.7)
        
        # Ensure logical threshold ordering
        if self.thresholds['high_confidence'] <= self.thresholds['medium_confidence']:
            logger.warning("High confidence threshold should be > medium, adjusting")
            self.thresholds['high_confidence'] = self.thresholds['medium_confidence'] + 0.1
        
        if self.thresholds['medium_confidence'] <= self.thresholds['low_confidence']:
            logger.warning("Medium confidence threshold should be > low, adjusting")
            self.thresholds['medium_confidence'] = self.thresholds['low_confidence'] + 0.1
        
        logger.debug(f"Confidence scorer initialized with thresholds: {self.thresholds}")
        
    def calculate_confidence(self, processing_result: Any) -> ConfidenceMetrics:
        """
        Calculate overall confidence from component confidences.
        Uses intelligent weighted average with adaptive component-specific weights.
        
        Args:
            processing_result: Result object from text processing pipeline.
                              Should contain corrections_made, processed_text, and metadata.
        
        Returns:
            ConfidenceMetrics: Comprehensive confidence assessment with component scores.
        
        Raises:
            ValueError: If processing_result is None or lacks required attributes.
        """
        if processing_result is None:
            raise ValueError("Processing result cannot be None")
        
        logger.debug(f"Calculating confidence for processing result type: {type(processing_result).__name__}")
        # Component confidences from specialized processors
        lexicon_conf = self._assess_lexicon_confidence(processing_result)
        sacred_conf = self._assess_sacred_confidence(processing_result)  
        compound_conf = self._assess_compound_confidence(processing_result)
        scripture_conf = self._assess_scripture_confidence(processing_result)
        
        # Adaptive weighted aggregation with intelligent boosting
        weights = self._calculate_adaptive_weights(lexicon_conf, sacred_conf, compound_conf, scripture_conf)
        
        overall = (
            lexicon_conf * weights['lexicon'] +
            sacred_conf * weights['sacred'] + 
            compound_conf * weights['compound'] +
            scripture_conf * weights['scripture']
        )
        
        # Apply sophisticated confidence adjustments
        overall = self._apply_confidence_adjustments(overall, [lexicon_conf, sacred_conf, compound_conf, scripture_conf])
        
        # Ensure confidence stays within valid range
        overall = max(0.0, min(1.0, overall))
        
        logger.debug(f"Component confidences - Lexicon: {lexicon_conf:.3f}, Sacred: {sacred_conf:.3f}, "
                    f"Compound: {compound_conf:.3f}, Scripture: {scripture_conf:.3f}, Overall: {overall:.3f}")
        
        # Generate processing flags for quality concerns
        flags = self._generate_flags(lexicon_conf, sacred_conf, compound_conf, scripture_conf)
        
        return ConfidenceMetrics(
            lexicon_confidence=lexicon_conf,
            sacred_confidence=sacred_conf, 
            compound_confidence=compound_conf,
            scripture_confidence=scripture_conf,
            overall_confidence=overall,
            processing_flags=flags
        )
        
    def _assess_lexicon_confidence(self, result) -> float:
        """Simple lexicon confidence based on correction patterns."""
        # Handle different ProcessingResult types
        corrections_made = getattr(result, 'corrections_made', 0)
        text_length = len(getattr(result, 'processed_text', '').split())
        
        if corrections_made == 0:
            return 1.0  # No corrections needed = high confidence
            
        # Lower confidence if many corrections relative to text length
        correction_ratio = corrections_made / max(text_length, 1)
        if correction_ratio > 0.5:
            return 0.6  # Many corrections = uncertain
        elif correction_ratio > 0.2:
            return 0.8  # Some corrections = medium confidence
        else:
            return 0.9  # Few corrections = high confidence
            
    def _assess_sacred_confidence(self, result) -> float:
        """Sacred content processing confidence."""
        # Check if sacred processing was performed
        metadata = getattr(result, 'metadata', {})
        specialized = getattr(result, 'specialized_processing', {})
        
        if not (metadata.get('sacred_processing') or specialized.get('sacred')):
            return 1.0  # No sacred content = not applicable
            
        # Check for sacred symbols preserved
        sacred_symbols = ['|', '||', '।', '।।', 'ॐ']
        text = getattr(result, 'processed_text', '')
        
        if any(symbol in text for symbol in sacred_symbols):
            return 0.95  # Sacred symbols preserved = high confidence
        elif getattr(result, 'content_type', '').lower() in ['mantra', 'verse', 'prayer']:
            return 0.7   # Sacred content but no symbols = medium confidence  
        else:
            return 0.9
            
    def _assess_compound_confidence(self, result) -> float:
        """Compound term processing confidence."""
        specialized = getattr(result, 'specialized_processing', {})
        compound_data = specialized.get('compound', {})
        
        if not compound_data:
            return 0.85  # No compound processing = neutral confidence
            
        # Check compound matching metrics if available
        matches = compound_data.get('matches', [])
        if not matches:
            return 0.8
            
        # Higher confidence for exact matches vs fuzzy matches
        exact_matches = sum(1 for match in matches if match.get('confidence', 0) > 0.95)
        match_ratio = exact_matches / len(matches) if matches else 0
        
        if match_ratio > 0.8:
            return 0.9
        elif match_ratio > 0.5:
            return 0.8
        else:
            return 0.7
            
    def _assess_scripture_confidence(self, result) -> float:
        """Scripture reference processing confidence.""" 
        specialized = getattr(result, 'specialized_processing', {})
        scripture_data = specialized.get('scripture', {})
        
        if not scripture_data:
            return 0.9  # No scripture processing = high confidence (not applicable)
            
        # Check scripture validation results
        validated = scripture_data.get('validated', True)
        references = scripture_data.get('references', [])
        
        if validated and references:
            return 0.95  # Validated scripture references = high confidence
        elif references:
            return 0.8   # References found but not validated = medium
        else:
            return 0.7   # Scripture processing attempted but no clear results
            
    def _generate_flags(self, lexicon_conf: float, sacred_conf: float, 
                       compound_conf: float, scripture_conf: float) -> List[str]:
        """Generate flags for low-confidence areas."""
        flags = []
        
        if lexicon_conf < self.thresholds['medium_confidence']:
            flags.append('uncertain_corrections')
        if sacred_conf < 0.8:
            flags.append('sacred_formatting_issues')
        if compound_conf < self.thresholds['medium_confidence']:
            flags.append('compound_term_uncertainty')
        if scripture_conf < 0.6:
            flags.append('scripture_reference_uncertain')
            
        return flags
    
    def _calculate_adaptive_weights(self, lexicon_conf: float, sacred_conf: float, 
                                   compound_conf: float, scripture_conf: float) -> Dict[str, float]:
        """
        Calculate adaptive weights based on component performance.
        
        Higher-performing components get slightly higher weights for better overall accuracy.
        """
        base_weights = {'lexicon': 0.4, 'sacred': 0.2, 'compound': 0.2, 'scripture': 0.2}
        
        # If all components perform well (>0.8), use base weights
        components = [lexicon_conf, sacred_conf, compound_conf, scripture_conf]
        if all(conf > 0.8 for conf in components):
            return base_weights
        
        # Adaptive weighting: boost high-confidence components slightly
        total_conf = sum(components)
        if total_conf > 0:
            adaptation_factor = 0.1  # Maximum 10% weight adjustment
            
            adjustments = {
                'lexicon': (lexicon_conf - 0.7) * adaptation_factor if lexicon_conf > 0.7 else 0,
                'sacred': (sacred_conf - 0.7) * adaptation_factor * 0.5 if sacred_conf > 0.7 else 0,
                'compound': (compound_conf - 0.7) * adaptation_factor * 0.5 if compound_conf > 0.7 else 0,
                'scripture': (scripture_conf - 0.7) * adaptation_factor * 0.5 if scripture_conf > 0.7 else 0
            }
            
            # Apply adjustments while maintaining weight sum = 1.0
            adjusted_weights = {}
            total_adjustment = sum(adjustments.values())
            
            for component in base_weights:
                adjusted_weights[component] = base_weights[component] + adjustments[component]
                if total_adjustment != 0:
                    # Normalize to ensure sum = 1.0
                    adjusted_weights[component] *= 1.0 / (1.0 + total_adjustment)
            
            return adjusted_weights
        
        return base_weights
    
    def _apply_confidence_adjustments(self, base_confidence: float, component_values: List[float]) -> float:
        """
        Apply sophisticated confidence adjustments based on component agreement and patterns.
        
        Args:
            base_confidence: Initial weighted confidence score
            component_values: List of individual component confidence values
        
        Returns:
            Adjusted confidence score with intelligent boosts/penalties
        """
        adjusted = base_confidence
        
        # Agreement boost: If components agree strongly, increase confidence
        variance = sum((x - base_confidence) ** 2 for x in component_values) / len(component_values)
        if variance < 0.01:  # Very strong agreement
            adjusted = min(1.0, adjusted * 1.15)  # 15% boost
            logger.debug(f"Strong component agreement detected, confidence boosted to {adjusted:.3f}")
        elif variance < 0.05:  # Moderate agreement
            adjusted = min(1.0, adjusted * 1.05)  # 5% boost
        
        # Consistency penalty: If there's high variance, be more conservative
        elif variance > 0.2:
            adjusted = adjusted * 0.95  # 5% penalty for inconsistent results
            logger.debug(f"High component variance detected, confidence reduced to {adjusted:.3f}")
        
        # Extreme values check: Very low individual scores reduce overall confidence
        min_component = min(component_values)
        if min_component < 0.3:  # Any component performing very poorly
            penalty = (0.3 - min_component) * 0.5  # Up to 15% penalty
            adjusted = max(0.0, adjusted - penalty)
            logger.debug(f"Low component score penalty applied, confidence reduced to {adjusted:.3f}")
        
        # Excellence boost: If most components perform excellently, boost slightly
        excellent_count = sum(1 for conf in component_values if conf > 0.9)
        if excellent_count >= 3:  # 3 or more components excellent
            adjusted = min(1.0, adjusted * 1.08)  # 8% excellence boost
            logger.debug(f"Excellence boost applied for {excellent_count} high-performing components")
        
        return adjusted