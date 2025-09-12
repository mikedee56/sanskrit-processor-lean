"""
MetricsReporter - Comprehensive reporting for processing metrics.

Provides detailed report generation with JSON, HTML, CSV export formats,
console reporting, and historical tracking support.
"""

import json
import csv
import logging
from datetime import datetime
from typing import Dict, Any, List, Union, Optional
from pathlib import Path
from dataclasses import dataclass, field
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

@dataclass
class MetricsReport:
    """Comprehensive metrics report with metadata and analysis."""
    
    # Metadata
    file_path: str
    processing_mode: str
    timestamp: str
    processor_version: str = "10.6"
    
    # Summary metrics
    total_segments: int = 0
    corrections_made: int = 0
    correction_rate: float = 0.0
    processing_time: float = 0.0
    quality_score: float = 0.0
    
    # Detailed analysis
    corrections_by_type: Dict[str, int] = field(default_factory=dict)
    top_corrections: List[tuple] = field(default_factory=list)
    confidence_distribution: Dict[str, int] = field(default_factory=dict)
    sample_corrections: List[Dict[str, Union[str, float, int]]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class MetricsReporter:
    """Comprehensive reporting for processing metrics with multiple export formats.
    
    This class generates detailed reports from MetricsCollector data in console,
    JSON, HTML, and CSV formats for comprehensive analysis and visualization.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize reporter with metrics collector data."""
        self.metrics = metrics_collector
        self.report = self._build_report()
    
    def _build_report(self) -> MetricsReport:
        """Build comprehensive metrics report from collector data."""
        try:
            # Get comprehensive stats
            stats = self.metrics.get_stats_summary()
            performance = self.metrics.get_performance_metrics()
            
            # Calculate derived metrics
            correction_rate = (len(self.metrics.correction_details) / self.metrics.total_segments * 100) if self.metrics.total_segments > 0 else 0.0
            quality_score = self.metrics.calculate_quality_score(self.metrics.total_segments, 0)
            
            return MetricsReport(
                file_path=self.metrics.file_path,
                processing_mode=self.metrics.processing_mode,
                timestamp=datetime.now().isoformat(),
                total_segments=self.metrics.total_segments,
                corrections_made=len(self.metrics.correction_details),
                correction_rate=round(correction_rate, 2),
                processing_time=round(performance.get('total_processing_time', 0.0), 3),
                quality_score=round(quality_score, 1),
                corrections_by_type=stats['corrections_by_type'],
                top_corrections=stats['top_corrections'],
                confidence_distribution=stats['confidence_distribution'],
                sample_corrections=stats['sample_corrections'],
                performance_metrics=performance
            )
        except Exception as e:
            logger.error(f"Failed to build metrics report: {e}")
            return MetricsReport(
                file_path="unknown",
                processing_mode="unknown", 
                timestamp=datetime.now().isoformat()
            )
    
    def generate_console_report(self, verbose: bool = False) -> str:
        """Generate comprehensive console report (AC: 1, 2, 3, 4, 6)."""
        try:
            report_lines = []
            
            # Header
            report_lines.append("🔍 PROCESSING METRICS REPORT")
            report_lines.append("=" * 50)
            
            # Basic info
            report_lines.append(f"📁 File: {Path(self.report.file_path).name}")
            report_lines.append(f"⚙️  Mode: {self.report.processing_mode}")
            report_lines.append(f"📊 Segments: {self.report.total_segments:,}")
            report_lines.append(f"✏️  Corrections: {self.report.corrections_made:,} ({self.report.correction_rate:.1f}%)")
            report_lines.append(f"⏱️  Time: {self.report.processing_time:.2f}s")
            
            # Processing rate
            if self.report.processing_time > 0:
                rate = self.report.total_segments / self.report.processing_time
                report_lines.append(f"🚀 Speed: {rate:,.0f} segments/sec")
            
            # Quality score
            report_lines.append(f"⭐ Quality: {self.report.quality_score:.0f}/100")
            report_lines.append("")
            
            # Top corrections (AC: 2)
            if self.report.top_corrections:
                report_lines.append("📊 TOP CORRECTIONS:")
                for i, ((original, corrected), count) in enumerate(self.report.top_corrections[:10], 1):
                    report_lines.append(f"  {i:2d}. {original} → {corrected} ({count}x)")
                report_lines.append("")
            
            # Correction analysis
            if self.report.corrections_by_type:
                report_lines.append("🔧 CORRECTION BREAKDOWN:")
                total_corrections = sum(self.report.corrections_by_type.values())
                for correction_type, count in sorted(self.report.corrections_by_type.items()):
                    percentage = (count / total_corrections * 100) if total_corrections > 0 else 0
                    report_lines.append(f"  • {correction_type.title()}: {count:,} ({percentage:.1f}%)")
                report_lines.append("")
            
            # Confidence distribution (AC: 3)
            if self.report.confidence_distribution:
                report_lines.append("🎯 CONFIDENCE DISTRIBUTION:")
                for level, count in self.report.confidence_distribution.items():
                    if count > 0:
                        report_lines.append(f"  • {level}: {count:,} corrections")
                report_lines.append("")
            
            # Sample corrections (AC: 4)
            if verbose and self.report.sample_corrections:
                report_lines.append("📝 SAMPLE CORRECTIONS:")
                for i, sample in enumerate(self.report.sample_corrections[:5], 1):
                    confidence_str = f"{sample['confidence']:.2f}"
                    segment_str = f"seg #{sample['segment']}" if sample['segment'] >= 0 else "seg #?"
                    report_lines.append(f"  {i}. \"{sample['original']}\" → \"{sample['corrected']}\"")
                    report_lines.append(f"     ({sample['type']}, confidence: {confidence_str}, {segment_str})")
                report_lines.append("")
            
            # Performance metrics (AC: 6)
            if verbose and self.report.performance_metrics:
                perf = self.report.performance_metrics
                report_lines.append("⚡ PERFORMANCE ANALYSIS:")
                
                # Memory usage
                if 'memory_usage' in perf and perf['memory_usage']:
                    mem = perf['memory_usage']
                    if mem.get('peak_mb', 0) > 0:
                        report_lines.append(f"  • Memory: {mem['peak_mb']:.1f}MB peak")
                
                # Cache performance
                if 'cache_performance' in perf and perf['cache_performance']:
                    cache = perf['cache_performance']
                    hit_rate = cache.get('hit_rate_percent', 0)
                    if hit_rate > 0:
                        report_lines.append(f"  • Cache hit rate: {hit_rate:.1f}%")
                
                # Processing phases
                if 'processing_phases' in perf and perf['processing_phases']:
                    report_lines.append("  • Phase breakdown:")
                    for phase, time_taken in perf['processing_phases'].items():
                        percentage = (time_taken / self.report.processing_time * 100) if self.report.processing_time > 0 else 0
                        report_lines.append(f"    - {phase.title()}: {time_taken:.2f}s ({percentage:.1f}%)")
                
                report_lines.append("")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Failed to generate console report: {e}")
            return f"❌ Error generating console report: {e}"
    
    def export_json(self, output_path: Path) -> None:
        """Export comprehensive metrics to JSON format (AC: 5)."""
        try:
            # Build comprehensive JSON data
            json_data = {
                'metadata': {
                    'file_path': self.report.file_path,
                    'processing_mode': self.report.processing_mode,
                    'timestamp': self.report.timestamp,
                    'processor_version': self.report.processor_version
                },
                'summary': {
                    'total_segments': self.report.total_segments,
                    'corrections_made': self.report.corrections_made,
                    'correction_rate': self.report.correction_rate,
                    'processing_time': self.report.processing_time,
                    'quality_score': self.report.quality_score
                },
                'analysis': {
                    'corrections_by_type': self.report.corrections_by_type,
                    'top_corrections': [
                        {
                            'original': original,
                            'corrected': corrected,
                            'count': count
                        }
                        for (original, corrected), count in self.report.top_corrections
                    ],
                    'confidence_distribution': self.report.confidence_distribution,
                    'sample_corrections': self.report.sample_corrections
                },
                'performance': self.report.performance_metrics,
                'raw_data': {
                    'correction_details': [
                        {
                            'type': detail.type,
                            'original': detail.original,
                            'corrected': detail.corrected,
                            'confidence': round(detail.confidence, 3),
                            'processing_time': round(detail.processing_time, 6)
                        }
                        for detail in self.metrics.correction_details
                    ]
                }
            }
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"JSON metrics exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export JSON metrics: {e}")
            raise
    
    def export_html(self, output_path: Path) -> None:
        """Export comprehensive HTML report with visualizations (AC: 5)."""
        try:
            html_template = self._get_html_template()
            
            # Prepare data for template
            template_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'file_name': Path(self.report.file_path).name,
                'file_path': self.report.file_path,
                'processing_mode': self.report.processing_mode.title(),
                'total_segments': f"{self.report.total_segments:,}",
                'corrections_made': f"{self.report.corrections_made:,}",
                'correction_rate': f"{self.report.correction_rate:.1f}%",
                'processing_time': f"{self.report.processing_time:.2f}s",
                'quality_score': f"{self.report.quality_score:.0f}",
                'processing_speed': f"{self.report.total_segments/self.report.processing_time:,.0f} segments/sec" if self.report.processing_time > 0 else "N/A"
            }
            
            # Generate corrections table
            corrections_rows = ""
            for i, ((original, corrected), count) in enumerate(self.report.top_corrections[:15], 1):
                confidence = "High"  # Default for top corrections
                corrections_rows += f"""
                <tr>
                    <td>{i}</td>
                    <td><code>{original}</code></td>
                    <td><code>{corrected}</code></td>
                    <td>{count}</td>
                    <td><span class="confidence-high">{confidence}</span></td>
                </tr>"""
            template_data['corrections_rows'] = corrections_rows
            
            # Generate sample corrections
            samples_html = ""
            for i, sample in enumerate(self.report.sample_corrections[:8], 1):
                confidence_class = self._get_confidence_class(sample['confidence'])
                confidence_label = self._get_confidence_label(sample['confidence'])
                samples_html += f"""
                <div class="correction-sample">
                    <div class="sample-header">
                        <strong>Sample {i}:</strong> 
                        <span class="correction-type">{sample['type'].title()}</span>
                        <span class="confidence-badge {confidence_class}">{confidence_label}</span>
                    </div>
                    <div class="sample-content">
                        <span class="original">"{sample['original']}"</span>
                        <span class="arrow">→</span>
                        <span class="corrected">"{sample['corrected']}"</span>
                    </div>
                </div>"""
            template_data['sample_corrections'] = samples_html
            
            # Generate performance metrics
            perf_html = ""
            if self.report.performance_metrics.get('memory_usage'):
                mem = self.report.performance_metrics['memory_usage']
                if mem.get('peak_mb', 0) > 0:
                    perf_html += f"<p><strong>Peak Memory:</strong> {mem['peak_mb']:.1f} MB</p>"
            
            if self.report.performance_metrics.get('cache_performance'):
                cache = self.report.performance_metrics['cache_performance']
                hit_rate = cache.get('hit_rate_percent', 0)
                if hit_rate > 0:
                    perf_html += f"<p><strong>Cache Hit Rate:</strong> {hit_rate:.1f}%</p>"
                    
            template_data['performance_details'] = perf_html
            
            # Replace template variables
            html_content = html_template
            for key, value in template_data.items():
                html_content = html_content.replace(f"{{{{ {key} }}}}", str(value))
            
            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"HTML report exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export HTML report: {e}")
            raise
    
    def export_csv(self, output_path: Path) -> None:
        """Export corrections data to CSV format for spreadsheet analysis (AC: 5)."""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['original', 'corrected', 'confidence', 'type', 'processing_time_ms', 'segment']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write correction data
                for detail in self.metrics.correction_details:
                    # Find segment info from samples if available
                    segment_info = -1
                    for sample in self.report.sample_corrections:
                        if (sample['original'] == detail.original and 
                            sample['corrected'] == detail.corrected and
                            abs(sample['confidence'] - detail.confidence) < 0.001):
                            segment_info = sample.get('segment', -1)
                            break
                    
                    writer.writerow({
                        'original': detail.original,
                        'corrected': detail.corrected,
                        'confidence': round(detail.confidence, 3),
                        'type': detail.type,
                        'processing_time_ms': round(detail.processing_time * 1000, 2),
                        'segment': segment_info
                    })
                
            logger.info(f"CSV data exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def _get_confidence_class(self, confidence: float) -> str:
        """Get CSS class for confidence level."""
        if confidence >= 0.9:
            return "confidence-high"
        elif confidence >= 0.7:
            return "confidence-medium"
        elif confidence >= 0.5:
            return "confidence-low"
        else:
            return "confidence-very-low"
    
    def _get_confidence_label(self, confidence: float) -> str:
        """Get human-readable confidence label."""
        if confidence >= 0.9:
            return f"High ({confidence:.2f})"
        elif confidence >= 0.7:
            return f"Medium ({confidence:.2f})"
        elif confidence >= 0.5:
            return f"Low ({confidence:.2f})"
        else:
            return f"Very Low ({confidence:.2f})"
    
    def _get_html_template(self) -> str:
        """Get HTML report template."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sanskrit Processor Metrics Report</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 40px; 
            background-color: #f8f9fa;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #007bff; padding-bottom: 20px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
        .metric-card h4 { margin: 0 0 10px 0; color: #007bff; font-size: 14px; text-transform: uppercase; }
        .metric-card .value { font-size: 24px; font-weight: bold; color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #dee2e6; padding: 12px; text-align: left; }
        th { background-color: #007bff; color: white; font-weight: 600; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }
        .correction-sample { 
            background: #e8f5e8; 
            padding: 15px; 
            margin: 10px 0; 
            border-left: 4px solid #28a745; 
            border-radius: 4px;
        }
        .sample-header { font-weight: bold; margin-bottom: 8px; }
        .correction-type { background: #6c757d; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
        .confidence-badge { padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 8px; }
        .confidence-high { background: #28a745; color: white; }
        .confidence-medium { background: #ffc107; color: #212529; }
        .confidence-low { background: #fd7e14; color: white; }
        .confidence-very-low { background: #dc3545; color: white; }
        .original { color: #dc3545; font-weight: bold; }
        .arrow { color: #6c757d; margin: 0 8px; }
        .corrected { color: #28a745; font-weight: bold; }
        .section { margin: 40px 0; }
        .section h2 { color: #007bff; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Sanskrit Processor Metrics Report</h1>
            <p>Generated on {{ timestamp }}</p>
        </div>
        
        <div class="section">
            <h2>📊 Processing Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>File Processed</h4>
                    <div class="value">{{ file_name }}</div>
                </div>
                <div class="metric-card">
                    <h4>Processing Mode</h4>
                    <div class="value">{{ processing_mode }}</div>
                </div>
                <div class="metric-card">
                    <h4>Total Segments</h4>
                    <div class="value">{{ total_segments }}</div>
                </div>
                <div class="metric-card">
                    <h4>Corrections Made</h4>
                    <div class="value">{{ corrections_made }}</div>
                </div>
                <div class="metric-card">
                    <h4>Correction Rate</h4>
                    <div class="value">{{ correction_rate }}</div>
                </div>
                <div class="metric-card">
                    <h4>Processing Time</h4>
                    <div class="value">{{ processing_time }}</div>
                </div>
                <div class="metric-card">
                    <h4>Processing Speed</h4>
                    <div class="value">{{ processing_speed }}</div>
                </div>
                <div class="metric-card">
                    <h4>Quality Score</h4>
                    <div class="value">{{ quality_score }}/100</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Top Corrections</h2>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Original</th>
                    <th>Corrected</th>
                    <th>Count</th>
                    <th>Confidence</th>
                </tr>
                {{ corrections_rows }}
            </table>
        </div>
        
        <div class="section">
            <h2>📝 Sample Corrections</h2>
            {{ sample_corrections }}
        </div>
        
        <div class="section">
            <h2>⚡ Performance Metrics</h2>
            {{ performance_details }}
            <p><strong>Processing Details:</strong></p>
            <ul>
                <li><strong>File:</strong> {{ file_path }}</li>
                <li><strong>Total Processing Time:</strong> {{ processing_time }}</li>
                <li><strong>Average Speed:</strong> {{ processing_speed }}</li>
            </ul>
        </div>
    </div>
</body>
</html>'''