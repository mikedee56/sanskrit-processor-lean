#!/usr/bin/env python3
"""
Lean Sanskrit SRT Processor - Focused implementation
No bloat, no over-engineering, just working text processing.
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SRTSegment:
    """Simple SRT segment representation."""
    index: int
    start_time: str
    end_time: str
    text: str

@dataclass
class ProcessingResult:
    """Results from processing operation."""
    segments_processed: int
    corrections_made: int
    processing_time: float
    errors: List[str]

class LexiconLoader:
    """Simple lexicon loader for YAML files."""
    
    def __init__(self, lexicon_dir: Path):
        self.lexicon_dir = Path(lexicon_dir)
        self.corrections = {}
        self.proper_nouns = {}
        self._load_lexicons()
    
    def _load_lexicons(self):
        """Load correction lexicons from YAML files."""
        try:
            # Load corrections
            corrections_file = self.lexicon_dir / "corrections.yaml"
            if corrections_file.exists():
                with open(corrections_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    for entry in data.get('entries', []):
                        original = entry['original_term']
                        self.corrections[original] = entry
                        # Add variations
                        for variation in entry.get('variations', []):
                            self.corrections[variation] = entry
                logger.info(f"Loaded {len(self.corrections)} correction entries")
            
            # Load proper nouns
            proper_nouns_file = self.lexicon_dir / "proper_nouns.yaml"
            if proper_nouns_file.exists():
                with open(proper_nouns_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    for entry in data.get('entries', []):
                        # Handle both 'term' and 'original_term' formats
                        term = entry.get('term') or entry.get('original_term')
                        if term:
                            self.proper_nouns[term.lower()] = entry
                            # Add variations if they exist
                            for variation in entry.get('variations', []):
                                self.proper_nouns[variation.lower()] = entry
                logger.info(f"Loaded {len(self.proper_nouns)} proper noun entries")
                        
        except Exception as e:
            logger.error(f"Failed to load lexicons: {e}")
            raise

class SRTParser:
    """Simple SRT file parser."""
    
    @staticmethod
    def parse(content: str) -> List[SRTSegment]:
        """Parse SRT content into segments."""
        segments = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
                
            try:
                index = int(lines[0])
                timestamp = lines[1]
                text = '\n'.join(lines[2:])
                
                # Parse timestamp
                if ' --> ' not in timestamp:
                    continue
                    
                start_time, end_time = timestamp.split(' --> ')
                
                segments.append(SRTSegment(
                    index=index,
                    start_time=start_time.strip(),
                    end_time=end_time.strip(),
                    text=text.strip()
                ))
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipped malformed segment: {e}")
                continue
                
        return segments
    
    @staticmethod
    def to_srt(segments: List[SRTSegment]) -> str:
        """Convert segments back to SRT format."""
        srt_content = []
        
        for segment in segments:
            srt_content.append(f"{segment.index}")
            srt_content.append(f"{segment.start_time} --> {segment.end_time}")
            srt_content.append(segment.text)
            srt_content.append("")  # Empty line between segments
            
        return '\n'.join(srt_content)

class SanskritProcessor:
    """Lean Sanskrit text processor focused on core functionality."""
    
    def __init__(self, lexicon_dir: Path = None, config_path: Path = None):
        """Initialize processor with lexicon directory and configuration."""
        self.lexicon_dir = lexicon_dir or Path("lexicons")
        self.lexicons = LexiconLoader(self.lexicon_dir)
        
        # Load configuration
        self.config = self._load_config(config_path or Path("config.yaml"))
        
        # Basic text normalization patterns
        self.filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know']
        self.number_words = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
            'sixteen': '16', 'seventeen': '17', 'eighteen': '18'
        }
        
        logger.info("Sanskrit processor initialized")

    
    def _load_config(self, config_path: Path) -> dict:
        """Load configuration with fuzzy matching defaults."""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
            
            # Set fuzzy matching defaults
            if 'processing' not in config:
                config['processing'] = {}
            if 'fuzzy_matching' not in config['processing']:
                config['processing']['fuzzy_matching'] = {
                    'enabled': True,
                    'threshold': 0.7,
                    'log_matches': False
                }
            
            return config
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            return {
                'processing': {
                    'fuzzy_matching': {
                        'enabled': True,
                        'threshold': 0.7,
                        'log_matches': False
                    }
                }
            }
    
    def process_text(self, text: str) -> tuple[str, int]:
        """Process a single text segment. Returns (processed_text, corrections_made)."""
        original_text = text
        corrections = 0
        
        # 1. Basic text cleanup
        text = self._normalize_text(text)
        
        # 2. Apply lexicon corrections
        text, lexicon_corrections = self._apply_lexicon_corrections(text)
        corrections += lexicon_corrections
        
        # 3. Apply proper noun capitalization
        text, capitalization_corrections = self._apply_capitalization(text)
        corrections += capitalization_corrections
        
        # 4. Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text != original_text:
            logger.debug(f"Processed: '{original_text[:50]}...' -> '{text[:50]}...' ({corrections} corrections)")
            
        return text, corrections
    
    def _normalize_text(self, text: str) -> str:
        """Basic text normalization."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Convert number words to digits
        for word, digit in self.number_words.items():
            text = re.sub(rf'\b{re.escape(word)}\b', digit, text, flags=re.IGNORECASE)
        
        # Remove common filler words
        for filler in self.filler_words:
            text = re.sub(rf'\b{re.escape(filler)}\b', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
        """Apply corrections from lexicon files with fuzzy matching fallback."""
        corrections = 0
        words = text.split()
        corrected_words = []
        
        # Get fuzzy matching config
        fuzzy_config = self.config.get('processing', {}).get('fuzzy_matching', {})
        fuzzy_enabled = fuzzy_config.get('enabled', True)
        fuzzy_threshold = fuzzy_config.get('threshold', 0.8)
        log_fuzzy = fuzzy_config.get('log_matches', False)
        
        for word in words:
            # Clean word for lookup (remove punctuation)
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            # Try exact match first (existing logic)
            if clean_word in self.lexicons.corrections:
                entry = self.lexicons.corrections[clean_word]
                corrected = entry['original_term']
                
                # Preserve capitalization pattern
                if word[0].isupper():
                    corrected = corrected.capitalize()
                    
                corrected_words.append(corrected)
                corrections += 1
                logger.debug(f"Exact correction: {word} -> {corrected}")
                
            # Try fuzzy match if enabled and no exact match
            elif fuzzy_enabled and clean_word:
                fuzzy_match = self._find_fuzzy_match(clean_word, fuzzy_threshold)
                if fuzzy_match:
                    # Preserve capitalization pattern
                    if word[0].isupper():
                        fuzzy_match = fuzzy_match.capitalize()
                        
                    corrected_words.append(fuzzy_match)
                    corrections += 1
                    
                    if log_fuzzy:
                        logger.info(f"Fuzzy correction: {word} -> {fuzzy_match}")
                    else:
                        logger.debug(f"Fuzzy correction: {word} -> {fuzzy_match}")
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    def _apply_capitalization(self, text: str) -> tuple[str, int]:
        """Apply proper noun capitalization."""
        corrections = 0
        words = text.split()
        corrected_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            if clean_word in self.lexicons.proper_nouns:
                entry = self.lexicons.proper_nouns[clean_word]
                corrected = entry.get('term') or entry.get('original_term', word)
                corrected_words.append(corrected)
                corrections += 1
                logger.debug(f"Capitalization: {word} -> {corrected}")
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate character-based similarity ratio without external dependencies.
        Uses optimized character matching for ASR-style errors.
        """
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings (lowercase, strip punctuation)
        s1 = re.sub(r'[^\w]', '', str1.lower())
        s2 = re.sub(r'[^\w]', '', str2.lower())
        
        if not s1 or not s2:
            return 0.0
            
        if s1 == s2:
            return 1.0
        
        # Quick length check - very different lengths = low similarity
        len_diff = abs(len(s1) - len(s2))
        max_len = max(len(s1), len(s2))
        min_len = min(len(s1), len(s2))
        
        if len_diff / max_len > 0.5:  # More than 50% length difference
            return 0.0
        
        # Character-based similarity using multiple approaches
        # 1. Position-based matching (good for simple substitutions)
        position_matches = sum(1 for a, b in zip(s1, s2) if a == b)
        position_similarity = position_matches / max_len
        
        # 2. Character set intersection (good for reordering/missing chars)
        set1, set2 = set(s1), set(s2)
        common_chars = len(set1 & set2)
        total_unique = len(set1 | set2)
        set_similarity = common_chars / total_unique if total_unique > 0 else 0.0
        
        # 3. Length penalty
        length_similarity = 1.0 - (len_diff / max_len)
        
        # 4. Sequential character matching (handles insertions/deletions better)
        seq_matches = 0
        i = j = 0
        while i < len(s1) and j < len(s2):
            if s1[i] == s2[j]:
                seq_matches += 1
                i += 1
                j += 1
            elif len(s1) > len(s2):
                i += 1  # Skip character in longer string
            else:
                j += 1  # Skip character in longer string
        
        sequential_similarity = seq_matches / max_len
        
        # Combine similarities with weights optimized for ASR errors
        final_similarity = (
            position_similarity * 0.3 +      # Position matching
            set_similarity * 0.25 +          # Character overlap
            length_similarity * 0.2 +        # Length similarity
            sequential_similarity * 0.25     # Sequential matching
        )
        
        return min(1.0, final_similarity)

    def _find_fuzzy_match(self, word: str, threshold: float = 0.8) -> Optional[str]:
        """
        Find the best fuzzy match for a word in the lexicon.
        Returns the corrected term if similarity > threshold, None otherwise.
        """
        if not word or not self.lexicons.corrections:
            return None
            
        best_match = None
        best_similarity = 0.0
        
        for lexicon_term, entry in self.lexicons.corrections.items():
            similarity = self._calculate_similarity(word, lexicon_term)
            if similarity > threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = entry['original_term']
                
        return best_match
    
    def process_srt_file(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Process an SRT file with Sanskrit corrections."""
        import time
        start_time = time.time()
        
        logger.info(f"Processing SRT file: {input_path} -> {output_path}")
        
        try:
            # Read input file
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT
            segments = SRTParser.parse(content)
            if not segments:
                raise ValueError("No valid SRT segments found")
            
            logger.info(f"Parsed {len(segments)} segments")
            
            # Process each segment
            total_corrections = 0
            for segment in segments:
                processed_text, corrections = self.process_text(segment.text)
                segment.text = processed_text
                total_corrections += corrections
            
            # Write output file
            output_content = SRTParser.to_srt(segments)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                segments_processed=len(segments),
                corrections_made=total_corrections,
                processing_time=processing_time,
                errors=[]
            )
            
            logger.info(f"Processing complete: {len(segments)} segments, "
                       f"{total_corrections} corrections, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return ProcessingResult(
                segments_processed=0,
                corrections_made=0,
                processing_time=time.time() - start_time,
                errors=[str(e)]
            )

if __name__ == "__main__":
    # Simple test
    processor = SanskritProcessor()
    
    # Test text processing
    test_text = "Welcome to this bhagavad gita lecture on dharma and yoga"
    result, corrections = processor.process_text(test_text)
    print(f"Test: '{test_text}' -> '{result}' ({corrections} corrections)")