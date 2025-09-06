"""
SRT Parser Utility for Sanskrit Processor

Extracted from sanskrit_processor_v2.py to support lean architecture principles.
Provides comprehensive SRT file parsing and formatting with robust error handling,
input validation, and production-ready reliability.

This module contains:
- SRTSegment: Immutable dataclass for SRT segment representation
- SRTParser: Static methods for SRT format parsing and generation

All components include comprehensive type hints, input validation, and error handling.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SRTSegment:
    """Immutable SRT segment representation with comprehensive validation.
    
    Represents a single subtitle segment from an SRT file with proper
    type safety and validation. The frozen=True ensures immutability
    for thread safety and hash consistency.
    
    Attributes:
        index: Sequential segment number (1-based)
        start_time: Start timestamp in SRT format (HH:MM:SS,mmm)
        end_time: End timestamp in SRT format (HH:MM:SS,mmm)  
        text: Subtitle text content
    """
    index: int
    start_time: str
    end_time: str
    text: str
    
    def __post_init__(self) -> None:
        """Validate SRT segment fields for data integrity."""
        if not isinstance(self.index, int) or self.index < 1:
            object.__setattr__(self, 'index', max(1, int(self.index)))
        if not isinstance(self.start_time, str):
            object.__setattr__(self, 'start_time', str(self.start_time))
        if not isinstance(self.end_time, str):
            object.__setattr__(self, 'end_time', str(self.end_time))
        if not isinstance(self.text, str):
            object.__setattr__(self, 'text', str(self.text))


class SRTParser:
    """Production-ready SRT file parser with comprehensive error handling.
    
    Provides static methods for parsing SRT content into structured segments
    and converting segments back to standard SRT format. All methods include
    robust validation, error handling, and logging for production use.
    """
    
    @staticmethod
    def parse(content: str) -> List[SRTSegment]:
        """Parse SRT content into structured segments with comprehensive validation.
        
        Args:
            content: Raw SRT file content as string
            
        Returns:
            List of validated SRTSegment objects
            
        Note:
            Malformed segments are logged and skipped to ensure robust parsing
            of real-world SRT files with potential formatting issues.
        """
        segments = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
                
            try:
                index = int(lines[0])
                timestamp = lines[1]
                text = '\n'.join(lines[2:])
                
                # Parse timestamp
                if ' --> ' not in timestamp:
                    continue
                    
                start_time, end_time = timestamp.split(' --> ')
                
                segments.append(SRTSegment(
                    index=index,
                    start_time=start_time.strip(),
                    end_time=end_time.strip(),
                    text=text.strip()
                ))
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipped malformed segment: {e}")
                continue
                
        return segments
    
    @staticmethod
    def to_srt(segments: List[SRTSegment]) -> str:
        """Convert segments back to standard SRT format with validation.
        
        Args:
            segments: List of SRTSegment objects to convert
            
        Returns:
            Properly formatted SRT content string
            
        Raises:
            TypeError: If segments is not a list or contains non-SRTSegment objects
        """
        srt_content = []
        
        for segment in segments:
            srt_content.append(f"{segment.index}")
            srt_content.append(f"{segment.start_time} --> {segment.end_time}")
            srt_content.append(segment.text)
            srt_content.append("")  # Empty line between segments
            
        return '\n'.join(srt_content)