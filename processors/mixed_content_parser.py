#!/usr/bin/env python3
"""
Mixed Content Parser for Sanskrit SRT Processor
Handles Sanskrit terms embedded within English commentary with surgical precision
"""

import re
import logging
from typing import List, Dict, Tuple, Optional, NamedTuple
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class EmbeddedTerm(NamedTuple):
    """Represents a Sanskrit term found embedded in English text."""
    original: str
    corrected: str
    start_pos: int
    end_pos: int
    confidence: float
    context: str
    term_type: str


class MixedContentResult:
    """Result of mixed content parsing."""

    def __init__(self, processed_text: str, embedded_terms: List[EmbeddedTerm],
                 confidence: float, processing_mode: str):
        self.processed_text = processed_text
        self.embedded_terms = embedded_terms
        self.confidence = confidence
        self.processing_mode = processing_mode
        self.corrections_count = len(embedded_terms)


class MixedContentParser:
    """
    Advanced parser for mixed Sanskrit-English content.

    Identifies Sanskrit terms embedded within English commentary and applies
    surgical corrections while preserving the surrounding English structure.
    """

    def __init__(self, embedded_terms_path: Optional[str] = None,
                 scripture_titles_path: Optional[str] = None):
        """Initialize mixed content parser with term databases."""
        self.embedded_terms = self._load_embedded_terms(embedded_terms_path)
        self.scripture_titles = self._load_scripture_titles(scripture_titles_path)

        # Build lookup structures for performance
        self._build_lookup_structures()

        # Cache for processed content
        self.processing_cache = {}

        logger.info(f"Mixed content parser initialized with {len(self.embedded_terms)} embedded terms "
                   f"and {len(self.scripture_titles)} scripture titles")

    def _load_embedded_terms(self, terms_path: Optional[str]) -> Dict:
        """Load embedded Sanskrit terms database."""
        if terms_path is None:
            terms_path = Path(__file__).parent.parent / 'lexicons' / 'embedded_sanskrit.yaml'

        try:
            with open(terms_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return {entry['term']: entry for entry in data.get('entries', [])}
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Could not load embedded terms from {terms_path}: {e}")
            return {}

    def _load_scripture_titles(self, titles_path: Optional[str]) -> Dict:
        """Load scripture titles database."""
        if titles_path is None:
            titles_path = Path(__file__).parent.parent / 'lexicons' / 'scripture_titles.yaml'

        try:
            with open(titles_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return {entry['title']: entry for entry in data.get('entries', [])}
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Could not load scripture titles from {titles_path}: {e}")
            return {}

    def _build_lookup_structures(self):
        """Build optimized lookup structures for fast matching."""
        # Create variation-to-term mapping for embedded terms
        self.variation_to_term = {}
        for term_key, term_data in self.embedded_terms.items():
            # Add the main term
            self.variation_to_term[term_key.lower()] = term_data

            # Add all variations
            for variation in term_data.get('variations', []):
                self.variation_to_term[variation.lower()] = term_data

        # Create variation-to-title mapping for scripture titles
        self.variation_to_title = {}
        for title_key, title_data in self.scripture_titles.items():
            # Add the main title
            self.variation_to_title[title_key.lower()] = title_data

            # Add all variations
            for variation in title_data.get('variations', []):
                self.variation_to_title[variation.lower()] = title_data

        # Compile regex patterns for efficient matching
        self._compile_patterns()

        logger.debug(f"Built lookup structures: {len(self.variation_to_term)} term variations, "
                    f"{len(self.variation_to_title)} title variations")

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Pattern for Sanskrit terms in English context
        all_variations = list(self.variation_to_term.keys()) + list(self.variation_to_title.keys())

        # Sort by length (longest first) to avoid partial matches
        all_variations.sort(key=len, reverse=True)

        # Escape special regex characters and build pattern
        escaped_variations = [re.escape(var) for var in all_variations]
        self.term_pattern = re.compile(
            r'\b(' + '|'.join(escaped_variations) + r')\b',
            re.IGNORECASE
        )

        # Pattern for corrupted Sanskrit in English sentences
        self.corrupted_sanskrit_pattern = re.compile(
            r'\b(evam?\s+pravartitam?|mokha[mn]?\s+pārtha|aghāyur?\s+indriya)\b',
            re.IGNORECASE
        )

        logger.debug("Compiled regex patterns for mixed content matching")

    def parse_mixed_content(self, text: str) -> MixedContentResult:
        """
        Parse mixed content to identify and correct embedded Sanskrit terms.

        Args:
            text: Input text with potential mixed Sanskrit-English content

        Returns:
            MixedContentResult with processed text and corrections
        """
        # Check cache
        cache_key = hash(text.strip())
        if cache_key in self.processing_cache:
            return self.processing_cache[cache_key]

        # Determine processing mode based on content analysis
        processing_mode = self._determine_processing_mode(text)

        embedded_terms = []
        processed_text = text

        if processing_mode == 'none':
            result = MixedContentResult(text, [], 0.0, 'none')
            self.processing_cache[cache_key] = result
            return result

        # Process based on mode
        if processing_mode == 'embedded_terms':
            embedded_terms, processed_text = self._process_embedded_terms(text)
        elif processing_mode == 'corrupted_sanskrit':
            embedded_terms, processed_text = self._process_corrupted_sanskrit(text)
        elif processing_mode == 'scripture_titles':
            embedded_terms, processed_text = self._process_scripture_titles(text)
        elif processing_mode == 'comprehensive':
            # Apply all processing methods
            embedded_terms1, processed_text = self._process_embedded_terms(processed_text)
            embedded_terms2, processed_text = self._process_corrupted_sanskrit(processed_text)
            embedded_terms3, processed_text = self._process_scripture_titles(processed_text)
            embedded_terms = embedded_terms1 + embedded_terms2 + embedded_terms3

        # Calculate overall confidence
        confidence = self._calculate_confidence(embedded_terms, text)

        result = MixedContentResult(processed_text, embedded_terms, confidence, processing_mode)
        self.processing_cache[cache_key] = result
        return result

    def _determine_processing_mode(self, text: str) -> str:
        """Determine the appropriate processing mode for the text."""
        text_lower = text.lower()

        # Check for corrupted Sanskrit patterns
        has_corrupted_sanskrit = bool(self.corrupted_sanskrit_pattern.search(text))

        # Check for embedded terms
        has_embedded_terms = bool(self.term_pattern.search(text))

        # Check for scripture titles
        has_scripture_titles = any(title in text_lower for title in self.variation_to_title.keys())

        # Check if this looks like English commentary
        english_indicators = ['the ', 'and ', 'is ', 'are ', 'that ', 'which ', 'to ', 'in ', 'of ', 'with ', 'from ', 'at ', 'by ']
        english_score = sum(1 for indicator in english_indicators if indicator in text_lower)

        if english_score < 2:
            return 'none'  # Doesn't look like English commentary

        # Determine mode based on what we found
        if has_corrupted_sanskrit and has_embedded_terms:
            return 'comprehensive'
        elif has_corrupted_sanskrit:
            return 'corrupted_sanskrit'
        elif has_scripture_titles:
            return 'scripture_titles'
        elif has_embedded_terms:
            return 'embedded_terms'
        else:
            return 'none'

    def _process_embedded_terms(self, text: str) -> Tuple[List[EmbeddedTerm], str]:
        """Process embedded Sanskrit terms in English text."""
        embedded_terms = []
        processed_text = text

        # Find all matches
        for match in self.term_pattern.finditer(text):
            original_term = match.group(1)
            term_data = self.variation_to_term.get(original_term.lower())

            if term_data is None:
                continue

            # Check context patterns if available
            if not self._check_context_patterns(text, match, term_data):
                continue

            # Create embedded term
            corrected_term = term_data['correct']
            embedded_term = EmbeddedTerm(
                original=original_term,
                corrected=corrected_term,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=term_data.get('confidence', 0.8),
                context=self._extract_context(text, match),
                term_type='embedded_term'
            )

            embedded_terms.append(embedded_term)

        # Apply corrections (from end to start to preserve positions)
        embedded_terms.sort(key=lambda x: x.start_pos, reverse=True)
        for term in embedded_terms:
            processed_text = (processed_text[:term.start_pos] +
                            term.corrected +
                            processed_text[term.end_pos:])

        return embedded_terms, processed_text

    def _process_corrupted_sanskrit(self, text: str) -> Tuple[List[EmbeddedTerm], str]:
        """Process corrupted Sanskrit within English sentences."""
        embedded_terms = []
        processed_text = text

        # Common corrupted Sanskrit patterns and their corrections
        corrupted_patterns = {
            r'evam?\s+pravartitam?\s+chakram?\s+nānu?\s+vartaya?\s+tīraya?\s+aghāyur?\s+indriyā?\s+rāmo?\s+mokhaṁ?\s+pārtha\s+sa\s+jīvati':
                'evaṃ pravartitaṃ cakraṃ nānuvartayatīha yaḥ . aghāyurindriyārāmo moghaṃ pārtha sa jīvati',

            r'evam\s+pravartitam\s+chakram\s+nānu\s+vartaya\s+tīraya':
                'evaṃ pravartitaṃ cakraṃ nānuvartayatīha yaḥ',

            r'mokhaṁ?\s+pārtha\s+sa\s+jīvati':
                'moghaṃ pārtha sa jīvati'
        }

        for pattern, correction in corrupted_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                embedded_term = EmbeddedTerm(
                    original=match.group(0),
                    corrected=correction,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.9,
                    context=self._extract_context(text, match),
                    term_type='corrupted_sanskrit'
                )
                embedded_terms.append(embedded_term)

        # Apply corrections
        embedded_terms.sort(key=lambda x: x.start_pos, reverse=True)
        for term in embedded_terms:
            processed_text = (processed_text[:term.start_pos] +
                            term.corrected +
                            processed_text[term.end_pos:])

        return embedded_terms, processed_text

    def _process_scripture_titles(self, text: str) -> Tuple[List[EmbeddedTerm], str]:
        """Process scripture titles for proper formatting."""
        embedded_terms = []
        processed_text = text

        # Look for scripture title patterns
        for title_var, title_data in self.variation_to_title.items():
            pattern = re.compile(r'\b' + re.escape(title_var) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                correct_title = title_data['transliteration']

                embedded_term = EmbeddedTerm(
                    original=match.group(0),
                    corrected=correct_title,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=title_data.get('confidence', 0.9),
                    context=self._extract_context(text, match),
                    term_type='scripture_title'
                )
                embedded_terms.append(embedded_term)

        # Apply corrections
        embedded_terms.sort(key=lambda x: x.start_pos, reverse=True)
        for term in embedded_terms:
            processed_text = (processed_text[:term.start_pos] +
                            term.corrected +
                            processed_text[term.end_pos:])

        return embedded_terms, processed_text

    def _check_context_patterns(self, text: str, match, term_data: Dict) -> bool:
        """Check if the term appears in appropriate context."""
        context_patterns = term_data.get('context_patterns', [])
        if not context_patterns:
            return True  # No context restrictions

        # Extract context around the match
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end].lower()

        # Check if any pattern matches
        return any(pattern.lower() in context for pattern in context_patterns)

    def _extract_context(self, text: str, match) -> str:
        """Extract context around a match for debugging/logging."""
        start = max(0, match.start() - 20)
        end = min(len(text), match.end() + 20)
        return text[start:end]

    def _calculate_confidence(self, embedded_terms: List[EmbeddedTerm], original_text: str) -> float:
        """Calculate overall confidence in the processing result."""
        if not embedded_terms:
            return 0.0

        # Average confidence of all corrections
        avg_confidence = sum(term.confidence for term in embedded_terms) / len(embedded_terms)

        # Adjust based on the proportion of text that was corrected
        text_length = len(original_text)
        corrected_chars = sum(len(term.original) for term in embedded_terms)
        correction_ratio = corrected_chars / text_length if text_length > 0 else 0

        # Higher confidence if corrections are focused (not too much of the text changed)
        if correction_ratio > 0.5:
            avg_confidence *= 0.8  # Reduce confidence if too much changed
        elif correction_ratio < 0.1:
            avg_confidence *= 1.1  # Increase confidence for focused changes

        return min(avg_confidence, 1.0)

    def is_mixed_content(self, text: str) -> bool:
        """
        Quick check if text contains mixed Sanskrit-English content.

        Args:
            text: Text to check

        Returns:
            True if text appears to contain mixed content
        """
        # Check for English sentence structure
        english_indicators = ['the ', 'and ', 'is ', 'are ', 'that ', 'which ', 'to ', 'in ', 'of ', 'with ', 'from ', 'at ', 'by ']
        has_english = any(indicator in text.lower() for indicator in english_indicators)

        if not has_english:
            return False

        # Check for Sanskrit terms or patterns
        has_sanskrit_terms = bool(self.term_pattern.search(text))
        has_corrupted_sanskrit = bool(self.corrupted_sanskrit_pattern.search(text))

        return has_sanskrit_terms or has_corrupted_sanskrit

    def get_processing_stats(self) -> Dict:
        """Get statistics about mixed content processing."""
        return {
            'cache_size': len(self.processing_cache),
            'embedded_terms_count': len(self.embedded_terms),
            'scripture_titles_count': len(self.scripture_titles),
            'variation_mappings': len(self.variation_to_term) + len(self.variation_to_title)
        }

    def clear_cache(self):
        """Clear the processing cache."""
        self.processing_cache.clear()
        logger.debug("Mixed content parser cache cleared")


def test_mixed_content_parser():
    """Test function for the mixed content parser."""
    parser = MixedContentParser()

    test_cases = [
        "The verse number is 16. evam pravartitam chakram nānu vartaya tīraya aghāyur indriyā rāmo mokhaṁ pārtha sa jīvati",
        "The wheels set in motion, that has been explained to you before, following gada pari naya, which means we hammer it again and again.",
        "Shrimad Bhagavad Gita, in Chapter 3, that is entitled Karma Yoga, Yoga of Action.",
        "The first thing they require is āhār, food.",
        "Samskaras are like seeds that grow into karmas.",
        "According to Shankaracharya and great personalities in a very short time.",
        "This is just regular English text with no Sanskrit terms."
    ]

    for test_text in test_cases:
        result = parser.parse_mixed_content(test_text)
        print(f"\nInput: {test_text}")
        print(f"Mode: {result.processing_mode}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Corrections: {result.corrections_count}")
        print(f"Output: {result.processed_text}")
        if result.embedded_terms:
            print("Terms found:")
            for term in result.embedded_terms:
                print(f"  {term.original} → {term.corrected} (confidence: {term.confidence})")


if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.DEBUG)
    test_mixed_content_parser()