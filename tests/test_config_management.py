#!/usr/bin/env python3
"""
Comprehensive test suite for advanced configuration management.
Tests ConfigManager, environment inheritance, and variable substitution.

Usage: python3 tests/test_config_management.py  # Standalone runner
       python3 -m pytest tests/test_config_management.py  # With pytest
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add project root to path for standalone execution
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

from utils.config_manager import ConfigManager

class TestConfigManager:
    """Test suite for ConfigManager functionality."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.test_dir / "config"
        self.config_dir.mkdir()
        
        # Set required environment variables for tests
        os.environ['API_KEY'] = 'test_key_12345'
        os.environ['API_BASE_URL'] = 'http://test.example.com'
        
        # Create base configuration
        self.base_config = {
            'processing': {
                'use_iast_diacritics': True,
                'fuzzy_matching': {
                    'enabled': True,
                    'threshold': 0.8,
                    'log_matches': False
                }
            },
            'services': {
                'api': {
                    'base_url': '${API_BASE_URL:http://localhost:8080}',
                    'api_key': '${API_KEY}',
                    'timeout': 10
                }
            },
            'logging': {
                'level': 'INFO'
            }
        }
        
        with open(self.config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(self.base_config, f)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir)
        
        # Clean up environment variables
        test_vars = ['ENVIRONMENT', 'API_KEY', 'API_BASE_URL', 'TEST_VAR']
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_environment_detection_default(self):
        """Test default environment detection."""
        manager = ConfigManager(str(self.config_dir))
        assert manager.environment == "dev"
    
    def test_environment_detection_custom(self):
        """Test custom environment detection."""
        os.environ['ENVIRONMENT'] = 'prod'
        manager = ConfigManager(str(self.config_dir))
        assert manager.environment == "prod"
    
    def test_base_configuration_loading(self):
        """Test loading base configuration only."""
        manager = ConfigManager(str(self.config_dir))
        config = manager.load_config()
        
        # Should have base config values
        assert config['processing']['use_iast_diacritics'] == True
        assert config['processing']['fuzzy_matching']['threshold'] == 0.8
        assert config['services']['api']['timeout'] == 10
    
    def test_environment_override(self):
        """Test environment-specific configuration override."""
        # Create development override
        dev_override = {
            'processing': {
                'fuzzy_matching': {
                    'log_matches': True,  # Override
                    'threshold': 0.7      # Override
                }
            },
            'logging': {
                'level': 'DEBUG'  # Override
            },
            'development_only': {
                'debug_mode': True  # New config
            }
        }
        
        with open(self.config_dir / "config.dev.yaml", 'w') as f:
            yaml.dump(dev_override, f)
        
        os.environ['ENVIRONMENT'] = 'dev'
        manager = ConfigManager(str(self.config_dir))
        config = manager.load_config()
        
        # Should have base values
        assert config['processing']['use_iast_diacritics'] == True
        assert config['services']['api']['timeout'] == 10
        
        # Should have overridden values
        assert config['processing']['fuzzy_matching']['log_matches'] == True
        assert config['processing']['fuzzy_matching']['threshold'] == 0.7
        assert config['logging']['level'] == 'DEBUG'
        
        # Should have new environment-specific config
        assert config['development_only']['debug_mode'] == True
    
    def test_deep_merge_nested_objects(self):
        """Test deep merging of nested configuration objects."""
        # Create a complex override
        override = {
            'services': {
                'api': {
                    'timeout': 20,  # Override existing
                    'retries': 3    # Add new
                },
                'mcp': {        # Add new service
                    'enabled': True,
                    'timeout': 30
                }
            }
        }
        
        with open(self.config_dir / "config.dev.yaml", 'w') as f:
            yaml.dump(override, f)
        
        manager = ConfigManager(str(self.config_dir))
        config = manager.load_config()
        
        # Original api config should be preserved and extended
        assert config['services']['api']['base_url'] == 'http://localhost:8080'  # From base
        assert config['services']['api']['timeout'] == 20  # Overridden
        assert config['services']['api']['retries'] == 3   # Added
        
        # New service should be added
        assert config['services']['mcp']['enabled'] == True
        assert config['services']['mcp']['timeout'] == 30
    
    def test_environment_variable_substitution_with_values(self):
        """Test environment variable substitution when variables are set."""
        os.environ['API_KEY'] = 'test_key_123'
        os.environ['API_BASE_URL'] = 'https://api.example.com'
        
        manager = ConfigManager(str(self.config_dir))
        config = manager.load_config()
        
        assert config['services']['api']['api_key'] == 'test_key_123'
        assert config['services']['api']['base_url'] == 'https://api.example.com'
    
    def test_environment_variable_substitution_with_defaults(self):
        """Test environment variable substitution using default values."""
        # Don't set API_BASE_URL, should use default
        # Don't set API_KEY, should raise error since no default
        
        # Remove API_KEY to test error handling
        if 'API_KEY' in os.environ:
            del os.environ['API_KEY']
        
        manager = ConfigManager(str(self.config_dir))
        
        try:
            manager.load_config()
            assert False, "Should have raised ValueError for missing API_KEY"
        except ValueError as e:
            assert "Required environment variable not set: API_KEY" in str(e)
        finally:
            # Restore for other tests
            os.environ['API_KEY'] = 'test_key_12345'
    
    def test_environment_variable_substitution_defaults_used(self):
        """Test that default values are used when environment variables not set."""
        # Remove API_KEY requirement for this test
        base_config_no_required = self.base_config.copy()
        base_config_no_required['services']['api']['api_key'] = '${API_KEY:default_key}'
        
        with open(self.config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(base_config_no_required, f)
        
        manager = ConfigManager(str(self.config_dir))
        config = manager.load_config()
        
        # Should use defaults
        assert config['services']['api']['base_url'] == 'http://localhost:8080'
        assert config['services']['api']['api_key'] == 'default_key'
    
    def test_complex_environment_variable_patterns(self):
        """Test complex environment variable substitution patterns."""
        complex_config = {
            'database': {
                'url': '${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME:testdb}',
                'credentials': '${DB_USER:admin}:${DB_PASS:secret}'
            },
            'mixed': {
                'path': '/data/${APP_ENV:development}/files',
                'full_url': 'https://${DOMAIN:example.com}/api/v${VERSION:1}'
            }
        }
        
        with open(self.config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(complex_config, f)
        
        # Set some environment variables
        os.environ['DB_HOST'] = 'prod-db'
        os.environ['VERSION'] = '2'
        
        manager = ConfigManager(str(self.config_dir))
        config = manager.load_config()
        
        # Should substitute set variables and use defaults for others
        assert config['database']['url'] == 'prod-db:5432/testdb'
        assert config['database']['credentials'] == 'admin:secret'
        assert config['mixed']['path'] == '/data/development/files'
        assert config['mixed']['full_url'] == 'https://example.com/api/v2'
    
    def test_config_caching(self):
        """Test configuration caching functionality."""
        manager = ConfigManager(str(self.config_dir))
        
        # Load config twice
        config1 = manager.load_config()
        config2 = manager.load_config()
        
        # Should be the same object (cached)
        assert config1 is config2
        
        # Force reload should create new object
        config3 = manager.load_config(force_reload=True)
        assert config1 is not config3
        assert config1 == config3  # Same content, different objects
    
    def test_validation_success(self):
        """Test configuration validation with valid config."""
        os.environ['API_KEY'] = 'test_key'
        
        manager = ConfigManager(str(self.config_dir))
        report = manager.validate_config()
        
        assert report['valid'] == True
        assert report['environment'] == 'dev'
        assert len(report['config_files_used']) >= 1
        assert 'API_KEY' in report['env_vars_substituted']
    
    def test_validation_failure(self):
        """Test configuration validation with missing required env vars."""
        manager = ConfigManager(str(self.config_dir))
        report = manager.validate_config()
        
        assert report['valid'] == False
        assert 'Required environment variable not set: API_KEY' in report['error']
        assert report['environment'] == 'dev'
    
    def test_legacy_config_fallback(self):
        """Test fallback to legacy config.yaml when base config doesn't exist."""
        # Remove base config
        (self.config_dir / "config.base.yaml").unlink()
        
        # Create legacy config.yaml
        legacy_config = {
            'processing': {
                'legacy_mode': True,
                'threshold': 0.9
            }
        }
        
        legacy_path = self.test_dir / "config.yaml"
        with open(legacy_path, 'w') as f:
            yaml.dump(legacy_config, f)
        
        # ConfigManager should find and use legacy config
        manager = ConfigManager(str(self.config_dir))
        # Temporarily change working directory for legacy fallback
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        try:
            config = manager.load_config()
            assert config['processing']['legacy_mode'] == True
            assert config['processing']['threshold'] == 0.9
        finally:
            os.chdir(original_cwd)
    
    def test_no_environment_config_okay(self):
        """Test that missing environment-specific config is handled gracefully."""
        os.environ['ENVIRONMENT'] = 'staging'
        os.environ['API_KEY'] = 'test_key'
        
        # No config.staging.yaml file exists
        manager = ConfigManager(str(self.config_dir))
        config = manager.load_config()
        
        # Should load base config successfully
        assert config['processing']['use_iast_diacritics'] == True
        assert config['services']['api']['api_key'] == 'test_key'
    
    def test_config_files_used_reporting(self):
        """Test reporting of which configuration files were used."""
        # Create environment config
        with open(self.config_dir / "config.dev.yaml", 'w') as f:
            yaml.dump({'test': 'value'}, f)
        
        os.environ['API_KEY'] = 'test_key'
        manager = ConfigManager(str(self.config_dir))
        manager.load_config()
        
        files_used = manager._get_config_files_used()
        assert len(files_used) == 2
        assert any('config.base.yaml' in f for f in files_used)
        assert any('config.dev.yaml' in f for f in files_used)
    
    def test_env_vars_used_reporting(self):
        """Test reporting of environment variables found in config."""
        config_with_vars = {
            'service1': {'key': '${VAR1}'},
            'service2': {'url': '${VAR2:default}', 'token': '${VAR3}'},
            'nested': {'deep': {'value': '${VAR4:another_default}'}}
        }
        
        manager = ConfigManager(str(self.config_dir))
        env_vars = manager._get_env_vars_used(config_with_vars)
        
        expected_vars = {'VAR1', 'VAR2', 'VAR3', 'VAR4'}
        assert set(env_vars) == expected_vars


class TestConfigurationIntegration:
    """Integration tests for configuration management with processors."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.test_dir / "config"
        self.config_dir.mkdir()
        
        # Create realistic configuration
        base_config = {
            'processing': {
                'use_iast_diacritics': True,
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            },
            'services': {'api': {'timeout': 10}},
            'plugins': {'enabled': False}
        }
        
        with open(self.config_dir / "config.base.yaml", 'w') as f:
            yaml.dump(base_config, f)
    
    def teardown_method(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.test_dir)
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
    
    def test_processor_loads_advanced_config(self):
        """Test that processors can load advanced configuration."""
        from sanskrit_processor_v2 import SanskritProcessor
        
        # Change to test directory for config loading
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        try:
            processor = SanskritProcessor(lexicon_dir=Path("lexicons"))
            config = processor.config
            
            # Should have loaded advanced configuration
            assert config['processing']['use_iast_diacritics'] == True
            assert config['processing']['fuzzy_matching']['threshold'] == 0.8
            
        except ImportError:
            # ConfigManager not found in path, which is expected in test
            if HAS_PYTEST:
                pytest.skip("Integration test requires full project structure")
            else:
                return  # Skip test in standalone mode
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    """Standalone test runner for environments without pytest."""
    if HAS_PYTEST:
        pytest.main([__file__, "-v"])
    else:
        # Manual test runner
        print("🧪 Running ConfigManager Test Suite")
        print("=" * 50)
        
        test_class = TestConfigManager()
        integration_class = TestConfigurationIntegration()
        
        # Get all test methods
        test_methods = [
            (test_class, 'test_environment_detection_default'),
            (test_class, 'test_environment_detection_custom'),
            (test_class, 'test_base_configuration_loading'),
            (test_class, 'test_environment_override'),
            (test_class, 'test_deep_merge_nested_objects'),
            (test_class, 'test_environment_variable_substitution_with_values'),
            (test_class, 'test_environment_variable_substitution_with_defaults'),
            (test_class, 'test_environment_variable_substitution_defaults_used'),
            (test_class, 'test_complex_environment_variable_patterns'),
            (test_class, 'test_config_caching'),
            (test_class, 'test_validation_success'),
            (test_class, 'test_validation_failure'),
            (test_class, 'test_legacy_config_fallback'),
            (test_class, 'test_no_environment_config_okay'),
            (test_class, 'test_config_files_used_reporting'),
            (test_class, 'test_env_vars_used_reporting'),
            (integration_class, 'test_processor_loads_advanced_config')
        ]
        
        passed = 0
        failed = 0
        
        for test_instance, test_name in test_methods:
            try:
                test_instance.setup_method()
                test_method = getattr(test_instance, test_name)
                test_method()
                test_instance.teardown_method()
                print(f"✅ {test_name}")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name}: {str(e)[:100]}")
                failed += 1
                try:
                    test_instance.teardown_method()
                except:
                    pass
        
        print("\n" + "=" * 50)
        print(f"📊 Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Configuration management is working perfectly.")
            sys.exit(0)
        else:
            print("⚠️  Some tests failed. Check implementation.")
            sys.exit(1)