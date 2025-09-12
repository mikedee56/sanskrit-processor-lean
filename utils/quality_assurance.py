"""
Quality assurance utilities for Sanskrit processor validation.
Provides automated quality checks and confidence visualization tools.
"""

import re
import statistics
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass 
class QualityMetrics:
    """Quality assessment metrics for Sanskrit processing results."""
    total_corrections: int
    high_confidence_corrections: int  # >= 0.9
    medium_confidence_corrections: int  # 0.7-0.89
    low_confidence_corrections: int  # 0.5-0.69
    questionable_corrections: int  # < 0.5
    avg_confidence: float
    correction_diversity: float  # Unique corrections / total corrections
    english_protection_rate: float  # % of English words preserved

class QualityValidator:
    """Advanced quality validation for Sanskrit processing operations."""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.quality_thresholds = {
            'min_avg_confidence': 0.75,
            'max_questionable_rate': 0.05,  # Max 5% questionable corrections
            'min_english_protection': 0.95,  # Min 95% English protection
            'min_correction_diversity': 0.7   # Min 70% unique corrections
        }
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load quality validation rules."""
        return {
            'invalid_corrections': {
                # English words that should NEVER become Sanskrit
                'protected_words': {
                    'articles': {'the', 'a', 'an'},
                    'prepositions': {'in', 'on', 'at', 'by', 'for', 'with', 'from'},
                    'pronouns': {'he', 'she', 'it', 'they', 'we', 'you', 'i'},
                    'common_verbs': {'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would'},
                    'common_adjectives': {'good', 'bad', 'big', 'small', 'new', 'old', 'high', 'low'},
                    'numbers': {'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'}
                },
                # Patterns that indicate over-correction
                'suspicious_patterns': [
                    r'\b[A-Z]{2,}\b',  # ALL CAPS (often English acronyms)
                    r'\b\w*ing\b',     # -ing endings
                    r'\b\w*ed\b',      # -ed endings  
                    r'\b\w*ly\b',      # -ly endings
                    r'\b\w*tion\b',    # -tion endings
                ]
            },
            'quality_indicators': {
                'good_sanskrit_patterns': [
                    r'[āīūṛḷēōṃṅṇñṭḍṣśḥ]',  # Contains diacritics
                    r'dh|th|ph|bh|gh|kh|ch|jh',  # Aspirated consonants
                    r'kr|pr|tr|gr|br|dr',        # Consonant clusters
                ],
                'confidence_boosts': {
                    'scripture_reference': 0.1,   # Boost for known scripture terms
                    'compound_match': 0.05,       # Boost for compound corrections
                    'phonetic_similarity': 0.03   # Boost for phonetic matches
                }
            }
        }
    
    def assess_quality(self, text: str, corrections: List[Any]) -> QualityMetrics:
        """Perform comprehensive quality assessment of processing results."""
        if not corrections:
            return QualityMetrics(0, 0, 0, 0, 0, 0.0, 0.0, 1.0)
        
        # Categorize corrections by confidence
        high_conf = sum(1 for c in corrections if hasattr(c, 'confidence') and c.confidence >= 0.9)
        med_conf = sum(1 for c in corrections if hasattr(c, 'confidence') and 0.7 <= c.confidence < 0.9)
        low_conf = sum(1 for c in corrections if hasattr(c, 'confidence') and 0.5 <= c.confidence < 0.7)
        questionable = sum(1 for c in corrections if hasattr(c, 'confidence') and c.confidence < 0.5)
        
        # Calculate average confidence
        confidences = [c.confidence for c in corrections if hasattr(c, 'confidence')]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        # Calculate correction diversity
        unique_corrections = len(set(c.corrected for c in corrections if hasattr(c, 'corrected')))
        correction_diversity = unique_corrections / len(corrections) if corrections else 0.0
        
        # Calculate English protection rate
        english_protection_rate = self._calculate_english_protection(text, corrections)
        
        return QualityMetrics(
            total_corrections=len(corrections),
            high_confidence_corrections=high_conf,
            medium_confidence_corrections=med_conf,
            low_confidence_corrections=low_conf,
            questionable_corrections=questionable,
            avg_confidence=avg_confidence,
            correction_diversity=correction_diversity,
            english_protection_rate=english_protection_rate
        )
    
    def _calculate_english_protection(self, text: str, corrections: List[Any]) -> float:
        """Calculate the rate at which English words were correctly protected."""
        english_words = set()
        
        # Collect all protected word categories
        for category in self.validation_rules['invalid_corrections']['protected_words'].values():
            english_words.update(category)
        
        # Find English words in original text
        words = re.findall(r'\b\w+\b', text.lower())
        english_words_in_text = [w for w in words if w in english_words]
        
        if not english_words_in_text:
            return 1.0  # Perfect protection (no English to protect)
        
        # Check how many were incorrectly corrected
        corrected_words = {c.original.lower() for c in corrections if hasattr(c, 'original')}
        incorrectly_corrected = sum(1 for w in english_words_in_text if w in corrected_words)
        
        protection_rate = 1.0 - (incorrectly_corrected / len(english_words_in_text))
        return max(0.0, protection_rate)
    
    def validate_corrections(self, corrections: List[Any]) -> Tuple[bool, List[str]]:
        """Validate corrections against quality rules."""
        issues = []
        
        for correction in corrections:
            if not hasattr(correction, 'original') or not hasattr(correction, 'corrected'):
                continue
                
            original = correction.original.lower()
            corrected = correction.corrected
            
            # Check for protected words
            for category, words in self.validation_rules['invalid_corrections']['protected_words'].items():
                if original in words:
                    issues.append(f"Protected {category} word '{original}' was corrected to '{corrected}'")
            
            # Check for suspicious patterns in original
            for pattern in self.validation_rules['invalid_corrections']['suspicious_patterns']:
                if re.search(pattern, correction.original):
                    issues.append(f"Suspicious correction: '{correction.original}' → '{corrected}' (pattern: {pattern})")
            
            # Check confidence levels
            if hasattr(correction, 'confidence'):
                if correction.confidence < 0.3:
                    issues.append(f"Very low confidence correction: '{original}' → '{corrected}' (confidence: {correction.confidence:.3f})")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def generate_quality_report(self, metrics: QualityMetrics, validation_issues: List[str]) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        # Determine overall quality grade
        quality_grade = self._calculate_quality_grade(metrics, validation_issues)
        
        # Generate recommendations
        recommendations = self._generate_quality_recommendations(metrics, validation_issues)
        
        return {
            'quality_grade': quality_grade,
            'metrics': {
                'total_corrections': metrics.total_corrections,
                'confidence_distribution': {
                    'high_confidence': f"{metrics.high_confidence_corrections} ({metrics.high_confidence_corrections/max(1,metrics.total_corrections)*100:.1f}%)",
                    'medium_confidence': f"{metrics.medium_confidence_corrections} ({metrics.medium_confidence_corrections/max(1,metrics.total_corrections)*100:.1f}%)",
                    'low_confidence': f"{metrics.low_confidence_corrections} ({metrics.low_confidence_corrections/max(1,metrics.total_corrections)*100:.1f}%)",
                    'questionable': f"{metrics.questionable_corrections} ({metrics.questionable_corrections/max(1,metrics.total_corrections)*100:.1f}%)"
                },
                'average_confidence': f"{metrics.avg_confidence:.3f}",
                'correction_diversity': f"{metrics.correction_diversity:.3f}",
                'english_protection_rate': f"{metrics.english_protection_rate:.3f}"
            },
            'validation_issues': len(validation_issues),
            'issue_details': validation_issues[:10],  # Show first 10 issues
            'recommendations': recommendations,
            'thresholds_met': self._check_thresholds(metrics),
            'performance_indicators': self._generate_performance_indicators(metrics)
        }
    
    def _calculate_quality_grade(self, metrics: QualityMetrics, issues: List[str]) -> str:
        """Calculate overall quality grade A-F."""
        score = 100
        
        # Deduct for low average confidence
        if metrics.avg_confidence < 0.8:
            score -= 20
        elif metrics.avg_confidence < 0.7:
            score -= 40
        
        # Deduct for high questionable rate
        questionable_rate = metrics.questionable_corrections / max(1, metrics.total_corrections)
        if questionable_rate > 0.1:
            score -= 30
        elif questionable_rate > 0.05:
            score -= 15
        
        # Deduct for poor English protection
        if metrics.english_protection_rate < 0.9:
            score -= 25
        elif metrics.english_protection_rate < 0.95:
            score -= 10
        
        # Deduct for validation issues
        score -= min(30, len(issues) * 5)
        
        # Convert to letter grade
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B' 
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_quality_recommendations(self, metrics: QualityMetrics, issues: List[str]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        if metrics.avg_confidence < 0.75:
            recommendations.append("Consider increasing confidence thresholds to improve correction quality")
        
        questionable_rate = metrics.questionable_corrections / max(1, metrics.total_corrections)
        if questionable_rate > 0.05:
            recommendations.append(f"High rate of questionable corrections ({questionable_rate:.2%}) - review fuzzy matching parameters")
        
        if metrics.english_protection_rate < 0.95:
            recommendations.append("Improve English word protection to prevent over-correction")
        
        if metrics.correction_diversity < 0.5:
            recommendations.append("Low correction diversity may indicate repetitive or overly broad matching")
        
        if len(issues) > 10:
            recommendations.append("Multiple validation issues detected - review correction logic")
        
        if not recommendations:
            recommendations.append("Quality metrics are within acceptable ranges")
        
        return recommendations
    
    def _check_thresholds(self, metrics: QualityMetrics) -> Dict[str, bool]:
        """Check if quality metrics meet defined thresholds."""
        questionable_rate = metrics.questionable_corrections / max(1, metrics.total_corrections)
        
        return {
            'min_avg_confidence': metrics.avg_confidence >= self.quality_thresholds['min_avg_confidence'],
            'max_questionable_rate': questionable_rate <= self.quality_thresholds['max_questionable_rate'],
            'min_english_protection': metrics.english_protection_rate >= self.quality_thresholds['min_english_protection'],
            'min_correction_diversity': metrics.correction_diversity >= self.quality_thresholds['min_correction_diversity']
        }
    
    def _generate_performance_indicators(self, metrics: QualityMetrics) -> Dict[str, str]:
        """Generate performance indicator summary."""
        total = metrics.total_corrections
        
        indicators = {
            'correction_volume': 'high' if total > 50 else 'medium' if total > 10 else 'low',
            'confidence_profile': 'excellent' if metrics.avg_confidence > 0.9 else 'good' if metrics.avg_confidence > 0.8 else 'acceptable' if metrics.avg_confidence > 0.7 else 'poor',
            'protection_quality': 'excellent' if metrics.english_protection_rate > 0.98 else 'good' if metrics.english_protection_rate > 0.95 else 'acceptable' if metrics.english_protection_rate > 0.9 else 'poor',
            'diversity_score': 'high' if metrics.correction_diversity > 0.8 else 'medium' if metrics.correction_diversity > 0.6 else 'low'
        }
        
        return indicators