#!/usr/bin/env python3
"""
ASR-Specific Sanskrit Processor
Implements aggressive correction mode for ASR transcription errors
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, Set, List

from enhanced_processor import EnhancedSanskritProcessor
from processors.context_detector import ContextDetector
from sanskrit_processor_v2 import ProcessingResult

logger = logging.getLogger(__name__)

class ASRProcessor(EnhancedSanskritProcessor):
    """ASR-specific processor with aggressive correction capabilities."""
    
    def __init__(self, lexicon_dir: Path = None, config_path: Path = None):
        """Initialize ASR processor with specialized settings."""
        super().__init__(lexicon_dir, config_path)
        
        # Load Sanskrit whitelist for English protection bypass
        self.sanskrit_whitelist = self._load_sanskrit_whitelist()
        
        # Compile regex patterns for performance
        self._compiled_patterns = self._compile_whitelist_patterns()
        
        # ASR-specific configuration
        self.asr_config = self.config.get('processing', {}).get('asr_settings', {
            'english_protection_threshold': 0.8,
            'case_sensitive_matching': False,
            'sanskrit_whitelist_override': True,
            'minimum_correction_target': 25,
            'aggressive_compound_matching': True
        })
        
        # Override context detector with ASR-specific thresholds
        self.context_detector = ASRContextDetector(
            english_threshold=self.asr_config.get('english_protection_threshold', 0.8)
        )
        
        logger.info(f"ASR processor initialized with {len(self.sanskrit_whitelist)} whitelisted terms")
    
    def _load_sanskrit_whitelist(self) -> Set[str]:
        """Load Sanskrit terms that should bypass English protection with optimized performance."""
        import time
        start_time = time.time()
        
        whitelist = set()
        
        # Performance optimization: Use a single YAML import at the top
        import yaml
        
        # Load from lexicons with optimized file handling
        try:
            lexicon_files = [
                (Path(self.lexicon_dir) / 'corrections.yaml', 'corrections'),
                (Path(self.lexicon_dir) / 'proper_nouns.yaml', 'proper_nouns')
            ]
            
            # Batch process files for better I/O performance
            for file_path, file_type in lexicon_files:
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f) or {}
                            # Optimized bulk set operations instead of individual adds
                            if isinstance(data, dict):
                                whitelist.update(key.lower() for key in data.keys())
                                logger.debug(f"Loaded {len(data)} terms from {file_type}")
                            else:
                                logger.warning(f"Unexpected data format in {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load {file_type} from {file_path}: {e}")
            
            logger.debug(f"Loaded {len(whitelist)} terms from lexicons into Sanskrit whitelist")
            
        except Exception as e:
            logger.warning(f"Failed to load Sanskrit whitelist from lexicons: {e}")
        
        # Performance optimization: Use bulk update for common ASR errors
        common_asr_errors = frozenset({  # frozenset is faster for membership tests
            'yogabashi', 'shivashistha', 'malagrasth', 'jnana', 'gita', 'yoga', 'dharma',
            'karma', 'moksha', 'samsara', 'ahimsa', 'tapas', 'sadhana', 'guru', 'mantra',
            'yantra', 'tantra', 'chakra', 'kundalini', 'prana', 'asana', 'pranayama',
            'meditation', 'samadhi', 'nirvana', 'enlightenment', 'consciousness',
            'atman', 'brahman', 'ishvara', 'bhakti', 'devotion', 'surrender',
            # Additional high-frequency ASR error patterns
            'krishna', 'rama', 'shiva', 'vishnu', 'brahma', 'shakti', 'devi',
            'ganesh', 'hanuman', 'arjuna', 'pandava', 'kaurava', 'mahabharata',
            'ramayana', 'vedas', 'upanishads', 'puranas', 'sutras', 'tantras'
        })
        whitelist.update(common_asr_errors)
        
        load_time = time.time() - start_time
        logger.debug(f"Sanskrit whitelist loaded in {load_time:.3f}s with {len(whitelist)} total terms")
        
        # Performance verification: Log if loading is taking too long
        if load_time > 0.1:  # More than 100ms
            logger.warning(f"Sanskrit whitelist loading took {load_time:.3f}s - consider lexicon optimization")
        
        return whitelist
    
    def _compile_whitelist_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile regex patterns for performance optimization."""
        patterns = {}
        for term in self.sanskrit_whitelist:
            try:
                patterns[term] = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            except re.error:
                logger.debug(f"Failed to compile pattern for term: {term}")
        return patterns
    
    def process_text(self, text: str, context: Dict = None) -> tuple[str, int]:
        """ASR-specific text processing with aggressive corrections and detailed metrics."""
        if not text or not text.strip():
            return text, 0
        
        import time
        start_time = time.time()
        
        processed_text = text
        total_corrections = 0
        asr_metrics = {}
        
        # ASR Mode: Modified context detection with whitelist override
        context_start = time.time()
        context_result = self.context_detector.detect_context(text)
        asr_metrics['context_detection_time'] = time.time() - context_start
        asr_metrics['context_type'] = context_result.context_type
        asr_metrics['context_confidence'] = context_result.confidence
        
        logger.debug(f"ASR context detected: {context_result.context_type} (confidence: {context_result.confidence:.2f})")
        
        # Check for Sanskrit whitelist terms to override English protection
        whitelist_start = time.time()
        whitelist_matches = []
        if self.asr_config.get('sanskrit_whitelist_override', True):
            for term, pattern in self._compiled_patterns.items():
                if pattern.search(text):
                    whitelist_matches.append(term)
                    break  # Found at least one match, that's enough
            
            if whitelist_matches:
                logger.debug(f"Sanskrit whitelist override: found {whitelist_matches[:3]}...")  # Limit logging
                # Force Sanskrit processing even in English context
                context_result.context_type = 'sanskrit'
        
        asr_metrics['whitelist_check_time'] = time.time() - whitelist_start
        asr_metrics['whitelist_matches'] = len(whitelist_matches)
        asr_metrics['english_protection_bypassed'] = len(whitelist_matches) > 0
        
        # Handle different context types with ASR-specific logic
        if context_result.context_type == 'english' and not self.asr_config.get('sanskrit_whitelist_override', True):
            # Pure English context without whitelist override
            logger.debug("Pure English context detected, bypassing processing")
            asr_metrics['processing_path'] = 'english_bypass'
            asr_metrics['total_processing_time'] = time.time() - start_time
            return text, 0
        
        elif context_result.context_type == 'mixed' or context_result.context_type == 'english':
            # Mixed content or English with Sanskrit terms: Apply aggressive processing
            logger.debug("Mixed/English with Sanskrit terms: applying aggressive processing")
            asr_metrics['processing_path'] = 'mixed_aggressive'
            processed_text, corrections = self._process_asr_segment(text, context, asr_metrics)
            total_corrections = corrections
        
        elif context_result.context_type == 'sanskrit':
            # Sanskrit context: Full aggressive processing
            logger.debug("Sanskrit context detected, applying full ASR processing")
            asr_metrics['processing_path'] = 'sanskrit_full'
            processed_text, corrections = self._process_asr_segment(text, context, asr_metrics)
            total_corrections = corrections
        
        else:
            # Unknown context: Default to aggressive processing in ASR mode
            logger.debug(f"Unknown context type: {context_result.context_type}, applying ASR processing")
            asr_metrics['processing_path'] = 'unknown_aggressive'
            processed_text, corrections = self._process_asr_segment(text, context, asr_metrics)
            total_corrections = corrections
        
        asr_metrics['total_processing_time'] = time.time() - start_time
        asr_metrics['total_corrections'] = total_corrections
        asr_metrics['correction_rate'] = (total_corrections / len(text.split())) * 100 if text.split() else 0
        
        # Store metrics in context for potential reporting
        if context is None:
            context = {}
        context['asr_metrics'] = asr_metrics
        
        return processed_text, total_corrections
    
    def _process_asr_segment(self, text: str, context: Dict = None, asr_metrics: Dict = None) -> tuple[str, int]:
        """Process text segment with ASR-specific aggressive corrections and detailed metrics."""
        import time
        
        processed_text = text
        total_corrections = 0
        if asr_metrics is None:
            asr_metrics = {}
        
        step_times = {}
        
        # Step 1: Case-insensitive lexicon matching
        step_start = time.time()
        case_corrections = 0
        if not self.asr_config.get('case_sensitive_matching', False):
            case_corrected_text, case_corrections = self._apply_case_insensitive_corrections(processed_text)
            processed_text = case_corrected_text
            total_corrections += case_corrections
        step_times['case_insensitive_matching'] = time.time() - step_start
        
        # Step 2: Systematic term matching with aggressive settings
        step_start = time.time()
        systematic_corrections = 0
        if self.systematic_matcher:
            try:
                systematic_text, systematic_corrections_list = self.systematic_matcher.apply_corrections(
                    processed_text, aggressive_mode=True
                )
                if systematic_corrections_list:
                    processed_text = systematic_text
                    systematic_corrections = len(systematic_corrections_list)
                    total_corrections += systematic_corrections
                    logger.debug(f"Applied {systematic_corrections} aggressive systematic corrections")
            except Exception as e:
                logger.debug(f"Aggressive systematic matching failed: {e}")
        step_times['systematic_matching'] = time.time() - step_start
        
        # Step 3: Aggressive compound matching
        step_start = time.time()
        compound_corrections = 0
        if self.asr_config.get('aggressive_compound_matching', True) and self.compound_processor:
            try:
                compound_candidates = self.compound_processor.find_compound_candidates(
                    processed_text, aggressive=True
                )
                for original, corrected in compound_candidates:
                    if original != corrected:
                        # Use case-insensitive replacement for ASR
                        pattern = re.compile(re.escape(original), re.IGNORECASE)
                        if pattern.search(processed_text):
                            processed_text = pattern.sub(corrected, processed_text)
                            compound_corrections += 1
                            total_corrections += 1
                            logger.debug(f"Applied aggressive compound correction: {original} → {corrected}")
            except Exception as e:
                logger.debug(f"Aggressive compound processing failed: {e}")
        step_times['compound_matching'] = time.time() - step_start
        
        # Step 4: Base lexicon processing with case-insensitive matching
        step_start = time.time()
        base_text, base_corrections = self._apply_base_lexicon_asr(processed_text)
        processed_text = base_text
        total_corrections += base_corrections
        step_times['base_lexicon'] = time.time() - step_start
        
        # Step 5: Prayer recognition (unchanged from parent)
        step_start = time.time()
        prayer_corrections = 0
        if self.prayer_recognizer:
            try:
                prayer_match = self.prayer_recognizer.recognize_prayer(processed_text)
                if prayer_match and prayer_match.confidence > 0.6:  # Lower threshold for ASR
                    processed_text = prayer_match.corrected_text
                    prayer_corrections = 1
                    total_corrections += 1
                    logger.debug(f"Applied ASR prayer correction: {prayer_match.prayer_name}")
            except Exception as e:
                logger.debug(f"ASR prayer recognition failed: {e}")
        step_times['prayer_recognition'] = time.time() - step_start
        
        # Step 6: External services (if available, same as parent but with lower thresholds)
        step_start = time.time()
        external_corrections = 0
        if self.config.get('processing', {}).get('enable_semantic_analysis', True):
            try:
                enhanced_text = None
                if self.external_services:
                    enhanced_text = self.external_services.mcp_enhance_segment(processed_text)
                elif self.external_clients and self.external_clients.mcp_client:
                    enhanced_text = self.external_clients.mcp_client.context_correct(
                        processed_text, context.get('previous_text') if context else None
                    )
                
                if enhanced_text and enhanced_text != processed_text:
                    processed_text = enhanced_text
                    external_corrections = 1
                    total_corrections += 1
                    logger.debug("Applied MCP enhancement in ASR mode")
            except Exception as e:
                logger.debug(f"MCP enhancement failed in ASR mode: {e}")
        step_times['external_services'] = time.time() - step_start
        
        # Store detailed step metrics
        asr_metrics['step_breakdown'] = {
            'case_corrections': case_corrections,
            'systematic_corrections': systematic_corrections,
            'compound_corrections': compound_corrections,
            'base_corrections': base_corrections,
            'prayer_corrections': prayer_corrections,
            'external_corrections': external_corrections,
            'step_times': step_times,
            'total_step_time': sum(step_times.values())
        }
        
        return processed_text, total_corrections
    
    def _apply_case_insensitive_corrections(self, text: str) -> tuple[str, int]:
        """Apply lexicon corrections with case-insensitive matching."""
        corrections = 0
        processed_text = text
        
        try:
            # Get corrections from base processor
            for lexicon_name, lexicon_data in self.lexicons.items():
                if not lexicon_data:
                    continue
                    
                for original, corrected in lexicon_data.items():
                    if isinstance(corrected, str):
                        # Case-insensitive pattern matching
                        pattern = re.compile(r'\b' + re.escape(original) + r'\b', re.IGNORECASE)
                        if pattern.search(processed_text):
                            processed_text = pattern.sub(corrected, processed_text)
                            corrections += 1
                            logger.debug(f"Applied case-insensitive correction: {original} → {corrected}")
                    elif isinstance(corrected, list):
                        # Handle variations
                        for variant in corrected:
                            pattern = re.compile(r'\b' + re.escape(original) + r'\b', re.IGNORECASE)
                            if pattern.search(processed_text):
                                processed_text = pattern.sub(variant, processed_text)
                                corrections += 1
                                logger.debug(f"Applied case-insensitive variant: {original} → {variant}")
                                break
        
        except Exception as e:
            logger.debug(f"Case-insensitive corrections failed: {e}")
        
        return processed_text, corrections
    
    def _apply_base_lexicon_asr(self, text: str) -> tuple[str, int]:
        """Apply base lexicon with ASR-specific settings."""
        # Use parent's process_text but capture corrections differently
        base_text, base_corrections = super(EnhancedSanskritProcessor, self).process_text(text)
        return base_text, base_corrections

class ASRContextDetector(ContextDetector):
    """ASR-specific context detector with adjusted thresholds."""
    
    def __init__(self, english_threshold: float = 0.8):
        super().__init__()
        self.english_threshold = english_threshold
    
    def detect_context(self, text: str):
        """Detect context with ASR-specific thresholds."""
        result = super().detect_context(text)
        
        # Adjust thresholds for ASR processing
        if result.context_type == 'english' and result.confidence < self.english_threshold:
            # Lower confidence English detection should be treated as mixed
            result.context_type = 'mixed'
            logger.debug(f"ASR: Converted English to mixed context (confidence {result.confidence:.2f} < {self.english_threshold})")
        
        return result