"""Enhanced logging system with structured context and JSON output."""

import logging
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from exceptions import SanskritProcessorError


class StructuredLogger:
    """Enhanced logger with contextual information and JSON output."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(name)
        self.config = config or {}
        
        # Get logging configuration
        logging_config = self.config.get('logging', {})
        self.use_json = logging_config.get('json_output', False)
        self.level = logging_config.get('level', 'INFO').upper()
        self.include_context = logging_config.get('include_context', True)
        self.file_output = logging_config.get('file_output')
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """Set up logger with appropriate handlers and formatters."""
        # Set log level
        numeric_level = getattr(logging, self.level, logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        if self.use_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if self.file_output:
            file_path = Path(self.file_output)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(JSONFormatter() if self.use_json else
                                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            
            self.logger.addHandler(file_handler)
    
    def log_with_context(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Log with structured context information."""
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        
        if self.use_json or context:
            extra_data = {'context': context or {}} if self.include_context else {}
            log_method(message, extra=extra_data)
        else:
            log_method(message)
    
    def error_with_suggestions(self, error: SanskritProcessorError, context: Optional[Dict[str, Any]] = None):
        """Log errors with actionable suggestions."""
        context = context or {}
        context.update(error.context)
        
        error_data = {
            'error_code': error.error_code,
            'suggestions': error.suggestions,
            'context': context
        }
        
        if self.use_json:
            self.logger.error(str(error), extra={'error_data': error_data})
        else:
            # Format for human-readable console output
            formatted_msg = f"❌ {error}"
            if error.suggestions:
                formatted_msg += "\n💡 Suggestions:"
                for suggestion in error.suggestions:
                    formatted_msg += f"\n   • {suggestion}"
            
            self.logger.error(formatted_msg)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message with context."""
        self.log_with_context('DEBUG', message, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message with context.""" 
        self.log_with_context('INFO', message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message with context."""
        self.log_with_context('WARNING', message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log error message with context."""
        self.log_with_context('ERROR', message, context)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log critical message with context."""
        self.log_with_context('CRITICAL', message, context)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            'timestamp': self.formatTime(record),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage()
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # Add error data if available
        if hasattr(record, 'error_data'):
            log_data['error_data'] = record.error_data
            
        # Add filename and line number for debugging
        if record.filename and record.lineno:
            log_data['location'] = {
                'filename': record.filename,
                'line': record.lineno,
                'function': record.funcName
            }
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


def create_logger(name: str, config: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """Create a structured logger instance."""
    return StructuredLogger(name, config)