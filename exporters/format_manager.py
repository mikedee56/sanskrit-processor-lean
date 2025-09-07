"""
Core export coordination for multi-platform formats.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path


@dataclass
class ExportRequest:
    """Request for multi-format export."""
    source_filename: str
    segments: List[Any]  # List[SRTSegment] - avoiding circular import
    qa_report: dict
    metadata: dict
    output_formats: List[str]  # ['srt', 'vtt', 'json', 'xml']
    output_directory: Path


class FormatExporter(ABC):
    """Abstract base for format exporters."""
    
    @abstractmethod
    def export(self, request: ExportRequest) -> str:
        """Export to specific format, return output filename."""
        pass
        
    @abstractmethod 
    def get_file_extension(self) -> str:
        """Return file extension for this format."""
        pass


class FormatManager:
    """Manages multiple output format exports."""
    
    def __init__(self):
        # Lazy import to avoid circular dependencies
        from .srt_exporter import SRTExporter
        from .webvtt_exporter import WebVTTExporter
        from .json_exporter import JSONExporter
        from .docbook_exporter import DocBookExporter
        
        self.exporters = {
            'srt': SRTExporter(),
            'vtt': WebVTTExporter(), 
            'json': JSONExporter(),
            'xml': DocBookExporter()
        }
        
    def export_all_formats(self, request: ExportRequest) -> Dict[str, str]:
        """Export to all requested formats."""
        results = {}
        
        for format_name in request.output_formats:
            if format_name in self.exporters:
                try:
                    output_file = self.exporters[format_name].export(request)
                    results[format_name] = output_file
                except Exception as e:
                    results[format_name] = f"Error: {str(e)}"
            else:
                results[format_name] = f"Error: Unsupported format '{format_name}'"
                
        return results
        
    def get_available_formats(self) -> List[str]:
        """Return list of supported export formats."""
        return list(self.exporters.keys())