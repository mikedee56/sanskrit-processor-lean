"""
Context-aware processing pipeline for Sanskrit text.
Orchestrates specialized processors based on content classification.
Integrates Stories 6.1-6.4 into unified intelligent system.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .content_classifier import ContentClassifier, ContentClassification
from .compound_word_processor import SanskritCompoundProcessor
from utils.validation import InputValidator, DatabaseValidator

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Enhanced processing result with context awareness."""
    # Core processing results
    original_text: str
    processed_text: str
    corrections_made: int
    processing_time: float
    
    # Context-aware enhancements  
    content_type: str
    confidence: float
    corrections: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Quality tracking
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    specialized_processing: Dict[str, Any] = field(default_factory=dict)


class ContextAwarePipeline:
    """
    Main orchestration pipeline for context-aware Sanskrit processing.
    Routes content to appropriate specialized processors based on classification.
    """
    
    def __init__(self, config: dict):
        """Initialize pipeline with all specialized processors."""
        self.config = config
        self.processing_stats = {
            'classifications': 0,
            'by_type': {},
            'total_corrections': 0,
            'avg_confidence': 0.0
        }
        
        # Initialize content classifier
        self.classifier = ContentClassifier()
        
        # Initialize specialized processors (lazy loading for performance)
        self._processors = {}
        self._initialize_processors()
        
        # Initialize new systematic processors
        self.compound_processor = SanskritCompoundProcessor()
        
        # Initialize systematic term matcher
        try:
            from processors.systematic_term_matcher import SystematicTermMatcher
            self._processors['systematic'] = SystematicTermMatcher()
            logger.info("Systematic term matcher initialized in context pipeline")
        except ImportError as e:
            logger.warning(f"Systematic term matcher not available: {e}")
        
        logger.info("Context-aware pipeline initialized with specialized processors")

    def _preserve_case_pattern(self, original: str, corrected: str) -> str:
        """
        CRITICAL FIX: Preserve the original capitalization pattern in the corrected text.

        This prevents "Yoga Vasistha" from becoming "Yogavasistha" incorrectly.
        """
        original_words = original.split()
        corrected_words = corrected.split()

        # If word count differs, cannot preserve pattern - use corrected as is
        if len(original_words) != len(corrected_words):
            return corrected

        preserved_words = []
        for orig_word, corr_word in zip(original_words, corrected_words):
            # Preserve original capitalization pattern
            if orig_word.isupper():
                # All uppercase: "YOGA" → "VĀSIṢṬHA" (keep all caps)
                preserved_words.append(corr_word.upper())
            elif orig_word.istitle():
                # Title case: "Yoga" → "Vāsiṣṭha" (capitalize first letter)
                preserved_words.append(corr_word[0].upper() + corr_word[1:] if len(corr_word) > 0 else corr_word)
            elif orig_word.islower():
                # All lowercase: "yoga" → "vāsiṣṭha" (keep all lowercase)
                preserved_words.append(corr_word.lower())
            else:
                # Mixed case - use corrected as is
                preserved_words.append(corr_word)

        return ' '.join(preserved_words)

    def _initialize_processors(self):
        """Initialize specialized processors from previous stories."""
        try:
            # Story 6.1: Compound Term Recognition (Updated)
            from processors.compound_word_processor import SanskritCompoundProcessor
            self._processors['compound'] = SanskritCompoundProcessor()
            logger.info("Sanskrit compound processor initialized")
        except ImportError as e:
            logger.warning(f"Compound processor not available: {e}")
        
        try:
            # Legacy compound matcher fallback
            from utils.compound_matcher import CompoundTermMatcher
            compounds_path = Path("lexicons/compounds.yaml")
            if compounds_path.exists() and 'compound' not in self._processors:
                self._processors['compound'] = CompoundTermMatcher(compounds_path)
                logger.debug("Compound processor initialized")
            
        except ImportError as e:
            logger.warning(f"Compound processor not available: {e}")
        
        try:
            # Story 6.2: Sacred Text Preservation 
            from processors.sacred_classifier import SacredContentClassifier
            from processors.symbol_protector import SacredSymbolProtector
            from processors.verse_formatter import VerseFormatter
            
            self._processors['sacred'] = {
                'classifier': SacredContentClassifier(),
                'protector': SacredSymbolProtector(),
                'formatter': VerseFormatter()
            }
            logger.debug("Sacred text processors initialized")
            
        except ImportError as e:
            logger.warning(f"Sacred text processors not available: {e}")
        
        try:
            # Story 6.3: Database Integration
            from lexicons.hybrid_lexicon_loader import HybridLexiconLoader
            self._processors['database'] = HybridLexiconLoader(
                Path("lexicons"), self.config
            )
            logger.debug("Database processor initialized")
            
        except ImportError as e:
            logger.warning(f"Database processor not available: {e}")
        
        try:
            # Story 6.4: Scripture Reference Engine
            from scripture.reference_formatter import ReferenceFormatter
            self._processors['scripture'] = ReferenceFormatter()
            logger.debug("Scripture processor initialized")
            
        except ImportError as e:
            logger.warning(f"Scripture processor not available: {e}")
    
    def process_segment(self, text: str) -> ProcessingResult:
        """
        Main pipeline orchestration method.
        Classifies content and routes to appropriate specialized processors.
        """
        start_time = time.time()
        original_text = text
        
        # Step 1: Classify content type
        classification = self.classifier.classify_content(text)
        self._update_stats(classification)
        
        # Step 2: Get processing strategy
        strategy = self.classifier.get_processing_strategy(classification, text)
        
        # Step 3: Initialize processing state
        processed_text = text
        all_corrections = []
        metadata = classification.metadata.copy() or {}
        specialized_results = {}
        protected_ranges = []  # Track character ranges protected from further processing
        
        # Step 4: Apply specialized processing in optimized order
        for processor_name in strategy['processor_order']:
            try:
                processor_start = time.time()
                
                if processor_name == 'systematic' and 'systematic' in self._processors:
                    processed_text, corrections = self._apply_systematic_processing(
                        processed_text, strategy
                    )
                    all_corrections.extend(corrections)
                    specialized_results['systematic'] = {
                        'corrections': len(corrections),
                        'time': time.time() - processor_start
                    }
                
                elif processor_name == 'compound' and 'compound' in self._processors:
                    processed_text, corrections = self._apply_compound_processing(
                        processed_text, strategy
                    )
                    all_corrections.extend(corrections)
                    
                    # FIXED: Track character positions of compound corrections to prevent reprocessing
                    for correction in corrections:
                        # Find the position of the corrected text in the current processed_text
                        corrected = correction['corrected']
                        original = correction['original']
                        
                        # Find where this correction was applied in the text
                        if corrected in processed_text:
                            start_pos = processed_text.find(corrected)
                            end_pos = start_pos + len(corrected)
                            protected_ranges.append((start_pos, end_pos, original))
                    
                    specialized_results['compound'] = {
                        'corrections': len(corrections),
                        'time': time.time() - processor_start
                    }
                    
                elif processor_name == 'sacred' and 'sacred' in self._processors:
                    processed_text, sacred_metadata = self._apply_sacred_processing(
                        processed_text, strategy, classification
                    )
                    metadata.update(sacred_metadata)
                    specialized_results['sacred'] = {
                        'protected': sacred_metadata.get('symbols_protected', 0),
                        'time': time.time() - processor_start
                    }
                    
                elif processor_name == 'database' and 'database' in self._processors:
                    processed_text, corrections = self._apply_database_processing(
                        processed_text, strategy, protected_ranges
                    )
                    all_corrections.extend(corrections)
                    specialized_results['database'] = {
                        'corrections': len(corrections),
                        'time': time.time() - processor_start
                    }
                    
                elif processor_name == 'scripture' and 'scripture' in self._processors:
                    scripture_metadata = self._apply_scripture_processing(
                        processed_text, strategy
                    )
                    metadata.update(scripture_metadata)
                    specialized_results['scripture'] = {
                        'references': len(scripture_metadata.get('scripture_references', [])),
                        'time': time.time() - processor_start
                    }
                    
            except Exception as e:
                # Graceful fallback - log error but continue processing
                logger.warning(f"Processor {processor_name} failed: {e}")
                continue
        
        # Step 5: Calculate quality metrics
        processing_time = time.time() - start_time
        quality_metrics = self._calculate_quality_metrics(
            original_text, processed_text, all_corrections, processing_time
        )
        
        return ProcessingResult(
            original_text=original_text,
            processed_text=processed_text,
            corrections_made=len(all_corrections),
            processing_time=processing_time,
            content_type=classification.content_type,
            confidence=classification.confidence,
            corrections=all_corrections,
            metadata=metadata,
            quality_metrics=quality_metrics,
            specialized_processing=specialized_results
        )
    
    def _apply_systematic_processing(self, text: str, strategy: dict) -> Tuple[str, List[Dict]]:
        """Apply systematic term matching with scripture database."""
        systematic_processor = self._processors['systematic']
        processed_text, term_matches = systematic_processor.apply_corrections(text)
        
        corrections = [
            {
                'type': 'systematic',
                'original': match.original,
                'corrected': match.corrected,
                'confidence': match.confidence,
                'source': match.source,
                'match_type': match.match_type
            }
            for match in term_matches
        ]
        
        return processed_text, corrections
    
    def _apply_compound_processing(self, text: str, strategy: dict) -> Tuple[str, List[Dict]]:
        """Apply compound term recognition (Story 6.1)."""
        # ALWAYS apply compound processing since titles can appear in verses
        # The fuzzy_matching flag is for database processing, not compounds
            
        compound_processor = self._processors['compound']
        
        # Handle different compound processor types
        if hasattr(compound_processor, 'find_compound_candidates'):
            # New SanskritCompoundProcessor
            candidates = compound_processor.find_compound_candidates(text)
            processed_text = text
            corrections = []
            
            for original, corrected in candidates:
                if original != corrected:
                    # CRITICAL FIX: Preserve case pattern when applying compound corrections
                    # This prevents "Yoga Vasistha" -> "Yogavasistha" corruption
                    case_preserved_corrected = self._preserve_case_pattern(original, corrected)
                    processed_text = processed_text.replace(original, case_preserved_corrected)
                    corrections.append({
                        'type': 'compound',
                        'original': original,
                        'corrected': case_preserved_corrected,
                        'confidence': 0.85
                    })
            
            return processed_text, corrections
        else:
            # Legacy compound processor
            processed_text, matches = compound_processor.process_text(text)
        
        corrections = [
            {
                'type': 'compound',
                'original': match.original,
                'corrected': match.corrected,
                'confidence': match.confidence
            }
            for match in matches
        ]
        
        return processed_text, corrections
    
    def _apply_sacred_processing(
        self, text: str, strategy: dict, classification: ContentClassification
    ) -> Tuple[str, Dict[str, Any]]:
        """Apply sacred text preservation (Story 6.2)."""
        sacred_processors = self._processors['sacred']
        
        # Step 1: Protect sacred symbols
        if strategy['preserve_formatting']:
            protected_text, restoration_map = sacred_processors['protector'].protect_symbols(text)
        else:
            protected_text, restoration_map = text, {}
        
        # Step 2: Apply verse formatting if needed
        if classification.content_type in ['verse', 'mixed_verse', 'mantra']:
            formatted_text = sacred_processors['formatter'].process_verse(
                protected_text, classification.content_type
            )
        else:
            formatted_text = protected_text
        
        # Step 3: Restore symbols
        if restoration_map:
            final_text = sacred_processors['protector'].restore_symbols(
                formatted_text, restoration_map
            )
        else:
            final_text = formatted_text
        
        metadata = {
            'symbols_protected': len(restoration_map),
            'verse_formatted': classification.content_type in ['verse', 'mixed_verse', 'mantra'],
            'sacred_content_preserved': True
        }
        
        return final_text, metadata
    
    def _apply_database_processing(self, text: str, strategy: dict, protected_ranges: List[tuple] = None) -> Tuple[str, List[Dict]]:
        """Apply database + YAML lexicon processing (Story 6.3) - FIXED to match simple mode."""
        database_processor = self._processors['database']
        
        # Extract individual words for processing (preserve line structure)
        import re
        lines = text.split('\n')
        corrected_lines = []
        corrections = []
        
        for line in lines:
            words = line.split()
            corrected_words = []
            
            for word in words:
                # FIXED: Check if this word position is within any protected range
                word_start_in_text = text.find(word)
                word_end_in_text = word_start_in_text + len(word)
                is_protected = False
                
                if protected_ranges:
                    for prot_start, prot_end, original in protected_ranges:
                        if word_start_in_text >= prot_start and word_end_in_text <= prot_end:
                            is_protected = True
                            break
                
                if is_protected:
                    # Skip processing - word is already corrected by compound processor
                    corrected_words.append(word)
                else:
                    # FIXED: Pass the lexicon loader directly instead of calling it
                    corrected_word = self._process_word_with_punctuation(word, database_processor, strategy, protected_ranges)
                    corrected_words.append(corrected_word)
                    if corrected_word != word:
                        corrections.append({
                            'type': 'lexicon',
                            'original': word,
                            'corrected': corrected_word,
                            'confidence': 1.0,
                            'source': 'context_pipeline_fixed'
                        })
            
            corrected_lines.append(' '.join(corrected_words))
        
        return '\n'.join(corrected_lines), corrections
    
    def _process_word_with_punctuation(self, word: str, database_processor, strategy: dict, protected_ranges: List[tuple] = None) -> str:
        """Process word while preserving punctuation - FIXED to match simple mode logic."""
        import re
        
        # Extract leading/trailing punctuation
        match = re.match(r'^(\W*)(.*?)(\W*)$', word)
        if not match:
            return word
        
        prefix, clean_word, suffix = match.groups()
        
        # Skip empty words
        if not clean_word.strip():
            return word
            
        # Skip if no word characters
        if not re.search(r'\w', clean_word):
            return word
            
        clean_lower = clean_word.lower()
        
        # CRITICAL FIX: Use the SAME logic as simple mode's _apply_lexicon_corrections
        # Get the main processor's lexicons (should be HybridLexiconLoader)
        corrected = clean_word  # Default to original
        
        try:
            # Access the main processor's lexicons through the database_processor
            # The database_processor is actually the HybridLexiconLoader instance
            if hasattr(database_processor, 'corrections') and clean_lower in database_processor.corrections:
                entry = database_processor.corrections[clean_lower]
                
                # Apply transliterations with diacritics (same as simple mode)
                if isinstance(entry, dict):
                    if 'transliteration' in entry:
                        corrected = entry['transliteration']
                    elif 'original_term' in entry:
                        corrected = entry['original_term']
                    else:
                        corrected = entry.get('term', clean_word)
                else:
                    corrected = str(entry) if entry else clean_word
            
            # Also check proper nouns
            elif hasattr(database_processor, 'proper_nouns') and clean_lower in database_processor.proper_nouns:
                entry = database_processor.proper_nouns[clean_lower]
                if isinstance(entry, dict):
                    corrected = entry.get('term') or entry.get('original_term', clean_word)
                else:
                    corrected = str(entry) if entry else clean_word
        
        except Exception as e:
            # Graceful fallback
            corrected = clean_word
        
        # Apply intelligent capitalization preservation if correction was made
        if corrected != clean_word:
            # Simple capitalization preservation
            if clean_word.isupper():
                corrected = corrected.upper()
            elif clean_word.istitle():
                corrected = corrected.title()
            elif clean_word.islower():
                corrected = corrected.lower()
        
        return prefix + corrected + suffix
    
    def _apply_scripture_processing(self, text: str, strategy: dict) -> Dict[str, Any]:
        """Enhanced scripture reference detection using ScriptureReferenceEngine (Story 6.4)."""
        import re
        from pathlib import Path
        
        scripture_references = []
        verse_matches = []
        
        # Try to use enhanced scripture engine
        try:
            from scripture.verse_engine import ScriptureReferenceEngine
            
            # Initialize engine if not already done
            if not hasattr(self, '_scripture_engine'):
                db_path = Path("data/scripture_verses.db")
                self._scripture_engine = ScriptureReferenceEngine(db_path)
            
            # Use enhanced verse recognition
            threshold = strategy.get('confidence_threshold', 0.6)
            verse_matches = self._scripture_engine.identify_verses(text, threshold)
            
            # Convert to reference format
            for match in verse_matches:
                scripture_references.append({
                    'type': 'verse_match',
                    'source': match.source,
                    'chapter': match.chapter,
                    'verse': match.verse,
                    'matched_text': match.matched_text,
                    'confidence': match.confidence,
                    'citation': match.citation
                })
            
        except Exception as e:
            logger.warning(f"Enhanced scripture recognition failed: {e}, falling back to regex")
        
        # Fallback: Look for explicit verse references like "2.47", "Chapter 2", etc.
        verse_pattern = r'\b(\d+)\.(\d+)\b'
        chapter_pattern = r'\bchapter\s+(\d+)\b'
        
        for match in re.finditer(verse_pattern, text, re.IGNORECASE):
            scripture_references.append({
                'type': 'verse_reference',
                'chapter': int(match.group(1)),
                'verse': int(match.group(2)),
                'matched_text': match.group(0),
                'confidence': 0.9
            })
        
        for match in re.finditer(chapter_pattern, text, re.IGNORECASE):
            scripture_references.append({
                'type': 'chapter_reference', 
                'chapter': int(match.group(1)),
                'matched_text': match.group(0),
                'confidence': 0.8
            })
        
        # Calculate aggregate confidence
        avg_confidence = 0.0
        if scripture_references:
            confidences = [ref.get('confidence', 0.0) for ref in scripture_references]
            avg_confidence = sum(confidences) / len(confidences)
        
        return {
            'scripture_references': scripture_references,
            'reference_count': len(scripture_references),
            'verse_matches': len(verse_matches),
            'average_confidence': avg_confidence,
            'validated': len(verse_matches) > 0  # Mark as validated if we found verse matches
        }
    
    def _calculate_quality_metrics(
        self, original: str, processed: str, corrections: List, processing_time: float
    ) -> Dict[str, float]:
        """Calculate quality metrics for processing result."""
        return {
            'text_similarity': self._calculate_text_similarity(original, processed),
            'correction_density': len(corrections) / len(original.split()) if original.split() else 0,
            'processing_speed': len(original) / processing_time if processing_time > 0 else 0,
            'avg_correction_confidence': sum(c.get('confidence', 0) for c in corrections) / len(corrections) if corrections else 1.0
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Simple similarity calculation."""
        if text1 == text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        # Simple word-level similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _update_stats(self, classification: ContentClassification):
        """Update internal processing statistics."""
        self.processing_stats['classifications'] += 1
        content_type = classification.content_type
        self.processing_stats['by_type'][content_type] = self.processing_stats['by_type'].get(content_type, 0) + 1
        
        # Update rolling average confidence
        current_avg = self.processing_stats['avg_confidence']
        count = self.processing_stats['classifications']
        self.processing_stats['avg_confidence'] = (current_avg * (count - 1) + classification.confidence) / count
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Return comprehensive processing statistics."""
        classifier_stats = self.classifier.get_classification_stats()
        
        return {
            **self.processing_stats,
            'classifier_performance': classifier_stats,
            'available_processors': list(self._processors.keys())
        }
    
    def close(self):
        """Clean up resources."""
        if 'database' in self._processors:
            try:
                self._processors['database'].close()
            except Exception as e:
                logger.warning(f"Error closing database processor: {e}")