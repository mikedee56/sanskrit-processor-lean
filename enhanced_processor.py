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
    
    def __init__(self, lexicon_dir: Path = None, config_path: Path = None):
        """Initialize with enhanced services."""
        # Initialize base processor
        super().__init__(lexicon_dir)
        
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
        
        # Initialize context detector (CRITICAL: Prevents English→Sanskrit translation bugs)
        self.context_detector = ContextDetector()
        logger.info("Context detector initialized for English protection")
        
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
        """Enhanced text processing with context-aware protection and external services."""
        if not text or not text.strip():
            return text, 0
        
        processed_text = text
        total_corrections = 0
        
        # STEP 0: CONTEXT DETECTION GATE (CRITICAL - Prevents English→Sanskrit translation bugs)
        context_result = self.context_detector.detect_context(text)
        logger.debug(f"Context detected: {context_result.context_type} (confidence: {context_result.confidence:.2f})")
        
        # Handle different context types
        if context_result.context_type == 'english':
            # English context: Pass through unchanged (ZERO MODIFICATIONS)
            logger.debug(f"English context detected, bypassing all processing: {context_result.markers_found}")
            return text, 0
        
        elif context_result.context_type == 'mixed':
            # Mixed content: Process only Sanskrit segments
            if context_result.segments:
                words = text.split()
                modified_words = words.copy()
                
                # Process segments in reverse order to preserve word indices
                for start_idx, end_idx, segment_type in reversed(context_result.segments):
                    if segment_type == 'sanskrit':
                        segment_text = ' '.join(words[start_idx:end_idx])
                        segment_processed, segment_corrections = self._process_sanskrit_segment(segment_text, context)
                        
                        if segment_corrections > 0:
                            # Replace segment words with processed version
                            processed_segment_words = segment_processed.split()
                            modified_words[start_idx:end_idx] = processed_segment_words
                            total_corrections += segment_corrections
                            logger.debug(f"Processed Sanskrit segment [{start_idx}:{end_idx}]: {segment_corrections} corrections")
                
                processed_text = ' '.join(modified_words)
                return processed_text, total_corrections
            else:
                # No Sanskrit segments found in mixed content, treat as English
                logger.debug("Mixed content with no Sanskrit segments, bypassing processing")
                return text, 0
        
        elif context_result.context_type == 'sanskrit':
            # Sanskrit context: Full processing pipeline
            logger.debug(f"Sanskrit context detected, applying full processing: {context_result.markers_found}")
            return self._process_sanskrit_segment(text, context)
        
        else:
            # Unknown context: Default to safe mode (no processing)
            logger.debug(f"Unknown context type: {context_result.context_type}, defaulting to safe mode")
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
        
        # Step 6: Apply scripture lookup if available - ONLY for improving existing Sanskrit terms
        if self.config.get('processing', {}).get('enable_scripture_lookup', True):
            try:
                # CRITICAL: Only apply scripture lookup to segments that already contain Sanskrit diacriticals
                sanskrit_diacriticals = ['ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ḹ', 'ṁ', 'ṃ', 'ḥ', 'ś', 'ṣ', 'ñ', 'ṇ', 'ṭ', 'ḍ']
                has_diacriticals = any(char in processed_text for char in sanskrit_diacriticals)
                
                if not has_diacriticals:
                    logger.debug(f"Scripture lookup skipped: No Sanskrit diacriticals in text: '{processed_text}'")
                elif len(processed_text.split()) > 8:
                    logger.debug(f"Scripture lookup skipped: Text too long ({len(processed_text.split())} words > 8): '{processed_text[:50]}...'")
                else:
                    # Enhanced English word detection - expanded list of common English words
                    english_words = [
                        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                        'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
                        'this', 'that', 'these', 'those', 'then', 'there', 'here', 'where', 'when',
                        'you', 'your', 'yours', 'he', 'she', 'it', 'his', 'her', 'its', 'we', 'our', 'ours',
                        'they', 'them', 'their', 'theirs', 'i', 'my', 'mine', 'me',
                        'as', 'if', 'so', 'than', 'very', 'just', 'now', 'only', 'also', 'even',
                        'worship', 'succeed', 'business', 'given', 'bigger', 'extension', 'read', 'whole', 'tell'
                    ]
                    
                    # Check for English words in the text
                    words_in_text = [word.lower().strip('.,!?;:()[]{}"\'-') for word in processed_text.split()]
                    english_detected = any(word in english_words for word in words_in_text if word)
                    
                    if english_detected:
                        detected_words = [word for word in words_in_text if word in english_words]
                        logger.debug(f"Scripture lookup skipped: English words detected: {detected_words} in text: '{processed_text}'")
                    else:
                        # Proceed with scripture lookup
                        scripture_match = None
                        if self.external_services:
                            scripture_match = self.external_services.api_lookup_scripture(processed_text)
                        elif self.external_clients and self.external_clients.api_client:
                            scripture_match = self.external_clients.api_client.lookup_scripture(processed_text)
                        
                        if scripture_match:
                            # Enhanced validation for scripture responses
                            confidence = getattr(scripture_match, 'confidence', 0.0)
                            transliteration = getattr(scripture_match, 'transliteration', '')
                            verse_ref = getattr(scripture_match, 'verse_reference', 'unknown')
                            
                            # Validation checks
                            if confidence < 0.9:
                                logger.debug(f"Scripture lookup rejected: Low confidence ({confidence:.2f} < 0.9) for text: '{processed_text}'")
                            elif not transliteration:
                                logger.debug(f"Scripture lookup rejected: Empty transliteration for text: '{processed_text}'")
                            elif abs(len(transliteration) - len(processed_text)) > 10:
                                logger.debug(f"Scripture lookup rejected: Length mismatch (input: {len(processed_text)}, output: {len(transliteration)}) for text: '{processed_text}'")
                            elif len(transliteration.split('\n')) > 1:
                                logger.debug(f"Scripture lookup rejected: Multi-line response (verse injection) for text: '{processed_text}'")
                            elif any(pattern in transliteration.lower() for pattern in ['verse', 'chapter', 'bhagavad gītā 1.', 'bhagavad gītā 2.']):
                                # Detect if response contains verse references or typical verse patterns
                                # Note: Removed generic 'gītā' pattern as it blocks legitimate Sanskrit term enhancements
                                logger.debug(f"Scripture lookup rejected: Contains verse patterns in response for text: '{processed_text}'")
                            elif transliteration.count('.') > 2:
                                # Detect if response looks like full verses (multiple sentences)
                                logger.debug(f"Scripture lookup rejected: Response appears to be full verse content for text: '{processed_text}'")
                            else:
                                # Additional semantic validation - check if key terms are preserved
                                original_key_terms = [word for word in processed_text.split() if len(word) > 2]
                                response_text = transliteration.lower()
                                
                                # Check if at least 50% of original key terms are preserved in some form
                                preserved_terms = sum(1 for term in original_key_terms if term.lower() in response_text)
                                preservation_ratio = preserved_terms / len(original_key_terms) if original_key_terms else 0
                                
                                if preservation_ratio < 0.5:
                                    logger.debug(f"Scripture lookup rejected: Poor term preservation ({preservation_ratio:.2f} < 0.5) for text: '{processed_text}'")
                                else:
                                    # All validations passed - apply enhancement
                                    processed_text = transliteration
                                    total_corrections += 1
                                    logger.info(f"Applied scripture enhancement: '{text}' → '{transliteration}' (confidence: {confidence:.2f}, ref: {verse_ref})")
                        else:
                            logger.debug(f"Scripture lookup returned no match for text: '{processed_text}'")
                
            except Exception as e:
                logger.error(f"Scripture lookup failed: {e}")
        
        return processed_text, total_corrections
    
    def process_srt_file(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Enhanced SRT processing with batch optimizations."""
        import time
        start_time = time.time()
        
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