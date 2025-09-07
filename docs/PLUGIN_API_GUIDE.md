# Plugin API Development Guide

**Sanskrit Processor Lean Architecture - Plugin System**

Version: 1.0  
Last Updated: September 2024

## Overview

The Sanskrit Processor provides a lightweight, focused plugin architecture for extending core functionality without compromising the lean design philosophy. Plugins are Python modules that integrate seamlessly with the processing pipeline while maintaining system performance and reliability.

## Architecture Philosophy

### Core Principles
- **Lean by Design**: Plugins are optional enhancements, not requirements
- **Fail-Fast**: Plugin errors don't compromise core processing
- **Configuration-Driven**: All plugin behavior controlled via YAML
- **Performance Aware**: Plugins respect system performance constraints
- **Hot-Pluggable**: Enable/disable plugins without code changes

### Plugin Lifecycle
1. **Discovery**: Plugin modules auto-discovered in `plugins/` directory
2. **Registration**: Plugins register processing hooks during initialization
3. **Configuration**: Plugin settings loaded from `config.yaml`
4. **Execution**: Plugin methods called at designated processing stages
5. **Error Handling**: Plugin failures isolated from core processor

## Plugin API Reference

### Base Plugin Interface

All plugins must inherit from the `BasePlugin` class:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

class BasePlugin(ABC):
    """Base class for all Sanskrit Processor plugins."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize plugin with configuration."""
        self.config = config
        self.enabled = config.get('enabled', True)
        self.name = self.__class__.__name__
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, str]:
        """Return plugin metadata."""
        return {
            'name': 'PluginName',
            'version': '1.0.0',
            'description': 'Plugin description',
            'author': 'Author Name'
        }
    
    def pre_process_text(self, text: str, context: Dict[str, Any]) -> str:
        """Called before core processing. Override to implement."""
        return text
    
    def post_process_text(self, text: str, context: Dict[str, Any]) -> str:
        """Called after core processing. Override to implement."""
        return text
    
    def enhance_corrections(self, corrections: Dict[str, str]) -> Dict[str, str]:
        """Enhance lexicon corrections. Override to implement."""
        return corrections
    
    def validate_result(self, original: str, processed: str) -> Tuple[bool, str]:
        """Validate processing result. Return (is_valid, message)."""
        return True, "OK"
    
    def cleanup(self):
        """Cleanup plugin resources. Override if needed."""
        pass
```

### Processing Hook Points

Plugins can hook into these processing stages:

#### 1. Pre-Processing Hook
```python
def pre_process_text(self, text: str, context: Dict[str, Any]) -> str:
    """
    Called before any core processing.
    
    Args:
        text: Original segment text
        context: Processing context including:
            - segment_index: Current segment number
            - timestamp_start: Segment start time
            - timestamp_end: Segment end time
            - file_path: Source file path
    
    Returns:
        Modified text or original text
    """
```

#### 2. Post-Processing Hook
```python
def post_process_text(self, text: str, context: Dict[str, Any]) -> str:
    """
    Called after core processing complete.
    
    Args:
        text: Processed segment text
        context: Processing context plus:
            - corrections_applied: Number of corrections made
            - processing_time: Time taken for core processing
    
    Returns:
        Final processed text
    """
```

#### 3. Lexicon Enhancement Hook
```python
def enhance_corrections(self, corrections: Dict[str, str]) -> Dict[str, str]:
    """
    Enhance or modify lexicon corrections.
    
    Args:
        corrections: Current correction mappings
    
    Returns:
        Enhanced correction mappings
    """
```

#### 4. Validation Hook
```python
def validate_result(self, original: str, processed: str) -> Tuple[bool, str]:
    """
    Validate processing results.
    
    Args:
        original: Original text
        processed: Processed text
    
    Returns:
        Tuple of (is_valid, validation_message)
    """
```

## Plugin Development Tutorial

### Step 1: Create Plugin Structure

Create your plugin directory:
```bash
mkdir plugins/my_custom_plugin
cd plugins/my_custom_plugin
```

Create the main plugin file:
```python
# plugins/my_custom_plugin/plugin.py
import re
from typing import Dict, Any, Tuple
from utils.plugin_manager import BasePlugin

class MyCustomPlugin(BasePlugin):
    """Example custom correction plugin."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.custom_corrections = config.get('custom_corrections', {})
        self.strict_mode = config.get('strict_mode', False)
    
    def get_plugin_info(self) -> Dict[str, str]:
        return {
            'name': 'MyCustomPlugin',
            'version': '1.0.0',
            'description': 'Custom corrections for specific terminology',
            'author': 'Your Name'
        }
    
    def pre_process_text(self, text: str, context: Dict[str, Any]) -> str:
        """Apply custom preprocessing."""
        # Example: normalize specific patterns
        text = re.sub(r'\b(om|aum)\b', 'Om', text, flags=re.IGNORECASE)
        return text
    
    def enhance_corrections(self, corrections: Dict[str, str]) -> Dict[str, str]:
        """Add custom corrections to lexicon."""
        enhanced = corrections.copy()
        enhanced.update(self.custom_corrections)
        return enhanced
    
    def validate_result(self, original: str, processed: str) -> Tuple[bool, str]:
        """Validate results in strict mode."""
        if not self.strict_mode:
            return True, "OK"
        
        # Example validation: ensure Sanskrit terms are capitalized
        sanskrit_terms = ['Krishna', 'Shiva', 'Brahman', 'Dharma']
        for term in sanskrit_terms:
            if term.lower() in processed.lower() and term not in processed:
                return False, f"Sanskrit term '{term}' should be capitalized"
        
        return True, "Validation passed"
```

### Step 2: Configure Plugin

Add plugin configuration to `config.yaml`:
```yaml
plugins:
  enabled: true
  enabled_plugins:
    - my_custom_plugin
  
  # Plugin-specific configuration
  my_custom_plugin:
    enabled: true
    strict_mode: true
    custom_corrections:
      "yogic": "Yogic"
      "vedantic": "Vedantic"
      "upanishadic": "Upanishadic"
```

### Step 3: Test Plugin

Create a test file:
```python
# plugins/my_custom_plugin/test_plugin.py
import pytest
from .plugin import MyCustomPlugin

def test_plugin_initialization():
    config = {
        'enabled': True,
        'strict_mode': False,
        'custom_corrections': {'test': 'Test'}
    }
    
    plugin = MyCustomPlugin(config)
    assert plugin.enabled == True
    assert plugin.strict_mode == False
    assert 'test' in plugin.custom_corrections

def test_pre_processing():
    plugin = MyCustomPlugin({})
    
    result = plugin.pre_process_text("om namah shivaya", {})
    assert result == "Om namah shivaya"

def test_correction_enhancement():
    plugin = MyCustomPlugin({
        'custom_corrections': {'guru': 'Guru'}
    })
    
    base_corrections = {'om': 'Om'}
    enhanced = plugin.enhance_corrections(base_corrections)
    
    assert 'om' in enhanced
    assert 'guru' in enhanced
    assert enhanced['guru'] == 'Guru'

def test_validation():
    plugin = MyCustomPlugin({'strict_mode': True})
    
    # Should pass validation
    is_valid, msg = plugin.validate_result("krishna", "Krishna")
    assert is_valid == True
    
    # Should fail validation in strict mode
    is_valid, msg = plugin.validate_result("krishna", "krishna")  
    assert is_valid == False
    assert "Krishna" in msg
```

## Advanced Plugin Features

### Performance Monitoring
```python
def post_process_text(self, text: str, context: Dict[str, Any]) -> str:
    import time
    start_time = time.time()
    
    # Your processing logic
    result = self._custom_processing(text)
    
    processing_time = time.time() - start_time
    if processing_time > 0.1:  # Log slow operations
        logger.warning(f"Plugin {self.name} took {processing_time:.3f}s")
    
    return result
```

### Context-Aware Processing
```python
def pre_process_text(self, text: str, context: Dict[str, Any]) -> str:
    # Access segment metadata
    segment_index = context.get('segment_index', 0)
    file_path = context.get('file_path', '')
    
    # Different processing for different contexts
    if 'lecture' in file_path.lower():
        return self._lecture_preprocessing(text)
    elif segment_index == 0:  # First segment
        return self._title_preprocessing(text)
    else:
        return text
```

### Error Handling and Logging
```python
import logging

class SafePlugin(BasePlugin):
    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger(f"plugin.{self.name}")
    
    def post_process_text(self, text: str, context: Dict[str, Any]) -> str:
        try:
            return self._risky_processing(text)
        except Exception as e:
            self.logger.error(f"Plugin processing failed: {e}")
            return text  # Return original on error
    
    def _risky_processing(self, text: str) -> str:
        # Processing that might fail
        pass
```

## Plugin Configuration Reference

### Basic Configuration
```yaml
plugins:
  enabled: true                    # Master plugin switch
  auto_discover: false            # Manual configuration only
  enabled_plugins:                # List of enabled plugins
    - custom_corrections
    - sanskrit_validator
    - performance_monitor
```

### Plugin-Specific Settings
```yaml
plugins:
  # Plugin configurations
  custom_corrections:
    enabled: true
    strict_mode: false
    correction_file: "data/custom_corrections.yaml"
    
  sanskrit_validator:
    enabled: true
    validation_level: "strict"    # strict, moderate, lenient
    ignore_proper_nouns: false
    
  performance_monitor:
    enabled: false                # Disabled by default
    threshold_ms: 100            # Log operations > 100ms
    detailed_logging: false
```

### Environment-Specific Configuration
```yaml
# config.dev.yaml
plugins:
  enabled: true
  performance_monitor:
    enabled: true
    detailed_logging: true

# config.prod.yaml  
plugins:
  enabled: true
  performance_monitor:
    enabled: false              # Disabled in production
```

## Best Practices

### 1. Performance Guidelines
- **Measure Everything**: Use profiling to measure plugin performance
- **Fail Fast**: Return quickly if plugin isn't needed for current text
- **Cache Results**: Cache expensive computations when possible
- **Respect Limits**: Stay under 10ms per segment for real-time processing

### 2. Error Handling
- **Graceful Degradation**: Always return valid output, even on errors
- **Comprehensive Logging**: Log errors with context for debugging
- **Configuration Validation**: Validate plugin config during initialization
- **Resource Cleanup**: Implement proper cleanup in `cleanup()` method

### 3. Testing Strategy
- **Unit Tests**: Test each plugin method independently
- **Integration Tests**: Test with real Sanskrit text samples
- **Performance Tests**: Measure impact on processing speed
- **Error Tests**: Test failure scenarios and recovery

### 4. Configuration Management
- **Sensible Defaults**: Plugins should work with minimal configuration
- **Environment Awareness**: Support dev/test/prod configurations
- **Validation**: Validate configuration values during startup
- **Documentation**: Document all configuration options

## Plugin Examples

### Example 1: Scripture Reference Detector
```python
class ScriptureReferencePlugin(BasePlugin):
    """Detects and formats scripture references."""
    
    def __init__(self, config):
        super().__init__(config)
        self.reference_patterns = [
            r'\b(Bhagavad Gita|BG)\s+(\d+)\.(\d+)',
            r'\b(Srimad Bhagavatam|SB)\s+(\d+)\.(\d+)\.(\d+)'
        ]
    
    def post_process_text(self, text: str, context: Dict[str, Any]) -> str:
        for pattern in self.reference_patterns:
            text = re.sub(pattern, self._format_reference, text)
        return text
    
    def _format_reference(self, match):
        # Format scripture references consistently
        return f"[{match.group(0)}]"
```

### Example 2: Pronunciation Guide Plugin
```python
class PronunciationPlugin(BasePlugin):
    """Adds pronunciation guides for Sanskrit terms."""
    
    def post_process_text(self, text: str, context: Dict[str, Any]) -> str:
        if not self.config.get('add_pronunciation', False):
            return text
            
        pronunciations = self.config.get('pronunciation_guide', {})
        
        for term, pronunciation in pronunciations.items():
            pattern = rf'\b{re.escape(term)}\b'
            replacement = f"{term} [{pronunciation}]"
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
```

## Plugin Deployment

### Development Workflow
1. Create plugin in `plugins/plugin_name/`
2. Add configuration to `config.yaml`
3. Run tests: `pytest plugins/plugin_name/`
4. Test integration: `python cli.py sample_test.srt output.srt --verbose`
5. Monitor performance and adjust as needed

### Production Deployment
1. Test plugin thoroughly in development environment
2. Update production configuration with plugin settings
3. Deploy plugin files to production server
4. Enable plugin in production config
5. Monitor system performance after deployment

## Troubleshooting

### Common Issues

**Plugin Not Loading**
- Check plugin is in `plugins/` directory
- Verify plugin name in `enabled_plugins` list
- Check for syntax errors in plugin code

**Performance Issues**
- Profile plugin methods to find bottlenecks
- Check if plugin is being called unnecessarily
- Consider caching expensive operations

**Configuration Errors**
- Validate configuration schema
- Check for typos in config keys
- Ensure required configuration values are present

### Debug Mode
Enable plugin debugging:
```yaml
plugins:
  debug_mode: true              # Enable detailed plugin logging
  performance_tracking: true   # Track plugin performance
```

## Plugin Registry

### Available Plugins
- **custom_corrections**: Custom term corrections and variations
- **sanskrit_validator**: Validates Sanskrit term formatting
- **performance_monitor**: Tracks and logs plugin performance
- **scripture_references**: Formats scripture references consistently

### Community Plugins
Visit the project wiki for community-contributed plugins and examples.

---

*This guide covers the core plugin development concepts. For advanced use cases or specific implementation questions, refer to the source code in `utils/plugin_manager.py` or create an issue on GitHub.*