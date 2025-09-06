# Story 6.6: Quality Assurance Framework

**Epic**: Sanskrit Content Quality Excellence  
**Story Points**: 8  
**Priority**: Medium  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete Story 6.5 (Context-Aware Processing) first  
⚠️ **USER REQUIREMENT**: JSON flagging system for quality issues without marking final output

## 📋 User Story

**As a** content reviewer processing 11k hours of Sanskrit lectures  
**I want** automated quality confidence scoring and issue flagging  
**So that** I can prioritize manual review time on segments needing human attention

## 🎯 Business Value

- **Review Efficiency**: Focus human effort on segments with low confidence scores
- **Quality Transparency**: Clear metrics on processing accuracy per segment
- **Automated Flagging**: JSON output for integration with review platforms
- **Confidence Tracking**: Track quality improvements as system evolves
- **Issue Classification**: Categorize different types of processing concerns

## ✅ Acceptance Criteria

### **AC 1: Confidence Scoring System**
- [ ] **Segment Confidence**: Each segment gets 0.0-1.0 confidence score
- [ ] **Component Scores**: Individual scores from each specialized processor
- [ ] **Aggregation Logic**: Intelligent combination of multiple confidence sources
- [ ] **Threshold Classification**: High (>0.9), Medium (0.7-0.9), Low (<0.7) confidence

### **AC 2: Issue Detection & Flagging**
- [ ] **Quality Issues**: Detect potential transcription errors, formatting problems
- [ ] **Uncertainty Markers**: Flag segments where processor made uncertain choices
- [ ] **Conflict Resolution**: Identify when different processors disagree
- [ ] **JSON Output**: Machine-readable flagging without marking final SRT

### **AC 3: Review Integration Support**
- [ ] **Timestamp Mapping**: Issues linked to exact SRT timestamps
- [ ] **Context Information**: Surrounding text for review context
- [ ] **Priority Scoring**: Critical, High, Medium, Low review priorities
- [ ] **Batch Statistics**: Overall quality metrics per file/batch

### **AC 4: Lean Implementation Requirements**
- [ ] **Code Limit**: Maximum 200 lines for entire QA system
- [ ] **Performance**: <10ms per segment QA overhead
- [ ] **Memory**: <5MB additional footprint
- [ ] **JSON Format**: Simple, readable JSON structure

## 🏗️ Implementation Plan

### **Confidence Scoring Engine**
```python
# New: qa/confidence_scorer.py (~120 lines)
@dataclass
class ConfidenceMetrics:
    lexicon_confidence: float      # How confident in lexicon corrections
    sacred_confidence: float       # Sacred content preservation confidence
    compound_confidence: float     # Compound term recognition confidence
    scripture_confidence: float    # Scripture reference confidence
    overall_confidence: float      # Aggregated final confidence
    processing_flags: List[str] = None

class ConfidenceScorer:
    """
    Lean confidence scoring system for quality assurance.
    Aggregates confidence from all processing components.
    """
    
    def __init__(self, config: dict):
        self.thresholds = config.get('qa', {}).get('thresholds', {
            'high_confidence': 0.9,
            'medium_confidence': 0.7,
            'low_confidence': 0.4
        })
        
    def calculate_confidence(self, processing_result: ProcessingResult) -> ConfidenceMetrics:
        """
        Calculate overall confidence from component confidences.
        Uses weighted average with component-specific weights.
        """
        # Component confidences from specialized processors
        lexicon_conf = self._assess_lexicon_confidence(processing_result)
        sacred_conf = self._assess_sacred_confidence(processing_result)
        compound_conf = self._assess_compound_confidence(processing_result)
        scripture_conf = self._assess_scripture_confidence(processing_result)
        
        # Weighted aggregation
        weights = {'lexicon': 0.4, 'sacred': 0.2, 'compound': 0.2, 'scripture': 0.2}
        overall = (
            lexicon_conf * weights['lexicon'] +
            sacred_conf * weights['sacred'] + 
            compound_conf * weights['compound'] +
            scripture_conf * weights['scripture']
        )
        
        # Generate processing flags
        flags = self._generate_flags(lexicon_conf, sacred_conf, compound_conf, scripture_conf)
        
        return ConfidenceMetrics(
            lexicon_confidence=lexicon_conf,
            sacred_confidence=sacred_conf,
            compound_confidence=compound_conf,
            scripture_confidence=scripture_conf,
            overall_confidence=overall,
            processing_flags=flags
        )
        
    def _assess_lexicon_confidence(self, result: ProcessingResult) -> float:
        """Simple lexicon confidence based on correction patterns."""
        if not result.corrections_made:
            return 1.0  # No corrections needed = high confidence
            
        # Lower confidence if many corrections relative to text length
        correction_ratio = result.corrections_made / max(len(result.processed_text.split()), 1)
        if correction_ratio > 0.5:
            return 0.6  # Many corrections = uncertain
        elif correction_ratio > 0.2:
            return 0.8  # Some corrections = medium confidence
        else:
            return 0.9  # Few corrections = high confidence
            
    def _assess_sacred_confidence(self, result: ProcessingResult) -> float:
        """Sacred content processing confidence."""
        if not result.metadata_enrichment.get('sacred_processing'):
            return 1.0  # No sacred content = not applicable
            
        # Check for sacred symbols preserved
        sacred_symbols = ['|', '||', '।', '।।', 'ॐ']
        text = result.processed_text
        
        if any(symbol in text for symbol in sacred_symbols):
            # Sacred symbols preserved = high confidence
            return 0.95
        elif result.content_classification.get('content_type') in ['mantra', 'verse']:
            # Sacred content but no symbols preserved = medium confidence
            return 0.7
        else:
            return 0.9
            
    def _generate_flags(self, lexicon_conf: float, sacred_conf: float, 
                       compound_conf: float, scripture_conf: float) -> List[str]:
        """Generate flags for low-confidence areas."""
        flags = []
        
        if lexicon_conf < 0.7:
            flags.append('uncertain_corrections')
        if sacred_conf < 0.8:
            flags.append('sacred_formatting_issues')
        if compound_conf < 0.7:
            flags.append('compound_term_uncertainty')
        if scripture_conf < 0.6:
            flags.append('scripture_reference_uncertain')
            
        return flags
```

### **Issue Detection System**
```python
# New: qa/issue_detector.py (~80 lines)
@dataclass
class QualityIssue:
    issue_type: str               # 'transcription', 'formatting', 'uncertainty'
    severity: str                 # 'critical', 'high', 'medium', 'low'  
    description: str              # Human-readable issue description
    timestamp_start: str          # SRT timestamp where issue occurs
    timestamp_end: str            # End timestamp
    context_text: str             # Surrounding text for context
    suggested_action: str         # What reviewer should consider
    confidence: float             # How certain we are this is an issue

class QualityIssueDetector:
    """
    Lightweight issue detection for quality review.
    Focuses on common patterns that need human attention.
    """
    
    def __init__(self):
        # Common patterns that indicate potential issues
        self.transcription_patterns = [
            r'\b\w{15,}\b',           # Very long words (likely transcription errors)
            r'[A-Z]{5,}',             # Long sequences of caps
            r'\d{4,}',                # Long number sequences
            r'[.,!?]{3,}'             # Repeated punctuation
        ]
        
    def detect_issues(self, segment: SRTSegment, confidence: ConfidenceMetrics) -> List[QualityIssue]:
        """Find potential quality issues in processed segment."""
        issues = []
        
        # Low confidence = review needed
        if confidence.overall_confidence < 0.7:
            issues.append(QualityIssue(
                issue_type='uncertainty',
                severity='high' if confidence.overall_confidence < 0.5 else 'medium',
                description=f'Low processing confidence ({confidence.overall_confidence:.2f})',
                timestamp_start=segment.start_time,
                timestamp_end=segment.end_time,
                context_text=segment.text[:100] + '...' if len(segment.text) > 100 else segment.text,
                suggested_action='Manual review recommended',
                confidence=0.9
            ))
            
        # Potential transcription errors
        for pattern in self.transcription_patterns:
            if re.search(pattern, segment.text):
                issues.append(QualityIssue(
                    issue_type='transcription',
                    severity='medium',
                    description=f'Potential transcription error pattern detected',
                    timestamp_start=segment.start_time,
                    timestamp_end=segment.end_time,
                    context_text=segment.text,
                    suggested_action='Check for garbled text or misheard words',
                    confidence=0.7
                ))
                break
                
        return issues
```

### **JSON Export System**
```python
# Enhanced: cli.py (~50 lines addition)
class QualityReport:
    """Generate JSON quality reports for review platforms."""
    
    def __init__(self):
        self.version = "1.0"
        
    def generate_report(self, filename: str, segments: List[SRTSegment], 
                       confidence_scores: List[ConfidenceMetrics],
                       quality_issues: List[QualityIssue]) -> dict:
        """Generate comprehensive quality report."""
        
        # Overall statistics
        total_segments = len(segments)
        high_confidence = sum(1 for c in confidence_scores if c.overall_confidence > 0.9)
        medium_confidence = sum(1 for c in confidence_scores if 0.7 <= c.overall_confidence <= 0.9)
        low_confidence = sum(1 for c in confidence_scores if c.overall_confidence < 0.7)
        
        # Issue statistics
        critical_issues = sum(1 for i in quality_issues if i.severity == 'critical')
        high_issues = sum(1 for i in quality_issues if i.severity == 'high')
        
        report = {
            "metadata": {
                "filename": filename,
                "processed_at": datetime.now().isoformat(),
                "processor_version": self.version,
                "total_segments": total_segments
            },
            "quality_summary": {
                "high_confidence_segments": high_confidence,
                "medium_confidence_segments": medium_confidence, 
                "low_confidence_segments": low_confidence,
                "critical_issues": critical_issues,
                "high_priority_issues": high_issues,
                "review_recommended_segments": low_confidence + critical_issues + high_issues
            },
            "segment_details": [
                {
                    "segment_number": i + 1,
                    "timestamp": f"{seg.start_time} --> {seg.end_time}",
                    "confidence": {
                        "overall": conf.overall_confidence,
                        "lexicon": conf.lexicon_confidence,
                        "sacred": conf.sacred_confidence,
                        "compound": conf.compound_confidence,
                        "scripture": conf.scripture_confidence
                    },
                    "flags": conf.processing_flags,
                    "issues": [
                        {
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "description": issue.description,
                            "suggested_action": issue.suggested_action
                        }
                        for issue in quality_issues 
                        if issue.timestamp_start == seg.start_time
                    ]
                }
                for i, (seg, conf) in enumerate(zip(segments, confidence_scores))
                if conf.overall_confidence < 0.9 or any(
                    issue.timestamp_start == seg.start_time for issue in quality_issues
                )
            ]
        }
        
        return report
```

### **Integration with Main Processing**
```python
# Enhanced: sanskrit_processor_v2.py (~30 lines addition)
class SanskritProcessor:
    def __init__(self, lexicon_dir: Path, config: dict = None):
        # Add QA components
        self.confidence_scorer = ConfidenceScorer(config)
        self.issue_detector = QualityIssueDetector()
        self.qa_enabled = config.get('qa', {}).get('enabled', False)
        
    def process_srt_with_qa(self, srt_content: str) -> tuple[str, dict]:
        """Process SRT with quality assurance reporting."""
        segments = self.srt_parser.parse(srt_content)
        processed_segments = []
        confidence_scores = []
        all_issues = []
        
        for segment in segments:
            # Process segment with context-aware pipeline
            result = self.pipeline.process_segment(segment.text)
            
            # Generate confidence metrics
            if self.qa_enabled:
                confidence = self.confidence_scorer.calculate_confidence(result)
                issues = self.issue_detector.detect_issues(segment, confidence)
                
                confidence_scores.append(confidence)
                all_issues.extend(issues)
            
            # Create processed segment
            processed_segments.append(SRTSegment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=result.processed_text
            ))
        
        # Generate SRT output
        output_srt = self.srt_parser.generate_srt(processed_segments)
        
        # Generate quality report
        qa_report = None
        if self.qa_enabled:
            reporter = QualityReport()
            qa_report = reporter.generate_report(
                "processed_file", segments, confidence_scores, all_issues
            )
        
        return output_srt, qa_report
```

## 📁 Files to Create/Modify

### **New Files:**
- `qa/confidence_scorer.py` - Confidence scoring system (~120 lines)
- `qa/issue_detector.py` - Issue detection and flagging (~80 lines)

### **Modified Files:**
- `sanskrit_processor_v2.py` - QA integration (~30 lines addition)
- `cli.py` - JSON report output option (~50 lines addition)

**Total New Code**: ~200 lines (within limit)

## 📊 Success Metrics

### **Quality Assurance**
- **Confidence Accuracy**: 85%+ correlation with manual quality assessment
- **Issue Detection**: 90%+ recall for segments needing review
- **False Positive Rate**: <15% for quality flags
- **Review Efficiency**: 60%+ reduction in manual review time

### **Performance Requirements**
- **QA Overhead**: <10ms per segment
- **Memory Usage**: <5MB additional footprint
- **JSON Export**: <100ms for typical file
- **Processing Speed**: Maintain >1,500 segments/second with QA enabled

### **Integration Success**
- **JSON Compatibility**: Valid JSON format for all review platforms
- **Timestamp Accuracy**: Perfect alignment with SRT timestamps
- **Priority Correlation**: High-priority flags correlate with actual issues
- **Batch Processing**: Quality reports for entire folder processing

## 🔧 Technical Specifications

### **Confidence Scoring Algorithm**
```python
def calculate_overall_confidence(components: dict) -> float:
    """
    Weighted confidence scoring:
    - Lexicon confidence: 40% (most critical for accuracy)
    - Sacred content: 20% (important for cultural respect)
    - Compound terms: 20% (affects professionalism)  
    - Scripture refs: 20% (adds scholarly value)
    """
    weights = {'lexicon': 0.4, 'sacred': 0.2, 'compound': 0.2, 'scripture': 0.2}
    
    weighted_sum = sum(
        components[component] * weight 
        for component, weight in weights.items()
    )
    
    # Apply confidence boost for high agreement across components
    variance = np.var(list(components.values()))
    if variance < 0.1:  # Components agree strongly
        weighted_sum = min(1.0, weighted_sum * 1.1)
    
    return weighted_sum
```

### **JSON Report Structure**
```json
{
  "metadata": {
    "filename": "lecture_001.srt",
    "processed_at": "2025-01-15T10:30:00Z",
    "total_segments": 1250
  },
  "quality_summary": {
    "high_confidence_segments": 1150,
    "medium_confidence_segments": 80,
    "low_confidence_segments": 20,
    "review_recommended_segments": 35
  },
  "segment_details": [
    {
      "segment_number": 45,
      "timestamp": "00:02:15,000 --> 00:02:18,500",
      "confidence": {
        "overall": 0.65,
        "lexicon": 0.7,
        "sacred": 0.9,
        "compound": 0.4
      },
      "flags": ["compound_term_uncertainty"],
      "issues": [
        {
          "type": "uncertainty", 
          "severity": "medium",
          "description": "Low compound term confidence",
          "suggested_action": "Verify proper noun capitalization"
        }
      ]
    }
  ]
}
```

## 🧪 Test Cases

### **Confidence Scoring Tests**
```python
def test_confidence_calculation():
    scorer = ConfidenceScorer(config)
    
    # High confidence case
    high_confidence_result = ProcessingResult(
        corrections_made=2, segments_processed=1, 
        processing_time=0.1, content_classification={'content_type': 'regular'}
    )
    confidence = scorer.calculate_confidence(high_confidence_result)
    assert confidence.overall_confidence > 0.8
    
    # Low confidence case with many corrections
    low_confidence_result = ProcessingResult(
        corrections_made=20, segments_processed=1,
        processing_time=0.5, content_classification={'content_type': 'uncertain'}
    )
    confidence = scorer.calculate_confidence(low_confidence_result)
    assert confidence.overall_confidence < 0.7
    assert 'uncertain_corrections' in confidence.processing_flags
```

### **Issue Detection Tests**
```python
def test_issue_detection():
    detector = QualityIssueDetector()
    
    # Test transcription error pattern
    problematic_segment = SRTSegment(
        start_time="00:01:00,000",
        end_time="00:01:05,000", 
        text="This is a verylongwordthatisprobablyatranscriptionerror here"
    )
    
    low_confidence = ConfidenceMetrics(
        lexicon_confidence=0.6, sacred_confidence=0.9,
        compound_confidence=0.8, scripture_confidence=0.9,
        overall_confidence=0.65, processing_flags=[]
    )
    
    issues = detector.detect_issues(problematic_segment, low_confidence)
    assert len(issues) >= 1
    assert any(issue.issue_type == 'transcription' for issue in issues)
    assert any(issue.issue_type == 'uncertainty' for issue in issues)
```

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **False Positive Flags** | Medium | Conservative thresholds, extensive testing |
| **Performance Impact** | Medium | Lightweight scoring, optional QA mode |
| **JSON Size Growth** | Low | Only include flagged segments in detail |
| **Confidence Accuracy** | High | Validate against manual review samples |

## 🔄 Story Progress Tracking

- [ ] **Started**: QA framework implementation begun
- [ ] **Confidence Scorer**: Component confidence calculation working
- [ ] **Issue Detection**: Quality issue flagging implemented
- [ ] **JSON Export**: Report generation and export complete
- [ ] **Integration**: Works with context-aware processing pipeline
- [ ] **Performance Validated**: Meets speed/memory requirements
- [ ] **Testing Complete**: All QA test cases pass
- [ ] **Quality Improvement**: Effective prioritization for manual review

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Why This Approach is Lean:**
1. **Simple Metrics**: Rule-based confidence, no complex ML models
2. **Optional System**: Can be disabled for performance-critical use
3. **Focused Scope**: Only flags clear quality concerns
4. **Minimal Overhead**: <10ms per segment processing time
5. **Standard Output**: JSON format, no custom reporting systems

#### **Integration Strategy:**
- **Confidence Pipeline**: Confidence flows through existing processing
- **Optional QA**: System works with or without QA enabled
- **JSON Export**: Clean separation of processing and reporting
- **Review Platform Ready**: Standard JSON format for integration

### **Success Criteria for Story Completion:**
1. ✅ **Confidence Scoring**: Accurate quality confidence per segment
2. ✅ **Issue Flagging**: JSON output without marking final SRT
3. ✅ **Review Integration**: Timestamp mapping for review platforms  
4. ✅ **Performance Maintained**: <10ms QA overhead per segment
5. ✅ **Lean Compliance**: <200 lines, simple rule-based approach

**Story Definition of Done**: Quality assurance system provides automated confidence scoring and issue flagging in JSON format for integration with review platforms while maintaining lean architecture.

---

## 🤖 Dev Agent Instructions

**IMPLEMENTATION PRIORITY**: This story enables efficient human-in-the-loop review for 11k hours of content by automatically identifying segments needing attention.

**LEAN IMPLEMENTATION APPROACH**:
1. Start with simple rule-based confidence scoring
2. Implement lightweight issue detection patterns  
3. Add clean JSON export functionality
4. Test with realistic content samples
5. Validate correlation with manual quality assessment

**CRITICAL SUCCESS FACTORS**:
- Must provide JSON flagging without marking final output
- Must integrate seamlessly with context-aware processing
- Must maintain processing performance (<10ms overhead)
- Must stay within 200-line code budget
- Must enable efficient human review prioritization

**Story Status**: ⏳ Ready for Implementation