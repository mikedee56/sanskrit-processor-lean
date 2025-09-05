# Adding Terms to the Lexicon System - Developer Guide

## Quick Addition Process

### **1. Choose the Right File**
```bash
lexicons/corrections.yaml     # Sanskrit/Hindi terms (dharma, yoga, etc.)
lexicons/proper_nouns.yaml   # Names & places (Krishna, Vrindavan, etc.)
```

### **2. Follow the Template**

**For Corrections (Sanskrit/Hindi terms):**
```yaml
- original_term: "new_term"
  variations: ["common_misspelling", "phonetic_variant", "asr_error"]
  transliteration: "proper_iast"  # Use diacritics: ā, ī, ū, ṃ, ḥ, ṇ, ṣ
  is_proper_noun: false
  category: "concept|practice|philosophy|ritual"
  confidence: 1.0
  source_authority: "IAST|Traditional"
  difficulty_level: "beginner|intermediate|advanced"
  meaning: "concise definition"
```

**For Proper Nouns (Names, places, titles):**
```yaml
- term: "New_Name"  # Already capitalized
  variations: ["lowercase", "common_variant", "regional_spelling"]
  category: "deity|sage|place|festival|title"
  confidence: 1.0
```

## Example: Adding New Terms

### **Philosophy Term Example:**
```yaml
# Add to corrections.yaml
- original_term: "sadhguru"
  variations: ["sadguru", "sat guru", "spiritual teacher"]
  transliteration: "sadguru"
  is_proper_noun: false
  category: "concept" 
  confidence: 1.0
  source_authority: "Traditional"
  difficulty_level: "intermediate"
  meaning: "true spiritual teacher, guide to truth"
```

### **Deity Name Example:**
```yaml
# Add to proper_nouns.yaml
- term: "Kali"
  variations: ["kali", "kalika", "divine mother kali"]
  category: "deity"
  confidence: 1.0
```

## Automated Addition Tools

### **Quick Script for Batch Adding:**
```python
# Create helper script: add_terms.py
import yaml
from pathlib import Path

def add_correction_term(original, variations, transliteration, category, difficulty, meaning):
    corrections = yaml.safe_load(Path('lexicons/corrections.yaml').read_text())
    
    new_entry = {
        'original_term': original,
        'variations': variations,
        'transliteration': transliteration,
        'is_proper_noun': False,
        'category': category,
        'confidence': 1.0,
        'source_authority': 'IAST',
        'difficulty_level': difficulty,
        'meaning': meaning
    }
    
    corrections['entries'].append(new_entry)
    Path('lexicons/corrections.yaml').write_text(yaml.dump(corrections, allow_unicode=True, sort_keys=False))
    print(f'Added: {original}')

# Example usage:
add_correction_term(
    'ahimsa', 
    ['ahimsha', 'non-violence', 'nonviolence'], 
    'ahiṃsā',
    'concept',
    'intermediate', 
    'non-violence, principle of not harming'
)
```

## Quality Checklist Before Adding

### **✅ Research Phase:**
- [ ] Verify term in authoritative source (Monier-Williams Dictionary)
- [ ] Check existing entries for duplicates
- [ ] Confirm proper IAST transliteration
- [ ] Identify common misspellings from real usage

### **✅ Metadata Validation:**
- [ ] **Category**: Matches existing categories
- [ ] **Difficulty**: beginner (common) → advanced (scholarly)
- [ ] **Meaning**: Concise, accurate, culturally sensitive
- [ ] **Variations**: Include ASR errors, phonetic spellings

### **✅ Testing:**
```bash
# Verify no syntax errors
python3 -c "import yaml; yaml.safe_load(open('lexicons/corrections.yaml'))"

# Test the new term works
python3 -c "
from sanskrit_processor_v2 import SanskritProcessor
processor = SanskritProcessor()
result, corrections = processor.process_text('Test your new term here')
print(f'Result: {result}, Corrections: {corrections}')
"
```

## Common Patterns

### **For Sanskrit Terms:**
```yaml
# Yoga/Practice terms
category: "practice"
difficulty_level: "beginner"  # asana, pranayama
difficulty_level: "intermediate"  # dharana, samadhi

# Philosophy terms  
category: "philosophy"
difficulty_level: "advanced"  # advaita, brahman
```

### **For Proper Nouns:**
```yaml
# Deities: Krishna, Shiva, Ganesha, etc.
category: "deity"

# Places: Vrindavan, Haridwar, etc.
category: "place" 

# Teachers: Adi Shankara, Patanjali, etc.
category: "sage" or "acharya"
```

## Bulk Addition Workflow

### **1. Prepare CSV/List:**
```csv
term,variations,category,meaning
tapasya,"tapa,austerity,penance",practice,"spiritual austerity"
sannyasa,"sannyas,renunciation",concept,"renunciate lifestyle"
```

### **2. Convert to YAML:**
```python
# bulk_add.py
import yaml, csv
from pathlib import Path

corrections = yaml.safe_load(Path('lexicons/corrections.yaml').read_text())

with open('new_terms.csv', 'r') as f:
    for row in csv.DictReader(f):
        entry = {
            'original_term': row['term'],
            'variations': row['variations'].split(','),
            'transliteration': row['term'],  # Update manually later
            'is_proper_noun': False,
            'category': row['category'],
            'confidence': 1.0,
            'source_authority': 'IAST',
            'difficulty_level': 'intermediate',  # Update as needed
            'meaning': row['meaning']
        }
        corrections['entries'].append(entry)

# Save back
Path('lexicons/corrections.yaml').write_text(yaml.dump(corrections, allow_unicode=True, sort_keys=False))
```

### **3. Validate & Test:**
```bash
# Run comprehensive tests
python3 tests/test_extended_lexicons.py

# Quick processing test
python3 simple_cli.py sample_test.srt test_output.srt --lexicons lexicons --verbose
```

## Integration with Development

### **Git Workflow:**
```bash
# Create feature branch for new terms
git checkout -b add-new-sanskrit-terms

# Add terms using above process
# Test thoroughly

# Commit with clear message
git add lexicons/
git commit -m "Add 15 new yoga terminology entries

- Added pranayama variations and sub-practices
- Included meditation terminology from Patanjali Sutras
- All terms validated against Monier-Williams Dictionary"
```

### **Performance Considerations:**
- **Loading Time**: Minimal impact up to ~1000 entries
- **Memory**: Each entry ~200 bytes, very efficient
- **Processing**: O(1) lookup, no performance degradation

## Quick Reference

### **Most Common Categories:**
- `concept` - dharma, karma, moksha
- `practice` - yoga, meditation, pranayama  
- `philosophy` - advaita, dvaita, brahman
- `ritual` - puja, aarti, sankirtana
- `deity` - Krishna, Shiva, Ganesha
- `place` - Vrindavan, Haridwar
- `sage` - Vyasa, Patanjali

### **IAST Diacritics:**
- **ā** (long a) - prāṇa
- **ī** (long i) - yogī  
- **ū** (long u) - pūjā
- **ṃ** (anusvara) - saṃsāra
- **ṣ** (retroflex s) - mokṣa
- **ṇ** (retroflex n) - prāṇāyāma

### **Difficulty Level Guidelines:**
- **beginner**: Common terms (yoga, dharma, Krishna)
- **intermediate**: Practice-specific (pranayama, dhyana)
- **advanced**: Philosophical concepts (advaita, brahman)

## Validation Commands

```bash
# Quick validation
python3 -c "
import yaml
from pathlib import Path

# Test YAML syntax
corrections = yaml.safe_load(Path('lexicons/corrections.yaml').read_text())
proper_nouns = yaml.safe_load(Path('lexicons/proper_nouns.yaml').read_text())

print('✓ YAML syntax valid')
print(f'Corrections: {len(corrections[\"entries\"])} entries')
print(f'Proper nouns: {len(proper_nouns[\"entries\"])} entries')
"

# Test processing
python3 -c "
from sanskrit_processor_v2 import SanskritProcessor
processor = SanskritProcessor()
test_text = 'Test your new terms here'
result, corrections = processor.process_text(test_text)
print(f'Processed: {result} ({corrections} corrections)')
"
```

This system makes lexicon expansion straightforward while maintaining quality and performance standards.