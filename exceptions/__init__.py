"""Enhanced error handling module for Sanskrit Processor."""

from .processing_errors import (
    SanskritProcessorError,
    ConfigurationError, 
    ProcessingError,
    ServiceError,
    FileError,
    EXIT_CODES,
    get_exit_code
)

__all__ = [
    'SanskritProcessorError',
    'ConfigurationError',
    'ProcessingError', 
    'ServiceError',
    'FileError',
    'EXIT_CODES',
    'get_exit_code'
]