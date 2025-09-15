#!/usr/bin/env python3
"""
Capitalization Preservation System for Sanskrit Processing
Handles proper capitalization of divine names, scripture titles, and proper nouns.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CapitalizationPreserver:
    """Handles capitalization preservation based on lexicon flags"""

    def __init__(self, config: Dict):
        self.preservation_enabled = config.get('preserve_capitalization', True)
        self.category_rules = config.get('capitalization_categories', {
            'divine_name': True,
            'scripture_title': True,
            'scripture': True,  # Support legacy category name
            'deity': True,      # Support legacy category name
            'place_name': True,
            'concept': False
        })
        # Performance optimization: Cache category lookups
        self._category_cache = {}
        logger.debug(f"CapitalizationPreserver initialized: enabled={self.preservation_enabled}")

    def apply_capitalization(self, original: str, corrected: str, entry: Dict) -> str:
        """
        Apply appropriate capitalization based on lexicon entry

        Args:
            original: Original input text
            corrected: Corrected Sanskrit text  
            entry: Lexicon entry with preservation rules

        Returns:
            Properly capitalized corrected text
        
        Raises:
            TypeError: If inputs are not strings or entry is not dict
            ValueError: If required fields are missing from entry
        """
        # Enhanced input validation
        if not isinstance(original, (str, type(None))):
            raise TypeError(f"original must be string or None, got {type(original)}")
        if not isinstance(corrected, (str, type(None))):
            raise TypeError(f"corrected must be string or None, got {type(corrected)}")
        if not isinstance(entry, dict):
            raise TypeError(f"entry must be dict, got {type(entry)}")
        
        # Handle None inputs gracefully
        original = original or ""
        corrected = corrected or ""
        
        if not self.preservation_enabled:
            return corrected.capitalize() if corrected else ""

        # Check explicit preservation flag
        preserve_flag = entry.get('preserve_capitalization', False)
        if preserve_flag:
            return self._preserve_original_case(original, corrected, entry)

        # Optimized category checking with caching
        if self._should_preserve_by_category(entry):
            return self._preserve_original_case(original, corrected, entry)

        # Default: standard capitalization
        return corrected.capitalize() if corrected else ""

    def _should_preserve_by_category(self, entry: Dict) -> bool:
        """
        Optimized category checking with caching
        
        Args:
            entry: Lexicon entry to check
            
        Returns:
            True if any category requires preservation
        """
        # Create cache key from entry categories
        category = entry.get('category', '')
        categories = entry.get('categories', [])
        all_categories = tuple(categories if categories else [category] if category else [])
        
        # Use cached result if available
        if all_categories in self._category_cache:
            return self._category_cache[all_categories]
        
        # Check categories and cache result
        result = any(self.category_rules.get(cat, False) for cat in all_categories)
        self._category_cache[all_categories] = result
        return result

    def _is_sanskrit_term(self, word: str) -> bool:
        """
        Detect if a word is likely Sanskrit/divine term or English
        
        Args:
            word: Word to analyze
            
        Returns:
            True if likely Sanskrit, False if likely English
        """
        if not word:
            return False
        
        # Check for Sanskrit diacritics
        sanskrit_chars = {'ā', 'ī', 'ū', 'ṛ', 'ḷ', 'ṃ', 'ḥ', 'ṅ', 'ñ', 'ṭ', 'ḍ', 'ṇ', 'ś', 'ṣ'}
        if any(char in word.lower() for char in sanskrit_chars):
            return True
        
        # Common English words that should not be capitalized
        english_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must',
            'a', 'an', 'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our',
            'their', 'some', 'any', 'all', 'each', 'every', 'no', 'not', 'only', 'just', 'even',
            'speaks', 'teaches', 'says', 'tells', 'explains', 'describes', 'contains', 'includes',
            'chapter', 'verse', 'text', 'book', 'wisdom', 'knowledge', 'truth', 'path', 'way'
        }
        
        if word.lower() in english_words:
            return False
        
        # Sanskrit/divine name patterns (common terms that should be capitalized)
        sanskrit_patterns = {
            'krishna', 'rama', 'shiva', 'vishnu', 'lakshmi', 'saraswati', 'ganesha', 'hanuman',
            'bhagavan', 'bhagawan', 'devi', 'mata', 'ji', 'sri', 'sree', 'shri',
            'yoga', 'dharma', 'karma', 'moksha', 'moksa', 'jnana', 'gyana', 'bhakti', 'seva',
            'guru', 'swami', 'maharaj', 'ji', 'das', 'dasa',
            'gita', 'upanishad', 'veda', 'vedanta', 'sutra', 'shastra'
        }
        
        if word.lower() in sanskrit_patterns:
            return True
        
        # Default: if unsure, treat as English to be conservative
        return False

    def _preserve_original_case(self, original: str, corrected: str, entry: Dict) -> str:
        """
        Preserve capitalization pattern from original to corrected text

        Enhanced to handle:
        - Title case: "Lakshmi Devi" → "Lakṣmī Devī"
        - All caps: "KRISHNA" → "KṚṢṆA"
        - Mixed case: "lakSHmi" → "Lakṣmī" (intelligently)
        - Unicode handling: Proper case preservation for Sanskrit diacritics
        - Word boundary edge cases: Multiple spaces, punctuation
        - Whitespace preservation: Maintains original spacing patterns
        """
        if not original or not corrected:
            return corrected or ""

        # Handle unicode properly for Sanskrit text
        try:
            # Preserve whitespace by using regex split that maintains separators
            import re
            
            # Split while keeping separators (spaces, tabs, etc.)
            original_parts = re.split(r'(\s+)', original)
            corrected_words = corrected.split()
            
            # Extract just the words (non-whitespace parts)
            original_words = [part for part in original_parts if not re.match(r'^\s+$', part) and part]
            
        except (AttributeError, UnicodeError, ImportError) as e:
            logger.warning(f"Advanced text splitting error: {e}, falling back to simple split")
            # Fallback to simple splitting
            original_words = original.split()
            corrected_words = corrected.split()
            original_parts = None

        if len(original_words) != len(corrected_words):
            # Word count mismatch - use intelligent mapping
            return self._intelligent_case_mapping(original, corrected)

        # Apply case preservation to each word
        result_words = []
        for orig_word, corr_word in zip(original_words, corrected_words):
            try:
                # Strip punctuation for case analysis but preserve it in output
                import re
                clean_orig = re.sub(r'^[^\w]+|[^\w]+$', '', orig_word, flags=re.UNICODE)
                
                if not clean_orig:
                    # If word is all punctuation, keep corrected as-is
                    result_words.append(corr_word)
                    continue
                
                if clean_orig.isupper():
                    result_words.append(corr_word.upper())
                elif clean_orig.istitle():
                    result_words.append(corr_word.capitalize())
                elif clean_orig.islower():
                    # Special handling for scripture titles and divine names
                    if self._should_preserve_by_category(entry) or self._is_sanskrit_term(corr_word):
                        result_words.append(corr_word.capitalize())
                    else:
                        result_words.append(corr_word.lower())
                else:
                    # Mixed case - apply intelligent preservation using clean word
                    result_words.append(self._preserve_mixed_case(clean_orig, corr_word))
            except (AttributeError, UnicodeError) as e:
                logger.warning(f"Case preservation error for '{orig_word}' -> '{corr_word}': {e}")
                # Fallback to safe capitalization
                result_words.append(corr_word.capitalize() if corr_word else "")

        # If we have original_parts with whitespace info, reconstruct with original spacing
        if original_parts:
            try:
                import re
                result = ""
                word_index = 0
                for part in original_parts:
                    if re.match(r'^\s+$', part):
                        # This is whitespace, preserve it
                        result += part
                    elif part:
                        # This is a word, use the processed version
                        if word_index < len(result_words):
                            result += result_words[word_index]
                            word_index += 1
                        else:
                            result += part
                return result
            except Exception as e:
                logger.warning(f"Whitespace reconstruction error: {e}, falling back to simple join")
        
        # Fallback: simple space joining
        return ' '.join(result_words)

    def _intelligent_case_mapping(self, original: str, corrected: str) -> str:
        """
        Enhanced intelligent case mapping for word boundary mismatches
        
        Args:
            original: Original text with reference case pattern
            corrected: Corrected text to apply pattern to
            
        Returns:
            Corrected text with intelligent case mapping applied
        """
        if not original or not corrected:
            return corrected or ""
            
        try:
            # If original is title case, make corrected title case
            if original.istitle() or any(word.istitle() for word in original.split()):
                return corrected.title()
            elif original.isupper():
                return corrected.upper()
            else:
                # For divine names, prefer proper capitalization even for lowercase input
                return corrected.title()
        except (AttributeError, UnicodeError) as e:
            logger.warning(f"Intelligent case mapping error: {e}")
            return corrected.capitalize() if corrected else ""

    def _preserve_mixed_case(self, original: str, corrected: str) -> str:
        """
        Enhanced mixed case preservation with better heuristics
        
        Args:
            original: Original word with mixed case pattern
            corrected: Corrected word to apply pattern to
            
        Returns:
            Corrected word with intelligent mixed case applied
        """
        if not original or not corrected:
            return corrected or ""
            
        try:
            # Priority 1: For Sanskrit/divine terms, apply intelligent capitalization
            if self._is_sanskrit_term(corrected):
                # Divine names and Sanskrit terms should be properly capitalized
                return corrected.capitalize()
            
            # Priority 2: For non-Sanskrit terms, preserve case pattern of first character
            if original and original[0].islower():
                return corrected.lower()
            elif original and original[0].isupper():
                return corrected.capitalize()
            else:
                return corrected.capitalize()
        except (AttributeError, UnicodeError, IndexError) as e:
            logger.warning(f"Mixed case preservation error: {e}")
            return corrected.capitalize() if corrected else ""

    def should_preserve_capitalization(self, entry: Dict) -> bool:
        """
        Check if an entry should have its capitalization preserved

        Args:
            entry: Lexicon entry to check

        Returns:
            True if capitalization should be preserved
            
        Raises:
            TypeError: If entry is not a dictionary
        """
        if not isinstance(entry, dict):
            raise TypeError(f"entry must be dict, got {type(entry)}")
            
        if not self.preservation_enabled:
            return False

        # Check explicit flag
        if entry.get('preserve_capitalization', False):
            return True

        # Use optimized category checking
        return self._should_preserve_by_category(entry)

    def get_performance_stats(self) -> Dict[str, int]:
        """
        Get performance statistics for monitoring
        
        Returns:
            Dictionary with cache hit rates and other metrics
        """
        return {
            'category_cache_size': len(self._category_cache),
            'preservation_enabled': self.preservation_enabled,
            'category_rules_count': len(self.category_rules)
        }


def apply_correction_with_capitalization(word: str, correction_entry: Dict,
                                       preserver: CapitalizationPreserver) -> str:
    """
    Apply correction while preserving appropriate capitalization

    Args:
        word: Original word to correct
        correction_entry: Lexicon entry with correction info
        preserver: CapitalizationPreserver instance

    Returns:
        Corrected word with appropriate capitalization
    """
    corrected = correction_entry.get('transliteration', word)

    # Apply capitalization preservation
    final_corrected = preserver.apply_capitalization(word, corrected, correction_entry)

    return final_corrected