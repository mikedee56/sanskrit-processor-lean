#!/usr/bin/env python3
"""
Lean Sanskrit SRT Processor - Focused implementation
No bloat, no over-engineering, just working text processing.
"""

import re
import yaml
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
import logging

# Devanagari to IAST transliteration
try:
    from indic_transliteration import sanscript
    TRANSLITERATION_AVAILABLE = True
except ImportError:
    TRANSLITERATION_AVAILABLE = False
    sanscript = None

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

    def __init__(self, lexicon_dir: Path = None, config_path: Path = None, collect_metrics: bool = False, metadata_path: Path = None):
        """Initialize processor with lexicon directory, configuration, and optional LID metadata."""
        self.lexicon_dir = lexicon_dir or Path("lexicons")

        # Load LID metadata from production pipeline if provided
        self.lid_metadata = None
        self.use_lid_metadata = False
        if metadata_path and Path(metadata_path).exists():
            self.lid_metadata = self._load_lid_metadata(Path(metadata_path))
            self.use_lid_metadata = True
            logger.info(f"Loaded LID metadata with {len(self.lid_metadata)} segments")
        
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

        # Initialize validation cache for performance optimization (Story 11.1)
        try:
            from utils.validation import DatabaseValidator
            DatabaseValidator.initialize_validation_cache(self.lexicons)
        except Exception as e:
            logger.warning(f"Failed to initialize validation cache: {e}")
            # Continue without cache - system will work but with validation overhead
        
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

        # Initialize capitalization preservation (Story 11.2)
        from processors.capitalization_preserver import CapitalizationPreserver
        self.capitalization_preserver = CapitalizationPreserver(self.config.get('processing', {}))
        
        # FIXED: Check config to decide whether to use context pipeline
        enable_context_pipeline = self.config.get('processing', {}).get('enable_context_pipeline', True)
        
        # Initialize context-aware pipeline (Story 6.5) - ONLY if enabled in config
        if enable_context_pipeline:
            try:
                from processors.context_pipeline import ContextAwarePipeline
                self.context_pipeline = ContextAwarePipeline(self.config)
                self.use_context_pipeline = True
                logger.info("Context-aware pipeline initialized")
            except ImportError as e:
                logger.warning(f"Context-aware pipeline not available: {e}")
                self.context_pipeline = None
                self.use_context_pipeline = False
        else:
            logger.info("Context pipeline disabled by configuration - using legacy processing")
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

        # Initialize scriptural segment processor for multi-pass architecture
        try:
            from processors.scriptural_segment_processor import ScripturalSegmentProcessor
            self.scriptural_processor = ScripturalSegmentProcessor(self.config)
            logger.info("Scriptural segment processor initialized")
        except ImportError as e:
            logger.warning(f"Scriptural segment processor not available: {e}")
            self.scriptural_processor = None
        
        # Metrics collection
        self.collect_metrics = collect_metrics
        self.metrics_collector = MetricsCollector() if collect_metrics else None
        
        # Initialize plugin system (lean implementation)
        from utils.plugin_manager import PluginManager
        self.plugin_manager = PluginManager()
        if self.config.get('plugins', {}).get('enabled', False):
            self.plugin_manager.enable()
            self._load_plugins()
        
        # Initialize Mantra Standardization Engine (ADR-003)
        enable_mantra_standardization = self.config.get('processing', {}).get('enable_mantra_standardization', True)

        if enable_mantra_standardization:
            try:
                from processors.mantra_standardizer import MantraStandardizer
                from processors.smart_capitalizer import SmartCapitalizer
                self.mantra_standardizer = MantraStandardizer()
                self.smart_capitalizer = SmartCapitalizer()
                logger.info("Mantra Standardization Engine initialized (ADR-003)")
            except ImportError as e:
                logger.warning(f"Mantra Standardization Engine not available: {e}")
                self.mantra_standardizer = None
                self.smart_capitalizer = None
        else:
            logger.info("Mantra standardization disabled by configuration")
            self.mantra_standardizer = None
            self.smart_capitalizer = None

        # Initialize Sanskrit Linguistic Engine (NEW ARCHITECTURE)
        enable_linguistic_engine = self.config.get('processing', {}).get('enable_linguistic_engine', True)

        if enable_linguistic_engine:
            try:
                from sanskrit_linguistics import LinguisticMatcher
                self.linguistic_matcher = LinguisticMatcher(self.config)
                self.use_linguistic_engine = True
                logger.info("Sanskrit Linguistic Engine initialized - intelligent processing enabled")
            except ImportError as e:
                logger.warning(f"Sanskrit Linguistic Engine not available: {e}")
                self.linguistic_matcher = None
                self.use_linguistic_engine = False
        else:
            logger.info("Linguistic engine disabled by configuration - using traditional processing")
            self.linguistic_matcher = None
            self.use_linguistic_engine = False

        # Initialize Artifact Filter (Post-processing Enhancement)
        enable_artifact_filter = self.config.get('enable_artifact_filter', False)

        if enable_artifact_filter:
            try:
                from processors.artifact_filter import LaughterArtifactFilter
                self.artifact_filter = LaughterArtifactFilter(self.config)
                logger.info("Artifact Filter initialized (post-processing cleanup)")
            except ImportError as e:
                logger.warning(f"Artifact Filter not available: {e}")
                self.artifact_filter = None
        else:
            logger.debug("Artifact filter disabled by configuration")
            self.artifact_filter = None

        # Basic text normalization patterns
        self.filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know']

        # Log initialization summary
        if self.use_linguistic_engine:
            logger.info("Sanskrit processor initialized with LINGUISTIC ENGINE (intelligent processing)")
        elif self.use_context_pipeline:
            logger.info("Sanskrit processor initialized with context-aware processing")
        else:
            logger.info("Sanskrit processor initialized with legacy processing")

    
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

    
    def _load_metadata(self, srt_file: str) -> Optional[Dict]:
        """Load companion JSON metadata for enhanced processing with graceful fallback.
        
        CRITICAL FIX: This method now also enables LID-aware routing if the metadata
        contains language detection information. This ensures auto-detected metadata
        files trigger intelligent English preservation and language-specific processing.
        
        Args:
            srt_file: Path to SRT file
            
        Returns:
            Dict with metadata or None if not available
        """
        try:
            # Construct metadata file path
            srt_path = Path(srt_file)
            metadata_file = srt_path.with_name(srt_path.stem + '_metadata.json')

            if not metadata_file.exists():
                logger.debug(f"No metadata file found: {metadata_file}")
                return None
                
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Validate basic structure
            if not isinstance(metadata, dict):
                logger.warning(f"Invalid metadata format in {metadata_file}")
                return None
                
            # Validate segments array if present
            segments = metadata.get('segments', [])
            if segments and not isinstance(segments, list):
                logger.warning(f"Invalid segments format in {metadata_file}")
                return None
                
            logger.info(f"Loaded metadata for {len(segments)} segments from {metadata_file}")
            
            # CRITICAL FIX: Enable LID-aware routing from auto-detected metadata
            # This was the missing piece - metadata was loaded but LID routing wasn't enabled
            if not self.use_lid_metadata:  # Only if not already set via constructor
                lid_data = self._extract_lid_from_metadata(metadata)
                if lid_data:
                    self.lid_metadata = lid_data
                    self.use_lid_metadata = True
                    logger.info(f"✓ LID-aware routing ENABLED from auto-detected metadata")
                    logger.info(f"  English segments will be preserved, Sanskrit/Hindi intelligently processed")
                else:
                    logger.warning(f"⚠ Metadata found but no LID data - using legacy processing")
                    logger.warning(f"  Consider regenerating metadata with language detection enabled")
            
            return metadata
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse metadata JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return None
    
    def _get_segment_metadata(self, metadata: Optional[Dict], segment_index: int) -> Dict:
        """Get metadata for specific segment with safe fallback.
        
        Args:
            metadata: Loaded metadata dict or None
            segment_index: 0-based segment index
            
        Returns:
            Dict with segment metadata (empty dict if not available)
        """
        if not metadata:
            return {}
            
        segments = metadata.get('segments', [])
        if segment_index >= len(segments):
            return {}
            
        segment_meta = segments[segment_index]
        if not isinstance(segment_meta, dict):
            return {}
            
        return segment_meta
    
    def _apply_metadata_hints(self, text: str, segment_meta: Dict) -> Dict:
        """Apply metadata hints to processing parameters.
        
        Args:
            text: Segment text
            segment_meta: Metadata for this segment
            
        Returns:
            Dict with processing hints and adjusted parameters
        """
        hints = {
            'confidence_threshold': 0.7,  # Default threshold
            'sanskrit_priority': False,
            'expected_type': None,
            'language_context': 'mixed'
        }
        
        # Apply ASR confidence adjustments
        asr_confidence = segment_meta.get('asr_confidence', 1.0)
        if asr_confidence < 0.7:
            # Lower threshold for low-confidence ASR segments
            hints['confidence_threshold'] = 0.5
            hints['sanskrit_priority'] = True
            logger.debug(f"Low ASR confidence ({asr_confidence:.2f}): enabling aggressive Sanskrit correction")
        
        # Apply language detection hints
        lang_detection = segment_meta.get('language_detection', {})
        sanskrit_density = lang_detection.get('sanskrit_density', 0)
        if sanskrit_density > 0.3:
            hints['sanskrit_priority'] = True
            hints['language_context'] = 'sanskrit_heavy'
            logger.debug(f"High Sanskrit density ({sanskrit_density:.2f}): prioritizing Sanskrit processing")
        
        # Apply content type hints
        content_hints = segment_meta.get('content_hints', {})
        expected_type = content_hints.get('expected_type')
        if expected_type in ['opening_prayer', 'closing_prayer', 'mantra_recitation']:
            hints['expected_type'] = expected_type
            hints['sanskrit_priority'] = True
            hints['confidence_threshold'] = 0.6  # Moderate threshold for prayers
            logger.debug(f"Prayer context detected: {expected_type}")
        
        # Apply audio feature hints
        audio_features = segment_meta.get('audio_features', {})
        speech_rate = audio_features.get('speech_rate')
        if speech_rate == 'deliberate':
            hints['confidence_threshold'] = 0.6  # Lower threshold for deliberate speech
            hints['sanskrit_priority'] = True
            logger.debug("Deliberate speech detected: enhancing Sanskrit processing")
        
        return hints

    def _load_lid_metadata(self, metadata_path: Path) -> Dict[int, Dict]:
        """Load LID metadata from production pipeline JSON.

        Args:
            metadata_path: Path to production_pipeline_results.json

        Returns:
            Dict mapping final_segment_number to LID metadata
        """
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                pipeline_data = json.load(f)

            # Validate basic structure
            if not isinstance(pipeline_data, dict) or 'segments' not in pipeline_data:
                logger.warning(f"Invalid pipeline metadata format in {metadata_path}")
                return {}

            # Create lookup by segment number (supports multiple formats)
            lid_map = {}
            for idx, seg in enumerate(pipeline_data.get('segments', [])):
                # Determine segment number (1-based, like SRT)
                segment_num = seg.get('final_segment_number') or seg.get('segment_number') or (idx + 1)

                # Extract language
                language = seg.get('language', 'unknown')

                # Handle different confidence formats
                if 'language_confidence' in seg:
                    # Format 1: Direct confidence field
                    confidence = seg.get('language_confidence', 0.0)
                elif 'language_scores' in seg and language in seg['language_scores']:
                    # Format 2: Extract from language_scores dict
                    confidence = seg['language_scores'][language]
                else:
                    confidence = 0.0

                lid_map[segment_num] = {
                    'language': language,
                    'language_confidence': confidence,
                    'source': seg.get('source', 'whisperx'),
                    'start_time': seg.get('start') or seg.get('start_time'),
                    'end_time': seg.get('end') or seg.get('end_time'),
                    'duration': seg.get('duration')
                }

            logger.info(f"Loaded LID metadata for {len(lid_map)} segments")
            return lid_map

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pipeline metadata JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load pipeline metadata: {e}")
            return {}

    def _extract_lid_from_metadata(self, metadata: Dict) -> Dict[int, Dict]:
        """Extract LID routing data from auto-detected metadata JSON.
        
        This method bridges the gap between runtime-loaded metadata and LID routing.
        It extracts the same LID information that _load_lid_metadata() would get,
        enabling LID-aware processing from auto-detected metadata files.
        
        Args:
            metadata: Metadata dict from _load_metadata()
            
        Returns:
            Dict mapping segment_number to LID metadata (same format as _load_lid_metadata)
        """
        try:
            if not isinstance(metadata, dict) or 'segments' not in metadata:
                logger.warning("Cannot extract LID data: invalid metadata structure")
                return {}
            
            # Create lookup by segment number (1-based, like SRT)
            lid_map = {}
            for idx, seg in enumerate(metadata.get('segments', [])):
                # Determine segment number (1-based)
                segment_num = seg.get('segment_number', idx + 1)
                
                # Extract language
                language = seg.get('language', 'unknown')
                
                # Handle different confidence formats
                if 'language_confidence' in seg:
                    # Format 1: Direct confidence field
                    confidence = seg.get('language_confidence', 0.0)
                elif 'language_scores' in seg and language in seg['language_scores']:
                    # Format 2: Extract from language_scores dict
                    confidence = seg['language_scores'][language]
                else:
                    confidence = 0.0
                
                lid_map[segment_num] = {
                    'language': language,
                    'language_confidence': confidence,
                    'source': seg.get('source', 'whisperx'),
                    'start_time': seg.get('start'),
                    'end_time': seg.get('end'),
                    'duration': seg.get('duration')
                }
            
            logger.info(f"Extracted LID routing data for {len(lid_map)} segments from auto-detected metadata")
            return lid_map
            
        except Exception as e:
            logger.warning(f"Failed to extract LID data from metadata: {e}")
            return {}

    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate duration in seconds from SRT timestamps.
        
        Args:
            start_time: Start timestamp in SRT format (HH:MM:SS,mmm)
            end_time: End timestamp in SRT format (HH:MM:SS,mmm)
            
        Returns:
            Duration in seconds as float
        """
        def parse_timestamp(timestamp: str) -> float:
            """Parse SRT timestamp to seconds."""
            try:
                # Split time and milliseconds (HH:MM:SS,mmm)
                time_part, ms_part = timestamp.split(',')
                h, m, s = map(int, time_part.split(':'))
                ms = int(ms_part)
                return h * 3600 + m * 60 + s + ms / 1000
            except (ValueError, AttributeError):
                logger.warning(f"Failed to parse timestamp: {timestamp}")
                return 0.0
        
        return parse_timestamp(end_time) - parse_timestamp(start_time)

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
        """Process a single text segment with PHRASE-FIRST INTELLIGENT ARCHITECTURE.

        TRANSFORMATION: Complete units (prayers, verses) processed before word-by-word lookup.
        This is the core change from "glorified lookup table" to "intelligent processor".

        Returns (processed_text, corrections_made).
        """
        original_text = text
        corrections = 0

        # CRITICAL FIX: NORMALIZATION-FIRST ARCHITECTURE
        # Always normalize text FIRST to ensure Devanagari conversion happens regardless of processing path
        text = self._normalize_text(text)
        if text != original_text:
            logger.debug(f"Normalization applied: '{original_text[:50]}...' -> '{text[:50]}...'")

        # PHASE 0: MANTRA STANDARDIZATION (ADR-003) - Apply early for mantras
        if hasattr(self, 'mantra_standardizer') and self.mantra_standardizer:
            mantra_result, was_normalized = self.mantra_standardizer.normalize(text)
            if was_normalized:
                text = mantra_result
                corrections += 1
                logger.info(f"Mantra standardized: {text[:60]}...")

        # PHASE 1: INTELLIGENT SCRIPTURAL SEGMENT PROCESSING (HIGHEST PRIORITY)
        # This is the key transformation - phrase-level processing comes FIRST
        if self.scriptural_processor:
            try:
                processed_text, was_modified, reference = self.scriptural_processor.process_segment(text)
                if was_modified:
                    logger.info(f"PHRASE-LEVEL PROCESSING: {reference or 'Complete unit replacement'}")
                    logger.debug(f"Transformation: '{text[:50]}...' -> '{processed_text[:50]}...'")
                    return processed_text, corrections + 1  # Count as 1 major correction (complete unit) + any mantra corrections
                text = processed_text  # Continue with the (possibly unchanged) text
            except Exception as e:
                logger.warning(f"Phrase-level processing failed, falling back to word-level: {e}")

        # PHASE 2: SANSKRIT LINGUISTIC ENGINE (intelligent Sanskrit processing)
        if self.use_linguistic_engine and self.linguistic_matcher:
            try:
                # Detect content context for appropriate processing
                context_type = self._detect_content_context(text)

                # Apply intelligent linguistic processing
                result = self.linguistic_matcher.process_text_linguistically(text, context_type)

                if result.corrections_made > 0:
                    logger.info(f"Linguistic engine applied {result.corrections_made} enhancements "
                              f"(confidence: {result.confidence:.2f}, type: {result.enhancement_type})")
                    return result.enhanced_text, corrections + result.corrections_made
                else:
                    # Continue with original text if no enhancements were confident enough
                    text = result.enhanced_text

            except Exception as e:
                logger.warning(f"Linguistic engine failed, falling back to context pipeline: {e}")

        # PHASE 3: CONTEXT-AWARE PIPELINE (if available)
        if self.use_context_pipeline and self.context_pipeline:
            try:
                result = self.context_pipeline.process_segment(text)
                if hasattr(result, 'corrections_made') and result.corrections_made > 0:
                    logger.info(f"Context pipeline applied {result.corrections_made} corrections")
                    return result.processed_text, corrections + result.corrections_made
            except Exception as e:
                logger.warning(f"Context pipeline failed, falling back to legacy processing: {e}")

        # PHASE 4: LEGACY WORD-BY-WORD PROCESSING (FALLBACK ONLY)
        # This is now the LAST resort, not the primary method
        # NOTE: Skip normalization in _legacy_process_text as it's already done above
        logger.debug(f"Falling back to legacy word-by-word processing for: '{text[:50]}...'")
        text, legacy_corrections = self._legacy_process_text_normalized(text)
        corrections += legacy_corrections

        # PHASE 5: SMART CAPITALIZATION (ADR-003) - Apply at the end
        if hasattr(self, 'smart_capitalizer') and self.smart_capitalizer:
            # Detect if this looks like a prayer or mantra for appropriate capitalization
            if any(term in text.lower() for term in ['oṁ', 'om', 'namaḥ', 'namah', 'śrī', 'shri']):
                text = self.smart_capitalizer.apply(text, mode='prayer')
                logger.debug(f"Applied smart prayer capitalization")
            else:
                # Use conservative mode for other content
                text = self.smart_capitalizer.apply(text, mode='conservative')

        return text, corrections

    def process_text_with_metadata(self, text: str, hints: Dict) -> tuple[str, int]:
        """Process text with metadata hints for enhanced processing.
        
        Args:
            text: Text to process
            hints: Processing hints from metadata analysis
            
        Returns:
            Tuple of (processed_text, corrections_made)
        """
        original_text = text
        
        # Extract hints
        sanskrit_priority = hints.get('sanskrit_priority', False)
        expected_type = hints.get('expected_type')
        language_context = hints.get('language_context', 'mixed')
        confidence_threshold = hints.get('confidence_threshold', 0.7)
        
        logger.debug(f"Processing with metadata hints: priority={sanskrit_priority}, type={expected_type}, context={language_context}, threshold={confidence_threshold}")
        
        # CRITICAL FIX: NORMALIZATION-FIRST ARCHITECTURE
        # Always normalize text FIRST to ensure Devanagari conversion happens regardless of processing path
        text = self._normalize_text(text)
        if text != original_text:
            logger.debug(f"Normalization applied: '{original_text[:50]}...' -> '{text[:50]}...'")

        # PHASE 1: ENHANCED SCRIPTURAL PROCESSING with priority handling
        if self.scriptural_processor and (sanskrit_priority or expected_type):
            try:
                # Prime the prayer engine if we expect prayer content
                if expected_type in ['opening_prayer', 'closing_prayer', 'mantra_recitation']:
                    logger.debug(f"Priming prayer recognition for expected type: {expected_type}")
                
                processed_text, was_modified, reference = self.scriptural_processor.process_segment(text)
                if was_modified:
                    logger.info(f"METADATA-ENHANCED PHRASE PROCESSING: {reference or 'Complete unit replacement'}")
                    return processed_text, 1  # Count as 1 major correction
                text = processed_text
            except Exception as e:
                logger.warning(f"Enhanced phrase-level processing failed: {e}")

        # PHASE 2: LINGUISTIC ENGINE with adjusted confidence
        if self.use_linguistic_engine and self.linguistic_matcher:
            try:
                # Use metadata context for linguistic processing
                context_type = expected_type or self._detect_content_context(text)
                result = self.linguistic_matcher.process_text_linguistically(text, context_type)

                if result.corrections_made > 0:
                    logger.info(f"Metadata-enhanced linguistic processing: {result.corrections_made} corrections")
                    return result.enhanced_text, result.corrections_made
                text = result.enhanced_text
            except Exception as e:
                logger.warning(f"Enhanced linguistic processing failed: {e}")

        # PHASE 3: CONTEXT PIPELINE with metadata context override
        if self.use_context_pipeline and self.context_pipeline:
            try:
                # Override context detection with metadata hints
                if hasattr(self.context_pipeline, 'process_segment_with_context'):
                    result = self.context_pipeline.process_segment_with_context(text, language_context)
                else:
                    result = self.context_pipeline.process_segment(text)
                    
                if hasattr(result, 'corrections_made') and result.corrections_made > 0:
                    logger.info(f"Metadata-enhanced context processing: {result.corrections_made} corrections")
                    return result.processed_text, result.corrections_made
            except Exception as e:
                logger.warning(f"Enhanced context processing failed: {e}")

        # PHASE 4: ENHANCED LEGACY PROCESSING with adjusted thresholds
        logger.debug(f"Enhanced legacy processing with threshold: {confidence_threshold}")
        return self._legacy_process_text_with_hints(text, hints)

    def _legacy_process_text_with_hints(self, text: str, hints: Dict) -> tuple[str, int]:
        """Legacy processing enhanced with metadata hints.
        
        NOTE: Text normalization (including Devanagari conversion) is now handled 
        in process_text_with_metadata() to ensure consistent conversion across all paths.
        """
        original_text = text
        corrections = 0
        confidence_threshold = hints.get('confidence_threshold', 0.7)
        sanskrit_priority = hints.get('sanskrit_priority', False)
        
        # Override context detection if Sanskrit priority is set
        if sanskrit_priority:
            forced_context = 'sanskrit'
            logger.debug(f"Forcing Sanskrit context due to metadata priority")
        else:
            forced_context = None
        
        # Enhanced lexicon processing with adjusted thresholds
        # NOTE: Skip normalization as it's already done in process_text_with_metadata()
        text, lexicon_corrections = self._apply_lexicon_corrections_with_hints(text, hints, forced_context)
        corrections += lexicon_corrections
        
        # Enhanced capitalization with metadata awareness
        text, cap_corrections = self._apply_capitalization(text)
        corrections += cap_corrections
        
        # Clean up
        text = re.sub(r'[ \t]+', ' ', text).strip()
        text = self.plugin_manager.execute_all(text)
        
        if text != original_text:
            logger.debug(f"Enhanced legacy processing: '{original_text[:50]}...' -> '{text[:50]}...' ({corrections} corrections)")
            
        return text, corrections

    def _apply_lexicon_corrections_with_hints(self, text: str, hints: Dict, forced_context: str = None) -> tuple[str, int]:
        """Apply lexicon corrections with metadata hints."""
        corrections = 0
        original_text = text
        confidence_threshold = hints.get('confidence_threshold', 0.7)

        # Enhanced compound processing for Sanskrit priority content
        if self.compound_matcher and hints.get('sanskrit_priority', False):
            text, compound_matches = self.compound_matcher.process_text(text)
            corrections += len(compound_matches)
            if compound_matches:
                logger.info(f"Enhanced compound corrections: {len(compound_matches)}")

        # Enhanced word-level processing
        lines = text.split('\n')
        corrected_lines = []

        # Use forced context or detect normally
        text_context = forced_context or self.detect_context(text)
        
        logger.debug(f"Enhanced lexicon processing: context={text_context}, threshold={confidence_threshold}")

        word_corrections = 0
        for line in lines:
            words = line.split()
            corrected_words = []

            for word in words:
                original_word = word
                # Enhanced word processing with metadata-aware thresholds
                corrected_word = self._process_word_with_metadata(word, text_context, confidence_threshold, hints)
                corrected_words.append(corrected_word)

                if corrected_word != original_word:
                    word_corrections += 1
                    logger.debug(f"Enhanced word correction: '{word}' -> '{corrected_word}'")

            corrected_lines.append(' '.join(corrected_words))

        corrections += word_corrections
        final_text = '\n'.join(corrected_lines)

        if final_text != original_text:
            logger.info(f"Enhanced lexicon corrections total: {corrections}")

        return final_text, corrections

    def _process_word_with_metadata(self, word: str, context: str, confidence_threshold: float, hints: Dict) -> str:
        """Enhanced word processing with metadata hints."""
        sanskrit_priority = hints.get('sanskrit_priority', False)
        
        # If Sanskrit priority is set, use more aggressive processing
        if sanskrit_priority:
            # Lower confidence threshold for Sanskrit priority content
            adjusted_threshold = max(0.5, confidence_threshold - 0.2)
            logger.debug(f"Sanskrit priority: lowering threshold to {adjusted_threshold}")
        else:
            adjusted_threshold = confidence_threshold
        
        # Use the standard word processing with adjusted threshold
        return self._process_word_with_punctuation(word, context, adjusted_threshold)

    def _detect_content_context(self, text: str) -> str:
        """
        Detect content context for linguistic processing.

        Maps from existing context detection to linguistic engine context types.
        """
        if not text or not isinstance(text, str):
            return 'mixed'

        text_lower = text.lower().strip()

        # Mantra detection (high confidence indicators)
        if (text_lower.startswith('om ') or text_lower.startswith('aum ') or
            'om namah' in text_lower or 'om mani' in text_lower or
            text_lower.startswith('gayatri') or 'svaha' in text_lower):
            return 'mantra'

        # Prayer detection
        if ('namaste' in text_lower or 'namaskara' in text_lower or
            'prasadam' in text_lower or 'blessing' in text_lower):
            return 'prayer'

        # Verse detection (scripture references, structured content)
        if (re.search(r'\d+\.\d+', text) or  # Verse references like "2.47"
            'verse' in text_lower or 'shloka' in text_lower or
            'chapter' in text_lower or text_lower.startswith('in ')):
            return 'verse'

        # Use existing context detection for Sanskrit density
        try:
            # Leverage existing sophisticated context detection
            detected_context = self.detect_context(text)

            # Map to linguistic engine context types
            if detected_context == 'sanskrit':
                # High Sanskrit density - likely verse or mantra content
                if any(term in text_lower for term in ['om', 'aum', 'mantra', 'gayatri']):
                    return 'mantra'
                elif any(term in text_lower for term in ['verse', 'shloka', 'gita', 'upanishad']):
                    return 'verse'
                else:
                    return 'verse'  # Default high-Sanskrit content to verse processing

            elif detected_context == 'mixed':
                return 'explanation'  # Mixed content is usually explanatory

            else:  # 'english'
                return 'mixed'  # English context gets mixed processing

        except Exception as e:
            logger.warning(f"Context detection failed: {e}")
            return 'mixed'  # Safe fallback

    def _process_with_lid(self, text: str, segment_index: int) -> tuple[str, int, str]:
        """Process text using LID metadata for intelligent decisions.

        Args:
            text: Text to process
            segment_index: Segment index to lookup in LID metadata

        Returns:
            Tuple of (processed_text, corrections_made, stat_type)
            stat_type: One of 'english_preserved', 'sanskrit_aggressive', 'hindi_processed',
                      'mixed_conservative', 'uncertain_standard'
        """
        # Get LID data for this segment
        lid_data = self.lid_metadata.get(segment_index) if self.lid_metadata else None

        if not lid_data:
            # No LID data - fallback to current processing
            processed, corrections = self.process_text(text)
            return processed, corrections, 'uncertain_standard'

        language = lid_data.get('language', 'unknown')
        confidence = lid_data.get('language_confidence', 0.0)

        # Decision tree based on LID
        # Note: Thresholds calibrated for WhisperX language detection confidence scores
        # WhisperX scores are much lower (0.0-0.7 range) than traditional LID systems
        # Thresholds determined empirically from production data analysis
        if language == 'en' and confidence > 0.3:
            # ENGLISH PRESERVATION - Skip all processing for performance
            logger.debug(f"Seg {segment_index}: English (conf {confidence:.2f}) - preserved")
            return text, 0, 'english_preserved'

        elif language == 'sa' and confidence > 0.3:
            # SANSKRIT AGGRESSIVE - Prayers, mantras, full Sanskrit content
            logger.info(f"Seg {segment_index}: Sanskrit (conf {confidence:.2f}) - aggressive")
            processed, corrections = self._process_sanskrit_aggressive(text)
            return processed, corrections, 'sanskrit_aggressive'

        elif language == 'hi' and confidence > 0.25:
            # HINDI PROCESSING - Sanskrit terms in Hindi context (lower threshold)
            logger.info(f"Seg {segment_index}: Hindi (conf {confidence:.2f}) - Hindi rules")
            processed, corrections = self._process_hindi(text)
            return processed, corrections, 'hindi_processed'

        elif language == 'mixed':
            # MIXED CONTENT - CONSERVATIVE
            logger.info(f"Seg {segment_index}: Mixed content - conservative")
            processed, corrections = self._process_conservative(text)
            return processed, corrections, 'mixed_conservative'

        else:
            # LOW CONFIDENCE - FALLBACK
            logger.debug(f"Seg {segment_index}: Uncertain ({language}, {confidence:.2f}) - fallback")
            processed, corrections = self.process_text(text)
            return processed, corrections, 'uncertain_standard'

    def _process_sanskrit_aggressive(self, text: str) -> tuple[str, int]:
        """Aggressively process Sanskrit text (prayers, mantras).

        Args:
            text: Text to process

        Returns:
            Tuple of (processed_text, corrections_made)
        """
        corrections = 0
        original = text

        # NEW (ADR-003): Apply mantra standardization first
        if hasattr(self, 'mantra_standardizer') and self.mantra_standardizer:
            text, was_normalized = self.mantra_standardizer.normalize(text)
            if was_normalized:
                corrections += 1
                logger.info(f"Mantra standardized to IAST: {text[:60]}...")

        # Fix ALL CAPS to Title Case for prayers
        if text.isupper() and len(text) > 20:
            text = text.title()
            corrections += 1
            logger.debug(f"Fixed ALL CAPS prayer: {original[:50]}...")

        # Apply scriptural segment processing (existing)
        if hasattr(self, 'scriptural_processor') and self.scriptural_processor:
            try:
                processed, was_modified, ref = self.scriptural_processor.process_segment(text)
                if was_modified:
                    logger.info(f"Scripture match: {ref}")
                    return processed, corrections + 1
                text = processed
            except Exception as e:
                logger.warning(f"Scriptural processing failed: {e}")

        # Apply lexicon corrections
        text, lex_corrections = self.process_text(text)
        corrections += lex_corrections

        # NEW (ADR-003): Apply smart capitalization for prayers
        if hasattr(self, 'smart_capitalizer') and self.smart_capitalizer:
            text = self.smart_capitalizer.apply(text, mode='prayer')
            logger.debug(f"Applied smart capitalization")

        return text, corrections

    def _process_conservative(self, text: str) -> tuple[str, int]:
        """Conservatively process mixed content (fix Sanskrit only).

        Args:
            text: Text to process

        Returns:
            Tuple of (processed_text, corrections_made)
        """
        # Use existing process_text but could be made more conservative
        # For now, delegate to existing processing
        return self.process_text(text)

    def _process_hindi(self, text: str) -> tuple[str, int]:
        """Hindi-specific processing.

        Args:
            text: Text to process

        Returns:
            Tuple of (processed_text, corrections_made)
        """
        # For now, treat like conservative processing
        # Could be enhanced with Hindi-specific lexicon later
        return self._process_conservative(text)

    def process_segment_detailed(self, segment) -> 'ProcessingResult':
        """
        New method providing detailed processing results with multi-pass architecture.
        Returns comprehensive processing result with linguistic analysis.
        """
        # Use linguistic engine for detailed processing if available
        if self.use_linguistic_engine and self.linguistic_matcher:
            try:
                context_type = self._detect_content_context(segment.text)
                result = self.linguistic_matcher.process_text_linguistically(segment.text, context_type)

                # Convert LinguisticEnhancement to ProcessingResult
                from utils.processing_reporter import ProcessingResult
                return ProcessingResult(
                    segments_processed=1,
                    corrections_made=result.corrections_made,
                    processing_time=result.processing_time,
                    errors=[]
                )
            except Exception as e:
                logger.warning(f"Linguistic engine detailed processing failed: {e}")

        # Use the same multi-pass architecture as process_text (fallback)
        processed_text, corrections = self.process_text(segment.text)

        if self.use_context_pipeline and self.context_pipeline:
            from processors.context_pipeline import ProcessingResult as ContextProcessingResult

            # Try to get detailed results from context pipeline if it was used
            try:
                result = self.context_pipeline.process_segment(processed_text)
                return result
            except Exception as e:
                logger.warning(f"Context pipeline detailed processing failed: {e}")

        # Fallback to basic processing result
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
            text = re.sub(r'[ \t]+', ' ', text).strip()
            
            # 5. Apply plugins (lean implementation)
            text = self.plugin_manager.execute_all(text)
        
        if text != original_text:
            logger.debug(f"Processed ({content_type}): '{original_text[:50]}...' -> '{text[:50]}...' ({corrections} corrections)")
            
        return text, corrections

    def _legacy_process_text_normalized(self, text: str) -> tuple[str, int]:
        """Legacy processing pipeline for text that has already been normalized.
        
        NOTE: This method assumes text has already been through _normalize_text() 
        including Devanagari conversion, so it skips that step.
        """
        original_text = text
        corrections = 0
        
        # 1. Classify content type for sacred text handling
        content_type = self.sacred_classifier.classify_content(text)
        
        if content_type in ['mantra', 'verse', 'prayer']:
            # Sacred content processing pipeline (skip normalization)
            logger.debug(f"Sacred content detected: {content_type}")
            
            # 1. Protect sacred symbols before processing
            protected_text, restoration_map = self.symbol_protector.protect_symbols(text)
            
            # 2. Apply corrections to protected text (skip normalization)
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
            # Regular text processing (skip normalization as it's already done)
            # 1. Apply lexicon corrections
            text, lexicon_corrections = self._apply_lexicon_corrections(text)
            corrections += lexicon_corrections
            
            # 2. Apply proper noun capitalization
            text, capitalization_corrections = self._apply_capitalization(text)
            corrections += capitalization_corrections
            
            # 3. Clean up extra whitespace (preserve line breaks)
            text = re.sub(r'[ \t]+', ' ', text).strip()
            
            # 4. Apply plugins (lean implementation)
            text = self.plugin_manager.execute_all(text)
        
        if text != original_text:
            logger.debug(f"Processed normalized ({content_type}): '{original_text[:50]}...' -> '{text[:50]}...' ({corrections} corrections)")
            
        return text, corrections

    def _convert_devanagari_to_iast(self, text: str) -> str:
        """Convert Devanagari script to IAST transliteration."""
        if not TRANSLITERATION_AVAILABLE:
            logger.warning("indic-transliteration library not available, skipping Devanagari conversion")
            return text

        if not self.config.get('processing', {}).get('devanagari_to_iast', True):
            return text

        # Check if text contains Devanagari characters (U+0900–U+097F)
        devanagari_pattern = re.compile(r'[\u0900-\u097F]+')
        if not devanagari_pattern.search(text):
            return text

        try:
            # Convert Devanagari to IAST
            converted = sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
            logger.debug(f"Converted Devanagari to IAST: '{text[:50]}...' -> '{converted[:50]}...'")
            return converted
        except Exception as e:
            logger.warning(f"Devanagari to IAST conversion failed: {e}, keeping original text")
            return text

    def _normalize_text(self, text: str) -> str:
        """Basic text normalization with configurable punctuation enhancement."""
        # 1. Convert Devanagari to IAST first (before any other processing)
        text = self._convert_devanagari_to_iast(text)

        # 2. Remove excessive whitespace (preserve line breaks)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove common filler words
        for filler in self.filler_words:
            text = re.sub(rf'\b{re.escape(filler)}\b', '', text, flags=re.IGNORECASE)
        
        # Apply punctuation enhancement if enabled (Story 12.2: Disabled by default)
        if self.config.get('processing', {}).get('punctuation_enhancement', {}).get('enabled', False):
            text = self._enhance_punctuation(text)
        
        return text.strip()

    def _enhance_punctuation(self, text: str) -> str:
        """Configurable punctuation enhancement for lean architecture."""
        punct_config = self.config.get('processing', {}).get('punctuation_enhancement', {})
        
        if self._is_sanskrit_context(text):
            return text
        
        # Only proceed if enabled
        if not punct_config.get('enabled', False):
            return text
        
        # Basic punctuation fixes only - controlled by configuration
        if punct_config.get('auto_periods', False):
            endings = ["thank you", "namaste", "om shanti"]
            for phrase in endings:
                if text.lower().rstrip().endswith(phrase.lower()):
                    if not text.rstrip().endswith('.'):
                        text = text.rstrip() + '.'
                    break
        
        # Basic question detection - controlled by configuration
        if punct_config.get('auto_questions', False):
            if any(text.lower().strip().startswith(q) for q in ['what', 'how', 'why', 'when']):
                if not text.rstrip().endswith('?'):
                    text = text.rstrip() + '?'
        
        # Clean spacing (preserve line breaks) - always applied when enhancement is enabled
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

        # FIX: More reasonable thresholds that actually allow Sanskrit processing
        context_config = self.config.get('context_detection', {})
        thresholds = context_config.get('thresholds', {})

        # CRITICAL FIX: Lower thresholds to allow more Sanskrit corrections
        high_threshold = max(0.3, min(0.7, thresholds.get('sanskrit_confidence', 0.4)))  # Was 0.6
        low_threshold = max(0.1, min(0.4, 1.0 - thresholds.get('english_confidence', 0.8)))  # Was 0.95

        # Ensure thresholds are logically consistent
        if low_threshold >= high_threshold:
            low_threshold = high_threshold - 0.1

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

        # CRITICAL FIX: Higher weight for opening mantra detection
        if text_lower.startswith('om ') or text_lower.startswith('oṃ '):
            score += 0.8  # Very strong Sanskrit indicator (increased from 0.6)
        elif ' om ' in text_lower or ' oṃ ' in text_lower:
            score += 0.7  # Very strong Sanskrit indicator (increased from 0.5)

        # Sanskrit Context Indicators (higher weights)
        if 'purnam' in text_lower or 'pūrṇam' in text_lower:
            score += 0.4  # Opening mantra indicator (increased from 0.3)
        if 'shanti' in text_lower or 'śānti' in text_lower:
            score += 0.4  # Peace mantra indicator (increased from 0.3)
        if 'brahman' in text_lower:
            score += 0.3  # Increased from 0.2

        # IAST diacritical marks (strong indicator)
        iast_chars = 'āīūṛṇṣśḥṃ'
        iast_count = sum(1 for char in text if char in iast_chars)
        if len(text) > 0:
            score += min(0.5, iast_count / len(text) * 15)  # Increased weight and cap

        # Verse number references (e.g., "2.41", "4.7")
        verse_refs = len(re.findall(r'\d+\.\d+', text))
        score += min(0.3, verse_refs * 0.15)  # Increased from 0.2 and 0.1

        # Sanskrit terms density
        words = text.lower().split()
        sanskrit_word_count = 0
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.lexicons.corrections or clean_word in self.lexicons.proper_nouns:
                sanskrit_word_count += 1

        if len(words) > 0:
            sanskrit_word_ratio = sanskrit_word_count / len(words)
            score += min(0.5, sanskrit_word_ratio * 1.2)  # Increased from 0.4

        # English Context Indicators (REDUCED penalty to allow more Sanskrit processing)
        english_indicators = [
            r'\b(means?|refers?\s+to|explains?|this|that|what|how|why|when|where|which|who)\b',
            r'\b(chapter|section|verse|explains?|teaching|lecture|says?|telling|talking)\b',
            r'\b(the|and|is|are|was|were|will|would|could|should|can|may|might)\b',
            r'\b(in|on|at|to|from|with|by|for|of|about|through|during)\b',
            r'\b(but|however|therefore|because|since|although|while|if|unless)\b',
            r'\b(very|really|quite|just|only|even|also|still|already|yet)\b',
            r'\?$',  # Question ending
            r'\.{3}',  # Ellipsis indicating explanation
        ]

        english_penalty = 0.0
        for pattern in english_indicators:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                # REDUCED penalty for English function words (from 0.3 to 0.15)
                english_penalty += matches * 0.15

        # REDUCED penalty for high density of English function words
        words = text.lower().split()
        english_function_words = ['the', 'and', 'is', 'are', 'was', 'were', 'will', 'would', 'could',
                                'should', 'can', 'may', 'might', 'in', 'on', 'at', 'to', 'from',
                                'with', 'by', 'for', 'of', 'about', 'this', 'that', 'these', 'those']
        english_word_count = sum(1 for word in words if word in english_function_words)

        if len(words) > 0:
            english_density = english_word_count / len(words)
            if english_density > 0.5:  # More lenient threshold (was 0.3)
                english_penalty += 0.3  # Reduced from 0.5
            elif english_density > 0.3:  # More lenient threshold (was 0.2)
                english_penalty += 0.15  # Reduced from 0.3

            score -= english_penalty

        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def _is_sanskrit_context(self, text: str) -> bool:
        """Check if text contains Sanskrit/sacred content that should be preserved."""
        context = self.detect_context(text)
        return context in ['sanskrit', 'mixed']
    
    def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
        """Apply corrections from lexicon files with compound matching and fuzzy matching fallback."""
        corrections = 0
        original_text = text

        # 1. First pass: Compound term recognition (Story 6.1)
        if self.compound_matcher:
            text, compound_matches = self.compound_matcher.process_text(text)
            corrections += len(compound_matches)
            if compound_matches:
                logger.info(f"Compound corrections applied: {len(compound_matches)}")
                for match in compound_matches:
                    logger.debug(f"  Compound: '{match.original}' -> '{match.corrected}'")
    
        # 2. Second pass: Individual word corrections (context-aware and preserve line structure)
        lines = text.split('\n')
        corrected_lines = []

        # Detect context for the entire text
        text_context = self.detect_context(text)

        # FIX: Read confidence threshold from correct config structure
        context_config = self.config.get('context_detection', {})
        confidence_threshold = context_config.get('thresholds', {}).get('confidence_threshold', 0.8)

        logger.info(f"Processing text with context: {text_context} (confidence threshold: {confidence_threshold})")
        logger.debug(f"Text sample: '{text[:100]}...'")

        word_corrections = 0
        for line in lines:
            words = line.split()
            corrected_words = []

            for word in words:
                original_word = word  # Keep track of original
                # Process word with context-aware punctuation preservation
                corrected_word = self._process_word_with_punctuation(word, text_context, confidence_threshold)
                corrected_words.append(corrected_word)

                # CRITICAL FIX: Only count as correction if word actually changed
                if corrected_word != original_word:
                    word_corrections += 1
                    logger.debug(f"Word correction ({text_context}): '{word}' -> '{corrected_word}'")

            corrected_lines.append(' '.join(corrected_words))

        corrections += word_corrections
        final_text = '\n'.join(corrected_lines)

        if final_text != original_text:
            logger.info(f"Total lexicon corrections: {corrections} (compounds: {len(compound_matches) if self.compound_matcher else 0}, words: {word_corrections})")

        return final_text, corrections
    
    def _process_word_with_punctuation(self, word: str, context: str = None, confidence_threshold: float = 0.8) -> str:
        """Process word while preserving punctuation and respecting context.

        This method implements the core fix for Story 12.4: Fix English Context Processing.
        It enables Sanskrit term corrections in English context with configurable higher thresholds,
        resolving the issue where English context was overly conservative.

        Args:
            word: Input word with potential punctuation
            context: Processing context ('english', 'sanskrit', 'mixed', None)
            confidence_threshold: Base confidence threshold for corrections (0.1-1.0)

        Returns:
            Corrected word with preserved punctuation

        Key Enhancements for Story 12.4:
            - English context now applies lexicon corrections with higher thresholds
            - Configuration-driven behavior via 'english_context_processing' config section
            - Backward compatibility through 'proper_nouns_only' rollback option
            - Enhanced safety checks prevent common English word corrections
        """
        # CRITICAL FIX: Skip processing if word contains Sanskrit diacriticals from compound processing
        # This prevents corruption of correctly processed compounds like "Yoga Vāsiṣṭha" -> "Yogavasistha"
        if re.search(r'[āīūṛṝḷēōṃṁṅñṇṭḍśṣḥ]', word):
            return word  # Already properly processed by compound matcher

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
        # Handles complex punctuation like quotes, ellipsis, multiple punctuation
        match = re.match(r'^(\W*)(\w+(?:\'\w+)*)(\W*)$', word)
        if not match:
            return word  # Fallback for complex cases
        
        prefix, clean_word, suffix = match.groups()
        original_clean_word = clean_word
        
        # Handle contractions and possessives properly
        # Example: "Krishna's" -> process "Krishna", preserve "'s"
        if "'" in clean_word:
            # For contractions like "don't" or possessives like "Krishna's"
            parts = clean_word.split("'")
            if len(parts) == 2 and parts[1].lower() in ['t', 's', 'd', 're', 've', 'll']:
                clean_word = parts[0]  # Process base word only
                suffix = "'" + parts[1] + suffix
        
        clean_lower = clean_word.lower()
        
        # Debug logging for key Sanskrit terms (development aid)
        debug_terms = ['suhya', 'vicharana', 'tanumanasi', 'yogavashistha', 'uttapatti', 'prakarna', 'sadgurum', 'brahman']
        is_debug_term = any(debug_term in clean_lower for debug_term in debug_terms)
        
        if is_debug_term:
            logger.info(f"🔍 DEBUG: Processing '{word}' -> clean_word: '{clean_word}', context: {context}")
        
        # Validate and normalize context parameter
        if context not in ['english', 'sanskrit', 'mixed', None]:
            context = 'mixed'  # Default to mixed for invalid context
            
        # Validate and bound confidence threshold
        confidence_threshold = max(0.1, min(1.0, confidence_threshold))

        # SAFETY CHECK: Protect common English words from correction
        # This is a curated list of high-frequency English words that should never be "corrected"
        # Story 12.4 enhancement: Reduced scope to allow more Sanskrit terms through
        common_english_words = {
            # Core English function words that should never be "corrected"
            'the', 'and', 'is', 'are', 'was', 'were', 'will', 'would', 'could', 'should',
            'can', 'may', 'might', 'in', 'on', 'at', 'to', 'from', 'with', 'by', 'for',
            'of', 'about', 'this', 'that', 'these', 'those', 'but', 'however', 'therefore',
            'because', 'since', 'although', 'while', 'if', 'unless', 'very', 'really',
            'quite', 'just', 'only', 'even', 'also', 'still', 'already', 'yet',
            # Common lecture/explanation words that might sound Sanskrit-like
            'means', 'refers', 'explains', 'says', 'tells', 'calls', 'gives', 'takes',
            'makes', 'does', 'goes', 'comes', 'gets', 'puts', 'sees', 'knows', 'thinks',
            'feels', 'seems', 'looks', 'becomes', 'appears', 'happens', 'occurs',
            # Educational/spiritual context words
            'teaching', 'lecture', 'chapter', 'section', 'verse', 'student', 'teacher',
            'master', 'practice', 'study', 'learn', 'understand', 'realize', 'experience',
            # Prevent common mistranslations
            'what', 'how', 'why', 'when', 'where', 'which', 'who', 'whose', 'whom'
        }

        if clean_lower in common_english_words:
            if is_debug_term:
                logger.info(f"🔍 DEBUG: Skipping correction for common English word: '{clean_word}'")
            return word  # Return original word with punctuation intact

        corrections_file = self.lexicon_dir / "corrections.yaml"
        corrected = clean_word  # Default to no change
        
        try:
            # STORY 12.4 CORE ENHANCEMENT: Configuration-driven English context processing
            # Read configuration for English context behavior control
            english_config = self.config.get('processing', {}).get('english_context_processing', {})
            enable_lexicon = english_config.get('enable_lexicon_corrections', True)
            threshold_increase = english_config.get('threshold_increase', 0.15)
            max_threshold = english_config.get('max_threshold', 0.95)
            proper_nouns_only = english_config.get('proper_nouns_only', False)
            
            if context == 'english':
                # ENHANCED ENGLISH CONTEXT PROCESSING (Story 12.4 Fix)
                # Previous behavior: Only corrected proper nouns, ignored all other Sanskrit terms
                # New behavior: Apply lexicon corrections with higher confidence thresholds
                
                # First check proper nouns (preserves existing logic)
                if hasattr(self.lexicons, 'proper_nouns') and clean_lower in self.lexicons.proper_nouns:
                    entry = self.lexicons.proper_nouns[clean_lower]
                    if isinstance(entry, dict):
                        corrected = entry.get('term', clean_word)
                    else:
                        corrected = str(entry) if entry else clean_word
                    if is_debug_term:
                        logger.info(f"🔍 DEBUG: English context - proper noun correction: '{clean_word}' -> '{corrected}'")
                        
                elif enable_lexicon and not proper_nouns_only:
                    # NEW FOR STORY 12.4: Apply general lexicon corrections with higher threshold
                    # This is the core fix that resolves inconsistent Sanskrit term processing
                    english_threshold = min(max_threshold, confidence_threshold + threshold_increase)
                    corrected = self._get_best_correction(clean_lower, corrections_file, english_threshold)
                    if corrected != clean_word and is_debug_term:
                        logger.info(f"🔍 DEBUG: English context - lexicon correction: '{clean_word}' -> '{corrected}' (threshold: {english_threshold})")
                    elif corrected == clean_word and is_debug_term:
                        logger.info(f"🔍 DEBUG: English context - no correction for '{clean_word}' (threshold too high)")
                        
                else:
                    # Fallback to no correction (old behavior or config disabled)
                    # This path provides backward compatibility via 'proper_nouns_only: true'
                    corrected = clean_word
                    if is_debug_term:
                        logger.info(f"🔍 DEBUG: English context - no correction for '{clean_word}' (lexicon disabled or proper_nouns_only mode)")
                        
            elif context == 'sanskrit':
                # In Sanskrit context, apply all corrections aggressively
                # Lower threshold for more liberal correction matching
                corrected = self._get_best_correction(clean_lower, corrections_file, max(0.5, confidence_threshold - 0.2))
                if is_debug_term:
                    logger.info(f"🔍 DEBUG: Sanskrit context - correction: '{clean_word}' -> '{corrected}'")
                    
            else:  # mixed context or None
                # In mixed context, apply corrections with reasonable threshold
                # Slightly more lenient than base threshold for mixed content
                adjusted_threshold = max(0.6, confidence_threshold - 0.1)
                corrected = self._get_best_correction(clean_lower, corrections_file, adjusted_threshold)
                if is_debug_term:
                    logger.info(f"🔍 DEBUG: Mixed context - correction: '{clean_word}' -> '{corrected}' (threshold: {adjusted_threshold})")
                    
        except Exception as e:
            # Graceful error handling - log and return original word
            # Prevents processing failures from breaking the entire pipeline
            logger.warning(f"Error processing word '{clean_word}': {e}")
            corrected = clean_word
        
        # If no correction found, keep original
        if corrected == clean_lower or not corrected:
            corrected = clean_word
            if is_debug_term:
                logger.info(f"🔍 DEBUG: No correction applied for '{clean_word}', keeping original")
        
        # Apply intelligent capitalization preservation (Story 11.2 integration)
        # Maintains proper capitalization based on original word and correction rules
        if clean_word and corrected and corrected != clean_word:
            # Find the correction entry to check for preserve_capitalization flag
            correction_entry = {}
            if hasattr(self.lexicons, 'corrections') and clean_lower in self.lexicons.corrections:
                correction_entry = self.lexicons.corrections[clean_lower]

            # Use CapitalizationPreserver for intelligent capitalization
            corrected = self.capitalization_preserver.apply_capitalization(clean_word, corrected, correction_entry)
            
            if is_debug_term:
                logger.info(f"🔍 DEBUG: After capitalization: '{clean_word}' -> '{corrected}'")
        
        # Reconstruct word with preserved punctuation
        result = prefix + corrected + suffix
        
        # Final validation - ensure result is reasonable
        # Prevents unreasonable text expansion that could indicate processing errors
        if not result or len(result) > len(word) * 3:  # 3x expansion limit
            if is_debug_term:
                logger.warning(f"🔍 DEBUG: Result validation failed for '{word}', returning original")
            return word
        
        if is_debug_term and result != word:
            logger.info(f"🔍 DEBUG: Final result: '{word}' -> '{result}'")
            
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
            
            # CRITICAL FIX: Apply transliterations with diacritics when enabled
            if use_diacritics and isinstance(entry, dict) and 'transliteration' in entry:
                corrected = entry['transliteration']
                logger.debug(f"Applied diacritics: {clean_lower} -> {corrected}")
            elif isinstance(entry, dict) and 'original_term' in entry:
                corrected = entry['original_term']
            elif isinstance(entry, dict):
                # Fallback to any available term
                corrected = entry.get('term', entry.get('transliteration', clean_lower))
            else:
                corrected = str(entry) if entry else clean_lower
                
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
        
        return clean_lower  # No suitable correction found  # No suitable correction found

    def _contains_processed_compound_terms(self, text: str) -> bool:
        """
        CRITICAL FIX: Detect if text contains properly processed compound terms.

        This prevents the capitalization processor from corrupting compounds like
        "Yoga Vāsiṣṭha" → "Yogavasistha".
        """
        # Check for Sanskrit diacriticals that indicate proper processing
        if re.search(r'[āīūṛṝḷēōṃṁṅñṇṭḍśṣḥ]', text):
            # Additional check: if it contains compound title patterns
            compound_patterns = [
                r'Yoga\s+[VvV][āa]si[sṣś][tṭṭh][ha]',  # "Yoga Vāsiṣṭha" etc
                r'Bhagavad\s+G[īi]t[āa]',              # "Bhagavad Gītā" etc
                r'[A-Z]\w+\s+[A-Z][āīūṛṝḷēōṃṁṅñṇṭḍśṣḥ]\w+',  # General pattern: "Title Diacritical..."
            ]

            for pattern in compound_patterns:
                if re.search(pattern, text):
                    return True

        return False

    def _apply_capitalization(self, text: str) -> tuple[str, int]:
        """Apply proper noun capitalization."""
        corrections = 0
        lines = text.split('\n')
        corrected_lines = []

        proper_nouns_file = self.lexicon_dir / "proper_nouns.yaml"

        for line in lines:
            # CRITICAL FIX: Skip capitalization if line contains correctly processed compound terms
            # This prevents "Yoga Vāsiṣṭha" from being corrupted to "Yogavasistha"
            if self._contains_processed_compound_terms(line):
                corrected_lines.append(line)
                continue

            words = line.split()
            corrected_words = []

            for word in words:
                clean_word = re.sub(r'[^\w\s]', '', word.lower())
                original_word = word  # Keep track of original for comparison

                # Try cache first
                cached_proper_noun = self.lexicon_cache.get_proper_noun(clean_word, proper_nouns_file)
                if cached_proper_noun is not None:
                    # CRITICAL FIX: Only count as correction if it actually changes the word
                    if cached_proper_noun != original_word:
                        # Record metrics if collecting
                        if self.metrics_collector:
                            self.metrics_collector.start_correction('capitalization', word)
                            self.metrics_collector.end_correction('capitalization', word, cached_proper_noun, 1.0)

                        corrections += 1
                        logger.debug(f"Cached capitalization: {word} -> {cached_proper_noun}")

                    corrected_words.append(cached_proper_noun)
                    continue

                # Try lexicon lookup
                if clean_word in self.lexicons.proper_nouns:
                    entry = self.lexicons.proper_nouns[clean_word]
                    corrected = entry.get('term') or entry.get('original_term', word)

                    # Cache the result
                    self.lexicon_cache.cache_proper_noun(clean_word, corrected, proper_nouns_file)

                    # CRITICAL FIX: Only count as correction if it actually changes the word
                    if corrected != original_word:
                        # Record metrics if collecting
                        if self.metrics_collector:
                            self.metrics_collector.start_correction('capitalization', word)
                            self.metrics_collector.end_correction('capitalization', word, corrected, 1.0)

                        corrections += 1
                        logger.debug(f"Capitalization: {word} -> {corrected}")

                    corrected_words.append(corrected)
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
        best_entry = None
        
        for lexicon_term, entry in self.lexicons.corrections.items():
            similarity = self._calculate_similarity(word, lexicon_term)
            if similarity > threshold and similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry
                
        if best_entry:
            # CRITICAL FIX: Apply transliterations for fuzzy matches too
            use_diacritics = self.config.get('processing', {}).get('use_iast_diacritics', False)
            
            if use_diacritics and isinstance(best_entry, dict) and 'transliteration' in best_entry:
                best_match = best_entry['transliteration']
                logger.debug(f"Fuzzy match with diacritics: {word} -> {best_match} (similarity: {best_similarity:.2f})")
            elif isinstance(best_entry, dict) and 'original_term' in best_entry:
                best_match = best_entry['original_term']
            elif isinstance(best_entry, dict):
                best_match = best_entry.get('term', best_entry.get('transliteration', word))
            else:
                best_match = str(best_entry) if best_entry else None
                
        return best_match
    
    def process_srt_file(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> ProcessingResult:
        """Process an SRT file with Sanskrit corrections, comprehensive metrics, and optional JSON metadata enhancement."""
        import time
        start_time = time.time()

        # Convert strings to Path objects for consistent handling
        input_path = Path(input_path) if isinstance(input_path, str) else input_path
        output_path = Path(output_path) if isinstance(output_path, str) else output_path

        logger.info(f"Processing SRT file: {input_path} -> {output_path}")

        # Load optional JSON metadata for enhanced processing
        metadata = self._load_metadata(str(input_path))
        if metadata:
            logger.info(f"Enhanced processing enabled with metadata for {len(metadata.get('segments', []))} segments")
        else:
            logger.debug("Processing with standard mode (no metadata file found)")
        
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

            # Initialize LID statistics tracking
            lid_stats = {
                'english_preserved': 0,
                'sanskrit_aggressive': 0,
                'hindi_processed': 0,
                'mixed_conservative': 0,
                'uncertain_standard': 0
            }

            for i, segment in enumerate(segments, 1):
                try:
                    # Priority 1: LID-aware processing if metadata available
                    if self.use_lid_metadata:
                        processed_text, corrections, stat_type = self._process_with_lid(segment.text, i)
                        segment.text = processed_text
                        total_corrections += corrections
                        lid_stats[stat_type] += 1
                    else:
                        # Priority 2: Legacy metadata hints (if available)
                        segment_meta = self._get_segment_metadata(metadata, i - 1)

                        # Apply metadata hints if available
                        if segment_meta:
                            hints = self._apply_metadata_hints(segment.text, segment_meta)
                            logger.debug(f"Segment {i}: Applied metadata hints - {hints}")

                            # Process with metadata-enhanced parameters
                            processed_text, corrections = self.process_text_with_metadata(segment.text, hints)
                        else:
                            # Standard processing without metadata
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

            # Post-processing: Artifact filtering (if enabled)
            if self.artifact_filter:
                artifacts_removed = 0
                filter_start = time.time()

                for i, segment in enumerate(segments):
                    # Calculate segment duration from SRT timestamps
                    duration = self._calculate_duration(segment.start_time, segment.end_time)

                    # Get context from adjacent segments
                    prev_text = segments[i-1].text if i > 0 else ""
                    next_text = segments[i+1].text if i < len(segments) - 1 else ""

                    # Apply filter
                    filtered_text, removed = self.artifact_filter.filter_segment(
                        segment.text, duration, prev_text, next_text
                    )

                    segment.text = filtered_text
                    artifacts_removed += removed

                filter_time = time.time() - filter_start
                logger.info(f"Artifact filter: Removed {artifacts_removed} artifacts in {filter_time:.2f}s")

                # Log detailed statistics
                stats = self.artifact_filter.get_statistics()
                for pattern_type, count in stats['by_pattern_type'].items():
                    logger.debug(f"  {pattern_type}: {count}")

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
            
            # Log LID statistics if LID-aware processing was used
            if self.use_lid_metadata:
                logger.info(f"LID-aware processing statistics:")
                logger.info(f"  English preserved: {lid_stats['english_preserved']}")
                logger.info(f"  Sanskrit aggressive: {lid_stats['sanskrit_aggressive']}")
                logger.info(f"  Hindi processed: {lid_stats['hindi_processed']}")
                logger.info(f"  Mixed conservative: {lid_stats['mixed_conservative']}")
                logger.info(f"  Uncertain standard: {lid_stats['uncertain_standard']}")

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
