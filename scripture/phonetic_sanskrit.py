"""
Sanskrit Phonetic Matching Module
Specialized phonetic algorithms for matching garbled Sanskrit transcriptions to proper verses

This module provides:
1. Sanskrit-specific Soundex for consonant clusters
2. Sanskrit Double Metaphone for phonetic similarity  
3. Weighted Levenshtein distance considering Sanskrit phonetics
4. N-gram matching for partial verse recognition
"""

import re
from typing import List, Tuple, Optional, Set
from difflib import SequenceMatcher

class SanskritPhoneticMatcher:
    """
    Core phonetic matching engine for Sanskrit text.
    Handles common transcription errors and phonetic variations.
    """
    
    def __init__(self):
        """Initialize with Sanskrit phonetic mapping tables."""
        # Sanskrit consonant cluster mappings
        self.consonant_clusters = {
            'ksh': 'x', 'gn': 'n', 'tn': 'n', 'dh': 'd', 'th': 't',
            'bh': 'b', 'ph': 'p', 'gh': 'g', 'kh': 'k', 'ch': 'c',
            'jh': 'j', 'nh': 'n', 'rh': 'r', 'sh': 's', 'zh': 's'
        }
        
        # Vowel reduction mappings for phonetic matching
        self.vowel_mappings = {
            'aa': 'a', 'ii': 'i', 'uu': 'u', 'ee': 'e', 'oo': 'o',
            'ai': 'e', 'au': 'o', 'ṛ': 'r', 'ṝ': 'r', 'ḷ': 'l'
        }
        
        # Common transcription variations
        self.variation_patterns = {
            r'v(?=[aeiou])': 'w',  # v -> w before vowels
            r'(?<=[aeiou])v': 'w', # v -> w after vowels  
            r'c(?=h)': 'ch',       # c -> ch 
            r'j(?=h)': 'jh',       # j -> jh
            r'[ñṅṇñ]': 'n',       # All nasals -> n
            r'[ṭḍ]': 't',          # Retroflex -> dental
            r'ś': 's',             # Sibilants -> s
            r'ṣ': 's'              # All sibilants -> s
        }
        
        # Sanskrit sound weights for Levenshtein
        self.sound_weights = self._build_sound_weights()
        
    def _build_sound_weights(self) -> dict:
        """Build phonetic similarity weights for Sanskrit sounds."""
        weights = {}
        
        # Similar consonants (lower cost for substitution)
        similar_groups = [
            ['k', 'g', 'kh', 'gh'],      # Velar stops
            ['c', 'j', 'ch', 'jh'],      # Palatal stops  
            ['t', 'd', 'th', 'dh'],      # Dental stops
            ['p', 'b', 'ph', 'bh'],      # Labial stops
            ['s', 'sh', 'ś', 'ṣ'],       # Sibilants
            ['n', 'ṅ', 'ñ', 'ṇ', 'm'],  # Nasals
            ['r', 'l'],                   # Liquids
            ['a', 'ā', 'aa'],            # Similar vowels
            ['i', 'ī', 'ii', 'e'],       
            ['u', 'ū', 'uu', 'o']
        ]
        
        for group in similar_groups:
            for char1 in group:
                for char2 in group:
                    if char1 != char2:
                        weights[(char1, char2)] = 0.3  # Low substitution cost
        
        return weights
    
    def sanskrit_soundex(self, word: str) -> str:
        """
        Generate Sanskrit-specific soundex code.
        Handles Sanskrit consonant clusters and phonetic variations.
        """
        if not word:
            return ""
            
        word = word.lower().strip()
        
        # Step 1: Apply consonant cluster reductions
        for cluster, replacement in self.consonant_clusters.items():
            word = word.replace(cluster, replacement)
        
        # Step 2: Apply vowel reductions
        for vowel, replacement in self.vowel_mappings.items():
            word = word.replace(vowel, replacement)
            
        # Step 3: Apply variation patterns
        for pattern, replacement in self.variation_patterns.items():
            word = re.sub(pattern, replacement, word)
        
        # Step 4: Standard soundex processing
        if not word:
            return ""
        
        # Keep first letter
        soundex = word[0].upper()
        word = word[1:]
        
        # Remove vowels and similar consonants
        word = re.sub(r'[aeiouhwy]', '', word)
        
        # Convert to soundex digits
        soundex_map = {
            'bfpv': '1', 'cgjkqsxz': '2', 'dt': '3',
            'l': '4', 'mn': '5', 'r': '6'
        }
        
        for chars, digit in soundex_map.items():
            for char in chars:
                word = word.replace(char, digit)
        
        # Remove duplicates and pad/truncate to 4 characters
        prev_char = ''
        result = soundex
        
        for char in word:
            if char != prev_char and char.isdigit():
                result += char
                prev_char = char
        
        # Pad or truncate to 4 characters
        result = (result + '000')[:4]
        
        return result
    
    def sanskrit_metaphone(self, word: str) -> str:
        """
        Sanskrit adaptation of Double Metaphone algorithm.
        Focuses on Sanskrit phonetic patterns.
        """
        if not word:
            return ""
        
        word = word.lower().strip()
        metaphone = ""
        
        # Handle Sanskrit-specific patterns
        patterns = [
            (r'^ksh', 'KS'),   # Initial ksha
            (r'ksh', 'KS'),    # Ksha everywhere
            (r'gn', 'N'),      # Gna -> N
            (r'[dt]h', 'T'),   # Aspirated stops
            (r'[pb]h', 'P'),   # Aspirated labials
            (r'[kg]h', 'K'),   # Aspirated velars
            (r'[cj]h', 'C'),   # Aspirated palatals
            (r'[ṛṝ]', 'R'),    # Vocalic R
            (r'[ḷḹ]', 'L'),    # Vocalic L
            (r'[ṅñṇ]', 'N'),  # All nasals
            (r'[śṣ]', 'S'),    # All sibilants
            (r'ā', 'A'),       # Long vowels
            (r'[īē]', 'I'),
            (r'[ūō]', 'U')
        ]
        
        for pattern, replacement in patterns:
            word = re.sub(pattern, replacement, word)
        
        # Convert remaining characters
        for char in word.upper():
            if char.isalpha():
                metaphone += char
        
        return metaphone[:6]  # Limit length
    
    def weighted_levenshtein(self, s1: str, s2: str) -> float:
        """
        Calculate Levenshtein distance with Sanskrit phonetic weights.
        Returns normalized distance (0.0 = identical, 1.0 = completely different).
        """
        if not s1 or not s2:
            return 1.0 if s1 != s2 else 0.0
        
        s1, s2 = s1.lower(), s2.lower()
        
        # Create matrix
        matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
        
        # Initialize first row and column
        for i in range(len(s1) + 1):
            matrix[i][0] = i
        for j in range(len(s2) + 1):
            matrix[0][j] = j
        
        # Fill matrix with weighted costs
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                if s1[i-1] == s2[j-1]:
                    cost = 0
                else:
                    # Check if we have a weighted substitution
                    char_pair = (s1[i-1], s2[j-1])
                    cost = self.sound_weights.get(char_pair, 1.0)
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        # Return normalized distance
        max_len = max(len(s1), len(s2))
        return matrix[len(s1)][len(s2)] / max_len if max_len > 0 else 0.0
    
    def generate_ngrams(self, text: str, n: int = 3) -> Set[str]:
        """Generate n-grams from text for partial matching."""
        if len(text) < n:
            return {text.lower()}
        
        text = text.lower()
        ngrams = set()
        
        for i in range(len(text) - n + 1):
            ngrams.add(text[i:i+n])
        
        return ngrams
    
    def ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """Calculate similarity based on n-gram overlap."""
        ngrams1 = self.generate_ngrams(text1, n)
        ngrams2 = self.generate_ngrams(text2, n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_phonetic_similarity(self, text1: str, text2: str) -> float:
        """
        Master phonetic similarity calculation combining multiple methods.
        Returns similarity score from 0.0 to 1.0.
        """
        if not text1 or not text2:
            return 0.0
        
        # Method 1: Soundex similarity
        soundex1 = self.sanskrit_soundex(text1)
        soundex2 = self.sanskrit_soundex(text2)
        soundex_match = 1.0 if soundex1 == soundex2 else 0.0
        
        # Method 2: Metaphone similarity
        metaphone1 = self.sanskrit_metaphone(text1)
        metaphone2 = self.sanskrit_metaphone(text2)
        metaphone_sim = SequenceMatcher(None, metaphone1, metaphone2).ratio()
        
        # Method 3: Weighted Levenshtein (convert distance to similarity)
        lev_distance = self.weighted_levenshtein(text1, text2)
        lev_similarity = 1.0 - lev_distance
        
        # Method 4: N-gram similarity
        ngram_sim = self.ngram_similarity(text1, text2, 3)
        
        # Weighted combination
        weights = {
            'soundex': 0.2,
            'metaphone': 0.3, 
            'levenshtein': 0.3,
            'ngram': 0.2
        }
        
        final_score = (
            soundex_match * weights['soundex'] +
            metaphone_sim * weights['metaphone'] +
            lev_similarity * weights['levenshtein'] +
            ngram_sim * weights['ngram']
        )
        
        return min(1.0, max(0.0, final_score))
    
    def find_best_phonetic_matches(self, query: str, candidates: List[str], 
                                 threshold: float = 0.6, max_results: int = 5) -> List[Tuple[str, float]]:
        """
        Find best phonetic matches from a list of candidates.
        Returns list of (candidate, similarity_score) tuples.
        """
        matches = []
        
        for candidate in candidates:
            similarity = self.calculate_phonetic_similarity(query, candidate)
            if similarity >= threshold:
                matches.append((candidate, similarity))
        
        # Sort by similarity score (descending) and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]


# Utility functions for easy access
def get_sanskrit_soundex(text: str) -> str:
    """Quick access to Sanskrit soundex."""
    matcher = SanskritPhoneticMatcher()
    return matcher.sanskrit_soundex(text)

def calculate_sanskrit_similarity(text1: str, text2: str) -> float:
    """Quick access to phonetic similarity calculation."""
    matcher = SanskritPhoneticMatcher()
    return matcher.calculate_phonetic_similarity(text1, text2)

def find_phonetic_matches(query: str, candidates: List[str], 
                         threshold: float = 0.6) -> List[Tuple[str, float]]:
    """Quick access to phonetic matching."""
    matcher = SanskritPhoneticMatcher()
    return matcher.find_best_phonetic_matches(query, candidates, threshold)


# Simple test
if __name__ == "__main__":
    matcher = SanskritPhoneticMatcher()
    
    # Test cases for common Gita verse variations
    test_cases = [
        ("karmanye vadhikaraste", "karmany evadhikaraste"),  # Missing 'e'
        ("ma phaleshu kadachana", "mā phaleṣu kadācana"),    # Diacritics
        ("krishna", "kṛṣṇa"),                                # Romanization
        ("dharma", "dharm"),                                 # Missing vowel
        ("yoga", "yog")                                      # Truncation
    ]
    
    print("Sanskrit Phonetic Matching Test Results:")
    print("=" * 50)
    
    for query, target in test_cases:
        similarity = matcher.calculate_phonetic_similarity(query, target)
        soundex1 = matcher.sanskrit_soundex(query)
        soundex2 = matcher.sanskrit_soundex(target)
        
        print(f"Query: '{query}' -> Target: '{target}'")
        print(f"  Similarity: {similarity:.3f}")
        print(f"  Soundex: {soundex1} -> {soundex2}")
        print()