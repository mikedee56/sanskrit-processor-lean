"""
HistoricalTracker - Historical metrics tracking and comparison.

Provides database storage for metrics, historical analysis, trend tracking,
and baseline comparison for processing runs.
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from .metrics_collector import MetricsCollector
from .metrics_reporter import MetricsReport

logger = logging.getLogger(__name__)

@dataclass
class HistoricalRun:
    """Historical processing run record."""
    id: int
    timestamp: str
    file_path: str
    file_name: str
    processing_mode: str
    total_segments: int
    corrections_made: int
    correction_rate: float
    processing_time: float
    quality_score: float
    segments_per_second: float
    corrections_by_type: Dict[str, int]
    performance_metrics: Dict[str, Any]

@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # 'improving', 'declining', 'stable'
    significance: str  # 'significant', 'minor', 'negligible'

@dataclass
class ComparisonReport:
    """Comparison report between runs."""
    current_run: HistoricalRun
    baseline_run: Optional[HistoricalRun]
    trends: List[TrendAnalysis]
    recommendations: List[str]


class HistoricalTracker:
    """Historical metrics tracking and analysis system (AC: 7).
    
    Provides database storage, trend analysis, baseline comparison,
    and regression detection for processing metrics over time.
    """
    
    def __init__(self, db_path: Path = None):
        """Initialize historical tracker with database."""
        if db_path is None:
            db_path = Path("metrics_history.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database for historical tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processing_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        processing_mode TEXT NOT NULL,
                        total_segments INTEGER NOT NULL,
                        corrections_made INTEGER NOT NULL,
                        correction_rate REAL NOT NULL,
                        processing_time REAL NOT NULL,
                        quality_score REAL NOT NULL,
                        segments_per_second REAL NOT NULL,
                        corrections_by_type TEXT NOT NULL,  -- JSON
                        performance_metrics TEXT NOT NULL   -- JSON
                    )
                """)
                
                # Create indexes for efficient queries
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON processing_runs(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_file_name ON processing_runs(file_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_mode ON processing_runs(processing_mode)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def store_run(self, metrics_collector: MetricsCollector, report: MetricsReport) -> int:
        """Store processing run in historical database.
        
        Args:
            metrics_collector: MetricsCollector with run data
            report: MetricsReport with analyzed data
            
        Returns:
            ID of stored run record
        """
        try:
            # Calculate segments per second
            segments_per_second = 0.0
            if report.processing_time > 0:
                segments_per_second = report.total_segments / report.processing_time
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO processing_runs (
                        timestamp, file_path, file_name, processing_mode,
                        total_segments, corrections_made, correction_rate,
                        processing_time, quality_score, segments_per_second,
                        corrections_by_type, performance_metrics
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.timestamp,
                    report.file_path,
                    Path(report.file_path).name,
                    report.processing_mode,
                    report.total_segments,
                    report.corrections_made,
                    report.correction_rate,
                    report.processing_time,
                    report.quality_score,
                    segments_per_second,
                    json.dumps(report.corrections_by_type),
                    json.dumps(report.performance_metrics)
                ))
                
                run_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Stored historical run with ID: {run_id}")
                return run_id
                
        except Exception as e:
            logger.error(f"Failed to store historical run: {e}")
            raise
    
    def get_recent_runs(self, file_name: str = None, mode: str = None, limit: int = 10) -> List[HistoricalRun]:
        """Get recent processing runs with optional filtering."""
        try:
            query = "SELECT * FROM processing_runs"
            params = []
            conditions = []
            
            if file_name:
                conditions.append("file_name = ?")
                params.append(file_name)
            
            if mode:
                conditions.append("processing_mode = ?")
                params.append(mode)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.execute(query, params)
                
                runs = []
                for row in cursor:
                    runs.append(HistoricalRun(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        file_path=row['file_path'],
                        file_name=row['file_name'],
                        processing_mode=row['processing_mode'],
                        total_segments=row['total_segments'],
                        corrections_made=row['corrections_made'],
                        correction_rate=row['correction_rate'],
                        processing_time=row['processing_time'],
                        quality_score=row['quality_score'],
                        segments_per_second=row['segments_per_second'],
                        corrections_by_type=json.loads(row['corrections_by_type']),
                        performance_metrics=json.loads(row['performance_metrics'])
                    ))
                
                return runs
                
        except Exception as e:
            logger.error(f"Failed to get recent runs: {e}")
            return []
    
    def compare_with_baseline(self, current_report: MetricsReport, 
                            baseline_days: int = 30) -> ComparisonReport:
        """Compare current run with historical baseline.
        
        Args:
            current_report: Current processing report
            baseline_days: Days to look back for baseline (default: 30)
            
        Returns:
            ComparisonReport with analysis and recommendations
        """
        try:
            # Get baseline run (average of similar runs from past N days)
            baseline_run = self._get_baseline_run(
                current_report.file_path, 
                current_report.processing_mode,
                baseline_days
            )
            
            # Create current run record
            current_run = HistoricalRun(
                id=0,  # Not stored yet
                timestamp=current_report.timestamp,
                file_path=current_report.file_path,
                file_name=Path(current_report.file_path).name,
                processing_mode=current_report.processing_mode,
                total_segments=current_report.total_segments,
                corrections_made=current_report.corrections_made,
                correction_rate=current_report.correction_rate,
                processing_time=current_report.processing_time,
                quality_score=current_report.quality_score,
                segments_per_second=current_report.total_segments / current_report.processing_time if current_report.processing_time > 0 else 0,
                corrections_by_type=current_report.corrections_by_type,
                performance_metrics=current_report.performance_metrics
            )
            
            # Analyze trends
            trends = self._analyze_trends(current_run, baseline_run)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(trends)
            
            return ComparisonReport(
                current_run=current_run,
                baseline_run=baseline_run,
                trends=trends,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to compare with baseline: {e}")
            return ComparisonReport(
                current_run=current_run,
                baseline_run=None,
                trends=[],
                recommendations=["Unable to generate comparison due to error"]
            )
    
    def _get_baseline_run(self, file_path: str, mode: str, days: int) -> Optional[HistoricalRun]:
        """Get baseline run by averaging recent similar runs."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM processing_runs 
                    WHERE file_name = ? AND processing_mode = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (Path(file_path).name, mode, cutoff_date))
                
                rows = cursor.fetchall()
                if not rows:
                    return None
                
                # Calculate averages
                total_segments = sum(row['total_segments'] for row in rows) // len(rows)
                corrections_made = sum(row['corrections_made'] for row in rows) // len(rows)
                correction_rate = sum(row['correction_rate'] for row in rows) / len(rows)
                processing_time = sum(row['processing_time'] for row in rows) / len(rows)
                quality_score = sum(row['quality_score'] for row in rows) / len(rows)
                segments_per_second = sum(row['segments_per_second'] for row in rows) / len(rows)
                
                # Use most recent corrections_by_type and performance_metrics
                corrections_by_type = json.loads(rows[0]['corrections_by_type'])
                performance_metrics = json.loads(rows[0]['performance_metrics'])
                
                return HistoricalRun(
                    id=0,  # Baseline (averaged)
                    timestamp=f"Baseline ({len(rows)} runs)",
                    file_path=file_path,
                    file_name=Path(file_path).name,
                    processing_mode=mode,
                    total_segments=total_segments,
                    corrections_made=corrections_made,
                    correction_rate=correction_rate,
                    processing_time=processing_time,
                    quality_score=quality_score,
                    segments_per_second=segments_per_second,
                    corrections_by_type=corrections_by_type,
                    performance_metrics=performance_metrics
                )
                
        except Exception as e:
            logger.error(f"Failed to get baseline run: {e}")
            return None
    
    def _analyze_trends(self, current: HistoricalRun, 
                       baseline: Optional[HistoricalRun]) -> List[TrendAnalysis]:
        """Analyze trends between current and baseline runs."""
        trends = []
        
        if not baseline:
            return trends
        
        # Key metrics to analyze
        metrics = [
            ('Quality Score', current.quality_score, baseline.quality_score, 'higher_better'),
            ('Processing Speed', current.segments_per_second, baseline.segments_per_second, 'higher_better'),
            ('Correction Rate', current.correction_rate, baseline.correction_rate, 'context_dependent'),
            ('Processing Time', current.processing_time, baseline.processing_time, 'lower_better'),
        ]
        
        for metric_name, current_val, baseline_val, trend_type in metrics:
            if baseline_val == 0:
                continue  # Skip division by zero
                
            change_percent = ((current_val - baseline_val) / baseline_val) * 100
            
            # Determine trend direction
            if abs(change_percent) < 2:
                direction = 'stable'
                significance = 'negligible'
            elif change_percent > 0:
                if trend_type == 'higher_better':
                    direction = 'improving'
                elif trend_type == 'lower_better':
                    direction = 'declining'
                else:  # context_dependent
                    direction = 'increasing'
                significance = 'significant' if abs(change_percent) > 10 else 'minor'
            else:
                if trend_type == 'higher_better':
                    direction = 'declining'
                elif trend_type == 'lower_better':
                    direction = 'improving'
                else:  # context_dependent
                    direction = 'decreasing'
                significance = 'significant' if abs(change_percent) > 10 else 'minor'
            
            trends.append(TrendAnalysis(
                metric_name=metric_name,
                current_value=current_val,
                previous_value=baseline_val,
                change_percent=change_percent,
                trend_direction=direction,
                significance=significance
            ))
        
        return trends
    
    def _generate_recommendations(self, trends: List[TrendAnalysis]) -> List[str]:
        """Generate recommendations based on trend analysis."""
        recommendations = []
        
        for trend in trends:
            if trend.significance == 'negligible':
                continue
                
            if trend.metric_name == 'Quality Score' and trend.trend_direction == 'declining':
                recommendations.append(
                    f"Quality score decreased by {abs(trend.change_percent):.1f}%. "
                    "Consider reviewing lexicon accuracy or correction thresholds."
                )
            
            elif trend.metric_name == 'Processing Speed' and trend.trend_direction == 'declining':
                recommendations.append(
                    f"Processing speed decreased by {abs(trend.change_percent):.1f}%. "
                    "Consider cache optimization or performance profiling."
                )
            
            elif trend.metric_name == 'Processing Time' and trend.trend_direction == 'declining':
                recommendations.append(
                    f"Processing time increased by {abs(trend.change_percent):.1f}%. "
                    "This may indicate performance regression or increased file complexity."
                )
            
            elif trend.trend_direction == 'improving' and trend.significance == 'significant':
                recommendations.append(
                    f"Great improvement in {trend.metric_name} ({trend.change_percent:.1f}% better)!"
                )
        
        if not recommendations:
            recommendations.append("Performance is stable compared to recent baseline.")
        
        return recommendations
    
    def get_trend_summary(self, file_name: str = None, days: int = 30) -> Dict[str, Any]:
        """Get trend summary for dashboard/reporting."""
        try:
            runs = self.get_recent_runs(file_name=file_name, limit=50)
            
            if len(runs) < 2:
                return {'message': 'Insufficient data for trend analysis'}
            
            # Filter runs within time window
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            recent_runs = [run for run in runs if run.timestamp >= cutoff_date]
            
            if len(recent_runs) < 2:
                return {'message': f'Insufficient data in last {days} days'}
            
            # Calculate trends
            latest = recent_runs[0]
            oldest = recent_runs[-1]
            
            return {
                'time_period': f'{days} days',
                'total_runs': len(recent_runs),
                'average_quality': sum(run.quality_score for run in recent_runs) / len(recent_runs),
                'average_speed': sum(run.segments_per_second for run in recent_runs) / len(recent_runs),
                'quality_trend': latest.quality_score - oldest.quality_score,
                'speed_trend': latest.segments_per_second - oldest.segments_per_second,
                'most_recent': latest.timestamp,
                'files_processed': len(set(run.file_name for run in recent_runs))
            }
            
        except Exception as e:
            logger.error(f"Failed to get trend summary: {e}")
            return {'error': str(e)}