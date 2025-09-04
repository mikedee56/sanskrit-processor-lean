"""
Simple NER Fallback System for Sanskrit/Hindu context processing.

Provides basic Named Entity Recognition when MCP services are unavailable.
Uses rule-based pattern matching with YAML-based entity definitions.
"""

import re
import time
import yaml
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class EntityMatch:
    """Represents a matched entity in text."""
    text: str           # Original text found
    entity: str         # Canonical entity name
    category: str       # deity, scripture, concept, place, person
    confidence: float   # 0.0 - 1.0
    start_pos: int      # Position in original text
    end_pos: int        # End position
    source: str         # 'simple_ner' vs 'mcp'


class SimpleNER:
    """
    Simple Named Entity Recognition using pattern matching.
    
    Fast, rule-based approach for common Sanskrit/Hindu entities.
    Designed as fallback when MCP services are unavailable.
    """
    
    def __init__(self, entities_path: str):
        """Initialize with entity database path."""
        self.entities_path = Path(entities_path)
        self.entities = {}
        self.lookup_trie = {}
        self.category_map = {}
        
        # Load and build lookup structures
        self._load_entities()
        self._build_lookup_tables()
    
    def _load_entities(self) -> None:
        """Load entity definitions from YAML file."""
        try:
            with open(self.entities_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.entities = data.get('entities', {})
        except Exception as e:
            raise RuntimeError(f"Failed to load entities from {self.entities_path}: {e}")
    
    def _build_lookup_tables(self) -> None:
        """Pre-compute lookup structures for fast matching."""
        self.category_map = {}
        
        # Build category mapping for quick lookups
        for category, category_data in self.entities.items():
            if 'entities' not in category_data:
                continue
                
            for entity_info in category_data['entities']:
                canonical_name = entity_info['name']
                variations = [canonical_name.lower()] + [v.lower() for v in entity_info.get('variations', [])]
                
                for variation in variations:
                    if variation not in self.category_map:
                        self.category_map[variation] = []
                    
                    self.category_map[variation].append({
                        'canonical': canonical_name,
                        'category': category,
                        'confidence': category_data['confidence'],
                        'is_main': variation == canonical_name.lower()
                    })
    
    def extract_entities(self, text: str) -> List[EntityMatch]:
        """
        Extract named entities using pattern matching.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of EntityMatch objects found in text
        """
        if not text or not text.strip():
            return []
            
        entities = []
        text_lower = text.lower()
        
        # Find all potential matches
        for variation, entity_list in self.category_map.items():
            # Find all occurrences of this variation
            start = 0
            variation_len = len(variation)
            
            while True:
                pos = text_lower.find(variation, start)
                if pos == -1:
                    break
                
                # Check word boundaries to avoid partial matches
                if self._is_word_boundary(text_lower, pos, pos + variation_len):
                    for entity_info in entity_list:
                        confidence = self._calculate_confidence(
                            variation, entity_info['canonical'], entity_info['confidence'], entity_info['is_main']
                        )
                        
                        entities.append(EntityMatch(
                            text=text[pos:pos + variation_len],
                            entity=entity_info['canonical'],
                            category=entity_info['category'],
                            confidence=confidence,
                            start_pos=pos,
                            end_pos=pos + variation_len,
                            source='simple_ner'
                        ))
                
                start = pos + 1
        
        # Remove duplicates and overlaps, keep highest confidence
        return self._deduplicate_entities(entities)
    
    def batch_extract(self, texts: List[str]) -> List[List[EntityMatch]]:
        """
        Efficient batch processing of multiple texts.
        
        Args:
            texts: List of text strings to process
            
        Returns:
            List of entity lists, one per input text
        """
        return [self.extract_entities(text) for text in texts]
    
    def _is_word_boundary(self, text: str, start: int, end: int) -> bool:
        """
        Check if match is at word boundaries to avoid partial matches.
        
        Args:
            text: Full text (lowercase)
            start: Start position of match
            end: End position of match
            
        Returns:
            True if match is at proper word boundaries
        """
        # Check character before start
        if start > 0:
            prev_char = text[start - 1]
            if prev_char.isalnum() or prev_char in ['_', "'", '-']:
                return False
        
        # Check character after end  
        if end < len(text):
            next_char = text[end]
            if next_char.isalnum() or next_char in ['_', "'", '-']:
                return False
        
        return True
    
    def _calculate_confidence(self, variation: str, canonical: str, base_confidence: float, is_main: bool) -> float:
        """
        Calculate confidence score for a match.
        
        Args:
            variation: The variation that matched
            canonical: Canonical entity name
            base_confidence: Base confidence for this category
            is_main: Whether this is the main canonical form
            
        Returns:
            Adjusted confidence score
        """
        confidence = base_confidence
        
        # Boost confidence for exact canonical matches
        if is_main:
            confidence *= 1.1
        else:
            # Slightly reduce for variations
            confidence *= 0.95
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _deduplicate_entities(self, entities: List[EntityMatch]) -> List[EntityMatch]:
        """
        Remove duplicate and overlapping entities, keeping highest confidence.
        
        Args:
            entities: List of raw entity matches
            
        Returns:
            Deduplicated list with overlaps resolved
        """
        if not entities:
            return []
        
        # Sort by position, then by confidence (descending)
        entities.sort(key=lambda e: (e.start_pos, -e.confidence))
        
        final_entities = []
        
        for entity in entities:
            # Check for overlap with existing entities
            overlaps = False
            for existing in final_entities:
                if (entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    # Overlapping - keep higher confidence
                    if entity.confidence > existing.confidence:
                        # Remove lower confidence entity
                        final_entities.remove(existing)
                        break
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                final_entities.append(entity)
        
        # Sort final results by position
        return sorted(final_entities, key=lambda e: e.start_pos)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded entities.
        
        Returns:
            Dictionary with entity counts and categories
        """
        stats = {
            'categories': len(self.entities),
            'total_entities': 0,
            'total_variations': 0,
            'category_breakdown': {}
        }
        
        for category, category_data in self.entities.items():
            if 'entities' not in category_data:
                continue
                
            entity_count = len(category_data['entities'])
            variation_count = sum(
                len(entity.get('variations', [])) + 1  # +1 for canonical name
                for entity in category_data['entities']
            )
            
            stats['total_entities'] += entity_count
            stats['total_variations'] += variation_count
            stats['category_breakdown'][category] = {
                'entities': entity_count,
                'variations': variation_count,
                'confidence': category_data['confidence']
            }
        
        return stats


def benchmark_performance(entities_path: str, test_text: str, iterations: int = 1000) -> Dict[str, float]:
    """
    Benchmark SimpleNER performance.
    
    Args:
        entities_path: Path to entities.yaml
        test_text: Text to use for benchmarking
        iterations: Number of iterations to run
        
    Returns:
        Performance metrics dictionary
    """
    ner = SimpleNER(entities_path)
    
    # Warm up
    for _ in range(10):
        ner.extract_entities(test_text)
    
    # Benchmark
    start_time = time.time()
    total_entities = 0
    
    for _ in range(iterations):
        entities = ner.extract_entities(test_text)
        total_entities += len(entities)
    
    end_time = time.time()
    duration = end_time - start_time
    
    return {
        'total_time': duration,
        'avg_time_per_extraction': duration / iterations * 1000,  # milliseconds
        'extractions_per_second': iterations / duration,
        'total_entities_found': total_entities,
        'avg_entities_per_text': total_entities / iterations
    }


if __name__ == "__main__":
    # Quick test
    entities_path = "data/entities.yaml"
    test_text = "Krishna and Arjuna discuss dharma in the Bhagavad Gita while in Kurukshetra"
    
    print("Testing SimpleNER...")
    ner = SimpleNER(entities_path)
    
    print(f"Entity stats: {ner.get_stats()}")
    
    entities = ner.extract_entities(test_text)
    print(f"\nTest text: {test_text}")
    print(f"Found {len(entities)} entities:")
    
    for entity in entities:
        print(f"  {entity.text} -> {entity.entity} ({entity.category}, {entity.confidence:.2f})")
    
    # Quick benchmark
    print(f"\nBenchmarking...")
    metrics = benchmark_performance(entities_path, test_text, 100)
    print(f"Average time per extraction: {metrics['avg_time_per_extraction']:.2f}ms")
    print(f"Extractions per second: {metrics['extractions_per_second']:.1f}")