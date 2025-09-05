# Code Style and Conventions

## Python Style
- **Standard**: Follows standard Python conventions
- **Imports**: Standard library first, then third-party, then local imports
- **Classes**: PascalCase (SRTSegment, ProcessingResult, LexiconLoader, SRTParser, SanskritProcessor)
- **Functions**: snake_case (setup_logging, create_mcp_client)
- **Constants**: UPPER_CASE (MCP_AVAILABLE)
- **Logging**: Uses Python logging module with structured logging

## Architecture Patterns
- **Separation of Concerns**: Core processor separate from CLI and external services
- **Circuit Breaker Pattern**: Used for external service integration
- **Fail-Fast**: Clear error messages instead of silent failures
- **Configuration-Driven**: YAML configuration for all settings
- **Gradual Enhancement**: Core works standalone, services add intelligence

## File Organization
- Core functionality in single focused files (~200 lines each)
- Services in separate `services/` directory
- Configuration data in `lexicons/` directory
- CLI interfaces as thin wrappers around core functionality

## Error Handling
- No silent failures - all errors should be explicit
- Circuit breaker protection for external services
- Graceful degradation when services unavailable
- Clear error messages for troubleshooting

## Data Formats
- **YAML**: Used for configuration and lexicon data
- **SRT**: Standard SubRip subtitle format
- **Structured Data**: Uses dataclasses for type safety (SRTSegment, ProcessingResult, etc.)

## Dependencies
- Minimal core dependencies (PyYAML, requests)
- Optional dependencies for enhanced features
- No complex dependency trees - keep it lean