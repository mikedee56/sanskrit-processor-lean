# Story 6.2: Sacred Text Preservation System

**Epic**: Sanskrit Content Quality Excellence  
**Story Points**: 5  
**Priority**: High  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **CRITICAL QUALITY ISSUE**: Fixes sacred text formatting destruction identified in processing analysis

## 📋 User Story

**As a** Sanskrit content processor handling sacred mantras and verses  
**I want** preservation of traditional formatting and sacred symbols  
**So that** mantras retain their structure and sacred symbols are not corrupted during processing

## 🔥 **Problem Being Solved**

### **Current Formatting Destruction:**
```text
INPUT:  "Om Puurnnam-Adah Puurnnam-Idam 
         Puurnnaat-Puurnnam-Udacyate |
         Purnnasya Puurnnam-Aadaaya 
         Puurnnam-Eva-Avashissyate ||
         Om  
         Shaantih Shaantih Shaantih ||"

OUTPUT: "Om Puurnnam-Adah Puurnnam-Idam Puurnnaat-Puurnnam-Udacyate ?
         Purnnasya Puurnnam-Aadaaya Puurnnam-Eva-Avashissyate ?
         Om
         Shaantih Shaantih Shaantih ?" ❌ WRONG!

SHOULD: "Om pūrṇam adaḥ pūrṇam idam 
         pūrṇāt pūrṇam udacyate |
         pūrṇasya pūrṇam ādāya 
         pūrṇam evāvaśiṣyate ||
         Om
         śāntiḥ śāntiḥ śāntiḥ ||" ✅ CORRECT
```

### **Sacred Symbol Corruption Analysis:**
- **Sacred Pipe Symbols**: `|` and `||` → `?` (Completely Wrong!)
- **Line Structure**: Verse breaks removed, traditional meter lost
- **Sacred Punctuation**: Traditional dandas `।` and double dandas `।।` not supported
- **Mantra Hyphens**: Sometimes appropriate (`Om-mani-padme-hum`), sometimes not

## 🎯 Business Value

- **Spiritual Integrity**: Maintain reverence for sacred content in 11k hours processing
- **Academic Standards**: Proper Sanskrit verse formatting for scholarly use
- **Cultural Respect**: Show appropriate respect for religious traditions
- **Professional Quality**: YouTube, books, apps display sacred content correctly

## ✅ Acceptance Criteria

### **AC 1: Sacred Symbol Protection**
- [ ] **Preserve Pipe Symbols**: `|` (single pipe) and `||` (double pipe) maintained
- [ ] **Support Devanagari Punctuation**: `।` (danda) and `।।` (double danda)  
- [ ] **Protect Om Symbol**: `ॐ` preserved when present
- [ ] **Sacred Unicode**: `◦`, `○`, `★`, `✦` symbols protected in mantras

### **AC 2: Verse Structure Preservation**
- [ ] **Line Break Intelligence**: Preserve verse structure in mantra/shloka context
- [ ] **Meter Preservation**: Traditional Sanskrit verse meter maintained where appropriate
- [ ] **Indentation Respect**: Sacred text indentation patterns preserved
- [ ] **Spacing Normalization**: Excessive spaces cleaned but structure preserved

### **AC 3: Context-Aware Processing**
- [ ] **Mantra Detection**: Identify mantra/verse context vs regular text
- [ ] **Sacred Text Classification**: Distinguish prayers, verses, mantras, regular commentary
- [ ] **Pronunciation Guide Handling**: Appropriate handling of hyphens in sacred contexts
- [ ] **Traditional Format Recognition**: Detect and preserve classical formatting patterns

### **AC 4: Lean Implementation Requirements**
- [ ] **Code Limit**: Maximum 180 lines for entire sacred preservation system
- [ ] **No New Dependencies**: Use only existing stdlib + PyYAML + requests
- [ ] **Performance**: Maintain >1,500 segments/second processing speed
- [ ] **Memory**: Add <5MB to memory footprint  
- [ ] **Backward Compatible**: All existing functionality preserved

## 🏗️ Implementation Plan

### **Phase 1: Sacred Content Detection (Day 1-2)**

#### **Sacred Context Classifier**
```python
# New: processors/sacred_classifier.py (~60 lines)
class SacredContentClassifier:
    """
    Lightweight classifier for sacred content detection.
    Uses simple pattern matching for lean implementation.
    """
    
    MANTRA_INDICATORS = [
        "om", "aum", "ॐ", "hare", "krishna", "rama",
        "shanti", "śānti", "namah", "namaha", "svaha"
    ]
    
    VERSE_INDICATORS = [
        "|", "||", "।", "।।", "chapter", "verse", 
        "shloka", "śloka", "adhyaya", "adhyāya"
    ]
    
    SACRED_SYMBOLS = {
        "|": "|",      # Preserve single pipe
        "||": "||",    # Preserve double pipe  
        "।": "।",      # Devanagari danda
        "।।": "।।",    # Devanagari double danda
        "ॐ": "ॐ",      # Om symbol
        "◦": "◦",      # Sacred bullet
        "○": "○",      # Sacred circle
        "★": "★",      # Sacred star
        "✦": "✦"       # Sacred sparkle
    }
    
    def classify_content(self, text: str) -> str:
        """
        Returns: 'mantra', 'verse', 'prayer', 'commentary', 'regular'
        Simple rule-based classification for performance.
        """
        text_lower = text.lower()
        
        # Check for sacred symbols (highest priority)
        if any(symbol in text for symbol in self.SACRED_SYMBOLS):
            return 'verse' if any(pipe in text for pipe in ['|', '||', '।', '।।']) else 'mantra'
            
        # Check for mantra indicators
        mantra_count = sum(1 for indicator in self.MANTRA_INDICATORS if indicator in text_lower)
        if mantra_count >= 2:
            return 'mantra'
            
        # Check for verse indicators  
        if any(indicator in text_lower for indicator in self.VERSE_INDICATORS):
            return 'verse'
            
        return 'regular'
```

#### **Sacred Symbol Protector**
```python
# New: processors/symbol_protector.py (~40 lines)
class SacredSymbolProtector:
    """
    Simple symbol protection system for sacred content.
    Prevents corruption during text processing.
    """
    
    def __init__(self):
        self.protected_symbols = SacredContentClassifier.SACRED_SYMBOLS
        self.symbol_placeholders = {}
        
    def protect_symbols(self, text: str) -> tuple[str, dict]:
        """
        Replace sacred symbols with placeholders before processing.
        Returns (protected_text, restoration_map).
        """
        protected_text = text
        restoration_map = {}
        
        for i, (symbol, replacement) in enumerate(self.protected_symbols.items()):
            if symbol in text:
                placeholder = f"__SACRED_{i}__"
                protected_text = protected_text.replace(symbol, placeholder)
                restoration_map[placeholder] = replacement
                
        return protected_text, restoration_map
        
    def restore_symbols(self, text: str, restoration_map: dict) -> str:
        """Restore sacred symbols from placeholders."""
        restored_text = text
        for placeholder, symbol in restoration_map.items():
            restored_text = restored_text.replace(placeholder, symbol)
        return restored_text
```

### **Phase 2: Verse Structure Preservation (Day 3-4)**

#### **Verse Formatter**
```python
# New: processors/verse_formatter.py (~80 lines)
class VerseFormatter:
    """
    Intelligent verse structure preservation for sacred texts.
    Maintains traditional formatting while enabling corrections.
    """
    
    def __init__(self):
        self.verse_patterns = self._compile_verse_patterns()
        
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
        # 1. Protect sacred symbols
        # 2. Preserve meaningful hyphens (Om-mani-padme-hum)
        # 3. Normalize excessive spacing
        # 4. Maintain line structure for multi-line mantras
        pass
        
    def _process_verse(self, text: str) -> str:
        """
        Verse processing: preserve meter, line breaks, traditional punctuation.
        """
        # 1. Detect verse boundaries (| and ||)
        # 2. Preserve line breaks at verse boundaries
        # 3. Maintain traditional indentation
        # 4. Handle śloka meter appropriately
        pass
        
    def _detect_verse_boundaries(self, text: str) -> list[int]:
        """Find positions of verse breaks (pipes, dandas)."""
        boundaries = []
        for i, char in enumerate(text):
            if char in ['|', '।']:
                boundaries.append(i)
        return boundaries
```

### **Phase 3: Integration & Testing (Day 5)**

#### **Integration with Main Processor**
```python
# Modified: sanskrit_processor_v2.py (add ~40 lines)
class SanskritProcessor:
    def __init__(self, lexicon_dir: Path, config: dict = None):
        # Add sacred text components
        self.sacred_classifier = SacredContentClassifier()
        self.symbol_protector = SacredSymbolProtector()
        self.verse_formatter = VerseFormatter()
        
    def process_text(self, text: str) -> str:
        """Enhanced processing with sacred text awareness."""
        # 1. Classify content type
        content_type = self.sacred_classifier.classify_content(text)
        
        if content_type in ['mantra', 'verse', 'prayer']:
            # Sacred content processing pipeline
            # 1. Protect symbols
            protected_text, restoration_map = self.symbol_protector.protect_symbols(text)
            
            # 2. Apply corrections to protected text
            corrected_text = self._apply_standard_corrections(protected_text)
            
            # 3. Apply verse formatting
            formatted_text = self.verse_formatter.process_verse(corrected_text, content_type)
            
            # 4. Restore sacred symbols
            final_text = self.symbol_protector.restore_symbols(formatted_text, restoration_map)
            
            return final_text
        else:
            # Regular text processing
            return self._apply_standard_corrections(text)
```

## 📁 Files to Create/Modify

### **New Files:**
- `processors/sacred_classifier.py` - Sacred content detection (~60 lines)
- `processors/symbol_protector.py` - Sacred symbol protection (~40 lines)  
- `processors/verse_formatter.py` - Verse structure preservation (~80 lines)

### **Modified Files:**
- `sanskrit_processor_v2.py` - Integration with sacred text processing (~40 additional lines)
- `config.yaml` - Add sacred text processing configuration

### **Code Budget:**
- **Total New Code**: ~180 lines (within story limit)
- **Modified Code**: ~40 lines (minimal integration changes)
- **Performance Impact**: Minimal overhead for non-sacred content

## 🔧 Technical Specifications

### **Sacred Content Detection Algorithm**
```python
def detect_sacred_content(text: str) -> tuple[str, float]:
    """
    Lightweight sacred content detection:
    1. Symbol-based detection (highest confidence)
    2. Keyword-based classification (medium confidence) 
    3. Pattern-based identification (lower confidence)
    
    Returns (content_type, confidence_score)
    """
    confidence = 0.0
    content_type = 'regular'
    
    # Sacred symbols = high confidence
    if any(symbol in text for symbol in ['|', '||', '।', '।।', 'ॐ']):
        content_type = 'verse' if '|' in text else 'mantra'
        confidence = 0.95
        
    # Multiple mantra keywords = medium confidence
    elif mantra_keyword_count(text) >= 2:
        content_type = 'mantra'
        confidence = 0.75
        
    # Verse structure indicators = medium confidence
    elif verse_structure_detected(text):
        content_type = 'verse'  
        confidence = 0.70
        
    return content_type, confidence
```

### **Symbol Protection Strategy**
```python
SYMBOL_PROTECTION_MAP = {
    # Sacred punctuation
    "|": "__PIPE_SINGLE__",
    "||": "__PIPE_DOUBLE__", 
    "।": "__DANDA_SINGLE__",
    "।।": "__DANDA_DOUBLE__",
    
    # Sacred symbols
    "ॐ": "__OM_SYMBOL__",
    "◦": "__SACRED_BULLET__",
    "○": "__SACRED_CIRCLE__",
    "★": "__SACRED_STAR__",
    
    # Traditional spacing markers
    "   ": "__TRIPLE_SPACE__"  # Preserve significant spacing
}
```

## 🧪 Test Cases

### **Critical Test Cases**
```python
def test_sacred_symbol_preservation():
    processor = SanskritProcessor("lexicons")
    
    # Test Case 1: Pipe symbol preservation
    input_text = "Om pūrṇam adaḥ pūrṇam idam | pūrṇāt pūrṇam udacyate ||"
    result = processor.process_text(input_text)
    assert "|" in result
    assert "||" in result
    assert "?" not in result
    
    # Test Case 2: Line structure preservation  
    input_mantra = """Om Puurnnam-Adah Puurnnam-Idam 
    Puurnnaat-Puurnnam-Udacyate |"""
    result = processor.process_text(input_mantra)
    assert "\n" in result or result.count(" ") < input_mantra.count(" ") + 5
    
    # Test Case 3: Om symbol protection
    input_text = "ॐ śāntiḥ śāntiḥ śāntiḥ"
    result = processor.process_text(input_text)  
    assert "ॐ" in result

def test_verse_structure_preservation():
    # Multiple line verse preservation
    # Sacred spacing preservation
    # Traditional punctuation handling
    pass
```

### **Edge Cases**
```python
def test_sacred_text_edge_cases():
    # Mixed sacred/regular content
    # Multiple sacred symbol types
    # Nested protection scenarios
    # Performance with long verses
    pass
```

## 📊 Success Metrics

### **Sacred Content Quality**
- **Symbol Preservation**: 100% for identified sacred symbols (vs current 0%)
- **Verse Structure**: 98%+ traditional formatting preserved
- **Mantra Integrity**: 95%+ proper mantra formatting maintained
- **Context Detection**: 90%+ accurate sacred vs regular classification

### **Performance Requirements** 
- **Processing Speed**: ≥1,500 segments/second (minimal degradation)
- **Memory Usage**: +4MB maximum (total <84MB vs current <80MB)
- **Sacred Content Overhead**: <20ms additional per sacred segment
- **Classification Accuracy**: <5% false positive sacred detection

### **Lean Compliance**
- **Code Size**: ≤180 lines total implementation
- **Dependencies**: Zero new external libraries
- **Configuration**: Simple enable/disable flag in YAML
- **Integration**: Minimal changes to existing processor

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Over-Classification** | Low | Conservative sacred content detection |
| **Symbol Collision** | Low | Unique placeholder generation |
| **Performance Impact** | Medium | Fast classification, bypass for regular content |
| **False Sacred Detection** | Medium | Multiple validation criteria required |
| **Unicode Compatibility** | Low | Test with common sacred Unicode characters |

## 🔄 Story Progress Tracking

- [ ] **Started**: Sacred text preservation implementation begun
- [ ] **Sacred Classifier**: Content type detection working
- [ ] **Symbol Protector**: Sacred symbol preservation system complete  
- [ ] **Verse Formatter**: Structure preservation logic implemented
- [ ] **Integration Complete**: Works with existing processor
- [ ] **Performance Validated**: Meets speed/memory requirements
- [ ] **Testing Complete**: All sacred content test cases pass
- [ ] **Quality Improvement**: Sacred formatting >98% preserved

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Why This Approach is Lean:**
1. **Simple Classification**: Rule-based detection, no complex ML
2. **Minimal Overhead**: Fast bypass for regular content
3. **Focused Scope**: Only handles identified quality problem  
4. **Reusable Components**: Symbol protection usable across features
5. **Configuration-Driven**: Can be enabled/disabled easily

#### **Performance Optimization:**
- **Early Detection**: Quick classification to avoid unnecessary processing
- **Lazy Loading**: Sacred processors only loaded when needed
- **Symbol Caching**: Reuse protection maps for similar content
- **Bypass Logic**: Regular content skips sacred processing entirely

#### **Cultural Sensitivity:**
- **Research-Based**: Sacred symbols based on authentic Sanskrit traditions
- **Conservative Approach**: When in doubt, preserve rather than modify
- **Community Input**: Design allows for easy expansion of protected symbols
- **Respectful Processing**: Maintains spiritual integrity of content

### **Success Criteria for Story Completion:**
1. ✅ **Sacred Symbol Preservation**: `|` and `||` never become `?`
2. ✅ **Verse Structure Maintained**: Traditional formatting preserved
3. ✅ **Performance Maintained**: >1,500 segments/second processing
4. ✅ **Lean Compliance**: <180 lines, no new dependencies
5. ✅ **Quality Improvement**: >98% sacred formatting accuracy

**Story Definition of Done**: Sacred content is processed with reverence and traditional formatting is preserved while maintaining lean architecture and performance.

---

## 🤖 Dev Agent Instructions

**IMPLEMENTATION PRIORITY**: This story addresses a critical cultural and spiritual quality issue - corruption of sacred content that could be offensive to practitioners.

**LEAN IMPLEMENTATION APPROACH**:
1. Start with simple rule-based sacred content detection
2. Implement symbol protection using placeholder strategy  
3. Add minimal verse structure preservation
4. Test extensively with real Sanskrit mantras and verses
5. Ensure performance impact is minimal for regular content

**CRITICAL SUCCESS FACTORS**:
- Must prevent sacred symbol corruption (`|` → `?`)  
- Must preserve traditional verse formatting
- Must maintain processing performance for non-sacred content
- Must stay within 180-line code budget
- Must be culturally respectful and spiritually appropriate

**Story Status**: ⏳ Ready for Implementation