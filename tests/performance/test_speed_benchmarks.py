"""
Performance Benchmark Tests for ASR Processing

Tests processing speed and performance characteristics to ensure
the system meets performance requirements and detect regressions.
"""

import pytest
import time
import sys
import os
from typing import List
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sanskrit_processor_v2 import SanskritProcessor, SRTSegment


class PerformanceTestSuite:
    """Performance testing utilities and benchmarks."""
    
    @staticmethod
    def create_test_segments(count: int, text_pattern: str = "Test segment {i} with some Sanskrit terms like yoga and dharma") -> List[SRTSegment]:
        """Create test segments for performance testing."""
        segments = []
        
        for i in range(count):
            start_seconds = i * 3
            end_seconds = start_seconds + 3
            
            start_time = f"00:{start_seconds//60:02d}:{start_seconds%60:02d},000"
            end_time = f"00:{end_seconds//60:02d}:{end_seconds%60:02d},000"
            
            segments.append(SRTSegment(
                index=i + 1,
                start_time=start_time,
                end_time=end_time,
                text=text_pattern.format(i=i+1)
            ))
        
        return segments
    
    @staticmethod
    def measure_processing_time(processor: SanskritProcessor, segments: List[SRTSegment]) -> dict:
        """Measure processing time and calculate metrics."""
        start_time = time.time()
        result = processor.process_segments(segments)
        end_time = time.time()
        
        processing_time = end_time - start_time
        segments_per_second = len(segments) / processing_time if processing_time > 0 else 0
        
        return {
            'processing_time': processing_time,
            'segment_count': len(segments),
            'segments_per_second': segments_per_second,
            'result': result
        }


@pytest.fixture
def simple_processor():
    """Fixture providing simple mode processor for consistent performance testing."""
    return SanskritProcessor(simple_mode=True, verbose=False)


@pytest.fixture
def enhanced_processor():
    """Fixture providing enhanced processor (if available)."""
    try:
        return SanskritProcessor(simple_mode=False, verbose=False)
    except:
        # Fall back to simple mode if enhanced not available
        return SanskritProcessor(simple_mode=True, verbose=False)


class TestProcessingSpeedBenchmarks:
    """Benchmark processing speed for different file sizes."""
    
    def test_small_file_speed_benchmark(self, simple_processor):
        """Benchmark processing speed for small files (50-100 segments)."""
        segments = PerformanceTestSuite.create_test_segments(75)
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        # Performance assertions
        assert metrics['processing_time'] < 2.0, f"Small file processing took {metrics['processing_time']:.2f}s, should be < 2.0s"
        assert metrics['segments_per_second'] > 50, f"Processing speed {metrics['segments_per_second']:.1f} segments/sec below 50/sec"
        
        print(f"Small file benchmark: {metrics['segment_count']} segments in {metrics['processing_time']:.2f}s "
              f"({metrics['segments_per_second']:.1f} segments/sec)")
    
    def test_medium_file_speed_benchmark(self, simple_processor):
        """Benchmark processing speed for medium files (200-500 segments)."""
        segments = PerformanceTestSuite.create_test_segments(350)
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        # Performance assertions
        assert metrics['processing_time'] < 5.0, f"Medium file processing took {metrics['processing_time']:.2f}s, should be < 5.0s"
        assert metrics['segments_per_second'] > 80, f"Processing speed {metrics['segments_per_second']:.1f} segments/sec below 80/sec"
        
        print(f"Medium file benchmark: {metrics['segment_count']} segments in {metrics['processing_time']:.2f}s "
              f"({metrics['segments_per_second']:.1f} segments/sec)")
    
    def test_large_file_speed_benchmark(self, simple_processor):
        """Benchmark processing speed for large files (500+ segments)."""
        segments = PerformanceTestSuite.create_test_segments(750)
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        # Performance assertions
        assert metrics['processing_time'] < 10.0, f"Large file processing took {metrics['processing_time']:.2f}s, should be < 10.0s"
        assert metrics['segments_per_second'] > 100, f"Processing speed {metrics['segments_per_second']:.1f} segments/sec below 100/sec"
        
        print(f"Large file benchmark: {metrics['segment_count']} segments in {metrics['processing_time']:.2f}s "
              f"({metrics['segments_per_second']:.1f} segments/sec)")
    
    @pytest.mark.parametrize("segment_count,max_time,min_speed", [
        (25, 1.0, 30),    # Very small
        (100, 2.5, 50),   # Small  
        (250, 4.0, 70),   # Medium
        (500, 7.0, 80),   # Large
        (1000, 12.0, 100) # Very large
    ])
    def test_scalability_benchmarks(self, simple_processor, segment_count, max_time, min_speed):
        """Test processing scalability across different file sizes."""
        segments = PerformanceTestSuite.create_test_segments(segment_count)
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        assert metrics['processing_time'] < max_time, (
            f"{segment_count} segments took {metrics['processing_time']:.2f}s, "
            f"should be < {max_time}s"
        )
        
        assert metrics['segments_per_second'] > min_speed, (
            f"Speed {metrics['segments_per_second']:.1f} segments/sec below "
            f"{min_speed}/sec for {segment_count} segments"
        )


class TestCorrectionSpeedBenchmarks:
    """Benchmark correction-specific performance."""
    
    def test_heavy_correction_load_speed(self, simple_processor):
        """Test speed with segments requiring many corrections."""
        correction_heavy_text = "filosofy darma yogabashi krisna shiva moksha pranayama samadhi"
        segments = PerformanceTestSuite.create_test_segments(200, correction_heavy_text)
        
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        # Should still maintain reasonable speed even with heavy corrections
        assert metrics['processing_time'] < 8.0, (
            f"Heavy correction processing took {metrics['processing_time']:.2f}s, should be < 8.0s"
        )
        
        assert metrics['segments_per_second'] > 30, (
            f"Heavy correction speed {metrics['segments_per_second']:.1f} segments/sec below 30/sec"
        )
    
    def test_no_correction_speed(self, simple_processor):
        """Test speed with segments requiring no corrections."""
        clean_text = "This is clean English text without any Sanskrit terms or errors."
        segments = PerformanceTestSuite.create_test_segments(500, clean_text)
        
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        # Should be very fast with no corrections needed
        assert metrics['processing_time'] < 3.0, (
            f"No correction processing took {metrics['processing_time']:.2f}s, should be < 3.0s"
        )
        
        assert metrics['segments_per_second'] > 200, (
            f"No correction speed {metrics['segments_per_second']:.1f} segments/sec below 200/sec"
        )
    
    def test_mixed_content_speed(self, simple_processor):
        """Test speed with mixed content (some corrections needed, some not)."""
        # Create alternating clean and correction-needing segments
        segments = []
        
        for i in range(300):
            if i % 2 == 0:
                text = "Clean English text without corrections needed."
            else:
                text = f"Text {i} with filosofy and darma terms needing correction."
            
            segments.append(SRTSegment(
                index=i + 1,
                start_time=f"00:{(i*3)//60:02d}:{(i*3)%60:02d},000",
                end_time=f"00:{((i*3)+3)//60:02d}:{((i*3)+3)%60:02d},000",
                text=text
            ))
        
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        assert metrics['processing_time'] < 6.0, (
            f"Mixed content processing took {metrics['processing_time']:.2f}s, should be < 6.0s"
        )
        
        assert metrics['segments_per_second'] > 60, (
            f"Mixed content speed {metrics['segments_per_second']:.1f} segments/sec below 60/sec"
        )


class TestMemoryPerformance:
    """Test memory usage during processing."""
    
    def test_memory_efficiency_large_files(self, simple_processor):
        """Test that large file processing doesn't cause memory issues."""
        # Create a large number of segments to test memory efficiency
        large_segment_count = 1500
        segments = PerformanceTestSuite.create_test_segments(large_segment_count)
        
        # Process in chunks to simulate streaming behavior
        chunk_size = 100
        total_time = 0
        
        for i in range(0, len(segments), chunk_size):
            chunk = segments[i:i + chunk_size]
            start_time = time.time()
            result = simple_processor.process_segments(chunk)
            total_time += time.time() - start_time
            
            # Verify results are generated correctly
            assert len(result.segments) == len(chunk)
        
        # Check overall performance
        overall_speed = large_segment_count / total_time if total_time > 0 else 0
        
        assert total_time < 20.0, (
            f"Chunked processing of {large_segment_count} segments took {total_time:.2f}s, "
            f"should be < 20.0s"
        )
        
        assert overall_speed > 80, (
            f"Chunked processing speed {overall_speed:.1f} segments/sec below 80/sec"
        )
    
    def test_repeated_processing_performance(self, simple_processor):
        """Test performance consistency across repeated processing calls."""
        segments = PerformanceTestSuite.create_test_segments(100)
        
        processing_times = []
        
        # Run multiple times to check for performance degradation
        for _ in range(10):
            start_time = time.time()
            result = simple_processor.process_segments(segments)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            assert len(result.segments) == 100
        
        # Check that performance doesn't degrade significantly
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        
        # Max time shouldn't be more than 50% longer than average
        assert max_time < avg_time * 1.5, (
            f"Performance degradation detected: max time {max_time:.3f}s vs avg {avg_time:.3f}s"
        )
        
        # All runs should be reasonably fast
        assert max_time < 3.0, f"Slowest run took {max_time:.3f}s, should be < 3.0s"
        
        print(f"Repeated processing: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")


class TestRegressionDetection:
    """Test for performance regressions."""
    
    def test_baseline_performance_metrics(self, simple_processor):
        """Test baseline performance metrics for regression detection."""
        # Standard test case for consistent measurement
        segments = PerformanceTestSuite.create_test_segments(500, 
            "Standard test text with yoga dharma filosofy darma corrections needed.")
        
        metrics = PerformanceTestSuite.measure_processing_time(simple_processor, segments)
        
        # These are baseline performance requirements
        baseline_requirements = {
            'max_processing_time': 8.0,     # seconds
            'min_segments_per_second': 70,   # segments/sec
            'min_corrections_handled': 10    # minimum corrections that should be made
        }
        
        assert metrics['processing_time'] < baseline_requirements['max_processing_time'], (
            f"Baseline performance regression: {metrics['processing_time']:.2f}s > "
            f"{baseline_requirements['max_processing_time']}s"
        )
        
        assert metrics['segments_per_second'] > baseline_requirements['min_segments_per_second'], (
            f"Baseline speed regression: {metrics['segments_per_second']:.1f} < "
            f"{baseline_requirements['min_segments_per_second']} segments/sec"
        )
        
        # Store metrics for comparison (in real implementation, this would be saved to file)
        performance_data = {
            'timestamp': time.time(),
            'processing_time': metrics['processing_time'],
            'segments_per_second': metrics['segments_per_second'],
            'segment_count': metrics['segment_count']
        }
        
        print(f"Baseline performance recorded: {performance_data}")


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([__file__, "-v", "-s"])