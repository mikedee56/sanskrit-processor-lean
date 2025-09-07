"""
DocBook XML format exporter for book publishing workflows.
"""

import xml.etree.ElementTree as ET
from .format_manager import FormatExporter, ExportRequest


class DocBookExporter(FormatExporter):
    """DocBook XML export for book publishing workflows."""
    
    def export(self, request: ExportRequest) -> str:
        """Export to DocBook XML with publishing metadata."""
        output_file = request.output_directory / f"{request.source_filename}.xml"
        
        # Create root element with namespace
        root = ET.Element('{http://docbook.org/ns/docbook}chapter')
        root.set('version', '5.0')
        
        # Add metadata
        info = ET.SubElement(root, '{http://docbook.org/ns/docbook}info')
        title = ET.SubElement(info, '{http://docbook.org/ns/docbook}title')
        title.text = f"Sanskrit Lecture: {request.source_filename}"
        
        # Add processing metadata
        meta = ET.SubElement(info, '{http://docbook.org/ns/docbook}meta')
        meta.set('name', 'processing-quality')
        meta.set('content', str(request.qa_report.get('quality_summary', {}).get('high_confidence_segments', 0)))
        
        # Add content sections
        for segment in request.segments:
            para = ET.SubElement(root, '{http://docbook.org/ns/docbook}para')
            
            # Add timestamp as role attribute
            para.set('role', f'timestamp-{segment.start_time}-{segment.end_time}')
            
            # Handle Sanskrit text with proper markup
            if self._contains_sanskrit_terms(segment.text):
                self._add_sanskrit_markup(para, segment.text)
            else:
                para.text = segment.text
                
        # Write to file
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        return str(output_file)
        
    def _contains_sanskrit_terms(self, text: str) -> bool:
        """Check if text contains Sanskrit terms (basic check)."""
        sanskrit_indicators = ['śa', 'ś', 'ṃ', 'ṅ', 'ṭ', 'ḍ', 'ṇ', 'ḥ', '॥', 'ॐ']
        return any(indicator in text for indicator in sanskrit_indicators)
        
    def _add_sanskrit_markup(self, parent: ET.Element, text: str):
        """Add Sanskrit-specific markup to XML."""
        # Simple implementation - could be enhanced with more sophisticated parsing
        parent.text = text
        
    def get_file_extension(self) -> str:
        return ".xml"