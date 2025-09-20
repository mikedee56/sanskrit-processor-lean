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
        """Check if cache is valid and populated with sufficient verses."""
        # Need substantial verse coverage - at least 600 verses for meaningful lookup
        return len(self.verses) >= 600
    
    def download_verses(self):
        """Download complete Bhagavad Gita from vedicscriptures.github.io API."""
        if self.is_cache_valid():
            logger.info(f"Cache already populated with {len(self.verses)} verses")
            return

        logger.info("Downloading complete Bhagavad Gita database...")

        # Bhagavad Gita chapter structure (chapter: verse_count)
        gita_structure = {
            1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28,
            9: 34, 10: 42, 11: 55, 12: 20, 13: 35, 14: 27, 15: 20,
            16: 24, 17: 28, 18: 78
        }

        try:
            import requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Sanskrit-Processor/1.0 (Academic Research)'
            })

            downloaded_verses = {}
            total_verses = sum(gita_structure.values())
            current_count = 0

            for chapter, verse_count in gita_structure.items():
                logger.info(f"Downloading Chapter {chapter} ({verse_count} verses)...")

                for verse in range(1, verse_count + 1):
                    try:
                        # Use the working vedicscriptures.github.io API
                        url = f"https://vedicscriptures.github.io/slok/{chapter}/{verse}"
                        response = session.get(url, timeout=10)

                        if response.status_code == 200:
                            data = response.json()

                            # Extract transliteration and keywords
                            transliteration = data.get('transliteration', '')
                            if not transliteration and 'slok' in data:
                                transliteration = self._basic_transliteration(data['slok'])

                            # Generate keywords from transliteration and translation
                            keywords = self._extract_keywords(transliteration, data.get('translation', ''))

                            verse_obj = CachedVerse(
                                chapter=chapter,
                                verse=verse,
                                sanskrit=data.get('slok', ''),
                                transliteration=transliteration,
                                translation=data.get('translation', ''),
                                keywords=keywords,
                                source="Bhagavad Gītā"
                            )

                            key = f"{chapter}.{verse}"
                            downloaded_verses[key] = verse_obj
                            current_count += 1

                            if current_count % 50 == 0:
                                logger.info(f"Downloaded {current_count}/{total_verses} verses...")

                        else:
                            logger.warning(f"Failed to download {chapter}.{verse}: HTTP {response.status_code}")

                    except Exception as e:
                        logger.warning(f"Error downloading verse {chapter}.{verse}: {e}")
                        continue

            if downloaded_verses:
                # Update internal cache
                self.verses.update(downloaded_verses)

                # Save to JSON file for persistence
                self._save_to_json(list(downloaded_verses.values()))

                logger.info(f"Successfully downloaded {len(downloaded_verses)} verses!")
                logger.info(f"Cache now contains {len(self.verses)} total verses")
            else:
                logger.warning("No verses were downloaded - check internet connection")

        except ImportError:
            logger.warning("Requests library not available - cannot download verses")
        except Exception as e:
            logger.error(f"Verse download failed: {e}")

    def _basic_transliteration(self, sanskrit_text: str) -> str:
        """Generate basic transliteration for verses without transliteration."""
        # This is a simplified fallback - in production would use proper library
        transliteration_map = {
            'कर्म': 'karma', 'धर्म': 'dharma', 'योग': 'yoga',
            'अर्जुन': 'arjuna', 'कृष्ण': 'kṛṣṇa', 'भगवान्': 'bhagavān',
            'गीता': 'gītā', 'वेद': 'veda', 'उपनिषद्': 'upaniṣad'
        }

        # For now, return a simplified version
        for sanskrit, iast in transliteration_map.items():
            if sanskrit in sanskrit_text:
                return iast + "..."

        return sanskrit_text[:50] + "..." if len(sanskrit_text) > 50 else sanskrit_text

    def _extract_keywords(self, transliteration: str, translation: str) -> str:
        """Extract searchable keywords from transliteration and translation."""
        import re

        keywords = set()

        # Extract from transliteration (Sanskrit terms) - more focused
        if transliteration:
            # Split compound words and extract meaningful terms
            words = re.findall(r'\b[a-zA-ZāīūṛṇṣśḥṁéóṭḍñĀĪŪṚṆṢŚḤṀ]+\b', transliteration)
            for word in words:
                if len(word) > 3:
                    keywords.add(word.lower())
                    # Add variations without diacritics
                    simplified = word.lower().replace('ā', 'a').replace('ī', 'i').replace('ū', 'u').replace('ṛ', 'r').replace('ṇ', 'n').replace('ṣ', 's').replace('ś', 's').replace('ḥ', 'h').replace('ṁ', 'm')
                    if simplified != word.lower():
                        keywords.add(simplified)

        # Extract comprehensive English concepts from translation
        if translation:
            # Extract all significant words, not just predefined spiritual terms
            words = re.findall(r'\b[a-zA-Z]+\b', translation.lower())

            # Add all meaningful words (length > 3, excluding common function words)
            function_words = {'that', 'this', 'with', 'from', 'they', 'them', 'have', 'been', 'were', 'will', 'would', 'could', 'should', 'their', 'there', 'where', 'when', 'what', 'which', 'whom', 'whose'}

            for word in words:
                if len(word) > 3 and word not in function_words:
                    keywords.add(word)

            # Add key concept mappings for better matching
            concept_mappings = {
                'action': ['karma', 'work', 'deed', 'activity', 'perform'],
                'duty': ['dharma', 'obligation', 'responsibility', 'right'],
                'fruits': ['results', 'consequences', 'outcomes', 'phala'],
                'attachment': ['clinging', 'desire', 'bondage', 'sangha'],
                'knowledge': ['jnana', 'wisdom', 'understanding', 'vidya'],
                'devotion': ['bhakti', 'worship', 'love', 'surrender'],
                'meditation': ['dhyana', 'contemplation', 'focus'],
                'consciousness': ['awareness', 'mind', 'spirit', 'atman']
            }

            for concept, synonyms in concept_mappings.items():
                if any(synonym in translation.lower() for synonym in synonyms):
                    keywords.add(concept)
                    keywords.update(synonyms)

        return ' '.join(sorted(keywords))

    def _save_to_json(self, verses: List[CachedVerse]):
        """Save verses to JSON file for persistence."""
        try:
            # Ensure data directory exists
            self.data_dir.mkdir(exist_ok=True)

            # Convert to JSON format
            json_data = []
            for verse in verses:
                json_data.append({
                    'source': verse.source,
                    'chapter': verse.chapter,
                    'verse': verse.verse,
                    'sanskrit': verse.sanskrit,
                    'transliteration': verse.transliteration,
                    'translation': verse.translation,
                    'keywords': verse.keywords
                })

            # Save with pretty formatting
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(verses)} verses to {self.json_path}")

        except Exception as e:
            logger.warning(f"Failed to save verses to JSON: {e}")
    
    def get_verse(self, chapter: int, verse: int) -> Optional[CachedVerse]:
        """Get a specific verse by chapter and verse number."""
        key = f"{chapter}.{verse}"
        return self.verses.get(key)
    
    def detect_verse_references(self, text: str) -> List[Tuple[int, int]]:
        """Detect verse references in multiple formats including ASR variations."""
        references = []

        # Enhanced patterns for various reference formats
        patterns = [
            # Standard formats: "BG 2.46", "Bhagavad Gita 2.46", "Gita 2.47"
            r'(?:BG|Bhagavad\s*Gita|Gita)\s*(\d+)\.(\d+)',

            # Chapter/verse formats: "chapter 2 verse 46", "ch 2 v 46"
            r'(?:chapter|ch\.?)\s*(\d+).*?(?:verse|v\.?)\s*(?:number\s+)?(\d+)',

            # Ordinal formats: "second chapter verse forty seven", "2nd chapter 47th verse"
            r'(?:(\d+)(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth)\s*chapter.*?(?:verse|sloka)\s*(?:number\s+)?(\d+)',

            # ASR variations: "gita to point forty seven", "chapter to verse forty seven"
            r'(?:gita|chapter)\s*(?:to|2)\s*(?:point|verse)\s*(\d+)',

            # Scriptural reference: "verse 2.47", "sloka 2.46"
            r'(?:verse|sloka|shloka)\s*(\d+)\.(\d+)',

            # Simple numeric: "2.47 of Gita", "Gita verse 2.47"
            r'(?:Gita\s*verse\s*|verse\s*)?(\d+)\.(\d+)(?:\s*of\s*(?:Gita|Bhagavad\s*Gita))?',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        chapter, verse = int(match.group(1)), int(match.group(2))
                        # Validate chapter/verse ranges for Bhagavad Gita
                        if 1 <= chapter <= 18 and 1 <= verse <= 78:  # Max verse is 78 in chapter 18
                            references.append((chapter, verse))
                except (ValueError, IndexError):
                    continue

        # Number word to digit conversion for ordinal chapters
        number_words = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
            'eleventh': 11, 'twelfth': 12, 'thirteenth': 13, 'fourteenth': 14,
            'fifteenth': 15, 'sixteenth': 16, 'seventeenth': 17, 'eighteenth': 18,
            'forty': 40, 'forty-seven': 47, 'forty-six': 46, 'thirty-two': 32
        }

        # Handle word-based references: "second chapter verse forty seven"
        word_pattern = r'(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth)\s*chapter.*?(?:verse|sloka)\s*(forty-seven|forty-six|thirty-two|\w+)'
        matches = re.finditer(word_pattern, text, re.IGNORECASE)
        for match in matches:
            chapter_word = match.group(1).lower()
            verse_word = match.group(2).lower()
            if chapter_word in number_words and verse_word in number_words:
                chapter, verse = number_words[chapter_word], number_words[verse_word]
                if 1 <= chapter <= 18 and 1 <= verse <= 78:
                    references.append((chapter, verse))

        # Remove duplicates while preserving order
        seen = set()
        unique_references = []
        for ref in references:
            if ref not in seen:
                seen.add(ref)
                unique_references.append(ref)

        return unique_references
    
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