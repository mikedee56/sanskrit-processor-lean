# Story 5.7: Plugin Architecture Framework

**Epic**: Architecture Excellence  
**Story Points**: 13  
**Priority**: Low  
**Status**: ⏳ Not Started

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete all previous stories (5.1-5.6) first  
⚠️ **HIGH RISK**: Most complex story - requires extensive testing and gradual rollout

## 📋 User Story

**As a** developer extending the Sanskrit processor  
**I want** a plugin system for custom processing capabilities  
**So that** I can add specialized functionality without modifying core code or breaking lean architecture

## 🎯 Business Value

- **Extensibility**: Add custom processing without core code changes
- **Maintainability**: Core system remains focused and unmodified
- **Innovation**: Enable community contributions and specialized features
- **Separation of Concerns**: Plugins handle specific use cases independently
- **Risk Isolation**: Plugin failures don't affect core processing

## ✅ Acceptance Criteria

### **AC 1: Plugin Interface Definition**
- [ ] Clear plugin interface contracts (`IProcessor`, `IEnhancer`, `IFormatter`)
- [ ] Plugin lifecycle management (init, process, cleanup)
- [ ] Plugin metadata and capability registration
- [ ] Version compatibility checking between plugins and core

### **AC 2: Plugin Discovery and Loading**
- [ ] Automatic plugin discovery in `plugins/` directory
- [ ] Safe plugin loading with error isolation
- [ ] Plugin dependency resolution and ordering
- [ ] Dynamic plugin enable/disable without restart

### **AC 3: Plugin Integration Points**
- [ ] Pre-processing hooks for custom text preparation
- [ ] Post-processing hooks for custom formatting
- [ ] Custom correction rules and lexicon extensions
- [ ] External service integration plugins

### **AC 4: Sample Plugin Implementations**
- [ ] Custom corrections plugin with domain-specific rules
- [ ] Custom formatter plugin for specialized output formats
- [ ] Template plugin showing all integration points
- [ ] Performance monitoring plugin using framework from 5.6

## 🏗️ Implementation Plan

### **Phase 1: Plugin Framework Design (4 hours)**
Design extensible plugin architecture:

1. **Define plugin interfaces**
   - Core plugin contract definitions
   - Plugin metadata requirements
   - Error handling and isolation patterns
   - Version compatibility framework

2. **Plugin discovery system**
   - Automatic plugin detection
   - Safe loading with error isolation
   - Plugin dependency management
   - Configuration integration

### **Phase 2: Core Integration (6 hours)**
Integrate plugin system with core:

1. **Plugin execution points**
   - Hook points in processing pipeline
   - Plugin chain execution
   - Result aggregation and merging
   - Error handling and fallback

2. **Configuration and management**
   - Plugin configuration in config.yaml
   - Runtime plugin management
   - Plugin enable/disable controls
   - Performance impact monitoring

### **Phase 3: Sample Plugins (3 hours)**
Create example plugins:

1. **Sample plugin implementations**
   - Custom corrections plugin
   - Custom formatter plugin
   - Template plugin for developers
   - Integration testing plugins

2. **Documentation and testing**
   - Plugin development guide
   - Comprehensive plugin testing
   - Integration test scenarios
   - Performance validation

## 📁 Files to Create/Modify

### **New Files:**
- `plugins/__init__.py` - Plugin package initialization (~20 lines)
- `plugins/base_plugin.py` - Plugin base classes and interfaces (~80 lines)
- `plugins/examples/custom_corrections.py` - Sample corrections plugin (~60 lines)
- `plugins/examples/custom_formatter.py` - Sample formatter plugin (~40 lines)
- `plugins/examples/template_plugin.py` - Template for developers (~50 lines)
- `utils/plugin_loader.py` - Plugin discovery and loading (~100 lines)
- `tests/test_plugin_system.py` - Comprehensive plugin tests

### **Modified Files:**
- `sanskrit_processor_v2.py` - Add plugin hook points (minimal changes)
- `enhanced_processor.py` - Plugin integration for enhanced processing
- `config.yaml` - Plugin configuration section
- `cli.py` - Plugin-related CLI options

## 🔧 Technical Specifications

### **Plugin Interface Definition:**
```python
# plugins/base_plugin.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class PluginMetadata:
    """Plugin metadata and capability information."""
    def __init__(self, name: str, version: str, description: str):
        self.name = name
        self.version = version
        self.description = description
        self.capabilities = []
        self.dependencies = []

class BasePlugin(ABC):
    """Base plugin interface for all Sanskrit processor plugins."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information."""
        pass
    
    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """Initialize plugin with configuration. Returns success status."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup plugin resources."""
        pass

class IProcessor(BasePlugin):
    """Interface for text processing plugins."""
    
    @abstractmethod
    def process_text(self, text: str, context: dict = None) -> str:
        """Process text and return modified version."""
        pass

class IEnhancer(BasePlugin):
    """Interface for text enhancement plugins."""
    
    @abstractmethod
    def enhance_segment(self, segment: str, metadata: dict = None) -> dict:
        """Enhance segment and return enhancement data."""
        pass

class IFormatter(BasePlugin):
    """Interface for output formatting plugins."""
    
    @abstractmethod
    def format_output(self, segments: List[str], format_options: dict = None) -> str:
        """Format output according to plugin specifications."""
        pass
```

### **Plugin Loader System:**
```python
# utils/plugin_loader.py
import os
import importlib
import logging
from typing import Dict, List, Type
from plugins.base_plugin import BasePlugin

class PluginLoader:
    """Safe plugin discovery and loading system."""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.loaded_plugins = {}
        self.failed_plugins = {}
        self.logger = logging.getLogger(__name__)
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in plugin directory."""
        plugins = []
        
        if not os.path.exists(self.plugin_dir):
            return plugins
            
        for item in os.listdir(self.plugin_dir):
            if item.endswith('.py') and not item.startswith('__'):
                plugins.append(item[:-3])  # Remove .py extension
                
        return plugins
    
    def load_plugin(self, plugin_name: str, config: dict = None) -> Optional[BasePlugin]:
        """Safely load and initialize a plugin."""
        try:
            module_name = f"{self.plugin_dir}.{plugin_name}"
            module = importlib.import_module(module_name)
            
            # Look for plugin class (convention: CapitalizedPluginName)
            plugin_class_name = ''.join(word.capitalize() for word in plugin_name.split('_'))
            plugin_class = getattr(module, plugin_class_name, None)
            
            if plugin_class and issubclass(plugin_class, BasePlugin):
                plugin_instance = plugin_class()
                
                if plugin_instance.initialize(config or {}):
                    self.loaded_plugins[plugin_name] = plugin_instance
                    self.logger.info(f"Successfully loaded plugin: {plugin_name}")
                    return plugin_instance
                else:
                    self.logger.warning(f"Plugin initialization failed: {plugin_name}")
                    
        except Exception as e:
            self.failed_plugins[plugin_name] = str(e)
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            
        return None
    
    def get_plugins_by_interface(self, interface: Type) -> List[BasePlugin]:
        """Get all loaded plugins implementing specific interface."""
        return [plugin for plugin in self.loaded_plugins.values() 
                if isinstance(plugin, interface)]
```

### **Configuration Integration:**
```yaml
# config.yaml (enhanced)
plugins:
  enabled: false  # Master plugin enable/disable
  directory: "plugins"
  auto_discover: true
  
  # Individual plugin configuration
  enabled_plugins:
    - custom_corrections
    - performance_monitor
  
  disabled_plugins:
    - experimental_plugin
  
  # Plugin-specific settings
  custom_corrections:
    strict_mode: false
    custom_lexicon: "domain_specific.yaml"
  
  performance_monitor:
    detailed_timing: true
    memory_tracking: false
```

### **Sample Plugin Implementation:**
```python
# plugins/examples/custom_corrections.py
from plugins.base_plugin import IProcessor, PluginMetadata
import yaml
import re

class CustomCorrections(IProcessor):
    """Sample plugin for domain-specific corrections."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Custom Corrections",
            version="1.0.0",
            description="Apply domain-specific text corrections"
        )
    
    def initialize(self, config: dict) -> bool:
        self.corrections = {}
        custom_lexicon = config.get('custom_lexicon')
        
        if custom_lexicon and os.path.exists(custom_lexicon):
            try:
                with open(custom_lexicon, 'r', encoding='utf-8') as f:
                    self.corrections = yaml.safe_load(f) or {}
                return True
            except Exception as e:
                logging.error(f"Failed to load custom lexicon: {e}")
                return False
        
        # Default to empty corrections if no custom lexicon
        return True
    
    def cleanup(self):
        self.corrections.clear()
    
    def process_text(self, text: str, context: dict = None) -> str:
        """Apply custom corrections to text."""
        result = text
        
        for incorrect, correct in self.corrections.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(incorrect) + r'\b'
            result = re.sub(pattern, correct, result, flags=re.IGNORECASE)
        
        return result
```

## 🧪 Test Cases

### **Plugin System Tests:**
```python
def test_plugin_discovery():
    loader = PluginLoader("tests/test_plugins")
    plugins = loader.discover_plugins()
    assert len(plugins) > 0
    assert "test_plugin" in plugins

def test_plugin_loading():
    loader = PluginLoader("tests/test_plugins")
    plugin = loader.load_plugin("test_plugin", {"test_config": "value"})
    assert plugin is not None
    assert plugin.metadata.name == "Test Plugin"

def test_plugin_interface_filtering():
    loader = PluginLoader("tests/test_plugins")
    loader.load_plugin("processor_plugin")
    loader.load_plugin("formatter_plugin")
    
    processors = loader.get_plugins_by_interface(IProcessor)
    formatters = loader.get_plugins_by_interface(IFormatter)
    
    assert len(processors) >= 1
    assert len(formatters) >= 1

def test_plugin_error_isolation():
    # Test that plugin failures don't crash core system
    loader = PluginLoader("tests/test_plugins")
    
    # Try to load a broken plugin
    plugin = loader.load_plugin("broken_plugin")
    assert plugin is None
    assert "broken_plugin" in loader.failed_plugins
    
    # Core system should still work
    processor = SanskritProcessor("lexicons")
    result = processor.process_text("test text")
    assert result is not None
```

### **Plugin Integration Tests:**
```python
def test_plugin_processing_chain():
    # Test plugins work within core processing pipeline
    config = {
        "plugins": {
            "enabled": True,
            "enabled_plugins": ["custom_corrections"]
        }
    }
    
    processor = SanskritProcessor("lexicons", config)
    result = processor.process_text("incorrect_word")
    
    # Should apply both core and plugin corrections
    assert "corrected_word" in result

def test_plugin_disable_fallback():
    # Test system works when plugins disabled
    config = {
        "plugins": {
            "enabled": False
        }
    }
    
    processor = SanskritProcessor("lexicons", config)
    result = processor.process_text("test text")
    
    # Should work normally without plugins
    assert result is not None
```

### **CLI Integration Tests:**
```bash
# Test with plugins enabled
python3 cli.py sample_test.srt test_output.srt --enable-plugins

# Test with specific plugins
python3 cli.py sample_test.srt test_output.srt --plugins custom_corrections,formatter

# Test plugin listing
python3 cli.py --list-plugins

# Test without plugins (should work as before)
python3 cli.py sample_test.srt test_output.srt
```

## 📊 Success Metrics

- **Extensibility**: Successful implementation of 3+ sample plugins
- **Stability**: Core system never crashes due to plugin failures
- **Performance**: <5% performance impact when plugins enabled
- **Usability**: Clear plugin development documentation and examples
- **Isolation**: Plugin errors don't affect core processing

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Plugin crashes affecting core system | High | Error isolation, try/catch around all plugin calls |
| Performance degradation from plugin overhead | Medium | Optional plugin system, performance monitoring |
| Complex plugin dependency management | Medium | Keep plugin system simple, minimal dependencies |
| Security issues from arbitrary plugin code | High | Plugin sandboxing, clear security guidelines |
| Maintenance overhead of plugin API | Medium | Stable plugin interfaces, backward compatibility |

## 🔄 Story Progress Tracking

- [ ] **Started**: Plugin architecture design begun
- [ ] **Interface Definition**: Plugin contracts and interfaces defined
- [ ] **Plugin Loader**: Discovery and loading system implemented
- [ ] **Core Integration**: Hook points added to processing pipeline
- [ ] **Sample Plugins**: Example plugins implemented and tested
- [ ] **Documentation**: Plugin development guide completed
- [ ] **Testing**: Comprehensive plugin system testing completed
- [ ] **Validation**: Zero impact on core system when plugins disabled

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Code Size Check:**
- [ ] **Plugin Framework**: <300 lines total ✅
- [ ] **Core Integration**: <50 lines added to existing files ✅
- [ ] **No Dependencies**: Use only stdlib and existing packages ✅
- [ ] **Optional System**: Zero impact when disabled ✅

#### **Plugin System Constraints:**
1. **Error Isolation**: Plugin failures never crash core system
2. **Optional by Default**: Plugins disabled unless explicitly enabled
3. **Minimal Overhead**: <5% performance impact when enabled
4. **Simple Interface**: Easy to understand and implement
5. **Backward Compatible**: Core system works unchanged without plugins

### **Security Considerations:**
- **Code Execution**: Plugins execute arbitrary Python code - requires trust
- **File Access**: Plugins have same file system access as main process
- **Network Access**: Plugins can make network requests
- **Resource Usage**: No built-in resource limiting for plugins
- **Best Practice**: Only load plugins from trusted sources

### **Plugin Development Guidelines:**
```python
# Plugin naming convention: snake_case file, PascalCase class
# File: custom_formatter.py
# Class: CustomFormatter

# Plugin must inherit from appropriate interface
class CustomFormatter(IFormatter):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Custom Formatter",
            version="1.0.0", 
            description="Custom output formatting"
        )
    
    def initialize(self, config: dict) -> bool:
        # Setup plugin, return True if successful
        return True
    
    def cleanup(self):
        # Clean up resources
        pass
    
    def format_output(self, segments: List[str], format_options: dict = None) -> str:
        # Implement formatting logic
        pass
```

## 🎯 Zero Functionality Loss Guarantee

### **Backward Compatibility Requirements:**
- [ ] Core system works identically when plugins disabled (default)
- [ ] All existing CLI commands and options work unchanged
- [ ] All existing processing behavior preserved
- [ ] Plugin system is purely additive, never replaces core functionality
- [ ] Easy complete removal if plugin system causes issues

### **Safety Mechanisms:**
- [ ] Master plugin disable: `plugins.enabled: false` (default)
- [ ] Individual plugin disable: Remove from `enabled_plugins` list
- [ ] Error isolation: Plugin failures don't affect core processing
- [ ] Performance monitoring: Track plugin performance impact
- [ ] Easy removal: Delete plugins/ directory to remove completely

### **Rollback Strategy:**
If plugin system causes any issues:
1. **Immediate**: Set `plugins.enabled: false` in config.yaml
2. **Plugin Removal**: Delete specific problematic plugins from plugins/
3. **Complete Removal**: Delete entire plugins/ directory and plugin_loader.py
4. **Code Cleanup**: Remove plugin hook points from core files
5. **Validation**: Run full test suite to ensure core system unaffected

---

## 🤖 Dev Agent Instructions

**CRITICAL: HIGH RISK STORY**
This is the most complex story with highest risk. Implement with extreme care:

**Implementation Order:**
1. **Design plugin interfaces** - Keep them simple and focused
2. **Implement plugin loader** - With comprehensive error isolation
3. **Add minimal hook points** - Don't modify core logic extensively
4. **Create sample plugins** - Prove the system works
5. **Test error isolation** - Verify plugin failures don't crash core
6. **Validate zero impact** - Ensure disabled plugins have no overhead

**Critical Requirements:**
- **ERROR ISOLATION** - Plugin failures NEVER crash core system
- **OPTIONAL BY DEFAULT** - Plugin system disabled unless explicitly enabled
- **MINIMAL CORE CHANGES** - Add hooks without changing core logic
- **SIMPLE INTERFACES** - Easy for developers to understand and implement

**Lean Architecture Violations to Avoid:**
- ❌ Adding heavy plugin framework dependencies
- ❌ Overly complex plugin interfaces or lifecycle management
- ❌ Modifying core processing logic extensively for plugin integration
- ❌ Creating performance overhead when plugins disabled
- ❌ Adding more than 300 lines total for entire plugin system

**Required Validations:**
```bash
# Test core system unchanged (MOST CRITICAL)
python3 cli.py sample_test.srt test_output.srt
python3 -m pytest tests/ -v

# Test plugin system works
python3 cli.py sample_test.srt test_output.srt --enable-plugins

# Test error isolation
# (create broken plugin and verify core still works)

# Test performance impact
time python3 cli.py large_file.srt output1.srt
time python3 cli.py large_file.srt output2.srt --enable-plugins
```

**Story Status**: ✅ Ready for Implementation (After 5.1-5.6 Complete) 
**Risk Level**: 🔴 HIGH - Implement with maximum caution and testing