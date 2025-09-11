#!/usr/bin/env python3
"""
Comprehensive Test Suite for Database Validation
Tests for Story 9.3: Database Cleanup & Validation
"""

import pytest
import sqlite3
import tempfile
import os
import json
from pathlib import Path

# Add parent directory to path to import modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.database_validator import SanskritEntryValidator, validate_database_entry

class TestSanskritEntryValidator:
    """Test suite for Sanskrit entry validation."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.validator = SanskritEntryValidator()
    
    def test_valid_sanskrit_with_diacriticals(self):
        """Test that Sanskrit terms with diacriticals are accepted."""
        test_cases = [
            {"original_term": "dharma", "transliteration": "dharma"},
            {"original_term": "kṛṣṇa", "transliteration": "krishna"},
            {"original_term": "bhagavān", "transliteration": "bhagavan"},
            {"original_term": "yogī", "transliteration": "yogi"},
            {"original_term": "śānti", "transliteration": "shanti"},
        ]
        
        for case in test_cases:
            is_valid, reason = self.validator.validate_entry(case)
            assert is_valid, f"Failed for {case}: {reason}"
    
    def test_whitelisted_sanskrit_terms(self):
        """Test that whitelisted Sanskrit terms are accepted."""
        whitelist_terms = [
            "dharma", "karma", "yoga", "guru", "mantra",
            "krishna", "rama", "shiva", "vishnu", "brahma"
        ]
        
        for term in whitelist_terms:
            entry = {"original_term": term, "transliteration": term}
            is_valid, reason = self.validator.validate_entry(entry)
            assert is_valid, f"Whitelisted term '{term}' was rejected: {reason}"
            assert "whitelisted" in reason.lower(), f"Expected whitelist reason for '{term}'"
    
    def test_english_word_rejection(self):
        """Test that obvious English words are rejected."""
        english_words = [
            "treading", "agitated", "reading", "leading",
            "walking", "talking", "thinking", "feeling",
            "the", "and", "or", "but", "when", "where"
        ]
        
        for word in english_words:
            entry = {"original_term": word, "transliteration": word}
            is_valid, reason = self.validator.validate_entry(entry)
            assert not is_valid, f"English word '{word}' was accepted"
            assert "english" in reason.lower(), f"Expected English rejection for '{word}'"
    
    def test_english_with_synthetic_diacriticals(self):
        """Test that English words with added diacriticals are rejected."""
        synthetic_cases = [
            {"original_term": "treāding", "transliteration": "treading"},
            {"original_term": "agītāted", "transliteration": "agitated"},
            {"original_term": "reāding", "transliteration": "reading"},
        ]
        
        for case in synthetic_cases:
            is_valid, reason = self.validator.validate_entry(case)
            assert not is_valid, f"Synthetic term should be rejected: {case}"
            assert "synthetic" in reason.lower() or "english" in reason.lower()
    
    def test_variations_cleaning(self):
        """Test that English variations are identified and cleaned."""
        # Test with JSON string variations
        variations_json = json.dumps(["dharma", "treading", "righteousness"])
        clean_variations = self.validator.clean_variations(variations_json)
        
        assert "dharma" in clean_variations
        assert "righteousness" in clean_variations
        assert "treading" not in clean_variations
        
        # Test with list variations
        variations_list = ["yoga", "walking", "union"]
        clean_variations = self.validator.clean_variations(variations_list)
        
        assert "yoga" in clean_variations
        assert "union" in clean_variations
        assert "walking" not in clean_variations
    
    def test_empty_entries(self):
        """Test handling of empty entries."""
        empty_cases = [
            {"original_term": "", "transliteration": ""},
            {"original_term": None, "transliteration": None},
            {"original_term": "  ", "transliteration": "  "},
        ]
        
        for case in empty_cases:
            is_valid, reason = self.validator.validate_entry(case)
            assert not is_valid, f"Empty entry should be rejected: {case}"
            assert "empty" in reason.lower()
    
    def test_batch_validation(self):
        """Test batch validation functionality."""
        test_entries = [
            {"original_term": "dharma", "transliteration": "dharma"},
            {"original_term": "treading", "transliteration": "treading"},
            {"original_term": "kṛṣṇa", "transliteration": "krishna"},
            {"original_term": "someterm", "transliteration": "someterm"},
        ]
        
        results = self.validator.validate_import_batch(test_entries)
        
        assert len(results['valid']) >= 2  # dharma, krishna
        assert len(results['invalid']) >= 1  # treading
        assert 'review_needed' in results
    
    def test_convenience_function(self):
        """Test the convenience validation function."""
        # Valid Sanskrit
        is_valid, reason = validate_database_entry("dharma", "dharma")
        assert is_valid
        
        # Invalid English
        is_valid, reason = validate_database_entry("treading", "treading")
        assert not is_valid
        
        # With variations
        variations = ["dharma", "treading", "righteousness"]
        is_valid, reason = validate_database_entry("dharma", "dharma", variations)
        assert is_valid  # Should still be valid despite contaminated variations
    
    def test_validation_metrics(self):
        """Test validation metrics calculation."""
        test_entries = [
            {"original_term": "dharma", "transliteration": "dharma"},
            {"original_term": "treading", "transliteration": "treading"},
            {"original_term": "kṛṣṇa", "transliteration": "krishna"},
            {"original_term": "someterm", "transliteration": "someterm"},
        ]
        
        batch_results = self.validator.validate_import_batch(test_entries)
        metrics = self.validator.get_validation_metrics(batch_results)
        
        assert metrics['total_processed'] == 4
        assert 'valid_count' in metrics
        assert 'invalid_count' in metrics
        assert 'review_needed_count' in metrics
        assert 'validation_rate' in metrics
        assert metrics['validation_rate'] >= 0 and metrics['validation_rate'] <= 100

class TestDatabaseIntegration:
    """Integration tests with actual database operations."""
    
    def setup_method(self):
        """Create temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create test database with sample data
        self._create_test_database()
        self.validator = SanskritEntryValidator()
    
    def teardown_method(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_test_database(self):
        """Create test database with known good and bad entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create terms table
        cursor.execute('''
            CREATE TABLE terms (
                id INTEGER PRIMARY KEY,
                original_term TEXT,
                transliteration TEXT,
                variations TEXT,
                category TEXT,
                confidence REAL
            )
        ''')
        
        # Insert test data
        test_data = [
            (1, "dharma", "dharma", '["righteousness"]', "concept", 0.95),
            (2, "treading", "treading", '["walking"]', "action", 0.80),
            (3, "kṛṣṇa", "krishna", '["Krishna"]', "deity", 0.99),
            (4, "agītāted", "agitated", '["disturbed"]', "state", 0.70),
            (5, "yoga", "yoga", '["union", "treading"]', "practice", 0.95),
        ]
        
        cursor.executemany('''
            INSERT INTO terms (id, original_term, transliteration, variations, category, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', test_data)
        
        conn.commit()
        conn.close()
    
    def test_database_contamination_detection(self):
        """Test detection of contamination in actual database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, original_term, transliteration, variations FROM terms")
        all_terms = cursor.fetchall()
        
        contaminated_count = 0
        valid_count = 0
        
        for term_id, original, transliteration, variations in all_terms:
            entry = {
                'original_term': original,
                'transliteration': transliteration,
                'variations': variations
            }
            
            is_valid, reason = self.validator.validate_entry(entry)
            
            if is_valid:
                valid_count += 1
            else:
                contaminated_count += 1
        
        conn.close()
        
        # We expect at least some contamination in our test data
        assert contaminated_count > 0, "Should detect contamination in test data"
        assert valid_count > 0, "Should preserve valid Sanskrit terms"
    
    def test_variations_cleaning_in_database(self):
        """Test cleaning variations in database context."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the yoga entry which has contaminated variations
        cursor.execute("SELECT variations FROM terms WHERE original_term = 'yoga'")
        result = cursor.fetchone()
        
        if result:
            original_variations = result[0]
            cleaned_variations = self.validator.clean_variations(original_variations)
            
            # Should keep "union" but remove "treading"
            assert "union" in cleaned_variations
            assert "treading" not in cleaned_variations
        
        conn.close()
    
    def test_database_backup_integrity(self):
        """Test that database operations preserve data integrity."""
        # Count original entries
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM terms")
        original_count = cursor.fetchone()[0]
        
        # Test that we can read all entries without corruption
        cursor.execute("SELECT original_term FROM terms WHERE original_term IS NOT NULL")
        terms = cursor.fetchall()
        
        assert len(terms) > 0, "Should have readable terms"
        assert len(terms) <= original_count, "Should not have more terms than expected"
        
        conn.close()

class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""
    
    def setup_method(self):
        """Setup for performance tests."""
        self.validator = SanskritEntryValidator()
    
    def test_large_batch_validation(self):
        """Test validation performance with large batches."""
        # Create a large batch of entries
        large_batch = []
        for i in range(1000):
            if i % 3 == 0:
                entry = {"original_term": "dharma", "transliteration": "dharma"}
            elif i % 3 == 1:
                entry = {"original_term": "treading", "transliteration": "treading"}
            else:
                entry = {"original_term": f"term{i}", "transliteration": f"term{i}"}
            large_batch.append(entry)
        
        # This should complete without timeout
        results = self.validator.validate_import_batch(large_batch)
        
        assert len(results['valid']) + len(results['invalid']) + len(results['review_needed']) == 1000
    
    def test_malformed_variations(self):
        """Test handling of malformed variations data."""
        malformed_cases = [
            {"original_term": "test", "transliteration": "test", "variations": "not json"},
            {"original_term": "test", "transliteration": "test", "variations": '{"not": "list"}'},
            {"original_term": "test", "transliteration": "test", "variations": None},
        ]
        
        for case in malformed_cases:
            # Should not raise exceptions
            is_valid, reason = self.validator.validate_entry(case)
            assert isinstance(is_valid, bool)
            assert isinstance(reason, str)
    
    def test_unicode_handling(self):
        """Test proper Unicode handling for Sanskrit diacriticals."""
        unicode_cases = [
            {"original_term": "अ", "transliteration": "a"},  # Devanagari
            {"original_term": "ॐ", "transliteration": "om"},  # Om symbol
            {"original_term": "mañtra", "transliteration": "mantra"},  # Mixed script
        ]
        
        for case in unicode_cases:
            # Should not raise exceptions
            is_valid, reason = self.validator.validate_entry(case)
            assert isinstance(is_valid, bool)
            assert isinstance(reason, str)

# Pytest configuration and runners
def test_main_functionality():
    """Main test to ensure basic functionality works."""
    validator = SanskritEntryValidator()
    
    # Test obvious cases
    assert validator.validate_entry({"original_term": "dharma", "transliteration": "dharma"})[0]
    assert not validator.validate_entry({"original_term": "treading", "transliteration": "treading"})[0]

if __name__ == "__main__":
    # Run basic tests if executed directly
    print("🧪 Running Database Validation Tests...")
    print("=" * 50)
    
    # Quick validation test
    test_main_functionality()
    print("✅ Basic functionality test passed")
    
    # Run a few key tests
    validator_tests = TestSanskritEntryValidator()
    validator_tests.setup_method()
    
    try:
        validator_tests.test_valid_sanskrit_with_diacriticals()
        print("✅ Sanskrit diacriticals test passed")
        
        validator_tests.test_english_word_rejection()
        print("✅ English word rejection test passed")
        
        validator_tests.test_english_with_synthetic_diacriticals()
        print("✅ Synthetic diacriticals test passed")
        
        print("\n🎯 All core validation tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    
    print("\n📝 To run full test suite: pytest tests/test_database_validation.py -v")