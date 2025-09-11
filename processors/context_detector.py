"""Context Detection Module for Sanskrit Processing Pipeline

Implements three-layer context detection to prevent English→Sanskrit translation bugs
while preserving accurate Sanskrit processing capabilities.

Author: Development Agent
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContextResult:
    """Result of context detection analysis."""
    context_type: str  # 'english', 'sanskrit', 'mixed'
    confidence: float  # 0.0 to 1.0
    segments: List[Tuple[int, int, str]] = None  # For mixed content: (start, end, type)
    markers_found: List[str] = None  # Specific markers that influenced decision

class ContextDetector:
    """Three-layer context detection for Sanskrit processing pipeline."""
    
    def __init__(self, config_path: str = None):
        """Initialize context detector with language markers from configuration."""
        import yaml
        from pathlib import Path
        
        # Load configuration file
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'lexicons' / 'language_markers.yaml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Could not load language markers config from {config_path}: {e}")
            logger.warning("Falling back to built-in markers")
            config = self._get_default_config()
        
        # Load English markers
        english_config = config.get('english_markers', {})
        self.english_markers = {
            'function_words': set(english_config.get('function_words', [])),
            'progressive_tense': set(english_config.get('progressive_tense_words', [])),
            'past_tense': set(english_config.get('past_tense_words', [])),
            'modal_patterns': set(english_config.get('modal_patterns', []))
        }
        
        # Load Sanskrit markers  
        sanskrit_config = config.get('sanskrit_markers', {})
        self.sanskrit_markers = {
            'diacriticals': set(sanskrit_config.get('diacriticals', [])),
            'sacred_terms': set(sanskrit_config.get('sacred_terms', [])),
            'common_suffixes': set(sanskrit_config.get('common_suffixes', []))
        }
        
        # Load English blocklist
        self.english_blocklist = set(english_config.get('blocklist', []))
        
        # Load thresholds
        thresholds = config.get('thresholds', {})
        self.english_confidence_threshold = thresholds.get('english_confidence_threshold', 0.7)
        self.sanskrit_confidence_threshold = thresholds.get('sanskrit_confidence_threshold', 0.7)
        self.diacritical_density_high = thresholds.get('diacritical_density_high', 0.3)
        self.diacritical_density_medium = thresholds.get('diacritical_density_medium', 0.1)
        self.english_markers_required = thresholds.get('english_markers_required', 2)
    
    def _get_default_config(self):
        """Fallback configuration if YAML file cannot be loaded."""
        return {
            'english_markers': {
                'function_words': [
                    'the', 'is', 'are', 'was', 'were', 'am', 'be', 'being', 'been',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                    'should', 'may', 'might', 'can', 'shall', 'must', 'ought',
                    'a', 'an', 'and', 'or', 'but', 'nor', 'for', 'yet', 'so',
                    'in', 'on', 'at', 'by', 'to', 'of', 'with', 'from', 'about'
                ],
                'progressive_tense_words': ['treading', 'reading', 'leading', 'heading'],
                'past_tense_words': ['agitated', 'meditated', 'dedicated'],
                'modal_patterns': ['was ', 'were ', 'is ', 'are '],
                'blocklist': [
                    'treading', 'reading', 'leading', 'heading', 'feeding', 'needing',
                    'agitated', 'meditated', 'dedicated', 'concentrated', 'frustrated',
                    'guru', 'teacher', 'student', 'devotee', 'practitioner', 'master',
                    'the', 'they', 'them', 'their', 'there', 'these', 'those', 'this',
                    'was', 'were', 'will', 'would', 'when', 'where', 'what', 'who',
                    'through', 'forest', 'delay', 'session', 'together', 'carefully'
                ]
            },
            'sanskrit_markers': {
                'diacriticals': ['ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ṅ', 'ñ', 'ṇ', 'ṭ', 'ḍ', 'ś', 'ṣ', 'ḥ', 'ṁ'],
                'sacred_terms': [
                    'oṁ', 'oṃ', 'namaḥ', 'namah', 'śrī', 'sri', 'mahā', 'maha',
                    'bhagavad', 'gītā', 'gita', 'rāmāyaṇa', 'ramayana', 'dharma',
                    'karma', 'yoga', 'vedanta', 'upaniṣad', 'upanishad'
                ],
                'common_suffixes': ['āya', 'aya', 'āni', 'ani', 'asya', 'ānām', 'anam']
            },
            'thresholds': {
                'english_confidence_threshold': 0.7,
                'sanskrit_confidence_threshold': 0.7,
                'diacritical_density_high': 0.3,
                'diacritical_density_medium': 0.1,
                'english_markers_required': 2
            }
        }
    
    def detect_context(self, text: str) -> ContextResult:
        """
        Main context detection method using three-layer algorithm.
        
        Args:
            text: Input text to analyze
            
        Returns:
            ContextResult with detected context type and details
        """
        if not text or not text.strip():
            return ContextResult('english', 1.0, markers_found=['empty_text'])
        
        # Layer 1: Fast English Protection
        english_result = self.is_pure_english(text)
        if english_result.confidence >= self.english_confidence_threshold:
            return english_result
        
        # Layer 2: Fast Sanskrit Acceptance  
        sanskrit_result = self.has_sanskrit_markers(text)
        if sanskrit_result.confidence >= self.sanskrit_confidence_threshold:
            return sanskrit_result
        
        # For single Sanskrit words, be more generous
        words = text.strip().split()
        if len(words) == 1:
            word_lower = words[0].lower()
            if (word_lower in self.sanskrit_markers['sacred_terms'] or
                any(char in words[0] for char in self.sanskrit_markers['diacriticals'])):
                return ContextResult('sanskrit', 0.8, markers_found=['single_sanskrit_word'])
        
        # Layer 3: Mixed Content Analysis
        return self.analyze_mixed_content(text)
    
    def is_pure_english(self, text: str) -> ContextResult:
        """
        Layer 1: Fast detection of pure English content.
        
        Returns high confidence for text that should pass through unchanged.
        """
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        if not words:
            return ContextResult('english', 0.5, markers_found=['no_words'])
        
        markers_found = []
        score = 0
        
        # Check for pure ASCII
        is_ascii = all(ord(char) < 128 for char in text)
        if is_ascii:
            score += 0.3
            markers_found.append('pure_ascii')
        
        # Count English function words
        function_word_count = sum(1 for word in words 
                                if word in self.english_markers['function_words'])
        
        if function_word_count >= self.english_markers_required:
            score += 0.4
            markers_found.append(f'function_words_{function_word_count}')
        
        # Check for English patterns
        for pattern in self.english_markers['modal_patterns']:
            if pattern in text_lower:
                score += 0.2
                markers_found.append(f'modal_pattern_{pattern.strip()}')
        
        # Check for progressive tense
        if any(word.endswith('ing') for word in words):
            score += 0.2
            markers_found.append('progressive_tense')
        
        # Check for past tense
        if any(word.endswith('ed') for word in words):
            score += 0.2
            markers_found.append('past_tense')
        
        # Check English blocklist words
        blocklist_matches = [word for word in words if word in self.english_blocklist]
        if blocklist_matches:
            score += 0.5
            markers_found.extend([f'blocklist_{word}' for word in blocklist_matches[:3]])
        
        # English sentence patterns
        if re.search(r'\b(he|she|they|it)\s+(was|were|is|are)\b', text_lower):
            score += 0.3
            markers_found.append('english_sentence_pattern')
        
        return ContextResult('english', min(score, 1.0), markers_found=markers_found)
    
    def has_sanskrit_markers(self, text: str) -> ContextResult:
        """
        Layer 2: Fast detection of Sanskrit content.
        
        Returns high confidence for text that should be fully processed.
        """
        markers_found = []
        score = 0
        
        # Count Sanskrit diacriticals
        diacritical_chars = [char for char in text if char in self.sanskrit_markers['diacriticals']]
        if diacritical_chars:
            # Calculate diacritical density
            total_chars = len([c for c in text if c.isalpha()])
            if total_chars > 0:
                density = len(diacritical_chars) / total_chars
                if density > self.diacritical_density_high:  # >30% diacritical density
                    score += 0.6
                    markers_found.append(f'high_diacritical_density_{density:.2f}')
                elif density > self.diacritical_density_medium:  # >10% diacritical density
                    score += 0.3
                    markers_found.append(f'medium_diacritical_density_{density:.2f}')
        
        # Check for Sanskrit sacred terms
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        sanskrit_terms = [word for word in words 
                         if word in self.sanskrit_markers['sacred_terms']]
        if sanskrit_terms:
            score += 0.4
            markers_found.extend([f'sanskrit_term_{term}' for term in sanskrit_terms[:3]])
        
        # Check for Sanskrit suffixes
        for word in words:
            for suffix in self.sanskrit_markers['common_suffixes']:
                if word.endswith(suffix):
                    score += 0.2
                    markers_found.append(f'sanskrit_suffix_{suffix}')
                    break
        
        # Check for specific Sanskrit phrases
        if re.search(r'oṁ\s+namaḥ|bhagavad\s+gītā|śrī\s+\w+', text, re.IGNORECASE):
            score += 0.5
            markers_found.append('sanskrit_phrase_pattern')
        
        return ContextResult('sanskrit', min(score, 1.0), markers_found=markers_found)
    
    def analyze_mixed_content(self, text: str) -> ContextResult:
        """
        Layer 3: Detailed analysis for mixed content.
        
        Returns segment boundaries for selective processing.
        """
        words = re.findall(r'\S+', text)  # Include punctuation
        word_contexts = []
        
        for word in words:
            # Clean word for analysis (remove punctuation)
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if not clean_word:
                word_contexts.append('neutral')
                continue
            
            # Check if word is clearly English
            if clean_word in self.english_blocklist:
                word_contexts.append('english')
            elif clean_word in self.english_markers['function_words']:
                word_contexts.append('english')
            elif any(char in word for char in self.sanskrit_markers['diacriticals']):
                word_contexts.append('sanskrit')
            elif clean_word in self.sanskrit_markers['sacred_terms']:
                word_contexts.append('sanskrit')
            else:
                word_contexts.append('neutral')
        
        # Find Sanskrit segments (consecutive Sanskrit/neutral words)
        segments = []
        current_segment_start = None
        current_segment_type = None
        
        for i, (word, context) in enumerate(zip(words, word_contexts)):
            if context == 'sanskrit':
                if current_segment_type != 'sanskrit':
                    # Start new Sanskrit segment
                    current_segment_start = i
                    current_segment_type = 'sanskrit'
            elif context == 'english':
                if current_segment_type == 'sanskrit':
                    # End Sanskrit segment
                    segments.append((current_segment_start, i, 'sanskrit'))
                    current_segment_start = None
                    current_segment_type = None
            # 'neutral' words continue current segment
        
        # Close final segment if needed
        if current_segment_type == 'sanskrit':
            segments.append((current_segment_start, len(words), 'sanskrit'))
        
        # Determine overall context
        sanskrit_words = sum(1 for ctx in word_contexts if ctx == 'sanskrit')
        english_words = sum(1 for ctx in word_contexts if ctx == 'english')
        neutral_words = sum(1 for ctx in word_contexts if ctx == 'neutral')
        
        # If we have Sanskrit words and English words, it's definitely mixed
        if sanskrit_words > 0 and english_words > 0:
            overall_context = 'mixed'
        # If only Sanskrit words (no English), it's Sanskrit
        elif sanskrit_words > 0 and english_words == 0:
            overall_context = 'sanskrit'
        # If only English words detected, it's English
        elif english_words > 0 and sanskrit_words == 0:
            overall_context = 'english'
        # If no clear indicators, default to mixed for safety
        else:
            overall_context = 'mixed'
        
        markers_found = [f'segments_{len(segments)}', f'sanskrit_words_{sanskrit_words}', f'english_words_{english_words}']
        
        confidence = 0.7
        if overall_context == 'mixed' and len(segments) > 0:
            confidence = 0.8  # Higher confidence if we found clear segments
        
        return ContextResult(
            overall_context, 
            confidence,
            segments=segments,
            markers_found=markers_found
        )
    
    def should_process_segment(self, text: str, start_idx: int, end_idx: int) -> bool:
        """
        Determine if a specific segment should be processed.
        
        Args:
            text: Full text
            start_idx: Start word index
            end_idx: End word index
            
        Returns:
            True if segment should be processed for Sanskrit corrections
        """
        words = re.findall(r'\S+', text)
        segment_words = words[start_idx:end_idx]
        segment_text = ' '.join(segment_words)
        
        # Quick Sanskrit marker check
        has_diacriticals = any(char in segment_text for char in self.sanskrit_markers['diacriticals'])
        has_sanskrit_terms = any(word.lower() in self.sanskrit_markers['sacred_terms'] 
                               for word in segment_words)
        
        return has_diacriticals or has_sanskrit_terms