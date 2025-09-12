"""
Test Data Generation Tools for ASR Testing

Tools for generating realistic ASR test data with controlled error patterns
to support comprehensive testing of the Sanskrit processor.
"""

import random
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sanskrit_processor_v2 import SRTSegment


class ASRErrorPatterns:
    """Defines realistic ASR error patterns for test data generation."""
    
    # Phonetic substitution patterns (ASR commonly confuses these sounds)
    PHONETIC_PATTERNS = {
        'th→t': {'pattern': r'\bth', 'replacement': 't', 'probability': 0.3},
        'ph→f': {'pattern': r'\bph', 'replacement': 'f', 'probability': 0.4},
        'v→w': {'pattern': r'\bv', 'replacement': 'w', 'probability': 0.2},
        'sh→s': {'pattern': r'sh', 'replacement': 's', 'probability': 0.3},
        'ṣ→s': {'pattern': r'ṣ', 'replacement': 's', 'probability': 0.8},
        'ś→s': {'pattern': r'ś', 'replacement': 's', 'probability': 0.7},
        'ñ→n': {'pattern': r'ñ', 'replacement': 'n', 'probability': 0.9},
        'ṛ→r': {'pattern': r'ṛ', 'replacement': 'r', 'probability': 0.8},
        'ā→a': {'pattern': r'ā', 'replacement': 'a', 'probability': 0.6},
        'ī→i': {'pattern': r'ī', 'replacement': 'i', 'probability': 0.6},
        'ū→u': {'pattern': r'ū', 'replacement': 'u', 'probability': 0.6},
        'ṁ→m': {'pattern': r'ṁ', 'replacement': 'm', 'probability': 0.7}
    }
    
    # Case variation patterns
    CASE_PATTERNS = {
        'all_caps': {'probability': 0.1},
        'all_lower': {'probability': 0.3}, 
        'random_case': {'probability': 0.1}
    }
    
    # Common Sanskrit term corruptions by ASR systems
    TERM_CORRUPTIONS = {
        'yogavāsiṣṭha': ['yogabashi', 'yoga vasishta', 'yogabasishta'],
        'bhagavadgītā': ['bhagabat gita', 'bhagavat geeta', 'bhagawat gita'],
        'kṛṣṇa': ['krishna', 'krisna', 'krishn'],
        'rāmāyaṇa': ['ramayana', 'ramayan', 'ramayen'],
        'mahābhārata': ['mahabharata', 'maha bharata', 'mahabharat'],
        'patañjali': ['patanjali', 'patangali', 'patanjali'],
        'prāṇāyāma': ['pranayama', 'pranayam', 'pranayam'],
        'sādhana': ['sadhana', 'sadhan', 'sadhna'],
        'samādhi': ['samadhi', 'samadh', 'samadhi']
    }


class ASRTestDataGenerator:
    """Generate realistic ASR test data with controlled error patterns."""
    
    def __init__(self, seed: int = None):
        """Initialize generator with optional random seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
        
        self.error_patterns = ASRErrorPatterns()
        self.sanskrit_vocabulary = self._load_sanskrit_vocabulary()
    
    def _load_sanskrit_vocabulary(self) -> List[str]:
        """Load common Sanskrit terms for test generation."""
        # Basic Sanskrit vocabulary for test generation
        vocabulary = [
            'yoga', 'dharma', 'karma', 'bhakti', 'jñāna', 'mokṣa',
            'sādhana', 'samādhi', 'prāṇāyāma', 'mantra', 'guru',
            'śiva', 'viṣṇu', 'brahmā', 'gaṇeśa', 'durgā',
            'vedānta', 'sāṅkhya', 'rāja yoga', 'haṭha yoga',
            'upaniṣad', 'vedas', 'sūtra', 'śloka', 'mantra'
        ]
        return vocabulary
    
    def apply_phonetic_errors(self, text: str) -> Tuple[str, List[str]]:
        """Apply phonetic substitution errors to text."""
        modified_text = text
        applied_errors = []
        
        for error_type, pattern_info in self.error_patterns.PHONETIC_PATTERNS.items():
            if random.random() < pattern_info['probability']:
                pattern = pattern_info['pattern']
                replacement = pattern_info['replacement']
                
                if re.search(pattern, modified_text):
                    modified_text = re.sub(pattern, replacement, modified_text)
                    applied_errors.append(error_type)
        
        return modified_text, applied_errors
    
    def apply_case_errors(self, text: str) -> Tuple[str, List[str]]:
        """Apply case variation errors to text."""
        applied_errors = []
        
        # Apply all caps with some probability
        if random.random() < self.error_patterns.CASE_PATTERNS['all_caps']['probability']:
            text = text.upper()
            applied_errors.append('all_caps')
        
        # Apply all lowercase (more common in ASR)
        elif random.random() < self.error_patterns.CASE_PATTERNS['all_lower']['probability']:
            text = text.lower()
            applied_errors.append('all_lower')
        
        # Apply random case variations
        elif random.random() < self.error_patterns.CASE_PATTERNS['random_case']['probability']:
            text = ''.join(
                char.upper() if random.random() > 0.5 else char.lower()
                for char in text
            )
            applied_errors.append('random_case')
        
        return text, applied_errors
    
    def apply_term_corruptions(self, text: str) -> Tuple[str, List[str]]:
        """Apply known ASR term corruption patterns."""
        modified_text = text
        applied_errors = []
        
        for correct_term, corruptions in self.error_patterns.TERM_CORRUPTIONS.items():
            # Check if the correct term appears in text (case insensitive)
            if correct_term.lower() in modified_text.lower():
                # Apply corruption with some probability
                if random.random() < 0.4:  # 40% chance of corruption
                    corruption = random.choice(corruptions)
                    # Replace case-insensitively
                    modified_text = re.sub(
                        re.escape(correct_term), 
                        corruption, 
                        modified_text, 
                        flags=re.IGNORECASE
                    )
                    applied_errors.append(f'term_corruption_{correct_term}')
        
        return modified_text, applied_errors
    
    def generate_realistic_asr_errors(self, clean_text: str) -> Tuple[str, List[str]]:
        """Generate realistic ASR errors in clean Sanskrit text."""
        modified_text = clean_text
        all_applied_errors = []
        
        # Apply different types of errors in sequence
        error_functions = [
            self.apply_phonetic_errors,
            self.apply_case_errors,
            self.apply_term_corruptions
        ]
        
        for error_func in error_functions:
            modified_text, errors = error_func(modified_text)
            all_applied_errors.extend(errors)
        
        return modified_text, all_applied_errors
    
    def generate_sanskrit_sentence(self) -> str:
        """Generate a synthetic Sanskrit sentence for testing."""
        sentence_templates = [
            "In the {text1} we learn about {text2} and {text3}",
            "The sage teaches us {text1} through {text2}",
            "{text1} is the path to {text2} and {text3}",
            "Through {text1} and {text2} we achieve {text3}",
            "The practice of {text1} leads to {text2}",
            "In {text1} philosophy, {text2} is essential for {text3}",
            "The {text1} tradition emphasizes {text2} and {text3}",
            "Students of {text1} study both {text2} and {text3}"
        ]
        
        template = random.choice(sentence_templates)
        
        # Fill template with Sanskrit terms
        terms = random.sample(self.sanskrit_vocabulary, min(3, len(self.sanskrit_vocabulary)))
        
        return template.format(
            text1=terms[0] if len(terms) > 0 else 'yoga',
            text2=terms[1] if len(terms) > 1 else 'dharma', 
            text3=terms[2] if len(terms) > 2 else 'mokṣa'
        )
    
    def create_test_srt_file(self, 
                           num_segments: int = 100, 
                           error_rate: float = 0.3,
                           filename: str = None) -> Path:
        """Create synthetic SRT file with controlled error patterns."""
        
        segments = []
        
        for i in range(num_segments):
            # Generate clean Sanskrit sentence
            clean_text = self.generate_sanskrit_sentence()
            
            # Apply ASR errors based on error_rate
            if random.random() < error_rate:
                corrupted_text, applied_errors = self.generate_realistic_asr_errors(clean_text)
                
                segment = SRTSegment(
                    index=i + 1,
                    start_time=f"00:{i//20:02d}:{(i*3)%60:02d},000",
                    end_time=f"00:{i//20:02d}:{((i*3)+3)%60:02d},000",
                    text=corrupted_text
                )
                
                # Store metadata for validation (in real implementation)
                segment.metadata = {
                    'clean_text': clean_text,
                    'applied_errors': applied_errors,
                    'error_rate': error_rate
                }
            else:
                segment = SRTSegment(
                    index=i + 1,
                    start_time=f"00:{i//20:02d}:{(i*3)%60:02d},000",
                    end_time=f"00:{i//20:02d}:{((i*3)+3)%60:02d},000",
                    text=clean_text
                )
            
            segments.append(segment)
        
        # Save SRT file
        if filename is None:
            filename = f"generated_test_{num_segments}segs_{int(error_rate*100)}pct_errors.srt"
        
        return self._save_srt_file(segments, filename)
    
    def _save_srt_file(self, segments: List[SRTSegment], filename: str) -> Path:
        """Save segments as SRT file."""
        output_dir = Path(__file__).parent.parent / 'fixtures' / 'generated'
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(f"{segment.index}\n")
                f.write(f"{segment.start_time} --> {segment.end_time}\n")
                f.write(f"{segment.text}\n")
                f.write("\n")
        
        return output_path
    
    def create_test_suite_files(self) -> Dict[str, Path]:
        """Create a complete test suite of generated files."""
        
        test_files = {}
        
        # Small files for quick testing
        test_files['small_clean'] = self.create_test_srt_file(50, 0.0, 'small_clean_50segs.srt')
        test_files['small_errors'] = self.create_test_srt_file(50, 0.3, 'small_errors_50segs.srt')
        
        # Medium files for comprehensive testing  
        test_files['medium_clean'] = self.create_test_srt_file(200, 0.0, 'medium_clean_200segs.srt')
        test_files['medium_errors'] = self.create_test_srt_file(200, 0.4, 'medium_errors_200segs.srt')
        
        # Large files for performance testing
        test_files['large_clean'] = self.create_test_srt_file(500, 0.0, 'large_clean_500segs.srt')
        test_files['large_errors'] = self.create_test_srt_file(500, 0.25, 'large_errors_500segs.srt')
        
        # High error rate for stress testing
        test_files['stress_errors'] = self.create_test_srt_file(100, 0.8, 'stress_high_errors_100segs.srt')
        
        return test_files
    
    def generate_mock_external_responses(self) -> Dict[str, Any]:
        """Generate mock responses for external service testing."""
        
        mock_responses = {
            'mcp_responses': {
                'semantic_analysis': {
                    'confidence': 0.85,
                    'corrections': [
                        {'original': 'filosofy', 'corrected': 'philosophy', 'confidence': 0.9},
                        {'original': 'darma', 'corrected': 'dharma', 'confidence': 0.95}
                    ]
                },
                'batch_processing': {
                    'processed_count': 100,
                    'success_rate': 0.92,
                    'processing_time': 2.3
                }
            },
            'api_responses': {
                'scripture_lookup': [
                    {
                        'verse': 'योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय',
                        'translation': 'Established in yoga, perform actions abandoning attachment, O Dhananjaya',
                        'reference': 'Bhagavad Gītā 2.48'
                    }
                ],
                'iast_validation': {
                    'valid_terms': ['yoga', 'dharma', 'karma'],
                    'invalid_terms': ['yogabashi', 'darma'],
                    'suggestions': {
                        'yogabashi': 'yogavāsiṣṭha',
                        'darma': 'dharma'
                    }
                }
            }
        }
        
        return mock_responses
    
    def create_edge_case_test_data(self) -> List[Dict[str, Any]]:
        """Create edge case test scenarios."""
        
        edge_cases = [
            # Empty segments
            {'input': '', 'expected': '', 'description': 'empty_segment'},
            
            # Very long segments 
            {'input': ' '.join(['yoga'] * 100), 'expected': ' '.join(['yoga'] * 100), 
             'description': 'very_long_segment'},
            
            # Mixed language segments
            {'input': 'English text with yoga and Sanskrit dharma mixed together',
             'expected': 'English text with yoga and Sanskrit dharma mixed together',
             'description': 'mixed_language'},
            
            # Special characters
            {'input': 'yoga! dharma? (sanskrit) [terms] - punctuation',
             'expected': 'yoga! dharma? (sanskrit) [terms] - punctuation',
             'description': 'special_characters'},
            
            # Numbers and Sanskrit
            {'input': '108 repetitions of the mantra Om',
             'expected': '108 repetitions of the mantra Om',
             'description': 'numbers_and_sanskrit'},
            
            # HTML-style formatting
            {'input': '<i>italicized yoga</i> and <b>bold dharma</b>',
             'expected': '<i>italicized yoga</i> and <b>bold dharma</b>',
             'description': 'html_formatting'},
            
            # Multiple corrections in one segment
            {'input': 'filosofy teaches us about darma and krisna',
             'expected': 'philosophy teaches us about dharma and kṛṣṇa',
             'description': 'multiple_corrections'},
        ]
        
        return edge_cases


def main():
    """Generate test data files for the testing framework."""
    
    print("Generating ASR test data files...")
    
    # Initialize generator with fixed seed for reproducible test data
    generator = ASRTestDataGenerator(seed=42)
    
    # Create test suite files
    generated_files = generator.create_test_suite_files()
    
    print("\nGenerated test files:")
    for file_type, file_path in generated_files.items():
        print(f"  {file_type}: {file_path}")
    
    # Generate mock responses file
    mock_responses = generator.generate_mock_external_responses()
    mock_file = Path(__file__).parent.parent / 'fixtures' / 'mock_external_responses.json'
    
    with open(mock_file, 'w', encoding='utf-8') as f:
        json.dump(mock_responses, f, indent=2, ensure_ascii=False)
    
    print(f"\nGenerated mock responses: {mock_file}")
    
    # Generate edge case test data
    edge_cases = generator.create_edge_case_test_data()
    edge_case_file = Path(__file__).parent.parent / 'fixtures' / 'edge_case_test_data.json'
    
    with open(edge_case_file, 'w', encoding='utf-8') as f:
        json.dump(edge_cases, f, indent=2, ensure_ascii=False)
    
    print(f"Generated edge cases: {edge_case_file}")
    
    print("\nTest data generation complete!")


if __name__ == "__main__":
    main()