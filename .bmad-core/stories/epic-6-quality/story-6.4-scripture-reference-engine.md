# Story 6.4: Scripture Reference Engine

**Epic**: Sanskrit Content Quality Excellence  
**Story Points**: 8  
**Priority**: Medium  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete Story 6.3 (Database Integration) first

## 📋 User Story

**As a** Sanskrit content processor handling scriptural quotes and verses  
**I want** automatic identification and referencing of scriptural passages  
**So that** verses are properly cited and users can find source references easily

## 🎯 Business Value

- **Academic Value**: Proper scripture citations for scholarly content
- **User Enhancement**: Viewers can lookup referenced verses
- **Content Enrichment**: 11k hours of lectures gain scriptural context
- **SEO/Searchability**: Content becomes more discoverable by verse references

## ✅ Acceptance Criteria

### **AC 1: Verse Recognition**
- [ ] **Bhagavad Gītā**: Identify verses with 90%+ accuracy for complete quotes
- [ ] **Major Upaniṣads**: Recognize common passages from key Upaniṣads
- [ ] **Fragment Recognition**: 70%+ accuracy for partial verse quotes
- [ ] **Confidence Scoring**: Each recognition includes confidence score

### **AC 2: Reference Generation**
- [ ] **Standard Citations**: "Bhagavad Gītā 2.56" format
- [ ] **Multiple Sources**: Cross-reference with different translations/editions  
- [ ] **Context Preservation**: Original text preserved, reference added to metadata
- [ ] **JSON Output**: Machine-readable scripture reference data

### **AC 3: Lean Implementation**
- [ ] **Code Limit**: Maximum 250 lines for scripture engine
- [ ] **Simple Database**: Verse database as SQLite (no complex systems)
- [ ] **Performance**: <100ms per verse recognition
- [ ] **Memory**: <20MB additional footprint

## 🏗️ Implementation Plan

### **Core Scripture Engine**
```python
# New: scripture/verse_engine.py (~180 lines)
class ScriptureReferenceEngine:
    def __init__(self, scripture_db_path: Path):
        self.db = sqlite3.connect(scripture_db_path)
        self.verse_cache = {}
        
    def identify_verses(self, text: str) -> List[ScriptureReference]:
        """Main verse identification with fuzzy matching."""
        # 1. Extract potential verse-like sentences
        # 2. Fuzzy match against scripture database
        # 3. Generate confidence scores
        # 4. Return top matches above threshold
        pass
        
    def fuzzy_match_verse(self, text: str, threshold: float = 0.8) -> Optional[ScriptureReference]:
        """Simple fuzzy verse matching using word overlap."""
        pass

@dataclass  
class ScriptureReference:
    source: str  # "Bhagavad Gītā"
    chapter: int
    verse: int  
    matched_text: str
    confidence: float
    citation: str  # "Bhagavad Gītā 2.56"
```

### **Verse Database Schema**
```sql
CREATE TABLE verses (
    id INTEGER PRIMARY KEY,
    source TEXT,  -- "Bhagavad Gītā"
    chapter INTEGER,
    verse INTEGER, 
    sanskrit TEXT,
    transliteration TEXT,
    translation TEXT,
    keywords TEXT  -- Space-separated for simple search
);
```

## 📁 Files to Create/Modify

### **New Files:**
- `scripture/verse_engine.py` - Core verse recognition (~180 lines)
- `data/scripture_verses.db` - Verse database (data, not code)
- `scripture/reference_formatter.py` - Citation formatting (~70 lines)

**Total Code**: ~250 lines (within limit)

## 📊 Success Metrics

- **Recognition Accuracy**: 90% complete verses, 70% fragments
- **Performance**: <100ms per text segment
- **Coverage**: 1000+ key verses from major scriptures
- **Integration**: JSON metadata output for verse references

## 🤖 Dev Agent Instructions

**LEAN FOCUS**: Simple fuzzy matching, SQLite database, essential verses only. Focus on Bhagavad Gītā first, expand later.

**Story Status**: ⏳ Ready for Implementation