#!/usr/bin/env python3
# tools/migrate_config.py
"""
Configuration migration utility for Sanskrit Processor.
Converts existing config.yaml to new environment-based structure.
"""

import sys
import os
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def migrate_config(source_config: Dict[str, Any], target_dir: str) -> Dict[str, Any]:
    """
    Migrate a configuration dictionary to new structure.
    
    Args:
        source_config: The original configuration dictionary
        target_dir: Target directory for new configuration files
        
    Returns:
        Migration result with status and details
    """
    try:
        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True)
        
        # Create base configuration
        base_config_path = target_path / "config.base.yaml"
        with open(base_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(source_config, f, default_flow_style=False, indent=2)
        
        # Create minimal environment-specific overrides
        dev_overrides = {
            'logging': {'level': 'DEBUG'},
            'environment': {'name': 'development', 'debug': True}
        }
        
        prod_overrides = {
            'logging': {'level': 'WARNING', 'json_output': True},
            'environment': {'name': 'production', 'debug': False}
        }
        
        # Write environment configs
        with open(target_path / "config.dev.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(dev_overrides, f, default_flow_style=False, indent=2)
            
        with open(target_path / "config.prod.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(prod_overrides, f, default_flow_style=False, indent=2)
            
        return {
            'success': True,
            'files_created': [
                str(base_config_path),
                str(target_path / "config.dev.yaml"),
                str(target_path / "config.prod.yaml")
            ],
            'message': 'Configuration migration completed successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Configuration migration failed: {e}'
        }

def backup_original_config(config_path: Path) -> Path:
    """Create a backup of the original configuration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"{config_path.stem}_backup_{timestamp}{config_path.suffix}"
    shutil.copy2(config_path, backup_path)
    return backup_path

def main():
    """Main migration command-line interface."""
    if len(sys.argv) != 3:
        print("Usage: python3 tools/migrate_config.py <source_config.yaml> <target_dir>")
        print("Example: python3 tools/migrate_config.py config.yaml config/")
        sys.exit(1)
    
    source_path = Path(sys.argv[1])
    target_dir = sys.argv[2]
    
    if not source_path.exists():
        print(f"Error: Source configuration file not found: {source_path}")
        sys.exit(1)
    
    try:
        # Load source configuration
        with open(source_path, 'r', encoding='utf-8') as f:
            source_config = yaml.safe_load(f)
        
        if source_config is None:
            print(f"Error: Source configuration file is empty: {source_path}")
            sys.exit(1)
        
        # Create backup
        backup_path = backup_original_config(source_path)
        print(f"Backup created: {backup_path}")
        
        # Perform migration
        result = migrate_config(source_config, target_dir)
        
        if result['success']:
            print("✅ Configuration migration completed successfully!")
            print(f"Files created:")
            for file_path in result['files_created']:
                print(f"  - {file_path}")
            print(f"\nOriginal configuration backed up to: {backup_path}")
            print(f"You can now use ENVIRONMENT=dev|staging|prod to select configurations")
        else:
            print(f"❌ Migration failed: {result['message']}")
            sys.exit(1)
            
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in source file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()