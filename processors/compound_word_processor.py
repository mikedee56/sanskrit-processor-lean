"""
Intelligent Compound Word Processor for Sanskrit Terms
Handles cases like "Sapta Bhoomikaas" → "Sapta Bhūmikāḥ"
"""

import re
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SanskritCompoundProcessor:
    """Process Sanskrit compound words and multi-word terms."""
    
    def __init__(self):
        # Common Sanskrit number words
        self.number_words = {
            'sapta': 'sapta',  # seven
            'eka': 'eka',      # one
            'dvi': 'dvi',      # two
            'tri': 'tri',      # three
            'catur': 'catur',  # four
            'panch': 'pañca',  # five
            'shad': 'ṣaḍ',     # six
            'ashta': 'aṣṭa',   # eight
            'nava': 'nava',    # nine
            'dasha': 'daśa'    # ten
        }
        
        # Common Sanskrit compound elements
        self.compound_elements = {
            # Common prefixes
            'maha': 'mahā',
            'para': 'para',
            'adi': 'ādi', 
            'anta': 'anta',
            'su': 'su',
            'dur': 'dur',
            'upa': 'upa',
            'pra': 'pra',
            'sam': 'sam',
            'vi': 'vi',
            'ni': 'ni',
            'anu': 'anu',
            'ati': 'ati',
            'abhi': 'abhi',
            
            # Common suffixes  
            'ika': 'ikā',
            'tva': 'tva', 
            'tvam': 'tvam',
            'ana': 'ana',
            'yana': 'yāna',
            'sastra': 'śāstra',
            'vidya': 'vidyā',
            'gita': 'gītā',
            'purana': 'purāṇa',
            'sutra': 'sūtra',
            
            # Plural markers
            'aas': 'āḥ',
            'ās': 'āḥ', 
            'ah': 'āḥ'
        }
        
        # Common ASR compound splitting errors
        self.compound_corrections = {
            'yogavashistha': 'Yogavāsiṣṭha',
            'yoga vasistha': 'Yogavāsiṣṭha',
            'yogabashi': 'Yogavāsiṣṭha',
            'bhagavad gita': 'Bhagavad Gītā',
            'bhagvad geeta': 'Bhagavad Gītā',
            'mahabharata': 'Mahābhārata',
            'ramayana': 'Rāmāyaṇa',
            'advaita vedanta': 'Advaita Vedānta',
            'sankhya yoga': 'Sāṅkhya Yoga'
        }
    
    def process_compound_term(self, text: str) -> str:
        """Process a compound Sanskrit term."""
        text_lower = text.lower().strip()
        
        # Check direct compound corrections first
        if text_lower in self.compound_corrections:
            return self.compound_corrections[text_lower]
        
        # Try to process as compound word
        processed = self._process_compound_word(text)
        if processed != text:
            return processed
            
        # Try to process multi-word terms
        words = text.split()
        if len(words) > 1:
            processed_words = []
            for word in words:
                processed_word = self._process_single_word(word)
                processed_words.append(processed_word)
            return ' '.join(processed_words)
        
        return text
    
    def _process_compound_word(self, word: str) -> str:
        """Process a single compound word."""
        word_lower = word.lower()
        
        # Handle common patterns
        result = word
        
        # Number + noun patterns (e.g., "sapta bhoomikaas")
        for number, correct_num in self.number_words.items():
            if word_lower.startswith(number):
                remaining = word_lower[len(number):].strip()
                if remaining:
                    processed_remaining = self._process_single_word(remaining)
                    return f"{correct_num} {processed_remaining}"
        
        # Check for compound elements
        for element, correct in self.compound_elements.items():
            if element in word_lower:
                result = result.replace(element, correct)
        
        return result
    
    def _process_single_word(self, word: str) -> str:
        """Process a single Sanskrit word."""
        word_lower = word.lower().strip()
        
        # Handle plural forms
        if word_lower.endswith(('aas', 'ās', 'ah')) and len(word) > 4:
            # Common plurals like "bhoomikaas" → "bhūmikāḥ"
            base = word_lower[:-3] if word_lower.endswith('aas') else word_lower[:-2]
            
            # Apply transformations to base
            base_corrected = self._apply_diacritic_corrections(base)
            return base_corrected + 'āḥ'
        
        # Handle -tva suffix (e.g., "mumukshutva" → "mumukṣutva")
        if word_lower.endswith('tva'):
            base = word_lower[:-3]
            base_corrected = self._apply_diacritic_corrections(base)
            return base_corrected + 'tva'
            
        # Handle -tvam suffix  
        if word_lower.endswith('tvam'):
            base = word_lower[:-4]
            base_corrected = self._apply_diacritic_corrections(base)
            return base_corrected + 'tvam'
        
        # Apply general diacritic corrections
        return self._apply_diacritic_corrections(word)
    
    def _apply_diacritic_corrections(self, word: str) -> str:
        """Apply common diacritic corrections."""
        result = word.lower()
        
        # Common ASR→Sanskrit transformations
        corrections = {
            'bhoomi': 'bhūmi',
            'bhumi': 'bhūmi', 
            'mukti': 'mukti',
            'mukta': 'mukta',
            'shuddhi': 'śuddhi',
            'shanti': 'śānti',
            'dharma': 'dharma',
            'karma': 'karma',
            'yoga': 'yoga',
            'vairagya': 'vairāgya',
            'bhagavan': 'bhagavān',
            'purusha': 'puruṣa',
            'prakarana': 'prakaraṇa',
            'upanishad': 'upaniṣad',
            'samsaya': 'saṁśaya',
            'samadhan': 'samādhāna',
            'vashikara': 'vaśīkara',
            'vasistha': 'vaśiṣṭha',
            'shivashistha': 'śivaśiṣṭha', # though usually should be Vaśiṣṭha
            'manushya': 'manuṣya',
            'mumukshu': 'mumukṣu',
            'adhikari': 'adhikārī',
            'ekendriya': 'ekendriya',
            'yatamana': 'yatamāna'
        }
        
        for wrong, right in corrections.items():
            if wrong in result:
                result = result.replace(wrong, right)
        
        return result
    
    def find_compound_candidates(self, text: str) -> List[Tuple[str, str]]:
        """Find potential compound words in text that need processing."""
        candidates = []
        
        # Look for capitalized multi-word terms
        multi_word_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        matches = re.finditer(multi_word_pattern, text)
        
        for match in matches:
            original = match.group()
            processed = self.process_compound_term(original)
            if processed != original:
                candidates.append((original, processed))
        
        # Look for potential compound words (long words without spaces)
        long_word_pattern = r'\b[A-Za-z]{8,}\b'
        matches = re.finditer(long_word_pattern, text)
        
        for match in matches:
            original = match.group()
            processed = self.process_compound_term(original)
            if processed != original:
                candidates.append((original, processed))
        
        return candidates

if __name__ == "__main__":
    processor = SanskritCompoundProcessor()
    
    # Test with your examples
    test_cases = [
        "Sapta Bhoomikaas",
        "Utpati Prakarana", 
        "Yogabashi",
        "Shivashistha",
        "Bhagawan",
        "Jeevan Mukta",
        "Manushyatvam",
        "Mumukshutvam",
        "Mahapurusha Samsaya"
    ]
    
    print("=== COMPOUND WORD PROCESSING TESTS ===")
    for test in test_cases:
        result = processor.process_compound_term(test)
        print(f"{test} → {result}")