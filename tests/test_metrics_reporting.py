"""
Test suite for Story 10.6: ASR Correction Metrics & Reporting.

Tests comprehensive metrics collection, reporting, export formats,
and historical tracking functionality.
"""

import pytest
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from utils.metrics_collector import MetricsCollector, CorrectionDetail
from utils.metrics_reporter import MetricsReporter, MetricsReport
from utils.historical_tracker import HistoricalTracker, HistoricalRun, TrendAnalysis


class TestMetricsCollector:
    """Test comprehensive metrics collection (AC: 1, 2, 3, 4, 6)."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.collector = MetricsCollector()
    
    def test_initialization(self):
        """Test metrics collector initialization."""
        assert self.collector.corrections_by_type == {}
        assert self.collector.correction_details == []
        assert self.collector.confidence_scores == []
        assert self.collector.correction_frequency == {}
        assert self.collector.sample_corrections == []
        assert self.collector.processing_phases == {}
    
    def test_processing_lifecycle(self):
        """Test complete processing lifecycle with metrics."""
        # Start processing
        self.collector.start_processing("test_file.srt", "enhanced", 100)
        assert self.collector.file_path == "test_file.srt"
        assert self.collector.processing_mode == "enhanced"
        assert self.collector.total_segments == 100
        
        # Phase timing
        self.collector.start_phase("parsing")
        self.collector.end_phase("parsing")
        assert "parsing" in self.collector.processing_phases
        
        # Record corrections
        self.collector.start_correction("lexicon", "krishna")
        self.collector.end_correction("lexicon", "krishna", "Kṛṣṇa", 0.95, segment_index=1)
        
        assert len(self.collector.correction_details) == 1
        assert self.collector.corrections_by_type["lexicon"] == 1
        assert len(self.collector.confidence_scores) == 1
        assert self.collector.confidence_scores[0] == 0.95
        
        # Finish processing
        self.collector.finish_processing(100)
        assert self.collector.end_time is not None
        assert self.collector.segments_per_second > 0
    
    def test_correction_frequency_tracking(self):
        """Test top corrections tracking (AC: 2)."""
        # Record multiple instances of same correction
        corrections = [
            ("jnana", "jñāna", 0.9),
            ("karma", "karma", 1.0),
            ("dharma", "dharma", 0.8),
            ("jnana", "jñāna", 0.95),  # Duplicate
            ("moksha", "mokṣa", 0.85),
            ("jnana", "jñāna", 0.92),  # Another duplicate
        ]
        
        for original, corrected, confidence in corrections:
            self.collector.start_correction("lexicon", original)
            self.collector.end_correction("lexicon", original, corrected, confidence)
        
        # Test top corrections
        top_corrections = self.collector.get_top_corrections(5)
        assert len(top_corrections) == 4  # 4 unique corrections
        
        # jnana->jñāna should be most frequent (3 times)
        assert top_corrections[0][0] == ("jnana", "jñāna")
        assert top_corrections[0][1] == 3
    
    def test_confidence_distribution(self):
        """Test confidence scoring and distribution (AC: 3)."""
        confidences = [0.95, 0.85, 0.75, 0.55, 0.45, 0.92, 0.88, 0.65]
        
        for i, confidence in enumerate(confidences):
            self.collector.start_correction("lexicon", f"word{i}")
            self.collector.end_correction("lexicon", f"word{i}", f"corrected{i}", confidence)
        
        distribution = self.collector.get_confidence_distribution()
        
        # Verify distribution calculation
        assert distribution['high (0.9-1.0)'] == 2  # 0.95, 0.92
        assert distribution['medium (0.7-0.9)'] == 3  # 0.85, 0.75, 0.88
        assert distribution['low (0.5-0.7)'] == 2   # 0.55, 0.65
        assert distribution['very_low (<0.5)'] == 1  # 0.45
    
    def test_sample_corrections(self):
        """Test before/after sample collection (AC: 4)."""
        sample_corrections = [
            ("yogabashi", "Yogavāsiṣṭha", 0.9, "lexicon"),
            ("shivashistha", "Vaśiṣṭha", 0.85, "fuzzy"),
            ("malagrasth", "mala-grasta", 0.8, "compound"),
        ]
        
        for i, (original, corrected, confidence, correction_type) in enumerate(sample_corrections):
            self.collector.start_correction(correction_type, original)
            self.collector.end_correction(correction_type, original, corrected, confidence, segment_index=i+1)
        
        samples = self.collector.get_sample_corrections(5)
        assert len(samples) == 3
        
        # Verify sample structure
        for sample in samples:
            assert 'original' in sample
            assert 'corrected' in sample
            assert 'confidence' in sample
            assert 'type' in sample
            assert 'segment' in sample
    
    def test_performance_metrics(self):
        """Test performance and resource tracking (AC: 6)."""
        self.collector.start_processing("test.srt", "enhanced")
        
        # Record cache performance
        self.collector.record_cache_hit()
        self.collector.record_cache_hit()
        self.collector.record_cache_miss()
        
        self.collector.finish_processing(50)
        
        performance = self.collector.get_performance_metrics()
        
        assert 'total_processing_time' in performance
        assert 'segments_per_second' in performance
        assert 'cache_performance' in performance
        
        cache_perf = performance['cache_performance']
        assert cache_perf['hits'] == 2
        assert cache_perf['misses'] == 1
        assert abs(cache_perf['hit_rate_percent'] - 66.7) < 0.1
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        # Add some corrections with varying confidence
        confidences = [0.9, 0.8, 0.95, 0.7, 0.85]
        for i, confidence in enumerate(confidences):
            self.collector.start_correction("lexicon", f"word{i}")
            self.collector.end_correction("lexicon", f"word{i}", f"corrected{i}", confidence)
        
        quality_score = self.collector.calculate_quality_score(100, 2)  # 100 segments, 2 errors
        
        assert 0 <= quality_score <= 100
        assert quality_score > 80  # Should be high with good confidence scores
    
    def test_input_validation(self):
        """Test robust input validation and error handling."""
        # Test invalid confidence scores
        self.collector.start_correction("lexicon", "test")
        self.collector.end_correction("lexicon", "test", "corrected", 1.5)  # Over 1.0
        assert self.collector.confidence_scores[-1] == 1.0  # Clamped
        
        self.collector.start_correction("lexicon", "test2")
        self.collector.end_correction("lexicon", "test2", "corrected", -0.1)  # Below 0.0
        assert self.collector.confidence_scores[-1] == 0.0  # Clamped
        
        # Test invalid types
        self.collector.start_correction("", "test")  # Empty correction type
        self.collector.end_correction("", "test", "corrected", "invalid")  # Invalid confidence type
        
        # Should handle gracefully without crashing


class TestMetricsReporter:
    """Test comprehensive metrics reporting and export formats (AC: 5)."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.collector = MetricsCollector()
        self.collector.start_processing("test_file.srt", "enhanced", 100)
        
        # Add sample data
        corrections = [
            ("jnana", "jñāna", 0.95, "lexicon"),
            ("karma", "karma", 1.0, "proper_noun"),
            ("moksha", "mokṣa", 0.85, "fuzzy"),
        ]
        
        for original, corrected, confidence, correction_type in corrections:
            self.collector.start_correction(correction_type, original)
            self.collector.end_correction(correction_type, original, corrected, confidence)
        
        self.collector.finish_processing(100)
        self.reporter = MetricsReporter(self.collector)
    
    def test_console_report_generation(self):
        """Test console report generation."""
        report = self.reporter.generate_console_report(verbose=False)
        
        assert "PROCESSING METRICS REPORT" in report
        assert "File: test_file.srt" in report
        assert "Mode: enhanced" in report
        assert "Segments: 100" in report
        assert "Corrections: 3" in report
        assert "TOP CORRECTIONS:" in report
        
        # Test verbose report
        verbose_report = self.reporter.generate_console_report(verbose=True)
        assert "SAMPLE CORRECTIONS:" in verbose_report
        assert "PERFORMANCE ANALYSIS:" in verbose_report
    
    def test_json_export(self, tmp_path):
        """Test JSON export functionality."""
        output_file = tmp_path / "metrics.json"
        self.reporter.export_json(output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Verify JSON structure
        assert 'metadata' in data
        assert 'summary' in data
        assert 'analysis' in data
        assert 'performance' in data
        assert 'raw_data' in data
        
        # Verify metadata
        metadata = data['metadata']
        assert metadata['file_path'] == "test_file.srt"
        assert metadata['processing_mode'] == "enhanced"
        assert metadata['processor_version'] == "10.6"
        
        # Verify analysis
        analysis = data['analysis']
        assert 'top_corrections' in analysis
        assert 'confidence_distribution' in analysis
        assert len(analysis['top_corrections']) > 0
    
    def test_html_export(self, tmp_path):
        """Test HTML report export."""
        output_file = tmp_path / "metrics.html"
        self.reporter.export_html(output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        # Verify HTML structure
        assert '<!DOCTYPE html>' in html_content
        assert 'Sanskrit Processor Metrics Report' in html_content
        assert 'Processing Summary' in html_content
        assert 'Top Corrections' in html_content
        assert 'test_file.srt' in html_content
        
        # Verify CSS styling is included
        assert 'metric-card' in html_content
        assert 'correction-sample' in html_content
    
    def test_csv_export(self, tmp_path):
        """Test CSV export functionality."""
        output_file = tmp_path / "metrics.csv"
        self.reporter.export_csv(output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Verify CSV structure
        lines = content.strip().split('\n')
        assert len(lines) >= 4  # Header + 3 corrections
        
        header = lines[0]
        assert 'original' in header
        assert 'corrected' in header
        assert 'confidence' in header
        assert 'type' in header
        
        # Verify data rows
        data_lines = lines[1:]
        for line in data_lines:
            fields = line.split(',')
            assert len(fields) >= 5  # All required fields


class TestHistoricalTracker:
    """Test historical tracking and trend analysis (AC: 7)."""
    
    def setup_method(self):
        """Setup test fixtures with temporary database."""
        self.db_path = Path("test_metrics.db")
        self.tracker = HistoricalTracker(self.db_path)
        
        # Create sample metrics
        self.collector = MetricsCollector()
        self.collector.start_processing("test.srt", "enhanced", 100)
        self.collector.finish_processing(100)
        
        self.reporter = MetricsReporter(self.collector)
    
    def teardown_method(self):
        """Clean up test database."""
        if self.db_path.exists():
            self.db_path.unlink()
    
    def test_database_initialization(self):
        """Test database setup and table creation."""
        # Verify database exists
        assert self.db_path.exists()
        
        # Verify table structure
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'processing_runs' in tables
    
    def test_run_storage(self):
        """Test storing processing runs in database."""
        run_id = self.tracker.store_run(self.collector, self.reporter.report)
        
        assert isinstance(run_id, int)
        assert run_id > 0
        
        # Verify data was stored
        runs = self.tracker.get_recent_runs(limit=1)
        assert len(runs) == 1
        assert runs[0].id == run_id
        assert runs[0].file_path == "test.srt"
        assert runs[0].processing_mode == "enhanced"
    
    def test_trend_analysis(self):
        """Test trend analysis and comparison."""
        # Store multiple runs with different metrics
        run1_collector = MetricsCollector()
        run1_collector.start_processing("test.srt", "enhanced", 100)
        run1_collector.finish_processing(100)
        run1_reporter = MetricsReporter(run1_collector)
        run1_reporter.report.quality_score = 85.0
        self.tracker.store_run(run1_collector, run1_reporter.report)
        
        # Second run with improved metrics
        run2_collector = MetricsCollector()
        run2_collector.start_processing("test.srt", "enhanced", 100)
        run2_collector.finish_processing(100)
        run2_reporter = MetricsReporter(run2_collector)
        run2_reporter.report.quality_score = 92.0
        
        # Compare with baseline
        comparison = self.tracker.compare_with_baseline(run2_reporter.report, baseline_days=1)
        
        assert comparison.current_run is not None
        assert comparison.baseline_run is not None
        assert len(comparison.trends) > 0
        assert len(comparison.recommendations) > 0
        
        # Check for improvement trend
        quality_trends = [t for t in comparison.trends if t.metric_name == "Quality Score"]
        if quality_trends:
            assert quality_trends[0].trend_direction == "improving"
    
    def test_recommendation_generation(self):
        """Test recommendation generation based on trends."""
        # Create trends with declining performance
        trends = [
            TrendAnalysis(
                metric_name="Quality Score",
                current_value=75.0,
                previous_value=85.0,
                change_percent=-11.8,
                trend_direction="declining",
                significance="significant"
            ),
            TrendAnalysis(
                metric_name="Processing Speed",
                current_value=450.0,
                previous_value=500.0,
                change_percent=-10.0,
                trend_direction="declining",
                significance="significant"
            )
        ]
        
        recommendations = self.tracker._generate_recommendations(trends)
        
        assert len(recommendations) > 0
        assert any("Quality score" in rec for rec in recommendations)
        assert any("Processing speed" in rec or "performance" in rec.lower() for rec in recommendations)


class TestIntegration:
    """Integration tests for complete metrics workflow."""
    
    def test_end_to_end_metrics_workflow(self, tmp_path):
        """Test complete metrics collection, reporting, and export workflow."""
        # Initialize metrics collector
        collector = MetricsCollector()
        collector.start_processing("integration_test.srt", "enhanced", 50)
        
        # Simulate processing with corrections
        collector.start_phase("parsing")
        collector.end_phase("parsing")
        
        collector.start_phase("processing")
        
        # Add various corrections
        corrections = [
            ("jnana", "jñāna", 0.95, "lexicon"),
            ("krishna", "Kṛṣṇa", 1.0, "proper_noun"),
            ("moksha", "mokṣa", 0.85, "fuzzy"),
            ("dharma", "dharma", 0.9, "lexicon"),
        ]
        
        for i, (original, corrected, confidence, correction_type) in enumerate(corrections):
            collector.start_correction(correction_type, original)
            collector.end_correction(correction_type, original, corrected, confidence, segment_index=i+1)
        
        collector.end_phase("processing")
        collector.finish_processing(50)
        
        # Create reporter and export all formats
        reporter = MetricsReporter(collector)
        
        json_file = tmp_path / "metrics.json"
        html_file = tmp_path / "metrics.html"
        csv_file = tmp_path / "metrics.csv"
        
        reporter.export_json(json_file)
        reporter.export_html(html_file)
        reporter.export_csv(csv_file)
        
        # Verify all exports
        assert json_file.exists()
        assert html_file.exists()
        assert csv_file.exists()
        
        # Test console report
        console_report = reporter.generate_console_report(verbose=True)
        assert "integration_test.srt" in console_report
        assert "jñāna" in console_report
        
        # Test historical tracking
        db_path = tmp_path / "test_history.db"
        tracker = HistoricalTracker(db_path)
        run_id = tracker.store_run(collector, reporter.report)
        
        assert run_id > 0
        
        runs = tracker.get_recent_runs(limit=1)
        assert len(runs) == 1
        assert runs[0].corrections_made == 4
    
    def test_error_handling(self):
        """Test comprehensive error handling in metrics system."""
        collector = MetricsCollector()
        
        # Test with invalid inputs
        collector.start_correction(None, "test")  # Invalid correction type
        collector.end_correction("", "", "", "invalid_confidence")  # Multiple invalid inputs
        
        # Should not crash
        stats = collector.get_stats_summary()
        assert isinstance(stats, dict)
        
        # Test reporter with minimal data
        reporter = MetricsReporter(collector)
        report = reporter.generate_console_report()
        assert isinstance(report, str)
        assert len(report) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])