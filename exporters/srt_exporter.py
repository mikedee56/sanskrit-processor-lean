"""
Standard SRT format exporter.
"""

from .format_manager import FormatExporter, ExportRequest


class SRTExporter(FormatExporter):
    """Standard SRT format export."""
    
    def export(self, request: ExportRequest) -> str:
        """Export to standard SRT format."""
        output_file = request.output_directory / f"{request.source_filename}.srt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for segment in request.segments:
                f.write(f"{segment.index}\n")
                f.write(f"{segment.start_time} --> {segment.end_time}\n")
                f.write(f"{segment.text}\n\n")
                
        return str(output_file)
        
    def get_file_extension(self) -> str:
        return ".srt"