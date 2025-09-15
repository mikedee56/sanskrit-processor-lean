"""
FuzzyMatcher - Intelligent fuzzy and case-insensitive matching for Sanskrit terms.
Provides Levenshtein distance-based matching with confidence scoring and performance optimization.
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
from .performance_cache import get_performance_cache

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Represents a fuzzy match result with confidence and metadata."""
    original: str
    candidate: str
    confidence: float
    edit_distance: int
    match_type: str  # 'exact', 'case_insensitive', 'fuzzy', 'pattern'
    transformation_info: Dict[str, Any] = None

class FuzzyMatcher:
    """
    Intelligent fuzzy matcher with case-insensitive and phonetic matching capabilities.
    Optimized for Sanskrit term matching with configurable thresholds.
    """
    
    def __init__(self, max_distance: int = 3, min_confidence: float = 0.6, enable_cache: bool = True):
        """
        Initialize FuzzyMatcher with configurable parameters.
        
        Args:
            max_distance: Maximum Levenshtein distance for fuzzy matches
            min_confidence: Minimum confidence score for matches
            enable_cache: Whether to cache expensive calculations
        """
        self.max_distance = max_distance
        self.min_confidence = min_confidence
        self.enable_cache = enable_cache
        self.cache: Dict[str, MatchResult] = {}
        
        # Initialize performance cache for expensive operations
        if enable_cache:
            self.perf_cache = get_performance_cache()
            # Apply decorators to expensive methods (skip due to signature incompatibility)
            # self.levenshtein_distance = self.perf_cache.cache_fuzzy_match(self.levenshtein_distance)
            # self._phonetic_distance = self.perf_cache.cache_fuzzy_match(self._phonetic_distance)
        
        # Sanskrit-specific phonetic mappings for enhanced matching
        self.sanskrit_phonetic_groups = {
            ('s', 'ś', 'ṣ'): 0.1,  # Very similar sounds, low penalty
            ('n', 'ṇ', 'ṅ', 'ñ'): 0.1,
            ('t', 'ṭ'): 0.1,
            ('d', 'ḍ'): 0.1,
            ('a', 'ā'): 0.2,  # Vowel length differences
            ('i', 'ī'): 0.2,
            ('u', 'ū'): 0.2,
            ('r', 'ṛ', 'ṝ'): 0.2,
            ('l', 'ḷ', 'ḹ'): 0.2,
            ('e', 'ē'): 0.2,
            ('o', 'ō'): 0.2,
            ('m', 'ṃ', 'ṁ'): 0.1,
            # ASR common confusions
            ('v', 'w'): 0.3,
            ('sh', 's'): 0.3,
            ('ch', 'c'): 0.3,
            ('th', 't'): 0.3,
            ('ph', 'f'): 0.3,
            ('bh', 'b'): 0.3,
            ('dh', 'd'): 0.3,
        }
        
        # Build phonetic substitution lookup
        self._build_phonetic_substitutions()
        
        logger.debug(f"FuzzyMatcher initialized: max_distance={max_distance}, min_confidence={min_confidence}")
    
    def _build_phonetic_substitutions(self):
        """Build lookup table for phonetic character substitutions."""
        self.phonetic_subs = {}
        
        # Single character mappings
        for group, penalty in self.sanskrit_phonetic_groups.items():
            if len(group) > 0 and len(group[0]) == 1:  # Single characters only
                for char in group:
                    if char not in self.phonetic_subs:
                        self.phonetic_subs[char] = []
                    for other_char in group:
                        if other_char != char:
                            self.phonetic_subs[char].append((other_char, penalty))
    
    def match(self, input_term: str, target_term: str) -> Optional[MatchResult]:
        """
        Find best match for input_term against target_term using cascading approach.
        
        Args:
            input_term: Term to match
            target_term: Target term to match against
            
        Returns:
            MatchResult if match found above confidence threshold, None otherwise
        """
        if not input_term or not target_term:
            return None
        
        # Check cache first
        cache_key = f"{input_term}|{target_term}"
        if self.enable_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self._find_best_match(input_term, target_term)
        
        # Cache result if caching enabled
        if self.enable_cache and result:
            self.cache[cache_key] = result
        
        return result
    
    def _find_best_match(self, input_term: str, target_term: str) -> Optional[MatchResult]:
        """Internal method to find the best match using cascading strategy."""
        
        # 1. Exact match (highest confidence)
        if input_term == target_term:
            return MatchResult(
                original=input_term,
                candidate=target_term,
                confidence=1.0,
                edit_distance=0,
                match_type='exact',
                transformation_info={'method': 'exact_match'}
            )
        
        # 2. Case-insensitive match
        if input_term.lower() == target_term.lower():
            return MatchResult(
                original=input_term,
                candidate=target_term,
                confidence=0.95,
                edit_distance=0,
                match_type='case_insensitive',
                transformation_info={'method': 'case_normalization'}
            )
        
        # 3. Fuzzy match with Levenshtein distance
        distance = self.levenshtein_distance(input_term.lower(), target_term.lower())
        if distance <= self.max_distance:
            confidence = self.calculate_confidence(input_term, target_term, distance)
            if confidence >= self.min_confidence:
                return MatchResult(
                    original=input_term,
                    candidate=target_term,
                    confidence=confidence,
                    edit_distance=distance,
                    match_type='fuzzy',
                    transformation_info={
                        'method': 'levenshtein',
                        'edit_distance': distance,
                        'length_diff': abs(len(input_term) - len(target_term))
                    }
                )
        
        # 4. Phonetic similarity for Sanskrit terms
        phonetic_result = self.phonetic_match(input_term, target_term)
        if phonetic_result and phonetic_result.confidence >= self.min_confidence:
            return phonetic_result
        
        # 5. Compound word similarity for complex Sanskrit terms
        compound_result = self.compound_similarity_match(input_term, target_term)
        if compound_result and compound_result.confidence >= self.min_confidence:
            return compound_result
        
        return None
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance with early termination optimization.
        Optimized for performance with minimal memory usage.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Edit distance between strings
        """
        if s1 == s2:
            return 0
        
        len1, len2 = len(s1), len(s2)
        
        # Early termination for very different lengths
        if abs(len1 - len2) > self.max_distance:
            return self.max_distance + 1
            
        # Early termination for very short strings
        if len1 == 0:
            return min(len2, self.max_distance + 1)
        if len2 == 0:
            return min(len1, self.max_distance + 1)
        
        # Use single-row optimization for memory efficiency
        if len1 > len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        
        # Initialize previous row
        previous_row = list(range(len1 + 1))
        
        # Process each character in s2
        for i in range(len2):
            current_row = [i + 1]
            char2 = s2[i]
            
            for j in range(len1):
                char1 = s1[j]
                cost = 0 if char1 == char2 else 1
                
                current_row.append(min(
                    previous_row[j + 1] + 1,    # deletion
                    current_row[j] + 1,        # insertion
                    previous_row[j] + cost     # substitution
                ))
            
            # Early termination: if minimum in row exceeds max_distance
            if min(current_row) > self.max_distance:
                return self.max_distance + 1
                
            previous_row = current_row
        
        return min(previous_row[len1], self.max_distance + 1)
    
    def calculate_confidence(self, input_str: str, target_str: str, distance: int) -> float:
        """
        Calculate confidence score based on edit distance and string characteristics.
        Enhanced with Sanskrit-specific weighting and positional matching bonuses.
        
        Args:
            input_str: Input string
            target_str: Target string
            distance: Edit distance between strings
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        max_len = max(len(input_str), len(target_str))
        if max_len == 0:
            return 1.0
        
        # Base confidence from edit distance
        base_confidence = 1.0 - (distance / max_len)
        
        # Length similarity bonus (penalize extreme length differences less for Sanskrit)
        len_diff = abs(len(input_str) - len(target_str))
        length_similarity = 1.0 - (len_diff / max_len)
        
        # Character overlap bonus with Sanskrit-aware weighting
        set1, set2 = set(input_str.lower()), set(target_str.lower())
        if len(set1) > 0 and len(set2) > 0:
            overlap_ratio = len(set1 & set2) / max(len(set1), len(set2))
            # Boost confidence for high character overlap
            overlap_bonus = min(0.25, overlap_ratio * 0.3)
        else:
            overlap_bonus = 0
        
        # Positional accuracy bonus - reward matches at word boundaries
        positional_bonus = 0
        if len(input_str) >= 3 and len(target_str) >= 3:
            # Check prefix/suffix similarity
            prefix_match = input_str[:2].lower() == target_str[:2].lower()
            suffix_match = input_str[-2:].lower() == target_str[-2:].lower()
            
            if prefix_match:
                positional_bonus += 0.05
            if suffix_match:
                positional_bonus += 0.05
        
        # Combine scores with optimized weights for Sanskrit processing
        final_confidence = (
            base_confidence * 0.65 +      # Primary weight on edit distance
            length_similarity * 0.20 +    # Length matters but less critical
            overlap_bonus +               # Character overlap (up to 0.25)
            positional_bonus              # Positional matching (up to 0.10)
        )
        
        return min(1.0, max(0.0, final_confidence))
    
    def phonetic_match(self, input_term: str, target_term: str) -> Optional[MatchResult]:
        """
        Perform phonetic matching using Sanskrit-aware character substitutions.
        
        Args:
            input_term: Input term
            target_term: Target term
            
        Returns:
            MatchResult if phonetic match found, None otherwise
        """
        # Convert to lowercase for comparison
        input_lower = input_term.lower()
        target_lower = target_term.lower()
        
        # Calculate phonetic distance using Sanskrit-aware substitutions
        distance = self._phonetic_distance(input_lower, target_lower)
        max_len = max(len(input_lower), len(target_lower))
        
        if max_len == 0:
            return None
        
        # Calculate confidence based on phonetic distance
        confidence = 1.0 - (distance / max_len)
        
        if confidence >= self.min_confidence:
            return MatchResult(
                original=input_term,
                candidate=target_term,
                confidence=confidence * 0.85,  # Slightly lower than exact fuzzy match
                edit_distance=int(distance),
                match_type='phonetic',
                transformation_info={
                    'method': 'phonetic_similarity',
                    'phonetic_distance': distance
                }
            )
        
        return None
    
    def compound_similarity_match(self, input_term: str, target_term: str) -> Optional[MatchResult]:
        """
        Perform compound word similarity matching for complex Sanskrit terms.
        Uses substring matching and common transformations.
        
        Args:
            input_term: Input term
            target_term: Target term
            
        Returns:
            MatchResult if compound match found, None otherwise
        """
        input_lower = input_term.lower()
        target_lower = target_term.lower()
        
        # For significantly different lengths, use substring matching
        min_len = min(len(input_lower), len(target_lower))
        max_len = max(len(input_lower), len(target_lower))
        
        if max_len > min_len * 1.2:  # Significant length difference
            # Find common subsequence
            common_ratio = self._longest_common_subsequence_ratio(input_lower, target_lower)
            
            # If there's good overlap, consider it a compound match
            if common_ratio >= 0.55:
                # Give compound matches higher confidence if they pass threshold
                confidence = min(0.9, common_ratio + 0.1)  # Boost confidence for compound matches
                if confidence >= self.min_confidence:
                    return MatchResult(
                        original=input_term,
                        candidate=target_term,
                        confidence=confidence,
                        edit_distance=int(max_len * (1 - common_ratio)),
                        match_type='compound',
                        transformation_info={
                            'method': 'compound_substring',
                            'common_ratio': common_ratio
                        }
                    )
        
        return None
    
    def _longest_common_subsequence_ratio(self, s1: str, s2: str) -> float:
        """
        Calculate the ratio of longest common subsequence to the longer string.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Ratio of LCS to longer string length
        """
        len1, len2 = len(s1), len(s2)
        
        # DP table for LCS
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[len1][len2]
        max_len = max(len1, len2)
        
        return lcs_length / max_len if max_len > 0 else 0.0
    
    def _phonetic_distance(self, s1: str, s2: str) -> float:
        """
        Calculate phonetic distance using Sanskrit-aware character penalties.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Phonetic distance (float for weighted penalties)
        """
        len1, len2 = len(s1), len(s2)
        
        # Initialize distance matrix
        dp = [[0.0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            dp[i][0] = float(i)
        for j in range(len2 + 1):
            dp[0][j] = float(j)
        
        # Fill the matrix with phonetic-aware costs
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    cost = 0.0
                else:
                    # Check if characters are phonetically similar
                    cost = self._get_phonetic_penalty(s1[i-1], s2[j-1])
                
                dp[i][j] = min(
                    dp[i-1][j] + 1.0,      # deletion
                    dp[i][j-1] + 1.0,      # insertion
                    dp[i-1][j-1] + cost    # substitution
                )
        
        return dp[len1][len2]
    
    def _get_phonetic_penalty(self, char1: str, char2: str) -> float:
        """
        Get phonetic penalty for character substitution.
        
        Args:
            char1: First character
            char2: Second character
            
        Returns:
            Penalty score (lower = more similar)
        """
        # Check Sanskrit phonetic groups
        for group, penalty in self.sanskrit_phonetic_groups.items():
            if char1 in group and char2 in group:
                return penalty
        
        # Default substitution cost
        return 1.0
    
    def batch_match(self, input_term: str, candidates: List[str]) -> List[MatchResult]:
        """
        Match input term against multiple candidates efficiently.
        
        Args:
            input_term: Term to match
            candidates: List of candidate terms
            
        Returns:
            List of MatchResults sorted by confidence (descending)
        """
        results = []
        
        for candidate in candidates:
            match_result = self.match(input_term, candidate)
            if match_result:
                results.append(match_result)
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results
    
    def clear_cache(self):
        """Clear the internal cache."""
        self.cache.clear()
        logger.debug("FuzzyMatcher cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'cache_size': len(self.cache),
            'cache_enabled': self.enable_cache
        }
        
        # Add performance cache stats if enabled
        if self.enable_cache and hasattr(self, 'perf_cache'):
            perf_stats = self.perf_cache.get_performance_stats()
            hit_rates = self.perf_cache.get_hit_rates()
            
            stats.update({
                'performance_cache_stats': perf_stats,
                'fuzzy_match_hit_rate': hit_rates.get('fuzzy_matches', 0.0),
                'performance_cache_memory_mb': perf_stats.get('memory_usage', {}).get('total_cache_mb', 0.0)
            })
        
        return stats

if __name__ == "__main__":
    # Test the fuzzy matcher
    matcher = FuzzyMatcher(max_distance=3, min_confidence=0.6)
    
    # Test cases from the story
    test_cases = [
        ("Karma", "karma"),  # Case insensitive
        ("yogabashi", "yogavasistha"),  # Fuzzy matching
        ("jnana", "jñāna"),  # Sanskrit diacriticals
        ("shivashistha", "sivasista"),  # Phonetic similarity
        ("malagrasth", "mala-grasta"),  # With hyphen
    ]
    
    
    print("=== FUZZY MATCHER TEST ===")
    for input_term, target_term in test_cases:
        result = matcher.match(input_term, target_term)
        if result:
            print(f"{input_term} → {target_term}: confidence={result.confidence:.3f}, "
                  f"type={result.match_type}, distance={result.edit_distance}")
        else:
            print(f"{input_term} → {target_term}: NO MATCH")