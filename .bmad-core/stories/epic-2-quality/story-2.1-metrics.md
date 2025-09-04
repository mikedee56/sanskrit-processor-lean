# Story 2.1: Enhanced Processing Metrics

**Epic**: Quality & Monitoring  
**Story Points**: 3  
**Priority**: Medium  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** quality analyst  
**I want** detailed correction statistics and processing metrics  
**So that** processing quality can be measured, tracked, and improved over time

## 🎯 Business Value

- **Quality Assurance**: Track correction types and success rates
- **Performance Monitoring**: Identify processing bottlenecks
- **Continuous Improvement**: Data-driven optimization decisions
- **User Confidence**: Transparent quality metrics build trust
- **Debugging**: Detailed metrics help diagnose issues

## ✅ Acceptance Criteria

### **AC 1: Detailed Correction Tracking**
- [ ] Track corrections by type: lexicon, capitalization, fuzzy, punctuation
- [ ] Record confidence scores for each correction (0.0 - 1.0)
- [ ] Count successful vs failed correction attempts  
- [ ] Track processing time per correction type
- [ ] Maintain backward compatibility with existing `ProcessingResult`

### **AC 2: Processing Performance Metrics**
- [ ] Measure segments per second processing rate
- [ ] Track memory usage during processing
- [ ] Record file processing times (parse, process, write phases)
- [ ] Calculate correction density (corrections per segment)
- [ ] Monitor error rates and types

### **AC 3: Quality Scoring System**
- [ ] Overall quality score (0-100) based on multiple factors
- [ ] Confidence distribution analysis  
- [ ] Error rate calculation
- [ ] Coverage metrics (% of text processed vs skipped)
- [ ] Improvement tracking over time

### **AC 4: Detailed Reporting**
- [ ] Summary report after each processing run
- [ ] Exportable metrics in JSON format
- [ ] Human-readable processing summary  
- [ ] Historical trend tracking (optional file-based storage)
- [ ] Comparison between processing runs

### **AC 5: CLI Integration** 
- [ ] Verbose mode shows detailed metrics
- [ ] `--metrics-only` flag for analysis without processing
- [ ] `--export-metrics` flag for JSON output
- [ ] Progress reporting for large files
- [ ] Color-coded output for quick quality assessment

## 🏗️ Implementation Plan

### **Phase 1: Enhanced Data Structures (45 minutes)**
```python
@dataclass
class CorrectionDetail:
    type: str  # 'lexicon', 'capitalization', 'fuzzy', 'punctuation'
    original: str
    corrected: str 
    confidence: float
    processing_time: float

@dataclass  
class DetailedProcessingResult:
    # Existing fields for compatibility
    segments_processed: int
    corrections_made: int
    processing_time: float
    errors: List[str]
    
    # New detailed fields
    corrections_by_type: Dict[str, int]
    correction_details: List[CorrectionDetail]
    confidence_scores: List[float]
    processing_phases: Dict[str, float]  # parse, process, write times
    quality_score: float
    memory_usage: Dict[str, float]  # peak, average
```

### **Phase 2: Metrics Collection (30 minutes)**
```python
class MetricsCollector:
    def start_correction(self, type: str, original: str):
        # Start timing for correction
        
    def end_correction(self, corrected: str, confidence: float):
        # Record completed correction with timing
        
    def calculate_quality_score(self) -> float:
        # Weighted score based on:
        # - Correction success rate
        # - Average confidence  
        # - Error rate
        # - Coverage percentage
```

### **Phase 3: Integration (30 minutes)**
```python
# Modify SanskritProcessor to collect detailed metrics
# Update each correction method to record metrics
# Enhance ProcessingResult with new fields
```

### **Phase 4: Reporting (45 minutes)**
```python
class ProcessingReporter:
    def generate_summary(self, result: DetailedProcessingResult) -> str:
        # Human-readable summary
        
    def export_json(self, result: DetailedProcessingResult) -> dict:
        # Machine-readable export
        
    def compare_runs(self, results: List[DetailedProcessingResult]) -> str:
        # Trend analysis
```

## 📁 Files to Create/Modify

### **Modified Files:**
- `sanskrit_processor_v2.py` - Add metrics collection throughout
- `simple_cli.py` - Add metrics display options
- `enhanced_cli.py` - Add detailed metrics and export options

### **New Files:**
- `services/metrics_collector.py` - Metrics collection logic
- `services/processing_reporter.py` - Report generation
- `tests/test_metrics.py` - Unit tests

## 🔧 Technical Specifications

### **Quality Score Calculation:**
```python
def calculate_quality_score(self) -> float:
    """
    Calculate overall quality score (0-100) based on:
    - Correction success rate (40%)
    - Average confidence (30%) 
    - Error rate penalty (20%)
    - Coverage completeness (10%)
    """
    success_rate = successful_corrections / total_attempts
    avg_confidence = sum(confidence_scores) / len(confidence_scores)
    error_penalty = max(0, 1 - (error_count / total_segments))
    coverage = processed_segments / total_segments
    
    score = (success_rate * 0.4 + 
            avg_confidence * 0.3 + 
            error_penalty * 0.2 + 
            coverage * 0.1) * 100
            
    return min(100, max(0, score))
```

### **Memory Monitoring:**
```python
import tracemalloc
import psutil

def monitor_memory():
    # Track Python memory usage with tracemalloc
    # Track system memory with psutil
    # Record peak and average usage
```

### **CLI Output Formats:**

#### **Summary Mode (Default):**
```
✅ Processing Complete!

📊 Results Summary:
   • Segments processed: 156 
   • Corrections made: 23 (14.7% of segments)
   • Processing time: 2.3s (2,608 segments/sec)
   • Quality score: 87/100

🔧 Correction Breakdown:
   • Lexicon corrections: 15 (65%)
   • Capitalization fixes: 6 (26%) 
   • Fuzzy matches: 2 (9%)
   
💡 Average confidence: 0.89 (High)
```

#### **Verbose Mode (`--verbose`):**
```
📈 Detailed Processing Metrics:

⏱️  Performance:
   • Parsing phase: 0.1s
   • Processing phase: 2.0s  
   • Writing phase: 0.2s
   • Total time: 2.3s (2,608 segments/sec)

🧠 Memory Usage:
   • Peak memory: 12.3 MB
   • Average memory: 8.7 MB

🎯 Quality Analysis:
   • Quality score: 87/100
   • Correction success rate: 95.8%
   • Average confidence: 0.89
   • Error rate: 0.6%
   • Coverage: 100%

📋 Correction Details:
   [23:45] dharma -> dharma (lexicon, confidence: 1.0, 0.2ms)
   [45:67] krishna -> Krishna (capitalization, confidence: 1.0, 0.1ms)  
   [89:12] bhagvad -> Bhagavad (fuzzy, confidence: 0.85, 1.2ms)
```

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_metrics_collection():
    collector = MetricsCollector()
    collector.start_correction('lexicon', 'dharma')
    collector.end_correction('dharma', 1.0)
    
    assert len(collector.correction_details) == 1
    assert collector.corrections_by_type['lexicon'] == 1

def test_quality_score_calculation():
    result = create_test_result()
    assert 0 <= result.quality_score <= 100
    assert result.quality_score == 87  # Expected for test data

def test_report_generation():
    result = create_test_result()
    reporter = ProcessingReporter()
    summary = reporter.generate_summary(result)
    
    assert "Quality score: 87/100" in summary
    assert "Corrections made: 23" in summary
```

### **Integration Tests:**
```python
def test_cli_metrics_output():
    # Test --verbose flag shows detailed metrics
    # Test --export-metrics creates JSON file
    # Test metrics accuracy with known input
```

## 📊 Success Metrics

- **Data Coverage**: 100% of processing operations tracked
- **Performance Impact**: < 5% processing time overhead
- **Memory Overhead**: < 2MB additional memory usage
- **Report Accuracy**: ±1% accuracy in all reported metrics
- **User Experience**: Clear, actionable insights in < 5 seconds

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance overhead | Medium | Minimize metrics collection overhead, optional detailed tracking |
| Memory bloat | Medium | Efficient data structures, optional detail storage |
| Report complexity | Low | Tiered reporting (summary/detailed), clear formatting |
| Backward compatibility | High | Extend existing classes, don't break current API |

## 🔄 Story Progress Tracking

- [ ] **Started**: Implementation begun  
- [ ] **Data Structures**: Enhanced ProcessingResult and CorrectionDetail created
- [ ] **Collection**: Metrics gathering integrated throughout processor
- [ ] **Quality Scoring**: Quality score algorithm implemented
- [ ] **Reporting**: Human and machine-readable reports working
- [ ] **CLI Integration**: All command-line options functional  
- [ ] **Testing**: Comprehensive test coverage
- [ ] **Performance**: Overhead within acceptable limits

## 📝 Implementation Notes

### **Design Principles:**
- **Backward Compatibility**: Existing code continues to work unchanged
- **Optional Overhead**: Detailed metrics only collected when requested  
- **Clear Insights**: Reports provide actionable information
- **Performance First**: Metrics don't slow down processing

### **Future Enhancements:**
- Historical trending (file-based storage)
- Web dashboard for visualization
- Automated quality alerts
- Comparative analysis between files
- Export to common formats (CSV, Excel)

### **Configuration Options:**
```yaml
metrics:
  collect_detailed: true
  track_memory: true  
  export_format: "json"
  historical_storage: false
```

---

**Dependencies**: None (can run independently)  
**Estimated completion**: Day 3 of sprint