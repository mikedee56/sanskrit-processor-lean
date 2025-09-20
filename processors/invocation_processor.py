#!/usr/bin/env python3
"""
Invocation Processor for Sanskrit SRT Processor
Handles sacred prayers, invocations, and opening/closing mantras with proper IAST formatting
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class InvocationResult:
    """Result of invocation processing."""

    def __init__(self, processed_text: str, confidence: float, invocation_type: str,
                 corrections_made: List[str], is_invocation: bool = True):
        self.processed_text = processed_text
        self.confidence = confidence
        self.invocation_type = invocation_type
        self.corrections_made = corrections_made
        self.is_invocation = is_invocation


class InvocationProcessor:
    """
    Advanced processor for Sanskrit invocations and prayers.

    Handles sacred texts like opening prayers, mantras, and invocations with
    proper IAST diacriticals and sacred name capitalization.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize invocation processor with sacred patterns and terms."""
        self.invocation_patterns = self._load_invocation_patterns()
        self.sacred_names = self._load_sacred_names()
        self.mantra_patterns = self._load_mantra_patterns()

        # Performance cache for repeated invocations
        self.processing_cache = {}

        logger.info(f"Invocation processor initialized with {len(self.invocation_patterns)} patterns")

    def _load_invocation_patterns(self) -> Dict:
        """Load common invocation patterns and their corrections."""
        return {
            # Om-based invocations
            'om_vasudeva': {
                'pattern': r'Om\s+Vasudeva.*?Jagadguru.*?Om',
                'template': 'Om {names}, Vande, Jagadguru, Om.',
                'confidence': 0.95,
                'type': 'om_invocation'
            },

            # Prayer patterns
            'devotions_pattern': {
                'pattern': r'Devotions?\s+to\s+Lord\s+Krishna.*?(immortality|destroyer)',
                'template': 'Devotions to Lord Kṛṣṇa, the preceptor of the universe, destroyer of the forces of darkness, bestower of immortality.',
                'confidence': 0.9,
                'type': 'devotional_prayer'
            },

            # Guru invocation
            'guru_invocation': {
                'pattern': r'(Om\s+)?Gurave\s+Namah?a?',
                'template': 'Om Gurave Namaḥ',
                'confidence': 0.95,
                'type': 'guru_mantra'
            },

            # Generic Om patterns
            'om_generic': {
                'pattern': r'Om\s+[A-Za-z\s,]+Om\.?',
                'template': None,  # Custom processing required
                'confidence': 0.8,
                'type': 'om_based'
            }
        }

    def _load_sacred_names(self) -> Dict:
        """Load sacred names and their proper IAST forms."""
        return {
            # Divine names
            'vasudeva': 'Vāsudeva',
            'sutam': 'Sutam',
            'devam': 'Devam',
            'kamsa': 'Kaṃsa',
            'chanura': 'Cāṇūra',
            'mardanam': 'Mardanam',
            'devaki': 'Devakī',
            'paramanandam': 'Paramānandam',
            'trishnam': 'Tṛṣṇam',
            'vande': 'Vande',
            'jagadguru': 'Jagadguru',

            # Common divine names
            'krishna': 'Kṛṣṇa',
            'rama': 'Rāma',
            'shiva': 'Śiva',
            'brahma': 'Brahmā',
            'vishnu': 'Viṣṇu',
            'ganesha': 'Gaṇeśa',
            'hanuman': 'Hanumān',

            # Guru names
            'guru': 'Guru',
            'gurave': 'Gurave',
            'namaha': 'Namaḥ',
            'namah': 'Namaḥ'
        }

    def _load_mantra_patterns(self) -> Dict:
        """Load common mantra structures."""
        return {
            'om_pattern': r'(om|aum)(\s+.*?)(?=\.|$)',
            'namaha_pattern': r'(\w+)\s+(namaha?|namaḥ)',
            'guru_pattern': r'(guru|gurave)\s+(namaha?|namaḥ)',
            'divine_name_sequence': r'([A-Z][a-z]+),?\s*([A-Z][a-z]+),?\s*([A-Z][a-z]+)'
        }

    def process_invocation(self, text: str) -> InvocationResult:
        """
        Process text to identify and format invocations properly.

        Args:
            text: Input text that may contain invocations

        Returns:
            InvocationResult with processed text and metadata
        """
        # Check cache first
        cache_key = hash(text.strip())
        if cache_key in self.processing_cache:
            return self.processing_cache[cache_key]

        # Identify invocation type
        invocation_type = self._identify_invocation_type(text)

        if invocation_type == 'none':
            result = InvocationResult(
                processed_text=text,
                confidence=0.0,
                invocation_type='none',
                corrections_made=[],
                is_invocation=False
            )
            self.processing_cache[cache_key] = result
            return result

        # Process based on identified type
        if invocation_type == 'om_vasudeva':
            result = self._process_om_vasudeva_invocation(text)
        elif invocation_type == 'devotional_prayer':
            result = self._process_devotional_prayer(text)
        elif invocation_type == 'guru_mantra':
            result = self._process_guru_mantra(text)
        else:
            result = self._process_generic_invocation(text)

        # Cache result
        self.processing_cache[cache_key] = result
        return result

    def _identify_invocation_type(self, text: str) -> str:
        """Identify the type of invocation in the text."""
        text_lower = text.lower()

        # Check for Om Vasudeva pattern
        if 'om' in text_lower and 'vasudeva' in text_lower and 'jagadguru' in text_lower:
            return 'om_vasudeva'

        # Check for devotional prayer
        if 'devotions' in text_lower and 'krishna' in text_lower:
            return 'devotional_prayer'

        # Check for guru mantra
        if ('guru' in text_lower or 'gurave' in text_lower) and 'namah' in text_lower:
            return 'guru_mantra'

        # Check for generic Om-based invocation
        if text_lower.startswith('om ') and len(text.split()) >= 3:
            return 'om_based'

        return 'none'

    def _process_om_vasudeva_invocation(self, text: str) -> InvocationResult:
        """Process the specific Om Vasudeva invocation pattern."""
        corrections_made = []

        # Extract the divine names sequence
        # Pattern: Om Vasudeva, Sutam, Devam, Kamsa, Chanura, Mardanam, Devaki, Paramanandam, Trishnam, Vande, Jagadguru, Om.

        words = text.replace(',', ' ').replace('.', ' ').split()
        processed_words = []

        for word in words:
            word_clean = word.strip().lower()
            if word_clean in self.sacred_names:
                correct_form = self.sacred_names[word_clean]
                if word != correct_form:
                    corrections_made.append(f"{word} → {correct_form}")
                processed_words.append(correct_form)
            elif word_clean == 'om':
                processed_words.append('Om')
            else:
                processed_words.append(word)

        # Reconstruct with proper formatting
        processed_text = f"Om {', '.join(processed_words[1:-1])}, Om."

        return InvocationResult(
            processed_text=processed_text,
            confidence=0.95,
            invocation_type='om_vasudeva',
            corrections_made=corrections_made
        )

    def _process_devotional_prayer(self, text: str) -> InvocationResult:
        """Process devotional prayer to Krishna."""
        corrections_made = []

        # Standard devotional prayer pattern
        original_text = text
        processed_text = text

        # Replace Krishna with proper form
        if 'Krishna' in text:
            processed_text = processed_text.replace('Krishna', 'Kṛṣṇa')
            corrections_made.append("Krishna → Kṛṣṇa")
        elif 'krishna' in text.lower():
            processed_text = re.sub(r'\bkrishna\b', 'Kṛṣṇa', processed_text, flags=re.IGNORECASE)
            corrections_made.append("krishna → Kṛṣṇa")

        # Ensure proper capitalization for "Lord"
        processed_text = re.sub(r'\blord\b', 'Lord', processed_text, flags=re.IGNORECASE)

        return InvocationResult(
            processed_text=processed_text,
            confidence=0.9,
            invocation_type='devotional_prayer',
            corrections_made=corrections_made
        )

    def _process_guru_mantra(self, text: str) -> InvocationResult:
        """Process guru mantras like Om Gurave Namaha."""
        corrections_made = []
        processed_text = text

        # Standard guru mantra corrections
        replacements = {
            r'\bgurave\s+namaha?\b': 'Gurave Namaḥ',
            r'\bguru\s+namaha?\b': 'Guru Namaḥ',
            r'\bom\b': 'Om'
        }

        for pattern, replacement in replacements.items():
            if re.search(pattern, processed_text, re.IGNORECASE):
                old_text = processed_text
                processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
                if old_text != processed_text:
                    corrections_made.append(f"guru mantra formatting applied")

        return InvocationResult(
            processed_text=processed_text,
            confidence=0.95,
            invocation_type='guru_mantra',
            corrections_made=corrections_made
        )

    def _process_generic_invocation(self, text: str) -> InvocationResult:
        """Process generic invocations with sacred name corrections."""
        corrections_made = []
        processed_text = text

        # Apply sacred name corrections
        words = text.split()
        processed_words = []

        for word in words:
            # Clean word for lookup (remove punctuation but preserve it)
            clean_word = re.sub(r'[^\w]', '', word).lower()
            punctuation = re.sub(r'[\w]', '', word)

            if clean_word in self.sacred_names:
                correct_form = self.sacred_names[clean_word]
                new_word = correct_form + punctuation
                if word != new_word:
                    corrections_made.append(f"{word} → {new_word}")
                processed_words.append(new_word)
            else:
                processed_words.append(word)

        processed_text = ' '.join(processed_words)

        return InvocationResult(
            processed_text=processed_text,
            confidence=0.8,
            invocation_type='generic_invocation',
            corrections_made=corrections_made
        )

    def is_likely_invocation(self, text: str) -> bool:
        """
        Quick check if text is likely an invocation.

        Args:
            text: Text to check

        Returns:
            True if text appears to be an invocation
        """
        text_lower = text.lower()

        # Check for common invocation indicators
        invocation_indicators = [
            'om ',
            'aum ',
            'namaha',
            'namaḥ',
            'vande',
            'devotions to',
            'guru',
            'gurave'
        ]

        # Check for divine name sequences (multiple divine names)
        divine_names_found = sum(1 for name in self.sacred_names.keys() if name in text_lower)

        # Check for prayer patterns
        prayer_patterns = [
            r'om\s+\w+.*?(om|namaha?)',
            r'devotions?\s+to\s+lord',
            r'(guru|gurave)\s+namaha?'
        ]

        # Must have invocation indicators OR multiple divine names OR prayer patterns
        has_indicators = any(indicator in text_lower for indicator in invocation_indicators)
        has_multiple_divine_names = divine_names_found >= 3
        has_prayer_pattern = any(re.search(pattern, text_lower) for pattern in prayer_patterns)

        return has_indicators or has_multiple_divine_names or has_prayer_pattern

    def get_processing_stats(self) -> Dict:
        """Get statistics about invocation processing."""
        return {
            'cache_size': len(self.processing_cache),
            'sacred_names_count': len(self.sacred_names),
            'invocation_patterns_count': len(self.invocation_patterns),
            'mantra_patterns_count': len(self.mantra_patterns)
        }

    def clear_cache(self):
        """Clear the processing cache."""
        self.processing_cache.clear()
        logger.debug("Invocation processor cache cleared")


def test_invocation_processor():
    """Test function for the invocation processor."""
    processor = InvocationProcessor()

    test_cases = [
        "Om Vasudeva, Sutam, Devam, Kamsa, Chanura, Mardanam, Devaki, Paramanandam, Trishnam, Vande, Jagadguru, Om.",
        "Devotions to Lord Krishna, the preceptor of the universe, destroyer of the forces of darkness, bestower of immortality.",
        "Om Gurave Namaha",
        "Some regular English text that is not an invocation"
    ]

    for test_text in test_cases:
        result = processor.process_invocation(test_text)
        print(f"\nInput: {test_text}")
        print(f"Is invocation: {result.is_invocation}")
        print(f"Type: {result.invocation_type}")
        print(f"Confidence: {result.confidence}")
        print(f"Output: {result.processed_text}")
        print(f"Corrections: {result.corrections_made}")


if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.DEBUG)
    test_invocation_processor()