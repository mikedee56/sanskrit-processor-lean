# Story 4.1: Extended Lexicon System

**Epic**: Content Enhancement  
**Story Points**: 2  
**Priority**: Low  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** Sanskrit scholar and content processor  
**I want** comprehensive term coverage with common variations  
**So that** more Sanskrit/Hindi terms are correctly processed and formatted

## 🎯 Business Value

- **Coverage**: Handle more diverse vocabulary in lectures
- **Accuracy**: Reduce missed corrections due to limited lexicon  
- **Quality**: Professional formatting for broader range of terms
- **Completeness**: Comprehensive spiritual and philosophical terminology
- **User Satisfaction**: Better results with less manual correction needed

## ✅ Acceptance Criteria

### **AC 1: Expanded Sanskrit Terms**
- [ ] Add 25+ additional core Sanskrit concepts beyond current lexicon
- [ ] Include philosophical terms: advaita, dvaita, vishistadvaita, etc.
- [ ] Add yoga terminology: pranayama, asana, meditation practices
- [ ] Include ritual/ceremony terms: puja, aarti, sankirtana
- [ ] Maintain IAST transliteration for all terms

### **AC 2: Extended Proper Nouns**  
- [ ] Add 15+ additional deity names and avatars
- [ ] Include sage and teacher names: Vyasa, Valmiki, Adi Shankara
- [ ] Add geographical/pilgrimage sites: Kumbh Mela locations
- [ ] Include festival names: Diwali, Holi, Janmashtami variations
- [ ] Add traditional titles: Acharya, Guru, Swami variations

### **AC 3: Common Variations & Misspellings**
- [ ] Include phonetic variations for each term
- [ ] Add common ASR transcription errors  
- [ ] Handle different transliteration systems
- [ ] Include regional pronunciation variants
- [ ] Cover common English adaptations

### **AC 4: Hierarchical Categories**
- [ ] Organize terms by category: philosophy, practice, geography, etc.
- [ ] Add subcategories for better organization
- [ ] Include difficulty/confidence levels per term
- [ ] Add etymology notes where helpful
- [ ] Maintain backward compatibility with existing structure

### **AC 5: Quality & Validation**  
- [ ] All terms verified against authoritative sources
- [ ] IAST transliterations validated for accuracy
- [ ] No duplicate entries across files
- [ ] Consistent formatting and structure
- [ ] Documentation of term sources and meanings

## 🏗️ Implementation Plan

### **Phase 1: Research & Compilation (30 minutes)**
```yaml
# Research authoritative sources:
# - Monier-Williams Sanskrit Dictionary
# - Contemporary spiritual literature
# - Common lecture terminology analysis
# - Regional variations documentation
```

### **Phase 2: YAML Structure Enhancement (15 minutes)**
```yaml
# Enhanced structure with categories:
entries:
  - original_term: "advaita"
    variations: ["adwita", "advait", "advaitic"]
    transliteration: "advaita"
    category: "philosophy"
    subcategory: "vedanta"
    confidence: 1.0
    source_authority: "Traditional"
    meaning: "non-dualism"
    difficulty_level: "intermediate"
```

### **Phase 3: File Updates (45 minutes)**
```yaml
# Update corrections.yaml with new terms
# Update proper_nouns.yaml with new entities  
# Maintain alphabetical ordering
# Validate all entries
```

### **Phase 4: Testing & Validation (30 minutes)**
```python
# Test loading of expanded lexicons
# Verify no conflicts or duplicates
# Test processing with new terms
# Performance impact assessment
```

## 📁 Files to Create/Modify

### **Modified Files:**
- `lexicons/corrections.yaml` - Add new Sanskrit/Hindi terms
- `lexicons/proper_nouns.yaml` - Add new entities and names
- `README.md` - Document expanded vocabulary coverage

### **New Files:**  
- `tests/test_extended_lexicons.py` - Validation tests
- `docs/lexicon_sources.md` - Documentation of term sources (optional)

## 🔧 **Extended Vocabulary Specifications**

### **New Sanskrit Concepts (corrections.yaml):**
```yaml
# Philosophy & Vedanta
- original_term: "advaita"
  variations: ["adwita", "advait", "advaitic", "non-dualism"]
  transliteration: "advaita"
  category: "philosophy"

- original_term: "dvaita"  
  variations: ["dwita", "dvait", "dualism"]
  transliteration: "dvaita"
  category: "philosophy"

- original_term: "vishistadvaita"
  variations: ["vishishtadvaita", "qualified non-dualism"]
  transliteration: "viśiṣṭādvaita"
  category: "philosophy"

# Yoga & Practices  
- original_term: "pranayama"
  variations: ["pranayam", "breath control", "breathing"]
  transliteration: "prāṇāyāma"
  category: "practice"

- original_term: "asana"
  variations: ["asan", "posture", "yoga pose"]
  transliteration: "āsana"  
  category: "practice"

- original_term: "dhyana"
  variations: ["dhyan", "meditation", "contemplation"]
  transliteration: "dhyāna"
  category: "practice"

# Rituals & Ceremonies
- original_term: "puja"
  variations: ["pooja", "worship", "ritual"]
  transliteration: "pūjā"
  category: "ritual"

- original_term: "aarti"
  variations: ["arti", "aarati", "lamp ceremony"]
  transliteration: "āratī"
  category: "ritual"

- original_term: "sankirtana"
  variations: ["sankirtan", "group chanting", "congregational singing"]
  transliteration: "saṅkīrtana"
  category: "ritual"
```

### **New Proper Nouns (proper_nouns.yaml):**
```yaml
# Additional Deities & Avatars
- term: "Ganesha"
  variations: ["ganesh", "ganapati", "vinayaka"]
  category: "deity"

- term: "Durga" 
  variations: ["durga", "devi", "divine mother"]
  category: "deity"

- term: "Hanuman"
  variations: ["hanuman", "maruti", "anjaneya"]
  category: "deity"

# Sages & Teachers  
- term: "Vyasa"
  variations: ["vyas", "krishna dwaipayana", "ved vyasa"]
  category: "sage"

- term: "Valmiki"
  variations: ["valmiki", "maharishi valmiki", "adi kavi"]
  category: "sage"

- term: "Adi Shankara"
  variations: ["adi shankara", "shankaracharya", "shankara"]
  category: "acharya"

# Places & Geography
- term: "Vrindavan"
  variations: ["vrindavan", "vrindavana", "brindavan"]
  category: "place"

- term: "Haridwar"
  variations: ["haridwar", "hardwar", "gateway to god"]
  category: "place"

- term: "Rishikesh"
  variations: ["rishikesh", "hrishikesh", "yoga capital"]
  category: "place"

# Festivals
- term: "Janmashtami"
  variations: ["janmashtami", "krishna jayanti", "gokulashtami"]
  category: "festival"

- term: "Diwali"
  variations: ["diwali", "deepavali", "festival of lights"]
  category: "festival"
```

### **Performance Considerations:**
```python
# Lexicon loading optimization for larger datasets
class OptimizedLexiconLoader:
    def __init__(self, lexicon_dir: Path):
        self.lexicon_dir = Path(lexicon_dir) 
        self.corrections = {}
        self.proper_nouns = {}
        self._variation_index = {}  # Fast lookup for variations
        self._load_lexicons()
        self._build_indexes()
    
    def _build_indexes(self):
        """Build fast lookup indexes for variations."""
        for term, data in self.corrections.items():
            for variation in data.get('variations', []):
                self._variation_index[variation.lower()] = term
```

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_expanded_lexicon_loading():
    lexicons = LexiconLoader("lexicons")
    
    # Test new philosophical terms
    assert "advaita" in lexicons.corrections
    assert "pranayama" in lexicons.corrections
    assert "puja" in lexicons.corrections
    
    # Test new proper nouns
    assert "ganesha" in lexicons.proper_nouns
    assert "vyasa" in lexicons.proper_nouns
    assert "vrindavan" in lexicons.proper_nouns

def test_variation_recognition():
    processor = SanskritProcessor()
    
    # Test philosophical term variations
    result, corrections = processor.process_text("I study adwita vedanta")
    assert "advaita" in result
    assert corrections >= 1
    
    # Test proper noun variations
    result, corrections = processor.process_text("ganesh is beloved")
    assert "Ganesha" in result
    assert corrections >= 1

def test_transliteration_accuracy():
    lexicons = LexiconLoader("lexicons")
    
    # Verify IAST transliterations are properly formatted
    advaita = lexicons.corrections["advaita"]  
    assert "ā" in advaita["transliteration"]  # Proper IAST long 'a'
    
    pranayama = lexicons.corrections["pranayama"]
    assert "ṇ" in pranayama["transliteration"]  # Proper IAST retroflex 'n'

def test_no_duplicates():
    lexicons = LexiconLoader("lexicons")
    
    # Check for duplicate entries across files
    correction_terms = set(lexicons.corrections.keys())
    proper_noun_terms = set(lexicons.proper_nouns.keys())
    
    # Should be no overlap between corrections and proper nouns
    overlap = correction_terms & proper_noun_terms
    assert len(overlap) == 0, f"Duplicate terms found: {overlap}"

def test_performance_with_extended_lexicon():
    processor = SanskritProcessor()
    test_text = "Krishna teaches advaita to arjuna in vrindavan during pranayama"
    
    start_time = time.time()
    result, corrections = processor.process_text(test_text)
    duration = time.time() - start_time
    
    # Should still be fast with expanded lexicon
    assert duration < 0.01  # < 10ms
    assert corrections >= 4  # Should find multiple terms
```

### **Integration Tests:**
```python
def test_real_lecture_processing():
    # Test with realistic spiritual lecture content
    lecture_text = """
    Today we will discuss the principles of advaita vedanta
    as taught by adi shankara. Through pranayama and dhyana,
    we can understand our true nature. ganesh removes obstacles
    on our spiritual path to vrindavan consciousness.
    """
    
    processor = SanskritProcessor()  
    result, corrections = processor.process_text(lecture_text)
    
    # Verify proper processing of extended vocabulary
    assert "advaita" in result
    assert "Adi Shankara" in result  
    assert "Ganesha" in result
    assert "Vrindavan" in result
    assert corrections >= 6
```

## 📊 Success Metrics

- **Vocabulary Coverage**: 50+ additional terms across all categories
- **Processing Accuracy**: > 95% recognition rate for new terms
- **Performance Impact**: < 5% increase in lexicon loading time
- **User Coverage**: Handle 90% of common spiritual/philosophical terminology
- **Quality**: 100% of new terms validated against authoritative sources

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Term accuracy issues | Medium | Verify against multiple authoritative sources |
| Performance degradation | Low | Optimize lookup algorithms, benchmark loading times |
| Maintenance complexity | Medium | Clear categorization, comprehensive documentation |
| Regional variation conflicts | Low | Include multiple valid variations, document sources |

## 🔄 Story Progress Tracking

- [ ] **Started**: Research and compilation begun
- [ ] **Research**: Terms researched from authoritative sources
- [ ] **Structure**: YAML structure enhanced with metadata
- [ ] **Implementation**: New terms added to lexicon files
- [ ] **Validation**: All terms verified for accuracy  
- [ ] **Testing**: Comprehensive test coverage completed
- [ ] **Performance**: Impact assessment completed
- [ ] **Documentation**: Usage and sources documented

## 📝 Implementation Notes

### **Term Selection Criteria:**
1. **Frequency**: Common in spiritual/philosophical discourse
2. **Authority**: Found in traditional texts or accepted usage  
3. **Variations**: Has multiple common misspellings/variations
4. **Context**: Relevant to yoga/vedanta lecture content
5. **Clarity**: Unambiguous meaning in spiritual context

### **Source References:**
- **Primary**: Traditional Sanskrit texts and commentaries
- **Secondary**: Contemporary spiritual literature  
- **Linguistic**: Monier-Williams Sanskrit Dictionary
- **Practical**: Common usage in spiritual communities

### **Quality Assurance:**
- Cross-reference multiple sources for each term
- Validate IAST transliterations with Sanskrit scholars
- Test variations with real ASR output
- Review for cultural sensitivity and accuracy

### **Future Expansion:**
- Add terms based on user feedback and common processing errors
- Include regional language variations (Tamil, Telugu, etc.)
- Add contemporary spiritual teacher names and terminology
- Expand to other Indian philosophical traditions

---

**Dependencies**: None (pure data enhancement)  
**Estimated completion**: Day 5 of sprint (parallel with Story 3.1)