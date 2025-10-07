#!/usr/bin/env python3
"""
Enhanced Sanskrit Processor with MCP and API Integration
Builds on the lean core with external service capabilities.
"""

import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from sanskrit_processor_v2 import SanskritProcessor, ProcessingResult, SRTSegment
from services.external import SimpleFallbackNER, ExternalClients, ExternalServiceManager
from processors.context_detector import ContextDetector
# Optional imports for external services
try:
    from services.mcp_client import MCPClient
except ImportError:
    MCPClient = None
try:
    from services.api_client import ExternalAPIClient  
except ImportError:
    ExternalAPIClient = None

logger = logging.getLogger(__name__)

class EnhancedSanskritProcessor(SanskritProcessor):
    """Enhanced processor with MCP and external API integration."""
    
    def __init__(self, lexicon_dir: Path = None, config_path: Path = None, metadata_path: Path = None):
        """Initialize with enhanced services and optional LID metadata."""
        # Initialize base processor with metrics collection enabled
        super().__init__(lexicon_dir, collect_metrics=True, metadata_path=metadata_path)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize prayer recognizer
        try:
            from processors.prayer_recognizer import SanskritPrayerRecognizer
            self.prayer_recognizer = SanskritPrayerRecognizer()
            logger.info("Sanskrit prayer recognizer initialized")
        except ImportError as e:
            logger.warning(f"Prayer recognizer not available: {e}")
            self.prayer_recognizer = None
        
        # Initialize systematic processors
        try:
            from processors.systematic_term_matcher import SystematicTermMatcher
            from processors.compound_word_processor import SanskritCompoundProcessor
            
            self.systematic_matcher = SystematicTermMatcher(lexicon_dir)
            self.compound_processor = SanskritCompoundProcessor()
            logger.info(f"Systematic processors initialized: {len(self.systematic_matcher.scripture_terms)} terms loaded")
        except ImportError as e:
            logger.warning(f"Systematic processors not available: {e}")
            self.systematic_matcher = None
            self.compound_processor = None
        
        # Initialize external services (consolidated or legacy based on feature flag)
        if self.config.get('processing', {}).get('use_consolidated_services', False):
            # New consolidated approach
            self.external_services = ExternalServiceManager(self.config)
            self.external_clients = None  # Legacy not used
            logger.info("Using consolidated external services")
        else:
            # Legacy approach (during transition) - need to map config structure
            legacy_config = {
                'mcp': self.config.get('services', {}).get('consolidated', {}).get('mcp', {}),
                'api': self.config.get('services', {}).get('consolidated', {}).get('api', {})
            }
            self.external_clients = ExternalClients(legacy_config)
            self.external_services = None  # Consolidated not used
            logger.info("Using legacy external clients")
        
        # Initialize simple NER fallback
        entities_file = Path(self.config.get('ner', {}).get('fallback', {}).get('entities_file', 'data/entities.yaml'))
        self.simple_ner = SimpleFallbackNER(entities_file if entities_file.exists() else None)
        
        # Initialize enhanced context detector with configuration
        try:
            from processors.context_config import ContextConfig

            # Create context config from main configuration
            context_config = ContextConfig.from_dict(self.config)
            self.context_detector = ContextDetector(context_config=context_config)
            logger.info(f"Enhanced context detector initialized with {len(context_config.sanskrit_priority_terms)} priority terms")
        except ImportError as e:
            # Fallback to legacy context detector if new one not available
            logger.warning(f"Enhanced context detector not available, using legacy: {e}")
            self.context_detector = ContextDetector()
            logger.info("Legacy context detector initialized for English protection")

        # Initialize mixed content processors
        try:
            from processors.invocation_processor import InvocationProcessor
            from processors.mixed_content_parser import MixedContentParser
            from processors.surgical_editor import SurgicalEditor

            self.invocation_processor = InvocationProcessor()
            self.mixed_content_parser = MixedContentParser()
            self.surgical_editor = SurgicalEditor()

            logger.info("Mixed content processors initialized (invocation, parser, surgical editor)")
        except ImportError as e:
            logger.warning(f"Mixed content processors not available: {e}")
            self.invocation_processor = None
            self.mixed_content_parser = None
            self.surgical_editor = None

        logger.info("Enhanced Sanskrit processor initialized")
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration using advanced ConfigManager with environment support."""
        # Import ConfigManager here to avoid circular imports
        from utils.config_manager import ConfigManager
        
        try:
            # Try advanced configuration management first
            config_manager = ConfigManager()
            config = config_manager.load_config()
            logger.info(f"Advanced configuration loaded for environment: {config_manager.environment}")
            # Validate scripture lookup configuration
            self._validate_scripture_config(config)
            return config
        except FileNotFoundError:
            # Fallback to legacy single config file loading
            if config_path and config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        logger.info(f"Legacy configuration loaded from {config_path}")
                        # Validate scripture lookup configuration
                        self._validate_scripture_config(config)
                        return config
                except Exception as e:
                    logger.error(f"Failed to load legacy config: {e}")
            
            logger.info("Using default configuration")
            default_config = self._get_default_config()
            return default_config
        except Exception as e:
            # Log the error but don't fail completely - fallback to legacy loading
            logger.warning(f"Advanced configuration loading failed, using fallback: {e}")
            
            if config_path and config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        logger.info(f"Fallback configuration loaded from {config_path}")
                        # Validate scripture lookup configuration
                        self._validate_scripture_config(config)
                        return config
                except Exception as fallback_error:
                    logger.error(f"Fallback config loading also failed: {fallback_error}")
            
            logger.warning("All config loading failed, using safe defaults")
            return self._get_default_config()
    
    def _validate_scripture_config(self, config: Dict[str, Any]) -> None:
        """Validate scripture lookup configuration settings."""
        processing = config.get('processing', {})
        
        # Validate scripture lookup settings
        if 'enable_scripture_lookup' in processing:
            if not isinstance(processing['enable_scripture_lookup'], bool):
                logger.warning("Invalid enable_scripture_lookup setting, must be boolean. Using default: True")
                processing['enable_scripture_lookup'] = True
        
        # Validate external service URLs if scripture lookup is enabled
        if processing.get('enable_scripture_lookup', True):
            external = config.get('external', {})
            if external:
                # Validate API endpoints
                api_endpoints = external.get('api_endpoints', {})
                if api_endpoints:
                    scripture_url = api_endpoints.get('scripture_lookup', '')
                    if scripture_url and not scripture_url.startswith(('http://', 'https://')):
                        logger.warning(f"Invalid scripture lookup URL: {scripture_url}. Must start with http:// or https://")
                
                # Validate confidence thresholds
                thresholds = external.get('confidence_thresholds', {})
                if thresholds:
                    scripture_confidence = thresholds.get('scripture', 0.9)
                    if not isinstance(scripture_confidence, (int, float)) or not 0.0 <= scripture_confidence <= 1.0:
                        logger.warning(f"Invalid scripture confidence threshold: {scripture_confidence}. Must be between 0.0 and 1.0. Using default: 0.9")
                        thresholds['scripture'] = 0.9
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get safe default configuration with scripture lookup disabled."""
        return {
            'processing': {
                'enable_scripture_lookup': False,  # Disabled by default for safety
                'enable_systematic_matching': True,
                'enable_compound_processing': True,
                'enable_semantic_analysis': False
            },
            'external': {
                'confidence_thresholds': {
                    'scripture': 0.9
                },
                'api_endpoints': {}
            }
        }
    
    def _get_ner_client(self):
        """Get NER client with automatic fallback logic."""
        # Check if using consolidated services
        if self.external_services:
            # Consolidated approach - check if MCP is available
            if self.config.get('processing', {}).get('enable_semantic_analysis', True):
                return self.external_services  # Will handle MCP internally
        else:
            # Legacy approach
            if (self.external_clients and self.external_clients.mcp_client and 
                self.config.get('processing', {}).get('enable_semantic_analysis', True)):
                return self.external_clients.mcp_client
        
        # Fallback to Simple NER
        if self.simple_ner:
            logger.info("Using Simple NER fallback")
            return self.simple_ner
        
        return None
    
    def extract_entities(self, text: str) -> list:
        """Extract named entities with automatic fallback."""
        ner_client = self._get_ner_client()
        
        if not ner_client:
            return []
        
        try:
            if hasattr(ner_client, 'extract_entities'):
                # Simple NER
                return ner_client.extract_entities(text)
            else:
                # MCP client - would need specific method call
                # This is a placeholder for MCP NER integration
                return []
        except Exception as e:
            logger.debug(f"Entity extraction failed: {e}")
            return []
    
    def process_text(self, text: str, context: Dict = None) -> tuple[str, int]:
        """Enhanced text processing with context-aware protection and per-segment overrides.
        
        FIXED: If context pipeline is disabled, use parent's simple processing method.
        
        Args:
            text: Input text to process
            context: Optional context dictionary that can include:
                - force_processing: bool - Force processing regardless of context
                - segment_type: str - Override detected segment type ('sanskrit', 'english', 'mixed')
                - threshold_overrides: dict - Override specific thresholds for this segment
                - debug_segment: bool - Enable debug logging for this specific segment
                
        Returns:
            Tuple of (processed_text, corrections_count)
        """
        if not text or not text.strip():
            return text, 0
        
        # CRITICAL FIX: Check if context pipeline is disabled in config
        enable_context_pipeline = self.config.get('processing', {}).get('enable_context_pipeline', True)
        
        if not enable_context_pipeline:
            # Context pipeline disabled - use parent's simple legacy processing
            return super().process_text(text)
        
        # Context pipeline enabled - use enhanced processing with context detection
        processed_text = text
        total_corrections = 0
        
        # Initialize context if not provided
        if context is None:
            context = {}
        
        # Check for segment-level debug override
        debug_enabled = context.get('debug_segment', False) or (
            hasattr(self.context_detector, 'config') and 
            self.context_detector.config.debug_logging
        )
        
        # STEP 0: Check for manual segment type override
        if 'segment_type' in context:
            override_type = context['segment_type']
            if debug_enabled:
                logger.debug(f"🔧 Segment type manually overridden to: {override_type}")
            
            if override_type == 'english':
                if debug_enabled:
                    logger.debug("Manual override: bypassing processing (English)")
                return text, 0
            elif override_type == 'sanskrit':
                if debug_enabled:
                    logger.debug("Manual override: applying full Sanskrit processing")
                return self._process_sanskrit_segment(text, context)
            elif override_type == 'mixed':
                # Force mixed content analysis even if context detection would suggest otherwise
                if debug_enabled:
                    logger.debug("Manual override: forcing mixed content analysis")
                context_result = self.context_detector.analyze_mixed_content(text)
                return self._process_mixed_content(text, context_result, context)
        
        # Check for force processing override
        if context.get('force_processing', False):
            if debug_enabled:
                logger.debug("🔧 Force processing enabled - bypassing context detection")
            return self._process_sanskrit_segment(text, context)
        
        # Apply threshold overrides if provided
        original_config = None
        if 'threshold_overrides' in context and hasattr(self.context_detector, 'config'):
            original_config = {
                'english_threshold': self.context_detector.config.english_threshold,
                'sanskrit_threshold': self.context_detector.config.sanskrit_threshold,
                'mixed_threshold': self.context_detector.config.mixed_threshold
            }
            
            overrides = context['threshold_overrides']
            if 'english_threshold' in overrides:
                self.context_detector.config.english_threshold = overrides['english_threshold']
            if 'sanskrit_threshold' in overrides:
                self.context_detector.config.sanskrit_threshold = overrides['sanskrit_threshold']
            if 'mixed_threshold' in overrides:
                self.context_detector.config.mixed_threshold = overrides['mixed_threshold']
            
            if debug_enabled:
                logger.debug(f"🔧 Applied threshold overrides: {overrides}")
        
        try:
            # STEP 1: CONTEXT DETECTION GATE (CRITICAL - Prevents English→Sanskrit translation bugs)
            context_result = self.context_detector.detect_context(text)
            
            if debug_enabled or (hasattr(self.context_detector, 'config') and self.context_detector.config.debug_logging):
                logger.debug(f"🔍 Context detected: {context_result.context_type} (confidence: {context_result.confidence:.2f})")
                if hasattr(context_result, 'override_reason') and context_result.override_reason:
                    logger.debug(f"🔍 Override reason: {context_result.override_reason}")
                logger.debug(f"🔍 Markers found: {context_result.markers_found}")
            
            # Handle different context types
            if context_result.context_type == 'english':
                # English context: Pass through unchanged (ZERO MODIFICATIONS)
                if debug_enabled:
                    logger.debug(f"English context detected, bypassing all processing: {context_result.markers_found}")
                return text, 0

            elif context_result.context_type == 'invocation':
                # Invocation/prayer: Use specialized invocation processor
                return self._process_invocation(text, context_result, context)

            elif context_result.context_type == 'corrupted_sanskrit':
                # Corrupted Sanskrit: Use surgical editor
                return self._process_corrupted_sanskrit(text, context_result, context)

            elif context_result.context_type == 'mixed':
                # Mixed content: Use mixed content parser with embedded term processing
                if hasattr(context_result, 'processing_mode') and context_result.processing_mode == 'embedded_correction':
                    return self._process_embedded_terms(text, context_result, context)
                else:
                    return self._process_mixed_content(text, context_result, context)

            elif context_result.context_type == 'sanskrit':
                # Sanskrit context: Full processing pipeline
                if debug_enabled:
                    logger.debug(f"Sanskrit context detected, applying full processing: {context_result.markers_found}")
                return self._process_sanskrit_segment(text, context)

            else:
                # Unknown context: Default to safe mode (no processing)
                if debug_enabled:
                    logger.debug(f"Unknown context type: {context_result.context_type}, defaulting to safe mode")
                return text, 0
                
        finally:
            # Restore original thresholds if they were overridden
            if original_config and hasattr(self.context_detector, 'config'):
                self.context_detector.config.english_threshold = original_config['english_threshold']
                self.context_detector.config.sanskrit_threshold = original_config['sanskrit_threshold']
                self.context_detector.config.mixed_threshold = original_config['mixed_threshold']
                
                if debug_enabled:
                    logger.debug("🔧 Restored original threshold configuration")    
    def _process_mixed_content(self, text: str, context_result: 'ContextResult', context: Dict = None) -> tuple[str, int]:
        """Process mixed content with enhanced segment handling.
        
        Args:
            text: Input text
            context_result: Result from context detection
            context: Processing context with potential overrides
            
        Returns:
            Tuple of (processed_text, corrections_count)
        """
        if context is None:
            context = {}
        
        debug_enabled = context.get('debug_segment', False) or (
            hasattr(self.context_detector, 'config') and 
            self.context_detector.config.debug_logging
        )
        
        total_corrections = 0
        
        if context_result.segments:
            words = text.split()
            modified_words = words.copy()
            
            # Process segments in reverse order to preserve word indices
            for start_idx, end_idx, segment_type in reversed(context_result.segments):
                if segment_type == 'sanskrit':
                    segment_text = ' '.join(words[start_idx:end_idx])
                    
                    # Create segment-specific context
                    segment_context = context.copy()
                    segment_context['segment_bounds'] = (start_idx, end_idx)
                    segment_context['parent_text'] = text
                    
                    segment_processed, segment_corrections = self._process_sanskrit_segment(segment_text, segment_context)
                    
                    if segment_corrections > 0:
                        # Replace segment words with processed version
                        processed_segment_words = segment_processed.split()
                        modified_words[start_idx:end_idx] = processed_segment_words
                        total_corrections += segment_corrections
                        
                        if debug_enabled:
                            logger.debug(f"🔍 Processed Sanskrit segment [{start_idx}:{end_idx}]: '{segment_text}' -> '{segment_processed}' ({segment_corrections} corrections)")
            
            processed_text = ' '.join(modified_words)
            return processed_text, total_corrections
        else:
            # No Sanskrit segments found in mixed content, treat as English
            if debug_enabled:
                logger.debug("Mixed content with no Sanskrit segments, bypassing processing")
            return text, 0

    def _process_invocation(self, text: str, context_result: 'ContextResult', context: Dict = None) -> tuple[str, int]:
        """Process invocations and prayers with specialized formatting."""
        if not self.invocation_processor:
            # Fallback to Sanskrit processing
            return self._process_sanskrit_segment(text, context)

        try:
            result = self.invocation_processor.process_invocation(text)
            if result.is_invocation and result.processed_text != text:
                logger.debug(f"Invocation processed: {result.invocation_type} (confidence: {result.confidence:.2f})")
                logger.debug(f"Corrections: {result.corrections_made}")
                return result.processed_text, len(result.corrections_made)
            else:
                # Not recognized as invocation, fallback to Sanskrit processing
                return self._process_sanskrit_segment(text, context)
        except Exception as e:
            logger.warning(f"Invocation processing failed: {e}")
            return self._process_sanskrit_segment(text, context)

    def _process_corrupted_sanskrit(self, text: str, context_result: 'ContextResult', context: Dict = None) -> tuple[str, int]:
        """Process corrupted Sanskrit using surgical editing."""
        if not self.surgical_editor:
            # Fallback to Sanskrit processing
            return self._process_sanskrit_segment(text, context)

        try:
            # Determine edit mode based on context confidence
            edit_mode = 'conservative' if context_result.confidence < 0.8 else 'moderate'
            result = self.surgical_editor.perform_surgical_edit(text, edit_mode)

            if result.success and result.edited_text != text:
                logger.debug(f"Surgical edit applied: {result.edit_count} edits (confidence: {result.confidence:.2f})")
                for edit in result.edits_applied:
                    logger.debug(f"  {edit.original_text} → {edit.replacement_text} ({edit.reason})")
                return result.edited_text, result.edit_count
            else:
                # No surgical edits applied, fallback to Sanskrit processing
                return self._process_sanskrit_segment(text, context)
        except Exception as e:
            logger.warning(f"Surgical editing failed: {e}")
            return self._process_sanskrit_segment(text, context)

    def _process_embedded_terms(self, text: str, context_result: 'ContextResult', context: Dict = None) -> tuple[str, int]:
        """Process mixed content with embedded Sanskrit terms."""
        if not self.mixed_content_parser:
            # Fallback to mixed content processing
            return self._process_mixed_content(text, context_result, context)

        try:
            result = self.mixed_content_parser.parse_mixed_content(text)

            if result.corrections_count > 0:
                logger.debug(f"Mixed content processed: {result.processing_mode} (confidence: {result.confidence:.2f})")
                for term in result.embedded_terms:
                    logger.debug(f"  {term.original} → {term.corrected} ({term.term_type})")
                return result.processed_text, result.corrections_count
            else:
                # No embedded terms found, preserve text
                return text, 0
        except Exception as e:
            logger.warning(f"Mixed content parsing failed: {e}")
            return text, 0

    def _process_sanskrit_segment(self, text: str, context: Dict = None) -> tuple[str, int]:
        """Process a confirmed Sanskrit text segment through the full pipeline."""
        processed_text = text
        total_corrections = 0
        
        # Step 1: Systematic term matching (HIGHEST PRIORITY)
        if self.systematic_matcher and self.config.get('processing', {}).get('enable_systematic_matching', True):
            try:
                systematic_text, systematic_corrections = self.systematic_matcher.apply_corrections(processed_text)
                if systematic_corrections:
                    processed_text = systematic_text
                    total_corrections += len(systematic_corrections)
                    logger.debug(f"Applied {len(systematic_corrections)} systematic corrections")
            except Exception as e:
                logger.debug(f"Systematic matching skipped: {e}")
        
        # Step 2: Compound word processing
        if self.compound_processor and self.config.get('processing', {}).get('enable_compound_processing', True):
            try:
                compound_candidates = self.compound_processor.find_compound_candidates(processed_text)
                for original, corrected in compound_candidates:
                    if original != corrected:
                        processed_text = processed_text.replace(original, corrected)
                        total_corrections += 1
                        logger.debug(f"Applied compound correction: {original} → {corrected}")
            except Exception as e:
                logger.debug(f"Compound processing skipped: {e}")
        
        # Step 3: Prayer recognition and formatting
        if self.prayer_recognizer:
            try:
                prayer_match = self.prayer_recognizer.recognize_prayer(processed_text)
                if prayer_match and prayer_match.confidence > 0.7:
                    processed_text = prayer_match.corrected_text
                    total_corrections += 1
                    logger.debug(f"Applied prayer correction: {prayer_match.prayer_name}")
                else:
                    # Try basic prayer formatting
                    formatted_text, was_prayer = self.prayer_recognizer.format_prayer_text(processed_text)
                    if was_prayer and formatted_text != processed_text:
                        processed_text = formatted_text
                        total_corrections += 1
                        logger.debug("Applied prayer formatting")
            except Exception as e:
                logger.debug(f"Prayer recognition skipped: {e}")
        
        # Step 4: Base lexicon processing (final cleanup)
        base_text, base_corrections = super().process_text(processed_text)
        processed_text = base_text
        total_corrections += base_corrections
        
        # Step 5: Apply MCP enhancements if available
        if self.config.get('processing', {}).get('enable_semantic_analysis', True):
            try:
                enhanced_text = None
                if self.external_services:
                    # Consolidated approach
                    enhanced_text = self.external_services.mcp_enhance_segment(processed_text)
                elif self.external_clients and self.external_clients.mcp_client:
                    # Legacy approach
                    enhanced_text = self.external_clients.mcp_client.context_correct(processed_text, 
                                                                  context.get('previous_text') if context else None)
                
                if enhanced_text and enhanced_text != processed_text:
                    processed_text = enhanced_text
                    total_corrections += 1
                    logger.debug("Applied MCP context correction")
            except Exception as e:
                logger.debug(f"MCP enhancement skipped: {e}")
        
        # Step 6: ENHANCED Scripture Processing with Multi-Source Fallback Chain
        if self.config.get('processing', {}).get('enable_scripture_lookup', True):
            scripture_processed_text, scripture_corrections = self._apply_scripture_processing(processed_text, context)
            if scripture_corrections > 0:
                processed_text = scripture_processed_text
                total_corrections += scripture_corrections
        
        return processed_text, total_corrections

    def _apply_scripture_processing(self, text: str, context: Dict = None) -> tuple[str, int]:
        """Apply scripture processing with fallback chain: API -> ScripturalSegmentProcessor -> VerseCache.
        
        FIXED: Implements comprehensive scripture processing with proper fallback logic.
        
        Args:
            text: Input text to process
            context: Processing context
            
        Returns:
            Tuple of (processed_text, corrections_count)
        """
        original_text = text
        
        # Skip very short or clearly English text  
        if len(text.strip()) < 3:
            return text, 0
            
        # Enhanced English detection - but less aggressive than before
        english_words = [
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'this', 'that', 'these', 'those', 'then', 'there', 'here', 'where', 'when',
            'you', 'your', 'he', 'she', 'it', 'his', 'her', 'its', 'we', 'our',
            'they', 'them', 'their', 'i', 'my', 'mine', 'me'
        ]
        
        words_in_text = [word.lower().strip('.,!?;:()[]{}"\'-') for word in text.split()]
        english_count = sum(1 for word in words_in_text if word in english_words and len(word) > 1)
        english_ratio = english_count / len(words_in_text) if words_in_text else 0
        
        # Skip if text is predominantly English (>60% English words)
        if english_ratio > 0.6:
            logger.debug(f"Scripture processing skipped: High English ratio ({english_ratio:.2f}) in text: '{text}'")
            return text, 0
        
        # PHASE 1: Try API scripture lookup (with relaxed validation)
        api_result = self._try_api_scripture_lookup(text)
        if api_result:
            processed_text, corrections = api_result
            logger.debug(f"API scripture lookup successful: '{text}' → '{processed_text}' ({corrections} corrections)")
            return processed_text, corrections
        
        # PHASE 2: Try ScripturalSegmentProcessor for pattern-based corrections
        scriptural_result = self._try_scriptural_segment_processor(text)
        if scriptural_result:
            processed_text, corrections = scriptural_result
            logger.debug(f"ScripturalSegmentProcessor successful: '{text}' → '{processed_text}' ({corrections} corrections)")
            return processed_text, corrections
        
        # PHASE 3: Try VerseCache for content-based matching
        verse_cache_result = self._try_verse_cache_lookup(text)
        if verse_cache_result:
            processed_text, corrections = verse_cache_result
            logger.debug(f"VerseCache lookup successful: '{text}' → '{processed_text}' ({corrections} corrections)")
            return processed_text, corrections
        
        # PHASE 4: No scripture processing applied
        logger.debug(f"No scripture processing applied to: '{text}'")
        return text, 0
    
    def _try_api_scripture_lookup(self, text: str) -> tuple[str, int] | None:
        """Try API-based scripture lookup with STRICT validation to prevent content corruption."""
        try:
            # Check for basic Sanskrit content indicators before API call
            sanskrit_indicators = ['om', 'oṃ', 'krishna', 'kṛṣṇa', 'gita', 'gītā', 'dharma', 'karma', 'yoga', 'arjuna']
            has_sanskrit_indicators = any(indicator in text.lower() for indicator in sanskrit_indicators)
            
            # Only try API if we have Sanskrit indicators OR existing diacriticals
            sanskrit_diacriticals = ['ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ḹ', 'ṃ', 'ṁ', 'ḥ', 'ś', 'ṣ', 'ñ', 'ṇ', 'ṭ', 'ḍ']
            has_diacriticals = any(char in text for char in sanskrit_diacriticals)
            
            if not (has_sanskrit_indicators or has_diacriticals):
                return None
            
            # Try API lookup
            scripture_match = None
            if self.external_services:
                scripture_match = self.external_services.api_lookup_scripture(text)
            elif self.external_clients and self.external_clients.api_client:
                scripture_match = self.external_clients.api_client.lookup_scripture(text)
            
            if not scripture_match:
                return None
            
            # STRICT validation to prevent content corruption
            confidence = getattr(scripture_match, 'confidence', 0.0)
            transliteration = getattr(scripture_match, 'transliteration', '')
            verse_ref = getattr(scripture_match, 'verse_reference', 'unknown')
            
            # Very high confidence threshold - only exact matches
            if confidence < 0.95:
                logger.debug(f"API scripture lookup: Low confidence ({confidence:.2f} < 0.95) for text: '{text}'")
                return None
            
            if not transliteration or len(transliteration.strip()) < 3:
                logger.debug(f"API scripture lookup: Invalid transliteration for text: '{text}'")
                return None
            
            # STRICT length validation - prevent complete text replacement
            length_ratio = len(transliteration) / len(text) if text else 0
            if length_ratio > 2.0 or length_ratio < 0.5:
                logger.debug(f"API scripture lookup: Excessive length change ratio {length_ratio:.2f} for text: '{text}'")
                return None
            
            # Block complete verse injections - these are content replacements, not corrections
            dangerous_patterns = [
                'bhagavad gītā chapter', 'verse number', 'śrīmad bhagavad gītā', 
                'thus speaks', 'arjuna said', 'kṛṣṇa said', 'bhagavān uvāca',
                '||', '|', 'chapter', 'verse'
            ]
            
            if any(pattern in transliteration.lower() for pattern in dangerous_patterns):
                logger.debug(f"API scripture lookup: Contains verse injection patterns in response for text: '{text}'")
                return None
            
            # CONTENT SIMILARITY CHECK - ensure API result is actually related to input
            original_words = set(text.lower().split())
            enhanced_words = set(transliteration.lower().split())
            
            # Require at least 30% word overlap for content similarity
            common_words = original_words.intersection(enhanced_words)
            similarity_ratio = len(common_words) / len(original_words) if original_words else 0
            
            if similarity_ratio < 0.3:
                logger.debug(f"API scripture lookup: Low content similarity ({similarity_ratio:.2f}) between '{text}' and '{transliteration}'")
                return None
            
            # Apply the enhancement only if it passes all strict validation
            logger.info(f"Applied API scripture enhancement: '{text}' → '{transliteration}' (confidence: {confidence:.2f}, ref: {verse_ref})")
            return transliteration, 1
            
        except Exception as e:
            logger.debug(f"API scripture lookup failed: {e}")
            return None
    
    def _try_scriptural_segment_processor(self, text: str) -> tuple[str, int] | None:
        """Try ScripturalSegmentProcessor for pattern-based corrections."""
        try:
            # Initialize ScripturalSegmentProcessor if not already done
            if not hasattr(self, 'scriptural_processor'):
                from processors.scriptural_segment_processor import ScripturalSegmentProcessor
                self.scriptural_processor = ScripturalSegmentProcessor(self.config)
                logger.debug("ScripturalSegmentProcessor initialized for fallback")
            
            # Process the segment
            processed_text, was_modified, reference = self.scriptural_processor.process_segment(text)
            
            if was_modified and processed_text != text:
                logger.debug(f"ScripturalSegmentProcessor correction: {reference or 'pattern-based'}")
                return processed_text, 1
            
            return None
            
        except Exception as e:
            logger.debug(f"ScripturalSegmentProcessor failed: {e}")
            return None
    
    def _try_verse_cache_lookup(self, text: str) -> tuple[str, int] | None:
        """Try VerseCache for content-based verse matching.
        
        CRITICAL FIX: Made much more conservative to prevent inappropriate verse substitutions.
        Only applies high-confidence exact matches, not broad content searches.
        """
        try:
            # Initialize verse cache if not already done
            if not hasattr(self, 'verse_cache_processor'):
                from services.verse_cache import VerseCache
                self.verse_cache_processor = VerseCache(self.config)
                
                # Download verses if cache is empty
                if not self.verse_cache_processor.is_cache_valid():
                    logger.info("Downloading verse cache for scripture processing...")
                    self.verse_cache_processor.download_verses()
                
                logger.debug(f"VerseCache initialized with {len(self.verse_cache_processor.verses)} verses")
            
            # CRITICAL: Only use verse cache for very specific patterns, not general content search
            # This prevents inappropriate verse substitutions
            
            # Check for explicit verse references (e.g., "gita 3.32", "bhagavad gita verse 47")
            verse_ref_patterns = [
                r'(?i)\b(?:gita|bhagavad\s*gita)\s*(?:verse\s*)?(\d+)\.(\d+)',
                r'(?i)\b(?:chapter\s*)?(\d+)\s*verse\s*(\d+)',
                r'(?i)\bverse\s*(\d+)\.(\d+)'
            ]
            
            for pattern in verse_ref_patterns:
                import re
                match = re.search(pattern, text)
                if match:
                    try:
                        chapter, verse = int(match.group(1)), int(match.group(2))
                        cached_verse = self.verse_cache_processor.get_verse(chapter, verse)
                        if cached_verse and hasattr(cached_verse, 'transliteration') and cached_verse.transliteration:
                            logger.debug(f"VerseCache reference match: {chapter}.{verse}")
                            return cached_verse.transliteration, 1
                    except (ValueError, AttributeError):
                        continue
            
            # REMOVED: General content search that was causing inappropriate replacements
            # The content search was too aggressive and replaced original text with unrelated verses
            
            return None
            
        except Exception as e:
            logger.debug(f"VerseCache lookup failed: {e}")
            return None
    
    def process_srt_file(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Enhanced SRT processing with batch optimizations.
        
        FIXED: If context pipeline is disabled, use parent's simple processing method.
        """
        import time
        start_time = time.time()
        
        # CRITICAL FIX: Check if context pipeline is disabled in config
        enable_context_pipeline = self.config.get('processing', {}).get('enable_context_pipeline', True)
        
        if not enable_context_pipeline:
            # Context pipeline disabled - use parent's simple SRT processing
            logger.info(f"Context pipeline disabled - using parent's simple processing: {input_path} -> {output_path}")
            return super().process_srt_file(input_path, output_path)
        
        # Context pipeline enabled - use enhanced processing
        logger.info(f"Enhanced processing: {input_path} -> {output_path}")
        
        try:
            # Read and parse (same as base)
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            from sanskrit_processor_v2 import SRTParser
            segments = SRTParser.parse(content)
            if not segments:
                raise ValueError("No valid SRT segments found")
            
            logger.info(f"Parsed {len(segments)} segments")
            
            # Enhanced processing with batching
            total_corrections = 0
            batch_size = self.config.get('processing', {}).get('batch_size', 10)
            
            # Process in batches for MCP efficiency
            for i in range(0, len(segments), batch_size):
                batch = segments[i:i+batch_size]
                
                # Prepare context for batch
                batch_context = {
                    'batch_index': i // batch_size,
                    'total_batches': (len(segments) + batch_size - 1) // batch_size
                }
                
                # Process each segment in batch
                for j, segment in enumerate(batch):
                    segment_context = {
                        'previous_text': segments[i+j-1].text if i+j > 0 else None,
                        'batch_context': batch_context
                    }
                    
                    processed_text, corrections = self.process_text(segment.text, segment_context)
                    segment.text = processed_text
                    total_corrections += corrections
                
                logger.debug(f"Processed batch {i//batch_size + 1}/{(len(segments) + batch_size - 1)//batch_size}")
            
            # Write output
            output_content = SRTParser.to_srt(segments)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                segments_processed=len(segments),
                corrections_made=total_corrections,
                processing_time=processing_time,
                errors=[]
            )
            
            logger.info(f"Enhanced processing complete: {len(segments)} segments, "
                       f"{total_corrections} corrections, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced processing failed: {e}")
            return ProcessingResult(
                segments_processed=0,
                corrections_made=0,
                processing_time=time.time() - start_time,
                errors=[str(e)]
            )
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all integrated services."""
        external_status = {}
        
        if self.external_services:
            # Consolidated services status
            external_status = self.external_services.get_service_status()
        elif self.external_clients:
            # Legacy services status
            external_status = {
                "mode": "legacy",
                "mcp_client": "available" if self.external_clients.mcp_client else "disabled",
                "api_client": "available" if self.external_clients.api_client else "disabled"
            }
        
        return {
            "base_processor": "active",
            "lexicons_loaded": {
                "corrections": len(self.lexicons.corrections),
                "proper_nouns": len(self.lexicons.proper_nouns)
            },
            "external_services": external_status,
            "simple_ner": "enabled" if self.simple_ner else "disabled"
        }
    
    def close(self):
        """Clean up external connections."""
        if self.external_services:
            self.external_services.close()
        elif self.external_clients:
            self.external_clients.close()
        logger.info("Enhanced processor closed")

if __name__ == "__main__":
    # Test enhanced processor
    processor = EnhancedSanskritProcessor(
        lexicon_dir=Path("lexicons"),
        config_path=Path("config.yaml")
    )
    
    # Test text processing
    test_text = "Welcome to this bhagavad gita lecture on dharma and yoga"
    result, corrections = processor.process_text(test_text)
    print(f"Enhanced Test: '{test_text}' -> '{result}' ({corrections} corrections)")
    
    # Show service status
    status = processor.get_service_status()
    print(f"Service Status: {status}")
    
    processor.close()