#!/usr/bin/env python3
"""
Unit tests for Simple NER Fallback System.

Tests core functionality, performance, and integration with enhanced processor.
"""

import pytest
import time
import tempfile
import yaml
from pathlib import Path
from services.simple_ner import SimpleNER, EntityMatch, benchmark_performance


class TestSimpleNER:
    """Test cases for Simple NER functionality."""
    
    @pytest.fixture
    def sample_entities_file(self):
        """Create temporary entities file for testing."""
        sample_data = {
            'entities': {
                'deities': {
                    'confidence': 0.9,
                    'entities': [
                        {
                            'name': 'Krishna',
                            'variations': ['krishna', 'krsna', 'kṛṣṇa'],
                            'category': 'deity'
                        },
                        {
                            'name': 'Shiva',
                            'variations': ['shiva', 'siva', 'śiva'],
                            'category': 'deity'
                        }
                    ]
                },
                'scriptures': {
                    'confidence': 0.95,
                    'entities': [
                        {
                            'name': 'Bhagavad Gita',
                            'variations': ['bhagavad gita', 'gita', 'bhagvad geeta'],
                            'category': 'scripture'
                        }
                    ]
                },
                'concepts': {
                    'confidence': 0.85,
                    'entities': [
                        {
                            'name': 'dharma',
                            'variations': ['dharma', 'righteous duty'],
                            'category': 'concept'
                        }
                    ]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_data, f)
            return f.name
    
    def test_initialization(self, sample_entities_file):
        """Test SimpleNER initialization."""
        ner = SimpleNER(sample_entities_file)
        
        assert ner.entities is not None
        assert len(ner.entities) == 3
        assert 'deities' in ner.entities
        assert 'scriptures' in ner.entities
        assert 'concepts' in ner.entities
    
    def test_deity_detection(self, sample_entities_file):
        """Test detection of deity entities."""
        ner = SimpleNER(sample_entities_file)
        entities = ner.extract_entities("Krishna and Shiva are important deities")
        
        assert len(entities) == 2
        
        # Check Krishna
        krishna_entities = [e for e in entities if e.entity == "Krishna"]
        assert len(krishna_entities) == 1
        assert krishna_entities[0].category == "deity"
        assert krishna_entities[0].confidence > 0.8
        assert krishna_entities[0].source == "simple_ner"
        
        # Check Shiva
        shiva_entities = [e for e in entities if e.entity == "Shiva"]
        assert len(shiva_entities) == 1
        assert shiva_entities[0].category == "deity"
        assert shiva_entities[0].confidence > 0.8
    
    def test_scripture_recognition(self, sample_entities_file):
        """Test recognition of scripture entities."""
        ner = SimpleNER(sample_entities_file)
        entities = ner.extract_entities("The Bhagavad Gita teaches us about dharma")
        
        scripture_entities = [e for e in entities if e.category == "scripture"]
        concept_entities = [e for e in entities if e.category == "concept"]
        
        assert len(scripture_entities) == 1
        assert len(concept_entities) == 1
        
        assert scripture_entities[0].entity == "Bhagavad Gita"
        assert concept_entities[0].entity == "dharma"
    
    def test_variations_matching(self, sample_entities_file):
        """Test matching of entity variations."""
        ner = SimpleNER(sample_entities_file)
        
        # Test Krishna variations
        test_texts = [
            "krishna is great",
            "krsna teaches",
            "kṛṣṇa shows the way"
        ]
        
        for text in test_texts:
            entities = ner.extract_entities(text)
            assert len(entities) == 1
            assert entities[0].entity == "Krishna"
            assert entities[0].category == "deity"
    
    def test_word_boundary_checking(self, sample_entities_file):
        """Test that partial matches are avoided."""
        ner = SimpleNER(sample_entities_file)
        
        # Should not match 'Krishna' in 'Krishnanda'
        entities = ner.extract_entities("Krishnanda is a name")
        assert len(entities) == 0
        
        # Should match 'Krishna' with punctuation
        entities = ner.extract_entities("Krishna, the divine teacher")
        assert len(entities) == 1
        assert entities[0].entity == "Krishna"
    
    def test_case_insensitive_matching(self, sample_entities_file):
        """Test case insensitive matching."""
        ner = SimpleNER(sample_entities_file)
        
        test_cases = [
            "KRISHNA is divine",
            "Krishna is divine",
            "krishna is divine"
        ]
        
        for text in test_cases:
            entities = ner.extract_entities(text)
            assert len(entities) == 1
            assert entities[0].entity == "Krishna"
    
    def test_overlapping_entities(self, sample_entities_file):
        """Test handling of overlapping entity matches."""
        # This is a more complex test case that would require overlapping entities
        # in the test data to be meaningful
        ner = SimpleNER(sample_entities_file)
        
        # For now, test that no exceptions are raised
        entities = ner.extract_entities("Krishna Krishna teaches dharma")
        # Should handle duplicate matches properly
        krishna_count = len([e for e in entities if e.entity == "Krishna"])
        assert krishna_count >= 1  # At least one Krishna should be found
    
    def test_empty_text_handling(self, sample_entities_file):
        """Test handling of empty or None text."""
        ner = SimpleNER(sample_entities_file)
        
        assert ner.extract_entities("") == []
        assert ner.extract_entities("   ") == []
        assert ner.extract_entities(None) == []
    
    def test_batch_processing(self, sample_entities_file):
        """Test batch processing functionality."""
        ner = SimpleNER(sample_entities_file)
        
        texts = [
            "Krishna teaches dharma",
            "Shiva is the destroyer",
            "The Bhagavad Gita is a scripture"
        ]
        
        results = ner.batch_extract(texts)
        
        assert len(results) == 3
        assert len(results[0]) >= 2  # Krishna + dharma
        assert len(results[1]) >= 1  # Shiva
        assert len(results[2]) >= 1  # Bhagavad Gita
    
    def test_confidence_scores(self, sample_entities_file):
        """Test confidence scoring."""
        ner = SimpleNER(sample_entities_file)
        entities = ner.extract_entities("Krishna teaches from the Bhagavad Gita about dharma")
        
        # Check confidence ranges
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0
        
        # Scriptures should have higher confidence than concepts
        scripture_entities = [e for e in entities if e.category == "scripture"]
        concept_entities = [e for e in entities if e.category == "concept"]
        
        if scripture_entities and concept_entities:
            assert scripture_entities[0].confidence > concept_entities[0].confidence
    
    def test_position_tracking(self, sample_entities_file):
        """Test that entity positions are correctly tracked."""
        ner = SimpleNER(sample_entities_file)
        text = "Krishna teaches dharma"
        entities = ner.extract_entities(text)
        
        for entity in entities:
            # Check that positions are valid
            assert 0 <= entity.start_pos < len(text)
            assert entity.start_pos < entity.end_pos <= len(text)
            
            # Check that extracted text matches position
            extracted = text[entity.start_pos:entity.end_pos]
            assert extracted.lower() == entity.text.lower()
    
    def test_get_stats(self, sample_entities_file):
        """Test statistics reporting."""
        ner = SimpleNER(sample_entities_file)
        stats = ner.get_stats()
        
        assert 'categories' in stats
        assert 'total_entities' in stats
        assert 'total_variations' in stats
        assert 'category_breakdown' in stats
        
        assert stats['categories'] == 3
        assert stats['total_entities'] > 0
        assert stats['total_variations'] > stats['total_entities']
        
        assert 'deities' in stats['category_breakdown']
        assert 'scriptures' in stats['category_breakdown']
        assert 'concepts' in stats['category_breakdown']


class TestPerformance:
    """Performance tests for Simple NER."""
    
    @pytest.fixture
    def sample_entities_file(self):
        """Create entities file for performance testing."""
        # Use the main entities file if available, otherwise create minimal one
        main_entities_file = Path("data/entities.yaml")
        if main_entities_file.exists():
            return str(main_entities_file)
        
        # Fallback minimal file
        minimal_data = {
            'entities': {
                'deities': {
                    'confidence': 0.9,
                    'entities': [
                        {'name': 'Krishna', 'variations': ['krishna'], 'category': 'deity'},
                        {'name': 'Shiva', 'variations': ['shiva'], 'category': 'deity'}
                    ]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(minimal_data, f)
            return f.name
    
    def test_single_extraction_performance(self, sample_entities_file):
        """Test performance of single entity extraction."""
        ner = SimpleNER(sample_entities_file)
        test_text = "Krishna and Shiva discuss dharma in the sacred texts"
        
        # Warm up
        for _ in range(10):
            ner.extract_entities(test_text)
        
        # Measure performance
        start_time = time.time()
        for _ in range(100):
            entities = ner.extract_entities(test_text)
        end_time = time.time()
        
        avg_time_ms = (end_time - start_time) / 100 * 1000
        
        # Should extract entities in less than 50ms (story requirement)
        assert avg_time_ms < 50, f"Average extraction time {avg_time_ms:.2f}ms exceeds 50ms limit"
        
        # Should find at least some entities
        entities = ner.extract_entities(test_text)
        assert len(entities) > 0
    
    def test_batch_processing_efficiency(self, sample_entities_file):
        """Test that batch processing is efficient."""
        ner = SimpleNER(sample_entities_file)
        
        texts = ["Krishna teaches dharma"] * 50
        
        # Time individual processing
        start_time = time.time()
        individual_results = [ner.extract_entities(text) for text in texts]
        individual_time = time.time() - start_time
        
        # Time batch processing
        start_time = time.time()
        batch_results = ner.batch_extract(texts)
        batch_time = time.time() - start_time
        
        # Results should be equivalent
        assert len(individual_results) == len(batch_results)
        
        # Batch processing doesn't need to be faster (it's just a convenience method)
        # but it shouldn't be significantly slower
        assert batch_time <= individual_time * 1.1  # Allow 10% overhead
    
    @pytest.mark.skipif(not Path("data/entities.yaml").exists(), 
                       reason="Main entities file not available")
    def test_benchmark_with_main_entities(self):
        """Benchmark performance with the main entities database."""
        test_text = "Krishna and Arjuna discuss dharma in the Bhagavad Gita while in Kurukshetra"
        
        metrics = benchmark_performance("data/entities.yaml", test_text, 100)
        
        # Check performance requirements
        assert metrics['avg_time_per_extraction'] < 50, \
            f"Avg extraction time {metrics['avg_time_per_extraction']:.2f}ms exceeds requirement"
        
        assert metrics['extractions_per_second'] > 20, \
            f"Only {metrics['extractions_per_second']:.1f} extractions/sec, need >20"
        
        # Should find multiple entities in the test text
        assert metrics['avg_entities_per_text'] >= 4, \
            f"Only found {metrics['avg_entities_per_text']:.1f} entities on average"


class TestIntegration:
    """Integration tests with enhanced processor."""
    
    @pytest.mark.skipif(not Path("data/entities.yaml").exists(), 
                       reason="Main entities file not available")
    def test_enhanced_processor_integration(self):
        """Test integration with enhanced processor."""
        from enhanced_processor import EnhancedSanskritProcessor
        
        # Initialize with minimal config to avoid external dependencies
        config_data = {
            'mcp': {'enabled': False},
            'external_apis': {'enabled': False},
            'ner': {
                'fallback': {
                    'enabled': True,
                    'entities_file': 'data/entities.yaml',
                    'log_fallback_usage': False
                }
            }
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            processor = EnhancedSanskritProcessor(
                lexicon_dir=Path("lexicons"),
                config_path=Path(config_path)
            )
            
            # Test entity extraction
            entities = processor.extract_entities("Krishna teaches dharma in the Gita")
            
            assert len(entities) > 0
            entity_names = [e.entity for e in entities]
            assert "Krishna" in entity_names
            
            # Test service status
            status = processor.get_service_status()
            assert status['simple_ner']['enabled'] is True
            assert status['simple_ner']['entities_loaded'] > 0
            
            processor.close()
            
        finally:
            Path(config_path).unlink()
    
    def test_fallback_activation_logging(self, caplog):
        """Test that fallback activation is properly logged."""
        import logging
        
        config_data = {
            'mcp': {'enabled': False},
            'external_apis': {'enabled': False},
            'ner': {
                'fallback': {
                    'enabled': True,
                    'entities_file': 'data/entities.yaml',
                    'log_fallback_usage': True
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Set up logging
            caplog.set_level(logging.INFO)
            
            from enhanced_processor import EnhancedSanskritProcessor
            processor = EnhancedSanskritProcessor(
                lexicon_dir=Path("lexicons") if Path("lexicons").exists() else None,
                config_path=Path(config_path)
            )
            
            # This should trigger fallback usage log
            processor.extract_entities("Krishna teaches")
            
            # Check that initialization and fallback usage were logged
            log_messages = [record.message for record in caplog.records]
            assert any("Simple NER fallback initialized" in msg for msg in log_messages)
            
            processor.close()
            
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    # Run basic tests if called directly
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick test mode
        entities_file = "data/entities.yaml"
        if not Path(entities_file).exists():
            print(f"Error: {entities_file} not found")
            sys.exit(1)
        
        print("Running quick SimpleNER tests...")
        
        ner = SimpleNER(entities_file)
        test_text = "Krishna and Arjuna discuss dharma in the Bhagavad Gita"
        
        entities = ner.extract_entities(test_text)
        print(f"Found {len(entities)} entities in: '{test_text}'")
        
        for entity in entities:
            print(f"  {entity.text} -> {entity.entity} ({entity.category}, conf:{entity.confidence:.2f})")
        
        # Quick benchmark
        metrics = benchmark_performance(entities_file, test_text, 50)
        print(f"\nPerformance: {metrics['avg_time_per_extraction']:.2f}ms per extraction")
        
        print("Quick tests completed successfully!")
    else:
        pytest.main([__file__, "-v"])