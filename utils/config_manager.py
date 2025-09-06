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
    
    def _get_config_files_used(self) -> list:
        """Get list of configuration files that were loaded."""
        files_used = []
        
        # Check base config
        base_path = self.config_dir / "config.base.yaml"
        if base_path.exists():
            files_used.append(str(base_path))
        else:
            legacy_path = Path("config.yaml")
            if legacy_path.exists():
                files_used.append(str(legacy_path))
        
        # Check environment config
        env_path = self.config_dir / f"config.{self.environment}.yaml"
        if env_path.exists():
            files_used.append(str(env_path))
            
        return files_used
    
    def _get_env_vars_used(self, config: Dict) -> list:
        """Get list of environment variables used in configuration."""
        env_vars = []
        
        def find_env_vars(value):
            if isinstance(value, str):
                pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
                matches = re.findall(pattern, value)
                for match in matches:
                    env_vars.append(match[0])
            elif isinstance(value, dict):
                for v in value.values():
                    find_env_vars(v)
            elif isinstance(value, list):
                for item in value:
                    find_env_vars(item)
        
        find_env_vars(config)
        return list(set(env_vars))  # Remove duplicates