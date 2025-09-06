"""
Verse Formatter for preserving sacred text structure.

Maintains traditional formatting for mantras, verses, and prayers while
enabling lexicon corrections to be applied properly.
"""

import re
from typing import List


class VerseFormatter:
    """
    Intelligent verse structure preservation for sacred texts.
    Maintains traditional formatting while enabling corrections.
    """
    
    def __init__(self):
        self.verse_patterns = self._compile_verse_patterns()
        
    def _compile_verse_patterns(self) -> dict:
        """Compile regex patterns for verse structure detection."""
        return {
            'pipe_break': re.compile(r'\s*\|\s*'),
            'double_pipe_break': re.compile(r'\s*\|\|\s*'),
            'danda_break': re.compile(r'\s*।\s*'),
            'double_danda_break': re.compile(r'\s*।।\s*'),
            'excessive_spaces': re.compile(r'\s{3,}'),
            'line_breaks': re.compile(r'\n\s*\n'),
            'mantra_hyphens': re.compile(r'(\w+)-(\w+)-(\w+)')  # Om-mani-padme pattern
        }
        
    def process_verse(self, text: str, content_type: str) -> str:
        """
        Process verse content while preserving sacred structure.
        Different handling for mantras vs verses vs prayers.
        """
        if content_type == 'mantra':
            return self._process_mantra(text)
        elif content_type == 'verse':
            return self._process_verse(text)
        elif content_type == 'prayer':
            return self._process_prayer(text)
        else:
            return text
            
    def _process_mantra(self, text: str) -> str:
        """
        Mantra processing: preserve rhythm, sacred symbols, pronunciation guides.
        """
        # 1. Normalize excessive spacing but preserve meaningful structure
        text = self.verse_patterns['excessive_spaces'].sub('  ', text)
        
        # 2. Preserve meaningful hyphens in mantras (Om-mani-padme-hum)
        # Don't remove hyphens that are part of traditional mantra structure
        
        # 3. Maintain line structure for multi-line mantras
        # Preserve existing line breaks in mantra context
        text = text.strip()
        
        return text
        
    def _process_verse(self, text: str) -> str:
        """
        Verse processing: preserve meter, line breaks, traditional punctuation.
        """
        # 1. Detect and preserve verse boundaries (| and ||)
        boundaries = self._detect_verse_boundaries(text)
        
        # 2. Preserve line breaks at verse boundaries if they exist
        # Insert appropriate spacing around pipe symbols
        text = self.verse_patterns['pipe_break'].sub(' | ', text)
        text = self.verse_patterns['double_pipe_break'].sub(' || ', text)
        text = self.verse_patterns['danda_break'].sub(' । ', text)
        text = self.verse_patterns['double_danda_break'].sub(' ।। ', text)
        
        # 3. Maintain traditional indentation patterns
        # Preserve existing line structure
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Clean up excessive spaces within lines but preserve structure
            line = re.sub(r' {2,}', ' ', line.strip())
            if line:  # Only add non-empty lines
                formatted_lines.append(line)
        
        # 4. Rejoin with appropriate spacing
        if len(formatted_lines) > 1:
            # Multi-line verse: preserve line structure
            return '\n'.join(formatted_lines)
        else:
            # Single line verse: return cleaned
            return formatted_lines[0] if formatted_lines else text.strip()
        
    def _process_prayer(self, text: str) -> str:
        """
        Prayer processing: similar to mantra but with different formatting rules.
        """
        # Prayers are processed similar to mantras but with less strict formatting
        return self._process_mantra(text)
        
    def _detect_verse_boundaries(self, text: str) -> List[int]:
        """Find positions of verse breaks (pipes, dandas)."""
        boundaries = []
        boundary_symbols = ['|', '।']
        
        for i, char in enumerate(text):
            if char in boundary_symbols:
                boundaries.append(i)
                
        return boundaries
    
    def preserve_verse_structure(self, text: str) -> str:
        """
        General verse structure preservation for any sacred content.
        Used when content type is unknown but structure needs preservation.
        """
        # Basic structure preservation
        text = self.verse_patterns['excessive_spaces'].sub('  ', text)
        
        # Clean up spacing around sacred symbols
        text = re.sub(r'\s*\|\s*', ' | ', text)
        text = re.sub(r'\s*\|\|\s*', ' || ', text)
        text = re.sub(r'\s*।\s*', ' । ', text)
        text = re.sub(r'\s*।।\s*', ' ।। ', text)
        
        return text.strip()
    
    def detect_traditional_formatting(self, text: str) -> dict:
        """
        Analyze text for traditional formatting patterns.
        Returns dict with detected patterns for preservation decisions.
        """
        patterns = {
            'has_pipes': '|' in text or '||' in text,
            'has_dandas': '।' in text or '।।' in text,
            'has_line_breaks': '\n' in text,
            'has_indentation': any(line.startswith(' ') for line in text.split('\n')),
            'has_mantra_hyphens': bool(self.verse_patterns['mantra_hyphens'].search(text)),
            'multiple_lines': len(text.split('\n')) > 1
        }
        
        return patterns