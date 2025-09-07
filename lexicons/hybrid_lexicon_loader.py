"""Story 6.3: Database Integration - Lean Implementation (200 lines total)"""
import yaml
from pathlib import Path
from typing import Optional, List
from database.lexicon_db import LexiconDatabase, DatabaseTerm
import logging

logger = logging.getLogger(__name__)

class HybridLexiconDict(dict):
    """Database-first dictionary with YAML fallback."""
    def __init__(self, database, yaml_dict, stats, lookup_type='corrections'):
        super().__init__(yaml_dict)
        self.database, self.stats, self.lookup_type = database, stats, lookup_type
        
    def __contains__(self, key):
        if self.database:
            result = self.database.lookup_term(key)
            if result and (result.confidence >= 0.7 if self.lookup_type == 'corrections' 
                          else result.category in ['deity', 'person', 'place']):
                return True
        return super().__contains__(key)
        
    def __getitem__(self, key):
        if self.database:
            result = self.database.lookup_term(key)
            is_correction = self.lookup_type == 'corrections'
            if result and (result.confidence >= 0.7 if is_correction 
                          else result.category in ['deity', 'person', 'place']):
                self.stats['database_hits'] += 1
                return {'original_term': result.original_term, 'variations': result.variations, 
                       'category': result.category} | ({'term': result.original_term} if not is_correction else {})
        if super().__contains__(key):
            self.stats['yaml_hits'] += 1
            return super().__getitem__(key)
        self.stats['misses'] += 1
        raise KeyError(key)


class HybridLexiconLoader:
    """Database + YAML lexicon loader with seamless fallback."""
    def __init__(self, lexicon_dir: Path, config: dict = None):
        self.lexicon_dir, self.config = Path(lexicon_dir), config or {}
        self.stats = {'database_hits': 0, 'yaml_hits': 0, 'misses': 0}
        
        # Initialize database
        self.database = None
        db_config = self.config.get('database', {})
        if db_config.get('enabled', True) and db_config.get('path'):
            db_path = Path(db_config['path'])
            self.database = LexiconDatabase(db_path)
            if self.database.connect():
                logger.info(f"Connected to database: {db_path}")
            else:
                logger.warning("Database connection failed, using YAML fallback only")
                self.database = None
                
        # Load YAML lexicons
        yaml_corrections, yaml_proper_nouns = {}, {}
        self._load_yaml_lexicons(yaml_corrections, yaml_proper_nouns)
        
        # Create hybrid dictionaries
        self.corrections = HybridLexiconDict(self.database, yaml_corrections, self.stats, 'corrections')
        self.proper_nouns = HybridLexiconDict(self.database, yaml_proper_nouns, self.stats, 'proper_nouns')
        
    def _load_yaml_lexicons(self, corrections_dict, proper_nouns_dict):
        """Load YAML files as fallback."""
        try:
            for filename, target_dict in [('corrections.yaml', corrections_dict), 
                                        ('proper_nouns.yaml', proper_nouns_dict)]:
                filepath = self.lexicon_dir / filename
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        for entry in data.get('entries', []):
                            key = entry.get('original_term') or entry.get('term')
                            if key:
                                key_lower = key.lower() if filename == 'proper_nouns.yaml' else key
                                target_dict[key_lower] = entry
                                for variation in entry.get('variations', []):
                                    var_key = variation.lower() if filename == 'proper_nouns.yaml' else variation
                                    target_dict[var_key] = entry
                    logger.info(f"Loaded {len(target_dict)} {filename.replace('.yaml', '')} entries")
        except Exception as e:
            logger.warning(f"Failed to load YAML lexicons: {e}")
            
    def get_compound_terms(self, text: str) -> List[DatabaseTerm]:
        """Get compound terms from database."""
        if not self.database:
            return []
        compounds = []
        words = text.split()
        for i in range(len(words)):
            for j in range(i + 2, min(i + 6, len(words) + 1)):
                result = self.database.lookup_term(' '.join(words[i:j]))
                if result and result.is_compound:
                    compounds.append(result)
        return compounds
        
    def get_stats(self):
        """Return lookup statistics."""
        total = sum(self.stats.values())
        return self.stats if total == 0 else {**self.stats, 
            'database_hit_rate': self.stats['database_hits'] / total * 100,
            'yaml_hit_rate': self.stats['yaml_hits'] / total * 100, 'total_lookups': total}
        
    def close(self):
        """Clean up database connections."""
        if self.database:
            self.database.close()