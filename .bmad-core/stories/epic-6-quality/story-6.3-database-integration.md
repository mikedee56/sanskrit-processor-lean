# Story 6.3: Database Integration System

**Epic**: Sanskrit Content Quality Excellence  
**Story Points**: 13  
**Priority**: High  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation  
⚠️ **DEPENDENCY**: Complete Stories 6.1 and 6.2 first  
⚠️ **HIGH VALUE**: Connects to existing 1000+ term database for massive quality improvement

## 📋 User Story

**As a** Sanskrit content processor with access to 1000+ existing terms in a database  
**I want** seamless integration with the existing term database while maintaining YAML fallback  
**So that** processing quality improves dramatically without losing lean architecture principles

## 🎯 Business Value

- **Massive Quality Improvement**: 1000+ terms vs current 425 YAML entries
- **Database Leverage**: Use existing investment in term database
- **Scalable Foundation**: Handle 10,000+ terms for 11k hours of content
- **Fallback Resilience**: Graceful degradation if database unavailable
- **Future-Proof Architecture**: Foundation for continued term expansion

## ✅ Acceptance Criteria

### **AC 1: Database Connectivity**
- [ ] **SQLite Integration**: Connect to existing term database (lean choice, no server)
- [ ] **Connection Pooling**: Simple connection management for performance
- [ ] **Query Optimization**: Efficient term lookup with minimal latency
- [ ] **Graceful Fallback**: Fall back to YAML lexicons if database unavailable

### **AC 2: Term Database Schema Support**
- [ ] **Existing Schema Compatibility**: Work with current database structure
- [ ] **Compound Term Support**: Handle multi-word terms from database
- [ ] **Metadata Integration**: Use confidence scores, categories, contexts from DB
- [ ] **Version Management**: Handle database updates without breaking processing

### **AC 3: Hybrid Lexicon System**
- [ ] **Database First**: Check database before YAML lexicons
- [ ] **YAML Fallback**: Use YAML if term not found in database
- [ ] **Cache Integration**: Work with existing smart caching system (Story 5.9)
- [ ] **Performance Priority**: Database queries must not slow processing <1,500 seg/sec

### **AC 4: Lean Implementation Requirements**
- [ ] **Code Limit**: Maximum 200 lines for entire database integration
- [ ] **Minimal Dependencies**: Only SQLite (Python stdlib), no ORM frameworks
- [ ] **Memory Efficient**: <15MB additional memory footprint
- [ ] **Simple Configuration**: Database path in YAML config only
- [ ] **Backward Compatible**: All existing YAML functionality preserved

## 🏗️ Implementation Plan

### **Phase 1: Database Connection Layer (Day 1-2)**

#### **Lean Database Connector**
```python
# New: database/lexicon_db.py (~80 lines)
import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

@dataclass
class DatabaseTerm:
    """Lean data structure for database terms."""
    original_term: str
    variations: List[str]
    transliteration: str
    category: str
    confidence: float
    context_clues: List[str] = None
    is_compound: bool = False

class LexiconDatabase:
    """
    Lightweight SQLite database integration for Sanskrit terms.
    Maintains lean architecture with simple queries and fallback.
    """
    
    def __init__(self, db_path: Path, enable_fallback: bool = True):
        self.db_path = db_path
        self.enable_fallback = enable_fallback
        self._connection = None
        self._term_cache = {}  # Simple in-memory cache
        
    def connect(self) -> bool:
        """Simple database connection with error handling."""
        try:
            if self.db_path.exists():
                self._connection = sqlite3.connect(str(self.db_path))
                self._connection.row_factory = sqlite3.Row  # Dict-like access
                return True
        except sqlite3.Error:
            pass
        return False
        
    def lookup_term(self, term: str) -> Optional[DatabaseTerm]:
        """
        Fast term lookup with caching.
        Returns None if term not found.
        """
        term_lower = term.lower().strip()
        
        # Check simple cache first
        if term_lower in self._term_cache:
            return self._term_cache[term_lower]
            
        # Database query
        if self._connection:
            try:
                cursor = self._connection.cursor()
                
                # Query for exact match or variation match
                query = """
                SELECT original_term, variations, transliteration, category, 
                       confidence, context_clues, is_compound
                FROM terms 
                WHERE LOWER(original_term) = ? 
                   OR LOWER(variations) LIKE ?
                LIMIT 1
                """
                
                cursor.execute(query, (term_lower, f'%{term_lower}%'))
                row = cursor.fetchone()
                
                if row:
                    # Parse JSON fields safely
                    variations = json.loads(row['variations']) if row['variations'] else []
                    context_clues = json.loads(row['context_clues']) if row['context_clues'] else []
                    
                    db_term = DatabaseTerm(
                        original_term=row['original_term'],
                        variations=variations,
                        transliteration=row['transliteration'],
                        category=row['category'],
                        confidence=row['confidence'],
                        context_clues=context_clues,
                        is_compound=bool(row['is_compound'])
                    )
                    
                    # Cache result
                    self._term_cache[term_lower] = db_term
                    return db_term
                    
            except (sqlite3.Error, json.JSONDecodeError, KeyError):
                # Database error - fallback will handle
                pass
                
        return None
        
    def close(self):
        """Clean up database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
```

### **Phase 2: Hybrid Lexicon Manager (Day 3-4)**

#### **Database + YAML Integration**
```python
# New: lexicons/hybrid_lexicon_loader.py (~120 lines)
class HybridLexiconLoader:
    """
    Combines database and YAML lexicon sources.
    Database first, YAML fallback, maintains existing API.
    """
    
    def __init__(self, lexicon_dir: Path, config: dict):
        # Initialize database connection
        db_path = config.get('database', {}).get('path')
        self.database = None
        
        if db_path:
            db_path = Path(db_path)
            self.database = LexiconDatabase(db_path)
            self.database.connect()
            
        # Initialize YAML fallback (existing system)
        from sanskrit_processor_v2 import LexiconLoader
        self.yaml_loader = LexiconLoader(lexicon_dir)
        
        # Statistics
        self.stats = {
            'database_hits': 0,
            'yaml_hits': 0,
            'misses': 0
        }
        
    def get_correction(self, term: str) -> Optional[str]:
        """
        Unified correction lookup: database first, YAML fallback.
        Maintains existing API for compatibility.
        """
        # Try database first
        if self.database:
            db_result = self.database.lookup_term(term)
            if db_result:
                self.stats['database_hits'] += 1
                return db_result.original_term if db_result.confidence >= 0.7 else None
                
        # Fallback to YAML
        yaml_result = self.yaml_loader.get_correction(term)
        if yaml_result:
            self.stats['yaml_hits'] += 1
            return yaml_result
            
        self.stats['misses'] += 1
        return None
        
    def get_proper_noun(self, term: str) -> Optional[str]:
        """Similar hybrid approach for proper nouns."""
        # Database lookup first
        if self.database:
            db_result = self.database.lookup_term(term)
            if db_result and db_result.category in ['deity', 'person', 'place']:
                self.stats['database_hits'] += 1
                return db_result.original_term
                
        # YAML fallback
        yaml_result = self.yaml_loader.get_proper_noun(term)
        if yaml_result:
            self.stats['yaml_hits'] += 1
            return yaml_result
            
        self.stats['misses'] += 1
        return None
        
    def get_compound_terms(self, text: str) -> List[DatabaseTerm]:
        """
        New functionality: get compound terms from database.
        Used by Story 6.1 compound recognition system.
        """
        compound_terms = []
        
        if self.database:
            # Simple sliding window approach for compound detection
            words = text.split()
            for i in range(len(words)):
                # Check 2-5 word combinations
                for j in range(i + 2, min(i + 6, len(words) + 1)):
                    phrase = ' '.join(words[i:j])
                    
                    db_result = self.database.lookup_term(phrase)
                    if db_result and db_result.is_compound:
                        compound_terms.append(db_result)
                        
        return compound_terms
        
    def get_stats(self) -> dict:
        """Return lookup statistics for monitoring."""
        total = sum(self.stats.values())
        if total == 0:
            return self.stats
            
        return {
            **self.stats,
            'database_hit_rate': self.stats['database_hits'] / total * 100,
            'yaml_hit_rate': self.stats['yaml_hits'] / total * 100,
            'total_lookups': total
        }
```

### **Phase 3: Integration & Performance Optimization (Day 5)**

#### **Main Processor Integration**
```python
# Modified: sanskrit_processor_v2.py (modify ~30 lines)
class SanskritProcessor:
    def __init__(self, lexicon_dir: Path, config: dict = None):
        self.config = config or {}
        
        # Use hybrid lexicon system instead of simple YAML loader
        from lexicons.hybrid_lexicon_loader import HybridLexiconLoader
        self.lexicon_loader = HybridLexiconLoader(lexicon_dir, self.config)
        
        # Rest of initialization remains the same...
        
    def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
        """Enhanced with database integration - API unchanged."""
        # Existing logic works with new hybrid loader
        # get_correction() and get_proper_noun() maintain same API
        pass
        
    def close(self):
        """Clean up database connections."""
        if hasattr(self.lexicon_loader, 'database') and self.lexicon_loader.database:
            self.lexicon_loader.database.close()
```

## 📁 Files to Create/Modify

### **New Files:**
- `database/lexicon_db.py` - Database connection and queries (~80 lines)
- `lexicons/hybrid_lexicon_loader.py` - Database + YAML integration (~120 lines)

### **Modified Files:**
- `sanskrit_processor_v2.py` - Integration with hybrid loader (~30 lines modified)
- `config.yaml` - Database configuration section

### **Configuration Changes:**
```yaml
# Enhanced config.yaml
database:
  enabled: true
  path: "data/sanskrit_terms.db"  # Path to existing database
  fallback_to_yaml: true
  connection_timeout: 5.0
  cache_size: 1000  # In-memory term cache
```

### **Code Budget:**
- **Total New Code**: ~200 lines (within story limit)
- **Modified Code**: ~30 lines (minimal integration changes)
- **Database Schema**: Assumes existing structure (no schema changes)

## 🔧 Technical Specifications

### **Database Schema Expectations**
```sql
-- Expected existing table structure
CREATE TABLE terms (
    id INTEGER PRIMARY KEY,
    original_term TEXT NOT NULL,
    variations TEXT,  -- JSON array of variations
    transliteration TEXT,
    category TEXT,
    confidence REAL,
    context_clues TEXT,  -- JSON array
    is_compound BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expected indexes for performance
CREATE INDEX idx_terms_original ON terms(original_term);
CREATE INDEX idx_terms_variations ON terms(variations);
CREATE INDEX idx_terms_compound ON terms(is_compound);
```

### **Fallback Strategy**
```python
def get_term_with_fallback(term: str) -> Optional[str]:
    """
    Fallback hierarchy:
    1. Database lookup (if available)
    2. YAML lexicon lookup  
    3. Return None (no correction)
    
    Ensures system never fails due to database issues.
    """
    try:
        # Database first
        if database_available():
            result = database_lookup(term)
            if result and result.confidence >= 0.7:
                return result.original_term
    except DatabaseError:
        # Log error but continue with fallback
        pass
        
    # YAML fallback
    try:
        return yaml_lookup(term)
    except YAMLError:
        pass
        
    return None  # No correction found
```

## 🧪 Test Cases

### **Critical Test Cases**
```python
def test_database_integration():
    config = {'database': {'path': 'test_terms.db', 'enabled': True}}
    loader = HybridLexiconLoader("lexicons", config)
    
    # Test Case 1: Database hit
    result = loader.get_correction("krishna")
    assert result == "Kṛṣṇa"  # From database
    
    # Test Case 2: YAML fallback
    result = loader.get_correction("yoga")  
    assert result == "yoga"  # From YAML
    
    # Test Case 3: Database unavailable fallback
    loader.database = None
    result = loader.get_correction("dharma")
    assert result is not None  # Should still work via YAML

def test_compound_terms():
    loader = HybridLexiconLoader("lexicons", config)
    
    # Test compound term from database
    compounds = loader.get_compound_terms("srimad bhagavad gita chapter 2")
    assert len(compounds) > 0
    assert any(c.original_term == "Śrīmad Bhagavad Gītā" for c in compounds)

def test_performance():
    loader = HybridLexiconLoader("lexicons", config)
    
    # Performance test: 1000 lookups should be fast
    import time
    start = time.time()
    for i in range(1000):
        loader.get_correction(f"test_term_{i % 100}")
    duration = time.time() - start
    
    assert duration < 2.0  # Should complete in under 2 seconds
```

### **Edge Cases**
```python
def test_database_edge_cases():
    # Database corruption handling
    # Invalid JSON in database fields
    # Network timeout scenarios (if using network DB)
    # Concurrent access patterns
    # Memory usage with large result sets
    pass
```

## 📊 Success Metrics

### **Quality Improvements**
- **Term Coverage**: 1000+ terms available (vs current 425)
- **Lookup Success**: 85%+ term recognition rate (vs current ~60%)
- **Compound Recognition**: 95%+ for database compound terms
- **Fallback Reliability**: 100% fallback to YAML when database unavailable

### **Performance Requirements**
- **Lookup Speed**: <5ms per database query (cached)
- **Processing Speed**: ≥1,500 segments/second maintained
- **Memory Usage**: +12MB maximum (total <92MB vs current <80MB)
- **Database Connection**: <500ms initial connection time

### **Integration Success**
- **API Compatibility**: 100% backward compatible with existing YAML system
- **Cache Integration**: Works with existing smart caching (Story 5.9)
- **Error Handling**: Graceful degradation in all failure scenarios
- **Configuration**: Simple YAML configuration, no complex setup

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Database Unavailable** | Medium | Robust YAML fallback system |
| **Performance Degradation** | High | Connection pooling, caching, query optimization |
| **Schema Changes** | Medium | Flexible query structure, version detection |
| **Memory Usage Growth** | Medium | Limited cache size, connection cleanup |
| **Data Corruption** | Low | Read-only access, transaction safety |

## 🔄 Story Progress Tracking

- [ ] **Started**: Database integration implementation begun
- [ ] **Database Connection**: SQLite connector working with fallback
- [ ] **Hybrid Loader**: Database + YAML integration complete
- [ ] **Performance Optimization**: Query caching and optimization done
- [ ] **Integration Testing**: Works with existing processor
- [ ] **Fallback Validation**: YAML fallback tested and working
- [ ] **Performance Validated**: Meets speed/memory requirements
- [ ] **Quality Improvement**: 1000+ terms accessible and improving results

## 📝 Implementation Notes

### **Lean Architecture Compliance:**

#### **Why This Approach is Lean:**
1. **SQLite Only**: No database server, no ORM framework, minimal complexity
2. **Fallback Design**: Never breaks existing functionality
3. **Simple Queries**: Direct SQL, no query builders or complex abstractions
4. **Minimal Configuration**: Single database path in YAML
5. **API Preservation**: Existing code continues to work unchanged

#### **Database Design Philosophy:**
- **Read-Only**: Processor only reads, never writes to database
- **Simple Schema**: Work with existing structure, no complex relationships
- **Local First**: SQLite file, no network dependencies
- **Cache-Friendly**: Simple in-memory caching for repeated queries
- **Error-Tolerant**: Any database error falls back to YAML gracefully

#### **Performance Strategy:**
- **Connection Reuse**: Single connection per processor instance
- **Query Optimization**: Simple indexes on key lookup fields
- **Memory Bounds**: Limited cache size prevents memory bloat
- **Fast Fallback**: YAML lookup when database query fails or is slow

### **Success Criteria for Story Completion:**
1. ✅ **Database Integration**: 1000+ terms accessible from existing database
2. ✅ **Fallback Reliability**: System never breaks when database unavailable
3. ✅ **Performance Maintained**: >1,500 segments/second processing speed
4. ✅ **Lean Compliance**: <200 lines, SQLite only, simple configuration
5. ✅ **Quality Improvement**: Significant increase in term recognition rate

**Story Definition of Done**: The existing 1000+ term database is seamlessly integrated while maintaining lean architecture, performance, and complete fallback reliability.

---

## 🤖 Dev Agent Instructions

**IMPLEMENTATION PRIORITY**: This story provides the foundation for massive quality improvements by connecting to existing term investments.

**LEAN IMPLEMENTATION APPROACH**:
1. Start with simple SQLite connector using stdlib only
2. Implement hybrid loader maintaining existing API
3. Add graceful fallback to YAML for all failure scenarios
4. Test performance with realistic database sizes
5. Ensure memory usage remains bounded

**CRITICAL SUCCESS FACTORS**:
- Must integrate with existing 1000+ term database
- Must maintain 100% backward compatibility with YAML
- Must never break processing when database unavailable
- Must stay within 200-line code budget
- Must maintain >1,500 segments/second performance

**Story Status**: ⏳ Ready for Implementation