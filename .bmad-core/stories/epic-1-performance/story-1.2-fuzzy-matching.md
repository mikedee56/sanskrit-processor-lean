# Story 1.2: Simple Fuzzy Matching

**Epic**: Performance & Reliability  
**Story Points**: 3  
**Priority**: High  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** text processor  
**I want** basic similarity matching for terms  
**So that** minor spelling variations are caught without heavy dependencies

## 🎯 Business Value

- **Accuracy**: Catch common misspellings and variations
- **Coverage**: Handle ASR transcription errors  
- **Performance**: Lightweight implementation without external libraries
- **Maintainability**: Simple algorithm easy to understand and modify

## ✅ Acceptance Criteria

### **AC 1: Character Similarity Algorithm**
- [ ] Implement character-based similarity function (no fuzzywuzzy dependency)
- [ ] Calculate similarity ratio between two strings
- [ ] Handle case-insensitive comparisons
- [ ] Configurable similarity threshold (default: 0.8)
- [ ] Performance: < 1ms per comparison

### **AC 2: Lexicon Integration**
- [ ] Integrate with existing `_apply_lexicon_corrections` method
- [ ] Try exact match first, then fuzzy match if no exact match  
- [ ] Only apply fuzzy match if similarity > threshold
- [ ] Track fuzzy matches separately in corrections count
- [ ] Maintain existing lexicon structure compatibility

### **AC 3: Common Variations Handling**
- [ ] Handle character substitutions: "krishna" ↔ "krsna"  
- [ ] Handle missing characters: "dharma" ↔ "dhrma"
- [ ] Handle extra characters: "yoga" ↔ "yogaa"  
- [ ] Handle phonetic variations: "shiva" ↔ "siva"
- [ ] Ignore punctuation in comparisons

### **AC 4: Performance Optimization** 
- [ ] Short-circuit for very different length strings
- [ ] Early termination for low similarity scores
- [ ] Efficient string comparison without creating multiple copies
- [ ] Memory usage < 1KB per comparison
- [ ] Benchmark: 10,000 comparisons in < 100ms

### **AC 5: Configuration & Tuning**
- [ ] Configurable threshold in config.yaml  
- [ ] Option to disable fuzzy matching entirely
- [ ] Logging of fuzzy matches for tuning
- [ ] Statistics on fuzzy match hit rates

## 🏗️ Implementation Plan

### **Phase 1: Core Algorithm (45 minutes)**
```python
def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate character-based similarity ratio.
    Uses simple character matching without external dependencies.
    """
    # Normalize strings (lowercase, strip)
    # Handle length differences  
    # Count matching characters in positions
    # Return ratio 0.0 - 1.0
```

### **Phase 2: Lexicon Integration (30 minutes)**
```python
def _apply_fuzzy_corrections(self, text: str) -> tuple[str, int]:
    """Apply fuzzy matching to uncorrected words."""
    # Split into words
    # For each word not in exact lexicon:
    #   Try fuzzy match against all terms
    #   Apply best match if above threshold
```

### **Phase 3: Configuration (15 minutes)**
```yaml
# Add to config.yaml
processing:
  fuzzy_matching:
    enabled: true
    threshold: 0.8
    log_matches: false
```

### **Phase 4: Testing & Optimization (30 minutes)**
```python
# Unit tests for similarity algorithm
# Performance benchmarking  
# Integration testing with real SRT content
```

## 📁 Files to Create/Modify

### **Modified Files:**
- `sanskrit_processor_v2.py` - Add similarity method and integration
- `config.yaml` - Add fuzzy matching configuration
- `README.md` - Document fuzzy matching feature

### **New Files:**
- `tests/test_fuzzy_matching.py` - Unit tests

## 🔧 Technical Specifications

### **Algorithm Choice: Character Position Matching**
```python
def calculate_similarity(str1: str, str2: str) -> float:
    """
    Simple character similarity without external dependencies.
    Based on character position matching with length normalization.
    """
    if not str1 or not str2:
        return 0.0
    
    # Quick length check - very different lengths = low similarity
    len_diff = abs(len(str1) - len(str2))
    max_len = max(len(str1), len(str2))
    if len_diff / max_len > 0.5:  # More than 50% length difference
        return 0.0
    
    # Normalize
    s1, s2 = str1.lower().strip(), str2.lower().strip()
    
    # Count matching characters at same positions
    matches = sum(1 for i, (a, b) in enumerate(zip(s1, s2)) if a == b)
    
    # Add partial credit for similar length
    length_similarity = 1.0 - (len_diff / max_len)
    
    # Combine position matches with length similarity  
    position_similarity = matches / max_len
    
    return (position_similarity * 0.7) + (length_similarity * 0.3)
```

### **Integration Pattern:**
```python
def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
    """Enhanced with fuzzy matching fallback."""
    corrections = 0
    words = text.split()
    corrected_words = []
    
    for word in words:
        clean_word = re.sub(r'[^\w\s]', '', word.lower())
        
        # Try exact match first (existing logic)
        if clean_word in self.lexicons.corrections:
            # ... existing exact match logic
        
        # Try fuzzy match if enabled and no exact match
        elif self.config.get('processing', {}).get('fuzzy_matching', {}).get('enabled', False):
            best_match = self._find_fuzzy_match(clean_word)
            if best_match:
                corrected_words.append(best_match)
                corrections += 1
                logger.debug(f"Fuzzy correction: {word} -> {best_match}")
            else:
                corrected_words.append(word)
        else:
            corrected_words.append(word)
    
    return ' '.join(corrected_words), corrections
```

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_similarity_calculation():
    assert calculate_similarity("krishna", "krsna") > 0.8
    assert calculate_similarity("dharma", "dhrma") > 0.8  
    assert calculate_similarity("yoga", "yogaa") > 0.8
    assert calculate_similarity("hello", "world") < 0.3
    
def test_fuzzy_lexicon_matching():
    processor = SanskritProcessor()
    # Test with intentional misspellings
    result, corrections = processor._apply_fuzzy_corrections("I study dhrma and krsna")
    assert "dharma" in result
    assert "krishna" in result
    assert corrections == 2

def test_performance():
    start = time.time()
    for i in range(10000):
        calculate_similarity("dharma", "dhrma")
    duration = time.time() - start
    assert duration < 0.1  # 10,000 comparisons in < 100ms
```

### **Integration Tests:**
```python
def test_srt_processing_with_fuzzy():
    # Create SRT with common misspellings
    srt_content = """
    1
    00:00:01,000 --> 00:00:03,000
    Welcome to this bhagvad gita lecture on dhrma
    """
    # Process and verify corrections
```

## 📊 Success Metrics

- **Accuracy Improvement**: Catch 80% more spelling variations
- **Performance**: < 1ms per word comparison
- **Memory Efficiency**: < 1KB per comparison
- **Coverage**: Handle all common ASR transcription errors
- **Integration**: Zero breaking changes to existing API

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives | Medium | Tune threshold, log matches for review |
| Performance degradation | High | Benchmark every change, optimize algorithm |
| Algorithm complexity | Low | Keep implementation simple, well-commented |
| Over-correction | Medium | Exact match first, fuzzy only as fallback |

## 🔄 Story Progress Tracking  

- [ ] **Started**: Implementation begun
- [ ] **Algorithm**: Character similarity function implemented
- [ ] **Integration**: Lexicon correction enhanced with fuzzy matching
- [ ] **Configuration**: Config options added  
- [ ] **Testing**: Unit tests passing
- [ ] **Performance**: Benchmarks meet requirements
- [ ] **Documentation**: Usage examples added
- [ ] **Edge Cases**: Handled all common variations

## 📝 Implementation Notes

### **Why Not Use fuzzywuzzy/Levenshtein?**
- Adds external dependency (against lean architecture)
- Overkill for our simple use case
- Our character-position algorithm is sufficient for ASR variations
- Easier to understand and modify

### **Algorithm Trade-offs:**
- **Chosen**: Character position matching
  - ✅ Simple, fast, no dependencies
  - ✅ Good for ASR-style errors (missing/extra chars)
  - ❌ Less sophisticated than edit distance

- **Rejected**: Levenshtein distance  
  - ✅ More accurate for complex variations
  - ❌ Requires external library or complex implementation
  - ❌ Slower performance

### **Threshold Tuning:**
- Start with 0.8 (80% similarity)
- Monitor false positives/negatives
- May need term-specific thresholds

---

**Dependencies**: None (Story 1.1 can run in parallel)  
**Estimated completion**: Day 2 of sprint