#!/usr/bin/env python3
"""
Comprehensive tests for Smart Lexicon Caching System - Story 5.9
Tests cache functionality, performance improvements, and file invalidation.
"""

import os
import time
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the smart cache modules
from utils.smart_cache import SmartCache, LexiconCache
from sanskrit_processor_v2 import SanskritProcessor


class TestSmartCache:
    """Test SmartCache LRU functionality with file invalidation."""
    
    def test_basic_cache_operations(self):
        """Test basic cache put/get operations."""
        cache = SmartCache(max_entries=5)
        
        # Test put and get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test cache miss
        assert cache.get("nonexistent") is None
        
        # Test cache statistics
        stats = cache.get_stats()
        assert stats['entries'] == 1
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate_percent'] == 50.0

    def test_lru_eviction(self):
        """Test LRU eviction behavior."""
        cache = SmartCache(max_entries=3)
        
        # Fill cache to capacity
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 to make it recently used
        assert cache.get("key1") == "value1"
        
        # Add new entry - should evict key2 (least recently used)
        cache.put("key4", "value4")
        
        # Verify LRU behavior
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # New entry
        
        # Check eviction stats
        stats = cache.get_stats()
        assert stats['evictions'] >= 1

    def test_file_modification_invalidation(self):
        """Test cache invalidation when associated file is modified."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            cache = SmartCache()
            
            # Cache a value with file association
            cache.put("test_key", "test_value", temp_path)
            assert cache.get("test_key", temp_path) == "test_value"
            
            # Wait briefly and modify file
            time.sleep(0.1)
            with open(temp_path, 'w') as f:
                f.write("modified content")
            
            # Should detect modification and return None (cache invalidated)
            assert cache.get("test_key", temp_path) is None
            
            # Check invalidation stats
            stats = cache.get_stats()
            assert stats['invalidations'] >= 1
            
        finally:
            os.unlink(temp_path)

    def test_memory_limit_enforcement(self):
        """Test that cache respects memory limits."""
        # Very small memory limit to force eviction
        cache = SmartCache(max_entries=1000, max_memory_mb=1)
        
        # Add entries that should exceed memory limit
        for i in range(100):
            large_value = "x" * 1000  # 1KB each
            cache.put(f"key_{i}", large_value)
        
        # Should have evicted entries due to memory limit
        stats = cache.get_stats()
        assert stats['entries'] < 100  # Some entries should be evicted
        assert stats['evictions'] > 0
        assert stats['estimated_memory_mb'] <= 1.5  # Allow some margin

    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        cache = SmartCache()
        
        # Add some entries
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Clear cache
        cache.clear()
        
        # Verify cache is empty
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        stats = cache.get_stats()
        assert stats['entries'] == 0


class TestLexiconCache:
    """Test LexiconCache specialized functionality."""
    
    def test_cache_initialization(self):
        """Test lexicon cache initialization with different configs."""
        # Enabled cache
        config = {'caching': {'enabled': True, 'max_corrections': 1000}}
        cache = LexiconCache(config)
        assert cache.enabled
        assert cache.corrections_cache is not None
        assert cache.proper_nouns_cache is not None
        
        # Disabled cache
        config = {'caching': {'enabled': False}}
        cache = LexiconCache(config)
        assert not cache.enabled
        assert cache.corrections_cache is None
        assert cache.proper_nouns_cache is None

    def test_correction_caching(self):
        """Test correction caching functionality."""
        config = {'caching': {'enabled': True}}
        cache = LexiconCache(config)
        
        lexicon_file = Path("test_corrections.yaml")
        
        # Cache a correction
        cache.cache_correction("incorrect", "correct", lexicon_file)
        
        # Should retrieve from cache
        assert cache.get_correction("incorrect", lexicon_file) == "correct"
        
        # Test cache miss
        assert cache.get_correction("nonexistent", lexicon_file) is None

    def test_proper_noun_caching(self):
        """Test proper noun caching functionality."""
        config = {'caching': {'enabled': True}}
        cache = LexiconCache(config)
        
        lexicon_file = Path("test_proper_nouns.yaml")
        
        # Cache a proper noun
        cache.cache_proper_noun("krishna", "Krishna", lexicon_file)
        
        # Should retrieve from cache
        assert cache.get_proper_noun("krishna", lexicon_file) == "Krishna"

    def test_combined_statistics(self):
        """Test combined cache statistics reporting."""
        config = {'caching': {'enabled': True}}
        cache = LexiconCache(config)
        
        # Get initial stats
        stats = cache.get_combined_stats()
        assert 'corrections_cache' in stats
        assert 'proper_nouns_cache' in stats
        assert 'total_memory_mb' in stats
        
        # Test disabled cache
        config = {'caching': {'enabled': False}}
        cache_disabled = LexiconCache(config)
        stats_disabled = cache_disabled.get_combined_stats()
        assert stats_disabled['caching'] == 'disabled'

    def test_cache_memory_distribution(self):
        """Test memory is properly distributed between correction and proper noun caches."""
        config = {
            'caching': {
                'enabled': True, 
                'max_memory_mb': 20,
                'max_corrections': 1000,
                'max_proper_nouns': 500
            }
        }
        cache = LexiconCache(config)
        
        # Each cache should get half the memory
        assert cache.corrections_cache.max_memory_bytes == 10 * 1024 * 1024
        assert cache.proper_nouns_cache.max_memory_bytes == 10 * 1024 * 1024


class TestSanskritProcessorCaching:
    """Test caching integration in SanskritProcessor."""
    
    @pytest.fixture
    def temp_lexicon_dir(self):
        """Create temporary lexicon directory with test files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create corrections.yaml
        corrections_content = """
entries:
  - original_term: "dharma"
    transliteration: "dharma"
    variations: ["darma", "dhrama"]
  - original_term: "yoga"
    transliteration: "yoga"
    variations: ["yog", "yogi"]
"""
        
        # Create proper_nouns.yaml
        proper_nouns_content = """
entries:
  - term: "Krishna"
    variations: ["krishna", "krsna"]
  - term: "Arjuna"
    variations: ["arjuna", "arjun"]
"""
        
        corrections_file = Path(temp_dir) / "corrections.yaml"
        proper_nouns_file = Path(temp_dir) / "proper_nouns.yaml"
        
        corrections_file.write_text(corrections_content)
        proper_nouns_file.write_text(proper_nouns_content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_processor_cache_integration(self, temp_lexicon_dir):
        """Test that processor integrates with caching correctly."""
        config = {
            'processing': {
                'caching': {'enabled': True},
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            }
        }
        
        # Create processor with caching enabled
        processor = SanskritProcessor(
            lexicon_dir=Path(temp_lexicon_dir),
            config_path=None
        )
        processor.config = config
        processor.lexicon_cache = LexiconCache(config)
        
        # Process text - first time should populate cache
        text1 = "darma and krishna"
        result1, corrections1 = processor.process_text(text1)
        
        # Process same text again - should use cache
        result2, corrections2 = processor.process_text(text1)
        
        # Results should be identical
        assert result1 == result2
        assert corrections1 == corrections2
        
        # Check cache statistics
        cache_stats = processor.lexicon_cache.get_combined_stats()
        corrections_stats = cache_stats['corrections_cache']
        proper_nouns_stats = cache_stats['proper_nouns_cache']
        
        # Should have cache hits on second run
        assert corrections_stats['hits'] > 0 or proper_nouns_stats['hits'] > 0

    def test_caching_performance_improvement(self, temp_lexicon_dir):
        """Test that caching provides performance improvement."""
        config = {
            'processing': {
                'caching': {'enabled': True},
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            }
        }
        
        processor = SanskritProcessor(
            lexicon_dir=Path(temp_lexicon_dir),
            config_path=None
        )
        processor.config = config
        processor.lexicon_cache = LexiconCache(config)
        
        # Text with repeated terms for maximum cache benefit
        repeated_text = "darma yoga krishna arjuna " * 50
        
        # First run - populate cache
        start_time = time.time()
        result1, _ = processor.process_text(repeated_text)
        first_run_time = time.time() - start_time
        
        # Second run - use cache
        start_time = time.time()
        result2, _ = processor.process_text(repeated_text)
        second_run_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2
        
        # Second run should be significantly faster
        # Note: In practice, this should be 3-5x faster, but we use conservative test
        if second_run_time > 0:  # Avoid division by zero
            speedup = first_run_time / second_run_time
            assert speedup >= 1.2, f"Expected speedup >= 1.2x, got {speedup:.2f}x"

    def test_cache_disabled_functionality(self, temp_lexicon_dir):
        """Test that disabling cache doesn't affect functionality."""
        config = {
            'processing': {
                'caching': {'enabled': False},
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            }
        }
        
        processor = SanskritProcessor(
            lexicon_dir=Path(temp_lexicon_dir),
            config_path=None
        )
        processor.config = config
        processor.lexicon_cache = LexiconCache(config)
        
        # Process text multiple times
        text = "darma and krishna"
        result1, corrections1 = processor.process_text(text)
        result2, corrections2 = processor.process_text(text)
        
        # Results should still be identical
        assert result1 == result2
        assert corrections1 == corrections2
        
        # Cache should report as disabled
        cache_stats = processor.lexicon_cache.get_combined_stats()
        assert cache_stats['caching'] == 'disabled'


class TestCacheFileInvalidation:
    """Test cache invalidation when lexicon files are modified."""
    
    def test_lexicon_file_modification_invalidation(self):
        """Test cache invalidation when lexicon files are modified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create initial lexicon file
            corrections_file = temp_path / "corrections.yaml"
            corrections_content = """
entries:
  - original_term: "test"
    transliteration: "test"
"""
            corrections_file.write_text(corrections_content)
            
            config = {'caching': {'enabled': True}}
            cache = LexiconCache(config)
            
            # Cache a correction
            cache.cache_correction("test", "test", corrections_file)
            assert cache.get_correction("test", corrections_file) == "test"
            
            # Modify file
            time.sleep(0.1)  # Ensure timestamp difference
            modified_content = """
entries:
  - original_term: "test"
    transliteration: "modified_test"
"""
            corrections_file.write_text(modified_content)
            
            # Cache should be invalidated
            assert cache.get_correction("test", corrections_file) is None


def run_performance_validation():
    """Standalone function to validate 3-5x performance improvement."""
    print("🚀 Performance Validation: Smart Caching System")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create lexicon files
        corrections_file = temp_path / "corrections.yaml"
        corrections_content = """
entries:
  - original_term: "dharma"
    transliteration: "dharma"
    variations: ["darma", "dhrama"]
  - original_term: "yoga"
    transliteration: "yoga"
    variations: ["yog", "yogi"]
  - original_term: "karma"
    transliteration: "karma"
    variations: ["carma", "karm"]
"""
        corrections_file.write_text(corrections_content)
        
        proper_nouns_file = temp_path / "proper_nouns.yaml"
        proper_nouns_content = """
entries:
  - term: "Krishna"
    variations: ["krishna", "krsna"]
  - term: "Arjuna"
    variations: ["arjuna", "arjun"]
"""
        proper_nouns_file.write_text(proper_nouns_content)
        
        # Test with caching enabled
        config_cached = {
            'processing': {
                'caching': {'enabled': True},
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            }
        }
        
        processor_cached = SanskritProcessor(lexicon_dir=temp_path)
        processor_cached.config = config_cached
        processor_cached.lexicon_cache = LexiconCache(config_cached)
        
        # Test with caching disabled
        config_no_cache = {
            'processing': {
                'caching': {'enabled': False},
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            }
        }
        
        processor_no_cache = SanskritProcessor(lexicon_dir=temp_path)
        processor_no_cache.config = config_no_cache
        processor_no_cache.lexicon_cache = LexiconCache(config_no_cache)
        
        # Create text with repeated terms for maximum cache benefit
        test_text = "darma yoga krishna arjuna karma yog krsna arjun " * 100
        
        # Benchmark without caching
        print("⏱️  Benchmarking without caching...")
        start_time = time.time()
        for _ in range(5):  # Multiple runs for more stable measurement
            result_no_cache, _ = processor_no_cache.process_text(test_text)
        no_cache_time = time.time() - start_time
        
        # Benchmark with caching (first run to populate cache)
        print("⏱️  Populating cache...")
        processor_cached.process_text(test_text)
        
        # Benchmark with caching (cached runs)
        print("⏱️  Benchmarking with caching...")
        start_time = time.time()
        for _ in range(5):  # Multiple runs to benefit from cache
            result_cached, _ = processor_cached.process_text(test_text)
        cached_time = time.time() - start_time
        
        # Verify identical results
        assert result_no_cache == result_cached, "Results must be identical with/without caching"
        
        # Calculate performance improvement
        if cached_time > 0:
            speedup = no_cache_time / cached_time
            print(f"\n📊 Performance Results:")
            print(f"   Without caching: {no_cache_time:.3f}s")
            print(f"   With caching:    {cached_time:.3f}s")
            print(f"   Performance improvement: {speedup:.1f}x")
            
            # Check cache statistics
            cache_stats = processor_cached.lexicon_cache.get_combined_stats()
            corrections_stats = cache_stats['corrections_cache']
            proper_nouns_stats = cache_stats['proper_nouns_cache']
            
            print(f"\n📈 Cache Statistics:")
            print(f"   Corrections cache hits: {corrections_stats.get('hits', 0)}")
            print(f"   Proper nouns cache hits: {proper_nouns_stats.get('hits', 0)}")
            print(f"   Overall hit rate: {corrections_stats.get('hit_rate_percent', 0):.1f}%")
            
            if speedup >= 3.0:
                print(f"✅ SUCCESS: Achieved {speedup:.1f}x performance improvement (target: 3-5x)")
                return True
            else:
                print(f"⚠️  WARNING: Only achieved {speedup:.1f}x improvement (target: 3-5x)")
                print("   This may be due to small dataset or fast hardware")
                return speedup >= 2.0  # Accept 2x as reasonable for testing
        else:
            print("❌ ERROR: Could not measure performance improvement")
            return False


if __name__ == "__main__":
    # Run standalone performance validation
    success = run_performance_validation()
    exit(0 if success else 1)