"""Story 6.3: Database Integration - Lean Implementation (200 lines total)"""
import yaml
from pathlib import Path
from typing import Optional, List
from database.lexicon_db import LexiconDatabase, DatabaseTerm
import logging
import re

logger = logging.getLogger(__name__)

def sanskrit_phonetic_similarity(word1: str, word2: str) -> float:
    """Calculate phonetic similarity for Sanskrit words considering ASR corruption."""
    if not word1 or not word2:
        return 0.0
    
    w1, w2 = word1.lower(), word2.lower()
    
    # Exact match
    if w1 == w2:
        return 1.0
        
    # ASR common corruptions for Sanskrit
    substitutions = {
        # Nasal corruptions
        'ṇ': 'n', 'ṃ': 'm', 'ṁ': 'n',
        # Retroflex corruptions  
        'ṭ': 't', 'ḍ': 'd', 'ṛ': 'r', 'ṝ': 'r',
        # Sibilant corruptions
        'ś': 'sh', 'ṣ': 's', 'ḥ': 'h',
        # Vowel corruptions
        'ā': 'aa', 'ī': 'ii', 'ū': 'uu',
        # Common ASR mistakes
        'rn': 'n', 'rṇ': 'n', 'purna': 'puna',
    }
    
    # Apply phonetic normalization
    def normalize(word):
        normalized = word
        for src, dest in substitutions.items():
            normalized = normalized.replace(src, dest)
        # Remove hyphens and spaces
        normalized = re.sub(r'[-\s]', '', normalized)
        return normalized
    
    norm1, norm2 = normalize(w1), normalize(w2)
    
    if norm1 == norm2:
        return 0.9  # High similarity for phonetic match
    
    # Levenshtein distance-based similarity for partial matches
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    max_len = max(len(norm1), len(norm2))
    if max_len == 0:
        return 0.0
    
    distance = levenshtein(norm1, norm2)
    similarity = 1.0 - (distance / max_len)
    
    # Boost similarity if it's likely the same Sanskrit word
    if similarity > 0.7 and len(w1) > 4 and len(w2) > 4:
        return min(0.85, similarity + 0.1)
        
    return similarity

# English words that should never be treated as Sanskrit variations
ENGLISH_BLOCKLIST = {
    'pad', 'man', 'car', 'mat', 'rat', 'ram', 'pan', 'tan', 'van', 'ban', 
    'can', 'dam', 'fan', 'jam', 'lag', 'mad', 'nag', 'rag', 'sag', 'tag', 
    'wag', 'bag', 'gag', 'hag', 'bat', 'cat', 'fat', 'hat', 'pat', 'sat',
    'bad', 'dad', 'had', 'lad', 'sad', 'tar', 'war', 'far', 'bar', 'jar',
    'lab', 'cab', 'tab', 'dab', 'gab', 'nab', 'sab', 'pal', 'gal', 'sal',
    'and', 'the', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
    'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how',
    'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did',
    'its', 'let', 'put', 'say', 'she', 'too', 'use', 'run', 'big', 'end',
    'why', 'win', 'yes', 'yet', 'cut', 'cup', 'fun', 'gun', 'hot', 'job',
    'lot', 'met', 'net', 'pen', 'red', 'run', 'sun', 'top', 'try', 'win'
}

class HybridLexiconDict(dict):
    """Database-first dictionary with YAML fallback and lookup cache."""
    def __init__(self, database, yaml_dict, stats, lookup_type='corrections'):
        super().__init__(yaml_dict)
        self.database, self.stats, self.lookup_type = database, stats, lookup_type
        self._lookup_cache = {}  # Cache database results
        
    def __contains__(self, key):
        # Filter out English words immediately
        if key.lower().strip() in ENGLISH_BLOCKLIST:
            return False
            
        # Check cache first
        if key in self._lookup_cache:
            return self._lookup_cache[key] is not None
            
        # Check database
        if self.database:
            result = self.database.lookup_term(key)
            if result and (result.confidence >= 0.7 if self.lookup_type == 'corrections' 
                          else result.category in ['deity', 'person', 'place']):
                self._lookup_cache[key] = result
                return True
            else:
                self._lookup_cache[key] = None  # Cache negative results too
        
        # Check YAML fallback
        return super().__contains__(key)
        
    def __getitem__(self, key):
        # Filter out English words immediately
        if key.lower().strip() in ENGLISH_BLOCKLIST:
            self.stats['misses'] += 1
            raise KeyError(key)
            
        # Check cache first
        if key in self._lookup_cache and self._lookup_cache[key] is not None:
            result = self._lookup_cache[key]
            self.stats['database_hits'] += 1
            is_correction = self.lookup_type == 'corrections'
            return {'original_term': result.original_term, 'variations': result.variations, 
                   'category': result.category} | ({'term': result.original_term} if not is_correction else {})
        
        # Database lookup (if not cached)
        if self.database and key not in self._lookup_cache:
            result = self.database.lookup_term(key)
            is_correction = self.lookup_type == 'corrections'
            if result and (result.confidence >= 0.7 if is_correction 
                          else result.category in ['deity', 'person', 'place']):
                self._lookup_cache[key] = result
                self.stats['database_hits'] += 1
                return {'original_term': result.original_term, 'variations': result.variations, 
                       'category': result.category} | ({'term': result.original_term} if not is_correction else {})
            else:
                self._lookup_cache[key] = None
        
        # YAML fallback - exact match
        if super().__contains__(key):
            self.stats['yaml_hits'] += 1
            return super().__getitem__(key)
            
        # Phonetic matching for Sanskrit terms (corrections only)
        is_correction = self.lookup_type == 'corrections'
        if is_correction and len(key) > 3:  # Only for longer terms
            best_match = None
            best_similarity = 0.0
            
            # Check YAML entries for phonetic similarity
            for yaml_key, yaml_value in super().items():
                # Check original term
                similarity = sanskrit_phonetic_similarity(key, yaml_key)
                if similarity > best_similarity and similarity >= 0.8:
                    best_similarity = similarity
                    best_match = yaml_value
                    
                # Check variations
                for variation in yaml_value.get('variations', []):
                    similarity = sanskrit_phonetic_similarity(key, variation)
                    if similarity > best_similarity and similarity >= 0.8:
                        best_similarity = similarity
                        best_match = yaml_value
            
            if best_match:
                self.stats['phonetic_matches'] = self.stats.get('phonetic_matches', 0) + 1
                return best_match
            
        self.stats['misses'] += 1
        raise KeyError(key)


class HybridLexiconLoader:
    """Database + YAML lexicon loader with seamless fallback."""
    def __init__(self, lexicon_dir: Path, config: dict = None):
        self.lexicon_dir, self.config = Path(lexicon_dir), config or {}
        self.stats = {'database_hits': 0, 'yaml_hits': 0, 'misses': 0}
        
        # Initialize database with proper configuration
        self.database = None
        
        # Try to get database config from multiple sources
        db_config = self.config.get('database', {})
        if not db_config and 'lexicons' in self.config:
            db_config = self.config['lexicons'].get('database', {})
        
        # Default database path if not specified
        if db_config.get('enabled', True):
            db_path = db_config.get('path', 'data/sanskrit_terms.db')
            db_path = Path(db_path)
            
            # Try to import and initialize LexiconDatabase
            try:
                from database.lexicon_db import LexiconDatabase
                self.database = LexiconDatabase(db_path)
                if self.database.connect():
                    term_count = self.database.get_term_count() if hasattr(self.database, 'get_term_count') else 'unknown'
                    logger.info(f"Connected to database: {db_path} ({term_count} terms)")
                else:
                    logger.warning("Database connection failed, using YAML fallback only")
                    self.database = None
            except ImportError as e:
                logger.warning(f"Database module not available: {e}, using YAML fallback only")
                self.database = None
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}, using YAML fallback only")
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