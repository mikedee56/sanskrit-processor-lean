# Brownfield Architecture: Sanskrit Processor Lean Implementation

**Current State**: Post-Emergency Lean Architecture Rescue  
**Total Lines**: 2,164 (reduced from 10,000+)  
**Architecture Status**: Stable Production System  
**Last Updated**: September 2024

## Executive Summary

This document captures the **current state** of the Sanskrit Processor after the emergency lean architecture rescue transformation. The system successfully processes Sanskrit/Hindi SRT files with a dramatically simplified 9-file architecture while maintaining full functionality.

### Key Metrics
- **Core Files**: 9 Python files (2,164 total lines)
- **Processing Speed**: 2,600+ segments/second
- **Memory Usage**: <50MB typical
- **Dependencies**: 5 core packages (lean by design)
- **Architecture Pattern**: Configuration-driven service-oriented

## System Architecture Overview

### Core Architecture Patterns

**1. Lean Core + Smart Externals**
- Minimal core processing logic (752 lines in `sanskrit_processor_v2.py`)
- External services provide intelligence via MCP/API integration
- Core remains functional without external dependencies

**2. Configuration-Driven Design**
- All behavior controlled via `config.yaml`
- Feature flags enable/disable services
- Environment-specific configurations supported

**3. Circuit Breaker Protection**
- External services fail gracefully to local processing
- No silent failures - clear error reporting
- System remains operational when services unavailable

## File Structure Analysis

### Core Processing Files (1,241 lines)
```
cli.py                     251 lines  - Unified CLI interface
sanskrit_processor_v2.py   752 lines  - Core processing engine  
enhanced_processor.py      238 lines  - External service integration
```

### Service Layer (698 lines)
```
services/external.py       117 lines  - Consolidated service coordinator
services/api_client.py     327 lines  - External API integration
services/mcp_client.py     254 lines  - MCP protocol client
services/__init__.py         0 lines  - Package marker
```

### Testing (225 lines)
```
tests/test_core_functionality.py  142 lines  - Core processor tests
tests/test_batch_processing.py     83 lines  - Batch processing tests
```

## Component Responsibilities

### 1. CLI Interface (`cli.py` - 251 lines)

**Purpose**: Unified command-line interface for all processing modes

**Key Features**:
- Single entry point for basic and enhanced processing
- Configuration file validation and loading
- Verbose output and error handling
- Cross-platform compatibility (Windows/Linux)

**Architecture Pattern**: Command pattern with service injection

```python
# Primary classes
class CLIConfig         # Configuration management
class ProcessingOrchestrator  # Workflow coordination
```

### 2. Core Processor (`sanskrit_processor_v2.py` - 752 lines)

**Purpose**: Main processing engine for Sanskrit/Hindi text processing

**Key Components**:
- `SRTSegment`: Immutable data structure for SRT entries
- `ProcessingResult`: Result container with metrics
- `LexiconLoader`: YAML lexicon file processor
- `SRTParser`: SRT format parser/generator
- `SanskritProcessor`: Main processing orchestrator

**Processing Pipeline**:
1. SRT parsing and segment extraction
2. Lexicon-based corrections (Sanskrit/Hindi terms)
3. Proper noun capitalization
4. Punctuation and formatting fixes
5. SRT reconstruction with preserved timestamps

### 3. Enhanced Processor (`enhanced_processor.py` - 238 lines)

**Purpose**: External service integration layer

**Key Features**:
- MCP semantic analysis integration
- External API scripture lookup
- Service health monitoring
- Graceful degradation patterns

**Architecture Pattern**: Adapter pattern for service integration

### 4. Service Layer (`services/` - 698 lines)

#### External Service Coordinator (`services/external.py` - 117 lines)
- Consolidates all external service interactions
- Implements circuit breaker patterns
- Provides unified interface for external capabilities

#### API Client (`services/api_client.py` - 327 lines)
- REST API integration for scripture lookup
- IAST validation services
- Retry logic and error handling

#### MCP Client (`services/mcp_client.py` - 254 lines)
- Model Context Protocol integration
- WebSocket-based communication
- Semantic analysis and batch processing

## Configuration Architecture

### Central Configuration (`config.yaml`)

**Structure**:
```yaml
processing:           # Core processing settings
  batch_size: 100
  timeout: 30

services:            # External service configuration
  mcp:
    enabled: true
    endpoint: "ws://localhost:8080"
  api:
    enabled: true
    base_url: "https://api.example.com"

lexicons:           # Lexicon file paths
  corrections: "lexicons/corrections.yaml"
  proper_nouns: "lexicons/proper_nouns.yaml"
```

**Configuration Loading Hierarchy**:
1. Default values in code
2. `config.yaml` overrides
3. Environment variables (future enhancement)
4. CLI arguments (highest priority)

## Data Architecture

### Lexicon System
```
lexicons/corrections.yaml     # Sanskrit/Hindi term corrections
lexicons/proper_nouns.yaml    # Proper noun capitalization
lexicons/test_*.yaml         # Performance test datasets
```

**Lexicon Format**:
```yaml
corrections:
  "incorrect_term":
    canonical: "correct_term"
    variations: ["alt1", "alt2"]
    context: "spiritual"
```

### Processing Data Flow

**Input**: SRT file with timestamps and text segments
**Processing**: 
1. Parse SRT → `SRTSegment` objects
2. Apply lexicon corrections
3. Enhance via external services (optional)
4. Apply formatting rules
**Output**: Corrected SRT file with preserved timestamps

## External Service Integration

### MCP (Model Context Protocol) Services
- **Purpose**: Semantic analysis and intelligent corrections
- **Communication**: WebSocket-based protocol
- **Fallback**: System continues with lexicon-only processing

### External API Services
- **Purpose**: Scripture lookup and IAST validation
- **Communication**: HTTP REST APIs
- **Fallback**: Local processing continues without external validation

### Circuit Breaker Implementation
```python
# Simplified circuit breaker logic
if service_available():
    result = external_service.process(text)
else:
    result = local_processor.process(text)  # Graceful fallback
```

## Dependencies and Tech Stack

### Core Dependencies (`requirements.txt`)
```
pyyaml>=6.0          # Configuration and lexicon files
requests>=2.28.0     # HTTP API client
pytest>=7.0.0        # Testing framework
pytest-cov>=4.0.0    # Coverage reporting
psutil>=5.9.0        # Performance monitoring
```

### Optional Dependencies
```
websocket-client>=1.4.0  # MCP protocol (commented out - install as needed)
```

**Dependency Philosophy**: 
- Minimal core dependencies
- Optional dependencies for enhanced features
- No framework dependencies (Flask, Django, etc.)

## Performance Characteristics

### Processing Performance
- **Throughput**: 2,600+ segments/second (measured)
- **Memory Usage**: <50MB typical operation
- **Startup Time**: <2 seconds cold start
- **File Size**: Handles multi-hour lecture files efficiently

### Scalability Patterns
- Batch processing for large files
- Streaming processing for memory efficiency
- Parallel processing for multi-file operations (future enhancement)

## Architectural Constraints and Limitations

### Current Constraints
1. **Single-threaded processing**: No parallel processing yet
2. **File-based input/output**: No streaming API interface
3. **YAML-based configuration**: No runtime configuration changes
4. **Local lexicon storage**: No distributed lexicon management

### Design Limitations
1. **Service discovery**: Hard-coded service endpoints
2. **Error recovery**: Limited retry strategies
3. **Monitoring**: Basic logging only
4. **Scalability**: Designed for single-user operation

## Extension Points for Future Development

### 1. Service Architecture Extensions
- **Plugin System**: Dynamic service registration
- **Service Discovery**: Automatic service endpoint detection
- **Load Balancing**: Multiple service instance support

### 2. Processing Pipeline Extensions
- **Custom Processors**: Plugin-based processing stages
- **Batch Processing**: Enhanced batch job management
- **Real-time Processing**: Streaming input/output support

### 3. Configuration Extensions
- **Dynamic Configuration**: Runtime configuration updates
- **Environment Profiles**: Development/staging/production configs
- **Feature Flags**: Granular feature toggling

### 4. API Extensions
- **REST API**: HTTP-based processing interface
- **WebSocket API**: Real-time processing updates
- **Batch API**: Asynchronous job processing

## Quality Attributes

### Maintainability ✅
- **Small Files**: Largest file is 752 lines
- **Clear Separation**: Each file has single responsibility
- **Minimal Dependencies**: Easy to understand and modify

### Reliability ✅
- **Circuit Breaker**: External service failures handled gracefully
- **Error Handling**: Clear error messages and recovery paths
- **Testing**: Core functionality covered by automated tests

### Performance ✅
- **Fast Processing**: 2,600+ segments/second throughput
- **Low Memory**: <50MB typical usage
- **Quick Startup**: <2 second cold start

### Scalability 🟡
- **Current State**: Designed for single-user operation
- **Future Ready**: Architecture supports scaling enhancements
- **Extension Points**: Clear paths for distributed processing

## Troubleshooting Guide

### Common Issues

**1. Configuration File Not Found**
```bash
# Verify config.yaml exists in project root
ls config.yaml
# Check configuration syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**2. External Service Unavailable**
```bash
# Check service status
python3 enhanced_processor.py --status-only
# Test with local processing only
python3 cli.py input.srt output.srt --lexicons-only
```

**3. Lexicon Files Missing**
```bash
# Verify lexicon files
ls lexicons/corrections.yaml lexicons/proper_nouns.yaml
# Test lexicon syntax
python3 -c "from sanskrit_processor_v2 import LexiconLoader; LexiconLoader('lexicons')"
```

### Performance Issues

**1. Slow Processing**
- Check available memory: `free -h`
- Monitor CPU usage: `top -p $(pgrep -f python3)`
- Reduce batch size in config.yaml

**2. High Memory Usage**
- Process files in smaller batches
- Check for large lexicon files
- Monitor with: `python3 -m psutil`

## Conclusion

The Sanskrit Processor lean architecture represents a successful transformation from a complex 10,000+ line system to a focused, maintainable 2,164-line implementation. The system maintains full functionality while dramatically improving maintainability, performance, and extensibility.

**Key Success Factors**:
1. **Lean Core**: Essential functionality in minimal code
2. **Smart Externals**: Intelligence via external services
3. **Graceful Degradation**: System works without external dependencies
4. **Clear Separation**: Each component has single responsibility
5. **Extension Ready**: Architecture supports future enhancements

**Next Steps**: This architecture provides a solid foundation for the planned enhancements in Epic 5 (Architecture Excellence) and future development cycles.