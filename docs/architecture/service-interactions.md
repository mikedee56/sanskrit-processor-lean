# Service Interactions and Flow Documentation

**Architecture**: Sanskrit Processor Lean Implementation  
**Version**: Post-Emergency Rescue (2,164 lines)  
**Last Updated**: September 2024

## Overview

This document details the service interaction patterns and data flow within the Sanskrit Processor lean architecture. The system follows a **configuration-driven service-oriented** approach with **circuit breaker protection** for external integrations.

## High-Level Architecture Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │────│  Core Processor  │────│ Enhanced Layer  │
│   (cli.py)      │    │ (sanskrit_...)   │    │ (enhanced_...)  │
│   251 lines     │    │ 752 lines        │    │ 238 lines       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                    ┌───────────▼────────────┐          │
                    │  Configuration Layer   │          │
                    │    (config.yaml)       │          │
                    │  + Lexicon System      │          │
                    └────────────────────────┘          │
                                                        │
                    ┌───────────────────────────────────▼┐
                    │         Service Layer              │
                    │  ┌─────────┬──────────┬──────────┐ │
                    │  │External │API Client│MCP Client│ │
                    │  │Coord.   │327 lines │254 lines │ │
                    │  │117 lines│          │          │ │
                    │  └─────────┴──────────┴──────────┘ │
                    └────────────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │        External Services            │
                    │  ┌──────────────┬──────────────────┐│
                    │  │ MCP Services │  REST APIs       ││
                    │  │ (WebSocket)  │  (HTTP)          ││
                    │  └──────────────┴──────────────────┘│
                    └────────────────────────────────────┘
```

## Processing Flow Details

### 1. CLI Entry Point (`cli.py`)

**Purpose**: Unified command-line interface and orchestration

**Flow**:
```
User Command → Argument Parsing → Configuration Loading → Processor Selection → Result Output
```

**Key Interactions**:
- **Configuration System**: Loads and validates `config.yaml`
- **Core Processor**: Instantiates and calls `SanskritProcessor`
- **Enhanced Processor**: Conditionally integrates for advanced features
- **File System**: Input/output SRT file handling

**Processing Modes**:
```python
# Basic mode (lexicon-only)
python3 cli.py input.srt output.srt --lexicons lexicons --verbose

# Enhanced mode (with external services)  
python3 cli.py input.srt output.srt --config config.yaml --enhanced --verbose

# Status check mode
python3 cli.py --status-only
```

### 2. Core Processing Pipeline (`sanskrit_processor_v2.py`)

**Purpose**: Main text processing engine with lexicon-based corrections

**Processing Steps**:
```
SRT Input → Parse Segments → Apply Lexicons → Format Text → Generate SRT Output
```

**Data Flow**:
1. **Input Processing**:
   ```python
   SRTParser.parse(srt_content) → List[SRTSegment]
   ```

2. **Lexicon Application**:
   ```python
   LexiconLoader.load_corrections() → Dict[str, Correction]
   SanskritProcessor.apply_corrections(segments, lexicons) → List[SRTSegment]
   ```

3. **Result Generation**:
   ```python
   SRTParser.generate(segments) → str
   ProcessingResult(segments, metrics, status) → Output
   ```

**Core Components**:
- **`SRTSegment`**: Immutable data structure for SRT entries
- **`ProcessingResult`**: Result container with processing metrics
- **`LexiconLoader`**: YAML lexicon file processor
- **`SRTParser`**: SRT format parser and generator
- **`SanskritProcessor`**: Main processing orchestrator

### 3. Enhanced Processing Layer (`enhanced_processor.py`)

**Purpose**: External service integration with graceful degradation

**Enhancement Flow**:
```
Core Result → Service Coordinator → External Analysis → Enhanced Result → Client
```

**Integration Pattern**:
```python
class EnhancedProcessor:
    def process(self, segments):
        # Get core processing result first
        core_result = self.core_processor.process(segments)
        
        # Attempt external enhancement
        if self.external_services.available():
            enhanced_segments = self.external_services.enhance(core_result.segments)
            return ProcessingResult(enhanced_segments, enhanced_metrics)
        
        # Graceful fallback to core result
        return core_result
```

## Service Layer Architecture

### Service Coordinator (`services/external.py`)

**Purpose**: Unified interface for all external service capabilities

**Coordination Pattern**:
```python
class ExternalServiceCoordinator:
    def enhance_segments(self, segments):
        results = []
        for segment in segments:
            # Try MCP analysis first
            enhanced = self.mcp_service.analyze(segment) if self.mcp_enabled else None
            
            # Fall back to API service
            if not enhanced and self.api_enabled:
                enhanced = self.api_service.lookup(segment)
            
            # Use original if no enhancement available
            results.append(enhanced or segment)
        return results
```

**Circuit Breaker Implementation**:
```python
class CircuitBreaker:
    def call_with_protection(self, service_func, *args):
        if self.is_open():
            return None  # Fail fast
        
        try:
            result = service_func(*args)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            return None  # Graceful degradation
```

### MCP Service Integration (`services/mcp_client.py`)

**Purpose**: Model Context Protocol integration for semantic analysis

**Communication Pattern**:
```
WebSocket Connection → MCP Protocol Messages → Semantic Analysis → Results
```

**MCP Message Flow**:
```json
// Request
{
  "id": "req-123",
  "method": "analyze_text",
  "params": {
    "text": "Sanskrit text segment",
    "context": "spiritual-lecture"
  }
}

// Response  
{
  "id": "req-123",
  "result": {
    "enhanced_text": "Enhanced Sanskrit text",
    "confidence": 0.95,
    "annotations": ["proper-noun", "technical-term"]
  }
}
```

**Connection Management**:
```python
class MCPClient:
    async def connect(self):
        self.websocket = await websockets.connect(self.endpoint)
        self.connected = True
        
    async def send_request(self, method, params):
        if not self.connected:
            await self.connect()
        
        request = {"id": self.next_id(), "method": method, "params": params}
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)
```

### API Service Integration (`services/api_client.py`)

**Purpose**: REST API integration for scripture lookup and validation

**HTTP Communication Pattern**:
```
HTTP Request → API Endpoint → Scripture Database → Response → Text Enhancement
```

**API Interaction Examples**:
```python
# Scripture lookup
GET /api/v1/lookup?text=गीता&context=bhagavad
Response: {
  "canonical": "भगवद्गीता", 
  "variations": ["गीता", "गीता शास्त्र"],
  "confidence": 0.9
}

# IAST validation
POST /api/v1/validate
Body: {"text": "yogaśāstra", "format": "iast"}
Response: {
  "valid": true,
  "devanagari": "योगशास्त्र",
  "suggestions": []
}
```

**Client Implementation**:
```python
class APIClient:
    def lookup_scripture(self, text, context=None):
        params = {"text": text}
        if context:
            params["context"] = context
            
        response = self.session.get(f"{self.base_url}/lookup", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            self.circuit_breaker.record_failure()
            return None
```

## Configuration-Driven Architecture

### Configuration Loading Flow

```
CLI Args → config.yaml → Environment Variables → Default Values → Final Configuration
```

**Configuration Hierarchy**:
1. **CLI Arguments** (highest priority)
2. **config.yaml** file settings
3. **Environment variables** (future enhancement)
4. **Code defaults** (fallback)

**Configuration Structure** (`config.yaml`):
```yaml
processing:
  batch_size: 100
  timeout_seconds: 30
  enable_punctuation_fixes: true

services:
  mcp:
    enabled: true
    endpoint: "ws://localhost:8080"
    timeout: 10
    retry_attempts: 3
    
  api:
    enabled: true
    base_url: "https://api.sanskrit.example.com"
    api_key: "${SANSKRIT_API_KEY}"
    timeout: 15

lexicons:
  corrections: "lexicons/corrections.yaml"
  proper_nouns: "lexicons/proper_nouns.yaml"
  
output:
  preserve_timestamps: true
  include_metrics: true
```

### Configuration Loading Implementation

```python
class ConfigurationManager:
    def load_config(self, config_path, cli_args):
        # Start with defaults
        config = self.get_defaults()
        
        # Override with YAML file
        if os.path.exists(config_path):
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)
                config = self.merge_configs(config, yaml_config)
        
        # Override with CLI arguments  
        config = self.apply_cli_overrides(config, cli_args)
        
        # Validate configuration
        self.validate_config(config)
        
        return config
```

## Data Flow Patterns

### Basic Processing Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ SRT File    │────│ SRT Parser   │────│ Segments    │
│ (Input)     │    │              │    │ List        │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                   ┌──────────────┐          │
                   │ Lexicon      │◄─────────┘
                   │ Corrections  │
                   └──────────────┘
                            │
                   ┌────────▼─────┐    ┌─────────────┐
                   │ Enhanced     │────│ SRT File    │
                   │ Segments     │    │ (Output)    │
                   └──────────────┘    └─────────────┘
```

### Enhanced Processing Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Basic       │────│ Service      │────│ Enhanced    │
│ Processing  │    │ Coordinator  │    │ Result      │
└─────────────┘    └──────────────┘    └─────────────┘
                            │
                   ┌────────▼─────────┐
                   │ External Services│
                   │ ┌──────┬───────┐ │
                   │ │ MCP  │ API   │ │
                   │ │      │ REST  │ │
                   │ └──────┴───────┘ │
                   └──────────────────┘
```

### Error Handling Flow

```
Service Call → Circuit Breaker Check → [OPEN] → Return Null (Fail Fast)
                     │
                 [CLOSED]
                     │
             ┌───────▼────────┐
             │ Execute Service│
             │ Call           │
             └───────┬────────┘
                     │
    ┌────────────────▼─────────────────┐
    │              Result              │
    │  ┌─────────┐        ┌─────────┐  │
    │  │ Success │        │ Failure │  │
    │  │         │        │         │  │
    │  │ Reset   │        │ Record  │  │
    │  │ Circuit │        │ Failure │  │
    │  │ Breaker │        │         │  │
    │  └─────────┘        └─────────┘  │
    └──────────────────────────────────┘
```

## Performance and Scalability Patterns

### Batch Processing Pattern

```python
class BatchProcessor:
    def process_large_file(self, segments, batch_size=100):
        results = []
        for batch_start in range(0, len(segments), batch_size):
            batch_end = min(batch_start + batch_size, len(segments))
            batch = segments[batch_start:batch_end]
            
            batch_result = self.process_batch(batch)
            results.extend(batch_result)
            
        return results
```

### Concurrent Service Calls (Future Enhancement)

```python
import asyncio

async def process_with_concurrent_services(segments):
    tasks = []
    for segment in segments:
        # Create concurrent tasks for different services
        mcp_task = asyncio.create_task(mcp_client.analyze(segment))
        api_task = asyncio.create_task(api_client.lookup(segment))
        tasks.extend([mcp_task, api_task])
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return merge_results(results)
```

## Testing and Validation Patterns

### Service Integration Testing

```python
class TestServiceIntegration:
    def test_with_mock_services(self):
        # Mock external services
        mock_mcp = Mock()
        mock_api = Mock()
        
        coordinator = ExternalServiceCoordinator(
            mcp_client=mock_mcp,
            api_client=mock_api
        )
        
        # Test service coordination
        result = coordinator.enhance_segments(test_segments)
        
        # Verify service calls
        mock_mcp.analyze.assert_called_once()
        mock_api.lookup.assert_called()
```

### Circuit Breaker Testing

```python
def test_circuit_breaker_behavior():
    # Simulate service failures
    for _ in range(5):  # Trigger circuit breaker threshold
        service.call_failing_service()
    
    # Verify circuit is open
    assert service.circuit_breaker.is_open()
    
    # Verify fail-fast behavior
    result = service.call_with_protection(mock_service_call)
    assert result is None
```

## Extension Points

### Adding New Service Integrations

1. **Create Service Client** (following existing patterns):
   ```python
   class NewServiceClient:
       def __init__(self, config):
           self.endpoint = config['endpoint']
           self.circuit_breaker = CircuitBreaker()
       
       def process_text(self, text):
           # Implementation following circuit breaker pattern
           pass
   ```

2. **Register with Service Coordinator**:
   ```python
   class ExternalServiceCoordinator:
       def __init__(self, config):
           # ... existing services ...
           if config['new_service']['enabled']:
               self.new_service = NewServiceClient(config['new_service'])
   ```

3. **Add Configuration Schema**:
   ```yaml
   services:
     new_service:
       enabled: true
       endpoint: "https://api.newservice.com"
       timeout: 10
   ```

### Adding New Processing Stages

```python
class ProcessingPipeline:
    def __init__(self):
        self.stages = [
            LexiconCorrectionStage(),
            ProperNounCapitalizationStage(),
            PunctuationFixStage(),
            # Add new stages here
            NewProcessingStage()
        ]
    
    def process(self, segments):
        for stage in self.stages:
            segments = stage.process(segments)
        return segments
```

## Troubleshooting Guide

### Service Connection Issues

**Problem**: External services not responding
```bash
# Check service status
python3 cli.py --status-only

# Test with services disabled
python3 cli.py input.srt output.srt --no-external-services
```

**Diagnosis**:
- Check network connectivity to service endpoints
- Verify configuration file service URLs
- Check service authentication credentials

### Circuit Breaker Activation

**Problem**: Circuit breaker preventing service calls
```python
# Check circuit breaker status
coordinator = ExternalServiceCoordinator(config)
print(f"MCP Circuit Open: {coordinator.mcp_client.circuit_breaker.is_open()}")
print(f"API Circuit Open: {coordinator.api_client.circuit_breaker.is_open()}")
```

**Recovery**:
- Wait for circuit breaker timeout period
- Verify external services are operational
- Restart processing to reset circuit breaker state

### Performance Issues

**Problem**: Slow processing with external services
- **Monitor service response times**: Enable verbose logging
- **Adjust timeouts**: Reduce timeout values in config.yaml
- **Disable slow services**: Temporarily disable problematic services
- **Use batch processing**: Process files in smaller batches

## Future Architectural Enhancements

### Planned Service Improvements

1. **Service Discovery**: Automatic detection of available services
2. **Load Balancing**: Distribution of requests across multiple service instances
3. **Advanced Circuit Breaker**: Exponential backoff and partial failure handling
4. **Service Health Monitoring**: Continuous health checks and metrics collection

### Scalability Enhancements

1. **Parallel Processing**: Concurrent processing of segments
2. **Distributed Processing**: Multi-node processing capability
3. **Streaming Interface**: Real-time processing API
4. **Caching Layer**: Service response caching for performance

This service interaction documentation provides the foundation for understanding and extending the current lean architecture while maintaining its core principles of simplicity, reliability, and maintainability.