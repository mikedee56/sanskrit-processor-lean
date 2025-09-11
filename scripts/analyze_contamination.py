#!/usr/bin/env python3
"""
Database Contamination Analysis Script
Analyzes Sanskrit terms database for English contamination
Part of Story 9.3: Database Cleanup & Validation
"""

import sqlite3
import json
import re
from collections import defaultdict
from datetime import datetime

# Sanskrit diacriticals for validation
SANSKRIT_CHARS = set('āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ')

# Common English words that should not be in Sanskrit database
COMMON_ENGLISH_WORDS = {
    'treading', 'agitated', 'reading', 'leading', 'teaching', 'learning',
    'walking', 'talking', 'thinking', 'feeling', 'being', 'doing',
    'having', 'going', 'coming', 'seeing', 'hearing', 'knowing',
    'the', 'and', 'or', 'but', 'if', 'then', 'when', 'where', 'how', 'why',
    'what', 'who', 'which', 'that', 'this', 'these', 'those', 'here', 'there',
    'now', 'then', 'always', 'never', 'often', 'sometimes', 'usually'
}

def analyze_database_contamination(db_path):
    """Analyze database for English contamination."""
    
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
        'problematic_entries': []
    }
    
    for term_id, original, transliteration, variations in all_terms:
        issues = []
        
        # Check for ASCII-only entries (no Sanskrit diacriticals)
        original_clean = original or ''
        transliteration_clean = transliteration or ''
        
        has_sanskrit_chars = any(char in SANSKRIT_CHARS for char in original_clean + transliteration_clean)
        
        if not has_sanskrit_chars:
            issues.append("no_sanskrit_diacriticals")
            contamination_report['statistics']['no_diacriticals'] += 1
        
        # Check against English word list
        if original_clean.lower() in COMMON_ENGLISH_WORDS:
            issues.append("common_english_word")
            contamination_report['statistics']['english_words'] += 1
        
        # Check for synthetic/generated patterns
        if original_clean and transliteration_clean:
            # Look for English words with random diacriticals
            ascii_version = re.sub(r'[āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ]', '', original_clean)
            if ascii_version.lower() in COMMON_ENGLISH_WORDS:
                issues.append("english_with_diacriticals")
                contamination_report['statistics']['synthetic_diacriticals'] += 1
        
        # Check variations for contamination
        if variations:
            try:
                variations_list = json.loads(variations) if isinstance(variations, str) else variations
                if isinstance(variations_list, list):
                    english_variations = [v for v in variations_list if v.lower() in COMMON_ENGLISH_WORDS]
                    if english_variations:
                        issues.append("english_in_variations")
                        contamination_report['statistics']['contaminated_variations'] += 1
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Record problematic entries
        if issues:
            entry_info = {
                'id': term_id,
                'original_term': original_clean,
                'transliteration': transliteration_clean,
                'variations': variations,
                'issues': issues,
                'removal_reason': ', '.join(issues)
            }
            contamination_report['problematic_entries'].append(entry_info)
            
            for issue in issues:
                contamination_report['contamination_categories'][issue].append(entry_info)
    
    # Calculate statistics
    contamination_report['statistics']['total_contaminated'] = len(contamination_report['problematic_entries'])
    contamination_report['statistics']['contamination_percentage'] = (
        contamination_report['statistics']['total_contaminated'] / 
        contamination_report['total_entries'] * 100
    )
    
    conn.close()
    return contamination_report

def save_audit_log(contamination_report, audit_file):
    """Save audit log of problematic entries."""
    
    with open(audit_file, 'w', encoding='utf-8') as f:
        f.write("Sanskrit Database Contamination Audit Log\n")
        f.write("=" * 50 + "\n")
        f.write(f"Analysis Date: {contamination_report['analysis_date']}\n")
        f.write(f"Total Entries: {contamination_report['total_entries']}\n")
        f.write(f"Contaminated Entries: {contamination_report['statistics']['total_contaminated']}\n")
        f.write(f"Contamination Rate: {contamination_report['statistics']['contamination_percentage']:.2f}%\n\n")
        
        f.write("PROBLEMATIC ENTRIES FOR REMOVAL:\n")
        f.write("-" * 40 + "\n")
        
        for entry in contamination_report['problematic_entries']:
            f.write(f"ID: {entry['id']}\n")
            f.write(f"Original: {entry['original_term']}\n")
            f.write(f"Transliteration: {entry['transliteration']}\n")
            f.write(f"Issues: {entry['removal_reason']}\n")
            f.write("-" * 20 + "\n")

def print_summary(contamination_report):
    """Print contamination analysis summary."""
    
    print("🔍 DATABASE CONTAMINATION ANALYSIS")
    print("=" * 40)
    print(f"Total entries: {contamination_report['total_entries']:,}")
    print(f"Contaminated entries: {contamination_report['statistics']['total_contaminated']:,}")
    print(f"Contamination rate: {contamination_report['statistics']['contamination_percentage']:.2f}%")
    print()
    
    print("📊 CONTAMINATION BREAKDOWN:")
    stats = contamination_report['statistics']
    print(f"• No Sanskrit diacriticals: {stats.get('no_diacriticals', 0):,}")
    print(f"• Common English words: {stats.get('english_words', 0):,}")
    print(f"• English with synthetic diacriticals: {stats.get('synthetic_diacriticals', 0):,}")
    print(f"• Contaminated variations: {stats.get('contaminated_variations', 0):,}")
    print()

if __name__ == "__main__":
    db_path = "data/sanskrit_terms.db"
    audit_file = "data/cleanup_audit.log"
    
    print("🔬 Analyzing database contamination...")
    contamination_report = analyze_database_contamination(db_path)
    
    print_summary(contamination_report)
    
    # Save audit log
    save_audit_log(contamination_report, audit_file)
    print(f"✅ Audit log saved to: {audit_file}")
    
    # Save detailed report
    with open("data/contamination_analysis.json", "w", encoding="utf-8") as f:
        json.dump(contamination_report, f, indent=2, ensure_ascii=False)
    print("✅ Detailed analysis saved to: data/contamination_analysis.json")