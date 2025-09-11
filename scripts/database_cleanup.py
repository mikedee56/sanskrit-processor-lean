#!/usr/bin/env python3
"""
Conservative Database Cleanup Script
Removes only high-confidence English contamination
Part of Story 9.3: Database Cleanup & Validation
"""

import sqlite3
import json
import re
from datetime import datetime

# Sanskrit diacriticals for validation
SANSKRIT_CHARS = set('āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ')

# Extended Sanskrit whitelist (comprehensive)
SANSKRIT_WHITELIST = {
    # Core concepts
    'dharma', 'karma', 'yoga', 'guru', 'mantra', 'chakra', 'tantra',
    'brahman', 'atman', 'moksha', 'samsara', 'nirvana', 'ashrama',
    
    # Deities and names
    'indra', 'vishnu', 'shiva', 'brahma', 'krishna', 'rama', 'gita',
    'hanuman', 'ganesha', 'lakshmi', 'saraswati', 'durga', 'kali',
    
    # Texts and literature
    'ramayana', 'mahabharata', 'upanishad', 'veda', 'vedanta', 'purana',
    'gita', 'bhagavad', 'rig', 'sama', 'yajur', 'atharva',
    
    # Yoga and practices
    'pranayama', 'asana', 'samadhi', 'dhyana', 'dharana', 'pratyahara',
    'yama', 'niyama', 'bandha', 'mudra', 'prana', 'apana', 'sushumna',
    'ida', 'pingala', 'nadis', 'kundalini',
    
    # Chakras and energy
    'ajna', 'muladhara', 'swadhisthana', 'manipura', 'anahata', 
    'vishuddha', 'sahasrara',
    
    # Sanskrit terms commonly written without diacriticals
    'ahimsa', 'satya', 'asteya', 'brahmacharya', 'aparigraha',
    'saucha', 'santosha', 'tapas', 'svadhyaya', 'ishvara',
    'pranidhana', 'samskara', 'vritti', 'chitta', 'buddhi',
    'manas', 'ahamkara', 'mahat', 'prakriti', 'purusha'
}

# High-confidence English contamination (conservative list)
DEFINITE_ENGLISH_CONTAMINATION = {
    'treading', 'agitated', 'reading', 'leading', 'teaching',
    'walking', 'talking', 'thinking', 'feeling', 'being', 'doing',
    'having', 'going', 'coming', 'seeing', 'hearing', 'knowing',
    'the', 'and', 'or', 'but', 'if', 'then', 'when', 'where',
    'how', 'why', 'what', 'who', 'which', 'that', 'this',
    'about', 'above', 'across', 'after', 'against', 'along',
    'around', 'before', 'behind', 'below', 'beneath', 'beside',
    'between', 'beyond', 'during', 'except', 'inside', 'instead',
    'outside', 'through', 'throughout', 'together', 'towards',
    'under', 'until', 'within', 'without'
}

def perform_conservative_cleanup(db_path):
    """Perform conservative database cleanup - high confidence only."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cleanup_log = {
        'cleanup_date': datetime.now().isoformat(),
        'removed_entries': [],
        'statistics': {
            'total_before': 0,
            'removed_count': 0,
            'total_after': 0
        }
    }
    
    # Get initial count
    cursor.execute("SELECT COUNT(*) FROM terms")
    cleanup_log['statistics']['total_before'] = cursor.fetchone()[0]
    
    print(f"🗃️  Database entries before cleanup: {cleanup_log['statistics']['total_before']:,}")
    
    # Find definite English contamination
    cursor.execute("SELECT id, original_term, transliteration, variations FROM terms")
    all_terms = cursor.fetchall()
    
    ids_to_remove = []
    
    for term_id, original, transliteration, variations in all_terms:
        original_clean = (original or '').strip()
        transliteration_clean = (transliteration or '').strip()
        should_remove = False
        removal_reason = []
        
        # Check for definite English words
        if original_clean.lower() in DEFINITE_ENGLISH_CONTAMINATION:
            should_remove = True
            removal_reason.append("definite_english_word")
        
        # Check for English words with synthetic diacriticals
        if original_clean:
            # Remove diacriticals and check if result is definite English
            ascii_version = re.sub(r'[āīūṛṝḷḹṁṃḥśṣṇṭḍñĀĪŪṚṜḶḸṀṂḤŚṢṆṬḌÑ]', '', original_clean)
            if ascii_version.lower() in DEFINITE_ENGLISH_CONTAMINATION:
                should_remove = True
                removal_reason.append("english_with_synthetic_diacriticals")
        
        # Remove variations that are definite English
        if variations and not should_remove:  # Only check if not already marked for removal
            try:
                variations_list = json.loads(variations) if isinstance(variations, str) else variations
                if isinstance(variations_list, list):
                    # Filter out English variations
                    clean_variations = [v for v in variations_list if v.lower() not in DEFINITE_ENGLISH_CONTAMINATION]
                    if len(clean_variations) != len(variations_list):
                        # Update variations to remove English contamination
                        updated_variations = json.dumps(clean_variations)
                        cursor.execute("UPDATE terms SET variations = ? WHERE id = ?", 
                                     (updated_variations, term_id))
                        removal_reason.append("cleaned_variations")
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Record entries to be completely removed
        if should_remove:
            ids_to_remove.append(term_id)
            cleanup_log['removed_entries'].append({
                'id': term_id,
                'original_term': original_clean,
                'transliteration': transliteration_clean,
                'removal_reason': ', '.join(removal_reason)
            })
    
    # Remove definite contamination
    if ids_to_remove:
        placeholders = ','.join(['?' for _ in ids_to_remove])
        cursor.execute(f"DELETE FROM terms WHERE id IN ({placeholders})", ids_to_remove)
        print(f"🗑️  Removed {len(ids_to_remove)} definite English contamination entries")
    else:
        print("✅ No definite English contamination found")
    
    # Optimize database
    print("🔧 Optimizing database...")
    cursor.execute("VACUUM")
    cursor.execute("REINDEX")
    cursor.execute("ANALYZE")
    
    # Get final count
    cursor.execute("SELECT COUNT(*) FROM terms")
    cleanup_log['statistics']['total_after'] = cursor.fetchone()[0]
    cleanup_log['statistics']['removed_count'] = len(ids_to_remove)
    
    conn.commit()
    conn.close()
    
    return cleanup_log

def save_cleanup_log(cleanup_log, log_file):
    """Save cleanup operation log."""
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("Sanskrit Database Cleanup Log\n")
        f.write("=" * 40 + "\n")
        f.write(f"Cleanup Date: {cleanup_log['cleanup_date']}\n")
        f.write(f"Entries Before: {cleanup_log['statistics']['total_before']}\n")
        f.write(f"Entries Removed: {cleanup_log['statistics']['removed_count']}\n")
        f.write(f"Entries After: {cleanup_log['statistics']['total_after']}\n")
        f.write(f"Cleanup Success: {cleanup_log['statistics']['removed_count']} definite contamination entries removed\n\n")
        
        if cleanup_log['removed_entries']:
            f.write("REMOVED ENTRIES:\n")
            f.write("-" * 20 + "\n")
            for entry in cleanup_log['removed_entries']:
                f.write(f"ID: {entry['id']}\n")
                f.write(f"Term: {entry['original_term']}\n")
                f.write(f"Reason: {entry['removal_reason']}\n")
                f.write("-" * 10 + "\n")

def validate_cleanup_results(db_path):
    """Validate that cleanup preserved valid Sanskrit terms."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 VALIDATING CLEANUP RESULTS...")
    
    # Check that key Sanskrit terms are still present
    test_terms = ['dharma', 'karma', 'yoga', 'krishna', 'rama', 'gita']
    preserved_count = 0
    
    for term in test_terms:
        cursor.execute("SELECT COUNT(*) FROM terms WHERE LOWER(original_term) = ? OR LOWER(transliteration) = ?", 
                      (term, term))
        count = cursor.fetchone()[0]
        if count > 0:
            preserved_count += 1
            print(f"✅ '{term}' preserved ({count} entries)")
        else:
            print(f"⚠️  '{term}' not found")
    
    print(f"\n📊 Validation: {preserved_count}/{len(test_terms)} key Sanskrit terms preserved")
    
    # Check for any remaining obvious English
    cursor.execute("SELECT COUNT(*) FROM terms WHERE LOWER(original_term) IN ('the', 'and', 'treading', 'agitated')")
    remaining_english = cursor.fetchone()[0]
    
    if remaining_english == 0:
        print("✅ No obvious English contamination remaining")
    else:
        print(f"⚠️  {remaining_english} obvious English entries still present")
    
    conn.close()
    return preserved_count == len(test_terms) and remaining_english == 0

if __name__ == "__main__":
    db_path = "data/sanskrit_terms.db"
    log_file = "data/cleanup_operation.log"
    
    print("🧹 Starting conservative database cleanup...")
    
    # Perform cleanup
    cleanup_log = perform_conservative_cleanup(db_path)
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"Entries before: {cleanup_log['statistics']['total_before']:,}")
    print(f"Entries removed: {cleanup_log['statistics']['removed_count']:,}")
    print(f"Entries after: {cleanup_log['statistics']['total_after']:,}")
    
    # Save log
    save_cleanup_log(cleanup_log, log_file)
    print(f"✅ Cleanup log saved to: {log_file}")
    
    # Validate results
    validation_passed = validate_cleanup_results(db_path)
    print(f"\n🎯 Cleanup validation: {'PASSED' if validation_passed else 'NEEDS REVIEW'}")
    
    # Save detailed cleanup report
    with open("data/cleanup_report.json", "w", encoding="utf-8") as f:
        json.dump(cleanup_log, f, indent=2, ensure_ascii=False)
    print("✅ Detailed cleanup report saved to: data/cleanup_report.json")