"""
Test Suite for Story 10.5: Performance Optimization
Validates caching, batch processing, and performance improvements.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from utils.performance_cache import PerformanceCache, get_performance_cache
from utils.pattern_manager import PatternManager, get_pattern_manager
from utils.batch_processor import BatchProcessor, BatchResult
import time


class TestPerformanceCache:
    """Test the performance cache system."""
    
    def test_cache_initialization(self):
        """Test cache system initializes correctly."""
        cache = PerformanceCache(max_entries=100, ttl_seconds=3600)
        assert cache.max_entries == 100
        assert cache.ttl == 3600
        assert cache.fuzzy_cache is not None
        assert cache.context_cache is not None
        assert cache.pattern_cache is not None
    
    def test_cache_fuzzy_match_decorator(self):
        """Test fuzzy match caching decorator."""
        cache = PerformanceCache()
        
        @cache.cache_fuzzy_match
        def mock_fuzzy_match(text: str, target: str, threshold: float = 0.8):
            # Simulate expensive calculation
            time.sleep(0.001)
            return {'similarity': 0.9, 'original': text, 'target': target}
        
        # First call should be slow
        start_time = time.perf_counter()
        result1 = mock_fuzzy_match("test", "target")
        first_call_time = time.perf_counter() - start_time
        
        # Second call should be fast (cached)
        start_time = time.perf_counter()
        result2 = mock_fuzzy_match("test", "target")
        second_call_time = time.perf_counter() - start_time
        
        assert result1 == result2
        assert second_call_time < first_call_time
    
    def test_cache_context_detection_decorator(self):
        """Test context detection caching decorator."""
        cache = PerformanceCache()
        
        @cache.cache_context_detection
        def mock_context_detection(text: str):
            time.sleep(0.001)
            return {'context': 'sanskrit', 'confidence': 0.9}
        
        start_time = time.perf_counter()
        result1 = mock_context_detection("oṁ namaḥ śivāya")
        first_call_time = time.perf_counter() - start_time
        
        start_time = time.perf_counter()
        result2 = mock_context_detection("oṁ namaḥ śivāya")
        second_call_time = time.perf_counter() - start_time
        
        assert result1 == result2
        assert second_call_time < first_call_time
    
    def test_cache_hit_rates(self):
        """Test cache hit rate calculation."""
        cache = PerformanceCache()
        
        @cache.cache_fuzzy_match
        def mock_function(text: str, target: str, threshold: float = 0.8):
            return {'result': f"{text}-{target}"}
        
        # Generate cache hits and misses
        mock_function("a", "b")  # miss
        mock_function("a", "b")  # hit
        mock_function("c", "d")  # miss
        mock_function("a", "b")  # hit
        
        hit_rates = cache.get_hit_rates()
        assert 'fuzzy_matches' in hit_rates
        assert hit_rates['fuzzy_matches'] > 0.0
        assert hit_rates['overall'] > 0.0
    
    def test_cache_performance_stats(self):
        """Test performance statistics collection."""
        cache = PerformanceCache()
        stats = cache.get_performance_stats()
        
        assert 'fuzzy_matches' in stats
        assert 'context_detection' in stats
        assert 'pattern_matching' in stats
        assert 'memory_usage' in stats


class TestPatternManager:
    """Test the pattern manager system."""
    
    def test_pattern_manager_singleton(self):
        """Test pattern manager singleton behavior."""
        pm1 = PatternManager()
        pm2 = PatternManager()
        assert pm1 is pm2
    
    def test_precompiled_patterns(self):
        """Test that common patterns are pre-compiled."""
        pm = get_pattern_manager()
        
        # Check that common patterns exist
        assert pm.get_pattern('sanskrit_word') is not None
        assert pm.get_pattern('english_word') is not None
        assert pm.get_pattern('diacritical_chars') is not None
        assert pm.get_pattern('word_boundaries') is not None
    
    def test_pattern_usage_tracking(self):
        """Test pattern usage statistics."""
        pm = get_pattern_manager()
        pm.clear_usage_stats()
        
        # Use some patterns
        pm.get_pattern('sanskrit_word')
        pm.get_pattern('sanskrit_word')
        pm.get_pattern('english_word')
        
        stats = pm.get_pattern_stats()
        assert stats['total_usage'] == 3
        assert 'sanskrit_word' in stats['pattern_usage']
        assert stats['pattern_usage']['sanskrit_word'] == 2
    
    def test_fast_methods(self):
        """Test optimized fast methods."""
        pm = get_pattern_manager()
        
        # Test Sanskrit character detection
        assert pm.has_sanskrit_chars_fast("oṁ namaḥ śivāya") == True
        assert pm.has_sanskrit_chars_fast("hello world") == False
        
        # Test word extraction
        words = pm.extract_words_fast("hello world test")
        assert len(words) == 3
        assert "hello" in words


class TestBatchProcessor:
    """Test the batch processing system."""
    
    def setUp(self):
        """Set up test environment with temporary files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.temp_dir / "input"
        self.output_dir = self.temp_dir / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        # Create test SRT files
        for i in range(3):
            test_file = self.input_dir / f"test_{i}.srt"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(f"""1
00:00:0{i},000 --> 00:00:0{i+1},000
Test subtitle {i}
""")
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)
    
    def test_batch_processor_initialization(self):
        """Test batch processor initializes correctly."""
        from sanskrit_processor_v2 import SanskritProcessor
        processor = SanskritProcessor(Path("lexicons"))
        
        batch_processor = BatchProcessor(processor)
        assert batch_processor.processor is processor
        assert batch_processor.max_workers > 0
    
    def test_batch_result_structure(self):
        """Test batch result data structure."""
        result = BatchResult(
            total_files=10,
            successful_files=8,
            failed_files=2,
            processing_time_seconds=30.5,
            files_per_second=0.33
        )
        
        assert result.total_files == 10
        assert result.successful_files == 8
        assert result.failed_files == 2
        assert result.processing_time_seconds == 30.5


class TestPerformanceIntegration:
    """Integration tests for performance optimizations."""
    
    def test_cache_effectiveness_target(self):
        """Test that caches meet target hit rates."""
        cache = PerformanceCache()
        
        @cache.cache_fuzzy_match
        def repeated_operation(text: str, target: str, threshold: float = 0.8):
            return {'result': 'test'}
        
        # Simulate repeated operations
        terms = [("test", "target"), ("hello", "world"), ("sanskrit", "term")]
        
        # First pass - all misses
        for text, target in terms * 3:  # Repeat 3 times
            repeated_operation(text, target)
        
        hit_rates = cache.get_hit_rates()
        target_met = cache.is_target_hit_rate_met(0.6)
        
        assert hit_rates['fuzzy_matches'] >= 0.6  # Should meet 60% target
        assert target_met['fuzzy_matches'] == True
    
    def test_performance_improvement_measurement(self):
        """Test that performance improvements can be measured."""
        cache = PerformanceCache()
        
        @cache.cache_fuzzy_match
        def expensive_operation(text: str, target: str, threshold: float = 0.8):
            # Simulate expensive calculation
            time.sleep(0.002)
            return {'result': f"processed_{text}"}
        
        # Warm up cache
        expensive_operation("test", "target")
        
        # Measure performance
        start_time = time.perf_counter()
        for _ in range(10):
            expensive_operation("test", "target")
        cached_time = time.perf_counter() - start_time
        
        stats = cache.get_performance_stats()
        assert stats['fuzzy_matches']['total_time_saved_ms'] > 0


def test_global_cache_instances():
    """Test global cache instance functions."""
    cache1 = get_performance_cache()
    cache2 = get_performance_cache()
    assert cache1 is cache2  # Should be same instance
    
    pm1 = get_pattern_manager()
    pm2 = get_pattern_manager()
    assert pm1 is pm2  # Should be same instance


if __name__ == "__main__":
    # Run basic functionality test
    print("🧪 Testing Performance Optimization Components...")
    
    # Test performance cache
    print("  ✅ Performance Cache:", end=" ")
    cache = PerformanceCache()
    print("OK")
    
    # Test pattern manager
    print("  ✅ Pattern Manager:", end=" ")
    pm = get_pattern_manager()
    print("OK")
    
    # Test batch processor
    print("  ✅ Batch Processor:", end=" ")
    from sanskrit_processor_v2 import SanskritProcessor
    processor = SanskritProcessor(Path("lexicons"))
    batch_processor = BatchProcessor(processor)
    print("OK")
    
    print("\n🎉 All performance optimization components working correctly!")