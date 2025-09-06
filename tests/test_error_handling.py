#!/usr/bin/env python3
"""
Comprehensive tests for enhanced error handling system.
Tests exception hierarchy, structured logging, and CLI error display.
"""

import unittest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
import sys
from io import StringIO

# Import the error handling components
from exceptions import (
    SanskritProcessorError, 
    ConfigurationError, 
    ProcessingError, 
    ServiceError, 
    FileError,
    get_exit_code,
    EXIT_CODES
)
from utils.structured_logger import StructuredLogger, create_logger
from sanskrit_processor_v2 import SanskritProcessor


class TestExceptionHierarchy(unittest.TestCase):
    """Test custom exception hierarchy and error codes."""
    
    def test_base_exception_creation(self):
        """Test base SanskritProcessorError functionality."""
        error = SanskritProcessorError(
            "Test error message",
            error_code="TEST_ERROR",
            suggestions=["Fix this", "Try that"],
            context={"file": "test.srt"}
        )
        
        self.assertEqual(str(error), "Test error message")
        self.assertEqual(error.error_code, "TEST_ERROR")
        self.assertEqual(error.suggestions, ["Fix this", "Try that"])
        self.assertEqual(error.context, {"file": "test.srt"})
    
    def test_configuration_error(self):
        """Test ConfigurationError with specific guidance."""
        error = ConfigurationError(
            "Invalid fuzzy matching threshold: 1.5",
            config_file="config.yaml",
            config_section="processing",
            suggestions=["Use threshold between 0.0 and 1.0"]
        )
        
        # Check that config file is mentioned in suggestions
        config_mentioned = any("config.yaml" in s for s in error.suggestions)
        self.assertTrue(config_mentioned)
        processing_mentioned = any("processing" in s for s in error.suggestions)
        self.assertTrue(processing_mentioned)
        self.assertEqual(error.error_code, "CONFIG_ERROR")
        self.assertEqual(error.context["config_file"], "config.yaml")
    
    def test_processing_error(self):
        """Test ProcessingError with context."""
        error = ProcessingError(
            "Failed to process segment",
            file_path="test.srt",
            segment_number=42,
            processing_stage="lexicon_matching"
        )
        
        self.assertEqual(error.error_code, "PROCESSING_ERROR")
        self.assertEqual(error.context["segment_number"], 42)
        # Check that input file is mentioned in suggestions
        file_mentioned = any("test.srt" in s for s in error.suggestions)
        self.assertTrue(file_mentioned)
        segment_mentioned = any("segment 42" in s for s in error.suggestions)
        self.assertTrue(segment_mentioned)
    
    def test_service_error(self):
        """Test ServiceError with service information."""
        error = ServiceError(
            "MCP connection failed",
            service_name="MCP",
            service_url="ws://localhost:8080"
        )
        
        self.assertEqual(error.error_code, "SERVICE_ERROR")
        # Check that service name is mentioned in suggestions
        mcp_mentioned = any("MCP" in s for s in error.suggestions)
        self.assertTrue(mcp_mentioned)
        url_mentioned = any("localhost:8080" in s for s in error.suggestions)
        self.assertTrue(url_mentioned)
        local_mentioned = any("local-only" in s for s in error.suggestions)
        self.assertTrue(local_mentioned)
    
    def test_file_error(self):
        """Test FileError with file operations."""
        error = FileError(
            "Permission denied",
            file_path="test.srt",
            file_operation="read"
        )
        
        self.assertEqual(error.error_code, "FILE_ERROR")
        # Check that permissions are mentioned in suggestions
        permissions_mentioned = any("permissions" in s for s in error.suggestions)
        self.assertTrue(permissions_mentioned)
        verbose_mentioned = any("--verbose" in s for s in error.suggestions)
        self.assertTrue(verbose_mentioned)
    
    def test_formatted_message(self):
        """Test get_formatted_message method."""
        error = ConfigurationError(
            "Invalid config",
            suggestions=["Fix config.yaml", "Check syntax"]
        )
        
        formatted = error.get_formatted_message()
        self.assertIn("Error:", formatted)
        self.assertIn("Suggestions:", formatted)
        self.assertIn("• Fix config.yaml", formatted)
        self.assertIn("• Check syntax", formatted)
    
    def test_exit_codes(self):
        """Test exit code mapping."""
        config_error = ConfigurationError("Config error")
        processing_error = ProcessingError("Processing error")
        service_error = ServiceError("Service error")
        file_error = FileError("File error")
        base_error = SanskritProcessorError("Base error")
        generic_error = Exception("Generic error")
        
        self.assertEqual(get_exit_code(config_error), EXIT_CODES["CONFIG_ERROR"])
        self.assertEqual(get_exit_code(processing_error), EXIT_CODES["PROCESSING_ERROR"])
        self.assertEqual(get_exit_code(service_error), EXIT_CODES["SERVICE_ERROR"])
        self.assertEqual(get_exit_code(file_error), EXIT_CODES["FILE_ERROR"])
        self.assertEqual(get_exit_code(base_error), EXIT_CODES["GENERAL_ERROR"])
        self.assertEqual(get_exit_code(generic_error), EXIT_CODES["GENERAL_ERROR"])


class TestStructuredLogger(unittest.TestCase):
    """Test structured logging system."""
    
    def setUp(self):
        """Set up test logger."""
        self.config = {
            'logging': {
                'level': 'DEBUG',
                'json_output': False,
                'include_context': True
            }
        }
        
    def test_logger_creation(self):
        """Test structured logger creation."""
        logger = StructuredLogger("test", self.config)
        self.assertIsNotNone(logger.logger)
        self.assertEqual(logger.level, "DEBUG")
        self.assertFalse(logger.use_json)
        self.assertTrue(logger.include_context)
    
    def test_json_logging_config(self):
        """Test JSON logging configuration."""
        config = {
            'logging': {
                'json_output': True,
                'level': 'INFO'
            }
        }
        logger = StructuredLogger("test_json", config)
        self.assertTrue(logger.use_json)
        self.assertEqual(logger.level, "INFO")
    
    @patch('logging.Logger.info')
    def test_log_with_context(self, mock_log):
        """Test logging with context."""
        logger = StructuredLogger("test", self.config)
        
        context = {"file": "test.srt", "stage": "parsing"}
        logger.log_with_context("INFO", "Processing started", context)
        
        mock_log.assert_called_once()
    
    @patch('logging.Logger.error')
    def test_error_with_suggestions(self, mock_log):
        """Test error logging with suggestions."""
        logger = StructuredLogger("test", self.config)
        
        error = ConfigurationError(
            "Invalid config",
            suggestions=["Fix config.yaml", "Check syntax"]
        )
        
        logger.error_with_suggestions(error)
        mock_log.assert_called_once()
        
        # Verify formatted message contains suggestions
        call_args = mock_log.call_args[0][0]
        self.assertIn("💡", call_args)
        self.assertIn("Fix config.yaml", call_args)
    
    def test_create_logger_function(self):
        """Test create_logger convenience function."""
        logger = create_logger("test_create", self.config)
        self.assertIsInstance(logger, StructuredLogger)
        self.assertEqual(logger.logger.name, "test_create")


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling integration in main components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: self._cleanup_temp_dir())
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_invalid_lexicon_file_error(self):
        """Test error handling for invalid lexicon files."""
        # Create invalid YAML file
        invalid_lexicon = self.temp_dir / "corrections.yaml"
        invalid_lexicon.write_text("invalid: yaml: content:")
        
        # This should raise a FileError
        with self.assertRaises(FileError) as context:
            processor = SanskritProcessor(self.temp_dir)
        
        error = context.exception
        self.assertEqual(error.error_code, "FILE_ERROR")
        self.assertIn("YAML", str(error))
        # Check that validator is mentioned in suggestions  
        validator_mentioned = any("validator" in s for s in error.suggestions)
        self.assertTrue(validator_mentioned)
    
    def test_missing_lexicon_directory(self):
        """Test graceful handling of missing lexicon directory."""
        nonexistent_dir = self.temp_dir / "nonexistent"
        
        # This should work (graceful degradation with warnings)
        # Processor initializes successfully even without lexicon files
        processor = SanskritProcessor(nonexistent_dir)
        
        # Verify processor works with empty lexicons
        self.assertIsNotNone(processor)
        self.assertEqual(len(processor.lexicons.corrections), 0)
        self.assertEqual(len(processor.lexicons.proper_nouns), 0)
    
    def test_processing_nonexistent_file(self):
        """Test processing non-existent SRT file."""
        # Create minimal valid lexicons
        lexicons_dir = self.temp_dir / "lexicons"
        lexicons_dir.mkdir()
        
        corrections = lexicons_dir / "corrections.yaml"
        corrections.write_text("entries: []")
        
        proper_nouns = lexicons_dir / "proper_nouns.yaml"
        proper_nouns.write_text("entries: []")
        
        processor = SanskritProcessor(lexicons_dir)
        
        nonexistent_file = self.temp_dir / "nonexistent.srt"
        output_file = self.temp_dir / "output.srt"
        
        with self.assertRaises(FileError) as context:
            processor.process_srt_file(nonexistent_file, output_file)
        
        error = context.exception
        self.assertEqual(error.error_code, "FILE_ERROR")
        self.assertIn("not found", str(error))
    
    def test_invalid_srt_content_error(self):
        """Test error handling for invalid SRT content."""
        # Create valid lexicons
        lexicons_dir = self.temp_dir / "lexicons"
        lexicons_dir.mkdir()
        
        corrections = lexicons_dir / "corrections.yaml"
        corrections.write_text("entries: []")
        
        proper_nouns = lexicons_dir / "proper_nouns.yaml"
        proper_nouns.write_text("entries: []")
        
        # Create invalid SRT file
        invalid_srt = self.temp_dir / "invalid.srt"
        invalid_srt.write_text("This is not valid SRT content")
        
        processor = SanskritProcessor(lexicons_dir)
        output_file = self.temp_dir / "output.srt"
        
        with self.assertRaises(ProcessingError) as context:
            processor.process_srt_file(invalid_srt, output_file)
        
        error = context.exception
        self.assertEqual(error.error_code, "PROCESSING_ERROR")
        self.assertIn("segments", str(error))


class TestCLIErrorDisplay(unittest.TestCase):
    """Test CLI error display and exit codes."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: self._cleanup_temp_dir())
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['cli.py', '--validate-config'])
    def test_config_validation_missing_file(self, mock_stdout):
        """Test configuration validation with missing file."""
        from cli import validate_configuration
        
        nonexistent_config = self.temp_dir / "nonexistent.yaml"
        result = validate_configuration(nonexistent_config)
        
        # Should return error exit code
        self.assertEqual(result, 1)
        
        # Should display user-friendly message
        output = mock_stdout.getvalue()
        self.assertIn("not found", output)
        self.assertIn("💡", output)
    
    def test_exit_code_constants(self):
        """Test exit code constants are properly defined."""
        self.assertEqual(EXIT_CODES["SUCCESS"], 0)
        self.assertEqual(EXIT_CODES["CONFIG_ERROR"], 2)
        self.assertEqual(EXIT_CODES["PROCESSING_ERROR"], 3)
        self.assertEqual(EXIT_CODES["FILE_ERROR"], 4)
        self.assertEqual(EXIT_CODES["SERVICE_ERROR"], 5)
    
    def test_error_message_formatting(self):
        """Test error message formatting includes emojis and suggestions."""
        error = ProcessingError(
            "Test processing error",
            suggestions=["Try this", "Or that"]
        )
        
        formatted = error.get_formatted_message()
        self.assertIn("Error:", formatted)
        self.assertIn("Suggestions:", formatted)
        self.assertIn("• Try this", formatted)
        self.assertIn("• Or that", formatted)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that enhanced error handling maintains backward compatibility."""
    
    def test_existing_exception_handling_still_works(self):
        """Test that existing try/except blocks still work."""
        # This should still work with generic Exception handling
        try:
            raise ConfigurationError("Test error")
        except Exception as e:
            self.assertIsInstance(e, Exception)
            self.assertIsInstance(e, ConfigurationError)
    
    def test_string_representation_unchanged(self):
        """Test that string representation of errors is still clean."""
        error = ProcessingError("Simple error message")
        self.assertEqual(str(error), "Simple error message")
    
    def test_inheritance_chain(self):
        """Test exception inheritance chain."""
        error = FileError("Test error")
        
        self.assertIsInstance(error, FileError)
        self.assertIsInstance(error, SanskritProcessorError)
        self.assertIsInstance(error, Exception)


if __name__ == '__main__':
    # Set up test logging to avoid interference
    logging.basicConfig(level=logging.CRITICAL)
    
    unittest.main(verbosity=2)