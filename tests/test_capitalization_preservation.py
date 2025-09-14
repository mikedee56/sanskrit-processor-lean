#!/usr/bin/env python3
"""
Tests for Capitalization Preservation System (Story 11.2)
Tests divine names, scripture titles, and proper noun capitalization preservation.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.capitalization_preserver import CapitalizationPreserver, apply_correction_with_capitalization

class TestCapitalizationPreserver:
    """Test the CapitalizationPreserver class functionality"""

    def setup_method(self):
        """Setup test configuration"""
        self.config = {
            'preserve_capitalization': True,
            'capitalization_categories': {
                'divine_name': True,
                'scripture_title': True,
                'scripture': True,
                'deity': True,
                'place_name': True,
                'concept': False
            }
        }
        self.preserver = CapitalizationPreserver(self.config)

    def test_divine_name_preservation(self):
        """Test divine names maintain proper capitalization"""
        entry = {
            'transliteration': 'Lakṣmī Devī',
            'preserve_capitalization': True,
            'category': 'divine_name'
        }

        # Title case input
        result = self.preserver.apply_capitalization('Lakshmi Devi', 'Lakṣmī Devī', entry)
        assert result == 'Lakṣmī Devī'

        # All lowercase input - should still preserve proper capitalization
        result = self.preserver.apply_capitalization('lakshmi devi', 'Lakṣmī Devī', entry)
        assert result == 'Lakṣmī Devī'

        # All uppercase input
        result = self.preserver.apply_capitalization('LAKSHMI DEVI', 'Lakṣmī Devī', entry)
        assert result == 'LAKṢMĪ DEVĪ'

    def test_krishna_capitalization(self):
        """Test Krishna name variations"""
        entry = {
            'transliteration': 'Śrī Kṛṣṇa',
            'preserve_capitalization': True,
            'category': 'divine_name'
        }

        # Various input cases
        assert self.preserver.apply_capitalization('Sri Krishna', 'Śrī Kṛṣṇa', entry) == 'Śrī Kṛṣṇa'
        assert self.preserver.apply_capitalization('sri krishna', 'Śrī Kṛṣṇa', entry) == 'Śrī Kṛṣṇa'
        assert self.preserver.apply_capitalization('KRISHNA', 'Kṛṣṇa', entry) == 'KṚṢṆA'

    def test_scripture_title_preservation(self):
        """Test scripture titles maintain proper formatting"""
        entry = {
            'transliteration': 'Bhagavad Gītā',
            'preserve_capitalization': True,
            'category': 'scripture_title'
        }

        # Various input cases
        assert self.preserver.apply_capitalization('Bhagavad Gita', 'Bhagavad Gītā', entry) == 'Bhagavad Gītā'
        assert self.preserver.apply_capitalization('bhagavad gita', 'Bhagavad Gītā', entry) == 'Bhagavad Gītā'
        assert self.preserver.apply_capitalization('BHAGAVAD GITA', 'Bhagavad Gītā', entry) == 'BHAGAVAD GĪTĀ'

    def test_yoga_vasistha_preservation(self):
        """Test Yoga Vasistha scripture title"""
        entry = {
            'transliteration': 'Yoga Vāsiṣṭha',
            'preserve_capitalization': True,
            'category': 'scripture_title'
        }

        assert self.preserver.apply_capitalization('yoga vasistha', 'Yoga Vāsiṣṭha', entry) == 'Yoga Vāsiṣṭha'
        assert self.preserver.apply_capitalization('Yoga Vasistha', 'Yoga Vāsiṣṭha', entry) == 'Yoga Vāsiṣṭha'

    def test_regular_terms_no_preservation(self):
        """Test regular terms use standard capitalization"""
        entry = {
            'transliteration': 'jñāna',
            'preserve_capitalization': False,
            'category': 'concept'
        }

        # Should use standard capitalization rules
        result = self.preserver.apply_capitalization('JNANA', 'jñāna', entry)
        assert result == 'Jñāna'  # Standard capitalize()

    def test_category_based_preservation(self):
        """Test category-based capitalization rules"""
        # Divine name category - should preserve
        divine_entry = {
            'transliteration': 'Śrī Rāma',
            'categories': ['divine_name']
        }
        result = self.preserver.apply_capitalization('sri rama', 'Śrī Rāma', divine_entry)
        assert result == 'Śrī Rāma'

        # Concept category - standard rules
        concept_entry = {
            'transliteration': 'mokṣa',
            'categories': ['concept']
        }
        result = self.preserver.apply_capitalization('MOKSHA', 'mokṣa', concept_entry)
        assert result == 'Mokṣa'

    def test_legacy_category_support(self):
        """Test support for legacy category names"""
        # Test 'deity' category (legacy)
        deity_entry = {
            'transliteration': 'Bhagavān',
            'category': 'deity'
        }
        result = self.preserver.apply_capitalization('bhagawan', 'Bhagavān', deity_entry)
        assert result == 'Bhagavān'

        # Test 'scripture' category (legacy)
        scripture_entry = {
            'transliteration': 'Bhagavad Gītā',
            'category': 'scripture'
        }
        result = self.preserver.apply_capitalization('bhagavad gita', 'Bhagavad Gītā', scripture_entry)
        assert result == 'Bhagavad Gītā'

    def test_mixed_case_handling(self):
        """Test mixed case input handling"""
        entry = {
            'transliteration': 'Lakṣmī',
            'preserve_capitalization': True,
            'category': 'divine_name'
        }

        # Mixed case should be handled intelligently
        result = self.preserver.apply_capitalization('lakSHmi', 'Lakṣmī', entry)
        assert result == 'Lakṣmī'

    def test_word_count_mismatch(self):
        """Test handling when word counts don't match"""
        entry = {
            'transliteration': 'Rāma',
            'preserve_capitalization': True,
            'category': 'divine_name'
        }

        # Single word to single word - different from multi-word
        result = self.preserver.apply_capitalization('rama', 'Rāma', entry)
        assert result == 'Rāma'

    def test_disabled_preservation(self):
        """Test behavior when preservation is disabled"""
        config = {'preserve_capitalization': False}
        preserver = CapitalizationPreserver(config)

        entry = {
            'transliteration': 'Lakṣmī Devī',
            'preserve_capitalization': True,
            'category': 'divine_name'
        }

        result = preserver.apply_capitalization('lakshmi devi', 'Lakṣmī Devī', entry)
        assert result == 'Lakṣmī devī'  # Standard capitalize() behavior

    def test_should_preserve_capitalization_check(self):
        """Test the should_preserve_capitalization helper method"""
        # Explicit flag
        entry_with_flag = {'preserve_capitalization': True}
        assert self.preserver.should_preserve_capitalization(entry_with_flag)

        # Category-based
        divine_entry = {'category': 'divine_name'}
        assert self.preserver.should_preserve_capitalization(divine_entry)

        # No preservation
        concept_entry = {'category': 'concept'}
        assert not self.preserver.should_preserve_capitalization(concept_entry)

    def test_empty_inputs(self):
        """Test handling of empty or None inputs"""
        entry = {'transliteration': 'test', 'preserve_capitalization': True}

        # Empty original
        result = self.preserver.apply_capitalization('', 'test', entry)
        assert result == 'test'

        # Empty corrected
        result = self.preserver.apply_capitalization('test', '', entry)
        assert result == ''

        # None inputs
        result = self.preserver.apply_capitalization(None, 'test', entry)
        assert result == 'test'


class TestCapitalizationIntegration:
    """Integration tests with correction application"""

    def test_apply_correction_with_capitalization(self):
        """Test the integration function"""
        config = {
            'preserve_capitalization': True,
            'capitalization_categories': {
                'divine_name': True,
                'concept': False
            }
        }
        preserver = CapitalizationPreserver(config)

        # Divine name correction
        divine_entry = {
            'transliteration': 'Kṛṣṇa',
            'preserve_capitalization': True,
            'category': 'divine_name'
        }

        result = apply_correction_with_capitalization('krishna', divine_entry, preserver)
        assert result == 'Kṛṣṇa'

        # All caps divine name
        result = apply_correction_with_capitalization('KRISHNA', divine_entry, preserver)
        assert result == 'KṚṢṆA'

    def test_no_correction_entry(self):
        """Test behavior when no transliteration is found"""
        config = {'preserve_capitalization': True}
        preserver = CapitalizationPreserver(config)

        entry = {}  # No transliteration
        result = apply_correction_with_capitalization('test', entry, preserver)
        assert result == 'Test'  # Should use standard capitalization


class TestCapitalizationPreserverAdvanced:
    """Advanced tests for 100% quality coverage"""

    def setup_method(self):
        """Setup test configuration"""
        self.config = {
            'preserve_capitalization': True,
            'capitalization_categories': {
                'divine_name': True,
                'scripture_title': True,
                'concept': False
            }
        }
        self.preserver = CapitalizationPreserver(self.config)

    def test_input_validation_errors(self):
        """Test proper error handling for invalid inputs"""
        entry = {'preserve_capitalization': True}

        # Test TypeError for non-string inputs
        with pytest.raises(TypeError):
            self.preserver.apply_capitalization(123, 'test', entry)

        with pytest.raises(TypeError):
            self.preserver.apply_capitalization('test', 456, entry)

        with pytest.raises(TypeError):
            self.preserver.apply_capitalization('test', 'test', 'not_dict')

    def test_should_preserve_capitalization_validation(self):
        """Test validation in should_preserve_capitalization method"""
        with pytest.raises(TypeError):
            self.preserver.should_preserve_capitalization('not_dict')

    def test_unicode_handling(self):
        """Test proper Unicode handling for Sanskrit text"""
        entry = {'transliteration': 'Kṛṣṇa', 'preserve_capitalization': True}

        # Test various Unicode scenarios
        result = self.preserver.apply_capitalization('कृष्ण', 'Kṛṣṇa', entry)
        assert result == 'Kṛṣṇa'  # Should handle Unicode gracefully

        # Test mixed Unicode and ASCII
        result = self.preserver.apply_capitalization('Krishna कृष्ण', 'Kṛṣṇa', entry)
        assert result == 'Kṛṣṇa'  # Word count mismatch handled

    def test_performance_stats(self):
        """Test performance monitoring functionality"""
        stats = self.preserver.get_performance_stats()

        assert isinstance(stats, dict)
        assert 'category_cache_size' in stats
        assert 'preservation_enabled' in stats
        assert 'category_rules_count' in stats
        assert stats['preservation_enabled'] == True
        assert stats['category_rules_count'] == 3

    def test_category_caching_optimization(self):
        """Test category lookup caching for performance"""
        entry1 = {'category': 'divine_name'}
        entry2 = {'categories': ['divine_name', 'deity']}

        # First calls should cache results
        result1 = self.preserver.should_preserve_capitalization(entry1)
        result2 = self.preserver.should_preserve_capitalization(entry2)

        assert result1 == True
        assert result2 == True

        # Verify cache is populated
        stats = self.preserver.get_performance_stats()
        assert stats['category_cache_size'] > 0

    def test_whitespace_preservation(self):
        """Test handling of multiple spaces and whitespace"""
        entry = {'transliteration': 'Śrī  Kṛṣṇa', 'preserve_capitalization': True}

        # Multiple spaces should be handled
        result = self.preserver.apply_capitalization('Sri  Krishna', 'Śrī  Kṛṣṇa', entry)
        assert result == 'Śrī  Kṛṣṇa'

    def test_punctuation_handling(self):
        """Test handling of punctuation in text"""
        entry = {'transliteration': 'Śrī Kṛṣṇa!', 'preserve_capitalization': True}

        # Punctuation should be preserved
        result = self.preserver.apply_capitalization('Sri Krishna!', 'Śrī Kṛṣṇa!', entry)
        assert result == 'Śrī Kṛṣṇa!'

    def test_very_long_text_performance(self):
        """Test performance with longer text strings"""
        long_original = 'Sri Krishna ' * 100
        long_corrected = 'Śrī Kṛṣṇa ' * 100
        entry = {'preserve_capitalization': True}

        # Should handle long strings efficiently
        result = self.preserver.apply_capitalization(long_original.strip(), long_corrected.strip(), entry)
        assert result.count('Śrī Kṛṣṇa') == 100

    def test_edge_case_single_characters(self):
        """Test single character handling"""
        entry = {'transliteration': 'A', 'preserve_capitalization': True}

        # Single uppercase character
        result = self.preserver.apply_capitalization('K', 'A', entry)
        assert result == 'A'

        # Single lowercase character
        result = self.preserver.apply_capitalization('k', 'A', entry)
        assert result == 'A'

    def test_numeric_and_special_characters(self):
        """Test handling of numbers and special characters"""
        entry = {'transliteration': 'Verse 2.47', 'preserve_capitalization': True}

        result = self.preserver.apply_capitalization('verse 2.47', 'Verse 2.47', entry)
        assert result == 'Verse 2.47'

    def test_disabled_preservation_edge_cases(self):
        """Test edge cases when preservation is disabled"""
        config = {'preserve_capitalization': False}
        preserver = CapitalizationPreserver(config)

        entry = {'preserve_capitalization': True, 'category': 'divine_name'}

        # Should ignore all preservation settings when disabled
        result = preserver.apply_capitalization('KRISHNA', 'Kṛṣṇa', entry)
        assert result == 'Kṛṣṇa'  # Standard capitalize

    def test_category_hierarchy_complex(self):
        """Test complex category hierarchies and combinations"""
        entry = {
            'categories': ['divine_name', 'concept', 'place_name'],
            'preserve_capitalization': False  # Explicit false but category should override
        }

        # Category rules should take precedence
        result = self.preserver.should_preserve_capitalization(entry)
        assert result == True  # divine_name and place_name are True

    def test_memory_efficiency(self):
        """Test memory efficiency with many category combinations"""
        # Test many different category combinations to ensure cache doesn't grow unbounded
        for i in range(50):
            entry = {'categories': [f'category_{i}', 'divine_name']}
            self.preserver.should_preserve_capitalization(entry)

        stats = self.preserver.get_performance_stats()
        # Cache should be reasonable size even with many lookups
        assert stats['category_cache_size'] <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])