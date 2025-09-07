"""
JSON-LD format exporter for mobile and web app development.
"""

import json
from .format_manager import FormatExporter, ExportRequest


class JSONExporter(FormatExporter):
    """JSON-LD export for mobile and web app development."""
    
    def export(self, request: ExportRequest) -> str:
        """Export to structured JSON with full metadata."""
        output_file = request.output_directory / f"{request.source_filename}.json"
        
        json_data = {
            "@context": "https://schema.org/",
            "@type": "VideoObject",
            "name": request.source_filename,
            "description": "Sanskrit lecture processed with quality enhancements",
            "processingMetadata": request.metadata,
            "qualityReport": request.qa_report,
            "transcript": [
                {
                    "startTime": segment.start_time,
                    "endTime": segment.end_time,
                    "text": segment.text,
                    "confidence": self._get_segment_confidence(segment, request.qa_report),
                    "hasIssues": self._segment_has_issues(segment, request.qa_report),
                    "metadata": self._extract_segment_metadata(segment, request)
                }
                for segment in request.segments
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
        return str(output_file)
        
    def _get_segment_confidence(self, segment, qa_report: dict) -> float:
        """Extract confidence score for segment from QA report."""
        for detail in qa_report.get('segment_details', []):
            if segment.start_time in detail.get('timestamp', ''):
                return detail.get('confidence', {}).get('overall', 1.0)
        return 1.0  # Default high confidence if not found
        
    def _segment_has_issues(self, segment, qa_report: dict) -> bool:
        """Check if segment has quality issues."""
        for detail in qa_report.get('segment_details', []):
            if segment.start_time in detail.get('timestamp', ''):
                return len(detail.get('issues', [])) > 0
        return False
        
    def _extract_segment_metadata(self, segment, request: ExportRequest) -> dict:
        """Extract segment-specific metadata."""
        return {
            "index": segment.index,
            "duration_ms": self._calculate_duration_ms(segment.start_time, segment.end_time),
            "contains_sanskrit": self._contains_sanskrit(segment.text),
            "character_count": len(segment.text)
        }
        
    def _calculate_duration_ms(self, start_time: str, end_time: str) -> int:
        """Calculate segment duration in milliseconds."""
        def parse_timestamp(timestamp: str) -> int:
            """Parse SRT timestamp to milliseconds."""
            time_part, ms_part = timestamp.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return (h * 3600 + m * 60 + s) * 1000 + ms
            
        return parse_timestamp(end_time) - parse_timestamp(start_time)
        
    def _contains_sanskrit(self, text: str) -> bool:
        """Check if text contains Sanskrit characters."""
        sanskrit_ranges = [(0x0900, 0x097F), (0xA8E0, 0xA8FF)]
        return any(
            any(start <= ord(char) <= end for start, end in sanskrit_ranges)
            for char in text
        )
        
    def get_file_extension(self) -> str:
        return ".json"