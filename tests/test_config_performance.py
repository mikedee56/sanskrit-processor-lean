#!/usr/bin/env python3
"""
Performance and edge case tests for ConfigManager.
Tests caching, error handling, and performance characteristics.
"""

import os
import sys
import tempfile
import time
import yaml
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager


def test_configuration_caching():
    """Test that configuration is cached properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        config = {'processing': {'use_iast_diacritics': True}}
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(config, f)
        
        manager = ConfigManager(str(config_dir))
        
        # First load
        start_time = time.time()
        config1 = manager.load_config()
        first_load_time = time.time() - start_time
        
        # Second load (should be cached)
        start_time = time.time()
        config2 = manager.load_config()
        second_load_time = time.time() - start_time
        
        # Should be same object (cached)
        assert config1 is config2, "Configuration should be cached"
        assert second_load_time < first_load_time, "Cached load should be faster"
        
        # Force reload should work
        config3 = manager.load_config(force_reload=True)
        assert config3 is not config2, "Force reload should create new object"
        
    print("✅ Configuration caching")


def test_invalid_yaml_handling():
    """Test handling of invalid YAML files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create invalid YAML
        with open(config_dir / "config.base.yaml", 'w') as f:
            f.write("invalid: yaml: content: [}")
        
        manager = ConfigManager(str(config_dir))
        
        try:
            manager.load_config()
            assert False, "Should have raised ValueError for invalid YAML"
        except ValueError as e:
            assert "Invalid YAML" in str(e)
        
    print("✅ Invalid YAML handling")


def test_missing_required_environment_variables():
    """Test handling of missing required environment variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Ensure the environment variable doesn't exist
        if 'MISSING_REQUIRED_VAR' in os.environ:
            del os.environ['MISSING_REQUIRED_VAR']
        
        config = {
            'services': {
                'api': {'key': '${MISSING_REQUIRED_VAR}'}  # No default value
            }
        }
        
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(config, f)
        
        manager = ConfigManager(str(config_dir))
        
        try:
            manager.load_config()
            assert False, "Should have raised ValueError for missing required env var"
        except ValueError as e:
            assert "Required environment variable not set" in str(e)
            assert "MISSING_REQUIRED_VAR" in str(e)
        
    print("✅ Missing required environment variables")


def test_deep_merge_behavior():
    """Test deep merging behavior with nested dictionaries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Base config with nested structure
        base_config = {
            'services': {
                'api': {'timeout': 10, 'retries': 3},
                'mcp': {'timeout': 30, 'enabled': False}
            },
            'processing': {'use_iast_diacritics': True}
        }
        
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(base_config, f)
        
        # Environment override - should merge deeply
        env_config = {
            'services': {
                'api': {'timeout': 5},  # Should override timeout but keep retries
                'new_service': {'enabled': True}  # Should add new service
            },
            'new_section': {'value': 42}  # Should add new top-level section
        }
        
        with open(config_dir / "config.dev.yaml", 'w') as f:
            yaml.dump(env_config, f)
        
        os.environ['ENVIRONMENT'] = 'dev'
        manager = ConfigManager(str(config_dir))
        result = manager.load_config()
        
        # Check deep merge worked correctly
        assert result['services']['api']['timeout'] == 5  # Overridden
        assert result['services']['api']['retries'] == 3  # Preserved
        assert result['services']['mcp']['timeout'] == 30  # Preserved
        assert result['services']['new_service']['enabled'] == True  # Added
        assert result['processing']['use_iast_diacritics'] == True  # Preserved
        assert result['new_section']['value'] == 42  # Added
        
    print("✅ Deep merge behavior")


def test_complex_environment_variable_patterns():
    """Test complex environment variable substitution patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Set up test environment variables
        os.environ['PREFIX'] = 'test'
        os.environ['SUFFIX'] = 'endpoint'
        os.environ['PORT'] = '8080'
        
        config = {
            'services': {
                'url1': '${PREFIX}_service_${SUFFIX}',  # Multiple vars in one string
                'url2': 'http://localhost:${PORT}/api',  # Embedded in URL
                'url3': '${MISSING:fallback_value}',    # With fallback
                'nested': {
                    'deep': {
                        'value': 'prefix_${PREFIX}_suffix'  # Nested substitution
                    }
                }
            }
        }
        
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(config, f)
        
        manager = ConfigManager(str(config_dir))
        result = manager.load_config()
        
        assert result['services']['url1'] == 'test_service_endpoint'
        assert result['services']['url2'] == 'http://localhost:8080/api'
        assert result['services']['url3'] == 'fallback_value'
        assert result['services']['nested']['deep']['value'] == 'prefix_test_suffix'
        
    print("✅ Complex environment variable patterns")


def test_performance_characteristics():
    """Test performance characteristics with larger configurations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create a reasonably large configuration
        large_config = {
            'processing': {
                f'option_{i}': f'value_{i}' for i in range(100)
            },
            'services': {
                f'service_{i}': {
                    'enabled': i % 2 == 0,
                    'timeout': i * 10,
                    'url': f'http://service{i}.example.com'
                } for i in range(50)
            }
        }
        
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(large_config, f)
        
        manager = ConfigManager(str(config_dir))
        
        # Time the loading
        start_time = time.time()
        config = manager.load_config()
        load_time = time.time() - start_time
        
        # Should load reasonably quickly (< 100ms for this size)
        assert load_time < 0.1, f"Configuration loading took too long: {load_time}s"
        
        # Verify some content loaded correctly
        assert len(config['processing']) == 100
        assert len(config['services']) == 50
        assert config['services']['service_0']['enabled'] == True
        assert config['services']['service_1']['enabled'] == False
        
    print(f"✅ Performance characteristics (loaded in {load_time:.3f}s)")


def run_all_tests():
    """Run all performance and edge case tests."""
    print("🚀 Running ConfigManager Performance & Edge Case Tests")
    print("=" * 60)
    
    tests = [
        test_configuration_caching,
        test_invalid_yaml_handling,
        test_missing_required_environment_variables,
        test_deep_merge_behavior,
        test_complex_environment_variable_patterns,
        test_performance_characteristics
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All performance and edge case tests passed!")
        return True
    else:
        print("⚠️ Some tests failed.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)