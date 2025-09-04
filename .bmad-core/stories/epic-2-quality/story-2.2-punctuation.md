# Story 2.2: Smart Punctuation Engine

**Epic**: Quality & Monitoring  
**Story Points**: 2  
**Priority**: Medium  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** content editor  
**I want** intelligent sentence structure and punctuation  
**So that** transcripts have proper readability and professional formatting

## 🎯 Business Value

- **Readability**: Proper punctuation makes content easier to read
- **Professionalism**: Well-formatted transcripts appear more polished  
- **User Experience**: Readers don't have to mentally add punctuation
- **Consistency**: Standardized formatting across all processed content
- **Academic Standards**: Proper sentence structure for scholarly content

## ✅ Acceptance Criteria

### **AC 1: Sentence Ending Detection**
- [ ] Detect common lecture conclusion phrases and add periods
- [ ] Handle Sanskrit/spiritual endings: "Om Shanti", "Namaste", "Hari Om"
- [ ] Recognize gratitude expressions: "Thank you", "Thank you very much"
- [ ] Add periods after blessing phrases: "May all beings be happy"
- [ ] Configurable phrase patterns via YAML configuration

### **AC 2: Capitalization After Punctuation**
- [ ] Capitalize first word after periods  
- [ ] Handle abbreviated titles properly: "Dr.", "Sri", "Swami"
- [ ] Maintain existing proper noun capitalization
- [ ] Don't capitalize after abbreviations or decimal numbers
- [ ] Smart handling of quotation marks and parentheses

### **AC 3: Intelligent Punctuation Placement**
- [ ] Add commas before transitional phrases: "however", "therefore", "thus"
- [ ] Handle questions with appropriate question marks
- [ ] Detect pause indicators and convert to appropriate punctuation
- [ ] Avoid over-punctuation (don't add where already exists)
- [ ] Preserve intentional formatting choices

### **AC 4: Sanskrit-Specific Handling**  
- [ ] Don't add punctuation within Sanskrit mantras or verses
- [ ] Handle transliterated text appropriately  
- [ ] Preserve sacred text formatting
- [ ] Recognize verse references and format appropriately
- [ ] Maintain IAST transliteration integrity

### **AC 5: Configuration & Control**
- [ ] Enable/disable punctuation enhancement in config
- [ ] Configurable phrase patterns and rules
- [ ] Severity levels: conservative, balanced, aggressive
- [ ] Custom phrase patterns for specific speakers/styles
- [ ] Logging of punctuation changes for review

## 🏗️ Implementation Plan

### **Phase 1: Phrase Pattern System (30 minutes)**
```python
class PunctuationPatterns:
    def __init__(self):
        self.ending_phrases = [
            "thank you", "namaste", "om shanti", "hari om",
            "may all beings be happy", "may you be blessed",
            "peace be with you", "god bless"
        ]
        self.transition_phrases = [
            "however", "therefore", "thus", "nevertheless", 
            "furthermore", "moreover", "in addition"
        ]
        self.abbreviations = ["dr", "sri", "swami", "mt", "st"]
```

### **Phase 2: Core Punctuation Logic (45 minutes)**
```python
def enhance_punctuation(self, text: str) -> str:
    """Add intelligent punctuation to text."""
    # 1. Add periods after conclusion phrases
    # 2. Capitalize after periods  
    # 3. Add commas before transitions
    # 4. Handle questions and exclamations
    # 5. Clean up spacing around punctuation
```

### **Phase 3: Sanskrit-Aware Processing (15 minutes)**
```python
def is_sanskrit_context(self, text: str, position: int) -> bool:
    """Check if position is within Sanskrit text that should be preserved."""
    # Look for Sanskrit indicators nearby
    # Check for verse references
    # Preserve transliterated passages
```

### **Phase 4: Configuration Integration (30 minutes)**
```yaml
punctuation:
  enabled: true
  mode: "balanced"  # conservative, balanced, aggressive
  custom_endings: []
  preserve_sanskrit: true
  log_changes: false
```

## 📁 Files to Create/Modify

### **Modified Files:**
- `sanskrit_processor_v2.py` - Add punctuation enhancement to `_normalize_text`
- `config.yaml` - Add punctuation configuration section
- `README.md` - Document punctuation features

### **New Files:**
- `services/punctuation_engine.py` - Punctuation logic (optional separation)
- `tests/test_punctuation.py` - Unit tests

## 🔧 Technical Specifications

### **Punctuation Enhancement Algorithm:**
```python
def enhance_punctuation(self, text: str) -> tuple[str, int]:
    """
    Enhance text punctuation using rule-based patterns.
    Returns (enhanced_text, changes_made).
    """
    original_text = text
    changes = 0
    
    # Phase 1: Add ending punctuation
    for phrase in self.ending_phrases:
        pattern = rf'\b{re.escape(phrase)}(?!\.)'
        if re.search(pattern, text, re.IGNORECASE):
            text = re.sub(pattern, f'{phrase}.', text, flags=re.IGNORECASE)
            changes += 1
    
    # Phase 2: Capitalize after periods
    text = re.sub(r'\.(\s+)([a-z])', 
                  lambda m: f'.{m.group(1)}{m.group(2).upper()}', 
                  text)
    
    # Phase 3: Add transitional commas
    for transition in self.transition_phrases:
        pattern = rf'\b{re.escape(transition)}(?!\s*,)'
        text = re.sub(pattern, f', {transition}', text, flags=re.IGNORECASE)
        changes += text.count(f', {transition}') - original_text.count(f', {transition}')
    
    # Phase 4: Question detection
    question_starters = ['what', 'where', 'when', 'why', 'how', 'who', 'which']
    for starter in question_starters:
        pattern = rf'\b{re.escape(starter)}\s+[^.?]*(?<![.?])$'
        if re.search(pattern, text, re.IGNORECASE):
            text = re.sub(pattern, lambda m: m.group(0) + '?', text, flags=re.IGNORECASE)
            changes += 1
    
    # Phase 5: Clean spacing
    text = re.sub(r'\s+([.,:;!?])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)  # Add space after sentence endings
    
    return text, changes
```

### **Sanskrit Context Detection:**
```python
def is_sanskrit_context(self, text: str, position: int) -> bool:
    """
    Check if position is within Sanskrit/sacred text context.
    Looks for indicators like verse references, transliteration, etc.
    """
    # Get context window around position
    window_start = max(0, position - 50)
    window_end = min(len(text), position + 50)
    context = text[window_start:window_end]
    
    sanskrit_indicators = [
        r'\d+\.\d+',  # Verse references like "2.47"
        r'chapter\s+\d+',  # "Chapter 2"
        r'[āīūṛṅṇṭḍṣśḥṃ]',  # IAST characters
        r'om\s+\w+\s+om',  # Mantras
        'bhagavad gita', 'upanishad', 'vedas'
    ]
    
    return any(re.search(pattern, context, re.IGNORECASE) for pattern in sanskrit_indicators)
```

### **Configuration Modes:**

#### **Conservative Mode:**
- Only add periods after very common endings
- Minimal capitalization changes  
- Preserve all existing formatting

#### **Balanced Mode (Default):**
- Standard punctuation improvements
- Smart capitalization
- Moderate comma insertion

#### **Aggressive Mode:**
- Extensive punctuation enhancement
- Complex sentence detection
- Maximum formatting improvements

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_ending_punctuation():
    processor = SanskritProcessor()
    
    # Test common endings
    result, changes = processor.enhance_punctuation("Thank you very much")
    assert result == "Thank you very much."
    assert changes == 1
    
    # Test Sanskrit endings  
    result, changes = processor.enhance_punctuation("Om Shanti")
    assert result == "Om Shanti."
    assert changes == 1

def test_capitalization():
    processor = SanskritProcessor()
    
    result, changes = processor.enhance_punctuation("Hello. how are you")
    assert result == "Hello. How are you"
    
def test_sanskrit_preservation():
    processor = SanskritProcessor()
    
    # Should not add punctuation within verse references
    text = "In Bhagavad Gita 2.47 Krishna says"  
    result, changes = processor.enhance_punctuation(text)
    assert "2.47." not in result  # Don't add period after verse number

def test_question_detection():
    processor = SanskritProcessor()
    
    result, changes = processor.enhance_punctuation("What is dharma")
    assert result == "What is dharma?"
    assert changes == 1
```

### **Integration Tests:**
```python
def test_full_srt_processing():
    # Test with realistic SRT content
    srt_content = """
    1
    00:00:01,000 --> 00:00:03,000
    Welcome to this lecture what is the meaning of life
    
    2  
    00:00:04,000 --> 00:00:06,000
    Thank you for joining us today
    """
    
    # Process and verify punctuation improvements
    processor = SanskritProcessor()
    result = processor.process_srt_file("test.srt", "output.srt")
    
    # Check for proper punctuation in output
```

## 📊 Success Metrics

- **Readability Improvement**: 20% fewer sentences without ending punctuation
- **Professional Formatting**: 95% of conclusion phrases properly punctuated
- **Accuracy**: < 1% false positive rate (incorrect punctuation added)
- **Performance**: < 10ms additional processing time per segment
- **User Satisfaction**: Improved transcript readability scores

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-punctuation | Medium | Conservative default mode, extensive testing |
| Sanskrit formatting damage | High | Context detection, preserve sacred text integrity |
| False question detection | Low | Careful pattern matching, manual review capabilities |
| Performance impact | Low | Efficient regex patterns, optional feature |

## 🔄 Story Progress Tracking

- [ ] **Started**: Implementation begun
- [ ] **Patterns**: Phrase pattern system implemented
- [ ] **Core Logic**: Punctuation enhancement algorithm working
- [ ] **Sanskrit Handling**: Context detection preserves sacred text  
- [ ] **Configuration**: All modes and options functional
- [ ] **Testing**: Comprehensive test coverage  
- [ ] **Integration**: Seamless integration with existing processor
- [ ] **Documentation**: Examples and configuration documented

## 📝 Implementation Notes

### **Design Philosophy:**
- **Conservative by Default**: Better to under-punctuate than over-punctuate
- **Context Aware**: Understand the spiritual/academic content context  
- **Configurable**: Users can adjust aggressiveness to their needs
- **Reversible**: Changes should be reviewable and adjustable

### **Common Patterns to Handle:**
```
Input:  "Thank you very much"
Output: "Thank you very much."

Input:  "what is the meaning of dharma"  
Output: "What is the meaning of dharma?"

Input:  "in bhagavad gita 2.47 krishna says"
Output: "In Bhagavad Gita 2.47 Krishna says"

Input:  "namaste"
Output: "Namaste."

Input:  "however this is important"
Output: "However, this is important"
```

### **Edge Cases:**
- Abbreviations: "Dr. Smith said" (don't capitalize 'said')
- Numbers: "The value is 2.47 meters" (don't capitalize 'meters')  
- Quotes: "He said 'hello.' How are you?" (capitalize 'How')
- Sanskrit: "Om mani padme hum" (preserve as sacred text)

---

**Dependencies**: None (can run independently)  
**Estimated completion**: Day 4 of sprint