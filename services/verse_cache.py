#!/usr/bin/env python3
"""
Verse Cache System for Sanskrit Scripture Lookup
Provides fast local lookup for Bhagavad Gita and other Sanskrit verses.
"""

import json
import re
import sqlite3
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CachedVerse:
    """A cached verse with metadata."""
    chapter: int
    verse: int
    sanskrit: str
    transliteration: str
    translation: str
    keywords: str
    source: str = "Bhagavad Gītā"

class VerseCache:
    """Local cache for Sanskrit verses with search capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_dir = Path("data")
        self.verse_db_path = self.data_dir / "scripture_verses.db"
        self.json_path = self.data_dir / "bhagavad_gita_verses.json"
        self.verses: Dict[str, CachedVerse] = {}
        self._load_verses()
    
    def _load_verses(self):
        """Load verses from available sources."""
        # Try JSON file first
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        key = f"{item['chapter']}.{item['verse']}"
                        self.verses[key] = CachedVerse(
                            chapter=item['chapter'],
                            verse=item['verse'],
                            sanskrit=item.get('sanskrit', ''),
                            transliteration=item.get('transliteration', ''),
                            translation=item.get('translation', ''),
                            keywords=item.get('keywords', ''),
                            source=item.get('source', 'Bhagavad Gītā')
                        )
                logger.info(f"Loaded {len(self.verses)} verses from JSON cache")
            except Exception as e:
                logger.warning(f"Failed to load verses from JSON: {e}")
        
        # Try SQLite database as fallback
        if not self.verses and self.verse_db_path.exists():
            self._load_from_sqlite()
    
    def _load_from_sqlite(self):
        """Load verses from SQLite database."""
        try:
            with sqlite3.connect(self.verse_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT chapter, verse, sanskrit, transliteration, translation, keywords, source
                    FROM verses WHERE source = 'Bhagavad Gītā'
                """)
                for row in cursor.fetchall():
                    key = f"{row[0]}.{row[1]}"
                    self.verses[key] = CachedVerse(
                        chapter=row[0], verse=row[1], sanskrit=row[2],
                        transliteration=row[3], translation=row[4],
                        keywords=row[5], source=row[6]
                    )
                logger.info(f"Loaded {len(self.verses)} verses from SQLite")
        except Exception as e:
            logger.warning(f"Failed to load verses from SQLite: {e}")
    
    def is_cache_valid(self) -> bool:
        """Check if cache is valid and populated."""
        return len(self.verses) > 0
    
    def download_verses(self):
        """Download/populate verses - for now just ensure we have the local data."""
        if not self.is_cache_valid():
            logger.warning("No verse data available - cache remains empty")
    
    def get_verse(self, chapter: int, verse: int) -> Optional[CachedVerse]:
        """Get a specific verse by chapter and verse number."""
        key = f"{chapter}.{verse}"
        return self.verses.get(key)
    
    def detect_verse_references(self, text: str) -> List[Tuple[int, int]]:
        """Detect verse references like 'BG 2.46' or 'chapter 2 verse 46'."""
        references = []
        
        # Pattern for "BG 2.46" or "Bhagavad Gita 2.46"
        bg_pattern = r'(?:BG|Bhagavad\s*Gita)\s*(\d+)\.(\d+)'
        matches = re.finditer(bg_pattern, text, re.IGNORECASE)
        for match in matches:
            chapter, verse = int(match.group(1)), int(match.group(2))
            references.append((chapter, verse))
        
        # Pattern for "chapter X verse Y"
        chapter_verse_pattern = r'chapter\s+(\d+).*?verse\s+(?:number\s+)?(\d+)'
        matches = re.finditer(chapter_verse_pattern, text, re.IGNORECASE)
        for match in matches:
            chapter, verse = int(match.group(1)), int(match.group(2))
            references.append((chapter, verse))
        
        return references
    
    def search_content(self, text_snippet: str, max_results: int = 5) -> List[CachedVerse]:
        """Search for verses by content similarity."""
        results = []
        search_terms = text_snippet.lower().split()
        
        for verse in self.verses.values():
            # Search in transliteration and keywords
            searchable_text = f"{verse.transliteration} {verse.keywords}".lower()
            
            # Simple scoring based on word matches
            score = 0
            for term in search_terms:
                if len(term) > 3 and term in searchable_text:
                    score += 1
            
            if score > 0:
                results.append((score, verse))
        
        # Sort by score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        return [verse for score, verse in results[:max_results]]

def create_verse_cache(config: Dict[str, Any]) -> VerseCache:
    """Factory function to create verse cache instance."""
    return VerseCache(config)