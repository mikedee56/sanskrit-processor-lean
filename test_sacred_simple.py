#!/usr/bin/env python3
"""
Simple test script to validate sacred content preservation functionality.
Runs without pytest dependency.
"""

import sys
from pathlib import Path
sys.path.append('.')

# Import the main processor and sacred content components
from sanskrit_processor_v2 import SanskritProcessor
from processors.sacred_classifier import SacredContentClassifier
from processors.symbol_protector import SacredSymbolProtector
from processors.verse_formatter import VerseFormatter

def test_sacred_symbol_preservation():
    """Test critical sacred symbol preservation."""
    print("🔥 Testing Sacred Symbol Preservation...")
    
    processor = SanskritProcessor(Path("lexicons"))
    
    # Critical Test 1: Pipe symbols never become question marks
    test_text = "Om pūrṇam adaḥ pūrṇam idam | pūrṇāt pūrṇam udacyate ||"
    result, corrections = processor.process_text(test_text)
    
    print(f"Input:  {test_text}")
    print(f"Output: {result}")
    
    # Assertions
    assert "|" in result, "❌ CRITICAL FAILURE: Single pipe missing"
    assert "||" in result, "❌ CRITICAL FAILURE: Double pipe missing"  
    assert "?" not in result, "❌ CRITICAL FAILURE: Sacred symbols corrupted to ?"
    
    print("✅ Pipe symbol preservation: PASSED")
    
    # Critical Test 2: Om symbol preservation
    test_text2 = "ॐ śāntiḥ śāntiḥ śāntiḥ"
    result2, corrections2 = processor.process_text(test_text2)
    
    print(f"Input:  {test_text2}")
    print(f"Output: {result2}")
    
    assert "ॐ" in result2, "❌ CRITICAL FAILURE: Om symbol missing"
    
    print("✅ Om symbol preservation: PASSED")
    
    # Test 3: Devanagari dandas
    test_text3 = "सर्वे भवन्तु सुखिनः । सर्वे सन्तु निरामयाः ।।"
    result3, corrections3 = processor.process_text(test_text3)
    
    print(f"Input:  {test_text3}")
    print(f"Output: {result3}")
    
    assert "।" in result3, "❌ FAILURE: Single danda missing"
    assert "।।" in result3, "❌ FAILURE: Double danda missing"
    
    print("✅ Devanagari danda preservation: PASSED")

def test_content_classification():
    """Test sacred content classification."""
    print("\n📊 Testing Content Classification...")
    
    classifier = SacredContentClassifier()
    
    # Test mantra classification
    mantra_text = "Om mani padme hum"
    result = classifier.classify_content(mantra_text)
    print(f"'{mantra_text}' classified as: {result}")
    assert result in ['mantra', 'regular'], f"Unexpected classification: {result}"
    
    # Test verse classification
    verse_text = "dharma kṣetre kuru kṣetre | samavetā yuyutsavaḥ ||"
    result = classifier.classify_content(verse_text)
    print(f"'{verse_text}' classified as: {result}")
    assert result == 'verse', f"Expected 'verse', got: {result}"
    
    # Test regular content
    regular_text = "This is regular English text without sacred content."
    result = classifier.classify_content(regular_text)
    print(f"'{regular_text}' classified as: {result}")
    assert result == 'regular', f"Expected 'regular', got: {result}"
    
    print("✅ Content classification: PASSED")

def test_symbol_protection():
    """Test symbol protection and restoration."""
    print("\n🛡️ Testing Symbol Protection...")
    
    protector = SacredSymbolProtector()
    
    test_text = "Om pūrṇam | adaḥ || pūrṇam ॐ"
    protected_text, restoration_map = protector.protect_symbols(test_text)
    
    print(f"Original: {test_text}")
    print(f"Protected: {protected_text}")
    print(f"Restoration map: {restoration_map}")
    
    # Check that symbols are replaced with placeholders
    assert "|" not in protected_text, "Single pipe should be protected"
    assert "||" not in protected_text, "Double pipe should be protected"
    assert "ॐ" not in protected_text, "Om symbol should be protected"
    
    # Restore symbols
    restored_text = protector.restore_symbols(protected_text, restoration_map)
    print(f"Restored: {restored_text}")
    
    # Check restoration
    assert restored_text == test_text, f"Restoration failed: {restored_text} != {test_text}"
    
    print("✅ Symbol protection and restoration: PASSED")

def test_performance():
    """Basic performance check."""
    print("\n⚡ Testing Performance...")
    
    import time
    processor = SanskritProcessor(Path("lexicons"))
    
    # Test with regular content (should be fast)
    regular_text = "This is regular text without sacred content that should process quickly."
    
    start_time = time.time()
    result, corrections = processor.process_text(regular_text)
    end_time = time.time()
    
    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"Regular text processing time: {processing_time:.2f}ms")
    
    # Test with sacred content
    sacred_text = "Om pūrṇam adaḥ pūrṇam idam | pūrṇāt pūrṇam udacyate ||"
    
    start_time = time.time()
    result, corrections = processor.process_text(sacred_text)
    end_time = time.time()
    
    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"Sacred text processing time: {processing_time:.2f}ms")
    
    # Performance should be reasonable (under 100ms for short texts)
    assert processing_time < 100, f"Processing too slow: {processing_time}ms"
    
    print("✅ Performance check: PASSED")

if __name__ == "__main__":
    print("🧪 Sacred Content Preservation Test Suite")
    print("=" * 50)
    
    try:
        test_sacred_symbol_preservation()
        test_content_classification() 
        test_symbol_protection()
        test_performance()
        
        print("\n🏆 ALL TESTS PASSED! Sacred content preservation is working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)