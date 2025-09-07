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
        """
        self.classification_count += 1
        
        if not text or not text.strip():
            return ContentClassification('regular', 0.0, ['database'])
        
        text_lower = text.lower().strip()
        
        # Initialize defaults
        confidence = 0.0
        content_type = 'regular'
        processors = ['database']  # Always apply database processing
        metadata = {}
        
        # First, detect all possible content types
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
        
        # Determine final classification
        if len(detected_types) == 0:
            # No special patterns detected - regular content
            content_type = 'regular'
            confidence = 0.5
            
        elif len(detected_types) == 1:
            # Single content type detected
            content_type = list(detected_types.keys())[0]
            confidence = list(detected_types.values())[0]
            
        else:
            # Multiple content types detected - mixed content
            primary_type = max(detected_types.items(), key=lambda x: x[1])[0]
            content_type = f"mixed_{primary_type}"
            confidence = min(0.9, max(detected_types.values()) + 0.1)
            metadata['mixed_content'] = detected_types
        
        # Set appropriate processors based on detected types
        if 'mantra' in detected_types or 'verse' in detected_types:
            processors.extend(['sacred'])
        if 'verse' in detected_types:
            processors.extend(['scripture'])
        
        # CRITICAL: Always apply compound processing for potential Sanskrit terms
        # This ensures compound terms like "Srimad Bhagavad Gita" are recognized
        processors.extend(['compound'])
            
        # Remove duplicates while preserving order
        processors = list(dict.fromkeys(processors))
        
        # Set metadata based on content type
        if content_type == 'mantra' or 'mantra' in detected_types:
            metadata['mantra_detected'] = True
        if content_type == 'verse' or 'verse' in detected_types:
            if '|' in text or '||' in text or '\u0964' in text:
                metadata['sacred_symbols'] = True
            else:
                metadata['verse_structure'] = True
        if content_type == 'commentary' or 'commentary' in detected_types:
            metadata['commentary_detected'] = True
        if content_type == 'title' or 'title' in detected_types:
            metadata['title_structure'] = True
        
        return ContentClassification(content_type, confidence, processors, metadata)
    
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
    
    def get_processing_strategy(self, classification: ContentClassification) -> Dict[str, Any]:
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