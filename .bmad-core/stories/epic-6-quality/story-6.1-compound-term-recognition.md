# Story 6.1: Compound Term Recognition System

**Epic**: Sanskrit Content Quality Excellence  
**Story Points**: 8  
**Priority**: High  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **CRITICAL QUALITY ISSUE**: Fixes title capitalization failures identified in processing analysis

## 📋 User Story

**As a** Sanskrit content processor handling scriptural texts  
**I want** intelligent recognition of compound Sanskrit terms and titles  
**So that** "Srimad Bhagavad Gita" becomes "Śrīmad Bhagavad Gītā" instead of "Srimad bhagavad gita"

## 🔥 **Problem Being Solved**

### **Current Failure Pattern:**
```text
INPUT:  "Srimad Bhagavad Gita, chapter 2, verse number 56"
OUTPUT: "Srimad bhagavad gita, prakaraṇa 2 verse, number. 56" ❌ WRONG!
SHOULD: "Śrīmad Bhagavad Gītā, adhyāya 2, śloka 56" ✅ CORRECT
```

### **Root Cause Analysis:**
1. **Fragment Processing**: Terms processed individually, not as compound titles
2. **Context Ignorance**: "The Bhagavad Gita" vs "a bhagavad gita" treated identically  
3. **Missing Compound Entries**: Lexicon has "Bhagavad Gita" but not "Srimad Bhagavad Gita"
4. **Case Context Loss**: Title case vs sentence case not distinguished

## 🎯 Business Value

- **Professional Output**: Proper Sanskrit title formatting for 11k hours of content
- **Academic Compliance**: Correct IAST transliteration for scholarly use
- **Brand Quality**: YouTube, books, apps show proper respect for sacred texts
- **Automation Value**: Reduce manual correction of 1000s of title references

## ✅ Acceptance Criteria

### **AC 1: Compound Title Recognition**
- [ ] **Detect Multi-Word Titles**: Recognize "Śrīmad Bhagavad Gītā" as single semantic unit
- [ ] **Context-Aware Matching**: "The Bhagavad Gita" (title) vs "a bhagavad gita" (reference)
- [ ] **Prefix Handling**: "Śrīmad", "Śrī", "Mahā" prefixes properly integrated
- [ ] **Academic Variations**: Handle "Srimad", "Shrimad", "Shreemad" variations

### **AC 2: Title Case Intelligence**
- [ ] **Definitive Articles**: "The Bhagavad Gītā" capitalized as title reference
- [ ] **Sentence Context**: "He read the bhagavad gītā" (casual reference, different handling)
- [ ] **Beginning of Sentence**: Always capitalize regardless of context
- [ ] **Chapter/Verse Context**: "Bhagavad Gītā 2.56" formatted as citation

### **AC 3: Compound Term Expansion**
- [ ] **Scripture Titles**: Bhagavad Gītā, Yoga Vāsiṣṭha, Viveka Cūḍāmaṇi, etc.
- [ ] **Philosophical Concepts**: Advaita Vedānta, Sāṅkhya Yoga, Karma Yoga, etc.  
- [ ] **Deity Compound Names**: Śrī Kṛṣṇa, Bhagavān Rāma, Śiva Śaṅkara, etc.
- [ ] **Teacher Names**: Ādi Śaṅkara, Rāmana Maharṣi, Swami Chinmayananda, etc.

### **AC 4: Lean Implementation Requirements**
- [ ] **Code Limit**: Maximum 150 lines for entire compound recognition system
- [ ] **No New Dependencies**: Use only existing stdlib + PyYAML + requests
- [ ] **Performance**: Maintain >1,500 segments/second processing speed
- [ ] **Memory**: Add <10MB to memory footprint
- [ ] **Backward Compatible**: All existing functionality preserved

## 🏗️ Implementation Plan

### **Phase 1: Compound Term Database (Day 1-2)**

#### **Enhanced Lexicon Structure**
```python
# Enhanced lexicon entries in YAML:
compound_terms:
  - phrase: "Śrīmad Bhagavad Gītā"
    variations: 
      - "srimad bhagavad gita"
      - "shrimad bhagavad geeta"  
      - "shreemad bhagwad gita"
    components: ["śrīmad", "bhagavad gītā"] 
    type: "scriptural_title"
    context_clues: ["chapter", "verse", "adhyaya", "sloka"]
    
  - phrase: "Advaita Vedānta" 
    variations:
      - "advaita vedanta"
      - "advait vedant"
      - "non-dual vedanta"
    type: "philosophical_system"
    context_clues: ["philosophy", "school", "tradition"]
```

#### **Compound Matcher Implementation**  
```python
# New: processors/compound_matcher.py (~80 lines)
class CompoundTermMatcher:
    """
    Intelligent compound term recognition with context awareness.
    Maintains lean architecture with focused functionality.
    """
    
    def __init__(self, lexicon_path: Path):
        self.compounds = self._load_compounds(lexicon_path)
        self.phrase_patterns = self._build_patterns()
    
    def process_text(self, text: str) -> tuple[str, list]:
        """
        Main processing with compound term recognition.
        Returns (corrected_text, corrections_made).
        """
        # Multi-pass processing:
        # 1. Identify compound term boundaries
        # 2. Apply context-aware matching  
        # 3. Preserve surrounding text structure
        pass
        
    def _detect_title_context(self, text: str, match_pos: int) -> str:
        """Determine if match is title, reference, or casual mention."""
        pass
```

### **Phase 2: Context Detection Engine (Day 3-4)**

#### **Context Classification**
```python
# Enhanced: processors/context_classifier.py (~70 lines)  
class ContextClassifier:
    """Simple context detection for compound term processing."""
    
    TITLE_INDICATORS = ["the", "chapter", "verse", "adhyaya", "sloka"]
    CASUAL_INDICATORS = ["a", "some", "read", "study", "practice"]
    
    def classify_context(self, text: str, term_position: int) -> str:
        """
        Returns: 'title', 'reference', 'casual', 'citation'
        """
        # Simple rule-based classification
        # Look at surrounding 5 words for context clues
        pass
```

### **Phase 3: Integration & Testing (Day 5)**

#### **Integration with Existing Processor**
```python
# Modified: sanskrit_processor_v2.py (add ~30 lines)
class SanskritProcessor:
    def __init__(self, lexicon_dir: Path, config: dict = None):
        # Add compound matcher to existing initialization
        self.compound_matcher = CompoundTermMatcher(lexicon_dir / "compounds.yaml")
        
    def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
        # Add compound processing before individual term processing
        # 1. First pass: Compound terms (preserve semantic units)
        # 2. Second pass: Individual terms (existing logic)
        pass
```

## 📁 Files to Create/Modify

### **New Files:**
- `lexicons/compounds.yaml` - Compound term database (~50 entries initially)
- `processors/compound_matcher.py` - Core compound recognition logic (~80 lines)
- `processors/context_classifier.py` - Simple context detection (~70 lines)

### **Modified Files:**
- `sanskrit_processor_v2.py` - Integration with existing processor (~30 additional lines)
- `config.yaml` - Add compound processing configuration options

### **Code Budget:**
- **Total New Code**: ~150 lines (within story limit)
- **Modified Code**: ~30 lines (minimal changes to core)
- **Data Files**: Compound lexicon entries (not counted toward code limit)

## 🔧 Technical Specifications

### **Compound Recognition Algorithm**
```python
def recognize_compounds(text: str) -> list[CompoundMatch]:
    """
    Lean compound recognition algorithm:
    1. Tokenize text into potential phrase boundaries
    2. Match against compound database (longest first)
    3. Apply context classification to matches
    4. Return prioritized correction candidates
    """
    
    # Phase 1: Sliding window matching (2-5 word phrases)
    phrases = extract_candidate_phrases(text, max_words=5)
    
    # Phase 2: Database matching with fuzzy tolerance
    matches = []
    for phrase in phrases:
        if compound_match := self.fuzzy_match_compound(phrase):
            context = self.classify_context(text, phrase.position)
            matches.append(CompoundMatch(phrase, compound_match, context))
    
    # Phase 3: Prioritization and conflict resolution
    return resolve_overlapping_matches(matches)
```

### **Context-Aware Capitalization Rules**
```python
CAPITALIZATION_RULES = {
    'title': lambda term: term.title(),           # "Śrīmad Bhagavad Gītā"  
    'reference': lambda term: term.title(),       # "The Bhagavad Gītā"
    'casual': lambda term: term.lower(),          # "the bhagavad gītā"  
    'citation': lambda term: term.title(),        # "Bhagavad Gītā 2.56"
    'sentence_start': lambda term: term.title()   # Always capitalize
}
```

## 🧪 Test Cases

### **Critical Test Cases**
```python
def test_compound_title_recognition():
    processor = CompoundMatcher("lexicons/compounds.yaml")
    
    # Test Case 1: Title context
    input_text = "Srimad Bhagavad Gita chapter 2 verse 56"
    expected = "Śrīmad Bhagavad Gītā adhyāya 2 śloka 56"
    result = processor.process_text(input_text)
    assert result[0] == expected
    
    # Test Case 2: Casual reference
    input_text = "He was reading the bhagavad gita yesterday"
    expected = "He was reading the Bhagavad Gītā yesterday"
    result = processor.process_text(input_text)
    assert result[0] == expected
    
    # Test Case 3: Definitive article
    input_text = "The Bhagavad Gita teaches us about dharma"
    expected = "The Bhagavad Gītā teaches us about dharma"  
    result = processor.process_text(input_text)
    assert result[0] == expected
```

### **Edge Cases**
```python
def test_compound_edge_cases():
    # Multiple compounds in same sentence
    # Compound term variations
    # Overlapping compound possibilities  
    # Punctuation preservation
    # Case sensitivity edge cases
    pass
```

## 📊 Success Metrics

### **Quality Improvements**
- **Title Accuracy**: 95%+ for compound scriptural titles (vs current ~60%)
- **Context Sensitivity**: 90%+ appropriate capitalization based on usage
- **Compound Recognition**: 95%+ for known multi-word terms
- **Variation Handling**: 90%+ for common misspellings/transliterations

### **Performance Requirements**
- **Processing Speed**: ≥1,500 segments/second (graceful degradation from 2,600+)
- **Memory Usage**: +8MB maximum (total <88MB vs current <80MB) 
- **Accuracy**: <5% false positive compound detections
- **Response Time**: <50ms additional processing per segment

### **Lean Compliance**
- **Code Size**: ≤150 lines total implementation
- **Dependencies**: Zero new external libraries
- **Configuration**: Simple YAML-based compound database
- **Integration**: Minimal changes to existing codebase

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Performance Degradation** | Medium | Profile each phase, optimize hotpaths |
| **False Positive Compounds** | Low | Conservative matching thresholds |
| **Context Classification Errors** | Medium | Rule-based approach with clear fallbacks |
| **Memory Usage Growth** | Low | Lazy loading of compound database |
| **Complexity Creep** | High | Strict 150-line limit enforcement |

## 🔄 Story Progress Tracking

- [ ] **Started**: Compound recognition implementation begun
- [ ] **Compound Database**: YAML lexicon with 50+ compound terms
- [ ] **Matcher Implementation**: Core recognition logic complete
- [ ] **Context Classification**: Simple context-aware processing
- [ ] **Integration Complete**: Works with existing processor
- [ ] **Performance Validated**: Meets speed/memory requirements  
- [ ] **Testing Complete**: All critical test cases pass
- [ ] **Quality Improvement**: Title accuracy >95% achieved

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Why This Approach is Lean:**
1. **Focused Problem**: Solves specific title capitalization issue
2. **Minimal Code**: 150 lines for entire system
3. **Simple Data**: YAML database, no complex schemas
4. **Rule-Based**: No ML/AI complexity, clear deterministic logic
5. **Incremental**: Builds on existing processor without major changes

#### **Performance Considerations:**
- **Sliding Window**: Efficient phrase boundary detection
- **Lazy Loading**: Load compound database only when needed  
- **Cache-Friendly**: Work with existing smart caching system
- **Memory-Conscious**: Reuse existing data structures

#### **Integration Strategy:**
- **Pre-Processing Step**: Run before individual term corrections
- **Fallback Graceful**: If compound matching fails, fall back to existing logic
- **Config-Driven**: Can be enabled/disabled via configuration
- **Test-Driven**: Extensive test suite for quality validation

### **Success Criteria for Story Completion:**
1. ✅ **Critical Problem Solved**: "Srimad Bhagavad Gita" → "Śrīmad Bhagavad Gītā"
2. ✅ **Context Awareness**: Title vs casual references handled appropriately
3. ✅ **Lean Compliance**: <150 lines, no new dependencies, >1,500 seg/sec
4. ✅ **Quality Improvement**: >95% accuracy for compound scriptural titles
5. ✅ **Backward Compatible**: All existing functionality preserved

**Story Definition of Done**: The critical compound term quality issue is resolved while maintaining lean architecture principles and performance requirements.

---

## 🤖 Dev Agent Instructions

**IMPLEMENTATION PRIORITY**: This story addresses the most visible quality failure in our processing analysis - improper title capitalization that makes the output look unprofessional.

**LEAN IMPLEMENTATION APPROACH**:
1. Start with minimal compound database (20-30 most common titles)
2. Implement simple rule-based matching (no complex algorithms)
3. Add context detection with clear fallback rules
4. Integrate with minimal changes to existing codebase
5. Test extensively with real content samples
6. Expand database based on actual processing results

**CRITICAL SUCCESS FACTORS**:
- Must fix "Śrīmad Bhagavad Gītā" capitalization issue
- Must maintain >1,500 segments/second processing
- Must stay within 150-line code budget
- Must work with existing lexicon caching system

**Story Status**: ⏳ Ready for Implementation