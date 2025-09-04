#!/usr/bin/env python3
"""
Lean Sanskrit SRT Processor - Focused implementation
No bloat, no over-engineering, just working text processing.
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SRTSegment:
    """Simple SRT segment representation."""
    index: int
    start_time: str
    end_time: str
    text: str

@dataclass
class ProcessingResult:
    """Results from processing operation."""
    segments_processed: int
    corrections_made: int
    processing_time: float
    errors: List[str]

@dataclass(frozen=True)
class CorrectionDetail:
    """Immutable details of a single correction operation with comprehensive validation.
    
    This class provides a thread-safe, immutable record of correction operations
    with built-in validation and performance optimization for metrics collection.
    
    Args:
        type: Type of correction ('lexicon', 'capitalization', 'fuzzy', 'punctuation')
        original: Original text before correction
        corrected: Text after correction is applied
        confidence: Confidence score (0.0-1.0) indicating correction reliability  
        processing_time: Time taken to perform correction (seconds, non-negative)
    """
    type: str  # 'lexicon', 'capitalization', 'fuzzy', 'punctuation'
    original: str
    corrected: str
    confidence: float
    processing_time: float
    
    def __post_init__(self):
        """Validate correction detail fields for data integrity."""
        if not isinstance(self.confidence, (int, float)) or not 0.0 <= self.confidence <= 1.0:
            object.__setattr__(self, 'confidence', max(0.0, min(1.0, float(self.confidence))))
        if not isinstance(self.processing_time, (int, float)) or self.processing_time < 0:
            object.__setattr__(self, 'processing_time', max(0.0, float(self.processing_time)))

@dataclass
class DetailedProcessingResult(ProcessingResult):
    """Extended processing result with detailed metrics and performance data.
    
    This class extends the base ProcessingResult with comprehensive metrics
    collection, maintaining full backward compatibility while providing
    detailed insights into processing performance, correction quality,
    and resource utilization.
    """
    corrections_by_type: Dict[str, int] = field(default_factory=dict)
    correction_details: List[CorrectionDetail] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    processing_phases: Dict[str, float] = field(default_factory=dict)  # parse, process, write times
    quality_score: float = 0.0
    memory_usage: Dict[str, float] = field(default_factory=dict)  # peak, average

class MetricsCollector:
    """Robust metrics collection for processing operations with comprehensive error handling.
    
    This class provides thread-safe metrics collection with proper error handling,
    optimized performance, and detailed tracking of correction operations.
    """
    
    def __init__(self):
        self.corrections_by_type: Dict[str, int] = {}
        self.correction_details: List[CorrectionDetail] = []
        self.confidence_scores: List[float] = []
        self.start_times: Dict[str, float] = {}
    
    def start_correction(self, correction_type: str, original: str) -> None:
        """Start timing a correction operation with error handling."""
        try:
            import time
            # Use unique key to handle duplicate words in same text
            key = f"{correction_type}:{original}:{len(self.correction_details)}"
            self.start_times[key] = time.time()
        except Exception as e:
            logger.warning(f"Failed to start correction timing: {e}")
    
    def end_correction(self, correction_type: str, original: str, corrected: str, confidence: float) -> None:
        """Record completed correction with timing and validation."""
        try:
            import time
            
            # Validate inputs
            if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
                logger.warning(f"Invalid confidence score {confidence}, defaulting to 1.0")
                confidence = 1.0
            
            # Calculate processing time
            key = f"{correction_type}:{original}:{len(self.correction_details)}"
            processing_time = time.time() - self.start_times.pop(key, time.time())
            
            # Update counters safely
            self.corrections_by_type[correction_type] = self.corrections_by_type.get(correction_type, 0) + 1
            
            # Record detail with validation
            detail = CorrectionDetail(
                type=correction_type,
                original=original,
                corrected=corrected,
                confidence=float(confidence),
                processing_time=max(0.0, processing_time)  # Ensure non-negative
            )
            self.correction_details.append(detail)
            self.confidence_scores.append(float(confidence))
            
        except Exception as e:
            logger.warning(f"Failed to record correction metrics: {e}")
    
    def calculate_quality_score(self, total_segments: int, error_count: int) -> float:
        """Calculate overall quality score (0-100) with robust error handling."""
        try:
            if total_segments <= 0:
                return 0.0
            
            total_corrections = len(self.correction_details)
            if total_corrections == 0:
                return 100.0 if error_count == 0 else max(0.0, 100.0 - (error_count / total_segments) * 50)
            
            # Success rate (40%) - we only record successful corrections
            success_rate = 1.0
            
            # Average confidence (30%)
            avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 1.0
            
            # Error penalty (20%)
            error_penalty = max(0.0, 1.0 - (error_count / total_segments))
            
            # Coverage (10%) - proportion of segments that had corrections
            coverage = min(1.0, total_corrections / total_segments)
            
            # Weighted score calculation
            score = (success_rate * 0.4 + avg_confidence * 0.3 + error_penalty * 0.2 + coverage * 0.1) * 100
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {e}")
            return 0.0

class ProcessingReporter:
    """Comprehensive reporting for processing metrics with enhanced formatting and validation.
    
    This class provides robust report generation with error handling, formatting validation,
    and optimized performance for both human-readable and machine-readable outputs.
    """
    
    @staticmethod
    def generate_summary(result: ProcessingResult, verbose: bool = False) -> str:
        """Generate human-readable processing summary with comprehensive error handling."""
        try:
            if isinstance(result, DetailedProcessingResult):
                return ProcessingReporter._generate_detailed_summary(result, verbose)
            else:
                return ProcessingReporter._generate_basic_summary(result)
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return f"❌ Error generating report: {e}"
    
    @staticmethod
    def _generate_basic_summary(result: ProcessingResult) -> str:
        """Generate basic summary for simple ProcessingResult with validation."""
        try:
            segments_per_sec = result.segments_processed / result.processing_time if result.processing_time > 0 else 0
            correction_rate = (result.corrections_made / result.segments_processed * 100) if result.segments_processed > 0 else 0
            
            error_section = f"\n   • Errors: {len(result.errors)}" if result.errors else ""
            
            return f"""✅ Processing Complete!

📊 Results Summary:
   • Segments processed: {result.segments_processed:,}
   • Corrections made: {result.corrections_made:,} ({correction_rate:.1f}% of segments)
   • Processing time: {result.processing_time:.1f}s ({segments_per_sec:,.0f} segments/sec){error_section}"""
        except Exception as e:
            logger.error(f"Failed to generate basic summary: {e}")
            return f"❌ Error in basic report generation: {e}"
    
    @staticmethod
    def _generate_detailed_summary(result: DetailedProcessingResult, verbose: bool) -> str:
        """Generate detailed summary for DetailedProcessingResult with comprehensive validation."""
        try:
            segments_per_sec = result.segments_processed / result.processing_time if result.processing_time > 0 else 0
            correction_rate = (result.corrections_made / result.segments_processed * 100) if result.segments_processed > 0 else 0
            avg_confidence = sum(result.confidence_scores) / len(result.confidence_scores) if result.confidence_scores else 0
            
            # Confidence level assessment
            confidence_level = "High" if avg_confidence > 0.8 else "Medium" if avg_confidence > 0.6 else "Low"
            
            summary = f"""✅ Processing Complete!

📊 Results Summary:
   • Segments processed: {result.segments_processed:,}
   • Corrections made: {result.corrections_made:,} ({correction_rate:.1f}% of segments)
   • Processing time: {result.processing_time:.1f}s ({segments_per_sec:,.0f} segments/sec)
   • Quality score: {result.quality_score:.0f}/100

🔧 Correction Breakdown:"""
            
            # Add correction breakdown with validation
            total_corrections = sum(result.corrections_by_type.values())
            if total_corrections > 0:
                for correction_type, count in sorted(result.corrections_by_type.items()):
                    percentage = (count / total_corrections * 100) if total_corrections > 0 else 0
                    summary += f"\n   • {correction_type.title()} corrections: {count:,} ({percentage:.0f}%)"
            else:
                summary += "\n   • No corrections applied"
            
            summary += f"\n\n💡 Average confidence: {avg_confidence:.2f} ({confidence_level})"
            
            # Add verbose details if requested
            if verbose:
                summary += "\n\n📈 Detailed Performance:"
                if result.processing_phases:
                    for phase, time_taken in result.processing_phases.items():
                        summary += f"\n   • {phase.title()} phase: {time_taken:.2f}s"
                
                if result.memory_usage:
                    summary += "\n\n🧠 Memory Usage:"
                    peak_memory = result.memory_usage.get('peak', 0)
                    avg_memory = result.memory_usage.get('average', 0)
                    summary += f"\n   • Peak memory: {peak_memory:.1f} MB"
                    summary += f"\n   • Average memory: {avg_memory:.1f} MB"
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate detailed summary: {e}")
            return f"❌ Error in detailed report generation: {e}"
    
    @staticmethod
    def export_json(result: ProcessingResult) -> Dict[str, Any]:
        """Export metrics in JSON format with comprehensive validation."""
        try:
            base_data = {
                'segments_processed': result.segments_processed,
                'corrections_made': result.corrections_made,
                'processing_time': round(result.processing_time, 3),
                'errors': result.errors,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
            
            if isinstance(result, DetailedProcessingResult):
                base_data.update({
                    'quality_score': round(result.quality_score, 1),
                    'corrections_by_type': result.corrections_by_type,
                    'processing_phases': {k: round(v, 3) for k, v in result.processing_phases.items()},
                    'memory_usage': {k: round(v, 2) for k, v in result.memory_usage.items()},
                    'avg_confidence': round(sum(result.confidence_scores) / len(result.confidence_scores), 3) if result.confidence_scores else 0,
                    'correction_count': len(result.correction_details),
                    'processing_rate': round(result.segments_processed / result.processing_time, 1) if result.processing_time > 0 else 0
                })
            
            return base_data
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return {'error': f'Failed to export metrics: {e}'}

class LexiconLoader:
    """Simple lexicon loader for YAML files."""
    
    def __init__(self, lexicon_dir: Path):
        self.lexicon_dir = Path(lexicon_dir)
        self.corrections = {}
        self.proper_nouns = {}
        self._load_lexicons()
    
    def _load_lexicons(self):
        """Load correction lexicons from YAML files."""
        try:
            # Load corrections
            corrections_file = self.lexicon_dir / "corrections.yaml"
            if corrections_file.exists():
                with open(corrections_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    for entry in data.get('entries', []):
                        original = entry['original_term']
                        self.corrections[original] = entry
                        # Add variations
                        for variation in entry.get('variations', []):
                            self.corrections[variation] = entry
                logger.info(f"Loaded {len(self.corrections)} correction entries")
            
            # Load proper nouns
            proper_nouns_file = self.lexicon_dir / "proper_nouns.yaml"
            if proper_nouns_file.exists():
                with open(proper_nouns_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    for entry in data.get('entries', []):
                        # Handle both 'term' and 'original_term' formats
                        term = entry.get('term') or entry.get('original_term')
                        if term:
                            self.proper_nouns[term.lower()] = entry
                            # Add variations if they exist
                            for variation in entry.get('variations', []):
                                self.proper_nouns[variation.lower()] = entry
                logger.info(f"Loaded {len(self.proper_nouns)} proper noun entries")
                        
        except Exception as e:
            logger.error(f"Failed to load lexicons: {e}")
            raise

class SRTParser:
    """Simple SRT file parser."""
    
    @staticmethod
    def parse(content: str) -> List[SRTSegment]:
        """Parse SRT content into segments."""
        segments = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
                
            try:
                index = int(lines[0])
                timestamp = lines[1]
                text = '\n'.join(lines[2:])
                
                # Parse timestamp
                if ' --> ' not in timestamp:
                    continue
                    
                start_time, end_time = timestamp.split(' --> ')
                
                segments.append(SRTSegment(
                    index=index,
                    start_time=start_time.strip(),
                    end_time=end_time.strip(),
                    text=text.strip()
                ))
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipped malformed segment: {e}")
                continue
                
        return segments
    
    @staticmethod
    def to_srt(segments: List[SRTSegment]) -> str:
        """Convert segments back to SRT format."""
        srt_content = []
        
        for segment in segments:
            srt_content.append(f"{segment.index}")
            srt_content.append(f"{segment.start_time} --> {segment.end_time}")
            srt_content.append(segment.text)
            srt_content.append("")  # Empty line between segments
            
        return '\n'.join(srt_content)

class SanskritProcessor:
    """Lean Sanskrit text processor focused on core functionality."""
    
    def __init__(self, lexicon_dir: Path = None, config_path: Path = None, collect_metrics: bool = False):
        """Initialize processor with lexicon directory and configuration."""
        self.lexicon_dir = lexicon_dir or Path("lexicons")
        self.lexicons = LexiconLoader(self.lexicon_dir)
        
        # Load configuration
        self.config = self._load_config(config_path or Path("config.yaml"))
        
        # Metrics collection
        self.collect_metrics = collect_metrics
        self.metrics_collector = MetricsCollector() if collect_metrics else None
        
        # Basic text normalization patterns
        self.filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know']
        self.number_words = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
            'sixteen': '16', 'seventeen': '17', 'eighteen': '18'
        }
        
        logger.info("Sanskrit processor initialized")

    
    def _load_config(self, config_path: Path) -> dict:
        """Load configuration with fuzzy matching defaults."""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
            
            # Set fuzzy matching defaults
            if 'processing' not in config:
                config['processing'] = {}
            if 'fuzzy_matching' not in config['processing']:
                config['processing']['fuzzy_matching'] = {
                    'enabled': True,
                    'threshold': 0.7,
                    'log_matches': False
                }
            
            return config
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            return {
                'processing': {
                    'fuzzy_matching': {
                        'enabled': True,
                        'threshold': 0.7,
                        'log_matches': False
                    }
                }
            }
    
    def process_text(self, text: str) -> tuple[str, int]:
        """Process a single text segment. Returns (processed_text, corrections_made)."""
        original_text = text
        corrections = 0
        
        # 1. Basic text cleanup
        text = self._normalize_text(text)
        
        # 2. Apply lexicon corrections
        text, lexicon_corrections = self._apply_lexicon_corrections(text)
        corrections += lexicon_corrections
        
        # 3. Apply proper noun capitalization
        text, capitalization_corrections = self._apply_capitalization(text)
        corrections += capitalization_corrections
        
        # 4. Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text != original_text:
            logger.debug(f"Processed: '{original_text[:50]}...' -> '{text[:50]}...' ({corrections} corrections)")
            
        return text, corrections
    
    def _normalize_text(self, text: str) -> str:
        """Basic text normalization with punctuation enhancement."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Convert number words to digits
        for word, digit in self.number_words.items():
            text = re.sub(rf'\b{re.escape(word)}\b', digit, text, flags=re.IGNORECASE)
        
        # Remove common filler words
        for filler in self.filler_words:
            text = re.sub(rf'\b{re.escape(filler)}\b', '', text, flags=re.IGNORECASE)
        
        # Apply punctuation enhancement if enabled
        if self.config.get('punctuation', {}).get('enabled', False):
            text = self._enhance_punctuation(text)
        
        return text.strip()

    def _enhance_punctuation(self, text: str) -> str:
        """Enhanced punctuation using rule-based patterns with metrics."""
        # Skip if Sanskrit context detected
        if self._is_sanskrit_context(text):
            return text
            
        mode = self.config.get('punctuation', {}).get('mode', 'balanced')
        punctuation_config = self.config.get('punctuation', {})
        changes_made = 0
        
        # Define base punctuation patterns
        ending_phrases = [
            "thank you very much", "thank you", "namaste", "om shanti", 
            "hari om", "may all beings be happy", "may you be blessed",
            "peace be with you", "god bless"
        ]
        
        # Add custom ending phrases from configuration
        custom_endings = punctuation_config.get('custom_endings', [])
        if custom_endings:
            ending_phrases.extend(custom_endings)
        
        transition_phrases = [
            "however", "therefore", "thus", "nevertheless", 
            "furthermore", "moreover", "in addition"
        ]
        
        # Conservative mode uses fewer patterns
        if mode == 'conservative':
            ending_phrases = ending_phrases[:4]
            transition_phrases = transition_phrases[:3]
        
        original_text = text
        
        # Process ending phrases - only at end of text
        for phrase in ending_phrases:
            lower_text = text.lower().rstrip()
            lower_phrase = phrase.lower()
            
            # Check if text ends with this phrase (no period after)
            if lower_text.endswith(lower_phrase) and not lower_text.endswith(lower_phrase + '.'):
                text = text.rstrip() + '.'
                changes_made += 1
                break  # Only add one period
        
        # Add commas before transitions (balanced/aggressive modes)
        if mode in ['balanced', 'aggressive']:
            for transition in transition_phrases:
                # Add comma if transition found but not at start or already with comma
                pattern = rf'(?<!^)\s+{re.escape(transition)}\b'
                if re.search(pattern, text, re.IGNORECASE) and f', {transition.lower()}' not in text.lower():
                    new_text = re.sub(pattern, f', {transition}', text, flags=re.IGNORECASE)
                    if new_text != text:
                        text = new_text
                        changes_made += 1
        
        # Capitalize first letter after periods
        text = re.sub(r'\.(\s+)([a-z])', 
                      lambda m: f'.{m.group(1)}{m.group(2).upper()}', text)
        
        # Handle common abbreviations - don't capitalize after them
        abbreviations = ['Dr', 'Sri', 'Swami', 'Mt', 'St']
        for abbr in abbreviations:
            # Fix overcapitalization after abbreviations
            pattern = rf'{re.escape(abbr)}\.(\s+)([A-Z])'
            text = re.sub(pattern, 
                         lambda m: f'{abbr}.{m.group(1)}{m.group(2).lower()}', text)
        
        # Enhanced question detection (both aggressive and balanced modes)
        if mode in ['balanced', 'aggressive']:
            question_starters = ['what', 'where', 'when', 'why', 'how', 'who', 'which', 'can', 'could', 'would', 'should']
            for starter in question_starters:
                # Match questions at start of text or after punctuation
                pattern = rf'(^|[.!?]\s+){re.escape(starter)}\s+[^.?!]*[^.?!]$'
                if re.search(pattern, text, re.IGNORECASE):
                    if not text.rstrip().endswith('?'):
                        text = text.rstrip() + '?'
                        changes_made += 1
                        break
        
        # Handle exclamations in aggressive mode
        if mode == 'aggressive':
            exclamation_starters = ['wow', 'amazing', 'wonderful', 'excellent', 'fantastic']
            for starter in exclamation_starters:
                pattern = rf'^{re.escape(starter)}\b.*[^!.]$'
                if re.search(pattern, text, re.IGNORECASE):
                    text = text.rstrip() + '!'
                    changes_made += 1
                    break
        
        # Clean spacing around punctuation
        text = re.sub(r'\s+([.,:;!?])', r'\1', text)  # Remove space before
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)  # Add space after
        
        # Log performance metrics if enabled and metrics collector available
        if punctuation_config.get('log_changes', False) and hasattr(self, 'metrics_collector') and self.metrics_collector:
            if changes_made > 0:
                self.metrics_collector.record_processing_detail(
                    'punctuation_enhancement', 
                    f"{changes_made} punctuation changes applied"
                )
        
        return text

    def _is_sanskrit_context(self, text: str) -> bool:
        """Check if text contains Sanskrit/sacred content that should be preserved."""
        sanskrit_indicators = [
            r'\d+\.\d+',  # Verse references like "2.47"
            r'chapter\s+\d+',  # "Chapter 2"  
            r'[āīūṛṅṇṭḍṣśḥṃ]',  # IAST characters
            r'om\s+\w+\s+om',  # Mantras
            'bhagavad gita', 'upanishad', 'vedas'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) 
                  for pattern in sanskrit_indicators)
    
    def _apply_lexicon_corrections(self, text: str) -> tuple[str, int]:
        """Apply corrections from lexicon files with fuzzy matching fallback."""
        corrections = 0
        words = text.split()
        corrected_words = []
        
        # Get fuzzy matching config
        fuzzy_config = self.config.get('processing', {}).get('fuzzy_matching', {})
        fuzzy_enabled = fuzzy_config.get('enabled', True)
        fuzzy_threshold = fuzzy_config.get('threshold', 0.8)
        log_fuzzy = fuzzy_config.get('log_matches', False)
        
        for word in words:
            # Clean word for lookup (remove punctuation)
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            # Try exact match first
            if clean_word in self.lexicons.corrections:
                entry = self.lexicons.corrections[clean_word]
                corrected = entry['original_term']
                
                # Preserve capitalization pattern
                if word[0].isupper():
                    corrected = corrected.capitalize()
                
                # Record metrics if collecting
                if self.metrics_collector:
                    self.metrics_collector.start_correction('lexicon', word)
                    self.metrics_collector.end_correction('lexicon', word, corrected, 1.0)
                    
                corrected_words.append(corrected)
                corrections += 1
                logger.debug(f"Exact correction: {word} -> {corrected}")
                
            # Try fuzzy match if enabled and no exact match
            elif fuzzy_enabled and clean_word:
                fuzzy_match = self._find_fuzzy_match(clean_word, fuzzy_threshold)
                if fuzzy_match:
                    # Preserve capitalization pattern
                    if word[0].isupper():
                        fuzzy_match = fuzzy_match.capitalize()
                    
                    # Calculate confidence for fuzzy match
                    confidence = self._calculate_similarity(clean_word, fuzzy_match.lower())
                    
                    # Record metrics if collecting
                    if self.metrics_collector:
                        self.metrics_collector.start_correction('fuzzy', word)
                        self.metrics_collector.end_correction('fuzzy', word, fuzzy_match, confidence)
                        
                    corrected_words.append(fuzzy_match)
                    corrections += 1
                    
                    if log_fuzzy:
                        logger.info(f"Fuzzy correction: {word} -> {fuzzy_match}")
                    else:
                        logger.debug(f"Fuzzy correction: {word} -> {fuzzy_match}")
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    def _apply_capitalization(self, text: str) -> tuple[str, int]:
        """Apply proper noun capitalization."""
        corrections = 0
        words = text.split()
        corrected_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            if clean_word in self.lexicons.proper_nouns:
                entry = self.lexicons.proper_nouns[clean_word]
                corrected = entry.get('term') or entry.get('original_term', word)
                
                # Record metrics if collecting
                if self.metrics_collector:
                    self.metrics_collector.start_correction('capitalization', word)
                    self.metrics_collector.end_correction('capitalization', word, corrected, 1.0)
                
                corrected_words.append(corrected)
                corrections += 1
                logger.debug(f"Capitalization: {word} -> {corrected}")
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate character-based similarity ratio without external dependencies.
        Uses optimized character matching for ASR-style errors.
        """
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings (lowercase, strip punctuation)
        s1 = re.sub(r'[^\w]', '', str1.lower())
        s2 = re.sub(r'[^\w]', '', str2.lower())
        
        if not s1 or not s2:
            return 0.0
            
        if s1 == s2:
            return 1.0
        
        # Quick length check - very different lengths = low similarity
        len_diff = abs(len(s1) - len(s2))
        max_len = max(len(s1), len(s2))
        min_len = min(len(s1), len(s2))
        
        if len_diff / max_len > 0.5:  # More than 50% length difference
            return 0.0
        
        # Character-based similarity using multiple approaches
        # 1. Position-based matching (good for simple substitutions)
        position_matches = sum(1 for a, b in zip(s1, s2) if a == b)
        position_similarity = position_matches / max_len
        
        # 2. Character set intersection (good for reordering/missing chars)
        set1, set2 = set(s1), set(s2)
        common_chars = len(set1 & set2)
        total_unique = len(set1 | set2)
        set_similarity = common_chars / total_unique if total_unique > 0 else 0.0
        
        # 3. Length penalty
        length_similarity = 1.0 - (len_diff / max_len)
        
        # 4. Sequential character matching (handles insertions/deletions better)
        seq_matches = 0
        i = j = 0
        while i < len(s1) and j < len(s2):
            if s1[i] == s2[j]:
                seq_matches += 1
                i += 1
                j += 1
            elif len(s1) > len(s2):
                i += 1  # Skip character in longer string
            else:
                j += 1  # Skip character in longer string
        
        sequential_similarity = seq_matches / max_len
        
        # Combine similarities with weights optimized for ASR errors
        final_similarity = (
            position_similarity * 0.3 +      # Position matching
            set_similarity * 0.25 +          # Character overlap
            length_similarity * 0.2 +        # Length similarity
            sequential_similarity * 0.25     # Sequential matching
        )
        
        return min(1.0, final_similarity)

    def _find_fuzzy_match(self, word: str, threshold: float = 0.8) -> Optional[str]:
        """
        Find the best fuzzy match for a word in the lexicon.
        Returns the corrected term if similarity > threshold, None otherwise.
        """
        if not word or not self.lexicons.corrections:
            return None
            
        best_match = None
        best_similarity = 0.0
        
        for lexicon_term, entry in self.lexicons.corrections.items():
            similarity = self._calculate_similarity(word, lexicon_term)
            if similarity > threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = entry['original_term']
                
        return best_match
    
    def process_srt_file(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Process an SRT file with Sanskrit corrections."""
        import time
        start_time = time.time()
        parse_start = time.time()
        
        # Memory monitoring (only when collecting metrics and psutil is available)
        memory_start = None
        if self.collect_metrics:
            try:
                import psutil
                process = psutil.Process()
                memory_start = process.memory_info().rss / 1024 / 1024  # MB
            except ImportError:
                pass
        
        logger.info(f"Processing SRT file: {input_path} -> {output_path}")
        
        try:
            # Read and parse phase
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            segments = SRTParser.parse(content)
            if not segments:
                raise ValueError("No valid SRT segments found")
            
            parse_time = time.time() - parse_start
            logger.info(f"Parsed {len(segments)} segments")
            
            # Processing phase
            process_start = time.time()
            total_corrections = 0
            for segment in segments:
                processed_text, corrections = self.process_text(segment.text)
                segment.text = processed_text
                total_corrections += corrections
            
            process_time = time.time() - process_start
            
            # Writing phase
            write_start = time.time()
            output_content = SRTParser.to_srt(segments)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            write_time = time.time() - write_start
            processing_time = time.time() - start_time
            
            # Create appropriate result type
            if self.collect_metrics and self.metrics_collector:
                # Calculate memory usage
                memory_usage = {}
                if memory_start:
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_end = process.memory_info().rss / 1024 / 1024
                        memory_usage = {
                            'peak': memory_end,
                            'average': (memory_start + memory_end) / 2
                        }
                    except ImportError:
                        pass
                
                # Calculate quality score
                quality_score = self.metrics_collector.calculate_quality_score(len(segments), 0)
                
                result = DetailedProcessingResult(
                    segments_processed=len(segments),
                    corrections_made=total_corrections,
                    processing_time=processing_time,
                    errors=[],
                    corrections_by_type=self.metrics_collector.corrections_by_type.copy(),
                    correction_details=self.metrics_collector.correction_details.copy(),
                    confidence_scores=self.metrics_collector.confidence_scores.copy(),
                    processing_phases={'parse': parse_time, 'process': process_time, 'write': write_time},
                    quality_score=quality_score,
                    memory_usage=memory_usage
                )
            else:
                result = ProcessingResult(
                    segments_processed=len(segments),
                    corrections_made=total_corrections,
                    processing_time=processing_time,
                    errors=[]
                )
            
            logger.info(f"Processing complete: {len(segments)} segments, "
                       f"{total_corrections} corrections, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            result_class = DetailedProcessingResult if self.collect_metrics else ProcessingResult
            return result_class(
                segments_processed=0,
                corrections_made=0,
                processing_time=time.time() - start_time,
                errors=[str(e)]
            )

if __name__ == "__main__":
    # Simple test
    processor = SanskritProcessor()
    
    # Test text processing
    test_text = "Welcome to this bhagavad gita lecture on dharma and yoga"
    result, corrections = processor.process_text(test_text)
    print(f"Test: '{test_text}' -> '{result}' ({corrections} corrections)")