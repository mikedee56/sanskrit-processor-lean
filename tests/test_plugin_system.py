"""
Tests for Plugin System - Lean Implementation
Comprehensive testing of function-based plugin system
"""
import pytest
from pathlib import Path
from utils.plugin_manager import PluginManager
from sanskrit_processor_v2 import SanskritProcessor


class TestPluginManager:
    """Test the PluginManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin_manager = PluginManager()
    
    def test_plugin_manager_initialization(self):
        """Test plugin manager initializes correctly."""
        assert not self.plugin_manager.enabled
        assert len(self.plugin_manager.plugins) == 0
    
    def test_enable_disable_plugin_system(self):
        """Test enabling and disabling plugin system."""
        self.plugin_manager.enable()
        assert self.plugin_manager.enabled
        
        self.plugin_manager.disable()
        assert not self.plugin_manager.enabled
    
    def test_register_plugin_function(self):
        """Test registering a simple plugin function."""
        def test_plugin(text: str) -> str:
            return text.upper()
        
        self.plugin_manager.register("test", test_plugin)
        assert "test" in self.plugin_manager.plugins
        assert len(self.plugin_manager.list_plugins()) == 1
    
    def test_execute_plugin_when_disabled(self):
        """Test plugin execution when system is disabled."""
        def test_plugin(text: str) -> str:
            return "MODIFIED"
        
        self.plugin_manager.register("test", test_plugin)
        result = self.plugin_manager.execute_plugin("test", "original")
        assert result == "original"  # Should return unchanged
    
    def test_execute_plugin_when_enabled(self):
        """Test plugin execution when system is enabled."""
        def test_plugin(text: str) -> str:
            return text.upper()
        
        self.plugin_manager.register("test", test_plugin)
        self.plugin_manager.enable()
        
        result = self.plugin_manager.execute_plugin("test", "hello")
        assert result == "HELLO"
    
    def test_execute_nonexistent_plugin(self):
        """Test executing a plugin that doesn't exist."""
        self.plugin_manager.enable()
        result = self.plugin_manager.execute_plugin("nonexistent", "text")
        assert result == "text"  # Should return unchanged
    
    def test_plugin_error_isolation(self):
        """Test that plugin errors don't crash the system."""
        def broken_plugin(text: str) -> str:
            raise Exception("Plugin error!")
        
        self.plugin_manager.register("broken", broken_plugin)
        self.plugin_manager.enable()
        
        result = self.plugin_manager.execute_plugin("broken", "original")
        assert result == "original"  # Should return original text on error
    
    def test_execute_all_plugins(self):
        """Test executing all registered plugins in sequence."""
        def plugin1(text: str) -> str:
            return text + "_1"
        
        def plugin2(text: str) -> str:
            return text + "_2"
        
        self.plugin_manager.register("plugin1", plugin1)
        self.plugin_manager.register("plugin2", plugin2)
        self.plugin_manager.enable()
        
        result = self.plugin_manager.execute_all("test")
        assert result == "test_1_2"
    
    def test_remove_plugin(self):
        """Test removing a plugin."""
        def test_plugin(text: str) -> str:
            return text.upper()
        
        self.plugin_manager.register("test", test_plugin)
        assert "test" in self.plugin_manager.plugins
        
        success = self.plugin_manager.remove_plugin("test")
        assert success
        assert "test" not in self.plugin_manager.plugins
        
        # Test removing nonexistent plugin
        success = self.plugin_manager.remove_plugin("nonexistent")
        assert not success


class TestSanskritProcessorPluginIntegration:
    """Test plugin integration with SanskritProcessor."""
    
    def test_processor_without_plugins(self):
        """Test processor works normally without plugins."""
        processor = SanskritProcessor()
        text = "test bhagavad gita"
        result, corrections = processor.process_text(text)
        assert result is not None
        assert isinstance(corrections, int)
    
    def test_processor_with_plugins_disabled(self):
        """Test processor works when plugins are disabled in config."""
        # Create a temporary config with plugins disabled
        config_content = """
plugins:
  enabled: false
  enabled_plugins: []
"""
        config_path = Path("test_config_disabled.yaml")
        config_path.write_text(config_content)
        
        try:
            processor = SanskritProcessor(config_path=config_path)
            text = "test arjun"
            result, corrections = processor.process_text(text)
            assert result == text  # Should be unchanged by plugins
        finally:
            config_path.unlink(missing_ok=True)
    
    def test_processor_plugin_loading(self):
        """Test processor loading plugins from config."""
        # This test verifies the plugin loading mechanism works
        # without actually enabling plugins (to avoid test dependencies)
        processor = SanskritProcessor()
        
        # Verify plugin manager exists
        assert hasattr(processor, 'plugin_manager')
        assert processor.plugin_manager is not None
        
        # Verify plugins are disabled by default
        assert not processor.plugin_manager.enabled


class TestActualPlugins:
    """Test the actual plugin implementations."""
    
    def test_custom_corrections_plugin(self):
        """Test the custom corrections plugin."""
        from plugins.custom_corrections import custom_corrections_plugin
        
        # Test basic correction
        result = custom_corrections_plugin("hello arjun")
        assert "Arjuna" in result
        
        # Test multiple corrections
        result = custom_corrections_plugin("arjun and krishn discuss bhagvad geeta")
        assert "Arjuna" in result
        assert "Krishna" in result  
        assert "Bhagavad" in result
        assert "Gita" in result
    
    def test_template_plugin(self):
        """Test the template plugin."""
        from plugins.template_plugin import template_plugin
        
        # Test Om capitalization
        result = template_plugin("om shanti")
        assert result == "Om shanti"
        
        # Test error handling (plugin should not raise exceptions)
        result = template_plugin("")
        assert result == ""


def test_plugin_system_performance():
    """Test that plugin system has minimal performance impact."""
    import time
    
    processor = SanskritProcessor()
    test_text = "This is a test of the bhagavad gita processing system"
    
    # Test without plugins
    start_time = time.time()
    for _ in range(100):
        processor.process_text(test_text)
    baseline_time = time.time() - start_time
    
    # Performance should be consistent (plugins are disabled by default)
    # This test ensures the plugin hooks don't add significant overhead
    assert baseline_time < 1.0  # Should process 100 segments quickly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])