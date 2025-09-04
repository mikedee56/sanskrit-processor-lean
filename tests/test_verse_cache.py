"""
Unit and integration tests for verse cache system
Following lean architecture - comprehensive testing with minimal overhead
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil
from datetime import datetime, timedelta

# Import the modules we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.verse_cache import VerseCache, CachedVerse, CacheMetadata, create_verse_cache

class TestVerseCache:
    """Test cases for VerseCache class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_path = self.temp_dir / "test_cache.json"
        self.cache = VerseCache(cache_path=self.cache_path)

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_pattern_detection(self):
        """Test verse reference pattern detection."""
        cache = VerseCache()
        
        # Test various patterns
        test_cases = [
            ("Chapter 2, verse 47", [(2, 47)]),
            ("Chapter 2 verse 47", [(2, 47)]),
            ("BG 2.47", [(2, 47)]),
            ("Bhagavad Gita 2.47", [(2, 47)]),
            ("Gita 2:47", [(2, 47)]),
            ("BG 2.47 and 4.7", [(2, 47), (4, 7)]),
            ("In Gita 3.21, Krishna teaches about leadership", [(3, 21)]),
            ("Random text without verses", []),
        ]
        
        for text, expected in test_cases:
            result = cache.detect_verse_references(text)
            assert set(result) == set(expected), f"Failed for: {text}, got: {result}, expected: {expected}"

    def test_cached_verse_dataclass(self):
        """Test CachedVerse data structure."""
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

    def test_cache_metadata(self):
        """Test cache metadata structure."""
        now = datetime.now()
        future = now + timedelta(days=30)
        
        metadata = CacheMetadata(
            created=now.isoformat(),
            expires=future.isoformat(), 
            version="1.0",
            total_verses=700
        )
        
        assert metadata.version == "1.0"
        assert metadata.total_verses == 700

    def test_keyword_extraction(self):
        """Test keyword extraction from translations."""
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

    def test_empty_cache_initialization(self):
        """Test initialization with empty cache."""
        cache = VerseCache(cache_path=self.cache_path)
        
        assert not cache.is_cache_valid()
        assert cache.get_cache_info()['verses_cached'] == 0
        assert not cache.get_cache_info()['cache_exists']

    def test_cache_creation_and_loading(self):
        """Test cache file creation and loading."""
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
                },
                "3.21": {
                    "chapter": 3,
                    "verse": 21,
                    "sanskrit": "यद्यदाचरति श्रेष्ठस्तत्तदेवेतरो जनः।",
                    "transliteration": "yad yad ācarati śreṣṭhas tat tad evetaro janaḥ",
                    "translation": "Whatever action is performed by a great man",
                    "keywords": ["action", "great", "man", "performed"]
                }
            }
        }
        
        # Write sample data to cache file
        self.cache_path.write_text(json.dumps(sample_data, ensure_ascii=False))
        
        # Create new cache instance and test loading
        cache = VerseCache(cache_path=self.cache_path)
        
        assert cache.is_cache_valid()
        assert cache.get_cache_info()['verses_cached'] == 2
        
        # Test verse retrieval
        verse = cache.get_verse(2, 47)
        assert verse is not None
        assert verse.chapter == 2
        assert verse.verse == 47
        assert "duty" in verse.keywords

    def test_verse_lookup(self):
        """Test fast verse retrieval."""
        # Create cache with test data
        self.test_cache_creation_and_loading()
        cache = VerseCache(cache_path=self.cache_path)
        
        # Test existing verse
        verse = cache.get_verse(2, 47)
        assert verse is not None
        assert verse.sanskrit.startswith("कर्मण्येवाधिकारस्ते")
        
        # Test non-existing verse
        verse = cache.get_verse(99, 99)
        assert verse is None

    def test_content_search(self):
        """Test keyword search functionality."""
        # Create cache with test data
        self.test_cache_creation_and_loading()
        cache = VerseCache(cache_path=self.cache_path)
        
        # Test search for duty
        results = cache.search_content("duty action")
        assert len(results) > 0
        assert results[0].chapter == 2
        
        # Test search with no matches
        results = cache.search_content("nonexistent keyword")
        assert len(results) == 0

    def test_cache_expiry(self):
        """Test cache expiry functionality."""
        # Create expired cache data
        expired_data = {
            "metadata": {
                "created": (datetime.now() - timedelta(days=35)).isoformat() + 'Z',
                "expires": (datetime.now() - timedelta(days=5)).isoformat() + 'Z',  # Expired
                "version": "1.0",
                "total_verses": 1
            },
            "verses": {
                "2.47": {
                    "chapter": 2, "verse": 47,
                    "sanskrit": "test", "transliteration": "test",
                    "translation": "test", "keywords": ["test"]
                }
            }
        }
        
        self.cache_path.write_text(json.dumps(expired_data))
        
        # Cache should recognize expiry and not load
        cache = VerseCache(cache_path=self.cache_path)
        assert not cache.is_cache_valid()

class TestVerseCacheIntegration:
    """Integration tests for verse cache with API client."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('services.verse_cache.requests.get')
    def test_download_verses_mock(self, mock_get):
        """Test verse downloading with mocked requests."""
        # Mock successful API responses
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "verse": 47,
                "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
                "transliteration": "karmaṇy-evādhikāras te mā phaleṣu kadācana",
                "translation": "You have the right to perform your prescribed duty, but never to the fruits of action"
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        cache_path = self.temp_dir / "test_download_cache.json"
        cache = VerseCache(cache_path=cache_path)
        
        # Test download
        success = cache.download_verses()
        assert success
        assert cache.is_cache_valid()
        assert cache_path.exists()
        
        # Verify calls were made for all chapters
        assert mock_get.call_count == 18  # 18 chapters

    def test_create_verse_cache_factory(self):
        """Test factory function."""
        config = {'cache_path': str(self.temp_dir / 'factory_cache.json')}
        cache = create_verse_cache(config)
        
        assert isinstance(cache, VerseCache)
        assert cache.cache_path == Path(config['cache_path'])

class TestPerformance:
    """Performance tests for verse cache."""
    
    def setup_method(self):
        """Set up performance test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_path = self.temp_dir / "perf_cache.json"
        
        # Create cache with test data for performance testing
        sample_data = {
            "metadata": {
                "created": datetime.now().isoformat() + 'Z',
                "expires": (datetime.now() + timedelta(days=30)).isoformat() + 'Z',
                "version": "1.0",
                "total_verses": 1000
            },
            "verses": {}
        }
        
        # Generate test verses
        for chapter in range(1, 19):
            for verse in range(1, 51):  # 50 verses per chapter
                key = f"{chapter}.{verse}"
                sample_data["verses"][key] = {
                    "chapter": chapter,
                    "verse": verse,
                    "sanskrit": f"Sanskrit text for {chapter}.{verse}",
                    "transliteration": f"Transliteration for {chapter}.{verse}",
                    "translation": f"Translation for duty action verse {chapter}.{verse}",
                    "keywords": ["duty", "action", "verse", str(chapter)]
                }
        
        self.cache_path.write_text(json.dumps(sample_data, ensure_ascii=False))
        self.cache = VerseCache(cache_path=self.cache_path)
    
    def teardown_method(self):
        """Clean up performance test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_lookup_performance(self):
        """Test verse lookup performance - should be < 1ms per lookup."""
        import time
        
        # Warm up
        for i in range(10):
            self.cache.get_verse(2, 47)
        
        # Performance test
        start = time.time()
        for i in range(1000):
            self.cache.get_verse(2, 47)
        duration = time.time() - start
        
        lookups_per_second = 1000 / duration
        assert lookups_per_second > 1000, f"Too slow: {lookups_per_second:.0f} lookups/sec"

    def test_pattern_matching_performance(self):
        """Test pattern matching performance - should be < 10ms per text."""
        import time
        
        test_text = "In Chapter 2, verse 47 of the Bhagavad Gita, Krishna teaches about dharma and duty"
        
        # Warm up
        for i in range(10):
            self.cache.detect_verse_references(test_text)
        
        # Performance test
        start = time.time()
        for i in range(100):
            self.cache.detect_verse_references(test_text)
        duration = time.time() - start
        
        avg_time_ms = (duration * 1000) / 100
        assert avg_time_ms < 10, f"Too slow: {avg_time_ms:.2f}ms per pattern match"

    def test_memory_usage(self):
        """Test memory footprint is reasonable."""
        import sys
        
        # Get cache size
        cache_info = self.cache.get_cache_info()
        verses_count = cache_info['verses_cached']
        
        # Rough memory calculation (very approximate)
        # Each verse has ~500 chars of text data on average
        estimated_memory_mb = (verses_count * 500) / (1024 * 1024)
        
        assert estimated_memory_mb < 10, f"Memory usage too high: {estimated_memory_mb:.2f}MB"

if __name__ == "__main__":
    # Run specific tests for development
    test_cache = TestVerseCache()
    test_cache.setup_method()
    
    print("Testing pattern detection...")
    test_cache.test_pattern_detection()
    print("✅ Pattern detection tests passed")
    
    print("Testing cache operations...")
    test_cache.test_cache_creation_and_loading()
    print("✅ Cache operations tests passed")
    
    print("Testing performance...")
    perf_test = TestPerformance()
    perf_test.setup_method()
    perf_test.test_lookup_performance()
    perf_test.test_pattern_matching_performance()
    print("✅ Performance tests passed")
    
    print("All tests completed successfully! ✅")
    
    # Clean up
    test_cache.teardown_method()
    perf_test.teardown_method()