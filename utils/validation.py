#!/usr/bin/env python3
"""
Input Validation Framework for Sanskrit Processor
Prevents type errors and ensures data integrity
"""

import logging
import time
from typing import Any, Dict, List, Union, Optional
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass

class InputValidator:
    """Comprehensive input validation for Sanskrit processor."""
    
    @staticmethod
    def validate_database_entry(entry: Any, entry_key: str, source: str = "unknown") -> bool:
        """
        Validate database entry structure to prevent type errors.
        
        Args:
            entry: Database entry to validate
            entry_key: Key/identifier for the entry
            source: Source of the entry (corrections, proper_nouns, etc.)
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If entry is critically malformed
        """
        try:
            # Check basic type
            if not isinstance(entry, (dict, str)):
                logger.error(f"Invalid entry type for '{entry_key}' in {source}: {type(entry)} (expected dict or str)")
                return False
            
            # If string, it's a simple mapping - valid
            if isinstance(entry, str):
                return True
            
            # If dict, validate required fields
            if isinstance(entry, dict):
                # Check for required fields based on source
                if source == "corrections":
                    required_fields = ['original_term']  # Minimal requirement
                    recommended_fields = ['transliteration', 'category', 'confidence']
                elif source == "proper_nouns":
                    required_fields = ['term']  # Minimal requirement  
                    recommended_fields = ['category', 'confidence']
                else:
                    required_fields = []
                    recommended_fields = []
                
                # Validate required fields
                for field in required_fields:
                    if field not in entry:
                        logger.warning(f"Missing required field '{field}' for '{entry_key}' in {source}")
                        return False
                    
                    # Validate field type
                    if not isinstance(entry[field], str):
                        logger.error(f"Invalid type for '{field}' in '{entry_key}' ({source}): {type(entry[field])}")
                        return False
                
                # Warn about missing recommended fields
                for field in recommended_fields:
                    if field not in entry:
                        logger.debug(f"Recommended field '{field}' missing for '{entry_key}' in {source}")
                
                return True
                
        except Exception as e:
            logger.error(f"Validation error for '{entry_key}' in {source}: {e}")
            raise ValidationError(f"Failed to validate entry '{entry_key}' in {source}: {e}")
        
        return False
    
    @staticmethod
    def validate_lexicon_file(file_path: Path) -> Dict[str, Any]:
        """
        Validate a lexicon YAML file structure.
        
        Args:
            file_path: Path to lexicon file
            
        Returns:
            Dict with validation results and statistics
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {'total_entries': 0, 'valid_entries': 0, 'invalid_entries': 0}
        }
        
        try:
            if not file_path.exists():
                results['errors'].append(f"File not found: {file_path}")
                results['valid'] = False
                return results
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                results['warnings'].append(f"Empty file: {file_path}")
                return results
            
            # Validate structure
            if 'entries' not in data:
                results['errors'].append(f"Missing 'entries' key in {file_path}")
                results['valid'] = False
                return results
            
            entries = data['entries']
            if not isinstance(entries, list):
                results['errors'].append(f"'entries' must be a list in {file_path}")
                results['valid'] = False
                return results
            
            # Validate each entry
            results['stats']['total_entries'] = len(entries)
            
            for i, entry in enumerate(entries):
                entry_id = f"entry_{i}"
                if isinstance(entry, dict) and 'original_term' in entry:
                    entry_id = entry['original_term']
                
                if InputValidator.validate_database_entry(entry, entry_id, file_path.stem):
                    results['stats']['valid_entries'] += 1
                else:
                    results['stats']['invalid_entries'] += 1
                    results['warnings'].append(f"Invalid entry: {entry_id}")
            
            # Check for duplicates
            seen_terms = set()
            for entry in entries:
                if isinstance(entry, dict) and 'original_term' in entry:
                    term = entry['original_term'].lower()
                    if term in seen_terms:
                        results['warnings'].append(f"Duplicate term: {entry['original_term']}")
                    seen_terms.add(term)
            
        except Exception as e:
            results['errors'].append(f"Failed to validate {file_path}: {e}")
            results['valid'] = False
        
        return results
    
    @staticmethod 
    def validate_all_lexicons(lexicon_dir: Path) -> Dict[str, Any]:
        """
        Validate all lexicon files in directory.
        
        Args:
            lexicon_dir: Directory containing lexicon files
            
        Returns:
            Combined validation results
        """
        combined_results = {
            'valid': True,
            'files_checked': 0,
            'files_valid': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'file_results': {}
        }
        
        lexicon_files = list(lexicon_dir.glob('*.yaml')) + list(lexicon_dir.glob('*.yml'))
        
        for file_path in lexicon_files:
            combined_results['files_checked'] += 1
            file_results = InputValidator.validate_lexicon_file(file_path)
            
            combined_results['file_results'][str(file_path)] = file_results
            combined_results['total_errors'] += len(file_results['errors'])
            combined_results['total_warnings'] += len(file_results['warnings'])
            
            if file_results['valid']:
                combined_results['files_valid'] += 1
            else:
                combined_results['valid'] = False
        
        logger.info(f"Lexicon validation: {combined_results['files_valid']}/{combined_results['files_checked']} files valid")
        if combined_results['total_errors'] > 0:
            logger.warning(f"Found {combined_results['total_errors']} validation errors")
        if combined_results['total_warnings'] > 0:
            logger.info(f"Found {combined_results['total_warnings']} validation warnings")
        
        return combined_results


class DatabaseValidator:
    """Validator for database entries with startup-time optimization."""

    # Class-level cache for validated entries (initialized at startup)
    _validated_cache = {}
    _validation_enabled = True

    @classmethod
    def initialize_validation_cache(cls, lexicon_loader: Any) -> None:
        """
        Pre-validate all lexicon entries at startup for optimal performance.
        Moves validation overhead from runtime to initialization.
        """
        logger.info("Initializing validation cache for performance optimization...")
        start_time = time.time()

        cls._validated_cache = {
            'corrections': {},
            'proper_nouns': {}
        }

        # Pre-validate corrections dictionary
        if hasattr(lexicon_loader, 'corrections'):
            for key, entry in lexicon_loader.corrections.items():
                validated_entry = cls._validate_and_normalize_entry(entry, key, 'corrections')
                if validated_entry:
                    cls._validated_cache['corrections'][key] = validated_entry

        # Pre-validate proper_nouns dictionary
        if hasattr(lexicon_loader, 'proper_nouns'):
            for key, entry in lexicon_loader.proper_nouns.items():
                validated_entry = cls._validate_and_normalize_entry(entry, key, 'proper_nouns')
                if validated_entry:
                    cls._validated_cache['proper_nouns'][key] = validated_entry

        cache_time = time.time() - start_time
        total_entries = len(cls._validated_cache['corrections']) + len(cls._validated_cache['proper_nouns'])
        logger.info(f"Validation cache initialized in {cache_time:.3f}s with {total_entries} validated entries")

    @classmethod
    def _validate_and_normalize_entry(cls, entry: Any, key: str, source: str) -> Optional[Dict[str, str]]:
        """
        Validate and normalize a single entry, returning a clean string-based dict.
        """
        try:
            if isinstance(entry, str):
                return {'original_term': entry, 'term': entry}
            elif isinstance(entry, dict):
                # Extract and validate the main term
                main_key = 'original_term' if source == 'corrections' else 'term'
                term_value = entry.get(main_key) or entry.get('original_term') or entry.get('term')

                if term_value and isinstance(term_value, str):
                    return {
                        'original_term': str(term_value),
                        'term': str(term_value),
                        # Include other string fields if present
                        **{k: str(v) for k, v in entry.items()
                           if isinstance(v, (str, int, float)) and k not in ['original_term', 'term']}
                    }

            logger.debug(f"Invalid entry type for '{key}' in {source}: {type(entry)}")
            return None

        except Exception as e:
            logger.warning(f"Failed to validate entry '{key}' in {source}: {e}")
            return None

    @classmethod
    def get_validated_entry(cls, database_type: str, key: str) -> Optional[Dict[str, str]]:
        """
        Fast lookup of pre-validated entries.
        Returns None if not found or validation disabled.
        """
        if not cls._validation_enabled or database_type not in cls._validated_cache:
            return None
        return cls._validated_cache[database_type].get(key)

    @staticmethod
    def safe_get_entry_value(entry: Any, key: str, default: str = "") -> str:
        """
        Safely extract value from database entry with type checking.
        
        Args:
            entry: Database entry (could be dict, str, or other)
            key: Key to extract
            default: Default value if extraction fails
            
        Returns:
            Extracted string value or default
        """
        try:
            if isinstance(entry, dict):
                value = entry.get(key, default)
                return str(value) if value is not None else default
            elif isinstance(entry, str):
                return entry if key in ['term', 'original_term'] else default
            else:
                logger.debug(f"Unexpected entry type: {type(entry)}, returning default")
                return default
        except Exception as e:
            logger.debug(f"Safe get failed for key '{key}': {e}")
            return default
    
    @staticmethod
    def validate_word_input(word: Any) -> Optional[str]:
        """
        Validate and normalize word input to prevent type errors.
        
        Args:
            word: Input word (should be string)
            
        Returns:
            Normalized string or None if invalid
        """
        if word is None:
            return None
        
        if isinstance(word, str):
            return word.strip() if word.strip() else None
        
        # Handle numeric or other types
        if isinstance(word, (int, float)):
            logger.debug(f"Converting numeric input to string: {word}")
            return str(word)
        
        logger.warning(f"Invalid word input type: {type(word)} - {word}")
        return None


# Quick validation utility functions
def validate_lexicon_directory(lexicon_dir: Path) -> bool:
    """Quick validation check for lexicon directory."""
    try:
        results = InputValidator.validate_all_lexicons(lexicon_dir)
        return results['valid'] and results['total_errors'] == 0
    except Exception as e:
        logger.error(f"Failed to validate lexicon directory: {e}")
        return False

def create_validation_report(lexicon_dir: Path, output_file: Optional[Path] = None) -> Dict[str, Any]:
    """Create comprehensive validation report."""
    try:
        results = InputValidator.validate_all_lexicons(lexicon_dir)
        
        # Add summary
        results['summary'] = {
            'overall_status': 'PASS' if results['valid'] else 'FAIL',
            'files_checked': results['files_checked'],
            'error_rate': results['total_errors'] / max(1, results['files_checked']),
            'warning_rate': results['total_warnings'] / max(1, results['files_checked'])
        }
        
        if output_file:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Validation report saved to: {output_file}")
        
        return results
    except Exception as e:
        logger.error(f"Failed to create validation report: {e}")
        return {'valid': False, 'error': str(e)}