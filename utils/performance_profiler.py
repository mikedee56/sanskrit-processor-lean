"""
Lightweight performance profiler with minimal overhead when disabled.
Part of the Sanskrit Processor Lean Architecture.
"""

import time
import contextlib
from typing import Dict, List, Optional, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceProfiler:
    """Lightweight performance profiler with minimal overhead."""
    
    def __init__(self, enabled: bool = False, detail_level: str = "basic"):
        self.enabled = enabled
        self.detail_level = detail_level
        self.timings: Dict[str, Dict[str, Any]] = {}
        self.start_time: Optional[float] = None
        self._process = None
        
        if self.enabled and PSUTIL_AVAILABLE:
            try:
                self._process = psutil.Process()
            except Exception:
                self._process = None
        
    @contextlib.contextmanager
    def profile_stage(self, stage_name: str):
        """Context manager for profiling processing stages."""
        if not self.enabled:
            yield
            return
            
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            
            self.timings[stage_name] = {
                'duration': end_time - start_time,
                'memory_start': start_memory,
                'memory_end': end_memory,
                'memory_delta': end_memory - start_memory if start_memory and end_memory else 0
            }
    
    def _get_memory_usage(self) -> Optional[int]:
        """Get current memory usage in bytes."""
        if not self.enabled or not self._process:
            return None
        try:
            return self._process.memory_info().rss
        except Exception:
            return None
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.enabled:
            return {"profiling": "disabled"}
            
        if not self.timings:
            return {"profiling": "enabled", "stages": "none"}
            
        total_time = sum(t['duration'] for t in self.timings.values())
        memory_values = [t['memory_end'] for t in self.timings.values() if t['memory_end']]
        peak_memory = max(memory_values) if memory_values else 0
        
        return {
            "total_duration": total_time,
            "peak_memory_mb": peak_memory / (1024 * 1024) if peak_memory else 0,
            "stage_timings": self.timings,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on profiling data."""
        recommendations = []
        
        if not self.timings:
            return recommendations
        
        total_time = sum(t['duration'] for t in self.timings.values())
        
        # Find slowest stage
        slowest_stage = max(self.timings.items(), key=lambda x: x[1]['duration'])
        slowest_percentage = (slowest_stage[1]['duration'] / total_time) * 100
        
        if slowest_stage[1]['duration'] > 1.0:  # More than 1 second
            recommendations.append(f"Consider optimizing {slowest_stage[0]} stage (slowest, {slowest_percentage:.1f}% of total time)")
        elif slowest_percentage > 60:  # More than 60% of total time
            recommendations.append(f"Consider optimizing {slowest_stage[0]} stage (consumes {slowest_percentage:.1f}% of processing time)")
        
        # Check memory usage
        memory_values = [t['memory_end'] for t in self.timings.values() if t['memory_end']]
        if memory_values:
            peak_memory_mb = max(memory_values) / (1024 * 1024)
            if peak_memory_mb > 100:  # More than 100MB
                recommendations.append(f"High memory usage detected ({peak_memory_mb:.1f}MB peak), consider optimization")
            elif peak_memory_mb > 50:  # More than 50MB
                recommendations.append(f"Moderate memory usage ({peak_memory_mb:.1f}MB peak), monitor for large files")
        
        # Check for memory leaks
        memory_deltas = [t['memory_delta'] for t in self.timings.values() if t['memory_delta'] and t['memory_delta'] > 0]
        if memory_deltas:
            total_memory_growth = sum(memory_deltas) / (1024 * 1024)  # Convert to MB
            if total_memory_growth > 10:  # More than 10MB growth
                recommendations.append(f"Potential memory leak detected ({total_memory_growth:.1f}MB growth)")
        
        # Performance rate recommendations
        if total_time > 0:
            if 'processing' in self.timings:
                processing_time = self.timings['processing']['duration']
                processing_percentage = (processing_time / total_time) * 100
                if processing_percentage < 50:  # Processing takes less than 50% of time
                    recommendations.append("Most time spent on initialization/cleanup - consider batch processing for multiple files")
        
        if not recommendations:
            recommendations.append("Performance appears optimal for current workload")
        
        return recommendations