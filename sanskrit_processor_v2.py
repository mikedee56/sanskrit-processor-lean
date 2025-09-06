#!/usr/bin/env python3
"""
Lean Sanskrit SRT Processor - Focused implementation
No bloat, no over-engineering, just working text processing.
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging

# Import utilities for lean architecture
from utils.srt_parser import SRTParser, SRTSegment
# Import exceptions for enhanced error handling
from exceptions import FileError, ProcessingError, ConfigurationError
from utils.metrics_collector import MetricsCollector, CorrectionDetail
from utils.processing_reporter import ProcessingReporter, ProcessingResult, DetailedProcessingResult

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
        self.lexicons = LexiconLoader(self.lexicon_dir)
        
        # Load configuration
        self.config = self._load_config(config_path or Path("config.yaml"))
        
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
        
        logger.info("Sanskrit processor initialized")

    
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
        """Process a single text segment. Returns (processed_text, corrections_made)."""
        original_text = text
        corrections = 0
        
        # 1. Basic text cleanup
        text = self._normalize_text(text)
        
        # 2. Apply lexicon corrections
        text, lexicon_corrections = self._apply_lexicon_corrections(text)
        corrections += lexicon_corrections
        
        # 3. Apply proper noun capitalization
        text, capitalization_corrections = self._apply_capitalization(text)
        corrections += capitalization_corrections
        
        # 4. Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 5. Apply plugins (lean implementation)
        text = self.plugin_manager.execute_all(text)
        
        if text != original_text:
            logger.debug(f"Processed: '{original_text[:50]}...' -> '{text[:50]}...' ({corrections} corrections)")
            
        return text, corrections
    
    def _normalize_text(self, text: str) -> str:
        """Basic text normalization with punctuation enhancement."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
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
        
        # Clean spacing
        text = re.sub(r'\s+([.,:;!?])', r'\1', text)
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        return text

    def _is_sanskrit_context(self, text: str) -> bool:
        """Check if text contains Sanskrit/sacred content that should be preserved."""
        sanskrit_indicators = [
            r'\d+\.\d+',  # Verse references like "2.47"
            r'chapter\s+\d+',  # "Chapter 2"  
            r'[āīūṛṅṇṭḍṣśḥṃ]',  # IAST characters
            r'om\s+\w+\s+om',  # Mantras
            'bhagavad gita', 'upanishad', 'vedas'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) 
                  for pattern in sanskrit_indicators)
    
    def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
        """Apply corrections from lexicon files with fuzzy matching fallback."""
        corrections = 0
        words = text.split()
        corrected_words = []
        
        # Get fuzzy matching config
        fuzzy_config = self.config.get('processing', {}).get('fuzzy_matching', {})
        fuzzy_enabled = fuzzy_config.get('enabled', True)
        fuzzy_threshold = fuzzy_config.get('threshold', 0.8)
        log_fuzzy = fuzzy_config.get('log_matches', False)
        
        for word in words:
            # Clean word for lookup (remove punctuation)
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            # Try exact match first
            if clean_word in self.lexicons.corrections:
                entry = self.lexicons.corrections[clean_word]
                
                # Choose output format based on configuration
                use_diacritics = self.config.get('processing', {}).get('use_iast_diacritics', False)
                if use_diacritics and 'transliteration' in entry:
                    corrected = entry['transliteration']
                else:
                    corrected = entry['original_term']
                
                # Preserve capitalization pattern
                if word[0].isupper():
                    corrected = corrected.capitalize()
                
                # Record metrics if collecting
                if self.metrics_collector:
                    self.metrics_collector.start_correction('lexicon', word)
                    self.metrics_collector.end_correction('lexicon', word, corrected, 1.0)
                    
                corrected_words.append(corrected)
                corrections += 1
                logger.debug(f"Exact correction: {word} -> {corrected}")
                
            # Try fuzzy match if enabled and no exact match
            elif fuzzy_enabled and clean_word:
                fuzzy_match = self._find_fuzzy_match(clean_word, fuzzy_threshold)
                if fuzzy_match:
                    # Preserve capitalization pattern
                    if word[0].isupper():
                        fuzzy_match = fuzzy_match.capitalize()
                    
                    # Calculate confidence for fuzzy match
                    confidence = self._calculate_similarity(clean_word, fuzzy_match.lower())
                    
                    # Record metrics if collecting
                    if self.metrics_collector:
                        self.metrics_collector.start_correction('fuzzy', word)
                        self.metrics_collector.end_correction('fuzzy', word, fuzzy_match, confidence)
                        
                    corrected_words.append(fuzzy_match)
                    corrections += 1
                    
                    if log_fuzzy:
                        logger.info(f"Fuzzy correction: {word} -> {fuzzy_match}")
                    else:
                        logger.debug(f"Fuzzy correction: {word} -> {fuzzy_match}")
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    def _apply_capitalization(self, text: str) -> tuple[str, int]:
        """Apply proper noun capitalization."""
        corrections = 0
        words = text.split()
        corrected_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            if clean_word in self.lexicons.proper_nouns:
                entry = self.lexicons.proper_nouns[clean_word]
                corrected = entry.get('term') or entry.get('original_term', word)
                
                # Record metrics if collecting
                if self.metrics_collector:
                    self.metrics_collector.start_correction('capitalization', word)
                    self.metrics_collector.end_correction('capitalization', word, corrected, 1.0)
                
                corrected_words.append(corrected)
                corrections += 1
                logger.debug(f"Capitalization: {word} -> {corrected}")
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections

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
    
    def process_srt_file(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Process an SRT file with Sanskrit corrections."""
        import time
        start_time = time.time()
        parse_start = time.time()
        
        # Memory monitoring (only when collecting metrics and psutil is available)
        memory_start = None
        if self.collect_metrics:
            try:
                import psutil
                process = psutil.Process()
                memory_start = process.memory_info().rss / 1024 / 1024  # MB
            except ImportError:
                pass
        
        logger.info(f"Processing SRT file: {input_path} -> {output_path}")
        
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
            
            parse_time = time.time() - parse_start
            logger.info(f"Parsed {len(segments)} segments")
            
            # Processing phase
            process_start = time.time()
            total_corrections = 0
            processing_errors = []
            
            for i, segment in enumerate(segments, 1):
                try:
                    processed_text, corrections = self.process_text(segment.text)
                    segment.text = processed_text
                    total_corrections += corrections
                except Exception as e:
                    # Log but continue processing other segments
                    error_msg = f"Failed to process segment {i}: {e}"
                    processing_errors.append(error_msg)
                    logger.warning(error_msg)
            
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
            
            write_time = time.time() - write_start
            processing_time = time.time() - start_time
            
            # Create appropriate result type
            if self.collect_metrics and self.metrics_collector:
                # Calculate memory usage
                memory_usage = {}
                if memory_start:
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_end = process.memory_info().rss / 1024 / 1024
                        memory_usage = {
                            'peak': memory_end,
                            'average': (memory_start + memory_end) / 2
                        }
                    except ImportError:
                        pass
                
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
                    processing_phases={'parse': parse_time, 'process': process_time, 'write': write_time},
                    quality_score=quality_score,
                    memory_usage=memory_usage
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
