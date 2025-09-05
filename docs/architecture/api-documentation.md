# API Documentation: Sanskrit Processor Lean Architecture

**Version**: Post-Emergency Rescue (2,164 lines)  
**Last Updated**: September 2024

## Overview

This document provides comprehensive API documentation for the Sanskrit Processor lean architecture, covering CLI interfaces, core processing APIs, and service integration points. The system provides both simple (lexicon-only) and enhanced (external service integration) processing capabilities.

## Command Line Interface

### Unified CLI (`cli.py`)

The system provides a single, unified command-line interface that supports both simple and enhanced processing modes.

#### Basic Usage

```bash
# Simple processing (lexicon-only)
python3 cli.py input.srt output.srt --simple --verbose

# Enhanced processing (with external services)  
python3 cli.py input.srt output.srt --config config.yaml --verbose

# Batch processing
python3 cli.py batch input_dir/ output_dir/ --pattern "*.srt"
```

#### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `command` | str | None | Optional: `batch` for batch processing mode |
| `input` | Path | Required | Input SRT file or directory (for batch) |
| `output` | Path | Required* | Output SRT file or directory (for batch) |
| `--config` | Path | `config.yaml` | Configuration file path |
| `--lexicons` | Path | `lexicons` | Directory containing lexicon YAML files |
| `--verbose, -v` | flag | False | Enable verbose logging and detailed metrics |
| `--status-only` | flag | False | Show service status and exit (enhanced mode only) |
| `--metrics` | flag | False | Collect detailed processing metrics |
| `--export-metrics` | Path | None | Export metrics to JSON file |
| `--pattern` | str | `*.srt` | File pattern for batch processing |
| `--simple` | flag | False | Use simple processor (lexicons only) |

*Required except for `--status-only` mode

#### Return Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error (file not found, processing failed) |
| 2 | Configuration error (invalid config.yaml) |
| 3 | Service unavailable (enhanced mode only) |

#### Examples

**1. Basic File Processing**
```bash
python3 cli.py lecture.srt corrected_lecture.srt --simple --verbose
```

**2. Enhanced Processing with Custom Configuration**
```bash
python3 cli.py lecture.srt enhanced_lecture.srt --config prod_config.yaml --metrics --export-metrics metrics.json
```

**3. Batch Processing Directory**
```bash
python3 cli.py batch ./input_lectures/ ./output_lectures/ --pattern "*.srt" --verbose
```

**4. Service Status Check**
```bash
python3 cli.py dummy.srt dummy_out.srt --status-only
```

**5. Simple Mode Processing (No External Services)**
```bash
python3 cli.py input.srt output.srt --simple --lexicons custom_lexicons/
```

## Core Processing API

### SanskritProcessor Class

**Location**: `sanskrit_processor_v2.py`  
**Purpose**: Core text processing engine with lexicon-based corrections

#### Constructor

```python
def __init__(self, lexicon_dir: Path, collect_metrics: bool = False)
```

**Parameters**:
- `lexicon_dir` (Path): Directory containing lexicon YAML files
- `collect_metrics` (bool): Enable detailed metrics collection

**Example**:
```python
from sanskrit_processor_v2 import SanskritProcessor

processor = SanskritProcessor(
    lexicon_dir=Path("lexicons"),
    collect_metrics=True
)
```

#### Core Methods

##### `process_text(text: str) -> str`

Process a single text segment with lexicon corrections.

**Parameters**:
- `text` (str): Input text to process

**Returns**:
- `str`: Processed text with corrections applied

**Example**:
```python
original = "gita and yoga sashtra"
corrected = processor.process_text(original)
# Result: "Gītā and Yoga Śāstra"
```

##### `process_srt_file(input_path: Path, output_path: Path) -> ProcessingResult`

Process an entire SRT file with comprehensive metrics.

**Parameters**:
- `input_path` (Path): Path to input SRT file
- `output_path` (Path): Path for output SRT file

**Returns**:
- `ProcessingResult`: Processing result with metrics and status

**Example**:
```python
result = processor.process_srt_file(
    input_path=Path("input.srt"),
    output_path=Path("output.srt")
)

print(f"Segments processed: {result.total_segments}")
print(f"Corrections applied: {result.corrections_applied}")
print(f"Processing time: {result.processing_time_ms}ms")
```

#### Configuration

The processor supports YAML-based configuration for customizing behavior:

```yaml
processing:
  enable_fuzzy_matching: true
  fuzzy_threshold: 0.8
  enable_punctuation_enhancement: true
  batch_size: 100

corrections:
  case_sensitive: false
  preserve_original_case: false
  apply_diacritics: true

metrics:
  detailed_reporting: true
  include_timing: true
```

### Data Structures

#### `SRTSegment`

Immutable data structure representing a single SRT segment.

```python
@dataclass(frozen=True)
class SRTSegment:
    index: int
    start_time: str
    end_time: str  
    text: str
    
    def to_srt_format(self) -> str:
        """Convert to SRT format string."""
        pass
```

#### `ProcessingResult`

Container for processing results and metrics.

```python
@dataclass
class ProcessingResult:
    segments: List[SRTSegment]
    total_segments: int
    corrections_applied: int
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None
    detailed_metrics: Optional[Dict] = None
```

#### `CorrectionDetail`

Details about specific corrections applied.

```python
@dataclass
class CorrectionDetail:
    original: str
    corrected: str
    correction_type: str  # 'lexicon', 'capitalization', 'punctuation'
    confidence: float
    position: int
```

## Enhanced Processing API

### EnhancedSanskritProcessor Class

**Location**: `enhanced_processor.py`  
**Purpose**: External service integration with graceful degradation

#### Constructor

```python
def __init__(self, lexicon_dir: Path, config_path: Path)
```

**Parameters**:
- `lexicon_dir` (Path): Directory containing lexicon YAML files  
- `config_path` (Path): Path to configuration YAML file

**Example**:
```python
from enhanced_processor import EnhancedSanskritProcessor

processor = EnhancedSanskritProcessor(
    lexicon_dir=Path("lexicons"),
    config_path=Path("config.yaml")
)
```

#### Enhanced Methods

##### `process_text(text: str) -> str`

Process text with both lexicon corrections and external service enhancement.

**Processing Flow**:
1. Apply core lexicon corrections
2. Attempt external service enhancement (MCP/API)
3. Graceful fallback to lexicon-only if services unavailable

**Example**:
```python
enhanced_text = processor.process_text("gita shastra discussion")
# May include additional semantic enhancements from external services
```

##### `extract_entities(text: str) -> List[Dict]`

Extract named entities using NER services.

**Returns**:
- `List[Dict]`: List of entity dictionaries with type, text, and confidence

**Example**:
```python
entities = processor.extract_entities("Bhagavad Gītā teaches yoga philosophy")
# [
#   {"text": "Bhagavad Gītā", "type": "SCRIPTURE", "confidence": 0.95},
#   {"text": "yoga", "type": "CONCEPT", "confidence": 0.85}
# ]
```

##### `get_service_status() -> Dict[str, Dict]`

Get status of all external services.

**Returns**:
- `Dict[str, Dict]`: Service status information

**Example**:
```python
status = processor.get_service_status()
# {
#   "mcp": {
#     "available": True,
#     "endpoint": "ws://localhost:8080",
#     "last_check": "2024-09-05T10:30:00Z"
#   },
#   "api": {
#     "available": False, 
#     "endpoint": "https://api.sanskrit.com",
#     "error": "Connection timeout"
#   }
# }
```

##### `close()`

Properly close all external service connections.

**Example**:
```python
try:
    result = processor.process_srt_file(input_path, output_path)
finally:
    processor.close()  # Ensure proper cleanup
```

## Service Integration APIs

### External Service Coordinator

**Location**: `services/external.py`  
**Purpose**: Unified interface for external service capabilities

```python
from services.external import ExternalServiceCoordinator

# Initialize with configuration
coordinator = ExternalServiceCoordinator(config)

# Enhance text segments
enhanced_segments = coordinator.enhance_segments(segments)

# Check service availability
if coordinator.is_service_available('mcp'):
    result = coordinator.call_mcp_service(text)
```

### MCP Client API

**Location**: `services/mcp_client.py`  
**Purpose**: Model Context Protocol integration

#### Key Methods

```python
from services.mcp_client import MCPClient

# Initialize client
client = MCPClient(endpoint="ws://localhost:8080")

# Establish connection
await client.connect()

# Analyze text semantically
result = await client.analyze_text(
    text="Sanskrit philosophical text",
    context="spiritual-lecture"
)

# Batch processing
results = await client.batch_analyze(text_segments)

# Close connection
await client.close()
```

#### MCP Message Format

**Request**:
```json
{
  "id": "req-123",
  "method": "analyze_text",
  "params": {
    "text": "bhagavad gita teachings",
    "context": "spiritual-lecture",
    "enhance_proper_nouns": true
  }
}
```

**Response**:
```json
{
  "id": "req-123", 
  "result": {
    "enhanced_text": "Bhagavad Gītā teachings",
    "confidence": 0.92,
    "entities": [
      {
        "text": "Bhagavad Gītā",
        "type": "SCRIPTURE",
        "start": 0,
        "end": 13
      }
    ],
    "corrections": [
      {
        "original": "gita",
        "corrected": "Gītā", 
        "type": "proper_noun_diacritics"
      }
    ]
  }
}
```

### API Client Integration

**Location**: `services/api_client.py`  
**Purpose**: REST API integration for scripture lookup

#### Key Methods

```python
from services.api_client import APIClient

# Initialize client
client = APIClient(
    base_url="https://api.sanskrit.example.com",
    api_key="your-api-key"
)

# Scripture lookup
result = client.lookup_scripture(
    text="gita",
    context="bhagavad"
)

# IAST validation
validation = client.validate_iast(
    text="yogaśāstra",
    format="iast"
)

# Batch lookup
results = client.batch_lookup(terms)
```

#### REST API Endpoints

**Scripture Lookup**:
```http
GET /api/v1/lookup?text=gita&context=bhagavad
Authorization: Bearer {api_key}

Response:
{
  "canonical": "Bhagavad Gītā",
  "variations": ["gita", "geeta", "gīta"],
  "confidence": 0.95,
  "source": "Mahabharata",
  "chapter_info": {
    "chapters": 18,
    "verses": 700
  }
}
```

**IAST Validation**:
```http
POST /api/v1/validate
Content-Type: application/json
Authorization: Bearer {api_key}

Body:
{
  "text": "yogaśāstra",
  "format": "iast",
  "target_script": "devanagari"
}

Response:
{
  "valid": true,
  "devanagari": "योगशास्त्र",
  "romanized": "yogaśāstra",
  "suggestions": []
}
```

## Configuration API

### Configuration Schema

The system uses YAML-based configuration with the following structure:

```yaml
# Core processing settings
processing:
  batch_size: 100
  timeout_seconds: 30
  enable_punctuation_fixes: true
  enable_fuzzy_matching: true
  fuzzy_threshold: 0.8

# External service configuration
services:
  mcp:
    enabled: true
    endpoint: "ws://localhost:8080"
    timeout: 10
    retry_attempts: 3
    circuit_breaker:
      failure_threshold: 5
      reset_timeout: 60
    
  api:
    enabled: true
    base_url: "https://api.sanskrit.example.com"
    api_key: "${SANSKRIT_API_KEY}"  # Environment variable
    timeout: 15
    retry_attempts: 2
    circuit_breaker:
      failure_threshold: 3
      reset_timeout: 30

# Lexicon configuration
lexicons:
  corrections: "lexicons/corrections.yaml"
  proper_nouns: "lexicons/proper_nouns.yaml"
  custom_entities: "lexicons/entities.yaml"

# Output configuration
output:
  preserve_timestamps: true
  include_metrics: true
  format: "srt"  # Future: support for other formats

# Logging configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  include_performance_metrics: true
```

### Configuration Loading

```python
from enhanced_processor import ConfigurationManager

# Load configuration with hierarchy
config = ConfigurationManager.load_config(
    config_path=Path("config.yaml"),
    cli_overrides=cli_args,
    environment_overrides=True
)

# Access configuration values
batch_size = config['processing']['batch_size']
mcp_enabled = config['services']['mcp']['enabled']
```

## Error Handling and Status Codes

### Processing Errors

| Error Type | Status Code | Description | Recovery |
|------------|-------------|-------------|----------|
| `FileNotFoundError` | 1 | Input file not found | Check file path |
| `InvalidConfigError` | 2 | Configuration file invalid | Validate YAML syntax |
| `LexiconLoadError` | 2 | Lexicon files corrupt/missing | Check lexicon directory |
| `ServiceUnavailableError` | 3 | External services down | Use simple mode or retry |
| `ProcessingTimeoutError` | 1 | Processing exceeded timeout | Increase timeout or use smaller batches |
| `InsufficientMemoryError` | 1 | Out of memory during processing | Reduce batch size |

### Service Status Codes

| Status | Description | Action |
|--------|-------------|--------|
| `available` | Service responding normally | Continue normal operation |
| `degraded` | Service slow but functional | Monitor and consider timeout adjustments |
| `unavailable` | Service not responding | Use circuit breaker, fall back to local processing |
| `error` | Service returning errors | Check configuration and service logs |

## Performance Considerations

### Processing Performance

| Metric | Simple Mode | Enhanced Mode | Notes |
|--------|-------------|---------------|-------|
| **Throughput** | 2,600+ segments/sec | 1,800+ segments/sec | Depends on service latency |
| **Memory Usage** | <50MB | <75MB | Additional overhead for service clients |
| **Startup Time** | <2 seconds | <5 seconds | Service connection establishment |
| **File Size Limit** | 500MB+ | 300MB+ | Limited by service timeouts |

### Optimization Guidelines

**1. Batch Processing**:
```python
# Process large files in batches
processor.config['processing']['batch_size'] = 50  # Reduce for better memory usage
```

**2. Service Timeouts**:
```yaml
services:
  mcp:
    timeout: 5  # Reduce for faster fallback
  api:
    timeout: 10
```

**3. Circuit Breaker Tuning**:
```yaml
services:
  mcp:
    circuit_breaker:
      failure_threshold: 3  # Fail fast
      reset_timeout: 30     # Quick recovery
```

## Testing APIs

### Unit Testing Utilities

```python
from sanskrit_processor_v2 import SanskritProcessor
import tempfile
import pytest

def test_basic_processing():
    """Test basic text processing functionality."""
    processor = SanskritProcessor(lexicon_dir=Path("test_lexicons"))
    
    test_text = "gita teaches yoga philosophy"
    result = processor.process_text(test_text)
    
    assert "Gītā" in result
    assert "Yoga" in result

def test_srt_file_processing():
    """Test SRT file processing end-to-end."""
    processor = SanskritProcessor(lexicon_dir=Path("test_lexicons"))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt') as input_file:
        input_file.write(sample_srt_content)
        input_file.flush()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt') as output_file:
            result = processor.process_srt_file(
                Path(input_file.name),
                Path(output_file.name)
            )
            
            assert result.success
            assert result.total_segments > 0
```

### Mock Service Testing

```python
from unittest.mock import Mock, patch
from enhanced_processor import EnhancedSanskritProcessor

def test_service_fallback():
    """Test graceful degradation when services fail."""
    with patch('services.external.ExternalServiceCoordinator') as mock_coordinator:
        # Mock service failure
        mock_coordinator.return_value.enhance_segments.return_value = None
        
        processor = EnhancedSanskritProcessor(
            lexicon_dir=Path("test_lexicons"),
            config_path=Path("test_config.yaml")
        )
        
        result = processor.process_text("test text")
        
        # Should still get lexicon-based processing
        assert result is not None
```

## Future API Enhancements

### Planned Extensions

**1. Streaming API**:
```python
# Future streaming interface
async def process_stream(input_stream, output_stream):
    async for segment in input_stream:
        enhanced_segment = await processor.process_segment_async(segment)
        await output_stream.send(enhanced_segment)
```

**2. REST API Server**:
```python
# Future HTTP API
@app.route('/api/v1/process', methods=['POST'])
def process_text():
    data = request.json
    result = processor.process_text(data['text'])
    return jsonify({'result': result})
```

**3. Plugin System**:
```python
# Future plugin architecture
processor.register_plugin('custom_enhancer', CustomEnhancerPlugin())
```

This API documentation provides comprehensive coverage of the current Sanskrit Processor lean architecture interfaces, enabling developers to integrate, extend, and maintain the system effectively.