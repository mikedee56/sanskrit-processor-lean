#!/usr/bin/env python3
"""
Integration tests for ConfigManager - Simple, robust tests that work without pytest.
Focuses on the core functionality that needs to work in production.
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager


def test_environment_detection():
    """Test basic environment detection."""
    # Test default
    if 'ENVIRONMENT' in os.environ:
        del os.environ['ENVIRONMENT']
    manager = ConfigManager()
    assert manager.environment == 'dev', f"Expected 'dev', got '{manager.environment}'"
    
    # Test custom
    os.environ['ENVIRONMENT'] = 'prod'
    manager = ConfigManager()
    assert manager.environment == 'prod', f"Expected 'prod', got '{manager.environment}'"
    print("✅ Environment detection")


def test_configuration_loading():
    """Test configuration loading with inheritance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Base config
        base_config = {
            'processing': {'use_iast_diacritics': True, 'threshold': 0.8},
            'logging': {'level': 'INFO'}
        }
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(base_config, f)
        
        # Environment override
        env_config = {
            'logging': {'level': 'DEBUG'},
            'environment': {'name': 'development'}
        }
        with open(config_dir / "config.dev.yaml", 'w') as f:
            yaml.dump(env_config, f)
        
        os.environ['ENVIRONMENT'] = 'dev'
        manager = ConfigManager(str(config_dir))
        config = manager.load_config()
        
        # Check base values preserved
        assert config['processing']['use_iast_diacritics'] == True
        assert config['processing']['threshold'] == 0.8
        
        # Check override applied
        assert config['logging']['level'] == 'DEBUG'
        assert config['environment']['name'] == 'development'
        
    print("✅ Configuration loading and inheritance")


def test_environment_variable_substitution():
    """Test environment variable substitution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Set test environment variables
        os.environ['TEST_API_KEY'] = 'secret123'
        os.environ['TEST_URL'] = 'https://example.com'
        
        config = {
            'services': {
                'api': {
                    'key': '${TEST_API_KEY}',
                    'url': '${TEST_URL}',
                    'fallback': '${MISSING_VAR:default_value}'
                }
            }
        }
        
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(config, f)
        
        manager = ConfigManager(str(config_dir))
        result = manager.load_config()
        
        assert result['services']['api']['key'] == 'secret123'
        assert result['services']['api']['url'] == 'https://example.com'
        assert result['services']['api']['fallback'] == 'default_value'
        
    print("✅ Environment variable substitution")


def test_backward_compatibility():
    """Test fallback to legacy config.yaml."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create legacy config.yaml (not in config/ subdirectory)
        legacy_config = {
            'processing': {'use_iast_diacritics': False},
            'legacy': {'enabled': True}
        }
        
        legacy_path = Path(temp_dir) / "config.yaml"
        with open(legacy_path, 'w') as f:
            yaml.dump(legacy_config, f)
        
        # Change to temp directory so ConfigManager finds config.yaml
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Use non-existent config dir to force fallback
            manager = ConfigManager('nonexistent_config')
            config = manager.load_config()
            
            assert config['processing']['use_iast_diacritics'] == False
            assert config['legacy']['enabled'] == True
            
        finally:
            os.chdir(original_cwd)
    
    print("✅ Backward compatibility")


def test_validation():
    """Test configuration validation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        config = {'processing': {'use_iast_diacritics': True}}
        with open(config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(config, f)
        
        manager = ConfigManager(str(config_dir))
        validation = manager.validate_config()
        
        assert validation['valid'] == True
        assert 'environment' in validation
        assert 'config_files_used' in validation
        
    print("✅ Configuration validation")


def run_all_tests():
    """Run all integration tests."""
    print("🧪 Running ConfigManager Integration Tests")
    print("=" * 50)
    
    tests = [
        test_environment_detection,
        test_configuration_loading,
        test_environment_variable_substitution,
        test_backward_compatibility,
        test_validation
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
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("⚠️ Some tests failed.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)