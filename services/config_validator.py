#!/usr/bin/env python3
"""
Lightweight Configuration Validator for Sanskrit Processor
Implements schema validation using only PyYAML and stdlib - no external dependencies.
Follows lean architecture principles with <50 lines of core logic.
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    effective_config: Dict[str, Any]
    metrics: Dict[str, Any] = None  # Validation metrics for tracking

class ConfigValidator:
    """Lightweight configuration validator with environment support."""
    
    def __init__(self, schema_path: Path = Path("config.schema.yaml")):
        """Initialize validator with schema."""
        self.schema = self._load_schema(schema_path)
        self.logger = logging.getLogger(__name__)
    
    def _load_schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load schema definition."""
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Schema file not found: {schema_path}. Validation disabled.")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid schema YAML: {e}")
            return {}
    
    def load_environment_config(self, base_config_path: Path) -> Dict[str, Any]:
        """Load config with environment-specific overrides."""
        # Load base configuration
        with open(base_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Check for environment-specific config
        env = os.environ.get('ENVIRONMENT', '').lower()
        env_configs = []
        self._env_applied = False
        
        if env:
            env_configs.append(base_config_path.parent / f"config.{env}.yaml")
        env_configs.append(base_config_path.parent / "config.local.yaml")
        
        # Apply environment overrides
        for env_config_path in env_configs:
            if env_config_path.exists():
                try:
                    with open(env_config_path, 'r', encoding='utf-8') as f:
                        env_config = yaml.safe_load(f)
                    config = self._merge_configs(config, env_config)
                    self._env_applied = True
                    self.logger.info(f"Applied environment config: {env_config_path}")
                except yaml.YAMLError as e:
                    self.logger.warning(f"Invalid environment config {env_config_path}: {e}")
        
        return config
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema with helpful error messages."""
        warnings, errors = [], []
        validation_start = __import__('time').time()
        
        if not self.schema:
            return ValidationResult(True, ["Schema validation disabled"], [], config)
        
        # Apply defaults and validate structure
        effective_config = self._apply_defaults_and_validate(config, self.schema, warnings, errors)
        
        # Generate validation metrics
        validation_time = (__import__('time').time() - validation_start) * 1000  # ms
        metrics = {
            'validation_time_ms': round(validation_time, 2),
            'schema_compliance': len(errors) == 0,
            'warnings_count': len(warnings),
            'errors_count': len(errors),
            'properties_validated': self._count_properties(effective_config),
            'environment_overrides_applied': hasattr(self, '_env_applied') and self._env_applied
        }
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            warnings=warnings,
            errors=errors,
            effective_config=effective_config,
            metrics=metrics
        )
    
    def _apply_defaults_and_validate(self, config: Dict[str, Any], schema: Dict[str, Any], 
                                   warnings: List[str], errors: List[str]) -> Dict[str, Any]:
        """Apply defaults and validate config structure."""
        result = config.copy()
        
        # Check required fields
        required = schema.get('required', [])
        for field in required:
            if field not in config:
                errors.append(f"Missing required field '{field}'. Please add it to your config.yaml")
        
        # Validate properties
        properties = schema.get('properties', {})
        for prop_name, prop_schema in properties.items():
            if prop_name in config:
                result[prop_name] = self._validate_property(
                    config[prop_name], prop_schema, prop_name, warnings, errors
                )
            elif 'default' in prop_schema:
                result[prop_name] = prop_schema['default']
                warnings.append(f"Using default value for '{prop_name}': {prop_schema['default']}")
        
        return result
    
    def _validate_property(self, value: Any, schema: Dict[str, Any], prop_path: str,
                          warnings: List[str], errors: List[str]) -> Any:
        """Validate individual property."""
        prop_type = schema.get('type')
        
        # Type validation
        if prop_type == 'boolean' and not isinstance(value, bool):
            errors.append(f"'{prop_path}' must be boolean (true/false), got {type(value).__name__}")
            return schema.get('default', value)
        elif prop_type == 'number' and not isinstance(value, (int, float)):
            errors.append(f"'{prop_path}' must be a number, got {type(value).__name__}")
            return schema.get('default', value)
        elif prop_type == 'string' and not isinstance(value, str):
            errors.append(f"'{prop_path}' must be a string, got {type(value).__name__}")
            return schema.get('default', value)
        
        # Range validation for numbers
        if prop_type == 'number' and isinstance(value, (int, float)):
            minimum = schema.get('minimum')
            maximum = schema.get('maximum')
            if minimum is not None and value < minimum:
                errors.append(f"'{prop_path}' must be >= {minimum}, got {value}")
                return schema.get('default', minimum)
            if maximum is not None and value > maximum:
                errors.append(f"'{prop_path}' must be <= {maximum}, got {value}")
                return schema.get('default', maximum)
        
        # Pattern validation for strings
        if prop_type == 'string' and isinstance(value, str):
            pattern = schema.get('pattern')
            if pattern and not re.match(pattern, value):
                errors.append(f"'{prop_path}' must match pattern '{pattern}', got '{value}'. Expected format: YAML file with .yaml or .yml extension")
                return schema.get('default', value)
        
        # Object validation (recursive)
        if prop_type == 'object' and isinstance(value, dict):
            return self._apply_defaults_and_validate(value, schema, warnings, errors)
        
        return value
    
    def _count_properties(self, config: Dict[str, Any]) -> int:
        """Count total properties in configuration for metrics."""
        count = 0
        for key, value in config.items():
            count += 1
            if isinstance(value, dict):
                count += self._count_properties(value)
        return count