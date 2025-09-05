# ADR-002: Service Layer Consolidation Strategy

**Date**: 2024-09-04  
**Status**: Accepted  
**Deciders**: Development Team, Architecture Review  
**Tags**: service-architecture, external-integration, circuit-breaker, mcp-integration

## Context

Following the lean architecture rescue (ADR-001), the system needed a clean approach to external service integration. The legacy system had complex, tightly-coupled external service dependencies that were difficult to maintain and test.

- **Business Context**: External services provide advanced semantic analysis and scripture lookup capabilities
- **Technical Context**: Need to integrate MCP (Model Context Protocol) services and REST APIs reliably
- **Current State**: Post-rescue system with simplified core but no external service integration
- **Driving Forces**: 
  - Need for optional advanced processing capabilities
  - Requirement for system to work with or without external services
  - Desire to maintain lean architecture principles
  - Need for reliable, testable service integration

## Decision Drivers

- **Quality Attributes**: 
  - Reliability: System must work when services are unavailable
  - Maintainability: Service integration must be simple to understand and modify
  - Performance: Service calls should not significantly impact processing speed
  - Testability: Service integration must be easily mockable and testable
- **Constraints**: 
  - Must maintain lean architecture principles
  - Cannot add significant complexity to core processing
  - Must support both MCP and REST API integrations
- **Assumptions**: 
  - External services are unreliable and may be unavailable
  - Core processing must remain functional without external services
  - Different services have different integration patterns (WebSocket vs HTTP)
- **Requirements**: 
  - Circuit breaker pattern for service failures
  - Unified interface for external service capabilities
  - Configuration-driven service enablement

## Considered Options

### Option 1: Direct Service Integration
- **Description**: Core processor directly calls external services when needed
- **Pros**: 
  - Simple implementation
  - Direct control over service calls
  - Minimal abstraction overhead
- **Cons**: 
  - Tight coupling between core and services
  - Difficult to test core logic in isolation
  - Service failures could break core processing
  - Would violate lean architecture principles
- **Impact**: Simple but brittle, high maintenance burden

### Option 2: Heavy Service Framework
- **Description**: Implement comprehensive service registry, discovery, and orchestration
- **Pros**: 
  - Supports complex service topologies
  - Built-in monitoring and management
  - Enterprise-grade reliability patterns
- **Cons**: 
  - Massive complexity increase
  - Would violate lean architecture principles
  - Overkill for current needs
  - High learning curve and maintenance burden
- **Impact**: Robust but extremely complex, violates project philosophy

### Option 3: Consolidated Service Layer with Circuit Breaker
- **Description**: Create focused service layer with circuit breaker protection and graceful degradation
- **Pros**: 
  - Clean separation of concerns
  - Circuit breaker protects against service failures
  - Simple to understand and maintain
  - Supports both MCP and REST integration patterns
  - Aligns with lean architecture principles
- **Cons**: 
  - Requires careful design of service interfaces
  - May need future enhancement for complex service scenarios
- **Impact**: Balanced approach, good maintainability, aligned with project goals

## Decision Outcome

**Chosen option**: "Consolidated Service Layer with Circuit Breaker"

**Rationale**: 
The consolidated service layer approach provides the best balance of functionality, reliability, and maintainability while preserving the lean architecture principles established in ADR-001.

Key factors in this decision:
- Maintains clear separation between core processing and external services
- Circuit breaker pattern ensures system reliability
- Single service coordinator simplifies understanding and testing
- Supports both current integration needs (MCP, REST APIs)
- Aligns with configuration-driven architecture approach

### Implementation Plan
- [x] **Phase 1**: Create service layer structure (services/ directory)
- [x] **Phase 2**: Implement MCP client with WebSocket communication (254 lines)
- [x] **Phase 3**: Implement REST API client with HTTP communication (327 lines)  
- [x] **Phase 4**: Create consolidated service coordinator (117 lines)
- [x] **Phase 5**: Implement circuit breaker and graceful degradation
- [x] **Phase 6**: Integration with enhanced processor (238 lines)

### Success Metrics
- **Service Integration**: Both MCP and REST APIs successfully integrated ✅
- **Reliability**: System works correctly with services unavailable ✅
- **Code Size**: Service layer kept under 700 lines total ✅
- **Performance**: No significant impact on processing speed ✅

## Consequences

### Positive Consequences
- **Clean Architecture**: Clear separation between core and external services
- **Reliability**: System remains functional when services fail
- **Maintainability**: Service integration logic consolidated in focused modules
- **Testability**: Easy to mock and test service interactions
- **Configuration Flexibility**: Services can be enabled/disabled via configuration
- **Performance**: Circuit breaker prevents hanging on failed services

### Negative Consequences
- **Initial Complexity**: Service layer adds architectural complexity
- **Learning Curve**: Developers must understand circuit breaker patterns
- **Configuration Overhead**: More configuration options to manage

### Neutral Consequences
- **Service Architecture**: System now has service-oriented architecture characteristics
- **Dependency Management**: Additional dependencies for service protocols
- **Deployment Considerations**: External services must be available for full functionality

## Service Layer Architecture Details

### Core Components

**1. External Service Coordinator** (`services/external.py` - 117 lines)
- Unified interface for all external service capabilities
- Circuit breaker implementation
- Service health monitoring
- Configuration-driven service enablement

**2. MCP Client** (`services/mcp_client.py` - 254 lines)
- WebSocket-based MCP protocol implementation
- Semantic analysis and batch processing capabilities
- Connection management and error recovery

**3. API Client** (`services/api_client.py` - 327 lines)
- HTTP REST API integration
- Scripture lookup and IAST validation
- Retry logic and timeout handling

### Circuit Breaker Implementation

```python
# Simplified circuit breaker pattern
class ServiceCircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = None
        
    def call_service(self, service_func, *args, **kwargs):
        if self.is_circuit_open():
            return None  # Fail fast
        
        try:
            result = service_func(*args, **kwargs)
            self.reset_failures()
            return result
        except Exception:
            self.record_failure()
            return None  # Graceful degradation
```

### Service Interface Pattern

```python
# Unified service interface
class ExternalServiceCoordinator:
    def enhance_text(self, text, context=None):
        # Try MCP service first
        if self.mcp_enabled and self.mcp_client.is_available():
            result = self.mcp_client.analyze_text(text, context)
            if result:
                return result
        
        # Fall back to API service
        if self.api_enabled and self.api_client.is_available():
            result = self.api_client.lookup_text(text)
            if result:
                return result
        
        # Graceful degradation - return original text
        return text
```

## Compliance

- **Architecture Principles**: 
  - Separation of Concerns: Services separate from core processing
  - Single Responsibility: Each service client has focused purpose
  - Fail-Safe: Circuit breaker ensures graceful degradation
- **Standards**: 
  - MCP protocol compliance for semantic services
  - HTTP standards for REST API integration
  - Python async/await patterns for concurrent operations
- **Governance**: 
  - Service integration patterns documented
  - Circuit breaker thresholds configurable
  - Service health monitoring implemented

## Notes

### Key Design Patterns Used

1. **Circuit Breaker**: Prevents cascading failures from external services
2. **Adapter Pattern**: Unified interface for different service protocols
3. **Configuration Injection**: Services configured via YAML, not code
4. **Graceful Degradation**: System provides reduced functionality rather than failing

### Integration Points

- **Enhanced Processor**: Main integration point for service capabilities
- **Configuration System**: All service settings in config.yaml
- **Core Processor**: Receives enhanced results transparently
- **CLI Interface**: Service status and health checking capabilities

### Future Extensibility

The service layer architecture supports future enhancements:
- **Additional Protocols**: Easy to add new service integration patterns
- **Load Balancing**: Service coordinator can distribute requests
- **Service Discovery**: Framework for automatic service detection
- **Advanced Circuit Breaker**: More sophisticated failure detection and recovery

### References
- MCP Protocol Specification
- Circuit Breaker Pattern (Fowler)
- Service Integration Best Practices
- Configuration Management Patterns

### Related ADRs
- ADR-001: Emergency Lean Architecture Rescue (established lean principles)
- Future ADR-003: Configuration Management Strategy (when implemented)

### Review Date
**Next Review**: 2024-12-01 (3 months post-implementation)
- Evaluate service reliability and performance
- Assess circuit breaker effectiveness
- Consider any needed service architecture adjustments
- Review service usage patterns and optimization opportunities