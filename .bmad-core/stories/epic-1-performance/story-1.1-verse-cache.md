# Story 1.1: Local Verse Cache System

**Epic**: Performance & Reliability  
**Story Points**: 5  
**Priority**: High  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** content processor  
**I want** offline verse lookup capability  
**So that** processing continues without internet dependency and verse lookups are faster

## 🎯 Business Value

- **Reliability**: Processing works offline once cache is populated
- **Performance**: Local lookups are 10x faster than API calls  
- **Cost**: Reduces external API usage
- **User Experience**: No delays from network latency

## ✅ Acceptance Criteria

### **AC 1: Verse Data Download**
- [ ] Download complete Bhagavad Gita verse data from GitHub API
- [ ] Store in `data/verse_cache.json` with proper structure
- [ ] Include: chapter, verse, Sanskrit text, transliteration, translation
- [ ] Handle network errors gracefully with retry logic
- [ ] One-time download on first usage

### **AC 2: Pattern Matching**  
- [ ] Detect verse references in multiple formats:
  - "Chapter 2, verse 47" or "Chapter 2 verse 47"
  - "Bhagavad Gita 2.47" or "BG 2.47" 
  - "Gita 2:47"
  - "2.47" when in context
- [ ] Case-insensitive matching
- [ ] Handle variations like "ch 2 v 47", "second chapter, verse forty-seven"

### **AC 3: Lookup Functionality**
- [ ] Fast verse retrieval by chapter/verse numbers
- [ ] Return structured verse data with confidence score
- [ ] Content search within verse translations for keywords
- [ ] Limit results to top 5 matches for content search

### **AC 4: Fallback Integration**
- [ ] Use cache first, external API as fallback
- [ ] Seamless integration with existing `api_client.py`
- [ ] No breaking changes to current API
- [ ] Maintain existing circuit breaker patterns

### **AC 5: Cache Management**
- [ ] Cache expiry after 30 days (configurable)
- [ ] Manual cache refresh capability
- [ ] Size-optimized storage (< 5MB cache file)
- [ ] Validate cache integrity on load

## 🏗️ Implementation Plan

### **Phase 1: Data Structure (1 hour)**
```python
@dataclass
class CachedVerse:
    chapter: int
    verse: int
    sanskrit: str
    transliteration: str 
    translation: str
    keywords: List[str]  # Extracted for search
```

### **Phase 2: Download Logic (1 hour)**
```python
class VerseCache:
    def download_verses(self) -> bool:
        # GitHub API: https://raw.githubusercontent.com/gita/gita/main/data/
        # Download all chapters and verses
        # Extract keywords from translations
        # Save to JSON with metadata
```

### **Phase 3: Pattern Matching (1 hour)**
```python
def detect_verse_references(self, text: str) -> List[Tuple[int, int]]:
    # Multiple regex patterns
    # Return (chapter, verse) tuples
    # Handle edge cases and validation
```

### **Phase 4: Integration (1 hour)**
```python
# Modify enhanced_processor.py to use cache first
# Fallback to external API if needed
# Maintain existing interface
```

### **Phase 5: Testing (1 hour)**
```python
# Unit tests for pattern matching
# Integration tests with real SRT files
# Performance benchmarking
```

## 📁 Files to Create/Modify

### **New Files:**
- `services/verse_cache.py` - Main cache implementation
- `data/verse_cache.json` - Generated cache file  
- `tests/test_verse_cache.py` - Unit tests

### **Modified Files:**
- `services/enhanced_api_client.py` - Integration with cache
- `config.yaml` - Cache configuration options
- `README.md` - Document new feature

## 🔧 Technical Specifications

### **API Endpoints:**
- **GitHub Base**: `https://raw.githubusercontent.com/gita/gita/main/data/`
- **Chapters**: `chapters.json` 
- **Verses**: `verses/{chapter}.json`

### **Cache File Structure:**
```json
{
  "metadata": {
    "created": "2025-01-09T10:00:00Z",
    "expires": "2025-02-08T10:00:00Z", 
    "version": "1.0",
    "total_verses": 700
  },
  "verses": {
    "2.47": {
      "chapter": 2, "verse": 47,
      "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
      "transliteration": "karmaṇy-evādhikāras te mā phaleṣu kadācana",
      "translation": "You have the right to perform your prescribed duty...",
      "keywords": ["duty", "action", "fruit", "right", "work"]
    }
  }
}
```

### **Performance Requirements:**
- Cache loading: < 500ms
- Verse lookup: < 1ms  
- Pattern matching: < 10ms per text segment
- Memory footprint: < 10MB

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_pattern_detection():
    assert detect_verse_references("Chapter 2, verse 47") == [(2, 47)]
    assert detect_verse_references("BG 2.47 and 4.7") == [(2, 47), (4, 7)]
    
def test_verse_lookup():
    verse = cache.get_verse(2, 47)
    assert verse.sanskrit.startswith("कर्मण्येवाधिकारस्ते")
    
def test_keyword_search():
    results = cache.search_content("duty action")
    assert len(results) > 0
    assert results[0].chapter == 2
```

### **Integration Tests:**
```python
def test_cache_fallback():
    # Test with empty cache -> should download
    # Test with populated cache -> should use cache
    # Test with network error -> should handle gracefully
```

## 📊 Success Metrics

- **Cache Hit Rate**: > 90% of verse lookups from cache
- **Performance Improvement**: 10x faster than API calls
- **Reliability**: 100% offline operation after initial download
- **Storage Efficiency**: < 5MB cache size
- **User Experience**: No noticeable delay in processing

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API rate limits | Medium | Implement exponential backoff, one-time download |
| Large cache size | Low | Compress data, extract only essential fields |
| Cache corruption | Medium | Validate integrity on load, auto-refresh on error |
| Network failures | High | Graceful fallback to external API |

## 🔄 Story Progress Tracking

- [ ] **Started**: Implementation begun
- [ ] **Data Structure**: CachedVerse class created  
- [ ] **Download Logic**: GitHub API integration working
- [ ] **Pattern Matching**: All verse reference formats detected
- [ ] **Integration**: Seamless fallback implemented
- [ ] **Testing**: All tests passing
- [ ] **Documentation**: README updated
- [ ] **Performance**: Benchmarks meet requirements  

## 📝 Notes

- Consider using compressed JSON or msgpack for larger datasets
- Implement background cache refresh for better UX
- Add metrics for cache hit/miss rates
- Future enhancement: Support for other scriptures (Upanishads, etc.)

---

**Ready to implement when**: Previous story completed  
**Estimated completion**: Day 1 of sprint