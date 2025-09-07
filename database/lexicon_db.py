"""Story 6.3: Lean SQLite Integration - <80 lines total"""
import sqlite3, json
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class DatabaseTerm:
    original_term: str
    variations: List[str] 
    transliteration: str
    category: str
    confidence: float
    context_clues: List[str] = None
    is_compound: bool = False

class LexiconDatabase:
    """Lightweight SQLite integration with caching."""
    def __init__(self, db_path: Path, enable_fallback: bool = True):
        self.db_path, self.enable_fallback = db_path, enable_fallback
        self._connection, self._term_cache = None, {}
        
    def connect(self) -> bool:
        """Connect to database with error handling."""
        try:
            if self.db_path.exists():
                self._connection = sqlite3.connect(str(self.db_path))
                self._connection.row_factory = sqlite3.Row
                return True
        except sqlite3.Error:
            pass
        return False
        
    def lookup_term(self, term: str) -> Optional[DatabaseTerm]:
        """Fast cached term lookup."""
        term_lower = term.lower().strip()
        if term_lower in self._term_cache:
            return self._term_cache[term_lower]
            
        if self._connection:
            try:
                cursor = self._connection.cursor()
                # FIXED: Use exact matching only, no wildcards
                # First try exact original_term match
                cursor.execute("""
                SELECT original_term, variations, transliteration, category, 
                       confidence, context_clues, is_compound
                FROM terms WHERE LOWER(original_term) = ? LIMIT 1
                """, (term_lower,))
                
                row = cursor.fetchone()
                if not row:
                    # Then try exact variation match by parsing JSON
                    cursor.execute("""
                    SELECT original_term, variations, transliteration, category, 
                           confidence, context_clues, is_compound
                    FROM terms WHERE variations IS NOT NULL
                    """)
                    for db_row in cursor.fetchall():
                        try:
                            variations = json.loads(db_row['variations']) if db_row['variations'] else []
                            if term_lower in [v.lower() for v in variations]:
                                row = db_row
                                break
                        except json.JSONDecodeError:
                            continue
                
                if row:
                    db_term = DatabaseTerm(
                        original_term=row['original_term'],
                        variations=json.loads(row['variations']) if row['variations'] else [],
                        transliteration=row['transliteration'],
                        category=row['category'], 
                        confidence=row['confidence'],
                        context_clues=json.loads(row['context_clues']) if row['context_clues'] else [],
                        is_compound=bool(row['is_compound']))
                    self._term_cache[term_lower] = db_term
                    return db_term
            except (sqlite3.Error, json.JSONDecodeError, KeyError):
                pass
        return None
        
    def close(self):
        """Clean up connection."""
        if self._connection:
            self._connection.close()
            self._connection = None