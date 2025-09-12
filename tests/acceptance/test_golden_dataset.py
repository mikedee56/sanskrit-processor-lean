"""
Golden Dataset ASR Correction Tests

Tests all ASR corrections against the golden dataset to ensure accuracy
and consistency of the Sanskrit processor's ASR correction capabilities.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sanskrit_processor_v2 import SanskritProcessor, SRTSegment, ProcessingResult


class ASRTestSuite:
    """Comprehensive ASR correction test suite using golden dataset."""
    
    def __init__(self):
        self.golden_dataset = self.load_golden_dataset()
        self.processor = None  # Will be injected during test setup
        
    def load_golden_dataset(self) -> Dict[str, Any]:
        """Load the golden dataset from fixtures."""
        fixtures_path = Path(__file__).parent.parent / 'fixtures' / 'asr_golden_dataset.json'
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_all_test_cases(self) -> List[Dict[str, Any]]:
        """Extract all test cases from the golden dataset."""
        test_cases = []
        dataset = self.golden_dataset['asr_test_dataset']
        
        for category_name, cases in dataset['categories'].items():
            test_cases.extend(cases)
        
        return test_cases
    
    def get_test_cases_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get test cases for a specific category."""
        dataset = self.golden_dataset['asr_test_dataset']
        return dataset['categories'].get(category, [])


@pytest.fixture
def asr_test_suite():
    """Fixture to provide ASR test suite instance."""
    return ASRTestSuite()


@pytest.fixture
def sanskrit_processor():
    """Fixture to provide configured Sanskrit processor instance."""
    # Use simple mode for consistent testing
    return SanskritProcessor(simple_mode=True, verbose=False)


@pytest.fixture
def test_suite_with_processor(asr_test_suite, sanskrit_processor):
    """Fixture combining test suite with processor."""
    asr_test_suite.processor = sanskrit_processor
    return asr_test_suite


class TestGoldenDatasetAccuracy:
    """Test ASR correction accuracy against golden dataset."""
    
    @pytest.mark.parametrize("test_case", ASRTestSuite().get_all_test_cases())
    def test_individual_asr_correction_accuracy(self, test_case, sanskrit_processor):
        """Test individual ASR correction accuracy against golden dataset."""
        input_text = test_case['input']
        expected = test_case['expected']
        test_id = test_case['id']
        category = test_case['category']
        
        # Create a test SRT segment
        test_segment = SRTSegment(
            index=1,
            start_time="00:00:00,000",
            end_time="00:00:03,000", 
            text=input_text
        )
        
        # Process the segment
        result = sanskrit_processor.process_segments([test_segment])
        
        # Extract the corrected text
        corrected_text = result.segments[0].text if result.segments else input_text
        
        # Assert correction accuracy
        assert corrected_text == expected, (
            f"Failed for {test_id} ({category}): '{input_text}' → '{corrected_text}' "
            f"(expected: '{expected}')"
        )
    
    @pytest.mark.parametrize("category", [
        "phonetic_substitution",
        "case_variations", 
        "compound_words",
        "asr_transcription_errors",
        "diacritical_issues"
    ])
    def test_category_correction_rates(self, category, test_suite_with_processor):
        """Test correction rates for each category meet expectations."""
        test_cases = test_suite_with_processor.get_test_cases_by_category(category)
        
        if not test_cases:
            pytest.skip(f"No test cases found for category: {category}")
        
        correct_count = 0
        total_count = len(test_cases)
        
        for test_case in test_cases:
            input_text = test_case['input']
            expected = test_case['expected']
            
            # Create test segment and process
            test_segment = SRTSegment(
                index=1, 
                start_time="00:00:00,000",
                end_time="00:00:03,000",
                text=input_text
            )
            
            result = test_suite_with_processor.processor.process_segments([test_segment])
            corrected_text = result.segments[0].text if result.segments else input_text
            
            if corrected_text == expected:
                correct_count += 1
        
        correction_rate = (correct_count / total_count) * 100
        
        # Different expectations per category
        expected_rates = {
            "phonetic_substitution": 80.0,
            "case_variations": 70.0,
            "compound_words": 75.0, 
            "asr_transcription_errors": 60.0,  # These are harder
            "diacritical_issues": 70.0
        }
        
        expected_rate = expected_rates.get(category, 70.0)
        
        assert correction_rate >= expected_rate, (
            f"Category '{category}' correction rate {correction_rate:.1f}% "
            f"below expected {expected_rate}%"
        )
    
    def test_overall_correction_benchmark(self, test_suite_with_processor):
        """Test that overall correction rate meets expectations."""
        all_test_cases = test_suite_with_processor.get_all_test_cases()
        
        correct_count = 0
        total_count = len(all_test_cases)
        
        for test_case in all_test_cases:
            input_text = test_case['input']
            expected = test_case['expected']
            
            # Skip cases marked as already correct to focus on actual corrections
            if test_case.get('pattern') == 'already_correct':
                continue
                
            test_segment = SRTSegment(
                index=1,
                start_time="00:00:00,000", 
                end_time="00:00:03,000",
                text=input_text
            )
            
            result = test_suite_with_processor.processor.process_segments([test_segment])
            corrected_text = result.segments[0].text if result.segments else input_text
            
            if corrected_text == expected:
                correct_count += 1
        
        # Calculate excluding 'already_correct' cases
        correction_cases = [tc for tc in all_test_cases if tc.get('pattern') != 'already_correct']
        correction_rate = (correct_count / len(correction_cases)) * 100
        
        assert correction_rate >= 70.0, (
            f"Overall correction rate {correction_rate:.1f}% below 70% threshold"
        )
    
    def test_confidence_thresholds(self, test_suite_with_processor):
        """Test that corrections meet confidence threshold expectations."""
        high_confidence_cases = []
        
        for test_case in test_suite_with_processor.get_all_test_cases():
            if test_case.get('confidence_threshold', 0) >= 0.8:
                high_confidence_cases.append(test_case)
        
        correct_count = 0
        
        for test_case in high_confidence_cases:
            input_text = test_case['input']
            expected = test_case['expected']
            
            test_segment = SRTSegment(
                index=1,
                start_time="00:00:00,000",
                end_time="00:00:03,000",
                text=input_text
            )
            
            result = test_suite_with_processor.processor.process_segments([test_segment])
            corrected_text = result.segments[0].text if result.segments else input_text
            
            if corrected_text == expected:
                correct_count += 1
        
        high_confidence_rate = (correct_count / len(high_confidence_cases)) * 100
        
        assert high_confidence_rate >= 85.0, (
            f"High confidence correction rate {high_confidence_rate:.1f}% "
            f"below 85% threshold"
        )


class TestGoldenDatasetIntegrity:
    """Test the integrity and consistency of the golden dataset itself."""
    
    def test_dataset_structure(self, asr_test_suite):
        """Test that dataset has proper structure and required fields."""
        dataset = asr_test_suite.golden_dataset
        
        # Check top-level structure
        assert 'asr_test_dataset' in dataset
        test_data = dataset['asr_test_dataset']
        
        # Check metadata
        required_metadata = ['version', 'created', 'total_cases', 'categories']
        for field in required_metadata:
            assert field in test_data, f"Missing required field: {field}"
        
        # Check categories
        expected_categories = [
            'phonetic_substitution',
            'case_variations', 
            'compound_words',
            'asr_transcription_errors',
            'diacritical_issues'
        ]
        
        for category in expected_categories:
            assert category in test_data['categories'], f"Missing category: {category}"
    
    def test_test_case_completeness(self, asr_test_suite):
        """Test that all test cases have required fields."""
        required_fields = ['id', 'input', 'expected', 'category', 'pattern', 
                          'difficulty', 'confidence_threshold']
        
        for test_case in asr_test_suite.get_all_test_cases():
            for field in required_fields:
                assert field in test_case, (
                    f"Test case {test_case.get('id', 'unknown')} missing field: {field}"
                )
            
            # Check field types and ranges
            assert isinstance(test_case['confidence_threshold'], (int, float))
            assert 0.0 <= test_case['confidence_threshold'] <= 1.0
            assert test_case['difficulty'] in ['easy', 'medium', 'hard']
    
    def test_case_count_accuracy(self, asr_test_suite):
        """Test that total case count matches actual cases."""
        dataset = asr_test_suite.golden_dataset['asr_test_dataset']
        declared_total = dataset['total_cases']
        actual_total = len(asr_test_suite.get_all_test_cases())
        
        assert actual_total == declared_total, (
            f"Declared total cases ({declared_total}) doesn't match "
            f"actual count ({actual_total})"
        )
        
        # Ensure we have at least 50 cases as specified in acceptance criteria
        assert actual_total >= 50, f"Need at least 50 test cases, found {actual_total}"
    
    def test_unique_test_ids(self, asr_test_suite):
        """Test that all test case IDs are unique."""
        test_ids = [tc['id'] for tc in asr_test_suite.get_all_test_cases()]
        unique_ids = set(test_ids)
        
        assert len(test_ids) == len(unique_ids), (
            f"Duplicate test IDs found: {len(test_ids)} total vs {len(unique_ids)} unique"
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])