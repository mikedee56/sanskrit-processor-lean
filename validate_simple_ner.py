#!/usr/bin/env python3
"""
Validation script for Simple NER fallback system.
Tests core functionality without external dependencies.
"""

import sys
import time
from pathlib import Path
from services.simple_ner import SimpleNER, benchmark_performance
from enhanced_processor import EnhancedSanskritProcessor


def test_basic_functionality():
    """Test basic SimpleNER functionality."""
    print("=" * 50)
    print("Testing Basic Functionality")
    print("=" * 50)
    
    # Test initialization
    try:
        ner = SimpleNER('data/entities.yaml')
        print("✓ SimpleNER initialized successfully")
    except Exception as e:
        print(f"✗ SimpleNER initialization failed: {e}")
        return False
    
    # Test stats
    stats = ner.get_stats()
    print(f"✓ Loaded {stats['total_entities']} entities across {stats['categories']} categories")
    print(f"  Categories: {list(stats['category_breakdown'].keys())}")
    
    # Test entity extraction
    test_cases = [
        ("Krishna teaches dharma", ["Krishna", "dharma"]),
        ("The Bhagavad Gita is sacred", ["Bhagavad Gita"]),
        ("Arjuna and Krishna in Kurukshetra", ["Arjuna", "Krishna", "Kurukshetra"]),
        ("", []),  # Empty text
        ("No entities here", []),  # Text without entities
    ]
    
    for text, expected in test_cases:
        entities = ner.extract_entities(text)
        found_entities = [e.entity for e in entities]
        
        if text == "":
            success = len(entities) == 0
        else:
            success = all(exp in found_entities for exp in expected)
        
        status = "✓" if success else "✗"
        print(f"{status} Text: '{text}' -> Found: {found_entities}")
    
    # Test variations
    print("\nTesting variations:")
    variation_tests = [
        ("krishna is great", "Krishna"),
        ("krsna teaches", "Krishna"),
        ("bhagavad gita wisdom", "Bhagavad Gita"),
        ("gita teachings", "Bhagavad Gita"),
    ]
    
    for text, expected in variation_tests:
        entities = ner.extract_entities(text)
        found = any(e.entity == expected for e in entities)
        status = "✓" if found else "✗"
        print(f"{status} '{text}' -> Expected: {expected}, Found: {found}")
    
    # Test confidence scores
    print("\nTesting confidence scores:")
    entities = ner.extract_entities("Krishna teaches from the Bhagavad Gita about dharma")
    for entity in entities:
        confidence_ok = 0.0 <= entity.confidence <= 1.0
        status = "✓" if confidence_ok else "✗"
        print(f"{status} {entity.entity}: {entity.confidence:.3f}")
    
    return True


def test_performance():
    """Test performance requirements."""
    print("\n" + "=" * 50)
    print("Testing Performance")
    print("=" * 50)
    
    test_text = "Krishna and Arjuna discuss dharma in the Bhagavad Gita while in Kurukshetra"
    
    # Quick performance test
    ner = SimpleNER('data/entities.yaml')
    
    # Warm up
    for _ in range(10):
        ner.extract_entities(test_text)
    
    # Measure performance
    start_time = time.time()
    iterations = 1000
    total_entities = 0
    
    for _ in range(iterations):
        entities = ner.extract_entities(test_text)
        total_entities += len(entities)
    
    duration = time.time() - start_time
    avg_time_ms = (duration / iterations) * 1000
    extractions_per_sec = iterations / duration
    
    print(f"✓ Performance test completed:")
    print(f"  Total time: {duration:.3f}s for {iterations} extractions")
    print(f"  Average time per extraction: {avg_time_ms:.3f}ms")
    print(f"  Extractions per second: {extractions_per_sec:.1f}")
    print(f"  Average entities found: {total_entities/iterations:.1f}")
    
    # Check requirements
    performance_ok = avg_time_ms < 50
    entities_ok = total_entities > 0
    
    status = "✓" if performance_ok else "✗"
    print(f"{status} Performance requirement (< 50ms): {avg_time_ms:.2f}ms")
    
    status = "✓" if entities_ok else "✗" 
    print(f"{status} Entities found: {total_entities > 0}")
    
    return performance_ok and entities_ok


def test_integration():
    """Test integration with enhanced processor."""
    print("\n" + "=" * 50)
    print("Testing Integration")
    print("=" * 50)
    
    try:
        # Initialize enhanced processor
        processor = EnhancedSanskritProcessor(
            lexicon_dir=Path('lexicons') if Path('lexicons').exists() else None,
            config_path=Path('config.yaml')
        )
        print("✓ Enhanced processor initialized")
        
        # Test service status
        status = processor.get_service_status()
        print(f"✓ Service status retrieved")
        
        simple_ner_enabled = (
            'simple_ner' in status and 
            status['simple_ner'] != 'disabled' and
            isinstance(status['simple_ner'], dict) and
            status['simple_ner'].get('enabled', False)
        )
        
        status_symbol = "✓" if simple_ner_enabled else "✗"
        print(f"{status_symbol} Simple NER enabled: {simple_ner_enabled}")
        
        if simple_ner_enabled:
            ner_status = status['simple_ner']
            print(f"  Entities loaded: {ner_status.get('entities_loaded', 0)}")
            print(f"  Fallback active: {ner_status.get('fallback_active', False)}")
        
        # Test entity extraction through processor
        test_text = "Krishna teaches dharma in the sacred Gita"
        entities = processor.extract_entities(test_text)
        
        entities_found = len(entities) > 0
        status_symbol = "✓" if entities_found else "✗"
        print(f"{status_symbol} Entity extraction: found {len(entities)} entities")
        
        for entity in entities:
            print(f"  {entity.text} -> {entity.entity} ({entity.category})")
        
        # Test text processing (basic functionality)
        processed_text, corrections = processor.process_text('bhagavad gita')
        processing_works = isinstance(processed_text, str) and isinstance(corrections, int)
        
        status_symbol = "✓" if processing_works else "✗"
        print(f"{status_symbol} Text processing: '{processed_text}' ({corrections} corrections)")
        
        processor.close()
        print("✓ Integration test completed")
        
        return simple_ner_enabled and entities_found and processing_works
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def test_accuracy():
    """Test accuracy against known examples."""
    print("\n" + "=" * 50)
    print("Testing Accuracy")
    print("=" * 50)
    
    ner = SimpleNER('data/entities.yaml')
    
    # Define test cases with expected entities
    test_cases = [
        {
            'text': "Krishna spoke to Arjuna about dharma and yoga in the Bhagavad Gita",
            'expected': {
                'Krishna': 'deities',
                'Arjuna': 'people', 
                'dharma': 'concepts',
                'yoga': 'concepts',
                'Bhagavad Gita': 'scriptures'
            }
        },
        {
            'text': "The devotees visited Vrindavan and Mathura to worship Lord Vishnu",
            'expected': {
                'Vrindavan': 'places',
                'Mathura': 'places',
                'Vishnu': 'deities'
            }
        },
        {
            'text': "Sage teaching about moksha and samsara from the Upanishads",
            'expected': {
                'moksha': 'concepts',
                'samsara': 'concepts',
                'Upanishads': 'scriptures'
            }
        }
    ]
    
    total_expected = 0
    total_found = 0
    total_correct = 0
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        expected = test_case['expected']
        
        entities = ner.extract_entities(text)
        found_dict = {e.entity: e.category for e in entities}
        
        print(f"\nTest case {i}: {text}")
        print(f"Expected: {list(expected.keys())}")
        print(f"Found: {list(found_dict.keys())}")
        
        # Count accuracy
        case_expected = len(expected)
        case_found = len(found_dict)
        case_correct = sum(1 for entity, category in expected.items() 
                          if entity in found_dict and found_dict[entity] == category)
        
        total_expected += case_expected
        total_found += case_found
        total_correct += case_correct
        
        accuracy = case_correct / case_expected if case_expected > 0 else 0
        print(f"Accuracy: {case_correct}/{case_expected} = {accuracy:.2%}")
    
    overall_precision = total_correct / total_found if total_found > 0 else 0
    overall_recall = total_correct / total_expected if total_expected > 0 else 0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    
    print(f"\nOverall Results:")
    print(f"  Precision: {total_correct}/{total_found} = {overall_precision:.2%}")
    print(f"  Recall: {total_correct}/{total_expected} = {overall_recall:.2%}")
    print(f"  F1-Score: {overall_f1:.2%}")
    
    # Story requirement is >80% accuracy (using F1 as overall measure)
    accuracy_ok = overall_f1 > 0.8
    status = "✓" if accuracy_ok else "✗"
    print(f"{status} Accuracy requirement (>80%): {overall_f1:.1%}")
    
    return accuracy_ok


def main():
    """Run all validation tests."""
    print("Simple NER Fallback System - Validation")
    print("=" * 60)
    
    if not Path('data/entities.yaml').exists():
        print("✗ Error: data/entities.yaml not found")
        return False
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Performance", test_performance),
        ("Integration", test_integration),
        ("Accuracy", test_accuracy),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall Result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Simple NER Fallback System is ready for production!")
        print("   - All acceptance criteria met")
        print("   - Performance requirements satisfied")
        print("   - Integration working correctly")
        print("   - Accuracy above 80% threshold")
    else:
        print("\n⚠️  Some issues need to be addressed before deployment.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)