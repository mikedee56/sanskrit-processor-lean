"""Enhanced error handling for Sanskrit Processor with structured error information."""

from typing import List, Dict, Any, Optional


class SanskritProcessorError(Exception):
    """Base exception for Sanskrit processor with structured error info."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 suggestions: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code or "GENERAL_ERROR"
        self.suggestions = suggestions or []
        self.context = context or {}
        
    def get_formatted_message(self) -> str:
        """Get user-friendly formatted error message with suggestions."""
        msg = f"Error: {self}"
        if self.suggestions:
            msg += "\n\nSuggestions:"
            for suggestion in self.suggestions:
                msg += f"\n  • {suggestion}"
        return msg


class ConfigurationError(SanskritProcessorError):
    """Configuration-related errors with specific guidance."""
    
    def __init__(self, message: str, config_file: Optional[str] = None, 
                 config_section: Optional[str] = None, suggestions: Optional[List[str]] = None):
        suggestions = suggestions or []
        if config_file and not any("config" in s.lower() for s in suggestions):
            suggestions.append(f"Check configuration file: {config_file}")
        if config_section:
            suggestions.append(f"Verify the '{config_section}' section in config")
        
        super().__init__(message, "CONFIG_ERROR", suggestions, 
                        {"config_file": config_file, "config_section": config_section})


class ProcessingError(SanskritProcessorError):
    """Text processing errors with context."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 segment_number: Optional[int] = None, processing_stage: Optional[str] = None,
                 suggestions: Optional[List[str]] = None):
        suggestions = suggestions or []
        if file_path and not any("file" in s.lower() for s in suggestions):
            suggestions.append(f"Check input file: {file_path}")
        if segment_number:
            suggestions.append(f"Review segment {segment_number} for formatting issues")
        
        super().__init__(message, "PROCESSING_ERROR", suggestions,
                        {"file_path": file_path, "segment_number": segment_number, 
                         "processing_stage": processing_stage})


class ServiceError(SanskritProcessorError):
    """External service integration errors."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 service_url: Optional[str] = None, suggestions: Optional[List[str]] = None):
        suggestions = suggestions or []
        if service_name:
            suggestions.append(f"Check {service_name} service status")
        suggestions.append("Processing will continue with local-only features")
        if service_url:
            suggestions.append(f"Verify connectivity to: {service_url}")
        
        super().__init__(message, "SERVICE_ERROR", suggestions,
                        {"service_name": service_name, "service_url": service_url})


class FileError(SanskritProcessorError):
    """File I/O and format errors."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 file_operation: Optional[str] = None, suggestions: Optional[List[str]] = None):
        suggestions = suggestions or []
        if file_path:
            suggestions.append(f"Verify file exists and is readable: {file_path}")
        if file_operation == "read":
            suggestions.append("Check file permissions and encoding (UTF-8 required)")
        elif file_operation == "write":
            suggestions.append("Ensure output directory exists and is writable")
        suggestions.append("Use --verbose flag for detailed error information")
        
        super().__init__(message, "FILE_ERROR", suggestions,
                        {"file_path": file_path, "file_operation": file_operation})


# Exit codes for CLI integration
EXIT_CODES = {
    "SUCCESS": 0,
    "GENERAL_ERROR": 1,
    "CONFIG_ERROR": 2,
    "PROCESSING_ERROR": 3,
    "FILE_ERROR": 4,
    "SERVICE_ERROR": 5
}


def get_exit_code(error: Exception) -> int:
    """Get appropriate exit code for an error."""
    if isinstance(error, ConfigurationError):
        return EXIT_CODES["CONFIG_ERROR"]
    elif isinstance(error, ProcessingError):
        return EXIT_CODES["PROCESSING_ERROR"]
    elif isinstance(error, FileError):
        return EXIT_CODES["FILE_ERROR"]
    elif isinstance(error, ServiceError):
        return EXIT_CODES["SERVICE_ERROR"]
    elif isinstance(error, SanskritProcessorError):
        return EXIT_CODES["GENERAL_ERROR"]
    else:
        return EXIT_CODES["GENERAL_ERROR"]