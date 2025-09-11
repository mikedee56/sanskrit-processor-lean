#!/usr/bin/env python3
"""
Improved Database Contamination Analysis Script
More sophisticated analysis with Sanskrit whitelist
Part of Story 9.3: Database Cleanup & Validation
"""

import sqlite3
import json
import re
from collections import defaultdict
from datetime import datetime

# Sanskrit diacriticals for validation
SANSKRIT_CHARS = set('āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ')

# Valid Sanskrit terms that may appear without diacriticals (whitelist)
SANSKRIT_WHITELIST = {
    'dharma', 'karma', 'yoga', 'guru', 'mantra', 'chakra', 'tantra',
    'brahman', 'atman', 'moksha', 'samsara', 'nirvana', 'ashrama',
    'indra', 'vishnu', 'shiva', 'brahma', 'krishna', 'rama', 'gita',
    'ramayana', 'mahabharata', 'upanishad', 'veda', 'vedanta',
    'pranayama', 'asana', 'samadhi', 'dhyana', 'dharana', 'pratyahara',
    'yama', 'niyama', 'bandha', 'mudra', 'prana', 'apana', 'sushumna',
    'ida', 'pingala', 'nadis', 'kundalini', 'ajna', 'muladhara',
    'swadhisthana', 'manipura', 'anahata', 'vishuddha', 'sahasrara'
}

# Obvious English words that should NEVER be in Sanskrit database
ENGLISH_REJECT_LIST = {
    'treading', 'agitated', 'reading', 'leading', 'teaching', 'learning',
    'walking', 'talking', 'thinking', 'feeling', 'being', 'doing',
    'having', 'going', 'coming', 'seeing', 'hearing', 'knowing',
    'the', 'and', 'or', 'but', 'if', 'then', 'when', 'where', 'how', 'why',
    'what', 'who', 'which', 'that', 'this', 'these', 'those', 'here', 'there',
    'now', 'then', 'always', 'never', 'often', 'sometimes', 'usually',
    'about', 'above', 'across', 'after', 'against', 'along', 'among',
    'around', 'before', 'behind', 'below', 'beneath', 'beside', 'between',
    'beyond', 'during', 'except', 'inside', 'instead', 'outside', 'through',
    'throughout', 'together', 'towards', 'under', 'until', 'within', 'without'
}

def analyze_sophisticated_contamination(db_path):
    """Sophisticated analysis for English contamination."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all terms
    cursor.execute("SELECT id, original_term, transliteration, variations FROM terms")
    all_terms = cursor.fetchall()
    
    contamination_report = {
        'total_entries': len(all_terms),
        'analysis_date': datetime.now().isoformat(),
        'contamination_categories': defaultdict(list),
        'statistics': defaultdict(int),
        'problematic_entries': [],
        'valid_sanskrit_preserved': []
    }
    
    for term_id, original, transliteration, variations in all_terms:
        issues = []
        is_valid_sanskrit = False
        
        original_clean = (original or '').strip()
        transliteration_clean = (transliteration or '').strip()
        
        # Check if it's whitelisted valid Sanskrit
        if (original_clean.lower() in SANSKRIT_WHITELIST or 
            transliteration_clean.lower() in SANSKRIT_WHITELIST):
            is_valid_sanskrit = True
            contamination_report['valid_sanskrit_preserved'].append({
                'id': term_id,
                'term': original_clean,
                'transliteration': transliteration_clean
            })
        
        # Check for obvious English words (high confidence contamination)
        if original_clean.lower() in ENGLISH_REJECT_LIST:
            issues.append("obvious_english_word")
            contamination_report['statistics']['obvious_english'] += 1
        
        # Check for English with synthetic diacriticals
        if original_clean and transliteration_clean:
            # Remove diacriticals and check if result is English
            ascii_original = re.sub(r'[āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ]', '', original_clean)
            if ascii_original.lower() in ENGLISH_REJECT_LIST:
                issues.append("english_with_synthetic_diacriticals")
                contamination_report['statistics']['synthetic_english'] += 1
        
        # Check for suspicious patterns (only if not whitelisted)
        if not is_valid_sanskrit:
            has_sanskrit_chars = any(char in SANSKRIT_CHARS for char in original_clean + transliteration_clean)
            
            # No Sanskrit markers and not whitelisted = suspicious
            if not has_sanskrit_chars:
                # Additional checks for likely contamination
                if (len(original_clean) > 3 and 
                    not any(term in original_clean.lower() for term in SANSKRIT_WHITELIST) and
                    re.match(r'^[a-zA-Z\s]+$', original_clean)):  # Pure ASCII
                    
                    issues.append("suspicious_ascii_only")
                    contamination_report['statistics']['suspicious_ascii'] += 1
        
        # Check variations for English contamination
        if variations:
            try:
                variations_list = json.loads(variations) if isinstance(variations, str) else variations
                if isinstance(variations_list, list):
                    english_variations = [v for v in variations_list if v.lower() in ENGLISH_REJECT_LIST]
                    if english_variations:
                        issues.append("english_in_variations")
                        contamination_report['statistics']['contaminated_variations'] += 1
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Record problematic entries (high confidence only)
        if issues:
            entry_info = {
                'id': term_id,
                'original_term': original_clean,
                'transliteration': transliteration_clean,
                'variations': variations,
                'issues': issues,
                'removal_reason': ', '.join(issues),
                'confidence': 'high' if any(issue in ['obvious_english_word', 'english_with_synthetic_diacriticals'] 
                                          for issue in issues) else 'medium'
            }
            contamination_report['problematic_entries'].append(entry_info)
            
            for issue in issues:
                contamination_report['contamination_categories'][issue].append(entry_info)
    
    # Calculate statistics
    contamination_report['statistics']['total_contaminated'] = len(contamination_report['problematic_entries'])
    contamination_report['statistics']['high_confidence_contaminated'] = len([
        e for e in contamination_report['problematic_entries'] if e['confidence'] == 'high'
    ])
    contamination_report['statistics']['contamination_percentage'] = (
        contamination_report['statistics']['total_contaminated'] / 
        contamination_report['total_entries'] * 100
    )
    contamination_report['statistics']['valid_sanskrit_preserved'] = len(contamination_report['valid_sanskrit_preserved'])
    
    conn.close()
    return contamination_report

def save_improved_audit_log(contamination_report, audit_file):
    """Save improved audit log with confidence levels."""
    
    with open(audit_file, 'w', encoding='utf-8') as f:
        f.write("Sanskrit Database Contamination Audit Log (Improved Analysis)\n")
        f.write("=" * 60 + "\n")
        f.write(f"Analysis Date: {contamination_report['analysis_date']}\n")
        f.write(f"Total Entries: {contamination_report['total_entries']}\n")
        f.write(f"Contaminated Entries: {contamination_report['statistics']['total_contaminated']}\n")
        f.write(f"High Confidence Contamination: {contamination_report['statistics']['high_confidence_contaminated']}\n")
        f.write(f"Valid Sanskrit Preserved: {contamination_report['statistics']['valid_sanskrit_preserved']}\n")
        f.write(f"Contamination Rate: {contamination_report['statistics']['contamination_percentage']:.2f}%\n\n")
        
        # High confidence entries first
        high_confidence = [e for e in contamination_report['problematic_entries'] if e['confidence'] == 'high']
        if high_confidence:
            f.write("HIGH CONFIDENCE CONTAMINATION (REMOVE IMMEDIATELY):\n")
            f.write("-" * 50 + "\n")
            for entry in high_confidence:
                f.write(f"ID: {entry['id']}\n")
                f.write(f"Original: {entry['original_term']}\n")
                f.write(f"Transliteration: {entry['transliteration']}\n")
                f.write(f"Issues: {entry['removal_reason']}\n")
                f.write("-" * 20 + "\n")
        
        # Medium confidence entries
        medium_confidence = [e for e in contamination_report['problematic_entries'] if e['confidence'] == 'medium']
        if medium_confidence:
            f.write("\nMEDIUM CONFIDENCE CONTAMINATION (REVIEW CAREFULLY):\n")
            f.write("-" * 50 + "\n")
            for entry in medium_confidence[:20]:  # Limit to first 20 for review
                f.write(f"ID: {entry['id']}\n")
                f.write(f"Original: {entry['original_term']}\n")
                f.write(f"Transliteration: {entry['transliteration']}\n")
                f.write(f"Issues: {entry['removal_reason']}\n")
                f.write("-" * 20 + "\n")

def print_improved_summary(contamination_report):
    """Print improved contamination analysis summary."""
    
    print("🔍 IMPROVED DATABASE CONTAMINATION ANALYSIS")
    print("=" * 50)
    print(f"Total entries: {contamination_report['total_entries']:,}")
    print(f"Contaminated entries: {contamination_report['statistics']['total_contaminated']:,}")
    print(f"High confidence contamination: {contamination_report['statistics']['high_confidence_contaminated']:,}")
    print(f"Valid Sanskrit preserved: {contamination_report['statistics']['valid_sanskrit_preserved']:,}")
    print(f"Contamination rate: {contamination_report['statistics']['contamination_percentage']:.2f}%")
    print()
    
    print("📊 CONTAMINATION BREAKDOWN:")
    stats = contamination_report['statistics']
    print(f"• Obvious English words: {stats.get('obvious_english', 0):,}")
    print(f"• English with synthetic diacriticals: {stats.get('synthetic_english', 0):,}")
    print(f"• Suspicious ASCII-only: {stats.get('suspicious_ascii', 0):,}")
    print(f"• Contaminated variations: {stats.get('contaminated_variations', 0):,}")
    print()
    
    # Show some examples of preserved Sanskrit
    if contamination_report['valid_sanskrit_preserved']:
        print("✅ VALID SANSKRIT PRESERVED (sample):")
        for item in contamination_report['valid_sanskrit_preserved'][:5]:
            print(f"   • {item['term']} / {item['transliteration']}")
        print()

if __name__ == "__main__":
    db_path = "data/sanskrit_terms.db"
    audit_file = "data/cleanup_audit_improved.log"
    
    print("🔬 Running improved contamination analysis...")
    contamination_report = analyze_sophisticated_contamination(db_path)
    
    print_improved_summary(contamination_report)
    
    # Save improved audit log
    save_improved_audit_log(contamination_report, audit_file)
    print(f"✅ Improved audit log saved to: {audit_file}")
    
    # Save detailed report
    with open("data/contamination_analysis_improved.json", "w", encoding="utf-8") as f:
        json.dump(contamination_report, f, indent=2, ensure_ascii=False)
    print("✅ Detailed analysis saved to: data/contamination_analysis_improved.json")