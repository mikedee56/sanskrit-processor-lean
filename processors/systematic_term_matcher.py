"""
Systematic Term Matcher - The Solution to Manual Corrections
Uses scripture databases and intelligent matching to catch all Sanskrit terms automatically.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TermMatch:
    """Represents a matched Sanskrit term with correction."""
    original: str
    corrected: str
    confidence: float
    match_type: str  # 'exact', 'phonetic', 'compound', 'scripture'
    source: str      # Where this term came from

class SystematicTermMatcher:
    """
    Systematic term matcher that eliminates the need for manual corrections.
    Combines scripture databases, compound processing, and intelligent matching.
    """
    
    def __init__(self, lexicon_dir: Path = None):
        self.lexicon_dir = Path(lexicon_dir or "lexicons")
        self.scripture_terms = {}
        self.compound_patterns = {}
        self.phonetic_cache = {}
        
        # Load all available term sources
        self._load_scripture_corrections()
        self._build_compound_patterns()
        self._create_intelligent_patterns()
        
        logger.info(f"Systematic term matcher initialized with {len(self.scripture_terms)} terms")
    
    def _load_scripture_corrections(self):
        """Load the enhanced corrections with scripture terms."""
        corrections_file = self.lexicon_dir / "corrections_with_scripture.yaml"
        if corrections_file.exists():
            with open(corrections_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            for entry in data.get('entries', []):
                original = entry['original_term']
                self.scripture_terms[original.lower()] = entry
                
                # Also index by variations
                for variation in entry.get('variations', []):
                    if isinstance(variation, str):  # Skip non-string variations
                        self.scripture_terms[variation.lower()] = entry
                    
            logger.info(f"Loaded {len(data.get('entries', []))} correction entries")
        else:
            logger.warning(f"Scripture corrections file not found: {corrections_file}")
    
    def _build_compound_patterns(self):
        """Build intelligent compound word patterns."""
        # Common Sanskrit compound patterns
        self.compound_patterns = {
            # Number + noun patterns
            r'\b(sapta|saptam)\s+(bhoomi\w+|bhumi\w+)': lambda m: f"sapta bhūmikāḥ",
            r'\b(pancha|panca)\s+(\w*kosha?\w*)': lambda m: f"pañca kośa",
            r'\b(catur|chatur)\s+(\w*varga?\w*)': lambda m: f"catur varga",
            
            # Title + name patterns  
            r'\b(sri|shri)\s+(vasi\w+|vashi\w+)': lambda m: "Śrī Vaśiṣṭha",
            r'\b(yoga)\s*(vasi\w+|bashi\w*)': lambda m: "Yogavāsiṣṭha",
            r'\b(bhagavad)\s*(gita|geeta)': lambda m: "Bhagavad Gītā",
            r'\b(maha)\s*(purusha?\w*)': lambda m: "mahāpuruṣa",
            
            # Compound technical terms
            r'\b(jivan|jeeva?n?)\s*(mukta?\w*)': lambda m: "jīvanmukta",
            r'\b(raga|raag)\s*(dvesha?|dvesh)': lambda m: "rāga-dveṣa", 
            r'\b(aham)\s*(brahma\w*)': lambda m: "ahaṁ brahmāsmi",
            r'\b(padaartha|padartha)\s*(bhavan\w*)': lambda m: "padārtha-bhāvanā",
            
            # ASR compound errors
            r'\btanva\s*manasi\b': lambda m: "tanumānasi",
            r'\basam\s*sakti\b': lambda m: "asaṁsakti",
            r'\bsattva\s*patti\b': lambda m: "sattvāpatti",
            r'\bshubh\s*iccha\b': lambda m: "śubhecchā"
        }
    
    def _create_intelligent_patterns(self):
        """Create patterns that learn from common ASR mistakes."""
        # Common ASR transformations we need to reverse
        self.asr_reversals = {
            # Consonant confusions
            'sh': 'ś', 'ch': 'c', 'th': 'th', 'dh': 'dh', 'ph': 'ph', 'bh': 'bh',
            # Vowel length confusions  
            'aa': 'ā', 'ii': 'ī', 'uu': 'ū', 'ee': 'e', 'oo': 'o',
            # Nasal confusions
            'ng': 'ṅ', 'nk': 'ṅk', 'nc': 'ñc', 'nj': 'ñj',
            # Retroflex confusions
            'rn': 'rṇ', 'rt': 'rṭ', 'rd': 'rḍ', 'rl': 'rḷ', 'rs': 'rṣ'
        }
    
    def find_all_corrections(self, text: str) -> List[TermMatch]:
        """Find all Sanskrit term corrections in text systematically."""
        corrections = []
        
        # 1. Exact scripture term matches
        corrections.extend(self._find_scripture_matches(text))
        
        # 2. Compound word matches
        corrections.extend(self._find_compound_matches(text))
        
        # 3. Phonetic similarity matches
        corrections.extend(self._find_phonetic_matches(text))
        
        # 4. Intelligent ASR correction matches
        corrections.extend(self._find_asr_corrections(text))
        
        # Remove duplicates and sort by confidence
        unique_corrections = self._deduplicate_corrections(corrections)
        return sorted(unique_corrections, key=lambda x: x.confidence, reverse=True)
    
    def _find_scripture_matches(self, text: str) -> List[TermMatch]:
        """Find exact matches in scripture database."""
        matches = []
        words = re.findall(r'\b\w+\b', text.lower())
        
        for word in words:
            if word in self.scripture_terms:
                entry = self.scripture_terms[word]
                corrected = entry['transliteration']
                if corrected.lower() != word:
                    matches.append(TermMatch(
                        original=word,
                        corrected=corrected,
                        confidence=entry.get('confidence', 0.9),
                        match_type='scripture',
                        source=entry.get('category', 'unknown')
                    ))
        
        return matches
    
    def _find_compound_matches(self, text: str) -> List[TermMatch]:
        """Find compound word pattern matches."""
        matches = []
        
        for pattern, correction_func in self.compound_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                original = match.group()
                try:
                    corrected = correction_func(match)
                    if corrected != original:
                        matches.append(TermMatch(
                            original=original,
                            corrected=corrected,
                            confidence=0.85,
                            match_type='compound',
                            source='pattern'
                        ))
                except Exception as e:
                    logger.debug(f"Compound pattern error: {e}")
        
        return matches
    
    def _find_phonetic_matches(self, text: str) -> List[TermMatch]:
        """Find phonetically similar terms."""
        matches = []
        words = re.findall(r'\b\w{4,}\b', text)  # Only longer words
        
        for word in words:
            word_lower = word.lower()
            if word_lower in self.phonetic_cache:
                continue
                
            # Check for phonetic similarity with scripture terms
            best_match = None
            best_score = 0.0
            
            for script_term, entry in self.scripture_terms.items():
                if abs(len(script_term) - len(word_lower)) > 3:  # Skip very different lengths
                    continue
                    
                similarity = self._calculate_phonetic_similarity(word_lower, script_term)
                if similarity > best_score and similarity >= 0.8:
                    best_score = similarity
                    best_match = entry
            
            if best_match:
                matches.append(TermMatch(
                    original=word,
                    corrected=best_match['transliteration'],
                    confidence=best_score * 0.9,  # Slightly lower than exact matches
                    match_type='phonetic',
                    source='similarity'
                ))
                self.phonetic_cache[word_lower] = best_match
        
        return matches
    
    def _find_asr_corrections(self, text: str) -> List[TermMatch]:
        """Find intelligent ASR corrections."""
        matches = []
        
        # Look for common ASR errors and reverse them
        for word_match in re.finditer(r'\b\w{4,}\b', text):
            word = word_match.group()
            word_lower = word.lower()
            
            # Try reversing common ASR transformations
            corrected_word = word_lower
            for asr_error, correct in self.asr_reversals.items():
                if asr_error in corrected_word:
                    corrected_word = corrected_word.replace(asr_error, correct)
            
            # If we made a change, check if the corrected version exists in our database
            if corrected_word != word_lower and corrected_word in self.scripture_terms:
                entry = self.scripture_terms[corrected_word]
                matches.append(TermMatch(
                    original=word,
                    corrected=entry['transliteration'],
                    confidence=0.75,
                    match_type='asr_correction',
                    source='asr_reversal'
                ))
        
        return matches
    
    def _calculate_phonetic_similarity(self, word1: str, word2: str) -> float:
        """Calculate phonetic similarity between two words."""
        # Simple but effective similarity measure
        if word1 == word2:
            return 1.0
        
        # Length penalty
        len_diff = abs(len(word1) - len(word2))
        if len_diff > 3:
            return 0.0
        
        # Character-level similarity with Sanskrit-aware substitutions
        similar_chars = {
            ('s', 'ś', 'ṣ'), ('n', 'ṇ', 'ṅ', 'ñ'), ('t', 'ṭ'), ('d', 'ḍ'),
            ('a', 'ā'), ('i', 'ī'), ('u', 'ū'), ('r', 'ṛ', 'ṝ'),
            ('l', 'ḷ', 'ḹ'), ('e', 'ē'), ('o', 'ō'), ('m', 'ṃ', 'ṁ')
        }
        
        # Create substitution groups lookup
        substitutions = {}
        for group in similar_chars:
            for char in group:
                substitutions[char] = group
        
        # Calculate edit distance with Sanskrit-aware substitutions
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i-1] == word2[j-1]:
                    cost = 0
                elif (word1[i-1] in substitutions and word2[j-1] in substitutions and
                      substitutions[word1[i-1]] == substitutions[word2[j-1]]):
                    cost = 0.3  # Low cost for Sanskrit-similar characters
                else:
                    cost = 1
                
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # deletion
                    dp[i][j-1] + 1,      # insertion  
                    dp[i-1][j-1] + cost  # substitution
                )
        
        max_len = max(len(word1), len(word2))
        similarity = 1 - (dp[m][n] / max_len)
        return max(0, similarity)
    
    def _deduplicate_corrections(self, corrections: List[TermMatch]) -> List[TermMatch]:
        """Remove duplicate corrections, keeping the highest confidence."""
        seen = {}
        for correction in corrections:
            key = correction.original.lower()
            if key not in seen or correction.confidence > seen[key].confidence:
                seen[key] = correction
        return list(seen.values())
    
    def apply_corrections(self, text: str) -> Tuple[str, List[TermMatch]]:
        """Apply all corrections to text and return corrected text."""
        corrections = self.find_all_corrections(text)
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

if __name__ == "__main__":
    matcher = SystematicTermMatcher()
    
    # Test with the user's examples
    test_text = """
    Utpati Prakarana, Sapta Bhoomikaas, Yogabashi, Shivashistha, 
    Shubh Iccha, Bhagawan, Jeevan Mukta, Tanvamanasi, asam sakti,
    Radha Dvesha, Sattvapatti, Manushyatvam, Mumukshutvam
    """
    
    print("=== SYSTEMATIC TERM MATCHING TEST ===")
    corrected_text, corrections = matcher.apply_corrections(test_text)
    
    print(f"Original: {test_text.strip()}")
    print(f"Corrected: {corrected_text.strip()}")
    print(f"\nCorrections applied: {len(corrections)}")
    
    for correction in corrections:
        print(f"  {correction.original} → {correction.corrected} "
              f"({correction.confidence:.2f}, {correction.match_type})")