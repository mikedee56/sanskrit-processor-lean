# ASR Testing Framework Documentation

This comprehensive testing framework ensures the quality, performance, and reliability of the Sanskrit ASR correction system.

## Overview

The testing framework consists of:
- **Golden Dataset**: 52+ carefully curated ASR error examples with expected corrections
- **Test Suites**: Unit, integration, acceptance, and performance tests
- **Test Data Generation**: Tools for creating realistic ASR test data
- **CI/CD Integration**: Automated testing on code changes
- **Performance Benchmarking**: Automated performance regression detection

## Quick Start

### Running All Tests
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-benchmark pytest-mock

# Run complete test suite
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html
```

### Running Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Golden dataset acceptance tests  
pytest tests/acceptance/test_golden_dataset.py -v

# Performance benchmarks
pytest tests/performance/ -v --benchmark-only

# Integration tests
pytest tests/integration/ -v
```

## Test Directory Structure

```
tests/
├── fixtures/                    # Test data and expected outputs
│   ├── asr_golden_dataset.json  # 52 curated test cases
│   ├── sample_asr_files/        # Sample SRT files for testing
│   ├── expected_outputs/        # Expected correction results
│   └── generated/               # Generated test files
├── unit/                        # Unit tests for components
│   ├── test_asr_processor.py    # Core processor unit tests
│   ├── test_fuzzy_matcher.py    # Fuzzy matching tests
│   └── test_systematic_matcher.py  # Systematic matching tests
├── integration/                 # Integration tests
│   ├── test_asr_pipeline.py     # End-to-end pipeline tests
│   └── test_cli_integration.py  # CLI integration tests
├── performance/                 # Performance benchmarks
│   ├── test_speed_benchmarks.py # Processing speed tests
│   └── test_memory_benchmarks.py # Memory usage tests
├── acceptance/                  # Acceptance tests
│   ├── test_golden_dataset.py   # Golden dataset validation
│   └── test_real_world_files.py # Real-world file testing
└── utils/                       # Test utilities
    ├── test_data_generator.py    # Generate realistic test data
    └── test_helpers.py          # Common test helper functions
```

## Golden Dataset

The golden dataset (`tests/fixtures/asr_golden_dataset.json`) contains 52 carefully curated test cases across 5 categories:

### Categories
1. **Phonetic Substitutions** (15 cases): `ph→f`, `th→t`, `v→w`, `sh→s`
2. **Case Variations** (10 cases): ALL CAPS, lowercase, Title Case
3. **Compound Words** (10 cases): Space handling, hyphenation
4. **ASR Transcription Errors** (10 cases): Heavy corruption, phonetic errors
5. **Diacritical Issues** (7 cases): Missing diacritical marks

### Example Test Case
```json
{
  "id": "ph_001",
  "input": "filosofy",
  "expected": "philosophy",
  "category": "phonetic_substitution",
  "pattern": "ph→f", 
  "difficulty": "easy",
  "confidence_threshold": 0.9,
  "notes": "Common ASR phonetic error"
}
```

## Test Data Generation

Use the test data generator to create realistic ASR test files:

```bash
# Generate complete test suite
python tests/utils/test_data_generator.py

# This creates:
# - Small files (50 segments) with 0% and 30% error rates
# - Medium files (200 segments) with 0% and 40% error rates  
# - Large files (500 segments) with 0% and 25% error rates
# - Stress test file (100 segments) with 80% error rate
```

### Generating Custom Test Data
```python
from tests.utils.test_data_generator import ASRTestDataGenerator

generator = ASRTestDataGenerator(seed=42)  # Reproducible results

# Create file with specific parameters
test_file = generator.create_test_srt_file(
    num_segments=100,
    error_rate=0.3,
    filename="custom_test.srt"
)

# Generate edge case scenarios
edge_cases = generator.create_edge_case_test_data()
```

## Performance Benchmarks

### Speed Requirements
- **Small files** (50-100 segments): < 2.0s, >50 segments/sec
- **Medium files** (200-500 segments): < 5.0s, >80 segments/sec  
- **Large files** (500+ segments): < 10.0s, >100 segments/sec

### Running Benchmarks
```bash
# Run all performance tests
pytest tests/performance/ -v --benchmark-only

# Specific benchmark types
pytest tests/performance/test_speed_benchmarks.py::TestProcessingSpeedBenchmarks -v

# Memory benchmarks  
pytest tests/performance/test_speed_benchmarks.py::TestMemoryPerformance -v

# Regression detection
pytest tests/performance/test_speed_benchmarks.py::TestRegressionDetection -v
```

### Interpreting Results
```bash
# Example benchmark output
test_small_file_speed_benchmark: 75 segments in 0.85s (88.2 segments/sec) PASSED
test_medium_file_speed_benchmark: 350 segments in 3.12s (112.2 segments/sec) PASSED  
test_large_file_speed_benchmark: 750 segments in 6.45s (116.3 segments/sec) PASSED
```

## Test Coverage Requirements

### Minimum Coverage Targets
- **Overall ASR Components**: >90%
- **ASR Mode Implementation**: >95%
- **Fuzzy Matching**: >90%
- **Context Detection**: >85%
- **Systematic Matcher**: >90%

### Running Coverage Analysis
```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html

# Check coverage thresholds
pytest tests/ --cov=. --cov-fail-under=90
```

## Acceptance Criteria Validation

### Test Categories and Expected Rates
```python
# Category-specific correction rate requirements
expected_rates = {
    "phonetic_substitution": 80.0,      # Easy phonetic errors
    "case_variations": 70.0,            # Case handling
    "compound_words": 75.0,             # Word boundary handling
    "asr_transcription_errors": 60.0,   # Heavy corruption (harder)
    "diacritical_issues": 70.0          # Diacritical mark restoration
}
```

### Running Acceptance Tests
```bash
# Full golden dataset validation
pytest tests/acceptance/test_golden_dataset.py -v

# Category-specific tests
pytest tests/acceptance/test_golden_dataset.py::TestGoldenDatasetAccuracy::test_category_correction_rates -v

# Overall correction rate test
pytest tests/acceptance/test_golden_dataset.py::TestGoldenDatasetAccuracy::test_overall_correction_benchmark -v
```

## CI/CD Integration

The testing framework integrates with GitHub Actions for automated testing:

### Workflow Triggers
- **Push to main/master/develop**: Run full test suite
- **Pull requests**: Run full test suite  
- **Nightly schedule**: Run regression tests with comprehensive data generation

### Workflow Jobs
1. **Unit Tests**: Fast feedback on core functionality
2. **Integration Tests**: End-to-end pipeline validation
3. **Acceptance Tests**: Golden dataset validation
4. **Performance Tests**: Benchmark validation and regression detection
5. **Cross-Platform Tests**: Compatibility across OS and Python versions

### Test Results
- **Coverage reports**: Uploaded to Codecov
- **Performance benchmarks**: Archived as artifacts
- **Test summaries**: Available in GitHub Actions summary

## Adding New Tests

### Unit Test Template
```python
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sanskrit_processor_v2 import SanskritProcessor

class TestNewFeature:
    @pytest.fixture
    def processor(self):
        return SanskritProcessor(simple_mode=True, verbose=False)
    
    def test_new_feature_basic(self, processor):
        """Test basic functionality of new feature."""
        # Arrange
        input_data = "test input"
        expected = "expected output"
        
        # Act  
        result = processor.process_text(input_data)
        
        # Assert
        assert result == expected
```

### Golden Dataset Addition
To add new test cases to the golden dataset:

1. Edit `tests/fixtures/asr_golden_dataset.json`
2. Add test case to appropriate category
3. Ensure unique `id` and required fields
4. Update `total_cases` count
5. Run validation: `pytest tests/acceptance/test_golden_dataset.py::TestGoldenDatasetIntegrity -v`

### Performance Test Addition
```python
def test_new_performance_scenario(self, simple_processor):
    """Test performance of new scenario."""
    # Create test data
    test_segments = create_scenario_segments()
    
    # Measure performance
    start_time = time.time()
    result = simple_processor.process_segments(test_segments)
    processing_time = time.time() - start_time
    
    # Assert performance requirements
    assert processing_time < MAX_TIME_THRESHOLD
    assert len(result.segments) / processing_time > MIN_SPEED_THRESHOLD
```

## Troubleshooting

### Common Test Failures

**Golden Dataset Test Failures**
```bash
# Check if processor is correctly configured
pytest tests/acceptance/test_golden_dataset.py::TestGoldenDatasetIntegrity -v

# Debug specific test case
pytest tests/acceptance/test_golden_dataset.py -v -s -k "ph_001"
```

**Performance Test Failures**  
```bash
# Check system performance
python -c "
import time
from tests.utils.test_data_generator import ASRTestDataGenerator
from sanskrit_processor_v2 import SanskritProcessor

generator = ASRTestDataGenerator()
segments = generator.create_test_segments(100)
processor = SanskritProcessor(simple_mode=True)

start = time.time()
result = processor.process_segments(segments)
print(f'Processing time: {time.time() - start:.2f}s')
"
```

**Coverage Failures**
```bash
# Identify uncovered lines
pytest tests/ --cov=. --cov-report=term-missing

# Focus on specific module
pytest tests/ --cov=sanskrit_processor_v2 --cov-report=html
```

### Test Data Issues
```bash
# Regenerate test data
python tests/utils/test_data_generator.py

# Validate generated files
ls -la tests/fixtures/generated/

# Check SRT format validity  
head -20 tests/fixtures/generated/small_errors_50segs.srt
```

## Best Practices

### Test Writing Guidelines
1. **Arrange-Act-Assert**: Structure tests clearly
2. **Descriptive names**: Test method names should describe what is tested
3. **Independent tests**: Each test should be self-contained
4. **Fast execution**: Unit tests should run quickly
5. **Deterministic**: Tests should produce consistent results

### Performance Testing
1. **Baseline measurements**: Always establish performance baselines
2. **Multiple runs**: Use multiple benchmark iterations for accuracy
3. **Realistic data**: Use representative test data sizes
4. **Environment consistency**: Account for CI environment differences

### Golden Dataset Maintenance
1. **Regular review**: Periodically review test cases for relevance
2. **Balance categories**: Ensure good coverage across error types
3. **Real-world examples**: Prefer actual ASR errors over synthetic ones
4. **Version control**: Track changes to test cases with clear commit messages

## Integration with Development Workflow

### Pre-commit Testing
```bash
# Quick smoke test before commit
pytest tests/unit/test_asr_processor.py::TestSanskritProcessor::test_process_single_segment -v

# Performance check
pytest tests/performance/test_speed_benchmarks.py::TestRegressionDetection::test_baseline_performance_metrics -v
```

### Feature Development Testing
1. **Write tests first**: Start with failing tests for new features
2. **Incremental testing**: Run relevant tests frequently during development  
3. **Golden dataset validation**: Ensure new features don't break existing corrections
4. **Performance impact**: Check that new features don't cause performance regressions

### Release Testing
```bash
# Full test suite before release
pytest tests/ -v --cov=. --cov-report=term-missing

# Generate fresh test data
python tests/utils/test_data_generator.py  

# Performance baseline update
pytest tests/performance/ -v --benchmark-only --benchmark-json=release_benchmarks.json
```

This comprehensive testing framework ensures the Sanskrit ASR processor maintains high quality and performance standards while enabling confident development and deployment.