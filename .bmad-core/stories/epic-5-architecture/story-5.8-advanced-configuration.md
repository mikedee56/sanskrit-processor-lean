# Story 5.8: Advanced Configuration Management

**Epic**: Architecture Excellence  
**Story Points**: 8  
**Priority**: Low  
**Status**: ⏳ Not Started

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete Story 5.7 first  
⚠️ **MEDIUM RISK**: Complex configuration management requires careful validation

## 📋 User Story

**As a** deployment engineer  
**I want** environment-specific configuration management with inheritance  
**So that** I can deploy the same codebase across different environments safely and efficiently

## 🎯 Business Value

- **Environment Safety**: Separate configurations for dev, staging, production
- **DRY Configuration**: Base configuration with environment-specific overrides
- **Deployment Flexibility**: Same codebase works across all environments
- **Security**: Environment variables for sensitive values (API keys, etc.)
- **Maintainability**: Clear configuration hierarchy and inheritance

## ✅ Acceptance Criteria

### **AC 1: Environment Detection**
- [ ] Automatic environment detection via `ENVIRONMENT` variable
- [ ] Support for standard environments: `dev`, `staging`, `prod`
- [ ] Fallback to `development` if no environment specified
- [ ] Clear environment reporting in logs and CLI output

### **AC 2: Configuration Inheritance**
- [ ] Base configuration in `config/config.base.yaml`
- [ ] Environment overrides in `config/config.{env}.yaml`
- [ ] Deep merging of nested configuration objects
- [ ] Environment-specific values override base values

### **AC 3: Environment Variable Substitution**
- [ ] Environment variable substitution in configuration files
- [ ] Syntax: `${ENV_VAR}` or `${ENV_VAR:default_value}`
- [ ] Support for sensitive values (API keys, database URLs)
- [ ] Clear error messages for missing required environment variables

### **AC 4: Migration and Compatibility**
- [ ] Migration tool to convert existing `config.yaml` to new structure
- [ ] Backward compatibility with single `config.yaml` files
- [ ] Validation tool to check configuration correctness
- [ ] Clear documentation for migration path

## 🏗️ Implementation Plan

### **Phase 1: Configuration Architecture (3 hours)**
Design new configuration system:

1. **Design configuration hierarchy**
   - Base configuration structure
   - Environment-specific override patterns
   - Environment variable substitution system
   - Validation and error handling

2. **Implement configuration manager**
   - Environment detection logic
   - Configuration loading and merging
   - Environment variable substitution
   - Validation and error reporting

### **Phase 2: Migration Tools (3 hours)**
Build migration and compatibility:

1. **Create migration utilities**
   - Convert existing config.yaml to new structure
   - Validation tools for configuration correctness
   - Backup and rollback mechanisms
   - Documentation generation

2. **Maintain backward compatibility**
   - Support existing single config.yaml
   - Graceful fallback mechanisms
   - Clear upgrade path documentation

### **Phase 3: Integration and Testing (2 hours)**
Integrate with existing system:

1. **Update core processors**
   - Enhanced config loading in processors
   - Environment reporting and logging
   - Configuration validation integration

2. **Comprehensive testing**
   - Multi-environment configuration testing
   - Environment variable substitution testing
   - Migration tool testing
   - Backward compatibility validation

## 📁 Files to Create/Modify

### **New Files:**
- `config/config.base.yaml` - Base configuration template
- `config/config.dev.yaml` - Development environment overrides
- `config/config.staging.yaml` - Staging environment overrides
- `config/config.prod.yaml` - Production environment overrides
- `utils/config_manager.py` - Advanced configuration management (~150 lines)
- `tools/migrate_config.py` - Configuration migration utility (~80 lines)
- `tests/test_config_management.py` - Configuration management tests

### **Modified Files:**
- `enhanced_processor.py` - Use advanced configuration management
- `cli.py` - Environment reporting and configuration validation
- `config.yaml` - Add migration notice or keep as fallback

## 🔧 Technical Specifications

### **Configuration Directory Structure:**
```
config/
├── config.base.yaml        # Base configuration (required)
├── config.dev.yaml         # Development overrides
├── config.staging.yaml     # Staging overrides
├── config.prod.yaml        # Production overrides
└── README.md              # Configuration documentation
```

### **Configuration Manager:**
```python
# utils/config_manager.py
import os
import yaml
import re
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Advanced configuration management with environment support."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.environment = os.environ.get('ENVIRONMENT', 'dev').lower()
        self._cache = {}
        
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration with environment inheritance."""
        if not force_reload and 'merged_config' in self._cache:
            return self._cache['merged_config']
        
        # Load base configuration
        base_config = self._load_base_config()
        
        # Load environment-specific overrides
        env_config = self._load_environment_config()
        
        # Merge configurations
        merged_config = self._deep_merge(base_config, env_config)
        
        # Substitute environment variables
        final_config = self._substitute_env_vars(merged_config)
        
        # Cache and return
        self._cache['merged_config'] = final_config
        return final_config
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration."""
        base_path = self.config_dir / "config.base.yaml"
        
        if not base_path.exists():
            # Fallback to legacy config.yaml
            legacy_path = Path("config.yaml")
            if legacy_path.exists():
                return self._load_yaml_file(legacy_path)
            else:
                raise FileNotFoundError(f"No base configuration found at {base_path}")
        
        return self._load_yaml_file(base_path)
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        env_path = self.config_dir / f"config.{self.environment}.yaml"
        
        if env_path.exists():
            return self._load_yaml_file(env_path)
        else:
            # No environment-specific config is okay
            return {}
    
    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Safely load YAML file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")
        except Exception as e:
            raise IOError(f"Cannot read {path}: {e}")
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _substitute_env_vars(self, config: Dict) -> Dict:
        """Substitute environment variables in configuration."""
        def substitute_value(value):
            if isinstance(value, str):
                return self._substitute_string(value)
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return substitute_value(config)
    
    def _substitute_string(self, text: str) -> str:
        """Substitute environment variables in string."""
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2)
            
            env_value = os.environ.get(var_name)
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                raise ValueError(f"Required environment variable not set: {var_name}")
        
        return re.sub(pattern, replace_var, text)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation report."""
        try:
            config = self.load_config()
            return {
                "valid": True,
                "environment": self.environment,
                "config_files_used": self._get_config_files_used(),
                "env_vars_substituted": self._get_env_vars_used(config)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "environment": self.environment
            }
```

### **Base Configuration Template:**
```yaml
# config/config.base.yaml
# Base Sanskrit Processor Configuration
# Environment-specific values should be overridden in config.{env}.yaml

processing:
  use_iast_diacritics: true
  preserve_capitalization: true
  fuzzy_matching:
    enabled: true
    threshold: 0.8
    log_matches: false

lexicons:
  corrections_file: "corrections.yaml"
  proper_nouns_file: "proper_nouns.yaml"

# External services (environment-specific)
services:
  mcp:
    enabled: false  # Override in environment configs
    timeout: 30
    
  api:
    enabled: false  # Override in environment configs
    base_url: "${API_BASE_URL:http://localhost:8080}"
    api_key: "${API_KEY}"  # Required environment variable
    timeout: 10

# Logging configuration
logging:
  level: "INFO"
  json_output: false
  include_context: true

# Environment-specific settings (to be overridden)
environment:
  name: "base"
  debug: false
  performance_monitoring: false
```

### **Environment-Specific Configurations:**
```yaml
# config/config.dev.yaml
# Development environment overrides

services:
  mcp:
    enabled: true
    timeout: 60  # Longer timeout for debugging
    
  api:
    enabled: true
    timeout: 30

logging:
  level: "DEBUG"
  include_context: true

environment:
  name: "development"
  debug: true
  performance_monitoring: true

# Development-specific plugins
plugins:
  enabled: true
  enabled_plugins:
    - performance_monitor
    - debug_helper
```

```yaml
# config/config.prod.yaml
# Production environment overrides

services:
  mcp:
    enabled: true
    timeout: 15  # Stricter timeout for production
    
  api:
    enabled: true
    timeout: 5

logging:
  level: "WARNING"
  json_output: true  # Structured logging for production
  include_context: false

environment:
  name: "production"
  debug: false
  performance_monitoring: false

# Production security settings
security:
  strict_validation: true
  disable_debug_endpoints: true
```

## 🧪 Test Cases

### **Configuration Management Tests:**
```python
def test_environment_detection():
    # Test default environment
    manager = ConfigManager()
    assert manager.environment == "dev"
    
    # Test custom environment
    os.environ['ENVIRONMENT'] = 'prod'
    manager = ConfigManager()
    assert manager.environment == "prod"

def test_configuration_inheritance():
    manager = ConfigManager("tests/config")
    config = manager.load_config()
    
    # Should have base config values
    assert config['processing']['use_iast_diacritics'] == True
    
    # Should have environment overrides
    assert config['logging']['level'] == "DEBUG"  # from dev config

def test_environment_variable_substitution():
    os.environ['API_KEY'] = 'test_key_123'
    os.environ['API_BASE_URL'] = 'https://test-api.example.com'
    
    manager = ConfigManager("tests/config")
    config = manager.load_config()
    
    assert config['services']['api']['api_key'] == 'test_key_123'
    assert config['services']['api']['base_url'] == 'https://test-api.example.com'

def test_missing_required_env_var():
    if 'REQUIRED_API_KEY' in os.environ:
        del os.environ['REQUIRED_API_KEY']
    
    manager = ConfigManager("tests/config")
    
    with pytest.raises(ValueError, match="Required environment variable"):
        manager.load_config()

def test_backward_compatibility():
    # Test loading legacy config.yaml
    manager = ConfigManager("tests/legacy")
    config = manager.load_config()
    
    # Should load successfully from config.yaml
    assert 'processing' in config
```

### **Migration Tool Tests:**
```python
def test_config_migration():
    from tools.migrate_config import migrate_config
    
    # Create test legacy config
    legacy_config = {
        'processing': {'use_iast_diacritics': True},
        'services': {'api': {'enabled': True}}
    }
    
    result = migrate_config(legacy_config, "tests/output")
    
    assert result['success'] == True
    assert os.path.exists("tests/output/config.base.yaml")

def test_migration_validation():
    # Test migration produces valid configuration
    migrate_config({'processing': {'use_iast_diacritics': True}}, "tests/output")
    
    manager = ConfigManager("tests/output")
    config = manager.load_config()
    
    assert config['processing']['use_iast_diacritics'] == True
```

### **Integration Tests:**
```bash
# Test different environments
ENVIRONMENT=dev python3 cli.py sample_test.srt test_output_dev.srt
ENVIRONMENT=prod python3 cli.py sample_test.srt test_output_prod.srt

# Test environment variable substitution
export API_KEY="test_key"
export API_BASE_URL="https://test.example.com"
python3 cli.py sample_test.srt test_output.srt

# Test configuration validation
python3 cli.py --validate-config --environment dev
python3 cli.py --validate-config --environment prod

# Test migration tool
python3 tools/migrate_config.py config.yaml config/
```

## 📊 Success Metrics

- **Environment Safety**: Clear separation between dev/staging/prod configurations
- **Configuration DRY**: Base configuration with minimal environment-specific overrides
- **Security**: Sensitive values managed via environment variables
- **Migration Success**: Existing installations can migrate without data loss
- **Backward Compatibility**: Legacy config.yaml continues to work

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex configuration debugging | Medium | Clear validation tools, detailed error messages |
| Environment variable management | Medium | Documentation, default values where possible |
| Migration tool failures | High | Extensive testing, backup mechanisms, rollback |
| Configuration file proliferation | Low | Clear naming conventions, documentation |
| Security exposure of sensitive values | High | Clear guidelines, environment variable validation |

## 🔄 Story Progress Tracking

- [ ] **Started**: Advanced configuration design begun
- [ ] **Config Manager**: Environment-aware configuration loading implemented
- [ ] **Environment Detection**: Automatic environment detection working
- [ ] **Variable Substitution**: Environment variable substitution functional
- [ ] **Migration Tools**: Configuration migration utilities completed
- [ ] **Integration**: Advanced config integrated with processors
- [ ] **Testing**: Multi-environment testing completed
- [ ] **Documentation**: Configuration management guide completed

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Code Size Check:**
- [ ] **Config Manager**: <150 lines ✅
- [ ] **Migration Tools**: <100 lines ✅
- [ ] **No Dependencies**: Use only PyYAML and stdlib ✅
- [ ] **Backward Compatible**: Legacy config.yaml still works ✅

#### **Configuration Strategy:**
1. **Additive Enhancement**: Existing config.yaml continues to work
2. **Optional Migration**: Users can choose when to upgrade
3. **Clear Benefits**: Environment-specific configs provide clear value
4. **Simple Migration**: Automated tools make upgrade easy
5. **Rollback Safety**: Easy to revert to single config.yaml

### **Security Best Practices:**
- **Environment Variables**: Use for all sensitive values (API keys, passwords)
- **Default Values**: Provide secure defaults where possible
- **Validation**: Validate all configuration values before use
- **Documentation**: Clear guidelines for secure configuration management
- **Access Control**: Recommend proper file permissions for config files

### **Migration Strategy:**
```python
# Migration process
1. Backup existing config.yaml
2. Create config/ directory
3. Convert config.yaml to config.base.yaml
4. Create environment-specific overrides
5. Update application to use ConfigManager
6. Validate new configuration works
7. Provide rollback instructions
```

## 🎯 Zero Functionality Loss Guarantee

### **Backward Compatibility Requirements:**
- [ ] Existing config.yaml files continue to work unchanged
- [ ] No changes to existing configuration loading behavior by default
- [ ] Advanced configuration is opt-in, not mandatory
- [ ] All existing configuration options preserved
- [ ] Migration is optional and reversible

### **Safety Mechanisms:**
- [ ] Legacy fallback: ConfigManager falls back to config.yaml automatically
- [ ] Validation tools: Comprehensive configuration validation before deployment
- [ ] Migration backup: Automatic backup of original configuration
- [ ] Environment validation: Clear error messages for configuration issues
- [ ] Rollback documentation: Clear instructions for reverting changes

### **Rollback Strategy:**
If advanced configuration causes issues:
1. **Immediate**: Delete config/ directory, use original config.yaml
2. **Config Manager**: Remove ConfigManager usage, use original config loading
3. **Environment Variables**: Remove environment variable dependencies
4. **File Cleanup**: Remove advanced config files and utilities
5. **Validation**: Test with original configuration to confirm rollback

---

## 🤖 Dev Agent Instructions

**Implementation Order:**
1. Create ConfigManager with environment detection and inheritance
2. Implement environment variable substitution safely
3. Build migration tools with comprehensive backup mechanisms
4. Maintain backward compatibility with existing config.yaml
5. Add configuration validation and reporting tools
6. Integrate with existing processors gradually
7. Create comprehensive documentation and examples

**Critical Requirements:**
- **BACKWARD COMPATIBLE** - Existing config.yaml files must continue working
- **SAFE MIGRATION** - Migration tools must backup and be reversible
- **CLEAR BENEFITS** - Advanced configuration must provide obvious value
- **SECURITY CONSCIOUS** - Proper handling of sensitive configuration values

**Lean Architecture Violations to Avoid:**
- ❌ Adding heavy configuration management dependencies
- ❌ Breaking existing configuration loading patterns
- ❌ Making advanced configuration mandatory instead of optional
- ❌ Creating overly complex configuration hierarchies
- ❌ Adding more than 250 lines total for advanced configuration system

**Required Validations:**
```bash
# Test backward compatibility (CRITICAL)
python3 cli.py sample_test.srt test_output.srt  # Must work with existing config.yaml

# Test advanced configuration
ENVIRONMENT=dev python3 cli.py sample_test.srt test_dev.srt
ENVIRONMENT=prod python3 cli.py sample_test.srt test_prod.srt

# Test migration tool
python3 tools/migrate_config.py config.yaml config/
python3 cli.py sample_test.srt test_migrated.srt  # Must work after migration

# Test validation
python3 cli.py --validate-config
```

**Story Status**: ✅ Ready for Implementation (After 5.7)  
**Risk Level**: 🟡 MEDIUM - Requires careful migration and validation testing