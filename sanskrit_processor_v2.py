#!/usr/bin/env python3
"""
Lean Sanskrit SRT Processor - Focused implementation
No bloat, no over-engineering, just working text processing.
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
import logging

# Import utilities for lean architecture
from utils.srt_parser import SRTParser, SRTSegment
# Import exceptions for enhanced error handling
from exceptions import FileError, ProcessingError, ConfigurationError
from utils.metrics_collector import MetricsCollector, CorrectionDetail
from utils.processing_reporter import ProcessingReporter, ProcessingResult, DetailedProcessingResult
from utils.smart_cache import LexiconCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SRTSegment now imported from utils.srt_parser

# ProcessingResult now imported from utils.processing_reporter

# CorrectionDetail now imported from utils.metrics_collector

# DetailedProcessingResult now imported from utils.processing_reporter

# MetricsCollector now imported from utils.metrics_collector

# ProcessingReporter now imported from utils.processing_reporter

class LexiconLoader:
    """Simple lexicon loader for YAML files."""
    
    def __init__(self, lexicon_dir: Path):
        self.lexicon_dir = Path(lexicon_dir)
        self.corrections = {}
        self.proper_nouns = {}
        self._load_lexicons()
    
    def _load_lexicons(self):
        """Load correction lexicons from YAML files."""
        try:
            # Load corrections
            corrections_file = self.lexicon_dir / "corrections.yaml"
            if corrections_file.exists():
                try:
                    with open(corrections_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        for entry in data.get('entries', []):
                            original = entry['original_term']
                            self.corrections[original] = entry
                            # Add variations
                            for variation in entry.get('variations', []):
                                self.corrections[variation] = entry
                    logger.info(f"Loaded {len(self.corrections)} correction entries")
                except yaml.YAMLError as e:
                    raise FileError(
                        f"Invalid YAML format in corrections file: {e}",
                        file_path=str(corrections_file),
                        file_operation="read",
                        suggestions=[
                            "Check YAML syntax with a validator",
                            "Ensure proper indentation and formatting",
                            "Restore from backup if corrupted"
                        ]
                    )
                except KeyError as e:
                    raise FileError(
                        f"Missing required field {e} in corrections file",
                        file_path=str(corrections_file),
                        file_operation="read",
                        suggestions=[
                            "Ensure all entries have 'original_term' field",
                            "Check corrections.yaml format against documentation"
                        ]
                    )
            else:
                logger.warning(f"Corrections file not found: {corrections_file}")
            
            # Load proper nouns
            proper_nouns_file = self.lexicon_dir / "proper_nouns.yaml"
            if proper_nouns_file.exists():
                try:
                    with open(proper_nouns_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        for entry in data.get('entries', []):
                            # Handle both 'term' and 'original_term' formats
                            term = entry.get('term') or entry.get('original_term')
                            if term:
                                self.proper_nouns[term.lower()] = entry
                                # Add variations if they exist
                                for variation in entry.get('variations', []):
                                    self.proper_nouns[variation.lower()] = entry
                    logger.info(f"Loaded {len(self.proper_nouns)} proper noun entries")
                except yaml.YAMLError as e:
                    raise FileError(
                        f"Invalid YAML format in proper nouns file: {e}",
                        file_path=str(proper_nouns_file),
                        file_operation="read",
                        suggestions=[
                            "Check YAML syntax with a validator", 
                            "Ensure proper indentation and formatting"
                        ]
                    )
            else:
                logger.warning(f"Proper nouns file not found: {proper_nouns_file}")
                        
        except FileNotFoundError as e:
            raise FileError(
                f"Lexicon directory or file not found: {e}",
                file_path=str(self.lexicon_dir),
                file_operation="read", 
                suggestions=[
                    "Ensure lexicons directory exists in project root",
                    "Create missing lexicon files from templates",
                    "Check file permissions"
                ]
            )
        except Exception as e:
            # Re-raise our custom errors, wrap others
            if isinstance(e, FileError):
                raise
            logger.error(f"Failed to load lexicons: {e}")
            raise FileError(
                f"Unexpected error loading lexicons: {e}",
                file_path=str(self.lexicon_dir),
                file_operation="read",
                suggestions=[
                    "Check lexicon files for corruption",
                    "Verify file permissions and encoding",
                    "Use --verbose flag for detailed error information"
                ]
            )

# SRTParser now imported from utils.srt_parser

class SanskritProcessor:
    """Lean Sanskrit text processor focused on core functionality."""
    
    def __init__(self, lexicon_dir: Path = None, config_path: Path = None, collect_metrics: bool = False):
        """Initialize processor with lexicon directory and configuration."""
        self.lexicon_dir = lexicon_dir or Path("lexicons")
        
        # Load configuration first (needed for database setup)
        self.config = self._load_config(config_path or Path("config.yaml"))
        
        # Use hybrid lexicon loader for database + YAML integration
        try:
            from lexicons.hybrid_lexicon_loader import HybridLexiconLoader
            self.lexicons = HybridLexiconLoader(self.lexicon_dir, self.config)
            logger.info("Using hybrid lexicon loader (database + YAML)")
        except ImportError:
            # Fallback to original loader if hybrid not available
            self.lexicons = LexiconLoader(self.lexicon_dir)
            logger.info("Using YAML-only lexicon loader (fallback)")
        
        # Initialize smart caching
        self.lexicon_cache = LexiconCache(self.config)
        
        # Initialize compound matcher (Story 6.1)
        from utils.compound_matcher import CompoundTermMatcher
        compounds_path = self.lexicon_dir / "compounds.yaml"
        self.compound_matcher = CompoundTermMatcher(compounds_path) if compounds_path.exists() else None
        
        # Initialize sacred text components (Story 6.2)
        from processors.sacred_classifier import SacredContentClassifier
        from processors.symbol_protector import SacredSymbolProtector
        from processors.verse_formatter import VerseFormatter
        
        self.sacred_classifier = SacredContentClassifier()
        self.symbol_protector = SacredSymbolProtector()
        self.verse_formatter = VerseFormatter()
        
        # Initialize context-aware pipeline (Story 6.5)
        try:
            from processors.context_pipeline import ContextAwarePipeline
            self.context_pipeline = ContextAwarePipeline(self.config)
            self.use_context_pipeline = True
            logger.info("Context-aware pipeline initialized")
        except ImportError as e:
            logger.warning(f"Context-aware pipeline not available: {e}")
            self.context_pipeline = None
            self.use_context_pipeline = False
        
        # Initialize quality assurance components (Story 6.6)
        try:
            from qa.confidence_scorer import ConfidenceScorer
            from qa.issue_detector import QualityIssueDetector
            self.confidence_scorer = ConfidenceScorer(self.config)
            self.issue_detector = QualityIssueDetector()
            self.qa_enabled = self.config.get('qa', {}).get('enabled', False)
            if self.qa_enabled:
                logger.info("Quality assurance system enabled")
            else:
                logger.debug("Quality assurance system initialized but disabled")
        except ImportError as e:
            logger.warning(f"Quality assurance system not available: {e}")
            self.confidence_scorer = None
            self.issue_detector = None
            self.qa_enabled = False
        
        # Metrics collection
        self.collect_metrics = collect_metrics
        self.metrics_collector = MetricsCollector() if collect_metrics else None
        
        # Initialize plugin system (lean implementation)
        from utils.plugin_manager import PluginManager
        self.plugin_manager = PluginManager()
        if self.config.get('plugins', {}).get('enabled', False):
            self.plugin_manager.enable()
            self._load_plugins()
        
        # Basic text normalization patterns
        self.filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know']
        self.number_words = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
            'sixteen': '16', 'seventeen': '17', 'eighteen': '18'
        }
        
        logger.info("Sanskrit processor initialized with context-aware processing")

    
    def _load_config(self, config_path: Path) -> dict:
        """Load configuration using advanced ConfigManager with environment support and fallback."""
        config = {}
        
        try:
            # Try advanced configuration management first
            from utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_config()
            logger.info(f"Advanced configuration loaded for environment: {config_manager.environment}")
            
        except (FileNotFoundError, ImportError) as e:
            # Fallback to legacy single config file loading
            logger.debug(f"Advanced config loading failed ({e}), trying legacy loading")
            
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    logger.info(f"Legacy configuration loaded from {config_path}")
                else:
                    logger.info("Config file not found, using defaults")
                    
            except yaml.YAMLError as e:
                raise ConfigurationError(
                    f"Invalid YAML syntax in configuration file: {e}",
                    config_file=str(config_path),
                    suggestions=[
                        "Check YAML syntax with a validator",
                        "Ensure proper indentation and quotes",
                        "Compare with config.yaml template"
                    ]
                )
            except PermissionError as e:
                raise ConfigurationError(
                    f"Permission denied reading config file: {e}",
                    config_file=str(config_path),
                    suggestions=[
                        "Check file permissions on config file",
                        "Run with appropriate user permissions"
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to load config, using defaults: {e}")
                # Continue with defaults rather than failing completely
                
        except Exception as e:
            # Log the error but don't fail completely
            logger.warning(f"Configuration loading error: {e}")
            # Try legacy loading as final fallback
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                    logger.info(f"Final fallback: loaded config from {config_path}")
            except Exception:
                pass  # Use empty config as ultimate fallback
            
        # Set fuzzy matching defaults if not present
        if 'processing' not in config:
            config['processing'] = {}
        if 'fuzzy_matching' not in config['processing']:
            config['processing']['fuzzy_matching'] = {
                'enabled': True,
                'threshold': 0.7,
                'log_matches': False
            }
        
        # Validate critical configuration values
        fuzzy_config = config['processing']['fuzzy_matching']
        threshold = fuzzy_config.get('threshold', 0.7)
        if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
            raise ConfigurationError(
                f"Invalid fuzzy matching threshold: {threshold}",
                config_file=str(config_path) if config_path else "unknown",
                config_section="processing.fuzzy_matching",
                suggestions=[
                    "Set threshold to value between 0.0 and 1.0",
                    "Use 0.7 for balanced accuracy/coverage", 
                    "Use 0.9 for high precision, 0.5 for high recall"
                ]
            )
            
        return config
    
    def _load_plugins(self):
        """Load plugins from configuration (lean implementation)."""
        try:
            import importlib
            plugin_config = self.config.get('plugins', {})
            enabled_plugins = plugin_config.get('enabled_plugins', [])
            
            for plugin_name in enabled_plugins:
                try:
                    module = importlib.import_module(f'plugins.{plugin_name}')
                    # Look for plugin function (convention: plugin_name + '_plugin')
                    plugin_func_name = f'{plugin_name}_plugin'
                    if hasattr(module, plugin_func_name):
                        plugin_func = getattr(module, plugin_func_name)
                        self.plugin_manager.register(plugin_name, plugin_func)
                        logger.info(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin {plugin_name}: {e}")
        except Exception as e:
            logger.warning(f"Plugin loading failed: {e}")
    
    def process_text(self, text: str) -> tuple[str, int]:
        """Process a single text segment with context-aware processing. Returns (processed_text, corrections_made)."""
        # Use context-aware pipeline if available (Story 6.5)
        if self.use_context_pipeline and self.context_pipeline:
            try:
                result = self.context_pipeline.process_segment(text)
                return result.processed_text, result.corrections_made
            except Exception as e:
                logger.warning(f"Context pipeline failed, falling back to legacy processing: {e}")
        
        # Fallback to legacy processing pipeline
        return self._legacy_process_text(text)
    
    def process_segment_detailed(self, segment) -> 'ProcessingResult':
        """
        New method providing detailed processing results with context information.
        Returns comprehensive processing result from context-aware pipeline.
        """
        if self.use_context_pipeline and self.context_pipeline:
            from processors.context_pipeline import ProcessingResult as ContextProcessingResult
            
            # Use the context-aware pipeline for detailed results
            result = self.context_pipeline.process_segment(segment.text)
            
            # Convert to the format expected by the existing system
            # Note: We import from context_pipeline to avoid conflicts
            return result
        else:
            # Fallback to basic processing
            processed_text, corrections = self._legacy_process_text(segment.text)
            
            # Create a basic ProcessingResult (import from utils.processing_reporter)
            from utils.processing_reporter import ProcessingResult
            return ProcessingResult(
                segments_processed=1,
                corrections_made=corrections,
                processing_time=0.0,
                errors=[]
            )
    
    def _legacy_process_text(self, text: str) -> tuple[str, int]:
        """Legacy processing pipeline (pre-Story 6.5) for fallback."""
        original_text = text
        corrections = 0
        
        # 1. Classify content type for sacred text handling
        content_type = self.sacred_classifier.classify_content(text)
        
        if content_type in ['mantra', 'verse', 'prayer']:
            # Sacred content processing pipeline
            logger.debug(f"Sacred content detected: {content_type}")
            
            # 1. Protect sacred symbols before processing
            protected_text, restoration_map = self.symbol_protector.protect_symbols(text)
            
            # 2. Apply standard corrections to protected text
            protected_text = self._normalize_text(protected_text)
            protected_text, lexicon_corrections = self._apply_lexicon_corrections(protected_text)
            corrections += lexicon_corrections
            protected_text, capitalization_corrections = self._apply_capitalization(protected_text)
            corrections += capitalization_corrections
            
            # 3. Apply verse formatting
            formatted_text = self.verse_formatter.process_verse(protected_text, content_type)
            
            # 4. Restore sacred symbols
            final_text = self.symbol_protector.restore_symbols(formatted_text, restoration_map)
            
            # 5. Apply plugins (lean implementation)
            final_text = self.plugin_manager.execute_all(final_text)
            
            text = final_text
        else:
            # Regular text processing (existing pipeline)
            # 1. Basic text cleanup
            text = self._normalize_text(text)
            
            # 2. Apply lexicon corrections
            text, lexicon_corrections = self._apply_lexicon_corrections(text)
            corrections += lexicon_corrections
            
            # 3. Apply proper noun capitalization
            text, capitalization_corrections = self._apply_capitalization(text)
            corrections += capitalization_corrections
            
            # 4. Clean up extra whitespace (preserve line breaks)
            text = re.sub(r'[ \\t]+', ' ', text).strip()
            
            # 5. Apply plugins (lean implementation)
            text = self.plugin_manager.execute_all(text)
        
        if text != original_text:
            logger.debug(f"Processed ({content_type}): '{original_text[:50]}...' -> '{text[:50]}...' ({corrections} corrections)")
            
        return text, corrections
    
    def _normalize_text(self, text: str) -> str:
        """Basic text normalization with punctuation enhancement."""
        # Remove excessive whitespace (preserve line breaks)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Convert number words to digits
        for word, digit in self.number_words.items():
            text = re.sub(rf'\b{re.escape(word)}\b', digit, text, flags=re.IGNORECASE)
        
        # Remove common filler words
        for filler in self.filler_words:
            text = re.sub(rf'\b{re.escape(filler)}\b', '', text, flags=re.IGNORECASE)
        
        # Apply punctuation enhancement if enabled
        if self.config.get('punctuation', {}).get('enabled', False):
            text = self._enhance_punctuation(text)
        
        return text.strip()

    def _enhance_punctuation(self, text: str) -> str:
        """Simplified punctuation enhancement for lean architecture."""
        if self._is_sanskrit_context(text):
            return text
        
        # Basic punctuation fixes only
        endings = ["thank you", "namaste", "om shanti"]
        for phrase in endings:
            if text.lower().rstrip().endswith(phrase.lower()):
                if not text.rstrip().endswith('.'):
                    text = text.rstrip() + '.'
                break
        
        # Basic question detection
        if any(text.lower().strip().startswith(q) for q in ['what', 'how', 'why', 'when']):
            if not text.rstrip().endswith('?'):
                text = text.rstrip() + '?'
        
        # Clean spacing (preserve line breaks)
        text = re.sub(r'[ \t]+([.,:;!?])', r'\1', text)
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        return text

    def detect_context(self, text: str) -> str:
        """Detect content context: 'sanskrit', 'english', or 'mixed'.
        
        Enhanced with input validation and caching for optimal performance.
        """
        # Input validation for robustness
        if not text or not isinstance(text, str):
            return 'mixed'  # Default to mixed for safety
            
        # Normalize whitespace for consistent processing
        normalized_text = ' '.join(text.split())
        if not normalized_text.strip():
            return 'mixed'
        
        # Check cache for performance optimization
        cache_key = hash(normalized_text)
        if hasattr(self, '_context_cache') and cache_key in self._context_cache:
            return self._context_cache[cache_key]
        
        # Initialize cache if needed
        if not hasattr(self, '_context_cache'):
            self._context_cache = {}
        
        sanskrit_score = self.calculate_sanskrit_density(normalized_text)
        confidence_config = self.config.get('processing', {}).get('context_detection', {})
        
        # Validate and constrain thresholds for reliability
        high_threshold = max(0.5, min(0.9, confidence_config.get('sanskrit_threshold', 0.7)))
        low_threshold = max(0.1, min(0.5, confidence_config.get('english_threshold', 0.3)))
        
        # Ensure thresholds are logically consistent
        if low_threshold >= high_threshold:
            low_threshold = high_threshold - 0.2
            
        if sanskrit_score > high_threshold:
            result = 'sanskrit'
        elif sanskrit_score < low_threshold:
            result = 'english'
        else:
            result = 'mixed'
            
        # Cache result for future lookups (limit cache size)
        if len(self._context_cache) < 1000:
            self._context_cache[cache_key] = result
            
        return result
    
    def calculate_sanskrit_density(self, text: str) -> float:
        """Calculate the density of Sanskrit indicators in text."""
        if not text.strip():
            return 0.0
        
        score = 0.0
        text_lower = text.lower()
        
        # Sanskrit Context Indicators (higher weights)
        if text_lower.startswith('om ') or ' om ' in text_lower:
            score += 0.4
        
        # IAST diacritical marks
        iast_chars = 'āīūṛṅṇṭḍṣśḥṃ'
        iast_count = sum(1 for char in text if char in iast_chars)
        if len(text) > 0:
            score += min(0.3, iast_count / len(text) * 10)  # Cap at 0.3
        
        # Verse number references (e.g., "2.41", "4.7") 
        verse_refs = len(re.findall(r'\d+\.\d+', text))
        score += min(0.2, verse_refs * 0.1)
        
        # Sanskrit terms density
        words = text.lower().split()
        sanskrit_word_count = 0
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.lexicons.corrections or clean_word in self.lexicons.proper_nouns:
                sanskrit_word_count += 1
        
        if len(words) > 0:
            sanskrit_word_ratio = sanskrit_word_count / len(words)
            score += min(0.4, sanskrit_word_ratio)
        
        # English Context Indicators (reduce score)
        english_indicators = [
            r'\b(means?|refers?\s+to|explains?|this|that|what|how|why|when)\b',
            r'\b(chapter|section|verse|explains?|teaching)\b',
            r'\?$',  # Question ending
        ]
        
        for pattern in english_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                score -= 0.15
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def _is_sanskrit_context(self, text: str) -> bool:
        """Check if text contains Sanskrit/sacred content that should be preserved."""
        context = self.detect_context(text)
        return context in ['sanskrit', 'mixed']
    
    def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
        """Apply corrections from lexicon files with compound matching and fuzzy matching fallback."""
        corrections = 0
        
        # 1. First pass: Compound term recognition (Story 6.1)
        if self.compound_matcher:
            text, compound_matches = self.compound_matcher.process_text(text)
            corrections += len(compound_matches)
            if compound_matches:
                logger.debug(f"Compound corrections: {len(compound_matches)}")
        
        # 2. Second pass: Individual word corrections (context-aware and preserve line structure)
        lines = text.split('\n')
        corrected_lines = []
        
        # Detect context for the entire text
        text_context = self.detect_context(text)
        
        # Get confidence threshold from config
        confidence_config = self.config.get('processing', {}).get('context_detection', {})
        confidence_threshold = confidence_config.get('confidence_threshold', 0.8)
        
        logger.debug(f"Text context detected: {text_context} (confidence threshold: {confidence_threshold})")
        
        for line in lines:
            words = line.split()
            corrected_words = []
            
            for word in words:
                # Process word with context-aware punctuation preservation
                corrected_word = self._process_word_with_punctuation(word, text_context, confidence_threshold)
                corrected_words.append(corrected_word)
                if corrected_word != word:
                    corrections += 1
                    logger.debug(f"Context-aware correction ({text_context}): {word} -> {corrected_word}")
            
            corrected_lines.append(' '.join(corrected_words))
        
        return '\n'.join(corrected_lines), corrections
    
    def _process_word_with_punctuation(self, word: str, context: str = None, confidence_threshold: float = 0.8) -> str:
        """Process word while preserving punctuation and respecting context.
        
        Enhanced with comprehensive edge case handling and validation.
        """
        # Input validation for robustness
        if not word or not isinstance(word, str):
            return word or ''
            
        # Handle empty or whitespace-only words
        if not word.strip():
            return word
            
        # Handle special cases: pure punctuation, numbers, single characters
        if not re.search(r'\w', word):
            return word  # Pure punctuation or symbols
        if word.isdigit():
            return word  # Pure numbers
        if len(word.strip()) == 1:
            return word  # Single characters
            
        # Extract leading/trailing punctuation with enhanced pattern
        # Handle complex punctuation like quotes, ellipsis, multiple punctuation
        match = re.match(r'^(\W*?)(\w+(?:\'\w+)*?)(\W*?)$', word)
        if not match:
            return word  # Fallback for complex cases
        
        prefix, clean_word, suffix = match.groups()
        
        # Handle contractions and possessives properly
        if "'" in clean_word:
            # For contractions like "don't" or possessives like "Krishna's"
            parts = clean_word.split("'")
            if len(parts) == 2 and parts[1].lower() in ['t', 's', 'd', 're', 've', 'll']:
                clean_word = parts[0]  # Process base word only
                suffix = "'" + parts[1] + suffix
        
        clean_lower = clean_word.lower()
        
        # Validate context parameter
        if context not in ['english', 'sanskrit', 'mixed', None]:
            context = 'mixed'  # Default to mixed for invalid context
            
        # Validate confidence threshold
        confidence_threshold = max(0.1, min(1.0, confidence_threshold))
        
        corrections_file = self.lexicon_dir / "corrections.yaml"
        corrected = clean_word  # Default to no change
        
        try:
            # Context-aware processing with enhanced error handling
            if context == 'english':
                # In English context, be very conservative with corrections
                # Only correct if it's a clear Sanskrit proper noun
                if hasattr(self.lexicons, 'proper_nouns') and clean_lower in self.lexicons.proper_nouns:
                    entry = self.lexicons.proper_nouns[clean_lower]
                    if isinstance(entry, dict):
                        corrected = entry.get('term', clean_word)
                    else:
                        corrected = str(entry) if entry else clean_word
                else:
                    corrected = clean_word  # No correction in English context
            elif context == 'sanskrit':
                # In Sanskrit context, apply all corrections aggressively
                corrected = self._get_best_correction(clean_lower, corrections_file, confidence_threshold)
            else:  # mixed context or None
                # In mixed context, apply corrections with higher confidence threshold
                adjusted_threshold = min(0.9, confidence_threshold + 0.1)
                corrected = self._get_best_correction(clean_lower, corrections_file, adjusted_threshold)
        except Exception as e:
            # Graceful error handling - log and return original
            logger.warning(f"Error processing word '{clean_word}': {e}")
            corrected = clean_word
        
        # If no correction found, keep original
        if corrected == clean_lower or not corrected:
            corrected = clean_word
        
        # Preserve capitalization pattern intelligently
        if clean_word and corrected:
            if clean_word.isupper():
                corrected = corrected.upper()
            elif clean_word[0].isupper():
                corrected = corrected.capitalize()
            elif clean_word.islower():
                corrected = corrected.lower()
        
        # Reconstruct word with preserved punctuation
        result = prefix + corrected + suffix
        
        # Final validation - ensure result is reasonable
        if not result or len(result) > len(word) * 3:  # Prevent unreasonable expansion
            return word
            
        return result
    
    def _get_best_correction(self, clean_lower: str, corrections_file, confidence_threshold: float) -> str:
        """Get best correction for a word with confidence filtering."""
        # Try cache first
        cached_correction = self.lexicon_cache.get_correction(clean_lower, corrections_file)
        if cached_correction is not None:
            return cached_correction
        
        # Try exact match in lexicon
        if clean_lower in self.lexicons.corrections:
            entry = self.lexicons.corrections[clean_lower]
            use_diacritics = self.config.get('processing', {}).get('use_iast_diacritics', False)
            if use_diacritics and 'transliteration' in entry:
                corrected = entry['transliteration']
            else:
                corrected = entry['original_term']
            # Cache the result
            self.lexicon_cache.cache_correction(clean_lower, corrected, corrections_file)
            return corrected
        
        # Try fuzzy match if enabled and confidence is high enough
        fuzzy_config = self.config.get('processing', {}).get('fuzzy_matching', {})
        if fuzzy_config.get('enabled', True):
            fuzzy_match = self._find_fuzzy_match(clean_lower, max(confidence_threshold, fuzzy_config.get('threshold', 0.8)))
            if fuzzy_match:
                self.lexicon_cache.cache_correction(clean_lower, fuzzy_match, corrections_file)
                return fuzzy_match
        
        return clean_lower  # No suitable correction found
    
    def _apply_capitalization(self, text: str) -> tuple[str, int]:
        """Apply proper noun capitalization."""
        corrections = 0
        lines = text.split('\n')
        corrected_lines = []
        
        proper_nouns_file = self.lexicon_dir / "proper_nouns.yaml"
        
        for line in lines:
            words = line.split()
            corrected_words = []
            
            for word in words:
                clean_word = re.sub(r'[^\w\s]', '', word.lower())
                
                # Try cache first
                cached_proper_noun = self.lexicon_cache.get_proper_noun(clean_word, proper_nouns_file)
                if cached_proper_noun is not None:
                    # Record metrics if collecting
                    if self.metrics_collector:
                        self.metrics_collector.start_correction('capitalization', word)
                        self.metrics_collector.end_correction('capitalization', word, cached_proper_noun, 1.0)
                    
                    corrected_words.append(cached_proper_noun)
                    corrections += 1
                    logger.debug(f"Cached capitalization: {word} -> {cached_proper_noun}")
                    continue
                
                # Try lexicon lookup
                if clean_word in self.lexicons.proper_nouns:
                    entry = self.lexicons.proper_nouns[clean_word]
                    corrected = entry.get('term') or entry.get('original_term', word)
                    
                    # Cache the result
                    self.lexicon_cache.cache_proper_noun(clean_word, corrected, proper_nouns_file)
                    
                    # Record metrics if collecting
                    if self.metrics_collector:
                        self.metrics_collector.start_correction('capitalization', word)
                        self.metrics_collector.end_correction('capitalization', word, corrected, 1.0)
                    
                    corrected_words.append(corrected)
                    corrections += 1
                    logger.debug(f"Capitalization: {word} -> {corrected}")
                else:
                    # Cache negative result (no capitalization needed)
                    self.lexicon_cache.cache_proper_noun(clean_word, word, proper_nouns_file)
                    corrected_words.append(word)
            
            corrected_lines.append(' '.join(corrected_words))
        
        return '\n'.join(corrected_lines), corrections

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Simple character similarity for lean architecture."""
        if not str1 or not str2:
            return 0.0
        
        s1, s2 = str1.lower().strip(), str2.lower().strip()
        if s1 == s2:
            return 1.0
        
        # Simple character overlap ratio
        common = sum(1 for a, b in zip(s1, s2) if a == b)
        return common / max(len(s1), len(s2))

    def _find_fuzzy_match(self, word: str, threshold: float = 0.8) -> Optional[str]:
        """
        Find the best fuzzy match for a word in the lexicon.
        Returns the corrected term if similarity > threshold, None otherwise.
        """
        if not word or not self.lexicons.corrections:
            return None
            
        best_match = None
        best_similarity = 0.0
        
        for lexicon_term, entry in self.lexicons.corrections.items():
            similarity = self._calculate_similarity(word, lexicon_term)
            if similarity > threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = entry['original_term']
                
        return best_match
    
    def process_srt_file(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> ProcessingResult:
        """Process an SRT file with Sanskrit corrections and comprehensive metrics."""
        import time
        start_time = time.time()
        
        # Convert strings to Path objects for consistent handling
        input_path = Path(input_path) if isinstance(input_path, str) else input_path
        output_path = Path(output_path) if isinstance(output_path, str) else output_path
        
        logger.info(f"Processing SRT file: {input_path} -> {output_path}")
        
        # Initialize enhanced metrics collection
        if self.collect_metrics and self.metrics_collector:
            self.metrics_collector.start_processing(
                file_path=str(input_path), 
                mode=getattr(self, 'processing_mode', 'standard')
            )
            self.metrics_collector.start_phase('parsing')
        
        try:
            # Validate input file exists
            if not input_path.exists():
                raise FileError(
                    f"Input SRT file not found: {input_path}",
                    file_path=str(input_path),
                    file_operation="read",
                    suggestions=[
                        "Check the input file path is correct",
                        "Ensure the file hasn't been moved or deleted",
                        "Use absolute paths to avoid confusion"
                    ]
                )
            
            # Read and parse phase
            parse_start = time.time()
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except PermissionError as e:
                raise FileError(
                    f"Permission denied reading input file: {e}",
                    file_path=str(input_path),
                    file_operation="read",
                    suggestions=[
                        "Check file permissions",
                        "Run with appropriate user permissions",
                        "Ensure file is not locked by another process"
                    ]
                )
            except UnicodeDecodeError as e:
                raise FileError(
                    f"Invalid UTF-8 encoding in input file: {e}",
                    file_path=str(input_path),
                    file_operation="read",
                    suggestions=[
                        "Ensure SRT file is saved with UTF-8 encoding",
                        "Convert file encoding to UTF-8",
                        "Check for special characters causing encoding issues"
                    ]
                )
            
            segments = SRTParser.parse(content)
            if not segments:
                raise ProcessingError(
                    "No valid SRT segments found in file",
                    file_path=str(input_path),
                    processing_stage="parsing",
                    suggestions=[
                        "Check SRT file format (index, timestamp, text structure)",
                        "Ensure file contains properly formatted segments",
                        "Verify timestamps are in correct format (HH:MM:SS,mmm)"
                    ]
                )
            
            # End parsing phase and start processing
            if self.collect_metrics and self.metrics_collector:
                self.metrics_collector.end_phase('parsing')
                self.metrics_collector.start_phase('processing')
            
            parse_time = time.time() - parse_start
            logger.info(f"Parsed {len(segments)} segments")
            
            # Processing phase with enhanced metrics
            process_start = time.time()
            total_corrections = 0
            processing_errors = []
            
            for i, segment in enumerate(segments, 1):
                try:
                    processed_text, corrections = self.process_text(segment.text)
                    segment.text = processed_text
                    total_corrections += corrections
                    
                    # Record cache performance if available
                    if self.collect_metrics and hasattr(self, 'lexicon_cache'):
                        # This is a placeholder - actual cache hits would be tracked in the correction methods
                        pass
                        
                except Exception as e:
                    # Log but continue processing other segments
                    error_msg = f"Failed to process segment {i}: {e}"
                    processing_errors.append(error_msg)
                    logger.warning(error_msg)
            
            # End processing phase and start writing
            if self.collect_metrics and self.metrics_collector:
                self.metrics_collector.end_phase('processing')
                self.metrics_collector.start_phase('writing')
            
            process_time = time.time() - process_start
            
            # Writing phase
            write_start = time.time()
            try:
                output_content = SRTParser.to_srt(segments)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                    
            except PermissionError as e:
                raise FileError(
                    f"Permission denied writing output file: {e}",
                    file_path=str(output_path),
                    file_operation="write",
                    suggestions=[
                        "Check output directory permissions",
                        "Ensure output directory exists",
                        "Run with appropriate user permissions"
                    ]
                )
            except OSError as e:
                raise FileError(
                    f"Failed to write output file: {e}",
                    file_path=str(output_path),
                    file_operation="write",
                    suggestions=[
                        "Check available disk space",
                        "Verify output path is valid",
                        "Ensure output directory is writable"
                    ]
                )
            
            # Complete metrics collection
            if self.collect_metrics and self.metrics_collector:
                self.metrics_collector.end_phase('writing')
                self.metrics_collector.finish_processing(len(segments))
            
            write_time = time.time() - write_start
            processing_time = time.time() - start_time
            
            # Create appropriate result type with enhanced metrics
            if self.collect_metrics and self.metrics_collector:
                # Get performance metrics
                performance_metrics = self.metrics_collector.get_performance_metrics()
                
                # Calculate quality score
                quality_score = self.metrics_collector.calculate_quality_score(len(segments), len(processing_errors))
                
                result = DetailedProcessingResult(
                    segments_processed=len(segments),
                    corrections_made=total_corrections,
                    processing_time=processing_time,
                    errors=processing_errors,
                    corrections_by_type=self.metrics_collector.corrections_by_type.copy(),
                    correction_details=self.metrics_collector.correction_details.copy(),
                    confidence_scores=self.metrics_collector.confidence_scores.copy(),
                    processing_phases=self.metrics_collector.processing_phases.copy(),
                    quality_score=quality_score,
                    memory_usage=performance_metrics.get('memory_usage', {})
                )
            else:
                result = ProcessingResult(
                    segments_processed=len(segments),
                    corrections_made=total_corrections,
                    processing_time=processing_time,
                    errors=processing_errors
                )
            
            logger.info(f"Processing complete: {len(segments)} segments, "
                       f"{total_corrections} corrections, {processing_time:.2f}s")
            
            return result
            
        except (FileError, ProcessingError, ConfigurationError) as e:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            logger.error(f"Processing failed: {e}")
            raise ProcessingError(
                f"Unexpected processing error: {e}",
                file_path=str(input_path),
                processing_stage="general",
                suggestions=[
                    "Use --verbose flag for detailed error information",
                    "Check input file format and encoding",
                    "Report this error if it persists"
                ]
            )

    def process_srt_with_qa(self, srt_content: str, filename: str = "processed_file") -> tuple[str, dict]:
        """Process SRT with quality assurance reporting."""
        from utils.srt_parser import SRTParser
        import time
        
        segments = SRTParser.parse(srt_content)
        processed_segments = []
        confidence_scores = []
        all_issues = []
        
        for segment in segments:
            # Process segment with context-aware pipeline
            if self.use_context_pipeline and self.context_pipeline:
                result = self.context_pipeline.process_segment(segment.text)
            else:
                # Fallback to legacy processing
                processed_text, corrections = self._legacy_process_text(segment.text)
                from utils.processing_reporter import ProcessingResult
                result = ProcessingResult(
                    segments_processed=1,
                    corrections_made=corrections,
                    processing_time=0.0,
                    errors=[]
                )
                result.processed_text = processed_text
            
            # Generate confidence metrics and quality issues
            if self.qa_enabled and self.confidence_scorer and self.issue_detector:
                confidence = self.confidence_scorer.calculate_confidence(result)
                issues = self.issue_detector.detect_issues(segment, confidence)
                
                confidence_scores.append(confidence)
                all_issues.extend(issues)
            
            # Create processed segment
            processed_segments.append(type(segment)(
                index=segment.index,
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=result.processed_text if hasattr(result, 'processed_text') else segment.text
            ))
        
        # Generate SRT output
        output_srt = SRTParser.to_srt(processed_segments)
        
        # Generate quality report
        qa_report = None
        if self.qa_enabled and confidence_scores:
            qa_report = self._generate_quality_report(filename, segments, confidence_scores, all_issues)
        
        return output_srt, qa_report
    
    def _generate_quality_report(self, filename: str, segments: list, 
                               confidence_scores: list, quality_issues: list) -> dict:
        """Generate comprehensive quality report."""
        from datetime import datetime
        
        # Overall statistics
        total_segments = len(segments)
        high_confidence = sum(1 for c in confidence_scores if c.overall_confidence > 0.9)
        medium_confidence = sum(1 for c in confidence_scores if 0.7 <= c.overall_confidence <= 0.9)
        low_confidence = sum(1 for c in confidence_scores if c.overall_confidence < 0.7)
        
        # Issue statistics
        critical_issues = sum(1 for i in quality_issues if i.severity == 'critical')
        high_issues = sum(1 for i in quality_issues if i.severity == 'high')
        
        report = {
            "metadata": {
                "filename": filename,
                "processed_at": datetime.now().isoformat(),
                "processor_version": "1.0",
                "total_segments": total_segments
            },
            "quality_summary": {
                "high_confidence_segments": high_confidence,
                "medium_confidence_segments": medium_confidence, 
                "low_confidence_segments": low_confidence,
                "critical_issues": critical_issues,
                "high_priority_issues": high_issues,
                "review_recommended_segments": low_confidence + critical_issues + high_issues
            },
            "segment_details": [
                {
                    "segment_number": i + 1,
                    "timestamp": f"{seg.start_time} --> {seg.end_time}",
                    "confidence": {
                        "overall": conf.overall_confidence,
                        "lexicon": conf.lexicon_confidence,
                        "sacred": conf.sacred_confidence,
                        "compound": conf.compound_confidence,
                        "scripture": conf.scripture_confidence
                    },
                    "flags": conf.processing_flags,
                    "issues": [
                        {
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "description": issue.description,
                            "suggested_action": issue.suggested_action
                        }
                        for issue in quality_issues 
                        if issue.timestamp_start == seg.start_time
                    ]
                }
                for i, (seg, conf) in enumerate(zip(segments, confidence_scores))
                if conf.overall_confidence < 0.9 or any(
                    issue.timestamp_start == seg.start_time for issue in quality_issues
                )
            ]
        }
        
        return report

    def close(self):
        """Clean up database connections and resources."""
        if hasattr(self.lexicons, 'close') and callable(self.lexicons.close):
            self.lexicons.close()
            logger.info("Database connections closed")

# Backward compatibility exports - maintain existing import paths
# These allow existing code to continue importing from sanskrit_processor_v2
__all__ = [
    'SRTSegment', 'ProcessingResult', 'DetailedProcessingResult', 'CorrectionDetail',
    'MetricsCollector', 'ProcessingReporter', 'LexiconLoader', 'SRTParser', 'SanskritProcessor'
]

if __name__ == "__main__":
    # Simple test
    processor = SanskritProcessor()
    
    # Test text processing
    test_text = "Welcome to this bhagavad gita lecture on dharma and yoga"
    result, corrections = processor.process_text(test_text)
    print(f"Test: '{test_text}' -> '{result}' ({corrections} corrections)")
