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
from .context_detector import ContextDetector
from .asr_pattern_matcher import ASRPatternMatcher
import sys
from pathlib import Path
# Add the parent directory to the path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.fuzzy_matcher import FuzzyMatcher

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
    
    def __init__(self, lexicon_dir: Path = None, config: Dict = None):
        self.lexicon_dir = Path(lexicon_dir or "lexicons")
        self.config = config or {}
        self.scripture_terms = {}
        self.compound_patterns = {}
        
        # Enhanced persistent caching system
        self.phonetic_cache = {}  # word_pair -> similarity_score
        self.term_index = {}      # first_letter -> [terms] for fast lookup
        self.processed_words = set()  # Track processed words to avoid recomputation
        
        # Initialize context detector for English protection
        self.context_detector = ContextDetector()
        
        # Initialize fuzzy matcher with configuration
        fuzzy_config = self.config.get('fuzzy_matching', {})
        self.fuzzy_matcher = FuzzyMatcher(
            max_distance=fuzzy_config.get('max_edit_distance', 3),
            min_confidence=fuzzy_config.get('min_confidence', 0.6),
            enable_cache=fuzzy_config.get('enable_caching', True)
        ) if fuzzy_config.get('enabled', True) else None
        
        # Initialize ASR pattern matcher
        asr_config = self.config.get('asr_pattern_matching', {})
        self.asr_matcher = ASRPatternMatcher(
            enable_compound_splitting=asr_config.get('enable_compound_splitting', True)
        ) if asr_config.get('enabled', True) else None
        
        # Configuration flags
        self.case_sensitive = self.config.get('case_sensitive_matching', True)
        self.enable_fuzzy_matching = fuzzy_config.get('enabled', True)
        self.enable_asr_patterns = asr_config.get('enabled', True)
        
        # Load all available term sources
        self._load_scripture_corrections()
        self._build_compound_patterns()
        self._build_term_index()  # Build fast lookup index
        self._create_intelligent_patterns()
        
        logger.info(f"Systematic term matcher initialized with {len(self.scripture_terms)} terms, indexed by {len(self.term_index)} buckets")
    
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

    def _build_term_index(self):
        """Build inverted index for fast term lookup by first letter."""
        self.term_index = {}
        
        for term in self.scripture_terms.keys():
            if term:
                first_letter = term[0].lower()
                if first_letter not in self.term_index:
                    self.term_index[first_letter] = []
                self.term_index[first_letter].append(term)
        
        # Sort each bucket by length for better matching
        for letter in self.term_index:
            self.term_index[letter].sort(key=len, reverse=True)
        
        logger.debug(f"Built term index with {len(self.term_index)} buckets")
    
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
        """Find all Sanskrit term corrections in text systematically with context awareness."""
        
        # CONTEXT VALIDATION: Check if text should be processed at all
        context_result = self.context_detector.detect_context(text)
        
        # If English context detected, return empty list (no corrections)
        if context_result.context_type == 'english':
            logger.debug(f"English context detected, skipping systematic matching: {context_result.markers_found}")
            return []
        
        corrections = []
        
        # For mixed content, only process Sanskrit segments
        if context_result.context_type == 'mixed' and context_result.segments:
            # Extract and process only Sanskrit segments
            words = text.split()
            for start_idx, end_idx, segment_type in context_result.segments:
                if segment_type == 'sanskrit':
                    segment_text = ' '.join(words[start_idx:end_idx])
                    corrections.extend(self._find_corrections_for_segment(segment_text))
            
        elif context_result.context_type == 'sanskrit':
            # Process full text for Sanskrit context
            corrections.extend(self._find_corrections_for_segment(text))
        
        # Remove duplicates and sort by confidence
        unique_corrections = self._deduplicate_corrections(corrections)
        return sorted(unique_corrections, key=lambda x: x.confidence, reverse=True)
    
    def _find_corrections_for_segment(self, text: str) -> List[TermMatch]:
        """Find corrections for a confirmed Sanskrit text segment."""
        corrections = []
        
        # 1. Exact scripture term matches
        corrections.extend(self._find_scripture_matches(text))
        
        # 2. Compound word matches  
        corrections.extend(self._find_compound_matches(text))
        
        # 3. Enhanced fuzzy matching (replaces phonetic similarity matches)
        if self.enable_fuzzy_matching and self.fuzzy_matcher:
            corrections.extend(self._find_fuzzy_matches(text))
        else:
            # Fallback to original phonetic similarity matches
            corrections.extend(self._find_phonetic_matches(text))
        
        # 4. ASR pattern-based corrections
        if self.enable_asr_patterns and self.asr_matcher:
            corrections.extend(self._find_asr_pattern_matches(text))
        else:
            # Fallback to original ASR correction logic
            corrections.extend(self._find_asr_corrections(text))
        
        return corrections
    
    def _find_scripture_matches(self, text: str) -> List[TermMatch]:
        """Find exact matches in scripture database."""
        matches = []
        words = re.findall(r'\b\w+\b', text.lower())
        
        # English words that should NEVER be translated to Sanskrit
        english_blocklist = {
            'treading', 'reading', 'leading', 'heading', 'spreading', 'breeding',
            'agitated', 'meditated', 'dedicated', 'activated', 'created', 'related',
            'seated', 'treated', 'heated', 'repeated', 'completed', 'defeated',
            'worship', 'business', 'success', 'given', 'extension', 'whole',
            'tell', 'four', 'neither', 'respect', 'courteous', 'gesture',
            'realized', 'surrender', 'looking', 'thinking', 'feeling', 'asking',
            'explained', 'carrying', 'powerful', 'mystical', 'meanings',
            'concluding', 'stage', 'grief', 'trees', 'plants', 'where',
            'different', 'sympathy', 'surprised', 'supposed', 'incarnation',
            'questioned', 'grieving', 'family', 'loss', 'makes', 'mind',
            'little', 'insane', 'extent', 'leaves', 'exaggerating', 'subtle',
            'meaning', 'behind', 'tells', 'experience', 'know', 'pretended',
            'herself', 'message', 'place', 'conquered', 'backed', 'certain',
            'some', 'authenticated', 'comes', 'subtle', 'fear', 'what',
            'bigger', 'well', 'read', 'will', 'there', 'when', 'easily',
            'guru', 'devotees', 'delay', 'forest', 'carefully', 'through',
            'together', 'session', 'meditation'
        }
        
        for word in words:
            # CRITICAL: Skip if word is common English word
            if word in english_blocklist:
                continue
                
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
        """Find phonetically similar terms with optimized caching and indexing."""
        matches = []
        words = re.findall(r'\b\w{4,}\b', text)  # Only longer words
        
        # English words that should NEVER be translated to Sanskrit
        english_blocklist = {
            'treading', 'reading', 'leading', 'heading', 'spreading', 'breeding',
            'agitated', 'meditated', 'dedicated', 'activated', 'created', 'related',
            'seated', 'treated', 'heated', 'repeated', 'completed', 'defeated',
            'worship', 'business', 'success', 'given', 'extension', 'whole',
            'tell', 'four', 'neither', 'respect', 'courteous', 'gesture',
            'realized', 'surrender', 'looking', 'thinking', 'feeling', 'asking',
            'explained', 'carrying', 'powerful', 'mystical', 'meanings',
            'concluding', 'stage', 'grief', 'trees', 'plants', 'where',
            'different', 'sympathy', 'surprised', 'supposed', 'incarnation',
            'questioned', 'grieving', 'family', 'loss', 'makes', 'mind',
            'little', 'insane', 'extent', 'leaves', 'exaggerating', 'subtle',
            'meaning', 'behind', 'tells', 'experience', 'know', 'pretended',
            'herself', 'message', 'place', 'conquered', 'backed', 'certain',
            'some', 'authenticated', 'comes', 'subtle', 'fear', 'what',
            'bigger', 'well', 'read', 'will', 'there', 'when', 'easily'
        }
        
        for word in words:
            word_lower = word.lower()
            
            # CRITICAL: Skip if word is common English word
            if word_lower in english_blocklist:
                continue
            
            # Skip if already processed this word
            if word_lower in self.processed_words:
                continue
            
            # Additional check: if word contains only ASCII and is common English pattern, skip
            if (word_lower.isascii() and 
                (word_lower.endswith('ing') or word_lower.endswith('ed') or 
                 word_lower.endswith('er') or word_lower.endswith('est') or
                 word_lower.endswith('ly') or word_lower.endswith('tion'))):
                continue
            
            # Check cache first
            cached_match = None
            for cached_key, cached_result in self.phonetic_cache.items():
                if cached_key.startswith(word_lower + "|"):
                    if cached_result['score'] >= 0.8:
                        cached_match = cached_result
                        break
            
            if cached_match:
                matches.append(TermMatch(
                    original=word,
                    corrected=cached_match['corrected'],
                    confidence=cached_match['score'] * 0.9,
                    match_type='phonetic_cached',
                    source='cache'
                ))
                continue
            
            # Use indexed lookup for efficiency
            first_letter = word_lower[0] if word_lower else ''
            candidate_terms = self.term_index.get(first_letter, [])
            
            # If no candidates in this bucket, try similar letters
            if not candidate_terms and first_letter:
                similar_letters = {'s': ['ś', 'ṣ'], 'n': ['ṇ', 'ñ'], 't': ['ṭ'], 'd': ['ḍ']}
                for similar in similar_letters.get(first_letter, []):
                    candidate_terms.extend(self.term_index.get(similar, []))
            
            # Early termination: limit candidates for performance
            candidate_terms = candidate_terms[:50]  # Process max 50 candidates per word
            
            best_match = None
            best_score = 0.0
            
            for script_term in candidate_terms:
                # Quick length check for early termination
                if abs(len(script_term) - len(word_lower)) > 3:
                    continue
                
                # Check cache for this specific pair
                cache_key = f"{word_lower}|{script_term}"
                if cache_key in self.phonetic_cache:
                    similarity = self.phonetic_cache[cache_key]['score']
                else:
                    similarity = self._calculate_phonetic_similarity(word_lower, script_term)
                    # Cache the result
                    self.phonetic_cache[cache_key] = {
                        'score': similarity,
                        'corrected': self.scripture_terms[script_term]['transliteration']
                    }
                
                if similarity > best_score and similarity >= 0.8:
                    best_score = similarity
                    best_match = self.scripture_terms[script_term]
            
            if best_match:
                matches.append(TermMatch(
                    original=word,
                    corrected=best_match['transliteration'],
                    confidence=best_score * 0.9,  # Slightly lower than exact matches
                    match_type='phonetic',
                    source='similarity'
                ))
            
            # Mark word as processed
            self.processed_words.add(word_lower)
        
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
    
    def _find_fuzzy_matches(self, text: str) -> List[TermMatch]:
        """
        Find matches using the enhanced fuzzy matcher with intelligent filtering.
        Optimized for Sanskrit processing with comprehensive English protection.
        """
        matches = []
        words = re.findall(r'\b\w{3,}\b', text)  # Only process words with 3+ characters
        
        # Comprehensive English protection system
        english_patterns = {
            # Common suffixes that indicate English words
            'suffixes': {'ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment', 'able', 'ible'},
            # Function words and common English terms
            'function_words': {
                'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but', 'his',
                'from', 'they', 'she', 'her', 'been', 'than', 'its', 'who', 'did', 'yes', 'would',
                'could', 'should', 'will', 'can', 'may', 'might', 'must', 'shall', 'ought'
            },
            # Content words that should never be Sanskrit
            'content_blocklist': {
                'treading', 'reading', 'leading', 'heading', 'spreading', 'breeding', 'feeding',
                'agitated', 'meditated', 'dedicated', 'activated', 'created', 'related', 'stated',
                'seated', 'treated', 'heated', 'repeated', 'completed', 'defeated', 'deleted',
                'worship', 'business', 'success', 'process', 'address', 'express', 'progress',
                'tell', 'four', 'five', 'neither', 'either', 'respect', 'aspect', 'suspect',
                'realized', 'surrender', 'looking', 'thinking', 'feeling', 'asking', 'walking',
                'explained', 'carrying', 'powerful', 'mystical', 'meanings', 'feelings', 'beings',
                'concluding', 'including', 'excluding', 'stage', 'grief', 'trees', 'plants', 'leaves',
                'different', 'sympathy', 'surprised', 'supposed', 'proposed', 'exposed', 'composed',
                'questioned', 'mentioned', 'presented', 'represented', 'family', 'clearly', 'really',
                'meaning', 'behind', 'beyond', 'beside', 'before', 'between', 'beneath', 'became',
                'bigger', 'smaller', 'better', 'worse', 'easier', 'harder', 'faster', 'slower'
            }
        }
        
        def is_likely_english(word: str) -> bool:
            """Determine if a word is likely English and should be protected."""
            word_lower = word.lower()
            
            # Check function words
            if word_lower in english_patterns['function_words']:
                return True
            
            # Check explicit blocklist
            if word_lower in english_patterns['content_blocklist']:
                return True
            
            # Check English suffixes
            for suffix in english_patterns['suffixes']:
                if word_lower.endswith(suffix):
                    return True
            
            # Additional heuristics for English detection
            if len(word_lower) >= 4:
                # Common English letter patterns
                english_patterns_regex = [
                    r'qu[aeiou]',   # qu- combinations
                    r'[^aeiou]{4}', # 4+ consecutive consonants (rare in Sanskrit)
                    r'^th[aeiou]',  # th- at start
                    r'ght$',        # -ght endings
                    r'ck[aeiou]',   # ck combinations
                ]
                
                for pattern in english_patterns_regex:
                    if re.search(pattern, word_lower):
                        return True
            
            return False
        
        # Process words with enhanced filtering
        for word in words:
            word_lower = word.lower()
            
            # Enhanced English protection
            if is_likely_english(word):
                continue
            
            # Skip if already processed (performance optimization)
            if word_lower in self.processed_words:
                continue
            
            # Additional Sanskrit likelihood check
            if self._is_likely_sanskrit_candidate(word_lower):
                matches.extend(self._process_fuzzy_candidate(word, word_lower))
            
            # Mark as processed regardless of outcome
            self.processed_words.add(word_lower)
        
        return matches
    
    def _is_likely_sanskrit_candidate(self, word: str) -> bool:
        """Determine if a word is a good candidate for Sanskrit matching."""
        # Sanskrit words often contain specific character patterns
        sanskrit_indicators = {
            'common_letters': set('aeiourmntpkdgbhvsy'),
            'sanskrit_combinations': ['dh', 'th', 'kh', 'gh', 'ch', 'jh', 'ph', 'bh', 'sh', 'kr', 'pr', 'tr'],
            'vowel_patterns': ['aa', 'ii', 'uu', 'ai', 'au'],
        }
        
        # Must have reasonable length
        if len(word) < 3:
            return False
        
        # Check for Sanskrit-like character composition
        sanskrit_char_ratio = sum(1 for c in word if c in sanskrit_indicators['common_letters']) / len(word)
        if sanskrit_char_ratio < 0.5:  # At least 50% Sanskrit-common characters
            return False
        
        # Bonus points for Sanskrit combinations
        for combo in sanskrit_indicators['sanskrit_combinations'] + sanskrit_indicators['vowel_patterns']:
            if combo in word:
                return True
        
        # Check against known prefixes/suffixes
        sanskrit_prefixes = ['upa', 'pra', 'sam', 'anu', 'ava', 'adhi', 'abhi']
        sanskrit_suffixes = ['ana', 'ika', 'tra', 'tha', 'nam', 'tam']
        
        for prefix in sanskrit_prefixes:
            if word.startswith(prefix):
                return True
        
        for suffix in sanskrit_suffixes:
            if word.endswith(suffix):
                return True
        
        return True  # Default to true for borderline cases
    
    def _process_fuzzy_candidate(self, original_word: str, word_lower: str) -> List[TermMatch]:
        """Process a single word candidate for fuzzy matching."""
        matches = []
        
        # Smart candidate selection using term index
        first_letter = word_lower[0] if word_lower else ''
        candidate_terms = self.term_index.get(first_letter, [])
        
        # If no direct matches, try phonetically similar first letters
        if not candidate_terms:
            similar_letters = {
                's': ['ś', 'ṣ'], 'n': ['ṇ', 'ñ'], 't': ['ṭ'], 'd': ['ḍ'],
                'r': ['ṛ'], 'l': ['ḷ'], 'm': ['ṃ']
            }
            for similar in similar_letters.get(first_letter, []):
                candidate_terms.extend(self.term_index.get(similar, []))
        
        # Optimize candidate list - prioritize by length similarity
        candidate_terms = sorted(candidate_terms, key=lambda x: abs(len(x) - len(word_lower)))[:15]
        
        best_match = None
        best_confidence = 0.0
        
        for script_term in candidate_terms:
            # Enhanced pre-filtering
            len_diff = abs(len(word_lower) - len(script_term))
            if len_diff > self.fuzzy_matcher.max_distance:
                continue
            
            # Quick similarity check before expensive fuzzy matching
            if len_diff <= 1:  # Very similar lengths get priority
                match_result = self.fuzzy_matcher.match(original_word, script_term)
                if match_result and match_result.confidence > best_confidence:
                    best_confidence = match_result.confidence
                    best_match = (match_result, script_term)
                    
                    # Early termination for excellent matches
                    if match_result.confidence >= 0.95:
                        break
        
        # Create match if we found a good candidate
        if best_match and best_confidence >= self.fuzzy_matcher.min_confidence:
            match_result, script_term = best_match
            entry = self.scripture_terms[script_term]
            matches.append(TermMatch(
                original=original_word,
                corrected=entry['transliteration'],
                confidence=match_result.confidence,
                match_type=f"fuzzy_{match_result.match_type}",
                source='enhanced_fuzzy_matcher'
            ))
        
        return matches
    
    def _find_asr_pattern_matches(self, text: str) -> List[TermMatch]:
        """Find matches using ASR pattern recognition."""
        matches = []
        
        if not self.asr_matcher:
            return matches
        
        # Get ASR corrections
        asr_corrections = self.asr_matcher.find_asr_corrections(text)
        
        for asr_correction in asr_corrections:
            # Check if the ASR-corrected term exists in our database
            corrected_lower = asr_correction.corrected.lower()
            if corrected_lower in self.scripture_terms:
                entry = self.scripture_terms[corrected_lower]
                matches.append(TermMatch(
                    original=asr_correction.original,
                    corrected=entry['transliteration'],
                    confidence=asr_correction.confidence,
                    match_type=f"asr_{asr_correction.transformation_type}",
                    source='asr_pattern_matcher'
                ))
            else:
                # Use the ASR correction directly if it's not in database but looks valid
                matches.append(TermMatch(
                    original=asr_correction.original,
                    corrected=asr_correction.corrected,
                    confidence=asr_correction.confidence * 0.8,  # Lower confidence for direct corrections
                    match_type=f"asr_direct_{asr_correction.transformation_type}",
                    source='asr_pattern_matcher'
                ))
        
        return matches
    
    def _calculate_phonetic_similarity(self, word1: str, word2: str) -> float:
        """Calculate phonetic similarity with optimized early termination."""
        # Quick exact match
        if word1 == word2:
            return 1.0
        
        # Early termination for very different lengths
        len_diff = abs(len(word1) - len(word2))
        if len_diff > 3:
            return 0.0
        
        # Quick character overlap check for early termination
        set1, set2 = set(word1.lower()), set(word2.lower())
        overlap = len(set1 & set2) / max(len(set1), len(set2))
        if overlap < 0.4:  # If less than 40% character overlap, skip expensive calculation
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
        
        # Optimized edit distance with early termination
        m, n = len(word1), len(word2)
        
        # If one string is much shorter, use simple approach
        if min(m, n) < 4:
            common = sum(1 for c1, c2 in zip(word1, word2) if c1 == c2)
            return common / max(m, n)
        
        # Use banded edit distance for performance (only compute within reasonable range)
        max_distance = max(m, n) * 0.6  # Allow up to 60% differences
        
        # Initialize DP array with band optimization
        band_width = min(6, max(m, n) // 2)  # Limit computation band
        dp = [[float('inf')] * (n + 1) for _ in range(m + 1)]
        
        dp[0][0] = 0
        for i in range(1, min(m + 1, band_width + 1)):
            dp[i][0] = i
        for j in range(1, min(n + 1, band_width + 1)):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            # Band optimization: only compute relevant range
            start_j = max(1, i - band_width)
            end_j = min(n + 1, i + band_width + 1)
            
            min_val_in_row = float('inf')
            
            for j in range(start_j, end_j):
                if word1[i-1] == word2[j-1]:
                    cost = 0
                elif (word1[i-1] in substitutions and word2[j-1] in substitutions and
                      substitutions[word1[i-1]] == substitutions[word2[j-1]]):
                    cost = 0.3  # Low cost for Sanskrit-similar characters
                else:
                    cost = 1
                
                dp[i][j] = min(
                    dp[i-1][j] + 1 if j > 0 else float('inf'),      # deletion
                    dp[i][j-1] + 1 if i > 0 else float('inf'),      # insertion  
                    dp[i-1][j-1] + cost if i > 0 and j > 0 else float('inf')  # substitution
                )
                
                min_val_in_row = min(min_val_in_row, dp[i][j])
            
            # Early termination: if minimum in current row exceeds threshold
            if min_val_in_row > max_distance:
                return 0.0
        
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
        """Apply all corrections to text with optimized batch processing."""
        corrections = self.find_all_corrections(text)
        applied_corrections = []
        result_text = text
        
        # Early termination: if no corrections found, return immediately
        if not corrections:
            return result_text, applied_corrections
        
        # Limit corrections to prevent over-processing (reduced from 20 to 10 for performance)
        max_corrections = 10
        if len(corrections) > max_corrections:
            # Keep highest confidence corrections
            corrections.sort(key=lambda x: x.confidence, reverse=True)
            corrections = corrections[:max_corrections]
        
        # Sort by original text length (longest first) to avoid partial replacements
        corrections.sort(key=lambda x: len(x.original), reverse=True)
        
        # Batch process corrections for efficiency
        replacements_made = 0
        for correction in corrections:
            # Early termination: stop if we've made enough corrections
            if replacements_made >= max_corrections:
                break
                
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(correction.original) + r'\b'
            if re.search(pattern, result_text, re.IGNORECASE):
                result_text = re.sub(pattern, correction.corrected, result_text, flags=re.IGNORECASE)
                applied_corrections.append(correction)
                replacements_made += 1
        
        return result_text, applied_corrections

    def apply_corrections_batch(self, texts: List[str]) -> List[Tuple[str, List[TermMatch]]]:
        """Apply corrections to multiple texts in batch for better performance."""
        results = []
        
        # Reset processed words cache for new batch
        batch_processed_words = set()
        
        for text in texts:
            # Temporarily update processed words to include batch context
            original_processed = self.processed_words.copy()
            self.processed_words.update(batch_processed_words)
            
            # Process the text
            corrected_text, corrections = self.apply_corrections(text)
            results.append((corrected_text, corrections))
            
            # Update batch cache with newly processed words
            words = re.findall(r'\b\w{4,}\b', text.lower())
            batch_processed_words.update(words)
            
            # Restore original processed words state
            self.processed_words = original_processed
        
        # Update global processed words with batch results
        self.processed_words.update(batch_processed_words)
        
        return results

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