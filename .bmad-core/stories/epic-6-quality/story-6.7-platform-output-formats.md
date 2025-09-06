# Story 6.7: Multi-Platform Output Formats

**Epic**: Sanskrit Content Quality Excellence  
**Story Points**: 5  
**Priority**: Low  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete Story 6.6 (Quality Assurance) first  
⚠️ **USER REQUIREMENT**: Support YouTube, book publishing, and app creation workflows

## 📋 User Story

**As a** content creator using Sanskrit lectures for YouTube, book publishing, and app development  
**I want** multiple output formats optimized for each platform  
**So that** I can seamlessly integrate processed content into different publishing workflows

## 🎯 Business Value

- **Platform Integration**: Direct export to YouTube SRT, book XML, app JSON formats
- **Workflow Efficiency**: Reduce manual format conversion for 11k hours of content
- **Quality Preservation**: Maintain formatting integrity across all output formats
- **Metadata Integration**: Include Sanskrit metadata in platform-appropriate ways
- **Future-Proofing**: Extensible format system for new platform requirements

## ✅ Acceptance Criteria

### **AC 1: YouTube Optimization**
- [ ] **WebVTT Export**: YouTube-compatible .vtt format with styling
- [ ] **Chapter Markers**: Auto-generate chapters from content structure
- [ ] **Sacred Symbol Support**: Proper Unicode rendering for Sanskrit symbols
- [ ] **Quality Metadata**: Include confidence scores as private metadata

### **AC 2: Book Publishing Support**
- [ ] **DocBook XML**: Structured XML for publishing workflows
- [ ] **IAST Formatting**: Proper IAST transliteration with diacritics
- [ ] **Footnote Integration**: Scripture references as footnotes
- [ ] **Quality Annotations**: Optional quality flags for editors

### **AC 3: App Development Support**
- [ ] **JSON-LD Export**: Structured data for mobile/web apps
- [ ] **Timestamp Precision**: Millisecond accuracy for media sync
- [ ] **Metadata Enrichment**: Include all processing metadata
- [ ] **Batch Processing**: Multiple formats in single processing run

### **AC 4: Lean Implementation Requirements**
- [ ] **Code Limit**: Maximum 150 lines for all format exporters
- [ ] **No New Dependencies**: Use only stdlib and existing libraries
- [ ] **Performance**: <50ms additional export time per format
- [ ] **Memory**: <2MB additional footprint per format

## 🏗️ Implementation Plan

### **Format Export System**
```python
# New: exporters/format_manager.py (~80 lines)
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any
import json
import xml.etree.ElementTree as ET
from pathlib import Path

@dataclass
class ExportRequest:
    """Request for multi-format export."""
    source_filename: str
    segments: List[SRTSegment]
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
```

### **YouTube WebVTT Exporter**
```python
# New: exporters/webvtt_exporter.py (~40 lines)
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
            
            for i, segment in enumerate(request.segments):
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
        sanskrit_ranges = [(0x0900, 0x097F), (0xA8E0, 0xA8FF)]  # Devanagari, Devanagari Extended
        return any(
            any(start <= ord(char) <= end for start, end in sanskrit_ranges)
            for char in text
        )
        
    def get_file_extension(self) -> str:
        return ".vtt"
```

### **Book Publishing XML Exporter**
```python
# New: exporters/docbook_exporter.py (~50 lines)
class DocBookExporter(FormatExporter):
    """DocBook XML export for book publishing workflows."""
    
    def export(self, request: ExportRequest) -> str:
        """Export to DocBook XML with publishing metadata."""
        output_file = request.output_directory / f"{request.source_filename}.xml"
        
        # Create root element
        root = ET.Element('chapter')
        root.set('xmlns', 'http://docbook.org/ns/docbook')
        root.set('version', '5.0')
        
        # Add metadata
        info = ET.SubElement(root, 'info')
        title = ET.SubElement(info, 'title')
        title.text = f"Sanskrit Lecture: {request.source_filename}"
        
        # Add processing metadata
        meta = ET.SubElement(info, 'meta')
        meta.set('name', 'processing-quality')
        meta.set('content', str(request.qa_report.get('quality_summary', {}).get('high_confidence_segments', 0)))
        
        # Add content sections
        for segment in request.segments:
            para = ET.SubElement(root, 'para')
            
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
        
    def _add_sanskrit_markup(self, parent: ET.Element, text: str):
        """Add Sanskrit-specific markup to XML."""
        # Simple implementation - could be enhanced with more sophisticated parsing
        parent.text = text
        
    def get_file_extension(self) -> str:
        return ".xml"
```

### **App Development JSON Exporter**
```python
# New: exporters/json_exporter.py (~30 lines)
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
        
    def _get_segment_confidence(self, segment: SRTSegment, qa_report: dict) -> float:
        """Extract confidence score for segment from QA report."""
        for detail in qa_report.get('segment_details', []):
            if segment.start_time in detail.get('timestamp', ''):
                return detail.get('confidence', {}).get('overall', 1.0)
        return 1.0  # Default high confidence if not found
        
    def get_file_extension(self) -> str:
        return ".json"
```

### **CLI Integration**
```python
# Enhanced: cli.py (~20 lines addition)
def main():
    parser = argparse.ArgumentParser(description='Sanskrit SRT Processor')
    # ... existing arguments ...
    parser.add_argument('--export-formats', 
                       nargs='+', 
                       default=['srt'],
                       choices=['srt', 'vtt', 'json', 'xml'],
                       help='Output formats to generate')
    
    args = parser.parse_args()
    
    # ... existing processing ...
    
    # Multi-format export
    if len(args.export_formats) > 1 or 'srt' not in args.export_formats:
        format_manager = FormatManager()
        export_request = ExportRequest(
            source_filename=Path(args.input_file).stem,
            segments=processed_segments,
            qa_report=qa_report,
            metadata=processing_metadata,
            output_formats=args.export_formats,
            output_directory=Path(args.output_file).parent
        )
        
        results = format_manager.export_all_formats(export_request)
        
        print("Export Results:")
        for format_name, result_file in results.items():
            print(f"  {format_name.upper()}: {result_file}")
```

## 📁 Files to Create/Modify

### **New Files:**
- `exporters/format_manager.py` - Main export coordination (~80 lines)
- `exporters/webvtt_exporter.py` - YouTube WebVTT export (~40 lines)
- `exporters/docbook_exporter.py` - Book publishing XML (~50 lines)  
- `exporters/json_exporter.py` - App development JSON (~30 lines)

### **Modified Files:**
- `cli.py` - Multi-format export options (~20 lines addition)

**Total New Code**: ~150 lines (within limit)

## 🔧 Technical Specifications

### **Format Support Matrix**
| Format | Extension | Primary Use | Metadata Support |
|--------|-----------|-------------|------------------|
| **SRT** | .srt | Standard subtitles | Timestamps only |
| **WebVTT** | .vtt | YouTube, web video | Styling, chapters |
| **JSON-LD** | .json | Apps, APIs | Full metadata |
| **DocBook XML** | .xml | Book publishing | Publishing metadata |

### **Export Configuration**
```yaml
# Enhanced config.yaml
export:
  formats:
    webvtt:
      include_styling: true
      chapter_markers: true
      sanskrit_css_class: "sanskrit"
      
    docbook:
      include_timestamps: true
      sanskrit_markup: true
      quality_annotations: false  # Set true for editorial workflows
      
    json:
      include_confidence: true
      include_qa_report: true
      schema_version: "1.0"
```

## 📊 Success Metrics

### **Format Quality**
- **YouTube Integration**: WebVTT files upload without errors
- **Publishing Workflow**: DocBook XML validates against schema
- **App Compatibility**: JSON-LD passes structured data validation
- **Sanskrit Preservation**: All formats maintain Unicode integrity

### **Performance Requirements**
- **Export Speed**: <50ms per format per file
- **Memory Usage**: <2MB per format during export
- **File Size**: <10% increase over source SRT for each format
- **Batch Processing**: Export 50+ files without memory issues

### **Integration Success**
- **CLI Integration**: Seamless multi-format command-line export
- **Format Selection**: Easy selection of output formats
- **Error Handling**: Clear error messages for format failures
- **Metadata Preservation**: All processing metadata carried forward

## 🧪 Test Cases

### **Format Export Tests**
```python
def test_multiformat_export():
    request = ExportRequest(
        source_filename="test_lecture",
        segments=sample_segments,
        qa_report=sample_qa_report,
        metadata={},
        output_formats=['srt', 'vtt', 'json', 'xml'],
        output_directory=Path('test_output')
    )
    
    manager = FormatManager()
    results = manager.export_all_formats(request)
    
    assert 'srt' in results
    assert 'vtt' in results
    assert 'json' in results
    assert 'xml' in results
    assert all(Path(result).exists() for result in results.values())

def test_sanskrit_preservation():
    sanskrit_segment = SRTSegment(
        start_time="00:01:00,000",
        end_time="00:01:05,000", 
        text="Om śāntiḥ śāntiḥ śāntiḥ ||"
    )
    
    # Test all formats preserve Sanskrit correctly
    for format_name in ['vtt', 'json', 'xml']:
        exported_content = export_single_format(sanskrit_segment, format_name)
        assert "śāntiḥ" in exported_content
        assert "||" in exported_content
```

### **Platform Integration Tests**
```python
def test_youtube_webvtt_compatibility():
    # Test WebVTT format meets YouTube requirements
    vtt_content = export_to_webvtt(sample_segments)
    
    assert vtt_content.startswith("WEBVTT")
    assert "-->" in vtt_content
    assert not vtt_content.count('\n\n\n') > 0  # No triple line breaks

def test_docbook_xml_validity():
    # Test XML validates against DocBook schema
    xml_content = export_to_docbook(sample_segments)
    
    # Basic XML validation
    try:
        ET.fromstring(xml_content)
    except ET.ParseError:
        assert False, "Generated XML is not valid"
```

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Format Incompatibility** | Medium | Validate against platform specs |
| **Unicode Issues** | High | Extensive UTF-8 testing |
| **File Size Growth** | Low | Monitor and optimize export efficiency |
| **Export Failures** | Medium | Robust error handling and fallbacks |

## 🔄 Story Progress Tracking

- [ ] **Started**: Multi-platform export implementation begun
- [ ] **Format Manager**: Core export coordination complete
- [ ] **WebVTT Exporter**: YouTube-compatible format working
- [ ] **DocBook Exporter**: Publishing XML format implemented
- [ ] **JSON Exporter**: App development format complete
- [ ] **CLI Integration**: Multi-format command-line interface
- [ ] **Testing Complete**: All format export tests pass
- [ ] **Platform Validation**: Formats tested with target platforms

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Why This Approach is Lean:**
1. **Standard Libraries**: Uses only stdlib XML/JSON, no heavy dependencies
2. **Simple Abstractions**: Clear format exporter interface
3. **Optional Feature**: Can export SRT only if other formats not needed
4. **Minimal Code**: 150 lines total for all format support
5. **Plugin Architecture**: Easy to add/remove formats

#### **Platform Integration Strategy:**
- **YouTube**: WebVTT with proper timestamps and Sanskrit styling
- **Book Publishing**: DocBook XML with publishing metadata and footnotes
- **App Development**: JSON-LD with full metadata and structured data
- **Extensibility**: Abstract interface allows adding new formats easily

### **Success Criteria for Story Completion:**
1. ✅ **Multi-Platform Support**: YouTube, book, and app formats working
2. ✅ **Sanskrit Preservation**: Unicode integrity across all formats
3. ✅ **Metadata Integration**: Quality and processing data included
4. ✅ **Performance Maintained**: <50ms export overhead per format
5. ✅ **Lean Compliance**: <150 lines, no new dependencies

**Story Definition of Done**: Multi-platform export system generates YouTube WebVTT, publishing XML, and app JSON formats while preserving Sanskrit content and metadata.

---

## 🤖 Dev Agent Instructions

**IMPLEMENTATION PRIORITY**: This story completes the Epic 6 vision by enabling seamless integration with YouTube, book publishing, and app development workflows.

**LEAN IMPLEMENTATION APPROACH**:
1. Start with simple format manager and abstract exporter interface
2. Implement WebVTT exporter for YouTube with Sanskrit support
3. Add DocBook XML exporter for publishing workflows
4. Add JSON-LD exporter for app development
5. Test format compatibility with target platforms

**CRITICAL SUCCESS FACTORS**:
- Must support YouTube, book publishing, and app creation workflows
- Must preserve Sanskrit Unicode characters across all formats
- Must include quality metadata in platform-appropriate ways  
- Must stay within 150-line code budget
- Must integrate seamlessly with existing CLI

**Story Status**: ⏳ Ready for Implementation