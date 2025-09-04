#!/usr/bin/env python3
"""
Simple CLI for Sanskrit SRT Processor
Usage: python simple_cli.py input.srt output.srt
"""

import sys
import argparse
from pathlib import Path
import logging

from sanskrit_processor_v2 import SanskritProcessor

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Process SRT files with Sanskrit/Hindi corrections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_cli.py input.srt output.srt
  python simple_cli.py input.srt output.srt --lexicons ./custom_lexicons --verbose
        """
    )
    
    parser.add_argument('input', type=Path, help='Input SRT file')
    parser.add_argument('output', type=Path, help='Output SRT file')
    parser.add_argument('--lexicons', type=Path, default=Path('data/lexicons'),
                        help='Directory containing lexicon YAML files (default: data/lexicons)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate inputs
    if not args.input.exists():
        logger.error(f"Input file does not exist: {args.input}")
        sys.exit(1)
    
    if not args.lexicons.exists():
        logger.error(f"Lexicons directory does not exist: {args.lexicons}")
        sys.exit(1)
    
    if args.input == args.output:
        logger.error("Input and output files cannot be the same")
        sys.exit(1)
    
    try:
        # Initialize processor
        logger.info(f"Initializing Sanskrit processor with lexicons from {args.lexicons}")
        processor = SanskritProcessor(lexicon_dir=args.lexicons)
        
        # Process file
        logger.info(f"Processing: {args.input} -> {args.output}")
        result = processor.process_srt_file(args.input, args.output)
        
        # Report results
        if result.errors:
            logger.error("Processing completed with errors:")
            for error in result.errors:
                logger.error(f"  - {error}")
            sys.exit(1)
        else:
            logger.info("✓ Processing completed successfully")
            logger.info(f"  Segments processed: {result.segments_processed}")
            logger.info(f"  Corrections made: {result.corrections_made}")
            logger.info(f"  Processing time: {result.processing_time:.2f} seconds")
            
            if result.corrections_made > 0:
                logger.info(f"  Average corrections per segment: {result.corrections_made / result.segments_processed:.2f}")
            
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