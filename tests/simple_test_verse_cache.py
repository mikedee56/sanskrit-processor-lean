#!/usr/bin/env python3
"""
Simple tests for verse cache system - no external dependencies
Following lean architecture principles
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.verse_cache import VerseCache, CachedVerse, create_verse_cache

def test_pattern_detection():
    """Test verse reference pattern detection."""
    print("Testing pattern detection...")
    cache = VerseCache()
    
    test_cases = [
        ("Chapter 2, verse 47", [(2, 47)]),
        ("Chapter 2 verse 47", [(2, 47)]),
        ("BG 2.47", [(2, 47)]),
        ("Bhagavad Gita 2.47", [(2, 47)]),
        ("Gita 2:47", [(2, 47)]),
        ("BG 2.47 and 4.7", [(2, 47), (4, 7)]),
        ("Random text without verses", []),
    ]
    
    for text, expected in test_cases:
        result = cache.detect_verse_references(text)
        assert set(result) == set(expected), f"Failed for: {text}, got: {result}, expected: {expected}"
    
    print("✅ Pattern detection tests passed")

def test_cached_verse():
    """Test CachedVerse data structure."""
    print("Testing CachedVerse dataclass...")
    verse = CachedVerse(
        chapter=2,
        verse=47,
        sanskrit="कर्मण्येवाधिकारस्ते",
        transliteration="karmaṇy-evādhikāras te",
        translation="You have the right to perform your prescribed duty",
        keywords=["duty", "action", "right", "work"]
    )
    
    assert verse.chapter == 2
    assert verse.verse == 47
    assert "duty" in verse.keywords
    print("✅ CachedVerse tests passed")

def test_keyword_extraction():
    """Test keyword extraction."""
    print("Testing keyword extraction...")
    cache = VerseCache()
    
    text = "You have the right to perform your prescribed duty, but never to the fruits of action"
    keywords = cache._extract_keywords(text)
    
    assert "right" in keywords
    assert "duty" in keywords
    assert "fruits" in keywords
    assert "action" in keywords
    # Stop words should be filtered
    assert "the" not in keywords
    assert "to" not in keywords
    print("✅ Keyword extraction tests passed")

def test_cache_operations():
    """Test cache file operations."""
    print("Testing cache operations...")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    cache_path = temp_dir / "test_cache.json"
    
    try:
        # Create sample cache data
        sample_data = {
            "metadata": {
                "created": datetime.now().isoformat() + 'Z',
                "expires": (datetime.now() + timedelta(days=30)).isoformat() + 'Z',
                "version": "1.0",
                "total_verses": 2
            },
            "verses": {
                "2.47": {
                    "chapter": 2,
                    "verse": 47,
                    "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
                    "transliteration": "karmaṇy-evādhikāras te mā phaleṣu kadācana",
                    "translation": "You have the right to perform your prescribed duty",
                    "keywords": ["duty", "action", "right", "work"]
                }
            }
        }
        
        # Write sample data
        cache_path.write_text(json.dumps(sample_data, ensure_ascii=False))
        
        # Create cache and test loading
        cache = VerseCache(cache_path=cache_path)
        
        assert cache.is_cache_valid()
        assert cache.get_cache_info()['verses_cached'] == 1
        
        # Test verse retrieval
        verse = cache.get_verse(2, 47)
        assert verse is not None
        assert verse.chapter == 2
        assert "duty" in verse.keywords
        
        # Test non-existing verse
        verse = cache.get_verse(99, 99)
        assert verse is None
        
        # Test content search
        results = cache.search_content("duty action")
        assert len(results) > 0
        assert results[0].chapter == 2
        
        print("✅ Cache operations tests passed")
        
    finally:
        # Clean up
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def test_performance():
    """Test basic performance requirements."""
    print("Testing performance...")
    
    # Create temporary test environment
    temp_dir = Path(tempfile.mkdtemp())
    cache_path = temp_dir / "perf_cache.json"
    
    try:
        # Create cache with minimal test data
        sample_data = {
            "metadata": {
                "created": datetime.now().isoformat() + 'Z',
                "expires": (datetime.now() + timedelta(days=30)).isoformat() + 'Z',
                "version": "1.0",
                "total_verses": 100
            },
            "verses": {}
        }
        
        # Generate test verses
        for i in range(1, 101):
            chapter = (i - 1) // 10 + 1
            verse = ((i - 1) % 10) + 1
            key = f"{chapter}.{verse}"
            sample_data["verses"][key] = {
                "chapter": chapter,
                "verse": verse,
                "sanskrit": f"Sanskrit text {i}",
                "transliteration": f"Transliteration {i}",
                "translation": f"Translation with duty action verse {i}",
                "keywords": ["duty", "action", "verse", str(i)]
            }
        
        cache_path.write_text(json.dumps(sample_data, ensure_ascii=False))
        cache = VerseCache(cache_path=cache_path)
        
        # Performance test - lookups
        import time
        start = time.time()
        for i in range(100):
            cache.get_verse(2, 1)
        duration = time.time() - start
        
        lookups_per_second = 100 / duration
        assert lookups_per_second > 1000, f"Too slow: {lookups_per_second:.0f} lookups/sec"
        
        # Pattern matching performance
        test_text = "Chapter 2, verse 47 teaches about duty"
        start = time.time()
        for i in range(50):
            cache.detect_verse_references(test_text)
        duration = time.time() - start
        
        avg_time_ms = (duration * 1000) / 50
        assert avg_time_ms < 10, f"Pattern matching too slow: {avg_time_ms:.2f}ms"
        
        print("✅ Performance tests passed")
        
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def test_factory_function():
    """Test create_verse_cache factory."""
    print("Testing factory function...")
    
    config = {'cache_path': 'test_factory_cache.json'}
    cache = create_verse_cache(config)
    
    assert isinstance(cache, VerseCache)
    assert cache.cache_path == Path(config['cache_path'])
    print("✅ Factory function tests passed")

def test_error_handling_and_edge_cases():
    """Test error handling and edge cases."""
    print("Testing error handling and edge cases...")
    
    cache = VerseCache()
    
    # Test invalid verse lookup inputs
    assert cache.get_verse("invalid", 47) is None
    assert cache.get_verse(2, "invalid") is None
    assert cache.get_verse(0, 47) is None  # Out of bounds
    assert cache.get_verse(99, 47) is None  # Out of bounds
    assert cache.get_verse(2, 0) is None  # Out of bounds
    assert cache.get_verse(2, 999) is None  # Out of bounds
    
    # Test invalid search content inputs
    assert cache.search_content("") == []  # Empty query
    assert cache.search_content("   ") == []  # Whitespace only
    assert cache.search_content(123) == []  # Invalid type
    
    # Test invalid pattern detection inputs
    assert cache.detect_verse_references("") == []  # Empty text
    assert cache.detect_verse_references("   ") == []  # Whitespace only
    assert cache.detect_verse_references(None) == []  # None input
    
    print("✅ Error handling and edge cases tests passed")

def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running Verse Cache Tests")
    print("=" * 50)
    
    try:
        test_pattern_detection()
        test_cached_verse()
        test_keyword_extraction()
        test_cache_operations()
        test_performance()
        test_factory_function()
        test_error_handling_and_edge_cases()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("Verse cache system is working correctly")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)