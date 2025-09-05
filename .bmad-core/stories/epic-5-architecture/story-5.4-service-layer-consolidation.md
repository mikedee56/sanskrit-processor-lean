# Story 5.4: Service Layer Consolidation

**Epic**: Architecture Excellence  
**Story Points**: 8  
**Priority**: Medium  
**Status**: ⏳ Not Started

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete Stories 5.3 and 5.5 first

## 📋 User Story

**As a** system architect  
**I want** consolidated external services to reduce service layer complexity  
**So that** the service layer is even more lean and maintainable with fewer interdependencies

## 🎯 Business Value

- **Extreme Simplification**: Service layer from 698 lines to ~400 lines
- **Single Service Point**: All external integrations in one location
- **Reduced Complexity**: Fewer service files to maintain and test
- **Better Resource Management**: Unified connection pooling and error handling
- **Lean Compliance**: Moves closer to target 1,500 line architecture

## ✅ Acceptance Criteria

### **AC 1: MCP Client Consolidation**
- [ ] Move MCP functionality from separate client to `services/external.py`
- [ ] Consolidate WebSocket connection management
- [ ] Maintain all existing MCP method signatures
- [ ] Preserve circuit breaker protection patterns

### **AC 2: API Client Consolidation**
- [ ] Move API functionality from separate client to `services/external.py`  
- [ ] Consolidate HTTP request handling
- [ ] Maintain all existing API method signatures
- [ ] Preserve timeout and retry logic

### **AC 3: Service Layer Reduction**
- [ ] Reduce service layer from 698 to ~400 lines total
- [ ] Eliminate redundant service files
- [ ] Consolidate common service utilities
- [ ] Maintain performance at 2,600+ segments/second

### **AC 4: Gradual Migration Strategy**
- [ ] Feature flag `use_consolidated_services` in config.yaml
- [ ] Both old and new service implementations work during transition
- [ ] Zero downtime migration path
- [ ] Easy rollback if consolidation causes issues

## 🏗️ Implementation Plan

### **Phase 1: Service Analysis and Planning (2 hours)**
Understand current service architecture:

1. **Analyze existing services**
   - Map all MCP client methods and dependencies
   - Map all API client methods and dependencies
   - Identify common patterns and utilities
   - Document current error handling approaches

2. **Design consolidated interface**
   - Single `ExternalServiceManager` class
   - Unified connection management
   - Common error handling and logging
   - Feature flag integration

### **Phase 2: Gradual Consolidation (4 hours)**
Implement side-by-side services:

1. **Extend services/external.py**
   - Add MCP client functionality
   - Add API client functionality  
   - Implement unified service manager
   - Add feature flag support

2. **Update enhanced_processor.py**
   - Add conditional service loading
   - Support both old and new service implementations
   - Maintain backward compatibility during transition

### **Phase 3: Migration and Cleanup (2 hours)**
Complete the transition:

1. **Test consolidated services thoroughly**
2. **Enable feature flag by default**
3. **Remove old service files** (only after validation)
4. **Update all references and imports**

## 📁 Files to Create/Modify

### **Enhanced Files:**
- `services/external.py` - Extended with MCP and API client functionality (~300 lines total)
- `config.yaml` - Add `use_consolidated_services: false` (default during transition)
- `enhanced_processor.py` - Support both service implementations

### **Files to Remove (After Validation):**
- `services/mcp_client.py` - Functionality moved to external.py
- `services/api_client.py` - Functionality moved to external.py

### **New Files:**
- `tests/test_service_consolidation.py` - Comprehensive consolidation tests

## 🔧 Technical Specifications

### **Consolidated Service Structure:**
```python
# services/external.py (enhanced)
class ExternalServiceManager:
    """Unified manager for all external service integrations."""
    
    def __init__(self, config: dict):
        self.config = config
        self.use_consolidated = config.get('use_consolidated_services', False)
        
        if self.use_consolidated:
            self._init_consolidated_services()
        else:
            self._init_legacy_services()
    
    # MCP Methods (consolidated)
    def mcp_analyze_batch(self, segments: List[str]) -> List[dict]:
        """Consolidated MCP batch analysis."""
        
    def mcp_enhance_segment(self, text: str) -> str:
        """Consolidated MCP segment enhancement."""
    
    # API Methods (consolidated)
    def api_lookup_scripture(self, term: str) -> dict:
        """Consolidated scripture lookup."""
        
    def api_validate_iast(self, text: str) -> bool:
        """Consolidated IAST validation."""
```

### **Feature Flag Configuration:**
```yaml
# config.yaml
processing:
  use_iast_diacritics: true
  preserve_capitalization: true
  use_consolidated_services: false  # Safe default during transition

services:
  consolidated:
    mcp:
      enabled: true
      timeout: 30
      max_retries: 3
    api:
      enabled: true  
      timeout: 10
      max_retries: 2
```

### **Migration Strategy:**
```python
# enhanced_processor.py
class EnhancedSanskritProcessor:
    def __init__(self, lexicon_dir: str, config_path: str):
        config = self._load_config(config_path)
        
        if config.get('use_consolidated_services', False):
            # New consolidated approach
            self.external_services = ExternalServiceManager(config)
        else:
            # Legacy approach (during transition)
            self.external_clients = ExternalClients(config)
```

## 🧪 Test Cases

### **Service Consolidation Tests:**
```python
def test_mcp_consolidation():
    # Test MCP functionality works identically in consolidated service
    manager = ExternalServiceManager({'use_consolidated_services': True})
    result = manager.mcp_analyze_batch(['test segment'])
    assert result is not None

def test_api_consolidation():
    # Test API functionality works identically in consolidated service
    manager = ExternalServiceManager({'use_consolidated_services': True})
    result = manager.api_lookup_scripture('Krishna')
    assert result is not None

def test_feature_flag_switching():
    # Test switching between old and new implementations
    config_old = {'use_consolidated_services': False}
    config_new = {'use_consolidated_services': True}
    
    # Both should work identically
    processor_old = EnhancedSanskritProcessor('lexicons', config_old)
    processor_new = EnhancedSanskritProcessor('lexicons', config_new)
    
    result_old = processor_old.process_file('test.srt')
    result_new = processor_new.process_file('test.srt')
    
    assert result_old.text == result_new.text
```

### **Performance Tests:**
```python
def test_consolidated_performance():
    # Ensure consolidation doesn't degrade performance
    import time
    
    manager = ExternalServiceManager({'use_consolidated_services': True})
    
    start = time.time()
    for i in range(100):
        manager.mcp_enhance_segment(f"test segment {i}")
    end = time.time()
    
    # Should maintain performance benchmarks
    assert (end - start) < 10.0  # Max 10 seconds for 100 segments
```

## 📊 Success Metrics

- **Line Reduction**: Service layer from 698 to ~400 lines (-43%)
- **File Consolidation**: 5+ service files to 1 consolidated file
- **Performance Maintained**: ≥2,600 segments/second processing speed
- **Zero Breaking Changes**: Feature flag enables safe migration
- **Simplified Maintenance**: Single point for all external service logic

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Service functionality loss | High | Feature flag for gradual rollout, extensive testing |
| Performance degradation | Medium | Benchmark testing, connection pooling optimization |
| Complex migration path | Medium | Side-by-side implementation, easy rollback |
| External service conflicts | Low | Isolated service implementations, circuit breakers |

## 🔄 Story Progress Tracking

- [ ] **Started**: Service consolidation analysis begun
- [ ] **Analysis Complete**: Current service dependencies mapped
- [ ] **Consolidation Design**: Unified service manager designed
- [ ] **Implementation**: Extended external.py with consolidated services
- [ ] **Feature Flag**: Gradual migration mechanism working
- [ ] **Testing**: Both service implementations validated
- [ ] **Migration Complete**: Old service files removed safely
- [ ] **Performance Validated**: Speed maintained ≥2,600 seg/sec

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Code Size Check:**
- [ ] **Service Reduction**: 698 → 400 lines ✅
- [ ] **File Consolidation**: Multiple services → Single service ✅
- [ ] **No Dependencies**: Use only existing packages ✅
- [ ] **Performance**: Maintain 2,600+ segments/second ✅

#### **Consolidation Strategy:**
1. **Preserve Interfaces**: All existing method signatures maintained
2. **Unified Management**: Single service manager for all externals
3. **Feature Flagged**: Safe migration with easy rollback
4. **Circuit Breaker**: Maintain all existing resilience patterns
5. **Performance First**: No degradation in processing speed

### **Critical Constraints:**
- **Zero Breaking Changes**: All existing external service calls work unchanged
- **Performance Preservation**: No degradation in service response times
- **Feature Flag Control**: Easy switching between implementations
- **Single Responsibility**: Consolidated service maintains clear interfaces

## 🎯 Zero Functionality Loss Guarantee

### **Backward Compatibility Checklist:**
- [ ] All existing MCP method signatures preserved
- [ ] All existing API method signatures preserved
- [ ] All error handling patterns maintained
- [ ] All timeout and retry logic preserved
- [ ] All circuit breaker functionality intact

### **Migration Safety:**
- **Feature Flag Control**: `use_consolidated_services` flag controls behavior
- **Gradual Rollout**: Enable for testing, disable if issues found
- **Performance Monitoring**: Benchmark before/after consolidation
- **Easy Rollback**: Remove external.py enhancements, re-enable old services

### **Rollback Strategy:**
If consolidation causes issues:
1. **Immediate**: Set `use_consolidated_services: false` in config
2. **Service Restore**: Re-add old service files from git history
3. **Clean Rollback**: Remove consolidated functionality from external.py
4. **Validate**: Run full test suite to confirm rollback success

---

## 🤖 Dev Agent Instructions

**Critical Implementation Order:**
1. **Analyze current services** without breaking anything
2. **Extend external.py** with consolidated functionality
3. **Add feature flag support** to enhanced_processor.py
4. **Test both implementations** side by side
5. **Validate performance** matches current benchmarks
6. **Enable consolidation** only after thorough testing
7. **Remove old services** only after consolidation proven stable

**Lean Architecture Violations to Avoid:**
- ❌ Adding any new dependencies for service management
- ❌ Creating overly complex service abstractions
- ❌ Breaking existing service method signatures
- ❌ Reducing service response performance
- ❌ Adding more than 300 lines of consolidated service code

**Required Validations:**
```bash
# Before consolidation
wc -l services/*.py  # Record baseline: ~698 lines

# After consolidation
wc -l services/external.py  # Should be ~300 lines
python3 -m pytest tests/test_service_consolidation.py -v
python3 cli.py sample_test.srt test_output.srt  # Must work with both flags
```

**Story Status**: ✅ Ready for Implementation (After 5.3 and 5.5)