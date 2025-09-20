#!/usr/bin/env python3
"""
Surgical Text Editor for Sanskrit SRT Processor
Provides precise text editing capabilities for mixed content with surgical precision
"""

import re
import logging
from typing import List, Dict, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EditType(Enum):
    """Types of surgical edits that can be performed."""
    REPLACE = "replace"
    INSERT = "insert"
    DELETE = "delete"
    TRANSFORM = "transform"


@dataclass
class SurgicalEdit:
    """Represents a precise edit operation."""
    edit_type: EditType
    start_pos: int
    end_pos: int
    original_text: str
    replacement_text: str
    confidence: float
    reason: str


class EditResult:
    """Result of surgical editing operation."""

    def __init__(self, edited_text: str, edits_applied: List[SurgicalEdit],
                 success: bool, confidence: float):
        self.edited_text = edited_text
        self.edits_applied = edits_applied
        self.success = success
        self.confidence = confidence
        self.edit_count = len(edits_applied)


class SurgicalEditor:
    """
    Precision text editor for Sanskrit content.

    Performs surgical edits on mixed Sanskrit-English content, preserving
    context while making targeted corrections with high precision.
    """

    def __init__(self):
        """Initialize surgical editor with edit patterns and rules."""
        self.edit_patterns = self._load_edit_patterns()
        self.preservation_rules = self._load_preservation_rules()

        # Cache for compiled patterns
        self.compiled_patterns = {}
        self._compile_patterns()

        logger.info("Surgical editor initialized with precision editing capabilities")

    def _load_edit_patterns(self) -> Dict:
        """Load surgical edit patterns for common corrections."""
        return {
            # Corrupted Sanskrit verse patterns
            'corrupted_verse_3_16': {
                'pattern': r'(verse\s+number\s+is\s+16\.\s+)?evam?\s+pravartitam?\s+chakram?\s+nānu?\s+vartaya?\s+tīraya?\s+aghāyur?\s+indriyā?\s+rāmo?\s+mokhaṁ?\s+pārtha\s+sa\s+jīvati',
                'replacement': lambda m: self._fix_verse_3_16(m),
                'confidence': 0.95,
                'preserve_prefix': True,
                'reason': 'Bhagavad Gītā 3.16 correction'
            },

            # Mixed Sanskrit-English verse patterns
            'mixed_verse_pattern': {
                'pattern': r'(The\s+verse\s+number\s+is\s+\d+\.\s+)([a-zA-Z\s]+(?:pārtha|mokhaṁ|karma|dharma)[a-zA-Z\s]*)',
                'replacement': lambda m: m.group(1) + self._clean_sanskrit_portion(m.group(2)),
                'confidence': 0.8,
                'preserve_prefix': True,
                'reason': 'Mixed verse content cleanup'
            },

            # Sanskrit terms in English context
            'embedded_sanskrit_terms': {
                'pattern': r'\b(samskaras?|gada\s+pari\s+naya|prarabdha\s+karma|Shankaracharya)\b',
                'replacement': lambda m: self._correct_embedded_term(m.group(1)),
                'confidence': 0.9,
                'preserve_prefix': False,
                'reason': 'Embedded Sanskrit term correction'
            },

            # Scripture title corrections
            'scripture_titles': {
                'pattern': r'\b(Shrimad\s+Bhagavad\s+Gita|Bhagavad\s+Gita)\b',
                'replacement': lambda m: self._correct_scripture_title(m.group(1)),
                'confidence': 0.95,
                'preserve_prefix': False,
                'reason': 'Scripture title formatting'
            },

            # Divine name corrections
            'divine_names': {
                'pattern': r'\b(Krishna|Arjuna|Shankaracharya)\b',
                'replacement': lambda m: self._correct_divine_name(m.group(1)),
                'confidence': 0.9,
                'preserve_prefix': False,
                'reason': 'Divine name IAST formatting'
            }
        }

    def _load_preservation_rules(self) -> Dict:
        """Load rules for what should be preserved during editing."""
        return {
            # Don't edit within these contexts
            'preserve_contexts': [
                r'http[s]?://',  # URLs
                r'\w+@\w+\.\w+',  # Email addresses
                r'\d{2}:\d{2}:\d{2}',  # Timestamps
                r'-->[<\d:,\s]+',  # SRT timestamp arrows
            ],

            # Preserve English sentence structure indicators
            'english_structure_markers': [
                'the ', 'and ', 'is ', 'are ', 'was ', 'were ',
                'which ', 'that ', 'this ', 'these ', 'those ',
                'a ', 'an ', 'to ', 'of ', 'in ', 'on ', 'at '
            ],

            # Don't break these patterns
            'protected_patterns': [
                r'\d+\.',  # Numbered lists
                r'Chapter\s+\d+',  # Chapter references
                r'verse\s+\d+',  # Verse numbers
                r'[A-Z][a-z]+\s+[A-Z][a-z]+',  # Proper names (two words)
            ]
        }

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        for pattern_name, pattern_data in self.edit_patterns.items():
            self.compiled_patterns[pattern_name] = re.compile(
                pattern_data['pattern'],
                re.IGNORECASE
            )
        logger.debug(f"Compiled {len(self.compiled_patterns)} surgical edit patterns")

    def perform_surgical_edit(self, text: str, edit_mode: str = 'conservative') -> EditResult:
        """
        Perform surgical editing on text with specified precision level.

        Args:
            text: Input text to edit
            edit_mode: 'conservative', 'moderate', or 'aggressive'

        Returns:
            EditResult with edited text and applied operations
        """
        edits_applied = []
        current_text = text

        # Adjust confidence thresholds based on mode
        confidence_threshold = {
            'conservative': 0.95,
            'moderate': 0.85,
            'aggressive': 0.7
        }.get(edit_mode, 0.85)

        # Check if text should be edited at all
        if not self._should_edit_text(text):
            return EditResult(text, [], True, 0.0)

        # Apply each edit pattern
        for pattern_name, pattern_data in self.edit_patterns.items():
            if pattern_data['confidence'] < confidence_threshold:
                continue

            compiled_pattern = self.compiled_patterns[pattern_name]
            matches = list(compiled_pattern.finditer(current_text))

            # Process matches from end to start to preserve positions
            for match in reversed(matches):
                if not self._is_safe_to_edit(current_text, match.start(), match.end()):
                    continue

                # Apply the edit
                edit = self._apply_pattern_edit(current_text, match, pattern_data, pattern_name)
                if edit:
                    current_text = edit.edited_text
                    edits_applied.append(edit.edit_operation)

        # Calculate overall confidence
        overall_confidence = self._calculate_edit_confidence(edits_applied, text)

        return EditResult(
            edited_text=current_text,
            edits_applied=edits_applied,
            success=len(edits_applied) > 0,
            confidence=overall_confidence
        )

    def _should_edit_text(self, text: str) -> bool:
        """Determine if text is a candidate for surgical editing."""
        # Check for mixed content indicators
        has_english = any(marker in text.lower() for marker in
                         self.preservation_rules['english_structure_markers'])

        # Check for Sanskrit content that might need correction
        sanskrit_indicators = [
            'evam', 'pravartitam', 'chakram', 'pārtha', 'mokhaṁ',
            'samskaras', 'gada pari naya', 'Shankaracharya',
            'Bhagavad Gita', 'Krishna', 'Arjuna'
        ]

        has_sanskrit = any(indicator in text for indicator in sanskrit_indicators)

        # Only edit if we have both English structure and Sanskrit content
        return has_english and has_sanskrit

    def _is_safe_to_edit(self, text: str, start_pos: int, end_pos: int) -> bool:
        """Check if it's safe to edit the specified text region."""
        # Check preservation contexts
        for preserve_pattern in self.preservation_rules['preserve_contexts']:
            if re.search(preserve_pattern, text[max(0, start_pos-10):end_pos+10]):
                return False

        # Check protected patterns
        region = text[start_pos:end_pos]
        for protected_pattern in self.preservation_rules['protected_patterns']:
            if re.search(protected_pattern, region):
                return False

        return True

    def _apply_pattern_edit(self, text: str, match, pattern_data: Dict, pattern_name: str):
        """Apply a specific pattern edit to the text."""
        try:
            # Get replacement text
            replacement_func = pattern_data['replacement']
            if callable(replacement_func):
                replacement_text = replacement_func(match)
            else:
                replacement_text = replacement_func

            if replacement_text == match.group(0):
                return None  # No change needed

            # Create the edit operation
            edit_operation = SurgicalEdit(
                edit_type=EditType.REPLACE,
                start_pos=match.start(),
                end_pos=match.end(),
                original_text=match.group(0),
                replacement_text=replacement_text,
                confidence=pattern_data['confidence'],
                reason=pattern_data['reason']
            )

            # Apply the edit
            edited_text = (text[:match.start()] +
                          replacement_text +
                          text[match.end():])

            return type('EditResult', (), {
                'edited_text': edited_text,
                'edit_operation': edit_operation
            })()

        except Exception as e:
            logger.warning(f"Failed to apply edit pattern {pattern_name}: {e}")
            return None

    def _fix_verse_3_16(self, match) -> str:
        """Fix the corrupted Bhagavad Gītā 3.16 verse."""
        original = match.group(0)

        # Check if it has the "verse number is 16" prefix
        if original.lower().startswith('verse number is 16'):
            prefix = "The verse number is 16. "
        else:
            prefix = ""

        # The correct verse
        correct_verse = "evaṃ pravartitaṃ cakraṃ nānuvartayatīha yaḥ . aghāyurindriyārāmo moghaṃ pārtha sa jīvati ||3-16||"

        return prefix + correct_verse

    def _clean_sanskrit_portion(self, sanskrit_portion: str) -> str:
        """Clean up a Sanskrit portion within mixed content."""
        # This is a simplified cleanup - in a full implementation,
        # this would use the systematic term matcher
        common_fixes = {
            'evam': 'evaṃ',
            'pravartitam': 'pravartitaṃ',
            'chakram': 'cakraṃ',
            'nānu': 'nānu',
            'vartaya': 'vartaya',
            'tīraya': 'tīha',
            'aghāyur': 'aghāyur',
            'indriyā': 'indriyā',
            'rāmo': 'rāmo',
            'mokhaṁ': 'moghaṃ'
        }

        cleaned = sanskrit_portion
        for wrong, correct in common_fixes.items():
            cleaned = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, cleaned, flags=re.IGNORECASE)

        return cleaned

    def _correct_embedded_term(self, term: str) -> str:
        """Correct embedded Sanskrit terms."""
        corrections = {
            'samskaras': 'saṃskāras',
            'samskara': 'saṃskāra',
            'gada pari naya': 'gadā parinaya',
            'prarabdha karma': 'prārabdha karma',
            'Shankaracharya': 'Śaṅkarācārya'
        }

        return corrections.get(term.lower(), term)

    def _correct_scripture_title(self, title: str) -> str:
        """Correct scripture titles."""
        title_lower = title.lower()

        if 'shrimad bhagavad gita' in title_lower:
            return 'Śrīmad Bhagavad Gītā'
        elif 'bhagavad gita' in title_lower:
            return 'Bhagavad Gītā'

        return title

    def _correct_divine_name(self, name: str) -> str:
        """Correct divine names with proper IAST."""
        corrections = {
            'krishna': 'Kṛṣṇa',
            'arjuna': 'Arjuna',  # Already correct
            'shankaracharya': 'Śaṅkarācārya'
        }

        return corrections.get(name.lower(), name)

    def _calculate_edit_confidence(self, edits: List[SurgicalEdit], original_text: str) -> float:
        """Calculate overall confidence in the editing result."""
        if not edits:
            return 0.0

        # Average confidence of all edits
        avg_confidence = sum(edit.confidence for edit in edits) / len(edits)

        # Adjust based on the proportion of text changed
        total_chars_changed = sum(len(edit.original_text) for edit in edits)
        change_ratio = total_chars_changed / len(original_text) if original_text else 0

        # Penalty for too many changes (less confident)
        if change_ratio > 0.3:
            avg_confidence *= 0.8
        elif change_ratio < 0.05:
            avg_confidence *= 1.1

        return min(avg_confidence, 1.0)

    def get_edit_statistics(self) -> Dict:
        """Get statistics about the surgical editor."""
        return {
            'edit_patterns_count': len(self.edit_patterns),
            'compiled_patterns_count': len(self.compiled_patterns),
            'preservation_rules_count': len(self.preservation_rules),
            'supported_edit_types': [edit_type.value for edit_type in EditType]
        }


def test_surgical_editor():
    """Test function for the surgical editor."""
    editor = SurgicalEditor()

    test_cases = [
        "The verse number is 16. evam pravartitam chakram nānu vartaya tīraya aghāyur indriyā rāmo mokhaṁ pārtha sa jīvati",
        "The wheels set in motion, that has been explained to you before, following gada pari naya, which means we hammer it again and again.",
        "Shrimad Bhagavad Gita, in Chapter 3, that is entitled Karma Yoga, Yoga of Action.",
        "Samskaras are like seeds that create prarabdha karma.",
        "According to Shankaracharya, Krishna teaches Arjuna about dharma.",
        "This is just regular English text with no Sanskrit issues."
    ]

    for test_text in test_cases:
        for mode in ['conservative', 'moderate', 'aggressive']:
            result = editor.perform_surgical_edit(test_text, mode)
            print(f"\nMode: {mode}")
            print(f"Input: {test_text}")
            print(f"Output: {result.edited_text}")
            print(f"Edits: {result.edit_count}, Confidence: {result.confidence:.2f}")
            if result.edits_applied:
                for edit in result.edits_applied:
                    print(f"  {edit.original_text} → {edit.replacement_text} ({edit.reason})")


if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.DEBUG)
    test_surgical_editor()