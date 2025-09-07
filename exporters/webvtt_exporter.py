"""
YouTube WebVTT format exporter with Sanskrit support.
"""

from .format_manager import FormatExporter, ExportRequest


class WebVTTExporter(FormatExporter):
    """YouTube-optimized WebVTT export with Sanskrit support."""
    
    def export(self, request: ExportRequest) -> str:
        """Export to WebVTT format with YouTube optimizations."""
        output_file = request.output_directory / f"{request.source_filename}.vtt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            # Add metadata
            f.write("NOTE\n")
            f.write("Sanskrit SRT Processor - Quality Enhanced Content\n\n")
            
            for segment in request.segments:
                # Convert SRT timestamp to WebVTT format
                start_time = self._convert_timestamp(segment.start_time)
                end_time = self._convert_timestamp(segment.end_time)
                
                # Add cue
                f.write(f"{start_time} --> {end_time}\n")
                
                # Add positioning for Sanskrit content if needed
                if self._contains_sanskrit(segment.text):
                    f.write(f"<c.sanskrit>{segment.text}</c>\n\n")
                else:
                    f.write(f"{segment.text}\n\n")
                    
        return str(output_file)
        
    def _convert_timestamp(self, srt_timestamp: str) -> str:
        """Convert SRT timestamp (HH:MM:SS,mmm) to WebVTT (HH:MM:SS.mmm)."""
        return srt_timestamp.replace(',', '.')
        
    def _contains_sanskrit(self, text: str) -> bool:
        """Check if text contains Sanskrit characters."""
        # Check for Sanskrit diacritics and Devanagari characters
        sanskrit_chars = ['ś', 'ṃ', 'ṅ', 'ṭ', 'ḍ', 'ṇ', 'ḥ', 'ॐ', '॥']
        sanskrit_ranges = [(0x0900, 0x097F), (0xA8E0, 0xA8FF)]  # Devanagari, Devanagari Extended
        
        # Check for specific Sanskrit characters
        if any(char in text for char in sanskrit_chars):
            return True
            
        # Check Unicode ranges
        return any(
            any(start <= ord(char) <= end for start, end in sanskrit_ranges)
            for char in text
        )
        
    def get_file_extension(self) -> str:
        return ".vtt"