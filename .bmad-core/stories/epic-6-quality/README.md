# Epic 6: Sanskrit Content Quality Excellence

## 🎯 Epic Goal
Transform the Sanskrit SRT Processor from 75% to 95%+ content quality while maintaining lean architecture principles. Focus on sacred text preservation, intelligent term recognition, scripture reference capabilities, and production-ready output for 11k hours of content.

## 📊 Epic Status

**Epic Duration:** 6-7 Weeks  
**Start Date:** TBD  
**Current Status:** ⚠️ 90% Functional - Major Issues Fixed, Minor Tuning Needed

### Overall Progress: 5/7 Stories Functional (90% Quality Restored)

| Story | Points | Priority | Status | Core Focus |
|-------|--------|----------|--------|------------|
| **6.1: Compound Term Recognition** | 8 | High | ⚠️ 90% Working | 9/10 tests pass - minor diacritic issue |
| **6.2: Sacred Text Preservation** | 5 | High | ✅ Working | Sacred content classification active |
| **6.3: Database Integration** | 13 | High | ✅ Fixed & Working | Database query bug fixed, 425 terms loaded |
| **6.4: Scripture Reference Engine** | 8 | Medium | ❌ Not Tested | Scripture detection unknown status |
| **6.5: Context-Aware Processing** | 13 | High | ✅ Working | 17/17 tests pass, pipeline operational |
| **6.6: Quality Assurance System** | 8 | Medium | ❌ Not Tested | QA system unknown status |
| **6.7: Platform Output Formats** | 5 | Low | ✅ Working | 9/9 tests pass, all formats functional |

**Total Epic Points:** 60 (Large Epic - Major Quality Transformation)

## 🔥 **Quality Problems Being Solved**

### **Critical Issues from Recent Analysis:**
1. **Incomplete Title Corrections**: "Srimad Bhagavad Gita" → "Srimad bhagavad gita" (FAILED)
2. **Sacred Formatting Destruction**: Mantras lose structure (`|` → `?`, line breaks lost)
3. **Context Ignorance**: "bhagavad gita" vs "the Bhagavad Gītā" processed identically
4. **Limited Term Coverage**: Missing compound terms and complete scriptural titles
5. **Symbol Substitution**: Sacred symbols inappropriately changed
6. **No Scripture Recognition**: Verses processed as regular text, no references

### **Target Quality Improvements:**
- **Title Accuracy**: 95%+ (vs current ~60%)
- **Sacred Text Preservation**: 98%+ (vs current ~40%)
- **Compound Terms**: 90%+ recognition (vs current ~60%)
- **Scripture References**: 90% complete verse identification, 70% fragments
- **Overall Content Quality**: 95%+ (vs current ~75%)

## 🗓️ Implementation Schedule

### **Phase 1 - Foundation (Weeks 1-2): Critical Quality**
**Week 1:**
- [ ] **Story 6.1**: Compound Term Recognition (8 pts) - *Fix title capitalization issues*
- [ ] **Story 6.2**: Sacred Text Preservation (5 pts) - *Protect mantras and verses*

**Week 2:**  
- [ ] **Story 6.3**: Database Integration (13 pts) - *Connect existing 1000+ terms*

### **Phase 2 - Intelligence (Weeks 3-4): Smart Processing**
**Week 3:**
- [ ] **Story 6.4**: Scripture Reference Engine (8 pts) - *Auto-identify verses/quotes*

**Week 4:**
- [ ] **Story 6.5**: Context-Aware Processing (13 pts) - *Specialized routing system*

### **Phase 3 - Production (Weeks 5-6): Quality & Output**
**Week 5:**
- [ ] **Story 6.6**: Quality Assurance System (8 pts) - *Confidence & flagging*

**Week 6 (Optional Bonus):**
- [ ] **Story 6.7**: Platform Output Formats (3 pts) - *YouTube, publishing, apps*

## 🏗️ **Architectural Approach**

### **Lean Architecture Compliance:**
- **Total Code Budget**: ~1,200 additional lines (within lean guidelines)
- **No New Dependencies**: Use only stdlib + existing PyYAML, requests
- **Performance Target**: 1,500+ segments/second (acceptable trade-off for quality)
- **Memory Target**: <150MB (increased but manageable)
- **Modular Design**: Each story adds focused capability without bloat

### **Code Distribution:**
```
Story 6.1 - Compound Terms:     ~150 lines
Story 6.2 - Sacred Preservation: ~180 lines  
Story 6.3 - Database Integration: ~200 lines
Story 6.4 - Scripture Engine:    ~250 lines
Story 6.5 - Context Processing:  ~300 lines
Story 6.6 - Quality Assurance:   ~200 lines
Story 6.7 - Output Formats:     ~120 lines
Total New Code:                 ~1,400 lines (within 1,500 limit)
```

## 🎯 Success Metrics

### **Quality Metrics:**
- **Title Corrections**: "Śrīmad Bhagavad Gītā" properly capitalized ✅
- **Sacred Text Integrity**: Mantras preserve original structure ✅
- **Scripture Identification**: 90% verse recognition rate ✅
- **Compound Terms**: "Advaita Vedānta" recognized as single unit ✅
- **Context Awareness**: Proper nouns vs common words distinguished ✅

### **Performance Metrics:**
- **Processing Speed**: ≥1,500 segments/second (vs current 2,600+)
- **Memory Usage**: ≤150MB peak (vs current <80MB)
- **Quality Score**: ≥95% for known content (vs current ~75%)
- **Sacred Preservation**: ≥98% formatting accuracy
- **Error Rate**: ≤5% false corrections (currently ~25%)

### **Production Readiness:**
- **11k Hours Ready**: Can process vast content libraries efficiently
- **Platform Support**: Output formats for YouTube, books, apps
- **Quality Flagging**: JSON reports for human review workflow
- **Database Scalability**: Handle 10,000+ terms efficiently

## 📊 Current vs Target State

| Aspect | Current State | Target State | Story |
|--------|---------------|--------------|--------|
| **Title Handling** | "srimad bhagavad gita" | "Śrīmad Bhagavad Gītā" | 6.1 |
| **Sacred Symbols** | `\|` → `?` | `\|` preserved | 6.2 |
| **Term Database** | 425 YAML entries | 1000+ database terms | 6.3 |
| **Scripture Refs** | None | Auto-identified with citations | 6.4 |
| **Context Handling** | Single processor | Specialized routing | 6.5 |
| **Quality Flagging** | None | JSON confidence scoring | 6.6 |
| **Output Formats** | SRT only | SRT, VTT, JSON, XML | 6.7 |

## 🚨 Epic-Level Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Performance Degradation** | Medium | High | Benchmark every story, maintain >1,500 seg/sec |
| **Memory Bloat** | Medium | Medium | Profile each addition, cap at 150MB |
| **Complexity Creep** | High | High | Strict code reviews, maintain <1,500 total lines |
| **Database Dependency** | Low | Medium | Design for graceful fallback to YAML |
| **Integration Difficulties** | Medium | Medium | Modular design, extensive testing |

## 🎭 **User Personas Served**

### **Primary: Content Producer**
- **Need**: Process 11k hours of Sanskrit lectures efficiently
- **Benefit**: 95% quality automated processing, minimal human review
- **Output**: Production-ready subtitles for YouTube, books, apps

### **Secondary: Academic Publisher**  
- **Need**: Scholarly accuracy with proper IAST formatting
- **Benefit**: Scripture references, sacred text preservation
- **Output**: Publication-ready text with citations

### **Tertiary: App Developer**
- **Need**: Structured data for interactive applications
- **Benefit**: JSON output with confidence scores, metadata
- **Output**: API-ready content with quality metrics

## 📋 Story Execution Order

### **Critical Path (Must Complete):**
1. **Story 6.1** → **Story 6.2** → **Story 6.3** → **Story 6.5** → **Story 6.6**

### **Parallel Development Possible:**
- Story 6.4 (Scripture Engine) can be developed in parallel with 6.5 (Context Processing)
- Story 6.7 (Output Formats) can be developed anytime after 6.6

### **Minimum Viable Epic:**
Complete Stories 6.1, 6.2, 6.3, and 6.5 for 85% of the quality improvement.

## 🔄 Session Restart Instructions

When restarting development:

1. **Load Epic Status**: Read this README.md for progress
2. **Review Lean Guidelines**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` 
3. **Check Current Story**: Look at the next ⏳ Todo story
4. **Load Story Context**: Read the specific story file
5. **Quality Focus**: Remember we're solving specific quality gaps identified in processing analysis
6. **Performance Budget**: Maintain >1,500 seg/sec, <150MB memory

## 📈 Definition of Epic Done

**This epic is complete when:**

1. ✅ **Quality Score ≥95%** for known Sanskrit terms and proper nouns
2. ✅ **Sacred Text Preservation ≥98%** accuracy for mantras, verses, symbols
3. ✅ **Scripture Reference System** identifies 90% of complete verses, 70% of fragments  
4. ✅ **Production Processing** handles 11k hours efficiently with quality flagging
5. ✅ **Platform Integration** outputs formats for YouTube, publishing, apps
6. ✅ **Lean Compliance** maintained with <1,500 additional lines of code
7. ✅ **Performance Requirements** met with ≥1,500 segments/second processing

**Success means**: Transform from development prototype to production-grade Sanskrit content processor serving multiple platforms and use cases with exceptional quality.

---

## 🚨 **CRITICAL FIXES APPLIED**

### **Root Cause Analysis Completed:**
Epic 6 was falsely marked complete with 0% functionality due to catastrophic "Kṛṣṇa bug" that replaced all input with repeated "Kṛṣṇa" outputs.

### **Major Issues Fixed:**
1. **Database Query Wildcard Bug** - Fixed overly broad LIKE queries
2. **Processing Pipeline Tokenization** - Fixed regex patterns and word boundaries  
3. **Compound Recognition Integration** - Fixed processor ordering and classification
4. **Content Classification Logic** - Fixed verse vs title detection

### **Current Functionality Status:**
- ✅ **Database Integration**: 425 corrections + 510 proper nouns loaded
- ✅ **Compound Recognition**: "Srimad bhagavad gita" → "Śrīmad Bhagavad Gītā" 
- ✅ **Context-Aware Processing**: All 17 tests pass
- ✅ **Platform Output Formats**: All 9 tests pass
- ✅ **Sacred Content Processing**: Classification working
- ⚠️ **Minor Issue**: 1 diacritic test failing (90% → 100% conversion needed)
- ❌ **Untested**: Stories 6.4 & 6.6 need validation

### **Quality Metrics ACTUAL:**
- **Processing Speed**: >2000 segments/second ✅
- **Memory Usage**: <100MB ✅ 
- **Correction Accuracy**: 90% functional (vs. claimed 95%)
- **Test Coverage**: 35/38 tests passing (92% pass rate)

**Next Action**: Validate remaining stories 6.4 & 6.6, fix minor diacritic issue to reach 100%.