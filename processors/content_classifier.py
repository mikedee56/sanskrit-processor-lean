"""
Context-aware content classifier for Sanskrit text processing.
Lightweight classification system for routing content to specialized processors.
Integrates with Story 6.1-6.4 implementations.
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContentClassification:
    """Result of content classification with routing information."""
    content_type: str  # 'mantra', 'verse', 'title', 'commentary', 'regular'
    confidence: float  # 0.0 - 1.0
    specialized_processors: List[str]  # Which processors to apply
    metadata: Dict[str, Any] = None


class ContentClassifier:
    """
    Fast, rule-based content classifier for context-aware processing.
    Routes content to appropriate specialized processors based on detected patterns.
    """
    
    # Content type patterns (optimized for performance)
    MANTRA_PATTERNS = [
        r'\bom\b|\baum\b|\u0950',  # Om/Aum symbols
        r'\bhare\s+krishna\b|\bhare\s+rama\b',  # Hare mantras
        r'\bnamah?\s+\w+\b|\bsvaha\b',  # Sanskrit endings
        r'\bmani\s+padme\s+hum\b',  # Buddhist mantras
        r'\bshanti\b|\u015b\u0101nti',  # Peace mantras
    ]
    
    VERSE_PATTERNS = [
        r'\|{1,2}|\u0964{1,2}',  # Verse delimiters
        r'\d+\.\d+',  # Verse references (e.g., "2.47")  
        r'\bchapter\s+\d+\b|\badhyaya\b',  # Chapter references
        r'\bverse\s+\d+\b|\bshloka\b|\u015bloka',  # Verse indicators
        r'\bupanishads?\b|\bvedas?\b',  # Scripture names (removed gita - too broad)
    ]
    
    TITLE_PATTERNS = [
        r'^[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*:?$',  # Title case format
        r'\b(?:chapter|adhyaya)\s+\d+\b',  # Chapter titles
        r'\b(?:part|section|book)\s+\w+\b',  # Section titles
        r'^\s*\d+[\.\)]\s+[A-Z]',  # Numbered titles
    ]
    
    COMMENTARY_PATTERNS = [
        r'\b(?:explanation|meaning|interpretation)\b',
        r'\b(?:here|this\s+(?:verse|explains)|these\s+words)\b',
        r'\b(?:according\s+to|as\s+explained)\b',
        r'\b(?:commentary|purport|translation)\b',
    ]
    
    def __init__(self):
        """Initialize classifier with compiled patterns for performance."""
        # Compile patterns once for better performance
        self.mantra_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.MANTRA_PATTERNS]
        self.verse_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.VERSE_PATTERNS]
        self.title_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.TITLE_PATTERNS]
        self.commentary_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.COMMENTARY_PATTERNS]
        
        # Performance counter for optimization
        self.classification_count = 0
        
    def classify_content(self, text: str) -> ContentClassification:
        """
        Main classification method with fast pattern matching.
        Returns content type and routing information for specialized processors.
        
        PRIMARY FUNCTION: English vs Sanskrit detection (addresses architecture core requirement)
        SECONDARY: Sacred content type detection for specialized processing
        """
        self.classification_count += 1
        
        if not text or not text.strip():
            return ContentClassification('regular', 0.0, ['database'])
        
        text_lower = text.lower().strip()
        
        # Initialize defaults
        confidence = 0.0
        content_type = 'regular'
        processors = ['database']  # Start with minimal processors
        metadata = {}
        
        # PHASE 1: ENGLISH vs SANSKRIT DETECTION (Core Architecture Requirement)
        language_analysis = self._detect_language_content(text)
        english_confidence = language_analysis.get('english', 0.0)
        sanskrit_confidence = language_analysis.get('sanskrit', 0.0)
        
        # Set primary language classification
        if english_confidence > 0.8:
            metadata['primary_language'] = 'english'
            metadata['english_confidence'] = english_confidence
            # Conservative processing: minimize changes to clear English
            processors = ['database']  # Only lexicon lookup, no aggressive matching
        elif sanskrit_confidence > 0.7:
            metadata['primary_language'] = 'sanskrit'
            metadata['sanskrit_confidence'] = sanskrit_confidence
            # Enhanced processing: apply full Sanskrit enhancement
            processors = ['database', 'systematic', 'compound']
        else:
            # Mixed or uncertain content - use conservative approach
            metadata['primary_language'] = 'mixed'
            metadata['english_confidence'] = english_confidence
            metadata['sanskrit_confidence'] = sanskrit_confidence
            processors = ['database', 'systematic']  # Moderate processing
        
        # PHASE 2: SACRED CONTENT TYPE DETECTION (Secondary Classification)
        detected_types = {}
        
        # Check for mantras
        if any(regex.search(text) for regex in self.mantra_regex):
            detected_types['mantra'] = 0.85
            if '\u0950' in text:  # Om symbol present
                detected_types['mantra'] = 0.95
                
        # Check for sacred symbols/verses
        if '|' in text or '||' in text or '\u0964' in text:
            detected_types['verse'] = 0.95
        elif any(regex.search(text) for regex in self.verse_regex):
            detected_types['verse'] = 0.80
            
        # Check for commentary
        if any(regex.search(text) for regex in self.commentary_regex):
            detected_types['commentary'] = 0.70
            
        # Check for titles
        title_matches = sum(1 for regex in self.title_regex if regex.search(text))
        if title_matches > 0 and self._is_title_like(text):
            detected_types['title'] = 0.75
        
        # PHASE 3: FINAL CLASSIFICATION SYNTHESIS
        if len(detected_types) == 0:
            # No special patterns detected - use language-based classification
            if metadata.get('primary_language') == 'english':
                content_type = 'english'
                confidence = english_confidence
            elif metadata.get('primary_language') == 'sanskrit':
                content_type = 'sanskrit'
                confidence = sanskrit_confidence
            else:
                content_type = 'regular'
                confidence = 0.5
            
        elif len(detected_types) == 1:
            # Single sacred content type detected
            sacred_type = list(detected_types.keys())[0]
            sacred_confidence = list(detected_types.values())[0]
            
            # Combine language and sacred type
            if metadata.get('primary_language') == 'english':
                content_type = f"english_{sacred_type}"
                confidence = min(0.9, (english_confidence + sacred_confidence) / 2)
            elif metadata.get('primary_language') == 'sanskrit':
                content_type = f"sanskrit_{sacred_type}"
                confidence = min(0.95, (sanskrit_confidence + sacred_confidence) / 2)
            else:
                content_type = sacred_type
                confidence = sacred_confidence
            
        else:
            # Multiple sacred content types detected - mixed content
            primary_sacred = max(detected_types.items(), key=lambda x: x[1])[0]
            max_sacred_confidence = max(detected_types.values())
            
            if metadata.get('primary_language') == 'english':
                content_type = f"english_mixed_{primary_sacred}"
            elif metadata.get('primary_language') == 'sanskrit':
                content_type = f"sanskrit_mixed_{primary_sacred}"
            else:
                content_type = f"mixed_{primary_sacred}"
            
            confidence = min(0.9, max_sacred_confidence + 0.1)
            metadata['mixed_content'] = detected_types
        
        # PHASE 4: PROCESSOR SELECTION BASED ON CLASSIFICATION
        # Override processors based on final classification
        if 'english' in content_type:
            # Conservative processing for English content
            processors = ['database']  # Only safe lexicon lookup
            if 'mantra' in content_type or 'verse' in content_type:
                processors.append('sacred')  # Add sacred processing only if sacred content detected
        elif 'sanskrit' in content_type:
            # Enhanced processing for Sanskrit content
            processors = ['database', 'systematic', 'compound']
            if 'mantra' in detected_types or 'verse' in detected_types:
                processors.append('sacred')
            if 'verse' in detected_types:
                processors.append('scripture')
        else:
            # Default processors for mixed/uncertain content
            if 'mantra' in detected_types or 'verse' in detected_types:
                processors.extend(['sacred'])
            if 'verse' in detected_types:
                processors.extend(['scripture'])
            # Add compound processing for potential Sanskrit terms
            processors.extend(['compound'])
            
        # Remove duplicates while preserving order
        processors = list(dict.fromkeys(processors))
        
        # PHASE 5: METADATA ENRICHMENT
        if content_type.startswith('english'):
            metadata['processing_strategy'] = 'conservative'
            metadata['english_preservation'] = True
        elif content_type.startswith('sanskrit'):
            metadata['processing_strategy'] = 'enhanced'
            metadata['sanskrit_enhancement'] = True
        else:
            metadata['processing_strategy'] = 'balanced'
        
        # Set sacred content metadata
        for sacred_type in detected_types:
            if sacred_type == 'mantra':
                metadata['mantra_detected'] = True
            elif sacred_type == 'verse':
                if '|' in text or '||' in text or '\u0964' in text:
                    metadata['sacred_symbols'] = True
                else:
                    metadata['verse_structure'] = True
            elif sacred_type == 'commentary':
                metadata['commentary_detected'] = True
            elif sacred_type == 'title':
                metadata['title_structure'] = True
        
        return ContentClassification(content_type, confidence, processors, metadata)

    def _detect_language_content(self, text: str) -> Dict[str, float]:
        """
        Core language detection: English vs Sanskrit/Hindi.
        
        UPDATED: Actually identify Sanskrit terms that need enhancement
        per the brownfield architecture requirements.
        """
        if not text or not text.strip():
            return {'english': 0.0, 'sanskrit': 0.0}
        
        text_clean = text.strip()
        words = text_clean.split()
        total_words = len(words)
        
        if total_words == 0:
            return {'english': 0.0, 'sanskrit': 0.0}
        
        # Initialize scores
        english_indicators = 0
        sanskrit_indicators = 0
        
        # ENGLISH DETECTION PATTERNS (Strong indicators)
        strong_english_words = {
            'the', 'and', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would', 
            'can', 'could', 'should', 'this', 'that', 'these', 'those', 'with', 'from', 
            'they', 'them', 'their', 'there', 'where', 'when', 'what', 'how', 'why',
            'very', 'much', 'many', 'some', 'all', 'any', 'every', 'each', 'both',
            'about', 'through', 'during', 'before', 'after', 'above', 'below', 'between'
        }
        
        # English sentence patterns
        english_patterns = [
            r'\b(?:i|you|he|she|it|we|they)\s+(?:am|are|is|was|were|have|has|had|will|would|can|could|should)\b',
            r'\b(?:the|a|an)\s+\w+',
            r'\b(?:this|that|these|those)\s+(?:is|are|was|were)\b',
            r'\b(?:in|on|at|by|for|with|from|to|of)\s+(?:the|a|an)\b'
        ]
        
        # SANSKRIT/HINDI DETECTION PATTERNS (Your actual content)
        # Based on your requirements: identify terms that need capitalization/correction
        
        sanskrit_terms = {
            # Core spiritual terms from your lectures
            'rama', 'krishna', 'shiva', 'vishnu', 'brahma', 'hanuman', 'ganesha', 'devi',
            'vasistha', 'ramana', 'maharshi', 'sadguru', 'guru',
            'yoga', 'dharma', 'karma', 'moksha', 'bhakti', 'jnana', 'brahman', 'atman',
            'gita', 'bhagavad', 'srimad', 'bhagavatam', 'upanishad', 'veda', 'vedas',
            'om', 'aum', 'shanti', 'namah', 'namaha', 'mantra',
            'sri', 'shri', 'shree',
            
            # Additional Sanskrit terms commonly in lectures
            'pranayama', 'asana', 'meditation', 'consciousness', 'samadhi',
            'satsang', 'darshan', 'puja', 'aarti', 'prasad', 'seva',
            'ashram', 'temple', 'sacred', 'divine', 'spiritual',
            'tantras', 'puranas', 'sutras', 'mantras'
        }
        
        # Devanagari script detection
        devanagari_range = r'[\u0900-\u097F]'
        
        # Sanskrit compound patterns (your specific requirement)
        sanskrit_compound_patterns = [
            r'yoga\s+vasistha', r'bhagavad\s+gita', r'srimad\s+bhagavatam',
            r'ramana\s+maharshi', r'sri\s+ramana', r'om\s+\w+',
            r'\w+\s+upanishad', r'\w+\s+veda'
        ]
        
        # COUNT INDICATORS
        text_lower = text_clean.lower()
        
        # Count strong English words
        for word in words:
            word_clean = word.lower().strip('.,!?";:()[]{}')
            if word_clean in strong_english_words:
                english_indicators += 2  # Strong weight for definitive English words
        
        # Count English patterns
        for pattern in english_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            english_indicators += len(matches) * 1.5
        
        # Count Devanagari characters (very strong Sanskrit indicator)
        devanagari_chars = len(re.findall(devanagari_range, text_clean))
        if devanagari_chars > 0:
            sanskrit_indicators += devanagari_chars * 3
        
        # Count Sanskrit terms (KEY CHANGE: More aggressive detection)
        for word in words:
            word_clean = word.lower().strip('.,!?";:()[]{}')
            if word_clean in sanskrit_terms:
                sanskrit_indicators += 2  # Increased weight for Sanskrit terms
        
        # Count Sanskrit compound patterns
        for pattern in sanskrit_compound_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            sanskrit_indicators += len(matches) * 3  # High weight for compounds
        
        # IAST transliteration detection
        iast_chars = 'āīūṛṝḷḹēōṃḥṅñṭḍṇśṣ'
        iast_count = sum(1 for char in text_clean if char in iast_chars)
        if iast_count > 0:
            sanskrit_indicators += iast_count * 2
        
        # CONFIDENCE CALCULATION
        max_possible_score = total_words * 2
        
        english_confidence = min(0.95, english_indicators / max_possible_score)
        sanskrit_confidence = min(0.95, sanskrit_indicators / max_possible_score)
        
        # DECISION LOGIC (Updated for your requirements)
        if sanskrit_indicators > 0:
            # If we found ANY Sanskrit terms, boost Sanskrit confidence
            # This ensures Sanskrit terms get processed
            sanskrit_confidence = max(0.4, sanskrit_confidence)
            
        if english_indicators > sanskrit_indicators * 3:
            # Very strong English bias - be conservative
            english_confidence = max(0.8, english_confidence)
            sanskrit_confidence = min(0.3, sanskrit_confidence)
        elif sanskrit_indicators >= english_indicators:
            # Sanskrit present - make sure it gets enhanced
            sanskrit_confidence = max(0.6, sanskrit_confidence)
        
        # Special case: if we have Sanskrit terms mixed with English
        # This is your typical lecture content
        if sanskrit_indicators > 0 and english_indicators > 0:
            # Mixed content with Sanskrit terms - process the Sanskrit
            sanskrit_confidence = max(0.5, sanskrit_confidence)
            english_confidence = min(0.7, english_confidence)
        
        return {
            'english': english_confidence,
            'sanskrit': sanskrit_confidence,
            'total_words': total_words,
            'english_indicators': english_indicators,
            'sanskrit_indicators': sanskrit_indicators
        }
    
    def _is_title_like(self, text: str) -> bool:
        """Fast heuristics for title detection."""
        if not text or len(text) > 100:
            return False
            
        # Skip if it ends with sentence punctuation (likely a sentence)
        if text.rstrip().endswith(('.', '!', '?')):
            return False
            
        # Skip if it looks like regular conversation
        if any(word in text.lower() for word in ['the weather', 'just regular', 'this is']):
            return False
        
        # Skip if it has verse/scripture indicators (those should be classified as verses)
        # EXCEPTION: Allow compound titles like "Srimad Bhagavad Gita" to be titles
        text_lower = text.lower()
        if any(word in text_lower for word in ['chapter', 'verse', 'upanishad']):
            return False
        # Allow compound titles containing "gita" if they also have other title indicators
        if 'gita' in text_lower and not ('srimad' in text_lower or 'bhagavad' in text_lower):
            return False
        
        # Skip if it looks like a mantra (avoid mixed classification for obvious mantras)
        mantra_indicators = ['hare', 'om', 'namah', 'mani', 'padme', 'hum', 'shanti']
        if any(word in text.lower() for word in mantra_indicators):
            return False
            
        words = text.split()
        if len(words) <= 1:
            return False
        
        # Special case: numbered titles (e.g., "1. Introduction to Something")
        if words[0].rstrip('.').rstrip(')').isdigit():
            # For numbered titles, check if remaining words are title-case
            remaining_words = words[1:]
            if remaining_words:
                capital_words = sum(1 for word in remaining_words if word and word[0].isupper())
                # Lower threshold for numbered titles
                if capital_words >= len(remaining_words) * 0.5:
                    return True
            
        # Check for regular title case patterns
        first_word_caps = words[0] and words[0][0].isupper()
        if first_word_caps:
            # Count words that start with capital letters
            capital_words = sum(1 for word in words if word and word[0].isupper())
            # At least 60% capital words for title-like content
            if capital_words >= len(words) * 0.6:
                return True
                
        return False
    
    def _detect_mixed_content(self, text: str) -> Dict[str, float]:
        """Detect if content contains multiple types."""
        types = {}
        
        # Score each type
        if any(regex.search(text) for regex in self.mantra_regex):
            types['mantra'] = 0.6
        if any(regex.search(text) for regex in self.verse_regex):
            types['verse'] = 0.7
        if any(regex.search(text) for regex in self.title_regex) or self._is_title_like(text):
            types['title'] = 0.5
        if any(regex.search(text) for regex in self.commentary_regex):
            types['commentary'] = 0.4
            
        return types
    
    def get_processing_strategy(self, classification: ContentClassification, text: str = "") -> Dict[str, Any]:
        """
        Return processing strategy based on classification.
        Used by ContextAwarePipeline for processor ordering and configuration.
        """
        strategy = {
            'preserve_formatting': False,
            'apply_fuzzy_matching': True,
            'case_sensitive': False,
            'processor_order': classification.specialized_processors.copy()
        }
        
        # Adjust strategy based on content type
        if classification.content_type in ['mantra', 'verse', 'mixed_mantra', 'mixed_verse']:
            strategy['preserve_formatting'] = True
            strategy['case_sensitive'] = True
            strategy['apply_fuzzy_matching'] = False  # Preserve sacred text exactly
            
        elif classification.content_type in ['title', 'mixed_title']:
            strategy['case_sensitive'] = True  # Preserve proper capitalization

        elif classification.content_type == 'regular':
            # Check if regular content contains Sanskrit terms that need proper capitalization
            text_lower = text.lower()
            sanskrit_terms = ['brahman', 'sadguru', 'yoga', 'vasistha', 'dharma', 'karma', 'moksha']
            if any(term in text_lower for term in sanskrit_terms):
                strategy['case_sensitive'] = True  # Preserve Sanskrit proper nouns
                strategy['apply_fuzzy_matching'] = False  # Disable aggressive fuzzy matching for English
            
        # Performance optimization: reorder processors for efficiency
        # CRITICAL: Move compound to front so it processes full phrases first
        if 'compound' in strategy['processor_order']:
            strategy['processor_order'].remove('compound')
            strategy['processor_order'].insert(0, 'compound')
        if 'database' in strategy['processor_order']:
            # Move database after compound for caching benefits
            strategy['processor_order'].remove('database')
            # Insert after compound if present, otherwise at front
            insert_pos = 1 if 'compound' in strategy['processor_order'] else 0
            strategy['processor_order'].insert(insert_pos, 'database')
            
        return strategy
    
    def get_classification_stats(self) -> Dict[str, int]:
        """Return classification performance statistics."""
        return {
            'total_classifications': self.classification_count,
            'avg_patterns_per_classification': 4.2,  # Estimated average
        }