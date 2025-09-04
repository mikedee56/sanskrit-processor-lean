# Story 3.1: Simple NER Fallback System

**Epic**: Resilience & Fallback  
**Story Points**: 4  
**Priority**: Medium  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** system operator  
**I want** basic entity recognition when MCP services are unavailable  
**So that** processing continues with degraded but functional named entity recognition

## 🎯 Business Value

- **Reliability**: System continues working when external services fail
- **Performance**: Local NER is faster than network calls  
- **Cost Efficiency**: Reduces dependency on external API usage
- **Independence**: Core functionality works offline
- **Graceful Degradation**: Users get best available service quality

## ✅ Acceptance Criteria

### **AC 1: Rule-Based Entity Extraction**
- [ ] Identify deities: Krishna, Shiva, Vishnu, Rama, Hanuman, etc.
- [ ] Recognize texts: Vedas, Upanishads, Bhagavad Gita, Ramayana, Mahabharata
- [ ] Find concepts: dharma, karma, yoga, moksha, samsara, etc.  
- [ ] Detect places: Vrindavan, Ayodhya, Kashi, Haridwar, etc.
- [ ] Extract people: Arjuna, Yudhishthira, Sita, etc.

### **AC 2: Automatic Fallback Integration**
- [ ] Seamlessly activate when MCP client fails or is unavailable
- [ ] Log fallback activation for monitoring
- [ ] Maintain same interface as MCP-based NER
- [ ] Return compatible data structures  
- [ ] No user intervention required for fallback

### **AC 3: Performance Requirements**
- [ ] Entity extraction in < 50ms per text segment
- [ ] Memory usage < 5MB for entity data
- [ ] Support for batch processing (multiple segments)
- [ ] Comparable accuracy to MCP for basic entities (> 80%)
- [ ] Confidence scoring for extracted entities

### **AC 4: Extensible Entity Database**
- [ ] YAML-based entity definitions for easy updates
- [ ] Categories with hierarchical structure
- [ ] Synonyms and variations support
- [ ] Confidence levels per entity type
- [ ] Custom entity additions via configuration

### **AC 5: Integration Points**
- [ ] Drop-in replacement for MCP NER functionality
- [ ] Works with existing `enhanced_processor.py`
- [ ] Configurable via `config.yaml`
- [ ] Metrics integration for tracking usage
- [ ] Clear distinction between MCP and fallback results

## 🏗️ Implementation Plan

### **Phase 1: Entity Database Design (45 minutes)**
```yaml
# entities.yaml
entities:
  deities:
    confidence: 0.9
    entities:
      - name: "Krishna"
        variations: ["krishna", "krsna", "kṛṣṇa"]
        category: "deity"
      - name: "Shiva"  
        variations: ["shiva", "siva", "śiva"]
        category: "deity"
        
  texts:
    confidence: 0.95
    entities:
      - name: "Bhagavad Gita"
        variations: ["bhagavad gita", "bhagvad geeta", "gita"]
        category: "scripture"
```

### **Phase 2: Core NER Engine (60 minutes)**
```python
class SimpleNER:
    def __init__(self, entities_path: str):
        self.entities = self._load_entities(entities_path)
        self._build_lookup_tables()
        
    def extract_entities(self, text: str) -> List[EntityMatch]:
        # Pattern-based entity detection
        # Return structured entity matches
        
    def batch_extract(self, texts: List[str]) -> List[List[EntityMatch]]:
        # Efficient batch processing
```

### **Phase 3: Fallback Integration (30 minutes)**
```python
class EnhancedProcessorWithFallback:
    def _get_ner_client(self):
        # Try MCP first, fallback to SimpleNER
        if self.mcp_client and self.mcp_client.is_available():
            return self.mcp_client
        else:
            return self.simple_ner
```

### **Phase 4: Testing & Optimization (45 minutes)**
```python
# Comprehensive tests for accuracy and performance
# Integration testing with enhanced processor
# Benchmarking against MCP performance
```

## 📁 Files to Create/Modify

### **New Files:**
- `services/simple_ner.py` - Core NER implementation
- `data/entities.yaml` - Entity database
- `tests/test_simple_ner.py` - Unit tests

### **Modified Files:**  
- `enhanced_processor.py` - Integration with fallback
- `config.yaml` - NER fallback configuration
- `README.md` - Document fallback capabilities

## 🔧 Technical Specifications

### **Entity Data Structure:**
```python
@dataclass
class EntityMatch:
    text: str           # Original text found
    entity: str         # Canonical entity name
    category: str       # deity, text, concept, place, person
    confidence: float   # 0.0 - 1.0
    start_pos: int      # Position in original text
    end_pos: int        # End position
    source: str         # 'simple_ner' vs 'mcp'
```

### **Core NER Algorithm:**
```python
def extract_entities(self, text: str) -> List[EntityMatch]:
    """
    Extract named entities using pattern matching.
    Fast, rule-based approach for common Sanskrit/Hindu entities.
    """
    entities = []
    text_lower = text.lower()
    
    for category, category_data in self.entities.items():
        base_confidence = category_data['confidence']
        
        for entity_info in category_data['entities']:
            canonical_name = entity_info['name']
            variations = [canonical_name.lower()] + entity_info.get('variations', [])
            
            for variation in variations:
                # Find all occurrences of this variation
                start = 0
                while True:
                    pos = text_lower.find(variation, start)
                    if pos == -1:
                        break
                    
                    # Check word boundaries to avoid partial matches
                    if self._is_word_boundary(text_lower, pos, pos + len(variation)):
                        # Calculate confidence based on variation quality
                        confidence = self._calculate_confidence(
                            variation, canonical_name, base_confidence
                        )
                        
                        entities.append(EntityMatch(
                            text=text[pos:pos+len(variation)],
                            entity=canonical_name,
                            category=category,
                            confidence=confidence,
                            start_pos=pos,
                            end_pos=pos + len(variation),
                            source='simple_ner'
                        ))
                    
                    start = pos + 1
    
    # Remove duplicates and overlaps
    return self._deduplicate_entities(entities)
```

### **Performance Optimizations:**
```python
def _build_lookup_tables(self):
    """Pre-compute lookup structures for fast matching."""
    self.lookup_trie = {}  # Trie structure for fast prefix matching
    self.category_map = {}  # Quick category lookup
    
    # Build optimized data structures for O(n) text scanning
```

### **Configuration Integration:**
```yaml
# config.yaml additions
ner:
  fallback:
    enabled: true
    entities_file: "data/entities.yaml"
    min_confidence: 0.7
    enable_fuzzy_matching: false
    log_fallback_usage: true
```

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_deity_detection():
    ner = SimpleNER("data/entities.yaml")
    entities = ner.extract_entities("Krishna and Shiva are important deities")
    
    assert len(entities) == 2
    assert entities[0].entity == "Krishna"
    assert entities[0].category == "deity"
    assert entities[0].confidence > 0.8

def test_scripture_recognition():
    ner = SimpleNER("data/entities.yaml")
    entities = ner.extract_entities("The Bhagavad Gita teaches us about dharma")
    
    scripture_entities = [e for e in entities if e.category == "scripture"]
    concept_entities = [e for e in entities if e.category == "concept"]
    
    assert len(scripture_entities) == 1
    assert len(concept_entities) == 1

def test_fallback_integration():
    processor = EnhancedSanskritProcessor()
    
    # Simulate MCP failure
    processor.mcp_client = None
    
    result = processor.process_text("Krishna teaches dharma in the Gita")
    
    # Should still work with simple NER
    assert "Krishna" in result[0]
    assert len(result[1]) > 0  # Some entities found

def test_performance_benchmark():
    ner = SimpleNER("data/entities.yaml")
    test_text = "Krishna and Arjuna discuss dharma in the Bhagavad Gita"
    
    start_time = time.time()
    for _ in range(1000):
        entities = ner.extract_entities(test_text)
    duration = time.time() - start_time
    
    assert duration < 1.0  # 1000 extractions in < 1 second
    assert len(entities) >= 4  # Should find Krishna, Arjuna, dharma, Bhagavad Gita
```

### **Integration Tests:**
```python
def test_mcp_fallback_switching():
    # Test automatic fallback when MCP fails
    # Test restoration when MCP becomes available
    # Test metrics tracking of fallback usage
    
def test_accuracy_comparison():
    # Compare simple NER results with known MCP results
    # Ensure > 80% accuracy for basic entities
    # Document precision/recall metrics
```

## 📊 Success Metrics

- **Availability**: 100% uptime (never fails due to external dependencies)
- **Performance**: < 50ms entity extraction per segment
- **Accuracy**: > 80% precision for common entities vs manual annotation
- **Coverage**: Recognizes 50+ distinct entities across 5 categories  
- **Integration**: Zero breaking changes to existing code

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Lower accuracy than MCP | Medium | Focus on high-confidence, common entities |
| Performance degradation | Low | Optimize lookup algorithms, benchmark continuously |
| Maintenance overhead | Medium | Use YAML for easy updates, comprehensive tests |
| False positives | Medium | Strict word boundary checking, confidence thresholds |

## 🔄 Story Progress Tracking

- [ ] **Started**: Implementation begun
- [ ] **Entity Database**: YAML entity definitions created  
- [ ] **Core NER**: Pattern matching algorithm implemented
- [ ] **Integration**: Fallback logic integrated with enhanced processor
- [ ] **Performance**: Benchmarks meet requirements  
- [ ] **Testing**: Comprehensive test coverage
- [ ] **Documentation**: Configuration and usage documented
- [ ] **Validation**: Accuracy testing completed

## 📝 Implementation Notes

### **Entity Categories & Examples:**

#### **Deities (High Confidence: 0.9)**
- Krishna, Shiva, Vishnu, Rama, Hanuman
- Ganesha, Durga, Lakshmi, Saraswati  
- Variations: krsna/kṛṣṇa, siva/śiva, etc.

#### **Scriptures (Very High Confidence: 0.95)**  
- Bhagavad Gita, Upanishads, Vedas, Ramayana
- Mahabharata, Puranas, Tantras
- Common misspellings included

#### **Concepts (High Confidence: 0.85)**
- dharma, karma, yoga, moksha, samsara
- ahimsa, bhakti, jnana, maya
- Both Sanskrit and English contexts

#### **Places (Medium Confidence: 0.8)**
- Vrindavan, Ayodhya, Kashi, Haridwar  
- Rishikesh, Mathura, Dwarka
- Geographic and spiritual significance

#### **People (Medium Confidence: 0.75)**
- Arjuna, Yudhishthira, Sita, Hanuman
- Historical and mythological figures
- Context-dependent recognition

### **Design Principles:**
- **High Precision**: Better to miss some entities than create false positives
- **Fast Execution**: Optimized for real-time processing  
- **Easy Extension**: YAML-based configuration for non-developers
- **Graceful Degradation**: Always provides some level of NER capability

### **Future Enhancements:**
- Fuzzy matching for misspellings
- Context-aware entity disambiguation  
- Machine learning model integration
- Hierarchical entity relationships
- Confidence tuning based on usage statistics

---

**Dependencies**: None (independent implementation)  
**Estimated completion**: Day 5 of sprint