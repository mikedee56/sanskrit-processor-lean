# Story 6.5: Context-Aware Processing Pipeline

**Epic**: Sanskrit Content Quality Excellence  
**Story Points**: 13  
**Priority**: High  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete Stories 6.1, 6.2, 6.3 first  
⚠️ **INTEGRATION STORY**: Orchestrates all quality improvements into unified pipeline

## 📋 User Story

**As a** Sanskrit content processor handling diverse content types  
**I want** intelligent routing to specialized processors based on content context  
**So that** mantras, verses, titles, and commentary are processed with appropriate specialized handling

## 🎯 Business Value

- **Quality Orchestration**: Ensures each content type gets optimal processing
- **Performance Optimization**: Avoid unnecessary processing for simple content  
- **Extensibility**: Foundation for future specialized processors
- **Error Reduction**: Context-appropriate processing reduces false corrections

## ✅ Acceptance Criteria

### **AC 1: Content Classification Pipeline**
- [ ] **Content Type Detection**: Classify as mantra, verse, title, commentary, regular
- [ ] **Confidence Scoring**: Each classification includes confidence level
- [ ] **Multi-Class Support**: Handle mixed content within single segment
- [ ] **Performance**: <50ms classification per segment

### **AC 2: Specialized Routing System**
- [ ] **Compound Processor**: Route titles to compound term recognition (Story 6.1)
- [ ] **Sacred Processor**: Route mantras/verses to sacred text preservation (Story 6.2)
- [ ] **Database Processor**: Route all content through database integration (Story 6.3)
- [ ] **Scripture Processor**: Route verses to reference engine (Story 6.4)
- [ ] **Regular Processor**: Route simple text to standard processing

### **AC 3: Quality Enhancement Pipeline**
- [ ] **Multi-Pass Processing**: Content can go through multiple specialized processors
- [ ] **Quality Aggregation**: Combine results from different processors intelligently  
- [ ] **Confidence Tracking**: Track confidence through entire pipeline
- [ ] **Error Handling**: Graceful fallback if any specialized processor fails

### **AC 4: Lean Implementation**
- [ ] **Code Limit**: Maximum 300 lines for entire pipeline system
- [ ] **Simple Architecture**: Rule-based routing, no complex state machines
- [ ] **Performance**: Maintain >1,500 segments/second overall processing
- [ ] **Memory**: <25MB additional footprint

## 🏗️ Implementation Plan

### **Content Classification Engine**
```python
# New: processors/context_pipeline.py (~200 lines)
@dataclass
class ContentClassification:
    content_type: str  # 'mantra', 'verse', 'title', 'commentary', 'regular'
    confidence: float
    specialized_processors: List[str]  # Which processors to apply
    metadata: Dict[str, Any] = None

class ContextAwarePipeline:
    def __init__(self, config: dict):
        # Initialize all specialized processors
        self.compound_processor = CompoundTermMatcher(config)  # Story 6.1
        self.sacred_processor = SacredTextProcessor(config)    # Story 6.2
        self.database_processor = HybridLexiconLoader(config)  # Story 6.3
        self.scripture_processor = ScriptureReferenceEngine(config)  # Story 6.4
        
        # Classification rules
        self.classifiers = self._build_classifiers()
        
    def process_segment(self, text: str) -> ProcessingResult:
        """Main pipeline orchestration."""
        # 1. Classify content type
        classification = self.classify_content(text)
        
        # 2. Route to appropriate processors
        processed_text = text
        corrections = []
        metadata = {}
        
        # 3. Apply specialized processing based on classification
        if 'compound' in classification.specialized_processors:
            processed_text, compound_corrections = self.compound_processor.process(processed_text)
            corrections.extend(compound_corrections)
            
        if 'sacred' in classification.specialized_processors:
            processed_text, sacred_metadata = self.sacred_processor.process(processed_text)
            metadata.update(sacred_metadata)
            
        # 4. Always apply database processing (enhanced lexicon)
        processed_text, db_corrections = self.database_processor.process(processed_text)
        corrections.extend(db_corrections)
        
        if 'scripture' in classification.specialized_processors:
            scripture_refs = self.scripture_processor.identify_verses(processed_text)
            metadata['scripture_references'] = scripture_refs
            
        # 5. Generate comprehensive result
        return ProcessingResult(
            original_text=text,
            processed_text=processed_text,
            content_type=classification.content_type,
            confidence=classification.confidence,
            corrections=corrections,
            metadata=metadata
        )
        
    def classify_content(self, text: str) -> ContentClassification:
        """Simple rule-based content classification."""
        # Rule-based classification using patterns from previous stories
        # Mantras: Contains sacred symbols, sacred words
        # Verses: Contains verse indicators, structured format
        # Titles: Contains title indicators, proper noun patterns
        # Commentary: Regular explanatory text
        pass
```

### **Processing Result Enhancement**
```python
# Enhanced: sanskrit_processor_v2.py 
@dataclass
class ProcessingResult:
    """Enhanced result structure with context awareness."""
    # Existing fields preserved for compatibility
    segments_processed: int
    corrections_made: int
    processing_time: float
    errors: List[str]
    
    # New context-aware fields
    content_classification: Dict[str, str] = None
    specialized_processing: Dict[str, Any] = None
    quality_metrics: Dict[str, float] = None
    metadata_enrichment: Dict[str, Any] = None
```

### **Integration with Main Processor**
```python
# Modified: sanskrit_processor_v2.py (~100 lines modified)
class SanskritProcessor:
    def __init__(self, lexicon_dir: Path, config: dict = None):
        # Replace simple processing with context-aware pipeline
        self.pipeline = ContextAwarePipeline(config)
        
    def process_text(self, text: str) -> str:
        """Enhanced processing with context awareness."""
        result = self.pipeline.process_segment(text)
        return result.processed_text
        
    def process_segment_detailed(self, segment: SRTSegment) -> ProcessingResult:
        """New method providing detailed processing results."""
        return self.pipeline.process_segment(segment.text)
```

## 📁 Files to Create/Modify

### **New Files:**
- `processors/context_pipeline.py` - Main pipeline orchestration (~200 lines)
- `processors/content_classifier.py` - Content type classification (~100 lines)

### **Modified Files:**
- `sanskrit_processor_v2.py` - Pipeline integration (~100 lines modified)
- `cli.py` - Enhanced output with context information (~50 lines)

**Total New Code**: ~300 lines (within limit)

## 📊 Success Metrics

### **Quality Orchestration**
- **Classification Accuracy**: 90%+ correct content type identification
- **Processing Quality**: 95%+ appropriate processor selection
- **Performance**: >1,500 segments/second end-to-end
- **Memory**: <25MB additional footprint

### **Integration Success**
- **All Processors Working**: Stories 6.1-6.4 integrated seamlessly
- **Backward Compatibility**: Existing API continues to work
- **Enhanced Output**: Rich metadata and context information available
- **Error Handling**: Graceful degradation if specialized processors fail

## 🤖 Dev Agent Instructions

**INTEGRATION FOCUS**: This story brings together all previous quality improvements into a unified, intelligent processing system.

**LEAN APPROACH**: Simple rule-based classification, clear processor routing, maintain performance.

**Story Status**: ⏳ Ready for Implementation