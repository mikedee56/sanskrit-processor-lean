#!/usr/bin/env python3
"""
Database Validation Module
Validation rules for Sanskrit database entries
Part of Story 9.3: Database Cleanup & Validation

This module provides comprehensive validation for Sanskrit database entries,
preventing English contamination while preserving authentic Sanskrit content.
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Union, Optional

# Sanskrit diacriticals for validation
SANSKRIT_CHARS = set('āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ')

# Comprehensive Sanskrit whitelist
SANSKRIT_WHITELIST = {
    # Core spiritual concepts
    'dharma', 'karma', 'yoga', 'guru', 'mantra', 'chakra', 'tantra',
    'brahman', 'atman', 'moksha', 'samsara', 'nirvana', 'ashrama',
    'ahimsa', 'satya', 'asteya', 'brahmacharya', 'aparigraha',
    
    # Deities and divine names
    'indra', 'vishnu', 'shiva', 'brahma', 'krishna', 'rama', 'gita',
    'hanuman', 'ganesha', 'lakshmi', 'saraswati', 'durga', 'kali',
    'surya', 'chandra', 'agni', 'vayu', 'prithvi', 'akasha',
    
    # Sacred texts and literature
    'ramayana', 'mahabharata', 'upanishad', 'veda', 'vedanta', 'purana',
    'bhagavad', 'rig', 'sama', 'yajur', 'atharva', 'smrti', 'shruti',
    
    # Yoga and spiritual practices
    'pranayama', 'asana', 'samadhi', 'dhyana', 'dharana', 'pratyahara',
    'yama', 'niyama', 'bandha', 'mudra', 'prana', 'apana', 'sushumna',
    'ida', 'pingala', 'nadis', 'kundalini', 'samana', 'udana', 'vyana',
    
    # Chakras and energy centers
    'ajna', 'muladhara', 'swadhisthana', 'manipura', 'anahata', 
    'vishuddha', 'sahasrara',
    
    # Philosophical terms
    'saucha', 'santosha', 'tapas', 'svadhyaya', 'ishvara', 'pranidhana',
    'samskara', 'vritti', 'chitta', 'buddhi', 'manas', 'ahamkara',
    'mahat', 'prakriti', 'purusha', 'guna', 'sattva', 'rajas', 'tamas',
    
    # Sanskrit grammatical and linguistic terms
    'sandhi', 'pada', 'sloka', 'mantra', 'bija', 'yantra', 'mudra',
    'raga', 'tala', 'shruti', 'swara', 'varṇa', 'akshara'
}

# Definite English words that should be rejected
ENGLISH_REJECT_LIST = {
    # Common English verbs with -ing endings that were causing issues
    'treading', 'agitated', 'reading', 'leading', 'teaching', 'learning',
    'walking', 'talking', 'thinking', 'feeling', 'being', 'doing',
    'having', 'going', 'coming', 'seeing', 'hearing', 'knowing',
    
    # Common English function words
    'the', 'and', 'or', 'but', 'if', 'then', 'when', 'where', 'how', 'why',
    'what', 'who', 'which', 'that', 'this', 'these', 'those', 'here', 'there',
    'now', 'then', 'always', 'never', 'often', 'sometimes', 'usually',
    
    # Common English prepositions
    'about', 'above', 'across', 'after', 'against', 'along', 'among',
    'around', 'before', 'behind', 'below', 'beneath', 'beside', 'between',
    'beyond', 'during', 'except', 'inside', 'instead', 'outside', 'through',
    'throughout', 'together', 'towards', 'under', 'until', 'within', 'without',
    
    # Common problematic words from analysis
    'english', 'language', 'word', 'text', 'translation', 'meaning',
    'dictionary', 'vocabulary', 'grammar', 'syntax'
}

class SanskritEntryValidator:
    """
    Validator for Sanskrit database entries.
    
    Provides comprehensive validation for Sanskrit terms to prevent English
    contamination while preserving authentic Sanskrit content.
    
    Attributes:
        sanskrit_chars: Set of Sanskrit diacritical characters
        whitelist: Set of confirmed valid Sanskrit terms  
        reject_list: Set of definite English words to reject
    """
    
    def __init__(self) -> None:
        """Initialize the validator with Sanskrit character sets and validation lists."""
        self.sanskrit_chars = SANSKRIT_CHARS
        self.whitelist = SANSKRIT_WHITELIST
        self.reject_list = ENGLISH_REJECT_LIST
        self.logger = logging.getLogger(__name__)
    
    def validate_entry(self, entry: Dict[str, Union[str, None]]) -> Tuple[bool, str]:
        """
        Validate a Sanskrit database entry.
        
        Args:
            entry: Dictionary with 'original_term', 'transliteration', 'variations'
        
        Returns:
            Tuple of (is_valid, reason)
        """
        original = (entry.get('original_term') or '').strip()
        transliteration = (entry.get('transliteration') or '').strip()
        variations = entry.get('variations', '')
        
        # Skip empty entries
        if not original and not transliteration:
            return False, "Empty entry"
        
        # Check for definite English rejection
        if original.lower() in self.reject_list:
            return False, f"Definite English word: '{original}'"
        
        if transliteration.lower() in self.reject_list:
            return False, f"Definite English transliteration: '{transliteration}'"
        
        # Check for English with synthetic diacriticals
        if original:
            ascii_original = re.sub(r'[āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ]', '', original)
            if ascii_original.lower() in self.reject_list:
                return False, f"English word with synthetic diacriticals: '{original}' -> '{ascii_original}'"
        
        if transliteration:
            ascii_transliteration = re.sub(r'[āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ]', '', transliteration)
            if ascii_transliteration.lower() in self.reject_list:
                return False, f"English transliteration with synthetic diacriticals: '{transliteration}' -> '{ascii_transliteration}'"
        
        # Check if whitelisted (automatically valid)
        if (original.lower() in self.whitelist or 
            transliteration.lower() in self.whitelist):
            return True, "Whitelisted Sanskrit term"
        
        # Check for Sanskrit diacriticals
        has_sanskrit_chars = any(char in self.sanskrit_chars 
                               for char in original + transliteration)
        
        if has_sanskrit_chars:
            return True, "Contains Sanskrit diacriticals"
        
        # Check variations for contamination
        if variations:
            try:
                if isinstance(variations, str):
                    variations_list = json.loads(variations)
                else:
                    variations_list = variations
                
                if isinstance(variations_list, list):
                    # Check if any variation is English
                    english_variations = [v for v in variations_list 
                                        if v.lower() in self.reject_list]
                    if english_variations:
                        return False, f"English words in variations: {english_variations}"
            except (json.JSONDecodeError, TypeError):
                pass
        
        # For ASCII-only terms, require manual review (but don't reject automatically)
        if not has_sanskrit_chars and original.lower() not in self.whitelist:
            # Additional heuristics for Sanskrit-ness
            
            # Check if it looks like a Sanskrit word pattern
            if self._looks_like_sanskrit(original):
                return True, "Appears to be Sanskrit despite lack of diacriticals"
            
            # Conservative approach: allow but flag for review
            return True, "ASCII-only term - manual review recommended"
        
        return True, "Valid entry"
    
    def _looks_like_sanskrit(self, term: str) -> bool:
        """Heuristic check if term looks like Sanskrit."""
        if not term:
            return False
        
        term_lower = term.lower()
        
        # Common Sanskrit endings
        sanskrit_endings = ['a', 'am', 'an', 'as', 'ah', 'i', 'u', 'um', 'ya', 'va', 'ma', 'na']
        if any(term_lower.endswith(ending) for ending in sanskrit_endings):
            return True
        
        # Common Sanskrit patterns
        sanskrit_patterns = ['dh', 'bh', 'gh', 'kh', 'th', 'ph', 'ch', 'jh', 'sh', 'ny', 'ng']
        if any(pattern in term_lower for pattern in sanskrit_patterns):
            return True
        
        # Contains 'a' vowel pattern typical of Sanskrit
        if term_lower.count('a') > len(term_lower) * 0.2:  # More than 20% 'a' characters
            return True
        
        return False
    
    def validate_import_batch(self, entries: List[Dict]) -> Dict[str, List]:
        """
        Validate a batch of entries for import.
        
        Returns:
            Dictionary with 'valid', 'invalid', and 'review_needed' lists
        """
        results = {
            'valid': [],
            'invalid': [],
            'review_needed': []
        }
        
        for entry in entries:
            is_valid, reason = self.validate_entry(entry)
            
            if is_valid:
                if "manual review" in reason.lower():
                    results['review_needed'].append({
                        'entry': entry,
                        'reason': reason
                    })
                else:
                    results['valid'].append({
                        'entry': entry,
                        'reason': reason
                    })
            else:
                results['invalid'].append({
                    'entry': entry,
                    'reason': reason
                })
        
        return results
    
    def get_validation_metrics(self, batch_results: Dict[str, List]) -> Dict[str, int]:
        """
        Calculate validation metrics from batch results.
        
        Args:
            batch_results: Results from validate_import_batch
            
        Returns:
            Dictionary with validation metrics
        """
        return {
            'total_processed': len(batch_results['valid']) + len(batch_results['invalid']) + len(batch_results['review_needed']),
            'valid_count': len(batch_results['valid']),
            'invalid_count': len(batch_results['invalid']),
            'review_needed_count': len(batch_results['review_needed']),
            'validation_rate': round(len(batch_results['valid']) / max(1, len(batch_results['valid']) + len(batch_results['invalid']) + len(batch_results['review_needed'])) * 100, 2)
        }
    
    def clean_variations(self, variations: Union[str, List, None]) -> List:
        """Clean variations list by removing English contamination."""
        if not variations:
            return []
        
        try:
            if isinstance(variations, str):
                variations_list = json.loads(variations)
            else:
                variations_list = variations
            
            if not isinstance(variations_list, list):
                return []
            
            # Filter out English contamination
            clean_variations = [
                v for v in variations_list 
                if v.lower() not in self.reject_list
            ]
            
            return clean_variations
            
        except (json.JSONDecodeError, TypeError):
            return []

def validate_database_entry(original_term: str, transliteration: str = "", 
                          variations: Union[str, List, None] = None) -> Tuple[bool, str]:
    """
    Convenience function for single entry validation.
    
    Validates a single Sanskrit database entry using the comprehensive
    validation rules. This is a simplified interface for the main
    SanskritEntryValidator class.
    
    Args:
        original_term: The original Sanskrit term to validate
        transliteration: The IAST transliteration of the term
        variations: Optional list or JSON string of term variations
    
    Returns:
        Tuple of (is_valid, reason) where:
        - is_valid: Boolean indicating if entry passes validation
        - reason: String explaining the validation result
        
    Example:
        >>> is_valid, reason = validate_database_entry("dharma", "dharma")
        >>> print(f"Valid: {is_valid}, Reason: {reason}")
        Valid: True, Reason: Whitelisted Sanskrit term
    """
    validator = SanskritEntryValidator()
    entry = {
        'original_term': original_term,
        'transliteration': transliteration,
        'variations': variations
    }
    return validator.validate_entry(entry)

# Example usage and testing
if __name__ == "__main__":
    validator = SanskritEntryValidator()
    
    # Test cases
    test_cases = [
        {"original_term": "dharma", "transliteration": "dharma"},
        {"original_term": "treading", "transliteration": "treading"},
        {"original_term": "kṛṣṇa", "transliteration": "krishna"},
        {"original_term": "yoga", "transliteration": "yoga"},
        {"original_term": "treāding", "transliteration": "treāding"},
        {"original_term": "agītāted", "transliteration": "agitated"},
    ]
    
    print("🧪 VALIDATOR TESTING:")
    print("=" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        is_valid, reason = validator.validate_entry(test_case)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{i}. {test_case['original_term']} → {status}")
        print(f"   Reason: {reason}")
        print()