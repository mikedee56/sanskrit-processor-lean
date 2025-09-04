#!/usr/bin/env python3
"""
Enhanced CLI for Sanskrit SRT Processor with MCP and API Integration
Usage: python enhanced_cli.py input.srt output.srt
"""

import sys
import argparse
from pathlib import Path
import logging
import json

from enhanced_processor import EnhancedSanskritProcessor

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def main():
    """Enhanced CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced Sanskrit SRT processor with MCP and external API integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_cli.py input.srt output.srt
  python enhanced_cli.py input.srt output.srt --config custom_config.yaml --verbose
  python enhanced_cli.py input.srt output.srt --status-only
        """
    )
    
    parser.add_argument('input', type=Path, nargs='?', help='Input SRT file')
    parser.add_argument('output', type=Path, nargs='?', help='Output SRT file')
    parser.add_argument('--config', type=Path, default=Path('config.yaml'),
                        help='Configuration file (default: config.yaml)')
    parser.add_argument('--lexicons', type=Path, default=Path('lexicons'),
                        help='Directory containing lexicon YAML files (default: lexicons)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--status-only', action='store_true',
                        help='Show service status and exit')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize processor
        logger.info("Initializing Enhanced Sanskrit processor...")
        processor = EnhancedSanskritProcessor(
            lexicon_dir=args.lexicons,
            config_path=args.config
        )
        
        # Show status if requested
        if args.status_only:
            status = processor.get_service_status()
            print("\n=== SERVICE STATUS ===")
            print(json.dumps(status, indent=2))
            processor.close()
            return
        
        # Validate arguments for processing
        if not args.input or not args.output:
            parser.error("Input and output files are required for processing")
        
        if not args.input.exists():
            logger.error(f"Input file does not exist: {args.input}")
            sys.exit(1)
        
        if not args.lexicons.exists():
            logger.error(f"Lexicons directory does not exist: {args.lexicons}")
            sys.exit(1)
        
        if args.input == args.output:
            logger.error("Input and output files cannot be the same")
            sys.exit(1)
        
        # Show service status
        status = processor.get_service_status()
        logger.info("=== SERVICE STATUS ===")
        logger.info(f"Base processor: {status['base_processor']}")
        logger.info(f"Lexicons loaded: {status['lexicons_loaded']}")
        
        if isinstance(status.get('mcp_client'), dict):
            mcp_status = status['mcp_client']
            logger.info(f"MCP client: enabled={mcp_status['enabled']}, connected={mcp_status['connected']}")
        else:
            logger.info(f"MCP client: {status.get('mcp_client', 'unknown')}")
        
        if isinstance(status.get('external_apis'), dict):
            api_status = status['external_apis']
            active_apis = sum(1 for svc in api_status.values() if svc['can_call'])
            logger.info(f"External APIs: {active_apis}/{len(api_status)} services available")
        else:
            logger.info(f"External APIs: {status.get('external_apis', 'unknown')}")
        
        # Process file
        logger.info(f"Processing: {args.input} -> {args.output}")
        result = processor.process_srt_file(args.input, args.output)
        
        # Report results
        if result.errors:
            logger.error("Processing completed with errors:")
            for error in result.errors:
                logger.error(f"  - {error}")
            processor.close()
            sys.exit(1)
        else:
            logger.info("✓ Enhanced processing completed successfully")
            logger.info(f"  Segments processed: {result.segments_processed}")
            logger.info(f"  Corrections made: {result.corrections_made}")
            logger.info(f"  Processing time: {result.processing_time:.2f} seconds")
            
            if result.segments_processed > 0:
                rate = result.segments_processed / result.processing_time if result.processing_time > 0 else 0
                logger.info(f"  Processing rate: {rate:.1f} segments/second")
            
            if result.corrections_made > 0:
                avg_corrections = result.corrections_made / result.segments_processed
                logger.info(f"  Average corrections per segment: {avg_corrections:.2f}")
        
        # Clean up
        processor.close()
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()