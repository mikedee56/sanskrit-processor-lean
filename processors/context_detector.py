"""Context Detection Module for Sanskrit Processing Pipeline

Implements three-layer context detection to prevent English→Sanskrit translation bugs
while preserving accurate Sanskrit processing capabilities.

Author: Development Agent
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from utils.performance_cache import get_performance_cache
    from utils.pattern_manager import get_pattern_manager
    PERF_CACHE_AVAILABLE = True
except ImportError:
    PERF_CACHE_AVAILABLE = False
    logger.debug("Performance cache not available - using basic caching")

@dataclass
class ContextResult:
    """Result of context detection analysis."""
    context_type: str  # 'english', 'sanskrit', 'mixed', 'invocation', 'corrupted_sanskrit'
    confidence: float  # 0.0 to 1.0
    segments: List[Tuple[int, int, str]] = None  # For mixed content: (start, end, type)
    markers_found: List[str] = None  # Specific markers that influenced decision
    override_reason: str = None  # Reason for override (e.g., 'sanskrit_whitelist')
    processing_mode: str = None  # Recommended processing mode: 'preserve', 'correct', 'surgical', 'replace'
    embedded_terms: List[str] = None  # Sanskrit terms found embedded in English

class ContextDetector:
    """Enhanced context detection with configurable thresholds and Sanskrit whitelist override."""
    
    def __init__(self, config_path: str = None, context_config: 'ContextConfig' = None):
        """Initialize context detector with enhanced configuration and scripture database integration.
        
        Args:
            config_path: Path to configuration file (legacy support)
            context_config: ContextConfig instance for modern configuration
        """
        import yaml
        from pathlib import Path
        from .context_config import ContextConfig
        
        # Use provided context config or load from file/defaults
        if context_config is not None:
            self.config = context_config
        elif config_path is not None:
            # Legacy mode - load from language markers file
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    legacy_config = yaml.safe_load(f)
                # Convert legacy config to new format
                self.config = self._convert_legacy_config(legacy_config)
            except (FileNotFoundError, yaml.YAMLError) as e:
                logger.warning(f"Could not load language markers config from {config_path}: {e}")
                self.config = ContextConfig()
        else:
            # Try to load from main config file
            main_config_path = Path(__file__).parent.parent / 'config.yaml'
            if main_config_path.exists():
                self.config = ContextConfig.load_from_file(main_config_path)
            else:
                self.config = ContextConfig()
        
        # Validate configuration
        if not self.config.validate():
            logger.warning("Invalid context configuration detected, using defaults")
            self.config = ContextConfig()
        
        # Performance optimization - convert lists to sets for O(1) lookups
        self.sanskrit_priority_set = set(term.lower() for term in self.config.sanskrit_priority_terms)
        self.english_function_set = set(term.lower() for term in self.config.english_function_words)
        self.sanskrit_diacriticals_set = set(self.config.sanskrit_diacriticals)
        self.sanskrit_sacred_set = set(term.lower() for term in self.config.sanskrit_sacred_terms)
        
        # ENHANCEMENT: Load scripture terms database for comprehensive Sanskrit recognition
        self.scripture_terms = {}
        self._load_scripture_database()
        
        # Load ASR variations from priority terms file if available
        self.asr_variations = {}
        priority_terms_path = Path(__file__).parent.parent / 'lexicons' / 'sanskrit_priority_terms.yaml'
        try:
            if priority_terms_path.exists():
                with open(priority_terms_path, 'r', encoding='utf-8') as f:
                    priority_data = yaml.safe_load(f)
                    self.asr_variations = priority_data.get('asr_variations', {})
        except Exception as e:
            logger.debug(f"Could not load ASR variations: {e}")
        
        # Cache for performance (if enabled)
        self.context_cache = {} if self.config.cache_results else None
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize performance cache and pattern manager if available
        self.perf_cache = None
        self.pattern_manager = None
        if PERF_CACHE_AVAILABLE and self.config.cache_results:
            self.perf_cache = get_performance_cache()
            self.pattern_manager = get_pattern_manager()
            # Apply performance caching to expensive methods
            self.is_pure_english = self.perf_cache.cache_context_detection(self.is_pure_english)
            self.has_sanskrit_markers = self.perf_cache.cache_context_detection(self.has_sanskrit_markers)
            self.analyze_mixed_content = self.perf_cache.cache_context_detection(self.analyze_mixed_content)
            # Preload patterns for better performance
            self.pattern_manager.preload_for_context('mixed')
        
        # Initialize mixed content detection capabilities
        self._initialize_mixed_content_detection()

        total_sanskrit_terms = len(self.sanskrit_priority_set) + len(self.scripture_terms)
        logger.info(f"Context detector initialized with {len(self.sanskrit_priority_set)} priority terms + {len(self.scripture_terms)} scripture terms = {total_sanskrit_terms} total Sanskrit terms")
        if self.config.debug_logging:
            logger.info(f"Debug logging enabled for context detection")

    def _load_scripture_database(self):
        """Load scripture terms database for comprehensive Sanskrit recognition."""
        from pathlib import Path
        import yaml
        
        lexicon_dir = Path(__file__).parent.parent / "lexicons"
        corrections_file = lexicon_dir / "corrections_with_scripture.yaml"
        
        if corrections_file.exists():
            try:
                with open(corrections_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                for entry in data.get('entries', []):
                    original = entry['original_term'].lower()
                    self.scripture_terms[original] = entry
                    
                    # Also index by variations
                    for variation in entry.get('variations', []):
                        if isinstance(variation, str):  # Skip non-string variations
                            self.scripture_terms[variation.lower()] = entry
                            
                logger.debug(f"Loaded {len(data.get('entries', []))} scripture entries for context detection")
                
            except Exception as e:
                logger.warning(f"Could not load scripture database for context detection: {e}")
                self.scripture_terms = {}
        else:
            logger.debug(f"Scripture corrections file not found: {corrections_file}")
            self.scripture_terms = {}

    def _initialize_mixed_content_detection(self):
        """Initialize mixed content detection patterns and capabilities."""
        # Invocation patterns
        self.invocation_patterns = {
            'om_based': re.compile(r'\bom\s+\w+.*?(om|namaha?)\b', re.IGNORECASE),
            'devotional': re.compile(r'devotions?\s+to\s+lord\s+\w+', re.IGNORECASE),
            'divine_sequence': re.compile(r'\b(vasudeva|devaki|paramanandam|trishnam|vande|jagadguru)\b', re.IGNORECASE)
        }

        # Corrupted Sanskrit patterns
        self.corrupted_sanskrit_patterns = {
            'verse_3_16': re.compile(r'evam?\s+pravartitam?\s+chakram?\s+.*?pārtha\s+sa\s+jīvati', re.IGNORECASE),
            'mixed_verse': re.compile(r'verse\s+number\s+is\s+\d+\.\s+[a-z\s]*?(pārtha|mokha|karma)', re.IGNORECASE)
        }

        # Embedded Sanskrit term patterns
        self.embedded_term_patterns = {
            'philosophical': re.compile(r'\b(samskaras?|dharma|karma|moksha|jnana)\b', re.IGNORECASE),
            'practices': re.compile(r'\b(gada\s+pari\s+naya|prarabdha\s+karma|āhār)\b', re.IGNORECASE),
            'names': re.compile(r'\b(shankaracharya|krishna|arjuna)\b', re.IGNORECASE),
            'titles': re.compile(r'\b(shrimad\s+)?bhagavad\s+gita\b', re.IGNORECASE)
        }

    def _convert_legacy_config(self, legacy_config: dict) -> 'ContextConfig':
        """Convert legacy language markers config to new ContextConfig format."""
        from .context_config import ContextConfig
        
        # Extract values from legacy structure
        english_markers = legacy_config.get('english_markers', {})
        sanskrit_markers = legacy_config.get('sanskrit_markers', {})
        thresholds = legacy_config.get('thresholds', {})
        
        return ContextConfig(
            english_threshold=thresholds.get('english_confidence_threshold', 0.7),
            sanskrit_threshold=thresholds.get('sanskrit_confidence_threshold', 0.7),
            diacritical_density_high=thresholds.get('diacritical_density_high', 0.3),
            diacritical_density_medium=thresholds.get('diacritical_density_medium', 0.1),
            english_markers_required=thresholds.get('english_markers_required', 2),
            english_function_words=english_markers.get('function_words', []),
            sanskrit_diacriticals=sanskrit_markers.get('diacriticals', []),
            sanskrit_sacred_terms=sanskrit_markers.get('sacred_terms', [])
        )
    
    def detect_context(self, text: str) -> 'ContextResult':
        """
        Enhanced context detection with Sanskrit whitelist override and performance profiling.
        
        Args:
            text: Input text to analyze
            
        Returns:
            ContextResult with detected context type and details
        """
        import time
        
        if not text or not text.strip():
            return ContextResult('english', 1.0, markers_found=['empty_text'])
        
        # Performance tracking if enabled
        start_time = time.perf_counter() if self.config.performance_profiling else None
        
        # Check cache if enabled
        if self.context_cache is not None:
            cache_key = hash(text)
            if cache_key in self.context_cache:
                self.cache_hits += 1
                if self.config.debug_logging:
                    logger.debug(f"Context cache hit for: '{text[:50]}...'")
                
                # Record cache hit time if profiling enabled
                if start_time is not None:
                    elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms
                    if self.config.debug_logging:
                        logger.debug(f"Context detection time (cache hit): {elapsed:.3f}ms")
                
                return self.context_cache[cache_key]
            else:
                self.cache_misses += 1
        
        step_times = {} if self.config.performance_profiling else None
        
        # Step 1: Check for Sanskrit whitelist override
        step_start = time.perf_counter() if step_times is not None else None
        
        if self.config.enable_whitelist_override:
            whitelist_result = self._check_sanskrit_whitelist_override(text)
            if whitelist_result is not None:
                if step_times is not None:
                    step_times['whitelist_override'] = (time.perf_counter() - step_start) * 1000
                
                if self.config.debug_logging:
                    logger.debug(f"Sanskrit whitelist override triggered: {whitelist_result.markers_found}")
                    if step_times:
                        logger.debug(f"Context detection time (whitelist): {sum(step_times.values()):.3f}ms")
                
                self._cache_result(text, whitelist_result)
                return whitelist_result
        
        if step_times is not None:
            step_times['whitelist_check'] = (time.perf_counter() - step_start) * 1000

        # Step 1.5: Check for specialized content types (invocations, corrupted Sanskrit)
        step_start = time.perf_counter() if step_times is not None else None

        specialized_result = self._check_specialized_content(text)
        if specialized_result is not None:
            if step_times is not None:
                step_times['specialized_content'] = (time.perf_counter() - step_start) * 1000

            if self.config.debug_logging:
                logger.debug(f"Specialized content detected: {specialized_result.context_type}")

            self._cache_result(text, specialized_result)
            return specialized_result

        if step_times is not None:
            step_times['specialized_check'] = (time.perf_counter() - step_start) * 1000

        # Step 2: Fast English Protection (with configurable threshold)
        step_start = time.perf_counter() if step_times is not None else None
        
        english_result = self.is_pure_english(text)
        
        if step_times is not None:
            step_times['english_detection'] = (time.perf_counter() - step_start) * 1000
        
        if english_result.confidence >= self.config.english_threshold:
            if self.config.debug_logging:
                logger.debug(f"English context detected (confidence: {english_result.confidence:.2f}): {english_result.markers_found}")
                if step_times:
                    total_time = sum(step_times.values())
                    logger.debug(f"Context detection time (English): {total_time:.3f}ms (breakdown: {step_times})")
            
            self._cache_result(text, english_result)
            return english_result
        
        # Step 3: Fast Sanskrit Acceptance (with configurable threshold)
        step_start = time.perf_counter() if step_times is not None else None
        
        sanskrit_result = self.has_sanskrit_markers(text)
        
        if step_times is not None:
            step_times['sanskrit_detection'] = (time.perf_counter() - step_start) * 1000
        
        if sanskrit_result.confidence >= self.config.sanskrit_threshold:
            if self.config.debug_logging:
                logger.debug(f"Sanskrit context detected (confidence: {sanskrit_result.confidence:.2f}): {sanskrit_result.markers_found}")
                if step_times:
                    total_time = sum(step_times.values())
                    logger.debug(f"Context detection time (Sanskrit): {total_time:.3f}ms (breakdown: {step_times})")
            
            self._cache_result(text, sanskrit_result)
            return sanskrit_result
        
        # Step 4: Single word Sanskrit handling
        step_start = time.perf_counter() if step_times is not None else None
        
        words = text.strip().split()
        if len(words) == 1:
            word_lower = words[0].lower()
            if (word_lower in self.sanskrit_sacred_set or 
                any(char in words[0] for char in self.sanskrit_diacriticals_set) or
                word_lower in self.sanskrit_priority_set):
                
                result = ContextResult('sanskrit', 0.8, markers_found=['single_sanskrit_word'])
                
                if step_times is not None:
                    step_times['single_word_check'] = (time.perf_counter() - step_start) * 1000
                
                if self.config.debug_logging:
                    logger.debug(f"Single Sanskrit word detected: '{word_lower}'")
                    if step_times:
                        total_time = sum(step_times.values())
                        logger.debug(f"Context detection time (single word): {total_time:.3f}ms")
                
                self._cache_result(text, result)
                return result
        
        if step_times is not None:
            step_times['single_word_check'] = (time.perf_counter() - step_start) * 1000
        
        # Step 5: Mixed Content Analysis
        step_start = time.perf_counter() if step_times is not None else None
        
        mixed_result = self.analyze_mixed_content(text)
        
        if step_times is not None:
            step_times['mixed_analysis'] = (time.perf_counter() - step_start) * 1000
        
        if self.config.debug_logging:
            logger.debug(f"Mixed content analysis result (confidence: {mixed_result.confidence:.2f}): {mixed_result.markers_found}")
            if step_times:
                total_time = sum(step_times.values())
                logger.debug(f"Context detection time (mixed): {total_time:.3f}ms (breakdown: {step_times})")
                
                # Performance analysis
                if total_time > 10:  # Warn if taking more than 10ms
                    logger.warning(f"Context detection slow ({total_time:.3f}ms) for text: '{text[:50]}...'")
                    slowest_step = max(step_times.items(), key=lambda x: x[1])
                    logger.warning(f"Slowest step: {slowest_step[0]} ({slowest_step[1]:.3f}ms)")
        
        self._cache_result(text, mixed_result)
        return mixed_result
    
    def _check_sanskrit_whitelist_override(self, text: str) -> 'ContextResult':
        """Check if text contains Sanskrit priority terms that should override context detection.

        ENHANCED: Improved logic for scripture processing - allows more Sanskrit content through
        while maintaining protection against mistranslations.

        Args:
            text: Input text to check

        Returns:
            ContextResult with Sanskrit context if override applies, None otherwise
        """
        text_lower = text.lower()
        words = text_lower.split()

        # Count Sanskrit priority terms AND scripture database terms
        found_priority_terms = []
        found_scripture_terms = []
        sanskrit_word_count = 0

        for word in words:
            # Check priority terms first (highest precedence)
            if word in self.sanskrit_priority_set:
                found_priority_terms.append(word)
                sanskrit_word_count += 1
            # ENHANCEMENT: Also check comprehensive scripture database
            elif word in self.scripture_terms:
                found_scripture_terms.append(word)
                sanskrit_word_count += 1

        # Check for compound phrases in scripture database
        found_compounds = []
        compound_phrases = [key for key in self.scripture_terms.keys() if ' ' in key]
        for compound_key in compound_phrases:
            if compound_key in text_lower:
                found_compounds.append(compound_key)
                # Don't double-count if individual words were already found
                compound_words = compound_key.split()
                new_sanskrit_words = sum(1 for w in compound_words if w not in found_priority_terms and w not in found_scripture_terms)
                sanskrit_word_count += new_sanskrit_words

        # Check for ASR variations
        found_variations = []
        for variation, correct_term in self.asr_variations.items():
            if variation.lower() in text_lower:
                found_variations.append(f"{variation}→{correct_term}")
                if variation.lower() not in found_priority_terms:
                    found_priority_terms.append(variation.lower())
                    sanskrit_word_count += 1

        if found_priority_terms or found_scripture_terms or found_compounds:
            # ENHANCED: Much more permissive logic for scripture processing
            if len(words) > 0:
                # Calculate Sanskrit term ratio
                sanskrit_ratio = sanskrit_word_count / len(words)

                # Count English function words
                english_function_count = sum(1 for w in words if w in self.english_function_set)

                # Detect clear English commentary patterns (more specific than before)
                english_commentary_patterns = [
                    'chapter entitled to', 'very short prayer', 'and great personalities',
                    'according to shankaracharya', 'following prayer', 'this is explained',
                    'commentary on the', 'meaning of this verse', 'translation of the'
                ]
                has_strong_commentary = any(pattern in text_lower for pattern in english_commentary_patterns)

                # Detect English sentence structure (stricter patterns)
                strong_english_patterns = [
                    'this is the', 'which is the', 'and the great', 'very short prayer to',
                    'according to the great', 'commentary explains that'
                ]
                has_strong_english_structure = any(pattern in text_lower for pattern in strong_english_patterns)

                # NEW: Detect corrupted Sanskrit that should be processed
                corrupted_sanskrit_indicators = [
                    'yey che dhabhyasu', 'sarva jnanavi moor', 'nashtana che tashaar',
                    'evam pravartitam chakram', 'paartha sa jeevati',
                    'om vahudevo sutam devam', 'kansa chan uram ardanam'
                ]
                has_corrupted_sanskrit = any(indicator in text_lower for indicator in corrupted_sanskrit_indicators)

                # NEW: Detect verses and prayers that should always be processed
                verse_prayer_indicators = [
                    'om ', 'oṃ ', 'krishna', 'kṛṣṇa', 'arjuna', 'bhagavad gita', 'dharma', 'karma',
                    'namaha', 'namaḥ', 'vande', 'vandana', 'guru', 'brahma', 'vishnu', 'shiva'
                ]
                has_verse_prayer_content = any(indicator in text_lower for indicator in verse_prayer_indicators)

                # CRITICAL IMPROVEMENT: Only block if it's clearly English commentary 
                # AND doesn't contain corrupted Sanskrit or verses
                if (sanskrit_ratio < 0.25 and  # Very low Sanskrit ratio (reduced from 0.35)
                    english_function_count >= 3 and  # Many English function words (increased from 2)
                    (has_strong_commentary or has_strong_english_structure) and  # Strong English patterns
                    not has_corrupted_sanskrit and  # No corrupted Sanskrit detected
                    not has_verse_prayer_content):  # No verses or prayers detected

                    # This is clearly English commentary - don't override
                    if self.config.debug_logging:
                        logger.debug(f"Smart whitelist: Clear English commentary detected, not overriding to Sanskrit. "
                                   f"Sanskrit ratio: {sanskrit_ratio:.2f}, English functions: {english_function_count}, "
                                   f"Strong patterns: {has_strong_commentary or has_strong_english_structure}, "
                                   f"Sanskrit terms: {found_priority_terms[:3]}")
                    return None

                # ENHANCEMENT: For borderline cases, check for specific Sanskrit content
                if sanskrit_ratio < 0.4 and english_function_count >= 2:
                    # Borderline case - check for specific scripture/verse content
                    scripture_content_patterns = [
                        'gita', 'verse', 'sloka', 'chapter', 'yoga', 'dharma', 'karma', 'moksha',
                        'sanskrit', 'transliteration', 'prayer', 'invocation', 'mantra'
                    ]
                    has_scripture_content = any(pattern in text_lower for pattern in scripture_content_patterns)
                    
                    if not has_scripture_content and not has_corrupted_sanskrit:
                        # Borderline English text without clear scripture content
                        if self.config.debug_logging:
                            logger.debug(f"Smart whitelist: Borderline case without scripture content, not overriding. "
                                       f"Sanskrit ratio: {sanskrit_ratio:.2f}, terms: {found_priority_terms[:3]}")
                        return None

            # Apply Sanskrit override - this text should be processed for Sanskrit corrections
            markers_found = [f'priority_term_{term}' for term in found_priority_terms[:3]]
            # ENHANCEMENT: Include scripture database matches in markers
            markers_found.extend([f'scripture_term_{term}' for term in found_scripture_terms[:3]])
            markers_found.extend([f'scripture_compound_{compound}' for compound in found_compounds[:2]])
            if found_variations:
                markers_found.extend([f'asr_variation_{var}' for var in found_variations[:2]])

            if self.config.debug_logging:
                logger.debug(f"Sanskrit whitelist override applied: {markers_found}")

            return ContextResult(
                context_type='sanskrit',
                confidence=self.config.whitelist_override_threshold,
                markers_found=markers_found,
                override_reason='sanskrit_whitelist'
            )

        return None
    
    def _cache_result(self, text: str, result: 'ContextResult') -> None:
        """Cache context detection result if caching is enabled."""
        if self.context_cache is not None:
            cache_key = hash(text)
            self.context_cache[cache_key] = result
            
            # Limit cache size to prevent memory issues
            if len(self.context_cache) > 1000:
                # Remove oldest 20% of entries
                items_to_remove = len(self.context_cache) // 5
                keys_to_remove = list(self.context_cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self.context_cache[key]
    
    def is_pure_english(self, text: str) -> 'ContextResult':
        """
        Enhanced English detection with configurable thresholds.
        
        Returns high confidence for text that should pass through unchanged.
        """
        text_lower = text.lower()
        if self.pattern_manager:
            words = self.pattern_manager.extract_words_fast(text_lower)
        else:
            words = re.findall(r'\b\w+\b', text_lower)
        
        if not words:
            return ContextResult('english', 0.5, markers_found=['no_words'])
        
        markers_found = []
        score = 0
        
        # Check for pure ASCII
        is_ascii = all(ord(char) < 128 for char in text)
        if is_ascii:
            score += 0.3
            markers_found.append('pure_ascii')
        
        # Count English function words using optimized set lookup
        function_word_count = sum(1 for word in words if word in self.english_function_set)
        
        if function_word_count >= self.config.english_markers_required:
            score += 0.4
            markers_found.append(f'function_words_{function_word_count}')
        
        # Check for English patterns
        modal_patterns = ['was ', 'were ', 'is ', 'are ']
        for pattern in modal_patterns:
            if pattern in text_lower:
                score += 0.2
                markers_found.append(f'modal_pattern_{pattern.strip()}')
        
        # Check for progressive tense
        if any(word.endswith('ing') for word in words):
            score += 0.2
            markers_found.append('progressive_tense')
        
        # Check for past tense
        if any(word.endswith('ed') for word in words):
            score += 0.2
            markers_found.append('past_tense')
        
        # English sentence patterns
        if re.search(r'\b(he|she|they|it)\s+(was|were|is|are)\b', text_lower):
            score += 0.3
            markers_found.append('english_sentence_pattern')
        
        return ContextResult('english', min(score, 1.0), markers_found=markers_found)
    
    def has_sanskrit_markers(self, text: str) -> 'ContextResult':
        """
        Enhanced Sanskrit detection with configurable thresholds.
        
        Returns high confidence for text that should be fully processed.
        """
        markers_found = []
        score = 0
        
        # Count Sanskrit diacriticals using optimized set lookup
        diacritical_chars = [char for char in text if char in self.sanskrit_diacriticals_set]
        if diacritical_chars:
            # Calculate diacritical density
            total_chars = len([c for c in text if c.isalpha()])
            if total_chars > 0:
                density = len(diacritical_chars) / total_chars
                if density > self.config.diacritical_density_high:
                    score += 0.6
                    markers_found.append(f'high_diacritical_density_{density:.2f}')
                elif density > self.config.diacritical_density_medium:
                    score += 0.3
                    markers_found.append(f'medium_diacritical_density_{density:.2f}')
        
        # Check for Sanskrit sacred terms using optimized set lookup
        text_lower = text.lower()
        if self.pattern_manager:
            words = self.pattern_manager.extract_words_fast(text_lower)
        else:
            words = re.findall(r'\b\w+\b', text_lower)
        
        sanskrit_terms = [word for word in words if word in self.sanskrit_sacred_set]
        if sanskrit_terms:
            score += 0.4
            markers_found.extend([f'sanskrit_term_{term}' for term in sanskrit_terms[:3]])
        
        # Check for Sanskrit suffixes
        common_suffixes = ['āya', 'aya', 'āni', 'ani', 'asya', 'ānām', 'anam']
        for word in words:
            for suffix in common_suffixes:
                if word.endswith(suffix):
                    score += 0.2
                    markers_found.append(f'sanskrit_suffix_{suffix}')
                    break
        
        # Check for specific Sanskrit phrases using optimized patterns
        if self.pattern_manager:
            if (self.pattern_manager.search_with_pattern('sanskrit_om', text) or 
                self.pattern_manager.search_with_pattern('sanskrit_phrase', text)):
                score += 0.5
                markers_found.append('sanskrit_phrase_pattern')
        else:
            if re.search(r'oṁ\s+namaḥ|bhagavad\s+gītā|śrī\s+\w+', text, re.IGNORECASE):
                score += 0.5
                markers_found.append('sanskrit_phrase_pattern')
        
        return ContextResult('sanskrit', min(score, 1.0), markers_found=markers_found)
    
    def analyze_mixed_content(self, text: str) -> 'ContextResult':
        """
        Enhanced mixed content analysis with configurable processing.
        
        Returns segment boundaries for selective processing.
        """
        if self.pattern_manager:
            # Use optimized word extraction
            words = text.split()  # Simple split is faster for mixed content
        else:
            words = re.findall(r'\S+', text)  # Include punctuation
        word_contexts = []
        
        for word in words:
            # Clean word for analysis (remove punctuation)
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if not clean_word:
                word_contexts.append('neutral')
                continue
            
            # Check priority terms first (highest precedence)
            if clean_word in self.sanskrit_priority_set:
                word_contexts.append('sanskrit')
            # Check if word is clearly English
            elif clean_word in self.english_function_set:
                word_contexts.append('english')
            # Check for Sanskrit diacriticals
            elif any(char in word for char in self.sanskrit_diacriticals_set):
                word_contexts.append('sanskrit')
            # Check sacred terms
            elif clean_word in self.sanskrit_sacred_set:
                word_contexts.append('sanskrit')
            else:
                word_contexts.append('neutral')
        
        # Find Sanskrit segments (consecutive Sanskrit/neutral words)
        segments = []
        current_segment_start = None
        current_segment_type = None
        
        for i, (word, context) in enumerate(zip(words, word_contexts)):
            if context == 'sanskrit':
                if current_segment_type != 'sanskrit':
                    # Start new Sanskrit segment
                    current_segment_start = i
                    current_segment_type = 'sanskrit'
            elif context == 'english':
                if current_segment_type == 'sanskrit':
                    # End Sanskrit segment
                    segments.append((current_segment_start, i, 'sanskrit'))
                    current_segment_start = None
                    current_segment_type = None
            # 'neutral' words continue current segment
        
        # Close final segment if needed
        if current_segment_type == 'sanskrit':
            segments.append((current_segment_start, len(words), 'sanskrit'))
        
        # Determine overall context with enhanced logic
        sanskrit_words = sum(1 for ctx in word_contexts if ctx == 'sanskrit')
        english_words = sum(1 for ctx in word_contexts if ctx == 'english')
        neutral_words = sum(1 for ctx in word_contexts if ctx == 'neutral')
        
        # Enhanced context determination based on configurable thresholds
        total_words = len(words)
        sanskrit_ratio = sanskrit_words / total_words if total_words > 0 else 0
        english_ratio = english_words / total_words if total_words > 0 else 0
        
        if sanskrit_words > 0 and english_words > 0:
            # Mixed content - check if it meets mixed threshold
            if sanskrit_ratio >= self.config.mixed_threshold:
                overall_context = 'mixed'
            elif english_ratio >= self.config.english_threshold:
                overall_context = 'english'
            else:
                overall_context = 'mixed'
        elif sanskrit_words > 0 and english_words == 0:
            overall_context = 'sanskrit'
        elif english_words > 0 and sanskrit_words == 0:
            overall_context = 'english'
        else:
            # No clear indicators, default based on neutral content
            overall_context = 'mixed' if neutral_words > 0 else 'english'
        
        markers_found = [f'segments_{len(segments)}', f'sanskrit_words_{sanskrit_words}', 
                        f'english_words_{english_words}', f'ratios_s{sanskrit_ratio:.2f}_e{english_ratio:.2f}']
        
        # Adjust confidence based on segment clarity
        confidence = 0.7
        if overall_context == 'mixed' and len(segments) > 0:
            confidence = 0.8  # Higher confidence if we found clear segments
        elif overall_context in ['sanskrit', 'english'] and max(sanskrit_ratio, english_ratio) > 0.8:
            confidence = 0.9  # Very high confidence for clear contexts
        
        return ContextResult(
            overall_context, 
            confidence,
            segments=segments,
            markers_found=markers_found
        )
    
    def should_process_segment(self, text: str, start_idx: int, end_idx: int) -> bool:
        """
        Enhanced segment processing decision with priority term support.
        
        Args:
            text: Full text
            start_idx: Start word index
            end_idx: End word index
            
        Returns:
            True if segment should be processed for Sanskrit corrections
        """
        words = re.findall(r'\S+', text)
        segment_words = words[start_idx:end_idx]
        segment_text = ' '.join(segment_words)
        segment_lower = segment_text.lower()
        
        # Check for priority terms first
        if any(term in segment_lower for term in self.sanskrit_priority_set):
            return True
        
        # Quick Sanskrit marker check with optimized set lookup
        has_diacriticals = any(char in segment_text for char in self.sanskrit_diacriticals_set)
        has_sanskrit_terms = any(word.lower() in self.sanskrit_sacred_set for word in segment_words)
        
        return has_diacriticals or has_sanskrit_terms

    def _check_specialized_content(self, text: str) -> Optional['ContextResult']:
        """Check for specialized content types that need specific handling."""

        # CRITICAL FIX: Check for language tags FIRST - force Sanskrit processing
        language_tag_patterns = [
            r'^\s*\[SA\]',   # Sanskrit tag at beginning
            r'^\s*\[HI\]',   # Hindi tag at beginning  
            r'^\s*\[SANSKRIT\]',  # Full Sanskrit tag
            r'^\s*\[HINDI\]'      # Full Hindi tag
        ]
        
        has_language_tag = any(re.search(pattern, text, re.IGNORECASE) for pattern in language_tag_patterns)
        
        if has_language_tag:
            # Force Sanskrit processing for tagged content
            return ContextResult(
                context_type='sanskrit',
                confidence=1.0,
                markers_found=['language_tag_override'],
                override_reason='Language tag forces Sanskrit processing'
            )

        # Check for scripture titles in commentary FIRST (before Sanskrit detection)
        scripture_commentary_patterns = [
            r'\b(Shrimad|Srimad)\s+Bhagavad\s+Gita\b.*\b(Chapter|entitled|Yoga)\b',
            r'\bBhagavad\s+Gita\b.*\b(Chapter|in\s+Chapter|entitled)\b',
            r'\b(Chapter\s+\d+|entitled)\b.*\b(Karma\s+Yoga|Yoga\s+of)\b'
        ]
        
        has_scripture_commentary = any(re.search(pattern, text, re.IGNORECASE) for pattern in scripture_commentary_patterns)
        
        if has_scripture_commentary:
            return ContextResult(
                context_type='mixed',
                confidence=0.95,
                markers_found=['scripture_title_commentary'],
                processing_mode='embedded_correction',
                embedded_terms=['scripture_title']
            )

        # Check for invocations/prayers
        invocation_result = self._detect_invocation(text)
        if invocation_result:
            return invocation_result

        # Check for corrupted Sanskrit that needs surgical editing
        corrupted_result = self._detect_corrupted_sanskrit(text)
        if corrupted_result:
            return corrupted_result

        # Check for mixed content with embedded Sanskrit terms
        mixed_result = self._detect_mixed_content_with_embedded_terms(text)
        if mixed_result:
            return mixed_result

        return None

    def _detect_invocation(self, text: str) -> Optional['ContextResult']:
        """Detect Sanskrit invocations and prayers."""
        invocation_indicators = []

        # Check each invocation pattern
        for pattern_name, pattern in self.invocation_patterns.items():
            if pattern.search(text):
                invocation_indicators.append(f'invocation_{pattern_name}')

        # Count divine names
        divine_name_count = len(self.invocation_patterns['divine_sequence'].findall(text))

        if invocation_indicators or divine_name_count >= 3:
            return ContextResult(
                context_type='invocation',
                confidence=0.95 if divine_name_count >= 3 else 0.8,
                markers_found=invocation_indicators + [f'divine_names_{divine_name_count}'],
                processing_mode='invocation_format'
            )

        return None

    def _detect_corrupted_sanskrit(self, text: str) -> Optional['ContextResult']:
        """Detect corrupted Sanskrit that needs surgical editing."""
        corrupted_indicators = []

        for pattern_name, pattern in self.corrupted_sanskrit_patterns.items():
            if pattern.search(text):
                corrupted_indicators.append(f'corrupted_{pattern_name}')

        if corrupted_indicators:
            return ContextResult(
                context_type='corrupted_sanskrit',
                confidence=0.9,
                markers_found=corrupted_indicators,
                processing_mode='surgical_edit'
            )

        return None

    def _detect_mixed_content_with_embedded_terms(self, text: str) -> Optional['ContextResult']:
        """Detect mixed content with embedded Sanskrit terms."""
        # Check for English sentence structure
        english_indicators = ['the ', 'and ', 'is ', 'are ', 'that ', 'which ', 'to ', 'in ', 'of ', 'with']
        english_count = sum(1 for indicator in english_indicators if indicator in text.lower())

        # Special case: Scripture titles in commentary
        scripture_commentary_patterns = [
            r'\b(Shrimad|Srimad)\s+Bhagavad\s+Gita\b.*\b(Chapter|entitled|Yoga)\b',
            r'\bBhagavad\s+Gita\b.*\b(Chapter|in\s+Chapter|entitled)\b',
            r'\b(Chapter\s+\d+|entitled)\b.*\b(Karma\s+Yoga|Yoga\s+of)\b'
        ]
        
        has_scripture_commentary = any(re.search(pattern, text, re.IGNORECASE) for pattern in scripture_commentary_patterns)
        
        if has_scripture_commentary:
            return ContextResult(
                context_type='mixed',
                confidence=0.9,
                markers_found=[f'english_structure_{english_count}', 'scripture_title_commentary'],
                processing_mode='embedded_correction',
                embedded_terms=['scripture_title']
            )

        # Names in commentary patterns
        names_in_commentary_patterns = [
            r'\b(Shankaracharya|Shankara)\b.*\b(and|personalities|in)\b',
            r'\b(great\s+personalities|according\s+to)\b'
        ]
        
        has_names_commentary = any(re.search(pattern, text, re.IGNORECASE) for pattern in names_in_commentary_patterns)
        
        if has_names_commentary and english_count >= 1:
            return ContextResult(
                context_type='mixed',
                confidence=0.8,
                markers_found=[f'english_structure_{english_count}', 'names_in_commentary'],
                processing_mode='embedded_correction',
                embedded_terms=['sacred_names']
            )

        if english_count < 2:
            return None  # Not English commentary

        # Find embedded Sanskrit terms
        embedded_terms = []
        for category, pattern in self.embedded_term_patterns.items():
            matches = pattern.findall(text)
            embedded_terms.extend([f'{category}_{match}' for match in matches])

        if embedded_terms:
            return ContextResult(
                context_type='mixed',
                confidence=0.8,
                markers_found=[f'english_structure_{english_count}'] + embedded_terms[:5],
                processing_mode='embedded_correction',
                embedded_terms=embedded_terms
            )

        return None

    def get_performance_stats(self) -> dict:
        """Get comprehensive performance statistics for context detection."""
        stats = {}
        
        # Cache statistics
        if self.context_cache is not None:
            total_requests = self.cache_hits + self.cache_misses
            stats['cache'] = {
                'enabled': True,
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': self.cache_hits / total_requests if total_requests > 0 else 0,
                'cache_size': len(self.context_cache),
                'total_requests': total_requests
            }
        else:
            stats['cache'] = {'enabled': False}
        
        # Performance cache statistics
        if self.perf_cache is not None:
            perf_stats = self.perf_cache.get_performance_stats()
            hit_rates = self.perf_cache.get_hit_rates()
            stats['performance_cache'] = {
                'context_detection_hit_rate': hit_rates.get('context_detection', 0.0),
                'memory_usage_mb': perf_stats.get('memory_usage', {}).get('context_cache_mb', 0.0),
                'time_saved_ms': perf_stats.get('context_detection', {}).get('total_time_saved_ms', 0.0)
            }
        
        # Configuration statistics
        stats['configuration'] = {
            'english_threshold': self.config.english_threshold,
            'sanskrit_threshold': self.config.sanskrit_threshold,
            'mixed_threshold': self.config.mixed_threshold,
            'whitelist_override_enabled': self.config.enable_whitelist_override,
            'priority_terms_count': len(self.sanskrit_priority_set),
            'function_words_count': len(self.english_function_set),
            'sacred_terms_count': len(self.sanskrit_sacred_set),
            'diacriticals_count': len(self.sanskrit_diacriticals_set)
        }
        
        # Performance recommendations
        recommendations = []
        
        if self.context_cache is not None:
            hit_rate = stats['cache']['hit_rate']
            if hit_rate < 0.3:
                recommendations.append("Low cache hit rate - consider enabling caching or reviewing text patterns")
            elif hit_rate > 0.8:
                recommendations.append("Excellent cache performance - context detection is highly optimized")
        else:
            recommendations.append("Caching disabled - enable caching for better performance on repeated text")
        
        # Memory usage estimation
        if self.context_cache is not None:
            # Rough estimate: each cache entry ~100 bytes on average
            estimated_cache_memory = len(self.context_cache) * 100 / 1024  # KB
            stats['memory'] = {
                'estimated_cache_kb': estimated_cache_memory,
                'optimization_sets_kb': (
                    len(self.sanskrit_priority_set) * 50 +  # Rough string size estimation
                    len(self.english_function_set) * 20 +
                    len(self.sanskrit_sacred_set) * 40 +
                    len(self.sanskrit_diacriticals_set) * 10
                ) / 1024
            }
        
        # Configuration optimization recommendations
        if self.config.english_threshold < 0.5:
            recommendations.append("English threshold very low - may cause over-processing of English text")
        elif self.config.english_threshold > 0.9:
            recommendations.append("English threshold very high - may miss English content protection")
        
        if self.config.sanskrit_threshold < 0.4:
            recommendations.append("Sanskrit threshold very low - may over-detect Sanskrit content")
        elif self.config.sanskrit_threshold > 0.8:
            recommendations.append("Sanskrit threshold very high - may miss valid Sanskrit content")
        
        stats['recommendations'] = recommendations
        
        return stats