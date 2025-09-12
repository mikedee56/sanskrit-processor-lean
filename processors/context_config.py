"""Context detection configuration management.

This module provides configuration management for the context detection system,
including threshold settings and marker configurations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    """Configuration for context detection system.
    
    This dataclass encapsulates all configuration settings for context detection,
    including thresholds, markers, and processing options.
    """
    
    # Threshold configuration
    english_threshold: float = 0.8
    sanskrit_threshold: float = 0.6
    mixed_threshold: float = 0.5
    whitelist_override_threshold: float = 0.9
    diacritical_density_high: float = 0.3
    diacritical_density_medium: float = 0.1
    english_markers_required: int = 2
    
    # Sanskrit priority terms for whitelist override
    sanskrit_priority_terms: List[str] = field(default_factory=lambda: [
        'dharma', 'karma', 'yoga', 'jñāna', 'jnana', 'brahman',
        'guru', 'mantra', 'yogavāsiṣṭha', 'yogavasistha', 'śivāśiṣṭha',
        'shivashistha', 'gītā', 'gita', 'upaniṣad', 'upanishad'
    ])
    
    # English function words
    english_function_words: List[str] = field(default_factory=lambda: [
        'the', 'and', 'is', 'are', 'was', 'were', 'be', 'being', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'a', 'an', 'or', 'but', 'in', 'on',
        'at', 'by', 'to', 'of', 'with', 'from', 'about'
    ])
    
    # Sanskrit diacriticals and markers
    sanskrit_diacriticals: List[str] = field(default_factory=lambda: [
        'ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ṅ', 'ñ', 'ṇ', 'ṭ', 'ḍ', 'ś', 'ṣ', 'ḥ', 'ṁ'
    ])
    
    sanskrit_sacred_terms: List[str] = field(default_factory=lambda: [
        'oṁ', 'oṃ', 'namaḥ', 'namah', 'śrī', 'sri', 'mahā', 'maha',
        'bhagavad', 'gītā', 'gita', 'rāmāyaṇa', 'ramayana', 'kṛṣṇa',
        'krishna', 'rāma', 'rama', 'vedanta'
    ])
    
    # Processing options
    enable_whitelist_override: bool = True
    debug_logging: bool = False
    cache_results: bool = True
    performance_profiling: bool = False
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ContextConfig':
        """Create ContextConfig from dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            ContextConfig instance with values from dictionary
        """
        # Extract context_detection section if it exists
        context_config = config_dict.get('context_detection', {})
        
        # Extract thresholds
        thresholds = context_config.get('thresholds', {})
        
        # Extract markers
        markers = context_config.get('markers', {})
        
        # Extract processing options
        processing = context_config.get('processing', {})
        
        return cls(
            # Thresholds
            english_threshold=thresholds.get('english_confidence', 0.8),
            sanskrit_threshold=thresholds.get('sanskrit_confidence', 0.6),
            mixed_threshold=thresholds.get('mixed_content', 0.5),
            whitelist_override_threshold=thresholds.get('whitelist_override', 0.9),
            diacritical_density_high=thresholds.get('diacritical_density_high', 0.3),
            diacritical_density_medium=thresholds.get('diacritical_density_medium', 0.1),
            english_markers_required=thresholds.get('english_markers_required', 2),
            
            # Markers
            sanskrit_priority_terms=markers.get('sanskrit_priority_terms', cls().sanskrit_priority_terms),
            english_function_words=markers.get('english_function_words', cls().english_function_words),
            sanskrit_diacriticals=markers.get('sanskrit_diacriticals', cls().sanskrit_diacriticals),
            sanskrit_sacred_terms=markers.get('sanskrit_sacred_terms', cls().sanskrit_sacred_terms),
            
            # Processing options
            enable_whitelist_override=processing.get('enable_whitelist_override', True),
            debug_logging=processing.get('debug_logging', False),
            cache_results=processing.get('cache_context_results', True),
            performance_profiling=processing.get('performance_profiling', False)
        )
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'ContextConfig':
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            ContextConfig instance loaded from file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            return cls.from_dict(config_dict)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Could not load context config from {config_path}: {e}")
            logger.info("Using default context configuration")
            return cls()
    
    def validate(self) -> bool:
        """Validate configuration values.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []
        
        # Validate thresholds are in valid range
        thresholds = [
            ('english_threshold', self.english_threshold),
            ('sanskrit_threshold', self.sanskrit_threshold),
            ('mixed_threshold', self.mixed_threshold),
            ('whitelist_override_threshold', self.whitelist_override_threshold),
            ('diacritical_density_high', self.diacritical_density_high),
            ('diacritical_density_medium', self.diacritical_density_medium)
        ]
        
        for name, value in thresholds:
            if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                errors.append(f"{name} must be a number between 0.0 and 1.0, got: {value}")
        
        # Validate english_markers_required is positive integer
        if not isinstance(self.english_markers_required, int) or self.english_markers_required < 1:
            errors.append(f"english_markers_required must be a positive integer, got: {self.english_markers_required}")
        
        # Validate lists are not empty
        if not self.sanskrit_priority_terms:
            errors.append("sanskrit_priority_terms cannot be empty")
        
        if not self.english_function_words:
            errors.append("english_function_words cannot be empty")
        
        if errors:
            for error in errors:
                logger.error(f"Context configuration validation error: {error}")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'context_detection': {
                'thresholds': {
                    'english_confidence': self.english_threshold,
                    'sanskrit_confidence': self.sanskrit_threshold,
                    'mixed_content': self.mixed_threshold,
                    'whitelist_override': self.whitelist_override_threshold,
                    'diacritical_density_high': self.diacritical_density_high,
                    'diacritical_density_medium': self.diacritical_density_medium,
                    'english_markers_required': self.english_markers_required
                },
                'markers': {
                    'sanskrit_priority_terms': self.sanskrit_priority_terms,
                    'english_function_words': self.english_function_words,
                    'sanskrit_diacriticals': self.sanskrit_diacriticals,
                    'sanskrit_sacred_terms': self.sanskrit_sacred_terms
                },
                'processing': {
                    'enable_whitelist_override': self.enable_whitelist_override,
                    'debug_logging': self.debug_logging,
                    'cache_context_results': self.cache_results,
                    'performance_profiling': self.performance_profiling
                }
            }
        }