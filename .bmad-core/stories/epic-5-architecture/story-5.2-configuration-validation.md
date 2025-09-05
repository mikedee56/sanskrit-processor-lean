# Story 5.2: Configuration Schema Validation

**Epic**: Architecture Excellence  
**Story Points**: 3  
**Priority**: High  
**Status**: ⏳ Not Started

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** system administrator  
**I want** configuration validation with clear error messages  
**So that** invalid configurations are caught early and I can fix them quickly without system failures

## 🎯 Business Value

- **Early Error Detection**: Catch configuration issues before processing starts
- **Reduced Downtime**: Clear error messages enable quick fixes
- **Environment Safety**: Validate environment-specific configurations
- **User Experience**: Helpful error messages instead of cryptic failures
- **System Reliability**: Prevent silent failures from misconfiguration

## ✅ Acceptance Criteria

### **AC 1: YAML Schema Validation**
- [ ] Schema definition for `config.yaml` in `config.schema.yaml`
- [ ] Validate all existing configuration options
- [ ] Support for optional and required fields
- [ ] Type validation (boolean, string, number, array)
- [ ] Default value documentation in schema

### **AC 2: Environment-Specific Configuration**
- [ ] Support for `config.dev.yaml`, `config.prod.yaml` overrides
- [ ] Environment detection and automatic config selection
- [ ] Config inheritance (base → environment-specific overrides)
- [ ] Validation of environment-specific configurations

### **AC 3: Configuration Validation CLI**
- [ ] New CLI command: `python cli.py --validate-config`
- [ ] Validates current configuration and reports issues
- [ ] Shows effective configuration after environment overrides
- [ ] Returns appropriate exit codes (0=valid, 1=invalid)

### **AC 4: Graceful Degradation**
- [ ] Invalid configurations generate warnings, not failures
- [ ] System falls back to safe defaults when possible
- [ ] Clear error messages with suggestions for fixes
- [ ] Backward compatibility with existing `config.yaml` files

## 🏗️ Implementation Plan

### **Phase 1: Schema Definition (1 hour)**
Create comprehensive schema for current configuration:
```yaml
# Current config.yaml structure to validate
processing:
  use_iast_diacritics: boolean
  preserve_capitalization: boolean
  fuzzy_matching:
    enabled: boolean
    threshold: number (0.0-1.0)
    log_matches: boolean
lexicons:
  corrections_file: string
  proper_nouns_file: string
```

### **Phase 2: Validation Implementation (2 hours)**
Build validation system:
- YAML schema validation using existing PyYAML
- Environment detection and config layering
- Graceful error handling with helpful messages
- **Lean Constraint**: No new dependencies

### **Phase 3: CLI Integration (1 hour)**
Add validation to CLI:
- New `--validate-config` flag
- Integration with existing config loading
- Enhanced error reporting
- **Zero Breaking Changes**: All existing commands work unchanged

## 📁 Files to Create/Modify

### **New Files:**
- `config.schema.yaml` - Configuration schema definition
- `services/config_validator.py` - Validation logic (~50 lines)
- `config.dev.yaml` - Development environment example
- `config.prod.yaml` - Production environment example
- `tests/test_config_validation.py` - Comprehensive tests

### **Modified Files:**
- `enhanced_processor.py` - Enhanced config loading with validation
- `cli.py` - Add `--validate-config` flag and validation logic
- `config.yaml` - Add comments referencing schema

## 🔧 Technical Specifications

### **Schema Format (config.schema.yaml):**
```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
  processing:
    type: object
    properties:
      use_iast_diacritics:
        type: boolean
        default: true
        description: "Enable IAST diacritics in output"
      preserve_capitalization:
        type: boolean
        default: true
      fuzzy_matching:
        type: object
        properties:
          enabled: {type: boolean, default: true}
          threshold: {type: number, minimum: 0.0, maximum: 1.0, default: 0.8}
          log_matches: {type: boolean, default: false}
        required: [enabled]
    required: [use_iast_diacritics]
  lexicons:
    type: object
    properties:
      corrections_file: {type: string, default: "corrections.yaml"}
      proper_nouns_file: {type: string, default: "proper_nouns.yaml"}
    required: [corrections_file, proper_nouns_file]
required: [processing, lexicons]
```

### **Environment Configuration Pattern:**
```bash
# Environment detection priority:
1. config.{ENVIRONMENT}.yaml (if ENVIRONMENT set)
2. config.local.yaml (for local development)  
3. config.yaml (base configuration)
```

### **Validation Logic (services/config_validator.py):**
```python
class ConfigValidator:
    def __init__(self, schema_path: Path):
        # Load schema without heavy dependencies
    
    def validate_config(self, config: dict) -> ValidationResult:
        # Return warnings/errors with helpful messages
        
    def load_environment_config(self, base_config_path: Path) -> dict:
        # Handle environment-specific loading
```

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_valid_config():
    validator = ConfigValidator("config.schema.yaml")
    config = load_yaml("config.yaml")
    result = validator.validate_config(config)
    assert result.is_valid

def test_invalid_config():
    # Test with invalid threshold (outside 0.0-1.0)
    # Test with missing required fields
    # Test with wrong data types

def test_environment_config():
    # Test config inheritance
    # Test environment detection
    # Test override behavior
```

### **Integration Tests:**
```bash
# Test validation CLI
python cli.py --validate-config
echo $?  # Should be 0

# Test with invalid config
mv config.yaml config.yaml.backup
echo "invalid: yaml: content" > config.yaml
python cli.py --validate-config
echo $?  # Should be 1

# Test processing still works with warnings
python cli.py sample_test.srt test_output.srt --simple
```

## 📊 Success Metrics

- **Early Detection**: Configuration errors caught before processing
- **User Experience**: Clear, actionable error messages
- **Reliability**: 100% backward compatibility with existing configs
- **Performance**: Validation adds <100ms to startup time
- **Maintainability**: Schema-driven validation reduces support issues

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing configs | High | Graceful degradation, warnings not errors |
| Performance overhead | Low | Cache validation results, optional validation |
| Schema maintenance overhead | Medium | Keep schema simple, focus on critical validations |
| Environment detection complexity | Medium | Simple environment variable detection only |

## 🔄 Story Progress Tracking

- [ ] **Started**: Schema design begun
- [ ] **Schema Definition**: config.schema.yaml created and validated
- [ ] **Validator Implementation**: services/config_validator.py completed
- [ ] **CLI Integration**: --validate-config flag working
- [ ] **Environment Support**: Environment-specific configs working
- [ ] **Testing**: All validation tests passing
- [ ] **Backward Compatibility**: All existing functionality preserved

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Dependencies Check:**
- [ ] **No New Dependencies**: Use only existing PyYAML ✅
- [ ] **Minimal Code**: Target ~50 lines for validator ✅
- [ ] **Performance**: <100ms validation overhead ✅
- [ ] **Simple Config**: YAML-only, no complex systems ✅

#### **Implementation Constraints:**
- Must work with existing PyYAML (no jsonschema library)
- Validation logic must be simple and maintainable
- No breaking changes to existing configuration loading
- Environment detection via simple `os.environ` checks only

### **Design Principles:**
- **Additive Only**: New validation supplements existing loading
- **Fail Safe**: Invalid configs warn but allow processing with defaults
- **Clear Messages**: Every error includes suggested fix
- **Zero Dependencies**: Implementation using stdlib and existing packages

### **Configuration Strategy:**
```python
# Validation approach
def load_and_validate_config(config_path: Path) -> dict:
    # 1. Load base config
    # 2. Apply environment overrides  
    # 3. Validate against schema
    # 4. Log warnings for invalid values
    # 5. Return config with defaults applied
```

## 🎯 Zero Functionality Loss Guarantee

### **Backward Compatibility Requirements:**
- [ ] All existing `config.yaml` files continue to work
- [ ] No changes to config loading behavior by default
- [ ] Validation is optional (`--validate-config` flag)
- [ ] Invalid configs generate warnings, not failures
- [ ] All existing CLI commands work unchanged

### **Safety Mechanisms:**
- [ ] Feature flag: `validate_config: false` disables validation
- [ ] Graceful degradation: Use defaults for invalid values
- [ ] Clear rollback: Remove validator files to disable completely
- [ ] Performance safety: Validation timeout after 5 seconds

---

## 🤖 Dev Agent Instructions

**Implementation Order:**
1. Create schema definition matching current config.yaml exactly
2. Implement lightweight validator using only PyYAML
3. Add environment config support with simple inheritance
4. Integrate CLI validation flag
5. Add comprehensive tests
6. Verify zero breaking changes

**Critical Requirements:**
- **NO NEW DEPENDENCIES** - Use only PyYAML and stdlib
- **BACKWARD COMPATIBLE** - All existing configs must work
- **LEAN IMPLEMENTATION** - Keep validator under 50 lines
- **CLEAR ERRORS** - Every validation error includes fix suggestion

**Story Status**: ✅ Ready for Implementation