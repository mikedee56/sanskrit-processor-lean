"""
Scripture Verse Bulk Import Utility
Imports verses from various formats into the scripture database with phonetic indexing

Supports:
- CSV/JSON imports from scripture collections
- Batch processing with progress tracking
- Automatic phonetic key generation
- Full-text indexing for fast searches
- Multiple scripture sources (Gita, Upanishads, etc.)
"""

import sqlite3
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from .phonetic_sanskrit import SanskritPhoneticMatcher
import logging

logger = logging.getLogger(__name__)

@dataclass
class VerseRecord:
    """Structure for a single verse record."""
    source: str           # "Bhagavad Gītā", "Īśā Upaniṣad", etc.
    chapter: int         # Chapter number
    verse: int           # Verse number  
    sanskrit: str        # Original Sanskrit text
    transliteration: str # IAST transliteration
    translation: str     # English translation
    keywords: str        # Space-separated keywords
    
    def __post_init__(self):
        """Validate and clean verse data."""
        if not self.source or not self.transliteration:
            raise ValueError(f"Source and transliteration are required")
        
        # Clean up text fields
        self.sanskrit = self.sanskrit.strip() if self.sanskrit else ""
        self.transliteration = self.transliteration.strip()
        self.translation = self.translation.strip() if self.translation else ""
        self.keywords = self.keywords.strip() if self.keywords else ""

class VerseImporter:
    """
    Main verse import utility with phonetic indexing.
    Handles bulk imports with progress tracking and validation.
    """
    
    def __init__(self, db_path: Union[str, Path], phonetic_matcher: Optional[SanskritPhoneticMatcher] = None):
        """Initialize importer with database path and phonetic matcher."""
        self.db_path = Path(db_path)
        self.phonetic_matcher = phonetic_matcher or SanskritPhoneticMatcher()
        self._ensure_database()
    
    def _ensure_database(self):
        """Create enhanced database schema if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verses'")
        if not cursor.fetchone():
            self._create_enhanced_schema(cursor)
            logger.info(f"Created enhanced scripture database at {self.db_path}")
        else:
            # Check if we need to add phonetic columns
            cursor.execute("PRAGMA table_info(verses)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'phonetic_key' not in columns:
                self._add_phonetic_columns(cursor)
                logger.info("Added phonetic indexing columns to existing database")
        
        conn.commit()
        conn.close()
    
    def _create_enhanced_schema(self, cursor):
        """Create enhanced database schema with phonetic indexing."""
        # Main verses table
        cursor.execute('''
            CREATE TABLE verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                sanskrit TEXT,
                transliteration TEXT NOT NULL,
                translation TEXT,
                keywords TEXT,
                phonetic_key TEXT,
                metaphone_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, chapter, verse)
            )
        ''')
        
        # N-gram table for partial matching
        cursor.execute('''
            CREATE TABLE verse_ngrams (
                verse_id INTEGER,
                ngram TEXT,
                FOREIGN KEY(verse_id) REFERENCES verses(id),
                PRIMARY KEY(verse_id, ngram)
            )
        ''')
        
        # Full-text search table
        cursor.execute('''
            CREATE VIRTUAL TABLE verse_fts USING fts5(
                source, transliteration, translation, keywords,
                content='verses', content_rowid='id'
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX idx_verses_source ON verses(source)')
        cursor.execute('CREATE INDEX idx_verses_phonetic ON verses(phonetic_key)')
        cursor.execute('CREATE INDEX idx_verses_metaphone ON verses(metaphone_key)')
        cursor.execute('CREATE INDEX idx_ngrams_ngram ON verse_ngrams(ngram)')
    
    def _add_phonetic_columns(self, cursor):
        """Add phonetic columns to existing database."""
        try:
            cursor.execute('ALTER TABLE verses ADD COLUMN phonetic_key TEXT')
            cursor.execute('ALTER TABLE verses ADD COLUMN metaphone_key TEXT')
            
            # Create new tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verse_ngrams (
                    verse_id INTEGER,
                    ngram TEXT,
                    FOREIGN KEY(verse_id) REFERENCES verses(id),
                    PRIMARY KEY(verse_id, ngram)
                )
            ''')
            
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS verse_fts USING fts5(
                    source, transliteration, translation, keywords,
                    content='verses', content_rowid='id'
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_verses_phonetic ON verses(phonetic_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_verses_metaphone ON verses(metaphone_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ngrams_ngram ON verse_ngrams(ngram)')
            
        except sqlite3.OperationalError as e:
            logger.warning(f"Some schema updates failed (may already exist): {e}")
    
    def _generate_phonetic_keys(self, verse: VerseRecord) -> Tuple[str, str]:
        """Generate phonetic keys for a verse."""
        # Use transliteration as primary text for phonetic matching
        text = verse.transliteration
        
        phonetic_key = self.phonetic_matcher.sanskrit_soundex(text)
        metaphone_key = self.phonetic_matcher.sanskrit_metaphone(text)
        
        return phonetic_key, metaphone_key
    
    def _generate_ngrams(self, verse: VerseRecord, n: int = 3) -> List[str]:
        """Generate n-grams for partial matching."""
        # Combine transliteration and translation for n-gram generation
        combined_text = f"{verse.transliteration} {verse.translation}"
        ngrams = self.phonetic_matcher.generate_ngrams(combined_text, n)
        return list(ngrams)
    
    def import_from_json(self, json_file: Union[str, Path], batch_size: int = 100) -> Dict[str, int]:
        """
        Import verses from JSON file.
        Expected format: {"verses": [{"source": "...", "chapter": 1, ...}, ...]}
        """
        json_file = Path(json_file)
        if not json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both array format and object format
        if isinstance(data, list):
            verses_data = data
        else:
            verses_data = data.get('verses', [])
        
        if not verses_data:
            raise ValueError("No verses found in JSON file")
        
        # Convert to VerseRecord objects
        verses = []
        for verse_data in verses_data:
            try:
                verse = VerseRecord(**verse_data)
                verses.append(verse)
            except (TypeError, ValueError) as e:
                logger.warning(f"Skipping invalid verse record: {e}")
                continue
        
        return self._import_verses_batch(verses, batch_size)
    
    def import_from_csv(self, csv_file: Path, batch_size: int = 100) -> Dict[str, int]:
        """
        Import verses from CSV file.
        Expected columns: source,chapter,verse,sanskrit,transliteration,translation,keywords
        """
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        verses = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    verse = VerseRecord(
                        source=row['source'],
                        chapter=int(row['chapter']),
                        verse=int(row['verse']),
                        sanskrit=row.get('sanskrit', ''),
                        transliteration=row['transliteration'],
                        translation=row.get('translation', ''),
                        keywords=row.get('keywords', '')
                    )
                    verses.append(verse)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid CSV row: {e}")
                    continue
        
        if not verses:
            raise ValueError("No valid verses found in CSV file")
        
        return self._import_verses_batch(verses, batch_size)
    
    def _import_verses_batch(self, verses: List[VerseRecord], batch_size: int = 100) -> Dict[str, int]:
        """Import verses in batches with full indexing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_verses': len(verses),
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
        
        try:
            for i in range(0, len(verses), batch_size):
                batch = verses[i:i + batch_size]
                batch_stats = self._import_batch(cursor, batch)
                
                # Update stats
                for key in ['imported', 'skipped', 'errors']:
                    stats[key] += batch_stats[key]
                
                # Progress logging
                progress = min(i + batch_size, len(verses))
                logger.info(f"Import progress: {progress}/{len(verses)} verses processed")
                
            conn.commit()
            logger.info(f"Import completed: {stats}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Import failed: {e}")
            stats['errors'] += 1
            raise
        finally:
            conn.close()
        
        return stats
    
    def _import_batch(self, cursor, verses: List[VerseRecord]) -> Dict[str, int]:
        """Import a single batch of verses."""
        batch_stats = {'imported': 0, 'skipped': 0, 'errors': 0}
        
        for verse in verses:
            try:
                # Generate phonetic keys
                phonetic_key, metaphone_key = self._generate_phonetic_keys(verse)
                
                # Insert verse
                cursor.execute('''
                    INSERT OR IGNORE INTO verses 
                    (source, chapter, verse, sanskrit, transliteration, translation, keywords, phonetic_key, metaphone_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    verse.source, verse.chapter, verse.verse, verse.sanskrit,
                    verse.transliteration, verse.translation, verse.keywords,
                    phonetic_key, metaphone_key
                ))
                
                if cursor.rowcount == 0:
                    batch_stats['skipped'] += 1
                    logger.debug(f"Skipped duplicate verse: {verse.source} {verse.chapter}.{verse.verse}")
                    continue
                
                verse_id = cursor.lastrowid
                batch_stats['imported'] += 1
                
                # Generate and insert n-grams
                ngrams = self._generate_ngrams(verse)
                for ngram in ngrams:
                    cursor.execute('''
                        INSERT OR IGNORE INTO verse_ngrams (verse_id, ngram) VALUES (?, ?)
                    ''', (verse_id, ngram))
                
                # Update FTS index
                cursor.execute('''
                    INSERT INTO verse_fts (rowid, source, transliteration, translation, keywords)
                    VALUES (?, ?, ?, ?, ?)
                ''', (verse_id, verse.source, verse.transliteration, verse.translation, verse.keywords))
                
            except Exception as e:
                batch_stats['errors'] += 1
                logger.error(f"Error importing verse {verse.source} {verse.chapter}.{verse.verse}: {e}")
        
        return batch_stats
    
    def get_import_stats(self) -> Dict[str, Any]:
        """Get current database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Total verses
            cursor.execute("SELECT COUNT(*) FROM verses")
            total_verses = cursor.fetchone()[0]
            
            # Verses by source
            cursor.execute("SELECT source, COUNT(*) FROM verses GROUP BY source ORDER BY COUNT(*) DESC")
            by_source = dict(cursor.fetchall())
            
            # N-grams count
            cursor.execute("SELECT COUNT(*) FROM verse_ngrams")
            ngram_count = cursor.fetchone()[0]
            
            # Phonetic keys coverage
            cursor.execute("SELECT COUNT(*) FROM verses WHERE phonetic_key IS NOT NULL")
            phonetic_coverage = cursor.fetchone()[0]
            
            return {
                'total_verses': total_verses,
                'verses_by_source': by_source,
                'ngram_count': ngram_count,
                'phonetic_coverage': phonetic_coverage,
                'coverage_percentage': (phonetic_coverage / total_verses * 100) if total_verses > 0 else 0
            }
        
        finally:
            conn.close()
    
    def rebuild_phonetic_index(self) -> Dict[str, int]:
        """Rebuild phonetic keys for existing verses."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {'updated': 0, 'errors': 0}
        
        try:
            # Get all verses without phonetic keys
            cursor.execute("SELECT id, transliteration FROM verses WHERE phonetic_key IS NULL OR phonetic_key = ''")
            verses_to_update = cursor.fetchall()
            
            for verse_id, transliteration in verses_to_update:
                try:
                    # Create temporary verse record
                    temp_verse = VerseRecord(
                        source="temp", chapter=1, verse=1, sanskrit="",
                        transliteration=transliteration, translation="", keywords=""
                    )
                    
                    phonetic_key, metaphone_key = self._generate_phonetic_keys(temp_verse)
                    
                    cursor.execute('''
                        UPDATE verses SET phonetic_key = ?, metaphone_key = ? WHERE id = ?
                    ''', (phonetic_key, metaphone_key, verse_id))
                    
                    stats['updated'] += 1
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Error updating phonetic keys for verse {verse_id}: {e}")
            
            conn.commit()
            logger.info(f"Phonetic index rebuild completed: {stats}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Phonetic index rebuild failed: {e}")
            raise
        finally:
            conn.close()
        
        return stats


def create_sample_gita_data(output_file: Path):
    """Create sample Bhagavad Gita data for testing."""
    sample_verses = [
        {
            "source": "Bhagavad Gītā",
            "chapter": 2,
            "verse": 47,
            "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥",
            "transliteration": "karmaṇy evādhikāras te mā phaleṣu kadācana mā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi",
            "translation": "You have a right to perform your prescribed duty, but not to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
            "keywords": "karma action duty fruits attachment prescribed dharma"
        },
        {
            "source": "Bhagavad Gītā", 
            "chapter": 2,
            "verse": 56,
            "sanskrit": "दुःखेष्वनुद्विग्नमनाः सुखेषु विगतस्पृहः। वीतरागभयक्रोधः स्थितधीर्मुनिरुच्यते॥",
            "transliteration": "duḥkheṣv anudvigna-manāḥ sukheṣu vigata-spṛhaḥ vīta-rāga-bhaya-krodhaḥ sthita-dhīr munir ucyate",
            "translation": "One who is not disturbed in mind even amidst the threefold miseries or elated when there is happiness, and who is free from attachment, fear and anger, is called a sage of steady mind.",
            "keywords": "mind steady sage happiness misery attachment fear anger wisdom"
        },
        {
            "source": "Bhagavad Gītā",
            "chapter": 18,
            "verse": 66,
            "sanskrit": "सर्वधर्मान्परित्यज्य मामेकं शरणं व्रज। अहं त्वां सर्वपापेभ्यो मोक्षयिष्यामि मा शुचः॥",
            "transliteration": "sarva-dharmān parityajya mām ekaṃ śaraṇaṃ vraja ahaṃ tvāṃ sarva-pāpebhyo mokṣayiṣyāmi mā śucaḥ",
            "translation": "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions. Do not fear.",
            "keywords": "surrender religion dharma sin moksha fear deliver krishna"
        }
    ]
    
    data = {"verses": sample_verses}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Sample Gita data created at {output_file}")


# CLI utility functions
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python verse_importer.py <command> [args...]")
        print("Commands:")
        print("  import_json <db_path> <json_file>")
        print("  import_csv <db_path> <csv_file>") 
        print("  create_sample <output_file>")
        print("  stats <db_path>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "import_json" and len(sys.argv) == 4:
        db_path = Path(sys.argv[2])
        json_file = Path(sys.argv[3])
        
        importer = VerseImporter(db_path)
        stats = importer.import_from_json(json_file)
        print(f"Import completed: {stats}")
        
    elif command == "import_csv" and len(sys.argv) == 4:
        db_path = Path(sys.argv[2])
        csv_file = Path(sys.argv[3])
        
        importer = VerseImporter(db_path)
        stats = importer.import_from_csv(csv_file)
        print(f"Import completed: {stats}")
        
    elif command == "create_sample" and len(sys.argv) == 3:
        output_file = Path(sys.argv[2])
        create_sample_gita_data(output_file)
        
    elif command == "stats" and len(sys.argv) == 3:
        db_path = Path(sys.argv[2])
        importer = VerseImporter(db_path)
        stats = importer.get_import_stats()
        print(json.dumps(stats, indent=2))
        
    else:
        print("Invalid command or arguments")
        sys.exit(1)