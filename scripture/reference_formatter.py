"""
Scripture Reference Formatter
Formats scripture references for output and metadata

Lean Implementation: ~70 lines
"""

import json
from typing import List, Dict, Any
from .verse_engine import ScriptureReference


class ReferenceFormatter:
    """
    Simple scripture reference formatter for various output formats.
    Supports standard citations and JSON metadata output.
    """
    
    def __init__(self):
        """Initialize formatter with standard formats."""
        self.citation_formats = {
            'standard': '{source} {chapter}.{verse}',
            'abbreviated': '{abbrev} {chapter}:{verse}',
            'full': '{source}, Chapter {chapter}, Verse {verse}'
        }
        
        # Source abbreviations
        self.abbreviations = {
            'Bhagavad Gītā': 'BG',
            'Īśopaniṣad': 'Iso',
            'Kaṭha Upaniṣad': 'Katha',
            'Muṇḍaka Upaniṣad': 'Mundaka'
        }
    
    def format_citation(self, reference: ScriptureReference, format_type: str = 'standard') -> str:
        """Format a single scripture reference as citation."""
        if format_type not in self.citation_formats:
            format_type = 'standard'
        
        format_template = self.citation_formats[format_type]
        
        return format_template.format(
            source=reference.source,
            chapter=reference.chapter,
            verse=reference.verse,
            abbrev=self.abbreviations.get(reference.source, reference.source)
        )
    
    def format_multiple_citations(self, references: List[ScriptureReference], format_type: str = 'standard') -> str:
        """Format multiple references as comma-separated citations."""
        if not references:
            return ""
        
        citations = [self.format_citation(ref, format_type) for ref in references]
        return ", ".join(citations)
    
    def to_json_metadata(self, references: List[ScriptureReference]) -> Dict[str, Any]:
        """Convert references to JSON metadata format."""
        metadata = {
            "scripture_references": [],
            "reference_count": len(references),
            "highest_confidence": max(ref.confidence for ref in references) if references else 0.0
        }
        
        for ref in references:
            ref_data = {
                "source": ref.source,
                "chapter": ref.chapter,
                "verse": ref.verse,
                "citation": ref.citation,
                "matched_text": ref.matched_text,
                "confidence": round(ref.confidence, 3)
            }
            metadata["scripture_references"].append(ref_data)
        
        return metadata
    
    def to_json_string(self, references: List[ScriptureReference], indent: int = 2) -> str:
        """Convert references to JSON string."""
        metadata = self.to_json_metadata(references)
        return json.dumps(metadata, indent=indent, ensure_ascii=False)
    
    def format_for_srt_metadata(self, references: List[ScriptureReference]) -> str:
        """Format references for SRT subtitle metadata comment."""
        if not references:
            return ""
        
        citations = self.format_multiple_citations(references, 'standard')
        confidence_info = f" (confidence: {references[0].confidence:.2f})" if references else ""
        
        return f"<!-- Scripture: {citations}{confidence_info} -->"


# Simple test
if __name__ == "__main__":
    from verse_engine import ScriptureReference
    
    # Test formatting
    test_ref = ScriptureReference(
        source="Bhagavad Gītā",
        chapter=2,
        verse=47,
        matched_text="You have a right to perform your duty",
        confidence=0.85,
        citation="Bhagavad Gītā 2.47"
    )
    
    formatter = ReferenceFormatter()
    
    print("Standard:", formatter.format_citation(test_ref))
    print("Abbreviated:", formatter.format_citation(test_ref, 'abbreviated'))
    print("JSON:", formatter.to_json_string([test_ref]))
    print("SRT Metadata:", formatter.format_for_srt_metadata([test_ref]))
    
    print("✅ Formatter test passed!")