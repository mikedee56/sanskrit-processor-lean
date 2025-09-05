#!/usr/bin/env python3
"""
Test Configuration Validation for Sanskrit Processor
Tests the config validator with various valid/invalid configurations.
"""

import os
import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch

from services.config_validator import ConfigValidator, ValidationResult

class TestConfigValidator:
    """Test suite for ConfigValidator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Valid base configuration
        self.valid_config = {
            'processing': {
                'use_iast_diacritics': True,
                'preserve_capitalization': True,
                'fuzzy_matching': {
                    'enabled': True,
                    'threshold': 0.8,
                    'log_matches': False
                }
            },
            'lexicons': {
                'corrections_file': 'corrections.yaml',
                'proper_nouns_file': 'proper_nouns.yaml'
            }
        }
        
        # Create schema file
        self.schema_path = self.test_dir / 'test_schema.yaml'
        schema_content = {
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'type': 'object',
            'properties': {
                'processing': {
                    'type': 'object',
                    'properties': {
                        'use_iast_diacritics': {'type': 'boolean', 'default': True},
                        'preserve_capitalization': {'type': 'boolean', 'default': True},
                        'fuzzy_matching': {
                            'type': 'object',
                            'properties': {
                                'enabled': {'type': 'boolean', 'default': True},
                                'threshold': {'type': 'number', 'minimum': 0.0, 'maximum': 1.0, 'default': 0.8},
                                'log_matches': {'type': 'boolean', 'default': False}
                            },
                            'required': ['enabled']
                        }
                    },
                    'required': ['use_iast_diacritics', 'preserve_capitalization', 'fuzzy_matching']
                },
                'lexicons': {
                    'type': 'object',
                    'properties': {
                        'corrections_file': {'type': 'string', 'default': 'corrections.yaml'},
                        'proper_nouns_file': {'type': 'string', 'default': 'proper_nouns.yaml'}
                    },
                    'required': ['corrections_file', 'proper_nouns_file']
                }
            },
            'required': ['processing', 'lexicons']
        }
        
        with open(self.schema_path, 'w') as f:
            yaml.dump(schema_content, f)
    
    def teardown_method(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_valid_config(self):
        """Test validation of valid configuration."""
        validator = ConfigValidator(self.schema_path)
        result = validator.validate_config(self.valid_config)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.effective_config['processing']['use_iast_diacritics'] is True
        assert result.effective_config['processing']['fuzzy_matching']['threshold'] == 0.8
    
    def test_invalid_threshold(self):
        """Test validation with invalid fuzzy matching threshold."""
        validator = ConfigValidator(self.schema_path)
        invalid_config = self.valid_config.copy()
        invalid_config['processing']['fuzzy_matching']['threshold'] = 1.5  # Invalid: > 1.0
        
        result = validator.validate_config(invalid_config)
        
        assert not result.is_valid
        assert any('threshold' in error and 'must be <=' in error for error in result.errors)
        # Should fall back to default
        assert result.effective_config['processing']['fuzzy_matching']['threshold'] == 0.8
    
    def test_missing_required_field(self):
        """Test validation with missing required field."""
        validator = ConfigValidator(self.schema_path)
        invalid_config = self.valid_config.copy()
        del invalid_config['processing']['fuzzy_matching']['enabled']  # Required field
        
        result = validator.validate_config(invalid_config)
        
        assert not result.is_valid
        assert any('enabled' in error for error in result.errors)
    
    def test_wrong_data_type(self):
        """Test validation with wrong data types."""
        validator = ConfigValidator(self.schema_path)
        invalid_config = self.valid_config.copy()
        invalid_config['processing']['use_iast_diacritics'] = 'yes'  # Should be boolean
        
        result = validator.validate_config(invalid_config)
        
        assert not result.is_valid
        assert any('boolean' in error for error in result.errors)
    
    def test_apply_defaults(self):
        """Test that defaults are applied for missing optional fields."""
        validator = ConfigValidator(self.schema_path)
        minimal_config = {
            'processing': {
                'use_iast_diacritics': True,
                'preserve_capitalization': True,
                'fuzzy_matching': {
                    'enabled': True
                    # Missing threshold and log_matches - should get defaults
                }
            },
            'lexicons': {
                'corrections_file': 'corrections.yaml',
                'proper_nouns_file': 'proper_nouns.yaml'
            }
        }
        
        result = validator.validate_config(minimal_config)
        
        assert result.is_valid
        assert result.effective_config['processing']['fuzzy_matching']['threshold'] == 0.8
        assert result.effective_config['processing']['fuzzy_matching']['log_matches'] is False
    
    def test_environment_config_loading(self):
        """Test environment-specific configuration loading."""
        validator = ConfigValidator(self.schema_path)
        
        # Create base config
        base_config_path = self.test_dir / 'config.yaml'
        with open(base_config_path, 'w') as f:
            yaml.dump(self.valid_config, f)
        
        # Create environment override
        env_config_path = self.test_dir / 'config.dev.yaml'
        env_override = {
            'processing': {
                'fuzzy_matching': {
                    'threshold': 0.7,  # Override
                    'log_matches': True  # Override
                }
            }
        }
        with open(env_config_path, 'w') as f:
            yaml.dump(env_override, f)
        
        # Test environment detection
        with patch.dict(os.environ, {'ENVIRONMENT': 'dev'}):
            config = validator.load_environment_config(base_config_path)
        
        assert config['processing']['fuzzy_matching']['threshold'] == 0.7
        assert config['processing']['fuzzy_matching']['log_matches'] is True
        assert config['processing']['use_iast_diacritics'] is True  # Inherited from base
    
    def test_local_config_override(self):
        """Test local configuration override (config.local.yaml)."""
        validator = ConfigValidator(self.schema_path)
        
        # Create base config
        base_config_path = self.test_dir / 'config.yaml'
        with open(base_config_path, 'w') as f:
            yaml.dump(self.valid_config, f)
        
        # Create local override
        local_config_path = self.test_dir / 'config.local.yaml'
        local_override = {
            'processing': {
                'fuzzy_matching': {
                    'log_matches': True
                }
            }
        }
        with open(local_config_path, 'w') as f:
            yaml.dump(local_override, f)
        
        config = validator.load_environment_config(base_config_path)
        
        assert config['processing']['fuzzy_matching']['log_matches'] is True
        assert config['processing']['fuzzy_matching']['threshold'] == 0.8  # From base
    
    def test_pattern_validation(self):
        """Test pattern validation for file extensions."""
        validator = ConfigValidator(self.schema_path)
        invalid_config = self.valid_config.copy()
        invalid_config['lexicons']['corrections_file'] = 'invalid-file.txt'  # Wrong extension
        
        result = validator.validate_config(invalid_config)
        
        assert not result.is_valid
        assert any('must match pattern' in error for error in result.errors)
        assert any('.yaml or .yml extension' in error for error in result.errors)
    
    def test_validation_metrics(self):
        """Test that validation metrics are generated."""
        validator = ConfigValidator(self.schema_path)
        result = validator.validate_config(self.valid_config)
        
        assert result.is_valid
        assert result.metrics is not None
        assert 'validation_time_ms' in result.metrics
        assert 'schema_compliance' in result.metrics
        assert 'properties_validated' in result.metrics
        assert result.metrics['properties_validated'] > 0
        assert result.metrics['schema_compliance'] is True
    
    def test_schema_not_found(self):
        """Test graceful handling when schema file doesn't exist."""
        validator = ConfigValidator(Path('nonexistent_schema.yaml'))
        result = validator.validate_config(self.valid_config)
        
        # Should still work but with warning
        assert result.is_valid
        assert any('Schema validation disabled' in warning for warning in result.warnings)
    
    def test_invalid_yaml_in_environment_config(self):
        """Test handling of invalid YAML in environment config."""
        validator = ConfigValidator(self.schema_path)
        
        # Create base config
        base_config_path = self.test_dir / 'config.yaml'
        with open(base_config_path, 'w') as f:
            yaml.dump(self.valid_config, f)
        
        # Create invalid environment config
        env_config_path = self.test_dir / 'config.dev.yaml'
        with open(env_config_path, 'w') as f:
            f.write('invalid: yaml: [unclosed')
        
        # Should handle gracefully with warning
        with patch.dict(os.environ, {'ENVIRONMENT': 'dev'}):
            config = validator.load_environment_config(base_config_path)
        
        # Should fall back to base config
        assert config == self.valid_config

class TestCLIValidation:
    """Test CLI validation integration."""
    
    def test_validate_config_command(self):
        """Test CLI config validation command."""
        import subprocess
        import tempfile
        
        # Create temporary valid config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'processing': {
                    'use_iast_diacritics': True,
                    'preserve_capitalization': True,
                    'fuzzy_matching': {
                        'enabled': True,
                        'threshold': 0.8,
                        'log_matches': False
                    }
                },
                'lexicons': {
                    'corrections_file': 'corrections.yaml',
                    'proper_nouns_file': 'proper_nouns.yaml'
                }
            }, f)
            temp_config = f.name
        
        try:
            # Test validation command
            result = subprocess.run([
                'python3', 'cli.py', '--validate-config', '--config', temp_config
            ], capture_output=True, text=True, cwd='/mnt/d/sanskrit-processor-lean')
            
            # Should exit with code 0 for valid config
            assert result.returncode == 0
            assert '✅ Configuration is valid!' in result.stdout
            
        finally:
            os.unlink(temp_config)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])