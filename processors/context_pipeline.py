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
        
        logger.info("Context-aware pipeline initialized with specialized processors")
    
    def _initialize_processors(self):
        """Initialize specialized processors from previous stories."""
        try:
            # Story 6.1: Compound Term Recognition
            from utils.compound_matcher import CompoundTermMatcher
            compounds_path = Path("lexicons/compounds.yaml")
            if compounds_path.exists():
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
        strategy = self.classifier.get_processing_strategy(classification)
        
        # Step 3: Initialize processing state
        processed_text = text
        all_corrections = []
        metadata = classification.metadata.copy() or {}
        specialized_results = {}
        
        # Step 4: Apply specialized processing in optimized order
        for processor_name in strategy['processor_order']:
            try:
                processor_start = time.time()
                
                if processor_name == 'compound' and 'compound' in self._processors:
                    processed_text, corrections = self._apply_compound_processing(
                        processed_text, strategy
                    )
                    all_corrections.extend(corrections)
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
                        processed_text, strategy
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
    
    def _apply_compound_processing(self, text: str, strategy: dict) -> Tuple[str, List[Dict]]:
        """Apply compound term recognition (Story 6.1)."""
        if not strategy.get('apply_fuzzy_matching', True):
            return text, []  # Skip for sacred content
            
        compound_processor = self._processors['compound']
        processed_text, matches = compound_processor.process_text(text)
        
        corrections = [
            {
                'type': 'compound',
                'original': match.get('original', ''),
                'corrected': match.get('corrected', ''),
                'confidence': match.get('confidence', 1.0)
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
        if classification.content_type in ['verse', 'mixed_verse']:
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
            'verse_formatted': classification.content_type in ['verse', 'mixed_verse'],
            'sacred_content_preserved': True
        }
        
        return final_text, metadata
    
    def _apply_database_processing(self, text: str, strategy: dict) -> Tuple[str, List[Dict]]:
        """Apply database + YAML lexicon processing (Story 6.3)."""
        database_processor = self._processors['database']
        
        # Extract individual words for processing
        import re
        words = text.split()
        corrected_words = []
        corrections = []
        
        for word in words:
            clean_word = re.sub(r'[^\\w\\s]', '', word.lower())
            
            # Try database lookup first
            if hasattr(database_processor, 'corrections'):
                if clean_word in database_processor.corrections:
                    entry = database_processor.corrections[clean_word]
                    corrected = entry.get('original_term', word)
                    
                    # Preserve capitalization if needed
                    if word[0].isupper() and not strategy['case_sensitive']:
                        corrected = corrected.capitalize()
                    
                    corrected_words.append(corrected)
                    corrections.append({
                        'type': 'lexicon',
                        'original': word,
                        'corrected': corrected,
                        'confidence': 1.0,
                        'source': 'database'
                    })
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    def _apply_scripture_processing(self, text: str, strategy: dict) -> Dict[str, Any]:
        """Apply scripture reference detection (Story 6.4)."""
        # This is a simplified implementation - actual scripture engine would be more complex
        import re
        
        scripture_references = []
        
        # Look for verse references like "2.47", "Chapter 2", etc.
        verse_pattern = r'\\b(\\d+)\\.(\\d+)\\b'
        chapter_pattern = r'\\bchapter\\s+(\\d+)\\b'
        
        for match in re.finditer(verse_pattern, text, re.IGNORECASE):
            scripture_references.append({
                'type': 'verse_reference',
                'chapter': match.group(1),
                'verse': match.group(2),
                'matched_text': match.group(0),
                'confidence': 0.9
            })
        
        for match in re.finditer(chapter_pattern, text, re.IGNORECASE):
            scripture_references.append({
                'type': 'chapter_reference', 
                'chapter': match.group(1),
                'matched_text': match.group(0),
                'confidence': 0.8
            })
        
        return {
            'scripture_references': scripture_references,
            'reference_count': len(scripture_references)
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