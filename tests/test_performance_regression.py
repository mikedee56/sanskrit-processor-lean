#!/usr/bin/env python3
"""
Performance Regression Test Suite
Ensures the Sanskrit Processor maintains performance standards across versions.
"""

import pytest
import time
import psutil
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import statistics

from sanskrit_processor_v2 import SanskritProcessor
from enhanced_processor import EnhancedSanskritProcessor

# Performance benchmarks based on architectural requirements
PERFORMANCE_BENCHMARKS = {
    'segments_per_second': 2600,     # Minimum processing speed
    'memory_limit_mb': 50,           # Maximum memory usage
    'startup_time_ms': 1000,         # Maximum startup time
    'single_segment_ms': 0.4,        # Maximum time per segment (1/2600)
    'cache_hit_ratio': 0.8,          # Minimum cache efficiency
    'memory_growth_mb': 10,          # Maximum memory growth during processing
}

# Test data sets of varying sizes
SMALL_SRT_CONTENT = """1
00:00:01,000 --> 00:00:03,000
Om namah shivaya guru dev

2
00:00:04,000 --> 00:00:06,000
Krishna consciousness meditation"""

MEDIUM_SRT_CONTENT = "\n\n".join([
    f"""{i}
00:00:{i:02d},000 --> 00:00:{i+2:02d},000
Om namah shivaya Krishna consciousness dharma yoga meditation bhagavad gita srimad vedanta"""
    for i in range(1, 51)  # 50 segments
])

LARGE_SRT_CONTENT = "\n\n".join([
    f"""{i}
00:00:{i%60:02d},{(i*20)%1000:03d} --> 00:00:{(i+2)%60:02d},{((i+2)*20)%1000:03d}
Om namah shivaya Krishna consciousness dharma yoga meditation bhagavad gita srimad vedanta upanishads guru teachings spiritual wisdom"""
    for i in range(1, 501)  # 500 segments  
])


class PerformanceTracker:
    """Tracks performance metrics during testing."""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.process = psutil.Process()
        self.metrics = {}
    
    def start(self):
        """Start performance tracking."""
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def stop(self) -> Dict[str, float]:
        """Stop tracking and return metrics."""
        end_time = time.perf_counter()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        self.metrics = {
            'duration_ms': (end_time - self.start_time) * 1000,
            'start_memory_mb': self.start_memory,
            'end_memory_mb': end_memory,
            'memory_delta_mb': end_memory - self.start_memory,
            'peak_memory_mb': self.process.memory_info().peak_wss / 1024 / 1024 if hasattr(self.process.memory_info(), 'peak_wss') else end_memory
        }
        return self.metrics


class TestPerformanceRegression:
    """Core performance regression tests."""
    
    @pytest.fixture
    def temp_lexicons(self):
        """Create temporary lexicon files for testing."""
        temp_dir = tempfile.mkdtemp()
        lexicons_dir = Path(temp_dir) / "lexicons"
        lexicons_dir.mkdir()
        
        import yaml
        
        # Create comprehensive test lexicons
        corrections = {
            'om': 'Om', 'namah': 'namah', 'shivaya': 'Shivaya',
            'krishna': 'Krishna', 'consciousness': 'consciousness',
            'dharma': 'dharma', 'yoga': 'yoga', 'meditation': 'meditation',
            'bhagavad': 'Bhagavad', 'gita': 'Gita', 'srimad': 'Srimad',
            'vedanta': 'Vedanta', 'upanishads': 'Upanishads',
            'guru': 'guru', 'teachings': 'teachings',
            'spiritual': 'spiritual', 'wisdom': 'wisdom'
        }
        
        proper_nouns = {
            'Krishna': 'Krishna', 'Shivaya': 'Shivaya', 'Bhagavad': 'Bhagavad',
            'Gita': 'Gita', 'Srimad': 'Srimad', 'Vedanta': 'Vedanta',
            'Upanishads': 'Upanishads'
        }
        
        (lexicons_dir / "corrections.yaml").write_text(yaml.dump(corrections))
        (lexicons_dir / "proper_nouns.yaml").write_text(yaml.dump(proper_nouns))
        
        return lexicons_dir
    
    @pytest.fixture
    def performance_tracker(self):
        """Create performance tracker."""
        return PerformanceTracker()

    def test_processor_startup_time(self, temp_lexicons, performance_tracker):
        """Test processor initialization performance."""
        performance_tracker.start()
        processor = SanskritProcessor(temp_lexicons)
        metrics = performance_tracker.stop()
        
        startup_time = metrics['duration_ms']
        assert startup_time < PERFORMANCE_BENCHMARKS['startup_time_ms'], \
            f"Startup time {startup_time:.2f}ms exceeds benchmark {PERFORMANCE_BENCHMARKS['startup_time_ms']}ms"

    def test_small_file_processing_speed(self, temp_lexicons, performance_tracker):
        """Test processing speed with small files."""
        processor = SanskritProcessor(temp_lexicons)
        
        # Create test file
        temp_file = Path(tempfile.mktemp(suffix='.srt'))
        temp_file.write_text(SMALL_SRT_CONTENT)
        output_file = Path(tempfile.mktemp(suffix='.srt'))
        
        performance_tracker.start()
        result = processor.process_srt_file(str(temp_file), str(output_file))
        metrics = performance_tracker.stop()
        
        # Calculate segments per second
        segments_per_second = (result.segments_processed / metrics['duration_ms']) * 1000
        
        assert segments_per_second >= PERFORMANCE_BENCHMARKS['segments_per_second'] * 0.5, \
            f"Small file processing speed {segments_per_second:.0f} segments/s below 50% of benchmark"
        
        # Cleanup
        temp_file.unlink()
        if output_file.exists():
            output_file.unlink()

    def test_medium_file_processing_speed(self, temp_lexicons, performance_tracker):
        """Test processing speed with medium files (50 segments)."""
        processor = SanskritProcessor(temp_lexicons)
        
        temp_file = Path(tempfile.mktemp(suffix='.srt'))
        temp_file.write_text(MEDIUM_SRT_CONTENT)
        output_file = Path(tempfile.mktemp(suffix='.srt'))
        
        performance_tracker.start()
        result = processor.process_srt_file(str(temp_file), str(output_file))
        metrics = performance_tracker.stop()
        
        segments_per_second = (result.segments_processed / metrics['duration_ms']) * 1000
        
        assert segments_per_second >= PERFORMANCE_BENCHMARKS['segments_per_second'] * 0.8, \
            f"Medium file processing speed {segments_per_second:.0f} segments/s below 80% of benchmark"
        
        # Memory usage should be reasonable
        assert metrics['end_memory_mb'] < PERFORMANCE_BENCHMARKS['memory_limit_mb'], \
            f"Memory usage {metrics['end_memory_mb']:.1f}MB exceeds limit {PERFORMANCE_BENCHMARKS['memory_limit_mb']}MB"
        
        # Cleanup
        temp_file.unlink()
        if output_file.exists():
            output_file.unlink()

    def test_large_file_processing_speed(self, temp_lexicons, performance_tracker):
        """Test processing speed with large files (500 segments)."""
        processor = SanskritProcessor(temp_lexicons)
        
        temp_file = Path(tempfile.mktemp(suffix='.srt'))
        temp_file.write_text(LARGE_SRT_CONTENT)
        output_file = Path(tempfile.mktemp(suffix='.srt'))
        
        performance_tracker.start()
        result = processor.process_srt_file(str(temp_file), str(output_file))
        metrics = performance_tracker.stop()
        
        segments_per_second = (result.segments_processed / metrics['duration_ms']) * 1000
        
        # Should meet full benchmark for large files
        assert segments_per_second >= PERFORMANCE_BENCHMARKS['segments_per_second'], \
            f"Large file processing speed {segments_per_second:.0f} segments/s below benchmark {PERFORMANCE_BENCHMARKS['segments_per_second']}"
        
        # Memory usage should remain within limits
        assert metrics['end_memory_mb'] < PERFORMANCE_BENCHMARKS['memory_limit_mb'], \
            f"Memory usage {metrics['end_memory_mb']:.1f}MB exceeds limit {PERFORMANCE_BENCHMARKS['memory_limit_mb']}MB"
        
        # Memory growth should be controlled
        assert metrics['memory_delta_mb'] < PERFORMANCE_BENCHMARKS['memory_growth_mb'], \
            f"Memory growth {metrics['memory_delta_mb']:.1f}MB exceeds limit {PERFORMANCE_BENCHMARKS['memory_growth_mb']}MB"
        
        # Cleanup
        temp_file.unlink()
        if output_file.exists():
            output_file.unlink()

    def test_memory_efficiency(self, temp_lexicons):
        """Test memory usage patterns during processing."""
        processor = SanskritProcessor(temp_lexicons)
        
        # Measure memory at different stages
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        temp_file = Path(tempfile.mktemp(suffix='.srt'))
        temp_file.write_text(LARGE_SRT_CONTENT)
        output_file = Path(tempfile.mktemp(suffix='.srt'))
        
        # Process file and measure memory
        result = processor.process_srt_file(str(temp_file), str(output_file))
        processing_memory = process.memory_info().rss / 1024 / 1024
        
        memory_usage = processing_memory - baseline_memory
        
        assert memory_usage < PERFORMANCE_BENCHMARKS['memory_limit_mb'], \
            f"Processing memory usage {memory_usage:.1f}MB exceeds benchmark {PERFORMANCE_BENCHMARKS['memory_limit_mb']}MB"
        
        # Cleanup
        temp_file.unlink()
        if output_file.exists():
            output_file.unlink()

    def test_cache_performance(self, temp_lexicons):
        """Test lexicon cache performance and hit ratios."""
        processor = SanskritProcessor(temp_lexicons)
        
        # Process same content multiple times to test caching
        temp_file = Path(tempfile.mktemp(suffix='.srt'))
        temp_file.write_text(MEDIUM_SRT_CONTENT)
        
        processing_times = []
        
        for i in range(3):
            output_file = Path(tempfile.mktemp(suffix='.srt'))
            
            start_time = time.perf_counter()
            result = processor.process_srt_file(str(temp_file), str(output_file))
            end_time = time.perf_counter()
            
            processing_times.append(end_time - start_time)
            
            if output_file.exists():
                output_file.unlink()
        
        # Second and third runs should be faster due to caching
        if len(processing_times) >= 2:
            improvement = (processing_times[0] - processing_times[1]) / processing_times[0]
            assert improvement > 0.1, \
                f"Cache performance improvement {improvement:.1%} is below expected 10%"
        
        # Cleanup
        temp_file.unlink()

    def test_concurrent_processing_performance(self, temp_lexicons):
        """Test performance under concurrent processing loads."""
        import threading
        import queue
        
        processor = SanskritProcessor(temp_lexicons)
        
        # Create test files
        test_files = []
        for i in range(3):
            temp_file = Path(tempfile.mktemp(suffix='.srt'))
            temp_file.write_text(MEDIUM_SRT_CONTENT)
            test_files.append(temp_file)
        
        results_queue = queue.Queue()
        
        def process_file(file_path):
            output_file = Path(tempfile.mktemp(suffix='.srt'))
            start_time = time.perf_counter()
            
            try:
                result = processor.process_srt_file(str(file_path), str(output_file))
                end_time = time.perf_counter()
                
                segments_per_second = result.segments_processed / (end_time - start_time)
                results_queue.put(segments_per_second)
                
            finally:
                if output_file.exists():
                    output_file.unlink()
        
        # Process files concurrently
        threads = []
        start_time = time.perf_counter()
        
        for test_file in test_files:
            thread = threading.Thread(target=process_file, args=(test_file,))
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
        
        end_time = time.perf_counter()
        
        # Collect results
        performance_results = []
        while not results_queue.empty():
            performance_results.append(results_queue.get())
        
        # All concurrent processes should maintain reasonable performance
        min_performance = min(performance_results) if performance_results else 0
        assert min_performance >= PERFORMANCE_BENCHMARKS['segments_per_second'] * 0.7, \
            f"Concurrent processing minimum performance {min_performance:.0f} segments/s below 70% of benchmark"
        
        # Cleanup
        for test_file in test_files:
            test_file.unlink()


class TestEnhancedProcessorPerformance:
    """Performance tests for enhanced processor with external services."""
    
    @pytest.fixture
    def temp_config(self, temp_lexicons):
        """Create temporary configuration for enhanced processor."""
        temp_dir = temp_lexicons.parent
        config_file = temp_dir / "config.yaml"
        
        config = {
            'processing': {
                'use_consolidated_services': False,  # Disable for performance testing
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8},
                'caching': {'enabled': True, 'max_corrections': 2000}
            },
            'performance': {
                'profiling': {'enabled': False},
                'monitoring': {'track_service_response_times': False}
            }
        }
        
        import yaml
        config_file.write_text(yaml.dump(config))
        return config_file

    def test_enhanced_processor_overhead(self, temp_lexicons, temp_config):
        """Test that enhanced processor doesn't add significant overhead when services disabled."""
        # Test basic processor
        basic_processor = SanskritProcessor(temp_lexicons)
        
        temp_file = Path(tempfile.mktemp(suffix='.srt'))
        temp_file.write_text(MEDIUM_SRT_CONTENT)
        
        # Measure basic processor
        output_file1 = Path(tempfile.mktemp(suffix='.srt'))
        start_time = time.perf_counter()
        result1 = basic_processor.process_srt_file(str(temp_file), str(output_file1))
        basic_time = time.perf_counter() - start_time
        
        # Measure enhanced processor (services disabled)
        enhanced_processor = EnhancedSanskritProcessor(temp_lexicons, temp_config)
        output_file2 = Path(tempfile.mktemp(suffix='.srt'))
        start_time = time.perf_counter()
        result2 = enhanced_processor.process_srt_file(str(temp_file), str(output_file2))
        enhanced_time = time.perf_counter() - start_time
        
        # Enhanced processor should have minimal overhead (<20%)
        overhead = (enhanced_time - basic_time) / basic_time
        assert overhead < 0.2, \
            f"Enhanced processor overhead {overhead:.1%} exceeds 20% limit"
        
        # Results should be equivalent
        assert result1.segments_processed == result2.segments_processed
        
        # Cleanup
        temp_file.unlink()
        for f in [output_file1, output_file2]:
            if f.exists():
                f.unlink()


class TestPerformanceHistory:
    """Track performance over time and detect regressions."""
    
    PERFORMANCE_HISTORY_FILE = Path("tests/performance_history.json")
    
    def load_performance_history(self) -> List[Dict[str, Any]]:
        """Load historical performance data."""
        if not self.PERFORMANCE_HISTORY_FILE.exists():
            return []
        
        try:
            with open(self.PERFORMANCE_HISTORY_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def save_performance_result(self, test_name: str, metrics: Dict[str, float]):
        """Save performance result to history."""
        history = self.load_performance_history()
        
        result = {
            'timestamp': time.time(),
            'test_name': test_name,
            'metrics': metrics
        }
        
        history.append(result)
        
        # Keep only last 100 results to prevent file from growing too large
        history = history[-100:]
        
        self.PERFORMANCE_HISTORY_FILE.parent.mkdir(exist_ok=True)
        with open(self.PERFORMANCE_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    
    def check_regression(self, test_name: str, current_metric: float, metric_name: str) -> bool:
        """Check if current performance shows regression."""
        history = self.load_performance_history()
        
        # Get recent results for this test
        recent_results = [
            r for r in history[-10:] 
            if r['test_name'] == test_name and metric_name in r['metrics']
        ]
        
        if len(recent_results) < 3:
            return True  # Not enough history, assume OK
        
        recent_values = [r['metrics'][metric_name] for r in recent_results]
        historical_median = statistics.median(recent_values)
        
        # Allow 10% degradation before flagging as regression
        regression_threshold = historical_median * 1.1
        
        return current_metric <= regression_threshold

    def test_performance_tracking_integration(self, temp_lexicons):
        """Integration test for performance tracking."""
        processor = SanskritProcessor(temp_lexicons)
        
        temp_file = Path(tempfile.mktemp(suffix='.srt'))
        temp_file.write_text(MEDIUM_SRT_CONTENT)
        output_file = Path(tempfile.mktemp(suffix='.srt'))
        
        # Measure performance
        start_time = time.perf_counter()
        result = processor.process_srt_file(str(temp_file), str(output_file))
        end_time = time.perf_counter()
        
        processing_time = end_time - start_time
        segments_per_second = result.segments_processed / processing_time
        
        # Save results
        metrics = {
            'processing_time_ms': processing_time * 1000,
            'segments_per_second': segments_per_second,
            'segments_processed': result.segments_processed,
            'corrections_applied': result.corrections_applied
        }
        
        self.save_performance_result('medium_file_processing', metrics)
        
        # Check for regression
        assert self.check_regression('medium_file_processing', processing_time, 'processing_time_ms'), \
            f"Performance regression detected: current time {processing_time:.3f}s"
        
        # Cleanup
        temp_file.unlink()
        if output_file.exists():
            output_file.unlink()


@pytest.mark.performance
class TestBenchmarkSuite:
    """Comprehensive benchmark suite for performance validation."""
    
    def test_full_benchmark_suite(self, temp_lexicons):
        """Run complete benchmark suite and validate all performance criteria."""
        processor = SanskritProcessor(temp_lexicons)
        
        benchmark_results = {}
        
        # Test different file sizes
        test_cases = [
            ('small', SMALL_SRT_CONTENT, 2),
            ('medium', MEDIUM_SRT_CONTENT, 50),
            ('large', LARGE_SRT_CONTENT, 500)
        ]
        
        for size_name, content, expected_segments in test_cases:
            temp_file = Path(tempfile.mktemp(suffix='.srt'))
            temp_file.write_text(content)
            output_file = Path(tempfile.mktemp(suffix='.srt'))
            
            # Measure performance
            start_time = time.perf_counter()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024
            
            result = processor.process_srt_file(str(temp_file), str(output_file))
            
            end_time = time.perf_counter()
            end_memory = process.memory_info().rss / 1024 / 1024
            
            # Calculate metrics
            processing_time = end_time - start_time
            segments_per_second = result.segments_processed / processing_time
            memory_used = end_memory - start_memory
            
            benchmark_results[size_name] = {
                'segments_per_second': segments_per_second,
                'processing_time_ms': processing_time * 1000,
                'memory_used_mb': memory_used,
                'segments_processed': result.segments_processed,
                'corrections_applied': result.corrections_applied
            }
            
            # Validate against benchmarks
            if size_name == 'large':  # Full benchmark for large files
                assert segments_per_second >= PERFORMANCE_BENCHMARKS['segments_per_second'], \
                    f"{size_name} file: {segments_per_second:.0f} segments/s below benchmark {PERFORMANCE_BENCHMARKS['segments_per_second']}"
            
            # Memory validation for all sizes
            assert end_memory < PERFORMANCE_BENCHMARKS['memory_limit_mb'], \
                f"{size_name} file: Memory usage {end_memory:.1f}MB exceeds {PERFORMANCE_BENCHMARKS['memory_limit_mb']}MB"
            
            # Cleanup
            temp_file.unlink()
            if output_file.exists():
                output_file.unlink()
        
        # Print benchmark summary
        print("\n=== PERFORMANCE BENCHMARK RESULTS ===")
        for size_name, metrics in benchmark_results.items():
            print(f"{size_name.upper()} FILE:")
            print(f"  Segments/sec: {metrics['segments_per_second']:.0f}")
            print(f"  Processing time: {metrics['processing_time_ms']:.1f}ms")
            print(f"  Memory used: {metrics['memory_used_mb']:.1f}MB")
            print(f"  Segments processed: {metrics['segments_processed']}")
            print(f"  Corrections applied: {metrics['corrections_applied']}")
        print("=" * 40)


if __name__ == "__main__":
    # Run performance tests
    pytest.main([
        __file__, 
        "-v", 
        "--tb=short",
        "-m", "performance",
        "--durations=10"
    ])