"""ASR Pattern Analyzer - Extracts common ASR error patterns from sample files."""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)

class ASRPatternAnalyzer:
    """Analyzes ASR files to extract common error patterns for lexicon enhancement."""
    
    def __init__(self):
        self.error_patterns: Dict[str, List[str]] = defaultdict(list)
        self.phonetic_substitutions: Dict[str, str] = {}
        self.case_variations: Set[str] = set()
        self.compound_errors: List[Tuple[str, str]] = []
        self.frequency_counts: Counter = Counter()
        
        # ASR error categories from story analysis
        self.known_patterns = {
            'phonetic_substitutions': {
                'ph': 'f', 'th': 't', 'bh': 'b', 'dh': 'd', 
                'v': 'w', 'sh': 's', 'gya': 'ya', 'ś': 's', 'ṣ': 's'
            },
            'dropped_consonants': {
                'utpatti': 'utpati', 'vasiṣṭha': 'vasitta', 'śiṣṭha': 'sishtha'  
            },
            'compound_word_errors': {
                'Yogavāsiṣṭha': 'yogabashi', 'Vaśiṣṭha': 'shivashistha', 
                'mala-grasta': 'malagrasth'
            }
        }
    
    def analyze_file(self, filepath: Path) -> Dict[str, int]:
        """Analyze a single SRT file for ASR error patterns."""
        errors_found = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract text content from SRT (skip timestamps)
            text_lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not re.match(r'^\d+$', line) and not re.match(r'^\d{2}:\d{2}:\d{2}', line):
                    text_lines.append(line)
            
            full_text = ' '.join(text_lines)
            
            # Analyze for known error patterns
            errors_found.update(self._find_phonetic_errors(full_text))
            errors_found.update(self._find_case_variations(full_text))
            errors_found.update(self._find_compound_errors(full_text))
            errors_found.update(self._find_dropped_consonants(full_text))
            
            logger.info(f"Analyzed {filepath.name}: found {len(errors_found)} error patterns")
            
        except Exception as e:
            logger.error(f"Error analyzing {filepath}: {e}")
            
        return errors_found
    
    def _find_phonetic_errors(self, text: str) -> Dict[str, int]:
        """Find phonetic substitution patterns."""
        errors = {}
        
        # Known problematic terms from story analysis
        known_errors = {
            'yogabashi': 'Yogavāsiṣṭha',
            'shivashistha': 'Vaśiṣṭha', 
            'darma': 'dharma',
            'barata': 'bharata',
            'wasistha': 'vasiṣṭha',
            'filosophy': 'philosophy',
            'siva': 'śiva',
            'gnana': 'jñāna',
            'yani': 'gyani'
        }
        
        text_lower = text.lower()
        for error_term, correct_term in known_errors.items():
            count = len(re.findall(r'\b' + re.escape(error_term) + r'\b', text_lower))
            if count > 0:
                errors[f"{error_term} → {correct_term}"] = count
                self.error_patterns['phonetic_substitutions'].append((error_term, correct_term, count))
                
        return errors
    
    def _find_case_variations(self, text: str) -> Dict[str, int]:
        """Find inconsistent capitalization patterns."""
        errors = {}
        
        # Major Sanskrit terms that should have consistent capitalization
        terms_to_check = ['dharma', 'karma', 'yoga', 'jnana', 'bhagavad gita', 'mahabharata']
        
        for term in terms_to_check:
            variations = [
                term.lower(),
                term.upper(), 
                term.title(),
                ' '.join(word.capitalize() for word in term.split())
            ]
            
            variation_counts = []
            for variation in set(variations):
                count = len(re.findall(r'\b' + re.escape(variation) + r'\b', text))
                if count > 0:
                    variation_counts.append((variation, count))
            
            if len(variation_counts) > 1:  # Multiple case variations found
                total_count = sum(count for _, count in variation_counts)
                errors[f"case_variations_{term}"] = total_count
                self.error_patterns['case_variations'].extend(variation_counts)
                
        return errors
    
    def _find_compound_errors(self, text: str) -> Dict[str, int]:
        """Find compound word spacing/hyphenation errors."""
        errors = {}
        
        compound_patterns = [
            ('karma yoga', 'karma-yoga'),
            ('bhagavad gita', 'Bhagavad-gītā'),
            ('maha bharata', 'Mahābhārata'),
            ('sapta bhoomi', 'sapta-bhūmi'),
            ('yoga vasistha', 'Yogavāsiṣṭha')
        ]
        
        text_lower = text.lower()
        for spaced, hyphenated in compound_patterns:
            count = len(re.findall(r'\b' + re.escape(spaced) + r'\b', text_lower))
            if count > 0:
                errors[f"{spaced} → {hyphenated}"] = count
                self.error_patterns['compound_errors'].append((spaced, hyphenated, count))
                
        return errors
    
    def _find_dropped_consonants(self, text: str) -> Dict[str, int]:
        """Find dropped double consonants and other ASR consonant errors."""
        errors = {}
        
        consonant_patterns = [
            ('utpati', 'utpatti'),
            ('vasitta', 'vasiṣṭha'), 
            ('shivaasishtha', 'śivaśiṣṭha'),
            ('bhoomikaas', 'bhūmikāḥ'),
            ('jnana', 'jñāna')  # Missing diacritical
        ]
        
        text_lower = text.lower()
        for error_form, correct_form in consonant_patterns:
            count = len(re.findall(r'\b' + re.escape(error_form) + r'\b', text_lower))
            if count > 0:
                errors[f"{error_form} → {correct_form}"] = count
                self.error_patterns['dropped_consonants'].append((error_form, correct_form, count))
                
        return errors
    
    def analyze_directory(self, directory: Path, pattern: str = "*.srt") -> Dict[str, Dict]:
        """Analyze all files in directory matching pattern."""
        results = {}
        
        for filepath in directory.glob(pattern):
            if filepath.is_file():
                file_errors = self.analyze_file(filepath)
                if file_errors:
                    results[filepath.name] = file_errors
                    
        return results
    
    def generate_classification_report(self) -> Dict[str, any]:
        """Generate comprehensive ASR error pattern classification."""
        
        # Count total errors by category
        category_counts = {}
        for category, patterns in self.error_patterns.items():
            category_counts[category] = len(patterns)
            
        # Identify top 200 most frequent errors
        all_errors = []
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if len(pattern) >= 3:  # Has count
                    error_term, correct_term, count = pattern
                    all_errors.append({
                        'error_term': error_term,
                        'correct_term': correct_term, 
                        'frequency': count,
                        'category': category
                    })
        
        # Sort by frequency and take top 200
        top_errors = sorted(all_errors, key=lambda x: x['frequency'], reverse=True)[:200]
        
        return {
            'summary': {
                'total_categories': len(self.error_patterns),
                'total_patterns': sum(len(patterns) for patterns in self.error_patterns.values()),
                'category_breakdown': category_counts
            },
            'top_200_errors': top_errors,
            'methodology': {
                'analysis_approach': 'Pattern-based ASR error detection',
                'categories': list(self.error_patterns.keys()),
                'confidence_scoring': 'Based on frequency and pattern matching',
                'validation_method': 'Cross-reference with known Sanskrit terms'
            }
        }
    
    def export_patterns_to_yaml(self, output_path: Path):
        """Export identified patterns to YAML for lexicon integration."""
        
        report = self.generate_classification_report()
        
        # Convert top errors to ASR correction format
        asr_corrections = []
        for error in report['top_200_errors']:
            correction_entry = {
                'original_term': error['error_term'],
                'transliteration': error['correct_term'],
                'asr_common_error': True,
                'error_type': error['category'],
                'frequency': 'high' if error['frequency'] >= 10 else 'medium' if error['frequency'] >= 3 else 'low',
                'confidence': 1.0 if error['frequency'] >= 5 else 0.9,
                'category': 'concept',  # Will be refined per term
                'variations': [error['error_term'].lower(), error['error_term'].upper()],
                'source_authority': 'ASR_Pattern_Analysis'
            }
            asr_corrections.append(correction_entry)
        
        output_data = {
            'metadata': {
                'version': '1.0',
                'description': 'ASR-specific corrections derived from pattern analysis',
                'analysis_date': 'Generated by ASRPatternAnalyzer',
                'total_patterns': len(asr_corrections)
            },
            'asr_corrections': asr_corrections
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(output_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
        logger.info(f"Exported {len(asr_corrections)} ASR corrections to {output_path}")

def main():
    """Standalone script to analyze ASR patterns."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze ASR error patterns in SRT files')
    parser.add_argument('input_dir', type=Path, help='Directory containing SRT files to analyze')
    parser.add_argument('--output', type=Path, default='asr_patterns_analysis.yaml', 
                       help='Output file for analysis results')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    analyzer = ASRPatternAnalyzer()
    
    # Analyze all SRT files in directory
    results = analyzer.analyze_directory(args.input_dir)
    
    # Generate and export classification report
    analyzer.export_patterns_to_yaml(args.output)
    
    print(f"Analysis complete. Results saved to {args.output}")
    print(f"Analyzed {len(results)} files with ASR error patterns")

if __name__ == "__main__":
    main()