# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Sanskrit SRT Processor** with lean architecture - a focused, maintainable implementation for processing Yoga Vedanta lecture SRT files with Sanskrit/Hindi corrections, proper noun capitalization, and external service integration. It's a complete redesign from a complex 10,000+ line system into ~500 lines while maintaining full functionality.

**Architecture Philosophy**: Lean core (200 lines) + smart externals (MCP/APIs) + fail-fast errors + gradual enhancement.

## Common Commands

### Basic Processing (Core Functionality)
```bash
# Process SRT with lexicon corrections only
python3 simple_cli.py input.srt output.srt --lexicons lexicons --verbose

# Test with sample file
python3 simple_cli.py sample_test.srt test_output.srt --lexicons lexicons --verbose
```

### Enhanced Processing (With External Services)
```bash
# Full processing with MCP/API integration
python3 enhanced_cli.py input.srt output.srt --config config.yaml --verbose

# Check external service status
python3 enhanced_cli.py --status-only
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Windows testing
test_windows.bat  # or test_windows.ps1
```

### Testing & Validation
```bash
# Basic validation test
python3 simple_cli.py sample_test.srt test_output.srt --lexicons lexicons --verbose

# Syntax check
python3 -m py_compile sanskrit_processor_v2.py

# Run pytest if tests exist
pytest --cov
```

## High-Level Architecture

### Core Components
- **`sanskrit_processor_v2.py`** - Main processor (200 lines): SRTSegment, ProcessingResult, LexiconLoader, SRTParser, SanskritProcessor
- **`simple_cli.py`** - Basic CLI for lexicon-only processing
- **`enhanced_cli.py`** - Full CLI with MCP/API integration
- **`enhanced_processor.py`** - External service integration layer

### Service Layer
- **`services/mcp_client.py`** - MCP integration with circuit breaker protection
- **`services/api_client.py`** - External API client for scripture lookup

### Configuration & Data
- **`config.yaml`** - Central configuration (MCP, APIs, processing settings)
- **`lexicons/corrections.yaml`** - Sanskrit/Hindi term corrections with variations
- **`lexicons/proper_nouns.yaml`** - Proper noun capitalization rules

### Processing Flow
1. **SRT Parsing** - Extract timestamps and text segments
2. **Lexicon Matching** - Apply corrections and proper noun capitalization  
3. **External Enhancement** (optional) - MCP semantic analysis, API scripture lookup
4. **SRT Generation** - Output with preserved timestamps

### Key Design Patterns
- **Circuit Breaker**: External services fail gracefully to local processing
- **Fail-Fast**: Clear errors instead of silent failures
- **Configuration-Driven**: All behavior controlled via YAML
- **Gradual Enhancement**: Core works standalone, services add intelligence

## Development Guidelines

### Code Style
- Standard Python conventions: PascalCase classes, snake_case functions
- Structured logging with clear error messages
- Minimal dependencies (PyYAML, requests core; websocket-client, pytest optional)
- ~200 lines per core file - keep it focused and maintainable

### Cross-Platform Support
- Supports Windows 11 (cmd/PowerShell), WSL2 Ubuntu, Linux
- Use both `python` and `python3` commands in examples
- Test files: `test_windows.bat` and `test_windows.ps1`

### Task Completion Requirements
- Test basic functionality: `python3 simple_cli.py sample_test.srt test_output.srt --lexicons lexicons --verbose`
- Test enhanced features: `python3 enhanced_cli.py --status-only`
- Verify cross-platform compatibility
- Validate YAML configuration files
- Performance: maintain 2,600+ segments/second, <50MB memory

### External Service Integration
- MCP services provide semantic analysis and batch processing
- External APIs handle scripture lookup and IAST validation
- All external services include circuit breaker protection
- System degrades gracefully when services unavailable