"""
ASR Pattern Matcher - Specialized recognition system for common ASR transcription errors.
Handles phonetic substitutions and Sanskrit-specific ASR error patterns.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ASRPattern:
    """Represents an ASR error pattern with correction."""
    error_pattern: str
    correction: str
    confidence: float
    pattern_type: str  # 'phonetic', 'compound', 'aspiration', 'nasal'

@dataclass
class ASRCorrection:
    """Represents a corrected ASR error."""
    original: str
    corrected: str
    confidence: float
    pattern_applied: str
    transformation_type: str

class ASRPatternMatcher:
    """
    ASR-specific pattern matcher for common speech recognition errors.
    Handles Sanskrit-specific phonetic confusions and compound word splitting.
    """
    
    def __init__(self, enable_compound_splitting: bool = True):
        """
        Initialize ASR pattern matcher with configurable options.
        
        Args:
            enable_compound_splitting: Whether to attempt compound word splitting
        """
        self.enable_compound_splitting = enable_compound_splitting
        
        # Common ASR phonetic error patterns
        self.phonetic_patterns = {
            # Aspirated consonant confusions (common in ASR)
            'ph': ASRPattern('ph', 'f', 0.9, 'aspiration'),
            'th': ASRPattern('th', 't', 0.9, 'aspiration'), 
            'bh': ASRPattern('bh', 'b', 0.9, 'aspiration'),
            'dh': ASRPattern('dh', 'd', 0.9, 'aspiration'),
            'kh': ASRPattern('kh', 'k', 0.9, 'aspiration'),
            'gh': ASRPattern('gh', 'g', 0.9, 'aspiration'),
            'ch': ASRPattern('ch', 'c', 0.9, 'aspiration'),
            'jh': ASRPattern('jh', 'j', 0.9, 'aspiration'),
            
            # Sibilant confusions
            'sh': ASRPattern('sh', 'ś', 0.85, 'phonetic'),
            'ss': ASRPattern('ss', 'ś', 0.8, 'phonetic'),
            
            # Vowel length confusions (ASR often misses length)
            'aa': ASRPattern('aa', 'ā', 0.95, 'phonetic'),
            'ii': ASRPattern('ii', 'ī', 0.95, 'phonetic'), 
            'uu': ASRPattern('uu', 'ū', 0.95, 'phonetic'),
            'ee': ASRPattern('ee', 'ē', 0.9, 'phonetic'),
            'oo': ASRPattern('oo', 'ō', 0.9, 'phonetic'),
            
            # Nasal confusions
            'ng': ASRPattern('ng', 'ṅ', 0.8, 'nasal'),
            'nk': ASRPattern('nk', 'ṅk', 0.8, 'nasal'),
            'nc': ASRPattern('nc', 'ñc', 0.8, 'nasal'),
            'nj': ASRPattern('nj', 'ñj', 0.8, 'nasal'),
            
            # Retroflex confusions
            'rn': ASRPattern('rn', 'rṇ', 0.8, 'phonetic'),
            'rt': ASRPattern('rt', 'rṭ', 0.8, 'phonetic'),
            'rd': ASRPattern('rd', 'rḍ', 0.8, 'phonetic'),
            'rl': ASRPattern('rl', 'rḷ', 0.8, 'phonetic'),
            'rs': ASRPattern('rs', 'rṣ', 0.8, 'phonetic'),
            
            # Common Sanskrit-specific confusions
            'v': ASRPattern('v', 'w', 0.7, 'phonetic'),  # vasistha → wasistha
            'w': ASRPattern('w', 'v', 0.7, 'phonetic'),  # reverse
            'gya': ASRPattern('gya', 'ya', 0.75, 'phonetic'),  # gyani → yani
        }
        
        # Compound word splitting patterns (common ASR errors)
        self.compound_patterns = {
            # Common compound separations that ASR incorrectly joins or splits
            r'\btanva\s*manasi\b': ('tanumānasi', 0.9),
            r'\basam\s*sakti\b': ('asaṁsakti', 0.9),
            r'\bsattva\s*patti\b': ('sattvāpatti', 0.9),
            r'\bshubh\s*iccha\b': ('śubhecchā', 0.9),
            # DISABLED: These patterns incorrectly match "Yoga Vasistha Utpatti Prakarana"
            # r'\byoga\s*bashi\b': ('yogavāsiṣṭha', 0.85),
            # r'\byoga\s*vashi\b': ('yogavāsiṣṭha', 0.85),
            # r'\bsri\s*vasi\w*\b': ('śrī vaśiṣṭha', 0.85),  # \w* wildcard too aggressive
            # r'\bshri\s*vasi\w*\b': ('śrī vaśiṣṭha', 0.85), # \w* wildcard too aggressive
            r'\bjivan\s*mukta?\w*\b': ('jīvanmukta', 0.85),
            r'\bmaha\s*purusha?\w*\b': ('mahāpuruṣa', 0.85),
            r'\bbhagavad\s*gita\b': ('bhagavad gītā', 0.95),
            r'\braga\s*dvesha?\w*\b': ('rāga-dveṣa', 0.85),
            r'\baham\s*brahma\w*\b': ('ahaṁ brahmāsmi', 0.9),
        }
        
        # Sanskrit phonological rules that ASR commonly violates
        self.phonological_corrections = {
            # DISABLED: These sandhi rules incorrectly smash separate words together
            # r'\b(\w+)o\s+a(\w+)\b': r'\1ava\2',  # o + a → ava
            # r'\b(\w+)a\s+i(\w+)\b': r'\1e\2',    # a + i → e
            # r'\b(\w+)a\s+u(\w+)\b': r'\1o\2',    # a + u → o - CORRUPTS "Vasistha Utpatti"
        }
        
        logger.info(f"ASR pattern matcher initialized with {len(self.phonetic_patterns)} phonetic patterns, "
                   f"{len(self.compound_patterns)} compound patterns")
    
    def find_asr_corrections(self, text: str) -> List[ASRCorrection]:
        """
        Find ASR correction opportunities in text.
        
        Args:
            text: Input text to analyze for ASR errors
            
        Returns:
            List of ASR corrections found
        """
        corrections = []
        
        # 1. Apply English ASR pattern corrections (for mixed content)
        corrections.extend(self._apply_english_asr_corrections(text))
        
        # 2. Apply phonetic pattern corrections
        corrections.extend(self._apply_phonetic_corrections(text))
        
        # 3. Apply compound word corrections  
        if self.enable_compound_splitting:
            corrections.extend(self._apply_compound_corrections(text))
        
        # 4. Apply phonological rule corrections
        corrections.extend(self._apply_phonological_corrections(text))
        
        # Remove duplicates and sort by confidence
        unique_corrections = self._deduplicate_corrections(corrections)
        return sorted(unique_corrections, key=lambda x: x.confidence, reverse=True)
    
    def _apply_english_asr_corrections(self, text: str) -> List[ASRCorrection]:
        """Apply English ASR pattern corrections for mixed content."""
        corrections = []
        
        # Direct pattern matching for common English ASR errors
        english_corrections = [
            # Common ASR transcription errors
            (r'\btat\'s\b', "That's", 0.95),
            (r'\bte\s+eśential\b', 'the essential', 0.95),  # Exact match for "te eśential"
            (r'\bte\s+essential\b', 'the essential', 0.95),  # Also match without diacritics
            (r'\bte\s+secret\b', 'the secret', 0.95),
            (r'\bteacing\b', 'teaching', 0.95),
            (r'\bteh\b', 'the', 0.9),
            (r'\band\s+and\b', 'and', 0.95),
            (r'\bof\s+of\b', 'of', 0.95),
            (r'\bto\s+to\b', 'to', 0.95),
            (r'\bis\s+is\b', 'is', 0.95),
        ]
        
        for pattern, replacement, confidence in english_corrections:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                original = match.group()
                corrected = replacement
                
                if original.lower() != corrected.lower():
                    corrections.append(ASRCorrection(
                        original=original,
                        corrected=corrected,
                        confidence=confidence,
                        pattern_applied=pattern,
                        transformation_type='english_asr'
                    ))
        
        return corrections

    def _apply_phonetic_corrections(self, text: str) -> List[ASRCorrection]:
        """Apply phonetic pattern corrections - only to Sanskrit-looking words."""
        corrections = []
        words = re.findall(r'\b\w+\b', text)
        
        # Common English words to NEVER apply Sanskrit phonetic corrections to
        english_words = {
            'that', 'this', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'you', 'your', 'he', 'she', 'it', 'his', 'her', 'we', 'our', 'they', 'them', 'their',
            'i', 'my', 'mine', 'me', 'will', 'would', 'could', 'should', 'can', 'may', 'might',
            'do', 'does', 'did', 'done', 'make', 'made', 'get', 'got', 'go', 'went', 'come', 'came',
            'see', 'saw', 'know', 'knew', 'think', 'thought', 'say', 'said', 'tell', 'told',
            'teaching', 'teacher', 'student', 'class', 'school', 'book', 'read', 'write'
        }
        
        for word in words:
            word_lower = word.lower()
            
            # Skip English words - don't apply Sanskrit phonetic patterns to them
            if word_lower in english_words:
                continue
                
            # Skip words that are clearly English (have common English patterns)
            if any(pattern in word_lower for pattern in ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion']):
                continue
            
            # Try each phonetic pattern only on Sanskrit-looking words
            for pattern_str, asr_pattern in self.phonetic_patterns.items():
                if pattern_str in word_lower:
                    corrected = word_lower.replace(pattern_str, asr_pattern.correction)
                    if corrected != word_lower:
                        corrections.append(ASRCorrection(
                            original=word,
                            corrected=corrected,
                            confidence=asr_pattern.confidence * 0.7,  # Lower confidence for automatic corrections
                            pattern_applied=pattern_str,
                            transformation_type=asr_pattern.pattern_type
                        ))
        
        return corrections
    
    def _apply_compound_corrections(self, text: str) -> List[ASRCorrection]:
        """Apply compound word pattern corrections."""
        corrections = []
        
        for pattern, (correction, confidence) in self.compound_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                original = match.group()
                corrections.append(ASRCorrection(
                    original=original,
                    corrected=correction,
                    confidence=confidence * 0.9,  # High confidence for known compound patterns
                    pattern_applied=pattern,
                    transformation_type='compound'
                ))
        
        return corrections
    
    def _apply_phonological_corrections(self, text: str) -> List[ASRCorrection]:
        """Apply Sanskrit phonological rule corrections."""
        corrections = []
        
        for pattern, replacement in self.phonological_corrections.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                original = match.group()
                corrected = re.sub(pattern, replacement, original, flags=re.IGNORECASE)
                if corrected != original:
                    corrections.append(ASRCorrection(
                        original=original,
                        corrected=corrected,
                        confidence=0.7,  # Medium confidence for phonological rules
                        pattern_applied=pattern,
                        transformation_type='phonological'
                    ))
        
        return corrections
    
    def _deduplicate_corrections(self, corrections: List[ASRCorrection]) -> List[ASRCorrection]:
        """Remove duplicate corrections, keeping highest confidence."""
        seen = {}
        for correction in corrections:
            key = correction.original.lower()
            if key not in seen or correction.confidence > seen[key].confidence:
                seen[key] = correction
        return list(seen.values())
    
    def apply_corrections(self, text: str) -> Tuple[str, List[ASRCorrection]]:
        """
        Apply ASR corrections to text.
        
        Args:
            text: Input text to correct
            
        Returns:
            Tuple of (corrected_text, corrections_applied)
        """
        corrections = self.find_asr_corrections(text)
        applied_corrections = []
        result_text = text
        
        # Sort by original text length (longest first) to avoid partial replacements
        corrections.sort(key=lambda x: len(x.original), reverse=True)
        
        for correction in corrections:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(correction.original) + r'\b'
            if re.search(pattern, result_text, re.IGNORECASE):
                result_text = re.sub(pattern, correction.corrected, result_text, flags=re.IGNORECASE)
                applied_corrections.append(correction)
        
        return result_text, applied_corrections
    
    def suggest_corrections(self, word: str) -> List[ASRCorrection]:
        """
        Suggest ASR corrections for a single word.
        
        Args:
            word: Word to analyze for ASR errors
            
        Returns:
            List of suggested corrections
        """
        return self.find_asr_corrections(word)

if __name__ == "__main__":
    # Test ASR pattern matcher
    asr_matcher = ASRPatternMatcher()
    
    # Test cases from the story
    test_texts = [
        "yogabashi teaches about shivashistha",
        "tanva manasi and shubh iccha are important",
        "aham brahma asmi is from bhagavad gita", 
        "jivan mukta achieves maha purusha state",
        "raga dvesha causes asam sakti problems"
    ]
    
    print("=== ASR PATTERN MATCHER TEST ===")
    for text in test_texts:
        corrected_text, corrections = asr_matcher.apply_corrections(text)
        print(f"Original: {text}")
        print(f"Corrected: {corrected_text}")
        if corrections:
            print("Corrections applied:")
            for correction in corrections:
                print(f"  {correction.original} → {correction.corrected} "
                      f"({correction.confidence:.2f}, {correction.transformation_type})")
        print()