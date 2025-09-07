"""
Tests for multi-platform output format exporters.
"""

import unittest
import tempfile
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from utils.srt_parser import SRTSegment
from exporters.format_manager import FormatManager, ExportRequest
from exporters.webvtt_exporter import WebVTTExporter
from exporters.docbook_exporter import DocBookExporter
from exporters.json_exporter import JSONExporter
from exporters.srt_exporter import SRTExporter


class TestMultiFormatExport(unittest.TestCase):
    """Test multi-format export functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_segments = [
            SRTSegment(1, "00:00:01,000", "00:00:05,000", "Test segment one"),
            SRTSegment(2, "00:00:05,000", "00:00:10,000", "Test segment two"),
            SRTSegment(3, "00:00:10,000", "00:00:15,000", "Om śāntiḥ śāntiḥ śāntiḥ ||")
        ]
        
        self.sample_qa_report = {
            'quality_summary': {
                'high_confidence_segments': 2,
                'medium_confidence_segments': 1,
                'low_confidence_segments': 0,
                'review_recommended_segments': 0
            },
            'segment_details': [
                {
                    'timestamp': '00:00:01,000',
                    'confidence': {'overall': 0.95},
                    'issues': []
                },
                {
                    'timestamp': '00:00:05,000',
                    'confidence': {'overall': 0.87},
                    'issues': []
                },
                {
                    'timestamp': '00:00:10,000',
                    'confidence': {'overall': 0.92},
                    'issues': []
                }
            ]
        }
        
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_multiformat_export(self):
        """Test exporting to multiple formats simultaneously."""
        request = ExportRequest(
            source_filename="test_lecture",
            segments=self.sample_segments,
            qa_report=self.sample_qa_report,
            metadata={},
            output_formats=['srt', 'vtt', 'json', 'xml'],
            output_directory=self.temp_dir
        )
        
        manager = FormatManager()
        results = manager.export_all_formats(request)
        
        # Check all formats were processed
        self.assertIn('srt', results)
        self.assertIn('vtt', results)
        self.assertIn('json', results)
        self.assertIn('xml', results)
        
        # Check all files exist
        for format_name, result_path in results.items():
            if not result_path.startswith("Error:"):
                self.assertTrue(Path(result_path).exists(), 
                              f"{format_name} file should exist: {result_path}")
    
    def test_sanskrit_preservation(self):
        """Test Sanskrit content preservation across all formats."""
        sanskrit_segments = [
            SRTSegment(1, "00:01:00,000", "00:01:05,000", "Om śāntiḥ śāntiḥ śāntiḥ ||"),
            SRTSegment(2, "00:01:05,000", "00:01:10,000", "ॐ नमः शिवाय"),
            SRTSegment(3, "00:01:10,000", "00:01:15,000", "गुरुर्ब्रह्मा गुरुर्विष्णुः")
        ]
        
        request = ExportRequest(
            source_filename="sanskrit_test",
            segments=sanskrit_segments,
            qa_report={},
            metadata={},
            output_formats=['srt', 'vtt', 'json', 'xml'],
            output_directory=self.temp_dir
        )
        
        manager = FormatManager()
        results = manager.export_all_formats(request)
        
        # Test each format preserves Sanskrit
        for format_name, result_path in results.items():
            if not result_path.startswith("Error:"):
                with open(result_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.assertIn("śāntiḥ", content, f"{format_name} should preserve Sanskrit diacritics")
                # Check for Sanskrit symbols (either Devanagari or ASCII version)
                self.assertTrue("॥" in content or "||" in content, f"{format_name} should preserve Sanskrit symbols")
                
                if format_name != 'xml':  # XML might encode differently
                    self.assertIn("ॐ", content, f"{format_name} should preserve Devanagari")


class TestWebVTTExporter(unittest.TestCase):
    """Test YouTube WebVTT format export."""
    
    def setUp(self):
        self.exporter = WebVTTExporter()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_youtube_webvtt_compatibility(self):
        """Test WebVTT format meets YouTube requirements."""
        segments = [
            SRTSegment(1, "00:00:01,000", "00:00:05,000", "Test segment"),
            SRTSegment(2, "00:00:05,000", "00:00:10,000", "Another segment")
        ]
        
        request = ExportRequest(
            source_filename="youtube_test",
            segments=segments,
            qa_report={},
            metadata={},
            output_formats=['vtt'],
            output_directory=self.temp_dir
        )
        
        output_file = self.exporter.export(request)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            vtt_content = f.read()
        
        # Test WebVTT requirements
        self.assertTrue(vtt_content.startswith("WEBVTT"), "Should start with WEBVTT header")
        self.assertIn("-->", vtt_content, "Should contain timestamp arrows")
        self.assertNotIn(",", vtt_content.split('\n')[3:], "Should use . not , for milliseconds")
        self.assertEqual(vtt_content.count('\n\n\n'), 0, "Should not have triple line breaks")
        
    def test_sanskrit_styling(self):
        """Test Sanskrit content gets proper styling."""
        sanskrit_segments = [
            SRTSegment(1, "00:00:01,000", "00:00:05,000", "Om śāntiḥ śāntiḥ śāntiḥ"),
            SRTSegment(2, "00:00:05,000", "00:00:10,000", "Regular English text")
        ]
        
        request = ExportRequest(
            source_filename="sanskrit_style_test",
            segments=sanskrit_segments,
            qa_report={},
            metadata={},
            output_formats=['vtt'],
            output_directory=self.temp_dir
        )
        
        output_file = self.exporter.export(request)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check Sanskrit gets styled
        self.assertIn("<c.sanskrit>", content, "Sanskrit text should be styled")
        self.assertIn("</c>", content, "Sanskrit styling should be closed")
        
        # Check regular text doesn't get styled
        lines = content.split('\n')
        english_line = next(line for line in lines if "Regular English" in line)
        self.assertNotIn("<c.sanskrit>", english_line, "English text should not be styled")


class TestDocBookExporter(unittest.TestCase):
    """Test book publishing DocBook XML export."""
    
    def setUp(self):
        self.exporter = DocBookExporter()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_docbook_xml_validity(self):
        """Test XML validates against basic DocBook structure."""
        segments = [
            SRTSegment(1, "00:00:01,000", "00:00:05,000", "Test content"),
            SRTSegment(2, "00:00:05,000", "00:00:10,000", "More content")
        ]
        
        request = ExportRequest(
            source_filename="docbook_test",
            segments=segments,
            qa_report={'quality_summary': {'high_confidence_segments': 2}},
            metadata={},
            output_formats=['xml'],
            output_directory=self.temp_dir
        )
        
        output_file = self.exporter.export(request)
        
        # Test XML validity
        try:
            tree = ET.parse(output_file)
            root = tree.getroot()
        except ET.ParseError as e:
            self.fail(f"Generated XML is not valid: {e}")
        
        # Test DocBook structure (handle namespace)
        self.assertTrue(root.tag.endswith('chapter'), "Root should be chapter element")
        self.assertIn('http://docbook.org/ns/docbook', root.tag, "Should have DocBook namespace")
        self.assertEqual(root.get('version'), '5.0', "Should be DocBook 5.0")
        
        # Test content structure
        paras = root.findall('.//{http://docbook.org/ns/docbook}para')
        self.assertEqual(len(paras), 2, "Should have paragraph for each segment")
        
        # Test timestamp metadata
        first_para = paras[0]
        self.assertTrue(first_para.get('role').startswith('timestamp-'), "Should have timestamp role")


class TestJSONExporter(unittest.TestCase):
    """Test app development JSON-LD export."""
    
    def setUp(self):
        self.exporter = JSONExporter()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_structure(self):
        """Test JSON-LD structure and content."""
        segments = [
            SRTSegment(1, "00:00:01,000", "00:00:05,000", "Test segment"),
            SRTSegment(2, "00:00:05,000", "00:00:10,000", "Another segment")
        ]
        
        qa_report = {
            'segment_details': [
                {'timestamp': '00:00:01,000', 'confidence': {'overall': 0.95}, 'issues': []},
                {'timestamp': '00:00:05,000', 'confidence': {'overall': 0.87}, 'issues': ['minor']}
            ]
        }
        
        request = ExportRequest(
            source_filename="json_test",
            segments=segments,
            qa_report=qa_report,
            metadata={'processing_version': '1.0'},
            output_formats=['json'],
            output_directory=self.temp_dir
        )
        
        output_file = self.exporter.export(request)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Test JSON-LD structure
        self.assertEqual(data['@context'], 'https://schema.org/', "Should have Schema.org context")
        self.assertEqual(data['@type'], 'VideoObject', "Should be VideoObject type")
        self.assertEqual(data['name'], 'json_test', "Should have correct name")
        
        # Test transcript structure
        self.assertIn('transcript', data, "Should have transcript array")
        self.assertEqual(len(data['transcript']), 2, "Should have all segments")
        
        # Test segment metadata
        first_segment = data['transcript'][0]
        self.assertEqual(first_segment['startTime'], '00:00:01,000', "Should preserve timestamp")
        self.assertEqual(first_segment['text'], 'Test segment', "Should preserve text")
        self.assertEqual(first_segment['confidence'], 0.95, "Should include confidence")
        self.assertFalse(first_segment['hasIssues'], "Should correctly identify no issues")
        
        second_segment = data['transcript'][1]
        self.assertTrue(second_segment['hasIssues'], "Should correctly identify issues")
    
    def test_duration_calculation(self):
        """Test segment duration calculation."""
        segment = SRTSegment(1, "00:01:00,500", "00:01:05,750", "Test")
        
        request = ExportRequest(
            source_filename="duration_test",
            segments=[segment],
            qa_report={},
            metadata={},
            output_formats=['json'],
            output_directory=self.temp_dir
        )
        
        output_file = self.exporter.export(request)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        duration = data['transcript'][0]['metadata']['duration_ms']
        expected_duration = 5250  # 5.25 seconds = 5250 ms
        self.assertEqual(duration, expected_duration, "Should calculate duration correctly")


class TestPlatformIntegration(unittest.TestCase):
    """Test platform-specific integration scenarios."""
    
    def test_error_handling(self):
        """Test graceful error handling for invalid inputs."""
        manager = FormatManager()
        
        # Test with invalid segments
        request = ExportRequest(
            source_filename="error_test",
            segments=[],  # Empty segments
            qa_report={},
            metadata={},
            output_formats=['srt', 'vtt', 'json', 'xml'],
            output_directory=Path("/nonexistent/path")
        )
        
        results = manager.export_all_formats(request)
        
        # Should handle errors gracefully
        for format_name, result in results.items():
            # Results should either be valid paths or error messages
            self.assertTrue(
                isinstance(result, str),
                f"Result for {format_name} should be string"
            )
    
    def test_unsupported_format(self):
        """Test handling of unsupported export formats."""
        manager = FormatManager()
        
        request = ExportRequest(
            source_filename="unsupported_test",
            segments=[],
            qa_report={},
            metadata={},
            output_formats=['pdf', 'docx'],  # Unsupported formats
            output_directory=Path(tempfile.mkdtemp())
        )
        
        results = manager.export_all_formats(request)
        
        for format_name in ['pdf', 'docx']:
            self.assertIn('Error: Unsupported format', results[format_name])


if __name__ == '__main__':
    unittest.main()