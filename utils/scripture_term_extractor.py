"""
Systematic Sanskrit Term Extractor from Scripture Databases
Solves the root problem: extracts real Sanskrit terms from actual scriptures
instead of relying on synthetic database entries.
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class ScriptureTermExtractor:
    """Extract Sanskrit terms systematically from scripture databases."""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = Path(data_dir or "data")
        self.scripture_files = [
            "bhagavad_gita_verses.json",
            "upanishad_verses.json", 
            "yoga_sutras_verses.json",
            "additional_verses.json"
        ]
        
        # Sanskrit word patterns for extraction
        self.sanskrit_patterns = [
            r'\b[a-zA-Z]*[āīūṛṝḷḹēōḥṃṁṅṇṭḍṇśṣñ]+[a-zA-Z]*\b',  # Words with diacritics
            r'\b[kgcjṭdtpbyrlvśṣsh][a-zA-Z]{2,}\b',  # Sanskrit consonant patterns
            r'\b[aeiouāīūṛṝḷḹēō][a-zA-Z]{2,}\b'  # Sanskrit vowel patterns
        ]
        
        # Common ASR corruptions for learning patterns
        self.known_corruptions = {
            'ṇ': 'n', 'ṃ': 'm', 'ṁ': 'n', 'ṛ': 'r', 'ṝ': 'r',
            'ṭ': 't', 'ḍ': 'd', 'ś': 'sh', 'ṣ': 's', 'ḥ': 'h',
            'ā': 'aa', 'ī': 'ii', 'ū': 'uu', 'ē': 'e', 'ō': 'o'
        }
    
    def extract_terms_from_scripture(self, scripture_file: str) -> Dict[str, List[str]]:
        """Extract Sanskrit terms from a scripture JSON file."""
        file_path = self.data_dir / scripture_file
        if not file_path.exists():
            logger.warning(f"Scripture file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                verses = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {scripture_file}: {e}")
            return {}
        
        terms = {}
        for verse in verses:
            # Extract from Sanskrit text
            sanskrit = verse.get('sanskrit', '')
            transliteration = verse.get('transliteration', '')
            keywords = verse.get('keywords', '')
            
            # Find Sanskrit words in transliteration (most reliable)
            if transliteration:
                words = self._extract_sanskrit_words(transliteration)
                for word in words:
                    if word not in terms:
                        terms[word] = []
                    terms[word].append({
                        'source': verse.get('source', 'Unknown'),
                        'chapter': verse.get('chapter'),
                        'verse': verse.get('verse'),
                        'context': transliteration[:50] + '...'
                    })
            
            # Extract from keywords
            if keywords:
                keyword_list = [k.strip() for k in keywords.split() if len(k.strip()) > 3]
                for keyword in keyword_list:
                    if self._is_sanskrit_word(keyword):
                        if keyword not in terms:
                            terms[keyword] = []
                        terms[keyword].append({
                            'source': verse.get('source', 'Unknown'),
                            'type': 'keyword',
                            'context': keywords
                        })
        
        logger.info(f"Extracted {len(terms)} terms from {scripture_file}")
        return terms
    
    def _extract_sanskrit_words(self, text: str) -> Set[str]:
        """Extract Sanskrit words from transliterated text."""
        words = set()
        
        # Split on common delimiters
        text_clean = re.sub(r'[।॥|\.,-]', ' ', text)
        potential_words = text_clean.split()
        
        for word in potential_words:
            word = word.strip('()[]{}\'\".,;:')
            if self._is_sanskrit_word(word):
                words.add(word.lower())
        
        return words
    
    def _is_sanskrit_word(self, word: str) -> bool:
        """Check if a word appears to be Sanskrit."""
        if len(word) < 3:
            return False
        
        # Must contain diacritics or Sanskrit patterns
        has_diacritics = any(char in word for char in 'āīūṛṝḷḹēōḥṃṁṅṇṭḍṇśṣñ')
        
        # Or common Sanskrit word patterns
        sanskrit_endings = ['am', 'an', 'as', 'at', 'ah', 'ya', 'va', 'ma', 'na', 'ta', 'ra']
        has_sanskrit_ending = any(word.endswith(ending) for ending in sanskrit_endings)
        
        # Or starts with Sanskrit consonant clusters
        sanskrit_starts = ['pr', 'kr', 'tr', 'dr', 'br', 'gr', 'shr', 'thr', 'dhr', 'bhr']
        has_sanskrit_start = any(word.startswith(start) for start in sanskrit_starts)
        
        return has_diacritics or (has_sanskrit_ending and len(word) > 4) or has_sanskrit_start
    
    def generate_asr_variations(self, sanskrit_word: str) -> List[str]:
        """Generate common ASR corruptions for a Sanskrit word."""
        variations = [sanskrit_word]
        
        # Apply known corruptions
        corrupted = sanskrit_word
        for sanskrit_char, english_char in self.known_corruptions.items():
            corrupted = corrupted.replace(sanskrit_char, english_char)
        
        if corrupted != sanskrit_word:
            variations.append(corrupted)
        
        # Common compound splitting errors
        if len(sanskrit_word) > 6:
            # Try splitting at common points
            mid = len(sanskrit_word) // 2
            split_variations = [
                sanskrit_word[:mid] + ' ' + sanskrit_word[mid:],
                sanskrit_word[:mid-1] + ' ' + sanskrit_word[mid-1:],
                sanskrit_word[:mid+1] + ' ' + sanskrit_word[mid+1:]
            ]
            variations.extend([v for v in split_variations if ' ' in v])
        
        return list(set(variations))
    
    def extract_all_scripture_terms(self) -> Dict[str, Dict]:
        """Extract all Sanskrit terms from all scripture files."""
        all_terms = {}
        
        for scripture_file in self.scripture_files:
            file_terms = self.extract_terms_from_scripture(scripture_file)
            
            for term, contexts in file_terms.items():
                if term not in all_terms:
                    all_terms[term] = {
                        'transliteration': term,
                        'variations': self.generate_asr_variations(term),
                        'contexts': contexts,
                        'category': self._categorize_term(term, contexts),
                        'confidence': self._calculate_confidence(contexts)
                    }
                else:
                    # Merge contexts
                    all_terms[term]['contexts'].extend(contexts)
        
        logger.info(f"Extracted {len(all_terms)} unique Sanskrit terms from all scriptures")
        return all_terms
    
    def _categorize_term(self, term: str, contexts: List[Dict]) -> str:
        """Categorize a Sanskrit term based on context."""
        # Simple categorization based on common patterns
        if any('gita' in ctx.get('source', '').lower() for ctx in contexts):
            return 'bhagavad_gita'
        elif any('upanishad' in ctx.get('source', '').lower() for ctx in contexts):
            return 'upanishad'
        elif any('yoga' in ctx.get('source', '').lower() for ctx in contexts):
            return 'yoga_sutra'
        else:
            return 'scripture'
    
    def _calculate_confidence(self, contexts: List[Dict]) -> float:
        """Calculate confidence based on frequency and source diversity."""
        frequency = len(contexts)
        source_diversity = len(set(ctx.get('source', '') for ctx in contexts))
        
        # Higher confidence for terms appearing frequently across multiple sources
        confidence = min(0.95, 0.5 + (frequency * 0.1) + (source_diversity * 0.1))
        return confidence
    
    def update_corrections_yaml(self, output_file: Path = None):
        """Update corrections.yaml with extracted scripture terms."""
        output_file = output_file or Path("lexicons/corrections_with_scripture.yaml")
        
        # Extract all terms
        scripture_terms = self.extract_all_scripture_terms()
        
        # Load existing corrections
        existing_corrections = Path("lexicons/corrections.yaml")
        if existing_corrections.exists():
            import yaml
            with open(existing_corrections, 'r', encoding='utf-8') as f:
                existing_data = yaml.safe_load(f)
        else:
            existing_data = {'entries': []}
        
        # Add scripture terms
        added_count = 0
        existing_terms = {entry['original_term'].lower() for entry in existing_data['entries']}
        
        for term, data in scripture_terms.items():
            if term.lower() not in existing_terms:
                entry = {
                    'original_term': term,
                    'variations': data['variations'],
                    'transliteration': data['transliteration'],
                    'is_proper_noun': False,
                    'category': data['category'],
                    'confidence': data['confidence'],
                    'source_authority': 'Scripture',
                    'difficulty_level': 'intermediate',
                    'meaning': f"Sanskrit term from {data['category']}"
                }
                existing_data['entries'].append(entry)
                added_count += 1
        
        # Save updated corrections
        with open(output_file, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Added {added_count} new scripture terms to {output_file}")
        return added_count

if __name__ == "__main__":
    extractor = ScriptureTermExtractor()
    
    # Extract and display sample terms
    terms = extractor.extract_all_scripture_terms()
    
    print("=== SAMPLE EXTRACTED TERMS ===")
    for i, (term, data) in enumerate(list(terms.items())[:10]):
        print(f"{term}: {data['variations'][:3]} (confidence: {data['confidence']:.2f})")
    
    print(f"\nTotal extracted terms: {len(terms)}")
    
    # Update corrections file
    added = extractor.update_corrections_yaml()
    print(f"Added {added} new scripture terms to corrections file")