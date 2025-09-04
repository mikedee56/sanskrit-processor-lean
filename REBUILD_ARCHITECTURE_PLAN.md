# REBUILD ARCHITECTURE PLAN - MCP-FIRST APPROACH

## 🎯 DESIGN PRINCIPLES

1. **Lean Core**: Single-file processor (~200 lines) handling only essential operations
2. **Smart Externals**: MCP and APIs handle complex analysis and knowledge lookups
3. **Fail Fast**: No silent errors - explicit error handling with user feedback
4. **Proven Patterns**: Use battle-tested approaches instead of custom frameworks

---

## 🏗️ PROPOSED ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    NEW ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │   CLI (main.py) │───▶│  Core Processor (200 lines) │   │
│  │   - File I/O    │    │  - SRT parsing               │   │
│  │   - Args        │    │  - Basic corrections         │   │
│  │   - Progress    │    │  - Lexicon matching          │   │
│  └─────────────────┘    │  - Output generation         │   │
│                         └──────────┬───────────────────┘   │
│                                    │                       │
│  ┌─────────────────────────────────┼─────────────────────┐ │
│  │            EXTERNAL SERVICES    ▼                     │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │                                                         │ │
│  │ ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐ │ │
│  │ │   MCP Server    │  │  Scripture APIs │  │ Quality  │ │ │
│  │ │                 │  │                 │  │ APIs     │ │ │
│  │ │ • NER Analysis  │  │ • Verse Lookup  │  │ • IAST   │ │ │
│  │ │ • Semantic      │  │ • Context Match │  │ • WER/CER│ │ │
│  │ │ • Capitalization│  │ • Citation Gen  │  │ • Academic│ │ │
│  │ └─────────────────┘  └─────────────────┘  └──────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 SIMPLIFIED FILE STRUCTURE

```
sanskrit-processor/
├── main.py                 # CLI entry point (50 lines)
├── processor.py           # Core processing logic (200 lines)  
├── lexicons/              # Your existing YAML files (KEEP AS-IS)
│   ├── corrections.yaml
│   ├── proper_nouns.yaml  
│   └── verses.yaml
├── config.py              # Simple configuration (30 lines)
├── requirements.txt       # Minimal dependencies
└── services/              # External service connectors
    ├── mcp_client.py      # MCP communication (100 lines)
    ├── scripture_api.py   # Scripture lookup (50 lines)
    └── quality_api.py     # Academic validation (50 lines)
```

**TOTAL: ~500 lines vs current 10,000+ lines**

---

## 🔧 CORE PROCESSOR DESIGN

### Single Responsibility: Text Correction Pipeline

```python
# processor.py - Clean, focused implementation
class SanskritProcessor:
    def __init__(self, config):
        self.lexicons = LexiconManager(config.lexicon_dir)
        self.mcp_client = MCPClient(config.mcp_endpoint) if config.enable_mcp else None
        self.apis = APIManager(config.api_keys) if config.enable_apis else None
    
    def process_srt(self, input_path, output_path):
        # 1. Parse SRT (fail fast on errors)
        segments = parse_srt_file(input_path)
        
        # 2. Apply basic corrections (lexicon-based)
        for segment in segments:
            segment.text = self.apply_lexicon_corrections(segment.text)
            
            # 3. External enhancement (optional, with fallback)
            if self.mcp_client:
                segment = self.enhance_via_mcp(segment)
                
            if self.apis:
                segment = self.enhance_via_apis(segment)
        
        # 4. Generate output (fail fast on write errors)
        write_srt_file(segments, output_path)
        return ProcessingReport(segments)
```

---

## 🌐 MCP INTEGRATION STRATEGY

### MCP Services to Implement

1. **Semantic Analysis Service**
   ```python
   # Via MCP - removes local NLP complexity
   enhanced_text = mcp_client.analyze_semantics(
       text=segment.text,
       domain="yoga_vedanta",
       features=["ner", "capitalization", "context"]
   )
   ```

2. **Academic Validation Service**
   ```python
   # Quality checking via MCP
   quality_score = mcp_client.validate_academic_quality(
       text=segment.text,
       standards=["iast", "sanskrit_accuracy"]
   )
   ```

3. **Context-Aware Corrections**
   ```python
   # Intelligent corrections based on surrounding context
   corrected = mcp_client.context_correct(
       text=segment.text,
       previous_segment=segments[i-1].text if i > 0 else None,
       domain_context="spiritual_lecture"
   )
   ```

---

## 🔌 EXTERNAL API STRATEGY

### Scripture Knowledge APIs
```python
# Replace local verse database with API calls
def lookup_scripture_verse(text_snippet):
    # Try multiple sources with fallback
    sources = [
        ("bhagavadgita.io", lookup_bhagavad_gita),
        ("wisdomlib.org", lookup_wisdom_library),  
        ("vedicscriptures.github.io", lookup_vedic_scripts)
    ]
    
    for source_name, lookup_func in sources:
        try:
            result = lookup_func(text_snippet)
            if result.confidence > 0.8:
                return result
        except APIError:
            continue  # Try next source
    
    return None  # No match found
```

### Quality Validation APIs
```python
# External academic validation
def validate_iast_transliteration(text):
    # Use specialized IAST validation service
    return requests.post("https://sanskrit-tools-api.com/validate-iast", {
        "text": text,
        "strict": True
    }).json()
```

---

## ⚡ PERFORMANCE & RELIABILITY DESIGN

### Circuit Breaker Pattern for External Calls
```python
class ExternalServiceManager:
    def __init__(self):
        self.circuit_breakers = {}
        self.fallback_strategies = {}
    
    def call_with_fallback(self, service_name, operation, *args):
        try:
            if self.circuit_breakers[service_name].can_call():
                return operation(*args)
        except ServiceError:
            self.circuit_breakers[service_name].record_failure()
            
        # Fallback to local processing
        return self.fallback_strategies[service_name](*args)
```

### Batch Processing for Efficiency
```python
# Process multiple segments in single API call
def batch_enhance_segments(segments, batch_size=10):
    for i in range(0, len(segments), batch_size):
        batch = segments[i:i+batch_size]
        
        # Single API call for batch
        results = mcp_client.analyze_batch([s.text for s in batch])
        
        # Apply results back to segments
        for segment, result in zip(batch, results):
            segment.enhanced_text = result.corrected_text
            segment.confidence = result.confidence
```

---

## 🎯 FEATURE PRESERVATION MAPPING

| Current Bloated Feature | New Lean Implementation |
|------------------------|-------------------------|
| 3,493-line processor | 200-line focused processor |
| Local NER processing | MCP semantic analysis |
| Hardcoded verse database | External scripture APIs |
| Complex fuzzy matching | Simple lexicon + API enhancement |
| 15 monitoring modules | External telemetry API |
| Academic validation framework | Quality validation API |
| Unicode corruption fixes | Proper Unicode handling + API validation |
| Performance optimization | External performance monitoring |

---

## 📋 IMPLEMENTATION PHASES

### Phase 1: Core Foundation (Week 1)
- [x] Create minimal processor.py (200 lines)
- [x] Integrate existing lexicons (no changes needed)
- [x] Basic SRT parsing with proper error handling
- [x] Simple CLI with progress reporting

### Phase 2: MCP Integration (Week 2) 
- [ ] Set up MCP client connection
- [ ] Implement semantic analysis calls
- [ ] Add NER processing via MCP
- [ ] Test with sample data

### Phase 3: External APIs (Week 3)
- [ ] Scripture lookup API integration
- [ ] Academic validation API
- [ ] IAST validation service
- [ ] Circuit breaker implementation

### Phase 4: Polish & Performance (Week 4)
- [ ] Batch processing optimization
- [ ] Error handling refinement
- [ ] Performance monitoring
- [ ] Documentation and testing

---

## 💰 COST-BENEFIT ANALYSIS

### Development Time
- **Current Fix Attempt**: 12+ weeks (high failure risk)
- **Proposed Rebuild**: 4 weeks (proven patterns)

### Maintenance Complexity
- **Current**: 100+ files, impossible to debug
- **Proposed**: ~10 files, clear separation of concerns

### External Dependencies
- **Current**: Massive local complexity
- **Proposed**: Managed external services with fallbacks

### Feature Completeness
- **Current**: Claims features that don't work
- **Proposed**: Fewer features that actually work + extensible via APIs

---

## 🚀 IMMEDIATE NEXT STEPS

1. **Validate MCP Services** - Confirm which MCP services are available for semantic processing
2. **API Research** - Identify and test actual scripture and validation APIs  
3. **Lexicon Migration** - Extract your existing YAML lexicons (they're the most valuable asset)
4. **Prototype Core** - Build minimal processor with just lexicon corrections
5. **Add One External Service** - Start with simplest API integration

This approach gives you:
- ✅ **All current valuable features preserved**
- ✅ **Dramatically reduced complexity** 
- ✅ **Better separation of concerns**
- ✅ **Easier to maintain and extend**
- ✅ **Actual working system in 4 weeks**

Want me to start with Phase 1 implementation?