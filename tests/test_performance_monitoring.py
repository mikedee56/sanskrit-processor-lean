"""
Tests for Performance Monitoring Framework
Part of the Sanskrit Processor Lean Architecture - Story 5.6
"""

import pytest
import time
import os
from pathlib import Path

from utils.performance_profiler import PerformanceProfiler


class TestPerformanceProfiler:
    """Test the PerformanceProfiler class."""
    
    def test_profiler_disabled_zero_overhead(self):
        """Test that disabled profiler has zero overhead."""
        profiler = PerformanceProfiler(enabled=False)
        
        # Measure timing without profiler
        start_time = time.perf_counter()
        for _ in range(1000):
            pass  # Simple loop
        no_profiler_time = time.perf_counter() - start_time
        
        # Measure timing with disabled profiler
        profiler = PerformanceProfiler(enabled=False)
        start_time = time.perf_counter()
        with profiler.profile_stage("test_stage"):
            for _ in range(1000):
                pass  # Same simple loop
        with_disabled_profiler_time = time.perf_counter() - start_time
        
        # Should have minimal overhead (within 20%)
        overhead_ratio = with_disabled_profiler_time / no_profiler_time
        assert overhead_ratio < 1.2, f"Disabled profiler has {((overhead_ratio-1)*100):.1f}% overhead, expected <20%"
        
        # Report should indicate profiling is disabled
        report = profiler.generate_report()
        assert report == {"profiling": "disabled"}
    
    def test_profiler_enabled_captures_timing(self):
        """Test that enabled profiler captures timing data."""
        profiler = PerformanceProfiler(enabled=True)
        
        with profiler.profile_stage("test_processing"):
            time.sleep(0.05)  # Simulate 50ms of processing
        
        report = profiler.generate_report()
        
        assert "total_duration" in report
        assert report["total_duration"] >= 0.05
        assert "test_processing" in report["stage_timings"]
        assert report["stage_timings"]["test_processing"]["duration"] >= 0.05
    
    def test_profiler_memory_tracking(self):
        """Test memory usage tracking functionality."""
        profiler = PerformanceProfiler(enabled=True)
        
        with profiler.profile_stage("memory_test"):
            # Allocate some memory
            data = [0] * 100000  # Allocate ~800KB
            time.sleep(0.01)  # Small delay to ensure measurement
            del data  # Clean up
        
        report = profiler.generate_report()
        
        assert "peak_memory_mb" in report
        assert "memory_test" in report["stage_timings"]
        
        # Memory measurements should be present (may be None if psutil unavailable)
        memory_info = report["stage_timings"]["memory_test"]
        if memory_info["memory_start"] is not None:
            assert isinstance(memory_info["memory_start"], int)
            assert isinstance(memory_info["memory_end"], int)
    
    def test_profiler_multiple_stages(self):
        """Test profiling multiple stages."""
        profiler = PerformanceProfiler(enabled=True)
        
        with profiler.profile_stage("initialization"):
            time.sleep(0.01)
        
        with profiler.profile_stage("processing"):
            time.sleep(0.02)
        
        with profiler.profile_stage("cleanup"):
            time.sleep(0.01)
        
        report = profiler.generate_report()
        
        assert len(report["stage_timings"]) == 3
        assert "initialization" in report["stage_timings"]
        assert "processing" in report["stage_timings"]
        assert "cleanup" in report["stage_timings"]
        
        # Processing should be the longest stage
        processing_time = report["stage_timings"]["processing"]["duration"]
        init_time = report["stage_timings"]["initialization"]["duration"]
        cleanup_time = report["stage_timings"]["cleanup"]["duration"]
        
        assert processing_time > init_time
        assert processing_time > cleanup_time
    
    def test_profiler_recommendations(self):
        """Test recommendation generation."""
        profiler = PerformanceProfiler(enabled=True)
        
        # Create a scenario where processing is slow
        with profiler.profile_stage("initialization"):
            time.sleep(0.005)  # 5ms
        
        with profiler.profile_stage("processing"):
            time.sleep(0.02)   # 20ms - slowest stage
        
        with profiler.profile_stage("cleanup"):
            time.sleep(0.005)  # 5ms
        
        report = profiler.generate_report()
        recommendations = report["recommendations"]
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should identify processing as slowest stage
        processing_mentioned = any("processing" in rec for rec in recommendations)
        assert processing_mentioned
    
    def test_profiler_detail_levels(self):
        """Test different profiling detail levels."""
        # Test basic level
        profiler_basic = PerformanceProfiler(enabled=True, detail_level="basic")
        assert profiler_basic.detail_level == "basic"
        
        # Test detailed level
        profiler_detailed = PerformanceProfiler(enabled=True, detail_level="detailed")
        assert profiler_detailed.detail_level == "detailed"
        
        # Test full level
        profiler_full = PerformanceProfiler(enabled=True, detail_level="full")
        assert profiler_full.detail_level == "full"
    
    def test_profiler_without_psutil(self):
        """Test profiler behavior when psutil is not available."""
        profiler = PerformanceProfiler(enabled=True)
        
        # Temporarily disable psutil functionality
        original_process = profiler._process
        profiler._process = None
        
        try:
            with profiler.profile_stage("test_no_psutil"):
                time.sleep(0.01)
            
            report = profiler.generate_report()
            
            # Should still work, just without memory info
            assert "total_duration" in report
            assert "test_no_psutil" in report["stage_timings"]
            
            memory_info = report["stage_timings"]["test_no_psutil"]
            assert memory_info["memory_start"] is None
            assert memory_info["memory_end"] is None
            assert memory_info["memory_delta"] == 0
        
        finally:
            # Restore original state
            profiler._process = original_process


class TestPerformanceIntegration:
    """Test performance monitoring integration with CLI."""
    
    def test_cli_profiling_import(self):
        """Test that CLI can import performance profiler."""
        from utils.performance_profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        assert profiler is not None
        assert hasattr(profiler, 'profile_stage')
        assert hasattr(profiler, 'generate_report')
    
    def test_config_structure(self):
        """Test that config.yaml has performance section."""
        config_path = Path("config.yaml")
        if config_path.exists():
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            assert "performance" in config
            assert "profiling" in config["performance"]
            assert "enabled" in config["performance"]["profiling"]
            assert config["performance"]["profiling"]["enabled"] is False  # Default disabled


class TestZeroImpactValidation:
    """Critical tests to ensure zero performance impact when disabled."""
    
    def test_context_manager_overhead(self):
        """Test that context manager has minimal overhead when disabled."""
        profiler_disabled = PerformanceProfiler(enabled=False)
        
        # Time the context manager itself
        iterations = 10000
        
        # Without profiler
        start_time = time.perf_counter()
        for _ in range(iterations):
            pass
        baseline_time = time.perf_counter() - start_time
        
        # With disabled profiler
        start_time = time.perf_counter()
        for _ in range(iterations):
            with profiler_disabled.profile_stage("test"):
                pass
        profiled_time = time.perf_counter() - start_time
        
        # Should be within 10% of baseline (very strict)
        overhead_ratio = profiled_time / baseline_time if baseline_time > 0 else 1
        assert overhead_ratio < 1.1, f"Context manager has {((overhead_ratio-1)*100):.1f}% overhead, expected <10%"
    
    def test_memory_overhead_when_disabled(self):
        """Test that disabled profiler uses minimal memory."""
        profiler = PerformanceProfiler(enabled=False)
        
        # Object should be lightweight
        assert profiler.timings == {}
        assert profiler.start_time is None
        assert profiler._process is None
        
        # Using it shouldn't change anything
        with profiler.profile_stage("test"):
            pass
        
        assert profiler.timings == {}  # Should remain empty
    
    def test_nested_profiling_stages(self):
        """Test nested profiling stages work correctly."""
        profiler = PerformanceProfiler(enabled=True)
        
        with profiler.profile_stage("outer"):
            time.sleep(0.01)
            with profiler.profile_stage("inner"):
                time.sleep(0.01)
            time.sleep(0.01)
        
        report = profiler.generate_report()
        
        # Both stages should be recorded
        assert "outer" in report["stage_timings"]
        assert "inner" in report["stage_timings"]
        
        # Outer should be longer than inner
        outer_time = report["stage_timings"]["outer"]["duration"]
        inner_time = report["stage_timings"]["inner"]["duration"]
        assert outer_time > inner_time


if __name__ == "__main__":
    # Run basic functionality test
    print("Running basic performance profiler tests...")
    
    # Test disabled profiler
    profiler = PerformanceProfiler(enabled=False)
    with profiler.profile_stage("test"):
        time.sleep(0.01)
    report = profiler.generate_report()
    assert report == {"profiling": "disabled"}
    print("✅ Disabled profiler test passed")
    
    # Test enabled profiler
    profiler = PerformanceProfiler(enabled=True)
    with profiler.profile_stage("test"):
        time.sleep(0.01)
    report = profiler.generate_report()
    assert report["total_duration"] > 0.01
    print("✅ Enabled profiler test passed")
    
    print("✅ All basic tests passed!")