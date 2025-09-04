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
from services.mcp_client import create_mcp_client, MCPClient
from services.api_client import create_api_client, ExternalAPIClient

logger = logging.getLogger(__name__)

class EnhancedSanskritProcessor(SanskritProcessor):
    """Enhanced processor with MCP and external API integration."""
    
    def __init__(self, lexicon_dir: Path = None, config_path: Path = None):
        """Initialize with enhanced services."""
        # Initialize base processor
        super().__init__(lexicon_dir)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize external services
        self.mcp_client: Optional[MCPClient] = None
        self.api_client: Optional[ExternalAPIClient] = None
        
        if self.config.get('mcp', {}).get('enabled', False):
            try:
                self.mcp_client = create_mcp_client(config_path)
                logger.info("MCP client initialized")
            except Exception as e:
                logger.warning(f"MCP client initialization failed: {e}")
        
        if self.config.get('external_apis', {}).get('enabled', False):
            try:
                self.api_client = create_api_client(config_path)
                logger.info("External API client initialized")
            except Exception as e:
                logger.warning(f"API client initialization failed: {e}")
        
        logger.info("Enhanced Sanskrit processor initialized")
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not config_path or not config_path.exists():
            logger.info("Using default configuration")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def process_text(self, text: str, context: Dict = None) -> tuple[str, int]:
        """Enhanced text processing with external services."""
        # Start with base processing
        processed_text, base_corrections = super().process_text(text)
        total_corrections = base_corrections
        
        # Apply MCP enhancements if available
        if self.mcp_client and self.config.get('processing', {}).get('enable_semantic_analysis', True):
            try:
                enhanced_text = self.mcp_client.context_correct(processed_text, 
                                                              context.get('previous_text') if context else None)
                if enhanced_text != processed_text:
                    processed_text = enhanced_text
                    total_corrections += 1
                    logger.debug("Applied MCP context correction")
            except Exception as e:
                logger.debug(f"MCP enhancement skipped: {e}")
        
        # Apply scripture lookup if available
        if self.api_client and self.config.get('processing', {}).get('enable_scripture_lookup', True):
            try:
                scripture_match = self.api_client.lookup_scripture(processed_text)
                if scripture_match and scripture_match.confidence > 0.8:
                    # For high-confidence matches, could enhance with citation
                    logger.debug(f"Scripture match found: {scripture_match.verse_reference}")
                    # Note: In a full implementation, might add footnote or enhance text
            except Exception as e:
                logger.debug(f"Scripture lookup skipped: {e}")
        
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
        status = {
            "base_processor": "active",
            "lexicons_loaded": {
                "corrections": len(self.lexicons.corrections),
                "proper_nouns": len(self.lexicons.proper_nouns)
            }
        }
        
        if self.mcp_client:
            status["mcp_client"] = {
                "enabled": self.mcp_client.config.enabled,
                "connected": self.mcp_client.connected
            }
        else:
            status["mcp_client"] = "disabled"
        
        if self.api_client:
            status["external_apis"] = self.api_client.get_service_status()
        else:
            status["external_apis"] = "disabled"
        
        return status
    
    def close(self):
        """Clean up external connections."""
        if self.mcp_client:
            self.mcp_client.close()
        
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