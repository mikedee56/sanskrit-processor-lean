# Lean Architecture Guidelines - Sanskrit Processor

## 🎯 **Core Lean Philosophy**

**Every story implementation MUST adhere to these principles. No exceptions.**

### **The Lean Commandments**

1. **🚫 NO NEW DEPENDENCIES** - Use only existing packages in `requirements.txt`
2. **📏 MINIMAL CODE** - Solve with fewer lines, not more  
3. **⚡ PERFORMANCE FIRST** - Maintain 2,600+ segments/second processing
4. **🧠 < 50MB MEMORY** - Stay under lean memory footprint
5. **🔧 SIMPLE CONFIG** - YAML only, no complex configuration systems
6. **📁 FLAT STRUCTURE** - Avoid deep module hierarchies
7. **❌ FAIL FAST** - Clear errors, no silent failures
8. **🔄 BACKWARD COMPATIBLE** - Never break existing APIs

---

## ✅ **Approved Patterns (USE THESE)**

### **Data Structures**
```python
# ✅ GOOD: Simple dataclasses
@dataclass
class ProcessingResult:
    segments_processed: int
    corrections_made: int

# ❌ BAD: Complex class hierarchies, multiple inheritance
```

### **Configuration**
```python
# ✅ GOOD: Direct YAML loading
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# ❌ BAD: Configuration frameworks, validation libraries
```

### **Error Handling**
```python
# ✅ GOOD: Explicit errors with context
if not input_file.exists():
    raise FileNotFoundError(f"Input file not found: {input_file}")

# ❌ BAD: Silent failures, generic exceptions
```

### **File Operations**
```python
# ✅ GOOD: Native pathlib and built-ins
from pathlib import Path
path = Path("data/cache.json")
data = json.loads(path.read_text())

# ❌ BAD: Additional file handling libraries
```

### **HTTP/API Calls**
```python
# ✅ GOOD: requests library (already in requirements)
response = requests.get(url, timeout=10)
response.raise_for_status()

# ❌ BAD: httpx, aiohttp, or other HTTP libraries
```

---

## ❌ **Forbidden Patterns (NEVER USE)**

### **Banned Dependencies**
```python
# ❌ BANNED: Heavy ML/NLP libraries
import spacy, nltk, transformers, tensorflow, torch

# ❌ BANNED: ORM frameworks  
import sqlalchemy, django, flask-sqlalchemy

# ❌ BANNED: Heavy fuzzy matching
import fuzzywuzzy, python-Levenshtein

# ❌ BANNED: Complex validation
import pydantic, cerberus, marshmallow

# ❌ BANNED: Additional web frameworks
import flask, fastapi, django
```

### **Banned Patterns**
```python
# ❌ BANNED: Abstract base classes for simple tasks
from abc import ABC, abstractmethod

# ❌ BANNED: Factories for straightforward objects
class ProcessorFactory:
    def create_processor(self): ...

# ❌ BANNED: Decorators for simple functionality  
@retry(times=3)
def process_text(): ...

# ❌ BANNED: Context managers for simple operations
with ProcessingContext() as ctx:
    ctx.process()
```

---

## 🔧 **Implementation Standards**

### **Code Simplicity Rules**

1. **One Purpose Per Function**: Each function does exactly one thing
2. **Maximum 50 Lines**: If a function is longer, split it
3. **Clear Variable Names**: `correction_count` not `cc`
4. **Minimal Nesting**: Maximum 3 levels of indentation
5. **Direct Logic**: Avoid clever tricks and complex algorithms

### **Performance Requirements**

```python
# ✅ Every story MUST pass these benchmarks:
def performance_test():
    # Processing speed
    assert segments_per_second > 2600
    
    # Memory usage  
    assert peak_memory_mb < 50
    
    # Response time for new features
    assert feature_response_time_ms < 100
    
    # File operations
    assert file_load_time_ms < 500
```

### **Memory Management**
```python
# ✅ GOOD: Efficient data handling
def process_large_file(file_path):
    # Process in chunks, don't load everything
    with open(file_path) as f:
        for chunk in iter(lambda: f.read(8192), ''):
            yield process_chunk(chunk)

# ❌ BAD: Loading everything into memory
def process_large_file(file_path):
    content = file_path.read_text()  # Could be huge!
    return process_all(content)
```

---

## 📊 **Story Validation Checklist**

**Before marking any story as ✅ Done, verify:**

### **Lean Compliance Check**
```markdown
- [ ] **No new dependencies** added to requirements.txt
- [ ] **Code size** < 200 lines for the entire story implementation
- [ ] **Performance** benchmarks still pass (>2600 seg/sec, <50MB)  
- [ ] **Configuration** uses existing YAML patterns only
- [ ] **Error handling** fails fast with clear messages
- [ ] **API compatibility** - no breaking changes
- [ ] **File structure** remains flat and simple
```

### **Code Quality Gates**
```python
# Run these checks before marking story complete:

# 1. Performance Gate
python -m timeit "process_sample_file()" 
# Must complete in < 1 second for 100 segments

# 2. Memory Gate  
import tracemalloc
tracemalloc.start()
# ... run processing ...
current, peak = tracemalloc.get_traced_memory()
assert peak < 50 * 1024 * 1024  # 50MB

# 3. Dependency Gate
pip freeze | wc -l  # Count should not increase

# 4. Line Count Gate
find . -name "*.py" -exec wc -l {} + | tail -1
# Should be < 1500 total lines (current: ~1286)
```

---

## 🏗️ **Architecture Decision Framework**

**When implementing any feature, ask:**

### **The 3 Lean Questions**
1. **Can we solve this without adding code?** (Configuration, data changes)
2. **Can we solve this with < 50 lines?** (Simple algorithm)  
3. **Will this break in 2 years?** (Avoid clever/complex solutions)

### **Complexity Budget**
```
Total Project Complexity Budget: 1,500 lines of Python
Current Usage: ~1,286 lines  
Remaining Budget: ~214 lines for ALL stories

Story Complexity Allocation:
- Story 1.1 (Verse Cache): ~80 lines max
- Story 1.2 (Fuzzy Match): ~40 lines max  
- Story 2.1 (Metrics): ~60 lines max
- Story 2.2 (Punctuation): ~30 lines max
- Story 3.1 (NER Fallback): ~70 lines max
- Story 4.1 (Lexicons): ~0 lines (data only)
- Story 4.2 (Batch Processing): ~100 lines max
```

---

## 🚨 **Red Flags - Stop Immediately If You See These**

### **Code Smells**
- Adding more than 100 lines for a single story
- Importing any library not in current `requirements.txt`
- Creating more than 2 new files per story
- Adding configuration validation logic
- Creating abstract classes or complex inheritance
- Using design patterns (Strategy, Factory, Observer, etc.)

### **Performance Degradation**
- Processing speed drops below 2,000 segments/second
- Memory usage exceeds 60MB during processing
- File loading takes more than 1 second
- Any operation takes more than 500ms to complete

### **Architectural Drift**
- Adding database systems (SQLite, PostgreSQL, etc.)
- Creating microservices or API endpoints
- Adding authentication/authorization systems
- Building web interfaces or dashboards  
- Creating complex logging frameworks

---

## 💡 **Lean Solutions Cookbook**

### **Common Challenges & Lean Solutions**

#### **"I need fuzzy string matching"**
```python
# ❌ WRONG: Add fuzzywuzzy dependency
from fuzzywuzzy import fuzz

# ✅ RIGHT: Simple character matching
def simple_similarity(s1, s2):
    matches = sum(a == b for a, b in zip(s1, s2))
    return matches / max(len(s1), len(s2))
```

#### **"I need a database for caching"**
```python
# ❌ WRONG: Add SQLite or Redis
import sqlite3

# ✅ RIGHT: JSON file caching  
cache = json.loads(Path("cache.json").read_text())
```

#### **"I need complex configuration validation"**
```python
# ❌ WRONG: Add pydantic or cerberus
from pydantic import BaseModel

# ✅ RIGHT: Simple dict checking with defaults
def load_config(config_path):
    config = yaml.safe_load(open(config_path))
    return {
        'enabled': config.get('enabled', True),
        'threshold': config.get('threshold', 0.8)
    }
```

#### **"I need background task processing"**
```python
# ❌ WRONG: Add Celery or background job systems  
from celery import Celery

# ✅ RIGHT: Simple sequential processing
for item in items:
    process_item(item)
    if should_stop():
        break
```

---

## 📋 **Story Implementation Template**

**Copy this template for every story implementation:**

```python
"""
Story X.X: [Story Name]
Implementation following Lean Architecture Guidelines

Lean Compliance:
- Dependencies: None added ✅  
- Code size: [X] lines ✅
- Performance: [X] segments/sec ✅
- Memory: [X] MB peak ✅
"""

# Imports ONLY from existing dependencies
import json
import yaml
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# Simple, focused implementation
class [ComponentName]:
    """[Brief description - one line only]"""
    
    def __init__(self, config_path: Path = None):
        """Simple initialization with minimal configuration."""
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Path) -> dict:
        """Load configuration using existing YAML patterns."""
        if not config_path or not config_path.exists():
            return {}
        return yaml.safe_load(config_path.read_text())
    
    def main_feature(self, input_data: str) -> tuple[str, int]:
        """
        Main feature implementation.
        Returns (result, operations_count) for metrics.
        """
        # Implementation in < 50 lines
        pass

# Performance validation
if __name__ == "__main__":
    # Quick performance check
    import time
    component = [ComponentName]()
    
    start = time.time()
    for i in range(1000):
        result = component.main_feature("test input")
    duration = time.time() - start
    
    print(f"Performance: {1000/duration:.0f} operations/second")
    assert duration < 1.0, "Performance regression detected!"
```

---

## 🎯 **Success Criteria**

**A story is only complete when:**

1. ✅ **All Lean Guidelines followed** (no exceptions)
2. ✅ **Performance benchmarks pass** (speed, memory, response time)  
3. ✅ **Complexity budget respected** (line count limits)
4. ✅ **Zero new dependencies** added
5. ✅ **Backward compatibility** maintained
6. ✅ **Clear, simple code** that any developer can understand

**Remember: It's better to deliver a simple, working solution than a complex, "perfect" one.** 

**Lean architecture is not about doing less - it's about doing the right things simply. 🎯**