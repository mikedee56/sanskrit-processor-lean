# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Advanced ASR Post-Processing Workflow** project designed to transform ASR-generated transcripts of Yoga Vedanta lectures into highly accurate, academically rigorous textual resources. The system processes SRT files to correct Sanskrit/Hindi terms, apply IAST transliteration standards, and identify scriptural verses.

## Technology Stack

- **Language**: Python 3.10
- **Data Processing**: pandas
- **NLP Libraries**: iNLTK, IndicNLP Library for Indic language support
- **Specialized Model**: ByT5-Sanskrit (optional for advanced corrections)
- **Data Storage**: File-based approach with JSON/YAML lexicons
- **Version Control**: Git

## Project Structure

The project follows a monorepo structure with these key directories:

- `docs/` - Project documentation (PRD, architecture, tech stack)
- `data/` - Raw and processed transcript data
  - `raw_srts/` - Original SRT files
  - `processed_srts/` - Post-processed outputs
  - `lexicons/` - Externalized Sanskrit/Hindi dictionaries
  - `golden_dataset/` - Manually perfected transcripts for benchmarking
- `src/` - Source code (to be created)
  - `post_processors/` - Core post-processing modules
  - `sanskrit_hindi_identifier/` - Language identification logic
  - `ner_module/` - Named Entity Recognition
  - `qa_module/` - Quality assurance metrics
- `tests/` - Test suite
- `config/` - Configuration files
- `scripts/` - Helper scripts

## Key Requirements

### Functional Requirements
- Process SRT files while maintaining timestamp integrity
- Convert spoken numbers to digits ("two thousand five" → "2005")
- Remove filler words ("um", "uh")
- Apply IAST transliteration standard to Sanskrit/Hindi terms
- Identify and correct scriptural verses using canonical text
- Capitalize proper nouns specific to Yoga Vedanta

### Non-Functional Requirements
- Handle large data volumes (12,000+ hours of audio)
- Preserve original speech intention, tone, and style
- Support externalized lexicons for easy updates by linguistic experts
- Maintain scalability for future growth

## Development Approach

This is a **MVP monolith** designed for progressive complexity:
1. **Epic 1**: Foundation & pre-processing pipeline (Complete)
2. **Epic 2**: Sanskrit & Hindi identification & correction (Complete - Stories 2.1-2.3)
3. **Epic 2.4**: Research-Grade Enhancement (In Development - Story 2.4.1 ready)
4. **Epic 3**: Semantic refinement & QA framework (Future)
5. **Epic 4**: Deployment & scalability (Future)

### Current Implementation Status
- ✅ **Story 2.1**: Lexicon-based correction system with fuzzy matching
- ✅ **Story 2.2**: Contextual modeling with n-gram language models  
- ✅ **Story 2.3**: Scripture processing with canonical verse identification
- 🚧 **Story 2.4.1**: Sanskrit sandhi preprocessing (Ready for Development)
- 📋 **Epic 2.4**: Research-grade hybrid matching pipeline (Architecture Complete)

## Key Data Models

### Transcript Segment
- `text` (string): Transcribed text
- `start_time`/`end_time` (float): Timestamps in seconds
- `confidence_score` (float): ASR confidence
- `is_flagged` (boolean): Requires human review
- `correction_history` (array): Log of human corrections

### Lexicon Entry
- `original_term` (string): Correct term
- `variations` (array): Common misrecognized variations
- `transliteration` (string): IAST transliteration
- `is_proper_noun`/`is_verse` (boolean): Classification flags
- `canonical_text` (string): Full scriptural text for verses

## Environment Setup (CRITICAL)

**⚠️ REQUIRED: Always activate the virtual environment before testing or development**

The project uses a configured virtual environment with all dependencies pre-installed:

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate.bat  # Windows

# Set Python path for imports
export PYTHONPATH=/path/to/project/src
# OR (Windows)
set PYTHONPATH=D:\Post-Processing-Shruti\src

# Verify environment
python -c "import fuzzywuzzy, sanskrit_parser, pysrt, yaml; print('Environment ready')"
```

**Dependencies installed in virtual environment:**
- Core: `fuzzywuzzy`, `python-Levenshtein`, `pysrt`, `pyyaml`, `structlog`
- Sanskrit/Hindi: `sanskrit_parser`, `indic-nlp-library`, `inltk`
- Data processing: `pandas`, `numpy`, `scipy`
- Academic features: All Story 4.5 dependencies

## Testing Requirements

Follow a **Full Testing Pyramid** approach:
- **ALWAYS use virtual environment**: `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python` (Linux/Mac)
- Unit tests for individual functions
- Integration tests for the complete pipeline
- Use golden dataset for accuracy measurements (WER/CER reduction)

### Running Tests
```bash
# Activate environment first
source .venv/bin/activate

# Run Story 4.5 validation
PYTHONPATH=/path/to/project/src python test_story_4_5_final_validation.py

# Run integration tests
PYTHONPATH=/path/to/project/src python test_task_4_system_integration.py
```

## Important Notes

- **CRITICAL**: All testing must use the virtual environment - dependency issues are environmental, not implementation issues
- Focus on defensive security - this processes academic content only
- Maintain academic integrity and IAST transliteration standards
- All external lexicons should be version-controlled JSON/YAML files
- The unprofessional behavior you've described - particularly adjusting tests to match code and bypassing functionality - violates core
  engineering principles. This needs immediate correction.