#!/usr/bin/env python3
"""
Unified CLI for Sanskrit SRT Processor - Lean Architecture
Usage: python cli.py input.srt output.srt [--simple] [batch input_dir output_dir]
"""

import sys
import os
import argparse
from pathlib import Path
import logging
import json

from enhanced_processor import EnhancedSanskritProcessor
from sanskrit_processor_v2 import SanskritProcessor
from services.config_validator import ConfigValidator
from exceptions import SanskritProcessorError, FileError, ConfigurationError, ProcessingError, get_exit_code
from utils.performance_profiler import PerformanceProfiler

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def validate_configuration(config_path: Path):
    """Validate configuration file using advanced ConfigManager."""
    print(f"🔍 Validating configuration with advanced config management")
    
    try:
        # Use advanced ConfigManager for validation
        from utils.config_manager import ConfigManager
        
        # Initialize ConfigManager
        config_manager = ConfigManager()
        
        # Get validation report
        validation_report = config_manager.validate_config()
        
        # Report environment information
        print(f"🌍 Environment: {validation_report['environment']}")
        
        if validation_report['valid']:
            print("✅ Configuration is valid!")
            
            # Show configuration files used
            print(f"\n📋 Configuration Sources:")
            for config_file in validation_report['config_files_used']:
                print(f"   • {config_file}")
            
            # Show environment variables used
            if validation_report['env_vars_substituted']:
                print(f"\n🔧 Environment Variables:")
                for env_var in validation_report['env_vars_substituted']:
                    value = "***" if 'KEY' in env_var or 'PASS' in env_var else os.environ.get(env_var, 'NOT_SET')
                    print(f"   • {env_var} = {value}")
            else:
                print(f"\n🔧 No environment variables used in configuration")
            
            # Load and display effective configuration summary
            try:
                effective_config = config_manager.load_config()
                print(f"\n📊 Configuration Summary:")
                
                # Processing settings
                if 'processing' in effective_config:
                    proc_config = effective_config['processing']
                    print(f"   • IAST Diacritics: {'✅' if proc_config.get('use_iast_diacritics') else '❌'}")
                    if 'fuzzy_matching' in proc_config:
                        fuzzy = proc_config['fuzzy_matching']
                        print(f"   • Fuzzy Matching: {'✅' if fuzzy.get('enabled') else '❌'} (threshold: {fuzzy.get('threshold', 'N/A')})")
                
                # Services
                if 'services' in effective_config:
                    services = effective_config['services']
                    for service_type, service_config in services.items():
                        if isinstance(service_config, dict):
                            for service_name, config in service_config.items():
                                if isinstance(config, dict):
                                    enabled = config.get('enabled', False)
                                    print(f"   • {service_type.title()}/{service_name.upper()}: {'✅' if enabled else '❌'}")
                
                # Plugins
                if 'plugins' in effective_config:
                    plugins = effective_config['plugins']
                    enabled = plugins.get('enabled', False)
                    plugin_list = plugins.get('enabled_plugins', [])
                    print(f"   • Plugins: {'✅' if enabled else '❌'} ({len(plugin_list)} enabled)")
                    
            except Exception as e:
                print(f"   ⚠️  Could not load effective configuration: {e}")
                
            return 0
            
        else:
            print("❌ Configuration validation failed!")
            print(f"   Error: {validation_report['error']}")
            print(f"\n💡 Try:")
            print(f"   • Check that base configuration exists in config/")
            print(f"   • Set required environment variables")
            print(f"   • Use migration tool: python3 tools/migrate_config.py config.yaml config/")
            return 1
            
    except ImportError:
        # Fallback to legacy validation if ConfigManager not available
        print("⚠️  Advanced config manager not available, using legacy validation")
        return validate_configuration_legacy(config_path)
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return 1


def validate_configuration_legacy(config_path: Path):
    """Legacy configuration validation fallback."""
    print(f"🔍 Legacy validation for: {config_path}")
    
    # Check if config file exists
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        print(f"💡 Create a config.yaml file or specify --config path/to/config.yaml")
        return 1
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("✅ Configuration file loads successfully!")
        print(f"📋 Configuration keys: {list(config.keys()) if config else 'Empty'}")
        
        return 0
        
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1

def main():
    """Enhanced CLI entry point with batch processing."""
    parser = argparse.ArgumentParser(
        description="Enhanced Sanskrit SRT processor with MCP and external API integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py input.srt output.srt
  python cli.py input.srt output.srt --config custom_config.yaml --verbose
  python cli.py input.srt output.srt --export-formats srt vtt json xml
  python cli.py input.srt output.srt --export-formats vtt --verbose
  python cli.py input.srt output.srt --status-only
  python cli.py input.srt output.srt --metrics --export-metrics metrics.json
  python cli.py input.srt output.srt --profile --profile-detail detailed
  python cli.py input.srt output.srt --cache-stats
  python cli.py input.srt output.srt --qa-report quality_report.json
  python cli.py batch input_dir/ output_dir/ --pattern "*.srt"
        """
    )
    
    parser.add_argument('command', nargs='?', default=None, help='Command: batch or single file processing')
    parser.add_argument('input', type=Path, nargs='?', help='Input SRT file or directory (for batch)')
    parser.add_argument('output', type=Path, nargs='?', help='Output SRT file or directory (for batch)')
    parser.add_argument('--config', type=Path, default=Path('config.yaml'),
                        help='Configuration file (default: config.yaml)')
    parser.add_argument('--lexicons', type=Path, default=Path('lexicons'),
                        help='Directory containing lexicon YAML files (default: lexicons)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging and detailed metrics')
    parser.add_argument('--status-only', action='store_true',
                        help='Show service status and exit')
    parser.add_argument('--metrics', action='store_true',
                        help='Collect detailed processing metrics')
    parser.add_argument('--export-metrics', type=Path,
                        help='Export metrics to JSON file')
    parser.add_argument('--qa-report', type=Path,
                        help='Generate quality assurance report in JSON format')
    parser.add_argument('--pattern', default='*.srt', 
                        help='File pattern for batch processing (default: *.srt)')
    parser.add_argument('--simple', action='store_true',
                        help='Use simple processor (lexicons only, no external services)')
    parser.add_argument('--validate-config', action='store_true',
                        help='Validate configuration file and exit')
    parser.add_argument('--profile', action='store_true',
                        help='Enable performance profiling')
    parser.add_argument('--profile-detail', choices=['basic', 'detailed', 'full'],
                        default='basic', help='Profiling detail level')
    parser.add_argument('--cache-stats', action='store_true',
                        help='Report cache statistics after processing')
    parser.add_argument('--export-formats', 
                       nargs='+', 
                       default=['srt'],
                       choices=['srt', 'vtt', 'json', 'xml'],
                       help='Output formats to generate (default: srt)')
    
    args = parser.parse_args()
    
    # Handle config validation if requested
    if args.validate_config:
        return validate_configuration(args.config)
    
    # Handle command parsing - if first arg looks like 'batch', it's batch mode
    if args.command == 'batch':
        if not args.output:
            print("❌ Error: Output directory required for batch processing")
            print("💡 Usage: python cli.py batch input_dir/ output_dir/")
            return 1
        return process_batch(args)
    else:
        # Single file mode - adjust args
        if args.command:
            # Shift args: command becomes input, input becomes output
            args.output = args.input
            args.input = Path(args.command)
        return process_single(args)

def process_single(args):
    """Process single file with enhanced error handling."""
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Initialize profiler
    profiler = PerformanceProfiler(
        enabled=args.profile,
        detail_level=args.profile_detail
    )
    
    try:
        with profiler.profile_stage("initialization"):
            # Initialize processor based on mode
            if args.simple:
                logger.info("Initializing Simple Sanskrit processor...")
                processor = SanskritProcessor(args.lexicons)
            else:
                logger.info("Initializing Enhanced Sanskrit processor...")
                processor = EnhancedSanskritProcessor(
                    lexicon_dir=args.lexicons,
                    config_path=args.config
                )
        
        # Show status if requested (enhanced mode only)
        if args.status_only:
            if args.simple:
                print("\n=== SIMPLE MODE STATUS ===")
                print("Simple processor - no external services")
                return 0
            else:
                status = processor.get_service_status()
                print("\n=== SERVICE STATUS ===")
                print(json.dumps(status, indent=2))
                processor.close()
                return 0
        
        # Validate arguments for processing
        if not args.input or not args.output:
            print("❌ Error: Input and output files are required for processing")
            print("💡 Usage: python cli.py input.srt output.srt")
            return 1
        
        with profiler.profile_stage("validation"):
            if not args.input.exists():
                from exceptions import FileError, get_exit_code
                error = FileError(
                    f"Input file not found: {args.input}",
                    file_path=str(args.input),
                    file_operation="read"
                )
                print(f"❌ {error.get_formatted_message()}")
                return get_exit_code(error)
            
            if not args.lexicons.exists():
                from exceptions import FileError, get_exit_code
                error = FileError(
                    f"Lexicons directory not found: {args.lexicons}",
                    file_path=str(args.lexicons),
                    file_operation="read",
                    suggestions=[
                        "Ensure lexicons directory exists in project root",
                        "Use --lexicons flag to specify different path"
                    ]
                )
                print(f"❌ {error.get_formatted_message()}")
                return get_exit_code(error)
            
            if args.input.resolve() == args.output.resolve():
                from exceptions import FileError, get_exit_code
                error = FileError(
                    "Input and output files cannot be the same",
                    file_path=str(args.input),
                    suggestions=["Use different output filename or path"]
                )
                print(f"❌ {error.get_formatted_message()}")
                return get_exit_code(error)
        
        with profiler.profile_stage("status_check"):
            # Show service status
            if hasattr(processor, 'get_service_status'):
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
            else:
                logger.info("=== SERVICE STATUS ===")
                logger.info("Simple processor mode - no external services")
        
        # Process file
        logger.info(f"Processing: {args.input} -> {args.output}")
        with profiler.profile_stage("processing"):
            # Handle QA report generation if requested
            if args.qa_report:
                logger.info("Quality assurance report requested")
                # Enable QA in processor if available
                if hasattr(processor, 'qa_enabled'):
                    original_qa_state = processor.qa_enabled
                    processor.qa_enabled = True
                
                # Read input file for QA processing
                with open(args.input, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                
                # Process with QA
                if hasattr(processor, 'process_srt_with_qa'):
                    processed_srt, qa_report = processor.process_srt_with_qa(
                        srt_content, args.input.name
                    )
                    
                    # Write processed SRT
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(processed_srt)
                    
                    # Write QA report
                    if qa_report:
                        import json
                        with open(args.qa_report, 'w', encoding='utf-8') as f:
                            json.dump(qa_report, f, indent=2)
                        logger.info(f"QA report written to: {args.qa_report}")
                        
                        # Display QA summary
                        summary = qa_report.get('quality_summary', {})
                        total = summary.get('high_confidence_segments', 0) + summary.get('medium_confidence_segments', 0) + summary.get('low_confidence_segments', 0)
                        review_needed = summary.get('review_recommended_segments', 0)
                        
                        print(f"\n🔍 Quality Assurance Summary:")
                        print(f"   Total segments: {total}")
                        print(f"   Review recommended: {review_needed}")
                        if total > 0:
                            print(f"   Review percentage: {(review_needed/total)*100:.1f}%")
                    
                    # Create a basic result object for compatibility
                    from utils.processing_reporter import ProcessingResult
                    result = ProcessingResult(
                        segments_processed=qa_report['metadata']['total_segments'] if qa_report else 0,
                        corrections_made=0,  # Not tracked in QA mode
                        processing_time=0.0,
                        errors=[]
                    )
                    
                    # Restore original QA state
                    if hasattr(processor, 'qa_enabled'):
                        processor.qa_enabled = original_qa_state
                else:
                    logger.warning("QA report requested but processor doesn't support process_srt_with_qa")
                    result = processor.process_srt_file(args.input, args.output)
            else:
                # Standard processing without QA report
                result = processor.process_srt_file(args.input, args.output)
        
        with profiler.profile_stage("reporting"):
            # Import reporter after processing
            from sanskrit_processor_v2 import ProcessingReporter
            
            # Report results
            if result.errors:
                print("⚠️  Processing completed with warnings:")
                for error in result.errors:
                    print(f"   • {error}")
                print("")  # Extra line for readability
                
                # Still show success report if segments were processed
                if result.segments_processed > 0:
                    report = ProcessingReporter.generate_summary(result, verbose=args.verbose)
                    print(report)
                    
                    # Display context-aware processing information if available
                    display_context_information(result)
                else:
                    print("❌ No segments were successfully processed")
                    return 3  # Processing error
            else:
                # Use the new reporter for enhanced output
                report = ProcessingReporter.generate_summary(result, verbose=args.verbose)
                print(report)
                
                # Display context-aware processing information if available
                display_context_information(result)
            
            # Report cache statistics if requested or enabled in config
            cache_enabled = getattr(args, 'cache_stats', False) or (
                hasattr(processor, 'config') and 
                processor.config.get('processing', {}).get('caching', {}).get('report_stats', False)
            )
            
            if cache_enabled and hasattr(processor, 'lexicon_cache'):
                cache_stats = processor.lexicon_cache.get_combined_stats()
                if cache_stats.get('caching') != 'disabled':
                    print("\n" + "="*40)
                    print("📊 CACHE STATISTICS")
                    print("="*40)
                    
                    corrections_stats = cache_stats.get('corrections_cache', {})
                    proper_nouns_stats = cache_stats.get('proper_nouns_cache', {})
                    
                    if corrections_stats:
                        print(f"\n🔧 Corrections Cache:")
                        print(f"   Entries: {corrections_stats.get('entries', 0)}")
                        print(f"   Hits: {corrections_stats.get('hits', 0)}")
                        print(f"   Misses: {corrections_stats.get('misses', 0)}")
                        print(f"   Hit Rate: {corrections_stats.get('hit_rate_percent', 0)}%")
                        print(f"   Memory: {corrections_stats.get('estimated_memory_mb', 0)} MB")
                    
                    if proper_nouns_stats:
                        print(f"\n🏛️  Proper Nouns Cache:")
                        print(f"   Entries: {proper_nouns_stats.get('entries', 0)}")
                        print(f"   Hits: {proper_nouns_stats.get('hits', 0)}")
                        print(f"   Misses: {proper_nouns_stats.get('misses', 0)}")
                        print(f"   Hit Rate: {proper_nouns_stats.get('hit_rate_percent', 0)}%")
                        print(f"   Memory: {proper_nouns_stats.get('estimated_memory_mb', 0)} MB")
                    
                    total_memory = cache_stats.get('total_memory_mb', 0)
                    print(f"\n💾 Total Cache Memory: {total_memory} MB")
                    
                    # Performance analysis
                    if corrections_stats.get('hits', 0) > 0 or proper_nouns_stats.get('hits', 0) > 0:
                        total_hits = corrections_stats.get('hits', 0) + proper_nouns_stats.get('hits', 0)
                        total_requests = (corrections_stats.get('hits', 0) + corrections_stats.get('misses', 0) + 
                                        proper_nouns_stats.get('hits', 0) + proper_nouns_stats.get('misses', 0))
                        
                        if total_requests > 0:
                            overall_hit_rate = (total_hits / total_requests) * 100
                            print(f"\n⚡ Overall Cache Performance:")
                            print(f"   Cache Hit Rate: {overall_hit_rate:.1f}%")
                            print(f"   Performance Boost: ~{(1 + overall_hit_rate/100):.1f}x faster lookups")
                
                
            # Multi-format export if requested
            if len(args.export_formats) > 1 or 'srt' not in args.export_formats:
                from exporters.format_manager import FormatManager, ExportRequest
                from utils.srt_parser import SRTParser
                
                # Read processed segments from output SRT file
                try:
                    with open(args.output, 'r', encoding='utf-8') as f:
                        processed_srt = f.read()
                    processed_segments = SRTParser.parse(processed_srt)
                    
                    format_manager = FormatManager()
                    export_request = ExportRequest(
                        source_filename=Path(args.input).stem,
                        segments=processed_segments,
                        qa_report=qa_report if 'qa_report' in locals() else {},
                        metadata=getattr(result, 'metadata', {}),
                        output_formats=args.export_formats,
                        output_directory=Path(args.output).parent
                    )
                    
                    export_results = format_manager.export_all_formats(export_request)
                    
                    print(f"\n📦 Export Results:")
                    for format_name, result_file in export_results.items():
                        if "Error:" in str(result_file):
                            print(f"   {format_name.upper()}: ❌ {result_file}")
                        else:
                            print(f"   {format_name.upper()}: ✅ {result_file}")
                            
                except Exception as e:
                    print(f"\n⚠️  Multi-format export failed: {e}")
                    if args.verbose:
                        import traceback
                        traceback.print_exc()
            
            # Export metrics if requested
            if args.export_metrics:
                import json
                metrics_data = ProcessingReporter.export_json(result)
                
                # Include cache statistics in exported metrics
                if hasattr(processor, 'lexicon_cache'):
                    cache_stats = processor.lexicon_cache.get_combined_stats()
                    if cache_stats.get('caching') != 'disabled':
                        metrics_data['cache_statistics'] = cache_stats
                
                # Include context-aware metrics if available
                if hasattr(result, 'quality_metrics') and result.quality_metrics:
                    metrics_data['context_aware_metrics'] = {
                        'content_type': getattr(result, 'content_type', 'unknown'),
                        'confidence': getattr(result, 'confidence', 0.0),
                        'quality_metrics': result.quality_metrics,
                        'specialized_processing': getattr(result, 'specialized_processing', {})
                    }
                
                with open(args.export_metrics, 'w') as f:
                    json.dump(metrics_data, f, indent=2)
                print(f"\n📊 Metrics exported to: {args.export_metrics}")
        
        # Generate and display performance report if profiling enabled
        if args.profile:
            perf_report = profiler.generate_report()
            print("\n" + "="*50)
            print("PERFORMANCE REPORT")
            print("="*50)
            print(f"Total Duration: {perf_report['total_duration']:.2f}s")
            print(f"Peak Memory: {perf_report['peak_memory_mb']:.1f}MB")
            
            if perf_report.get('stage_timings'):
                print("\nStage Breakdown:")
                for stage, timing in perf_report['stage_timings'].items():
                    percentage = (timing['duration'] / perf_report['total_duration']) * 100
                    print(f"  {stage}: {timing['duration']:.2f}s ({percentage:.1f}%)")
            
            if perf_report.get('recommendations'):
                print("\nOptimization Recommendations:")
                for rec in perf_report['recommendations']:
                    print(f"  • {rec}")
        
        # Clean up
        if hasattr(processor, 'close'):
            processor.close()
        
        return 0  # Success
            
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        return 1
    except Exception as e:
        from exceptions import get_exit_code, SanskritProcessorError
        
        # Handle our custom exceptions with formatted messages
        if isinstance(e, SanskritProcessorError):
            print(f"\n❌ {e.get_formatted_message()}")
            if args.verbose and hasattr(e, 'context') and e.context:
                print(f"\nContext: {e.context}")
            return get_exit_code(e)
        else:
            # Handle unexpected exceptions
            print(f"\n❌ Unexpected error: {e}")
            print("💡 Use --verbose flag for detailed error information")
            if args.verbose:
                import traceback
                print("\nDetailed error trace:")
                traceback.print_exc()
            return 1

def display_context_information(result):
    """Display context-aware processing information if available."""
    if not hasattr(result, 'content_type'):
        return  # Not a context-aware result
    
    print("\n" + "="*40)
    print("🧠 CONTEXT-AWARE PROCESSING")
    print("="*40)
    
    # Content classification
    print(f"\n📋 Content Classification:")
    print(f"   Type: {result.content_type}")
    print(f"   Confidence: {result.confidence:.1%}")
    
    if hasattr(result, 'metadata') and result.metadata:
        print(f"\n📊 Content Metadata:")
        for key, value in result.metadata.items():
            if isinstance(value, bool):
                print(f"   {key}: {'✓' if value else '✗'}")
            elif isinstance(value, list):
                print(f"   {key}: {len(value)} items")
            else:
                print(f"   {key}: {value}")
    
    # Specialized processing results
    if hasattr(result, 'specialized_processing') and result.specialized_processing:
        print(f"\n⚙️  Specialized Processing:")
        for processor, info in result.specialized_processing.items():
            if isinstance(info, dict):
                if 'corrections' in info:
                    print(f"   {processor.title()}: {info['corrections']} corrections in {info.get('time', 0):.3f}s")
                elif 'references' in info:
                    print(f"   {processor.title()}: {info['references']} references in {info.get('time', 0):.3f}s")
                elif 'protected' in info:
                    print(f"   {processor.title()}: {info['protected']} symbols protected in {info.get('time', 0):.3f}s")
                else:
                    print(f"   {processor.title()}: processed in {info.get('time', 0):.3f}s")
    
    # Quality metrics
    if hasattr(result, 'quality_metrics') and result.quality_metrics:
        print(f"\n📈 Quality Metrics:")
        for metric, value in result.quality_metrics.items():
            if 'similarity' in metric:
                print(f"   {metric.replace('_', ' ').title()}: {value:.1%}")
            elif 'speed' in metric:
                print(f"   {metric.replace('_', ' ').title()}: {value:.0f} chars/sec")
            elif 'confidence' in metric:
                print(f"   {metric.replace('_', ' ').title()}: {value:.1%}")
            else:
                print(f"   {metric.replace('_', ' ').title()}: {value:.3f}")

def process_batch(args):
    """Ultra-lean batch processing implementation."""
    import glob
    import time
    from pathlib import Path
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Initialize profiler
    profiler = PerformanceProfiler(
        enabled=args.profile,
        detail_level=args.profile_detail
    )
    
    with profiler.profile_stage("batch_initialization"):
        # Discover files
        input_dir = args.input
        if not input_dir.is_dir():
            logger.error(f"Input must be directory for batch processing: {input_dir}")
            sys.exit(1)
            
        pattern = str(input_dir / args.pattern)
        files = [Path(f) for f in glob.glob(pattern)]
        if not files:
            logger.error(f"No files found matching: {pattern}")
            sys.exit(1)
        
        # Create output directory
        args.output.mkdir(parents=True, exist_ok=True)
        
        # Initialize processor once
        processor = EnhancedSanskritProcessor(args.lexicons, args.config)
    
    with profiler.profile_stage("batch_processing"):
        # Process files with simple progress
        results = []
        errors = []
        start_time = time.time()
        
        print(f"🔄 Processing {len(files)} files...")
        
        for i, file_path in enumerate(files, 1):
            try:
                output_path = args.output / file_path.name
                print(f"[{i}/{len(files)}] {file_path.name}", end=" ... ")
                
                result = processor.process_srt_file(file_path, output_path)
                if result.errors:
                    errors.extend(result.errors)
                    print("❌")
                else:
                    results.append(result)
                    print("✅")
                    
            except Exception as e:
                errors.append(f"{file_path.name}: {e}")
                print("❌")
    
    with profiler.profile_stage("batch_cleanup"):
        processor.close()
        
        # Simple summary report
        duration = time.time() - start_time
        total_corrections = sum(r.corrections_made for r in results)
        
        print(f"\n📊 Batch Complete:")
        print(f"   Files: {len(results)} success, {len(errors)} errors")
        print(f"   Time: {duration:.1f}s ({len(files)/duration:.1f} files/min)")
        print(f"   Total corrections: {total_corrections}")
        
        if errors:
            print(f"\n❌ Errors:")
            for error in errors[:5]:  # Limit error output
                print(f"   - {error}")
            if len(errors) > 5:
                print(f"   ... and {len(errors)-5} more")
    
    # Generate and display performance report if profiling enabled
    if args.profile:
        perf_report = profiler.generate_report()
        print("\n" + "="*50)
        print("BATCH PERFORMANCE REPORT")
        print("="*50)
        print(f"Total Duration: {perf_report['total_duration']:.2f}s")
        print(f"Peak Memory: {perf_report['peak_memory_mb']:.1f}MB")
        print(f"Processing Rate: {len(results)/perf_report['total_duration']:.1f} files/second")
        
        if perf_report.get('stage_timings'):
            print("\nStage Breakdown:")
            for stage, timing in perf_report['stage_timings'].items():
                percentage = (timing['duration'] / perf_report['total_duration']) * 100
                print(f"  {stage}: {timing['duration']:.2f}s ({percentage:.1f}%)")
        
        if perf_report.get('recommendations'):
            print("\nOptimization Recommendations:")
            for rec in perf_report['recommendations']:
                print(f"  • {rec}")

if __name__ == "__main__":
    sys.exit(main())