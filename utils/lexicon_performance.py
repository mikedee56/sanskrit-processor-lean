"""Performance optimization utilities for lexicon expansion."""

import time
import psutil
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from lexicons.hybrid_lexicon_loader import HybridLexiconLoader

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for lexicon operations."""
    load_time: float
    memory_usage_mb: float
    total_terms: int
    asr_terms: int
    cache_hit_rate: float
    database_hit_rate: float
    yaml_hit_rate: float
    
    def meets_requirements(self) -> bool:
        """Check if performance meets story requirements."""
        return (
            self.load_time < 1.0 and  # < 1 second load time
            self.memory_usage_mb < 150.0  # < 150MB memory usage
        )
    
    def __str__(self) -> str:
        status = "✓ PASS" if self.meets_requirements() else "✗ FAIL"
        return f"""Performance Metrics ({status}):
  Load time: {self.load_time:.3f}s (target: <1.000s)
  Memory usage: {self.memory_usage_mb:.1f}MB (target: <150MB)
  Total terms: {self.total_terms:,}
  ASR terms: {self.asr_terms:,}
  Database hit rate: {self.database_hit_rate:.1f}%
  YAML hit rate: {self.yaml_hit_rate:.1f}%
  Cache hit rate: {self.cache_hit_rate:.1f}%"""

class LexiconPerformanceOptimizer:
    """Optimizes lexicon performance and monitors metrics."""
    
    def __init__(self, lexicon_dir: Path, config: dict = None):
        self.lexicon_dir = lexicon_dir
        self.config = config or {}
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def measure_load_performance(self, enable_lazy_loading: bool = False) -> PerformanceMetrics:
        """Measure lexicon loading performance."""
        # Record baseline memory
        baseline_memory = self.get_memory_usage()
        
        # Measure load time
        start_time = time.time()
        
        # Configure for performance if requested
        config = self.config.copy()
        if enable_lazy_loading:
            config['lexicons'] = config.get('lexicons', {})
            config['lexicons']['lazy_asr_loading'] = True
        
        # Load lexicon
        loader = HybridLexiconLoader(self.lexicon_dir, config)
        
        load_time = time.time() - start_time
        
        # Measure memory after loading
        post_load_memory = self.get_memory_usage()
        memory_usage = post_load_memory - baseline_memory
        
        # Get statistics
        stats = loader.get_stats()
        
        # Count terms (estimate from stats)
        total_lookups = stats.get('total_lookups', 0)
        
        # Estimate ASR terms from loader
        asr_terms = 0
        try:
            # Quick count of ASR entries
            for key, value in loader.corrections.items():
                if isinstance(value, dict) and value.get('asr_common_error'):
                    asr_terms += 1
                    if asr_terms > 100:  # Sampling to avoid full scan
                        asr_terms = int(asr_terms * (len(loader.corrections) / 100))
                        break
        except Exception:
            asr_terms = 0
        
        # Calculate hit rates
        total_hits = stats.get('database_hits', 0) + stats.get('yaml_hits', 0)
        database_hit_rate = (stats.get('database_hits', 0) / total_hits * 100) if total_hits > 0 else 0
        yaml_hit_rate = (stats.get('yaml_hits', 0) / total_hits * 100) if total_hits > 0 else 0
        
        loader.close()
        
        return PerformanceMetrics(
            load_time=load_time,
            memory_usage_mb=memory_usage,
            total_terms=len(loader.corrections) + len(loader.proper_nouns),
            asr_terms=asr_terms,
            cache_hit_rate=0.0,  # Will be measured during actual usage
            database_hit_rate=database_hit_rate,
            yaml_hit_rate=yaml_hit_rate
        )
    
    def benchmark_lookup_performance(self, test_terms: list, iterations: int = 1000) -> Dict[str, float]:
        """Benchmark lookup performance for specific terms."""
        loader = HybridLexiconLoader(self.lexicon_dir, self.config)
        
        # Warm up
        for term in test_terms[:10]:
            try:
                _ = loader.corrections[term]
            except KeyError:
                pass
        
        # Benchmark corrections lookup
        start_time = time.time()
        for _ in range(iterations):
            for term in test_terms:
                try:
                    _ = loader.corrections[term]
                except KeyError:
                    pass
        corrections_time = time.time() - start_time
        
        # Benchmark proper nouns lookup
        start_time = time.time()
        for _ in range(iterations):
            for term in test_terms:
                try:
                    _ = loader.proper_nouns[term]
                except KeyError:
                    pass
        proper_nouns_time = time.time() - start_time
        
        loader.close()
        
        total_lookups = len(test_terms) * iterations * 2  # corrections + proper nouns
        
        return {
            'corrections_time': corrections_time,
            'proper_nouns_time': proper_nouns_time,
            'total_time': corrections_time + proper_nouns_time,
            'lookups_per_second': total_lookups / (corrections_time + proper_nouns_time),
            'avg_lookup_ms': (corrections_time + proper_nouns_time) / total_lookups * 1000
        }
    
    def profile_memory_usage(self, sample_interval: float = 0.1, duration: float = 5.0) -> Dict[str, float]:
        """Profile memory usage during lexicon operations."""
        baseline_memory = self.get_memory_usage()
        
        # Load lexicon
        loader = HybridLexiconLoader(self.lexicon_dir, self.config)
        load_memory = self.get_memory_usage()
        
        # Sample memory during operations
        memory_samples = []
        start_time = time.time()
        
        # Perform various operations
        test_terms = ['dharma', 'karma', 'yoga', 'krishna', 'rama', 'jnana', 'yogabashi']
        
        while time.time() - start_time < duration:
            for term in test_terms:
                try:
                    _ = loader.corrections[term]
                    _ = loader.proper_nouns[term]
                except KeyError:
                    pass
            
            memory_samples.append(self.get_memory_usage())
            time.sleep(sample_interval)
        
        loader.close()
        final_memory = self.get_memory_usage()
        
        return {
            'baseline_mb': baseline_memory,
            'post_load_mb': load_memory,
            'peak_mb': max(memory_samples) if memory_samples else load_memory,
            'average_mb': sum(memory_samples) / len(memory_samples) if memory_samples else load_memory,
            'final_mb': final_memory,
            'load_overhead_mb': load_memory - baseline_memory,
            'peak_overhead_mb': max(memory_samples) - baseline_memory if memory_samples else load_memory - baseline_memory
        }
    
    def optimize_database_queries(self) -> Dict[str, str]:
        """Recommend database query optimizations."""
        recommendations = {}
        
        # Check if database exists and is accessible
        db_path = Path('data/sanskrit_terms.db')
        if db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Check for indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]
                
                required_indexes = [
                    'idx_original_term', 'idx_asr_errors', 'idx_error_type', 
                    'idx_category', 'idx_confidence'
                ]
                
                missing_indexes = [idx for idx in required_indexes if idx not in indexes]
                if missing_indexes:
                    recommendations['missing_indexes'] = f"Add indexes: {', '.join(missing_indexes)}"
                else:
                    recommendations['indexes'] = "All required indexes present"
                
                # Check table statistics
                cursor.execute("SELECT COUNT(*) FROM terms")
                total_terms = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM terms WHERE asr_common_error = TRUE")
                asr_terms = cursor.fetchone()[0]
                
                recommendations['database_stats'] = f"Total terms: {total_terms}, ASR terms: {asr_terms}"
                
                # Check for ANALYZE statistics
                cursor.execute("SELECT COUNT(*) FROM sqlite_stat1")
                if cursor.fetchone()[0] == 0:
                    recommendations['analyze_needed'] = "Run ANALYZE to update query statistics"
                
                conn.close()
                
            except Exception as e:
                recommendations['database_error'] = f"Database check failed: {e}"
        else:
            recommendations['database_missing'] = "Database file not found"
        
        return recommendations
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report."""
        report = ["=== Lexicon Performance Report ===\n"]
        
        # Basic load performance
        report.append("1. Load Performance:")
        metrics = self.measure_load_performance()
        report.append(str(metrics))
        
        # Memory profiling
        report.append("\n2. Memory Profiling:")
        memory_profile = self.profile_memory_usage()
        for key, value in memory_profile.items():
            if isinstance(value, float):
                report.append(f"  {key}: {value:.1f}MB")
            else:
                report.append(f"  {key}: {value}")
        
        # Lookup performance
        report.append("\n3. Lookup Performance:")
        test_terms = ['dharma', 'karma', 'yoga', 'krishna', 'rama', 'jnana', 'yogabashi', 'shivashistha']
        lookup_perf = self.benchmark_lookup_performance(test_terms)
        for key, value in lookup_perf.items():
            if 'time' in key:
                report.append(f"  {key}: {value:.3f}s")
            elif 'per_second' in key:
                report.append(f"  {key}: {value:,.0f}")
            elif 'ms' in key:
                report.append(f"  {key}: {value:.2f}ms")
        
        # Database optimization
        report.append("\n4. Database Optimization:")
        db_recommendations = self.optimize_database_queries()
        for key, value in db_recommendations.items():
            report.append(f"  {key}: {value}")
        
        # Performance requirements check
        report.append(f"\n5. Requirements Check:")
        if metrics.meets_requirements():
            report.append("  ✓ All performance requirements met")
        else:
            report.append("  ✗ Performance requirements not met")
            if metrics.load_time >= 1.0:
                report.append(f"    - Load time too high: {metrics.load_time:.3f}s (target: <1.000s)")
            if metrics.memory_usage_mb >= 150.0:
                report.append(f"    - Memory usage too high: {metrics.memory_usage_mb:.1f}MB (target: <150MB)")
        
        return "\n".join(report)

def main():
    """Run performance analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze lexicon performance')
    parser.add_argument('--lexicon-dir', type=Path, default='lexicons',
                       help='Lexicon directory path')
    parser.add_argument('--config-file', type=Path, help='Config file path')
    parser.add_argument('--output', type=Path, help='Output report file')
    
    args = parser.parse_args()
    
    # Load config if provided
    config = {}
    if args.config_file and args.config_file.exists():
        import yaml
        with open(args.config_file) as f:
            config = yaml.safe_load(f)
    
    optimizer = LexiconPerformanceOptimizer(args.lexicon_dir, config)
    report = optimizer.generate_performance_report()
    
    if args.output:
        args.output.write_text(report)
        print(f"Performance report saved to {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()