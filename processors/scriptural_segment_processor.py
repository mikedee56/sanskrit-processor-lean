#!/usr/bin/env python3
"""
Scriptural Segment Processor for Sanskrit Processor
Handles full-line scriptural content recognition and replacement.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
from services.verse_cache import VerseCache, CachedVerse

logger = logging.getLogger(__name__)

class PrayerRecognitionEngine:
    """Intelligent prayer and mantra recognition engine with complete unit replacement."""
    
    def __init__(self, lexicon_dir: Path, config: Dict = None):
        self.lexicon_dir = lexicon_dir
        self.config = config or {}
        self.prayer_database = {}
        self.opening_mantras = {}
        self.closing_mantras = {}
        self.guru_prayers = {}
        self.krishna_prayers = {}
        self._load_comprehensive_prayer_database()
        
    def _load_comprehensive_prayer_database(self):
        """Load comprehensive prayer database from lexicons and construct complete units."""
        self._load_from_corrections_yaml()
        self._construct_complete_prayer_units()
        self._generate_asr_variations()
        
    def _load_from_corrections_yaml(self):
        """Extract all mantra entries from corrections.yaml."""
        corrections_file = self.lexicon_dir / "corrections.yaml"
        if not corrections_file.exists():
            logger.warning(f"Corrections file not found: {corrections_file}")
            return
            
        try:
            import yaml
            with open(corrections_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            mantra_entries = {}
            for entry in data:
                if isinstance(entry, dict) and entry.get('category') == 'mantra':
                    original = entry.get('original_term', '')
                    transliteration = entry.get('transliteration', original)
                    variations = entry.get('variations', [])
                    meaning = entry.get('meaning', '')
                    
                    mantra_entries[original] = {
                        'transliteration': transliteration,
                        'variations': variations,
                        'meaning': meaning,
                        'confidence': entry.get('confidence', 1.0)
                    }
                    
            logger.info(f"Loaded {len(mantra_entries)} mantra entries from corrections.yaml")
            self.mantra_entries = mantra_entries
            
        except Exception as e:
            logger.error(f"Failed to load mantra entries: {e}")
            self.mantra_entries = {}
    
    def _construct_complete_prayer_units(self):
        """Construct complete prayer units from individual components."""
        
        # 1. UPANISHAD OPENING MANTRA (most critical - appears 1000s of times)
        self.opening_mantras['upanishad_opening'] = {
            'name': 'Īśāvāsya Upaniṣad Opening Mantra',
            'complete_sanskrit': 'oṁ pūrṇam-adaḥ pūrṇam-idaṁ pūrṇāt-pūrṇam-udacyate | pūrṇasya pūrṇam-ādāya pūrṇam-evāvaśiṣyate || oṁ śāntiḥ śāntiḥ śāntiḥ ||',
            'complete_transliteration': 'oṁ pūrṇam-adaḥ pūrṇam-idaṁ pūrṇāt-pūrṇam-udacyate | pūrṇasya pūrṇam-ādāya pūrṇam-evāvaśiṣyate || oṁ śāntiḥ śāntiḥ śāntiḥ ||',
            'segments': [
                'oṁ pūrṇam-adaḥ pūrṇam-idaṁ pūrṇāt-pūrṇam-udacyate',
                'pūrṇasya pūrṇam-ādāya pūrṇam-evāvaśiṣyate', 
                'oṁ śāntiḥ śāntiḥ śāntiḥ'
            ],
            'asr_variations': [
                # Full mantra variations
                'Om purnamadah purnamidam purnat purnamudacyate purnasya purnamadaya purnamevavashyate Om shanti shanti shanti',
                'om purnam adah purnam idam purnat purnam udacyate purnasya purnam adaya purnam evavashyate om shanti shanti shanti',
                'aum purnamadah purnamidam purnat purnamudacyate purnasya purnamadaya purnamevavashyate aum shanti shanti shanti',
                # Common ASR splits
                'Om purnamadah purnamidam',
                'purnamadah purnamidam', 
                'purnat purnamudacyate',
                'purnasya purnamadaya',
                'purnamevavashyate',
                'Om shanti shanti shanti'
            ],
            'meaning': 'That is complete, this is complete. From completeness, completeness emerges. Taking completeness from completeness, completeness remains.',
            'confidence': 1.0
        }
        
        # 2. KRISHNA PRAYER (from current hardcoded patterns)
        self.krishna_prayers['vasudeva_prayer'] = {
            'name': 'Vāsudeva Prayer',
            'complete_transliteration': 'oṁ vāsudeva-sutaṁ devaṁ kaṁsa-cāṇūra-mardanam | devakī-paramānandaṁ kṛṣṇaṁ vande jagad-gurum || oṁ ||',
            'asr_variations': [
                'Om Vahudevo Sutam Devam Kansa Chan Uram Ardanam Devaki Paramahnam Trishnam Vande Jagad Guru',
                'om vahudevo sutam devam kansa chan uram ardanam devaki paramahnam trishnam vande jagad guru',
                'O\u1e43 Vahudevo Sutam Devam Kansa Chan Uram Ardanam Devaki Paramahnam Trishnam Vande Jagad guru',
                # Split variations
                'Om Vahudevo Sutam Devam Kansa Chan Uram Ardanam',
                'Devaki Paramahnam Trishnam Vande Jagad Guru'
            ],
            'meaning': 'Om, I bow to Krishna, son of Vasudeva, destroyer of Kamsa and Chanura, supreme bliss of Devaki, teacher of the universe',
            'confidence': 1.0
        }
        
        # 3. GURU PRAYERS (from current patterns)
        self.guru_prayers['brahmanandam'] = {
            'name': 'Brahmānandam Prayer',
            'complete_transliteration': 'brahmānandam parama-sukhadam kevalaṁ jñānamūrtiṁ | dvandvātītaṁ gagana-sadṛśaṁ tattvam-asy-ādi-lakṣyam || eka nitya-vimalam-acalaṁ sarva-dhī-sākṣi-bhūtam | bhāvātītaṁ tri-guṇa-rahitaṁ sad-guruṁ taṁ namāmi ||',
            'asr_variations': [
                'brahmanandam parama sukhadam kevalam jnana murtim',
                'brahmanandam paramasukhadam kevalam jnanamurtim',
                'brahm\u0101nandam parama-sukhadam kevala\u1e43 j\u00f1\u0101nam\u016brti\u1e43'
            ],
            'meaning': 'I bow to the Guru who is Brahman-bliss, supreme happiness, absolute, the embodiment of knowledge',
            'confidence': 1.0
        }
        
        self.guru_prayers['guru_brahma'] = {
            'name': 'Guru Brahma Prayer', 
            'complete_transliteration': 'gurur brahmā gurur viṣṇuḥ gurur devo maheśvaraḥ | gurur-sākṣāt paraṁ brahma tasmai śrī-gurave namaḥ ||',
            'asr_variations': [
                'gurur brahma gurur vishnu gurur devo maheshwara',
                'guru brahma guru vishnu guru devo maheshwara',
                'gurur brahm\u0101 gurur vi\u1e63\u1e47u\u1e25 gurur devo mahe\u015bvara\u1e25'
            ],
            'meaning': 'The Guru is Brahma, the Guru is Vishnu, the Guru is Shiva - I bow to that glorious Guru',
            'confidence': 1.0
        }
        
    def _generate_asr_variations(self):
        """Generate additional ASR variations for better recognition."""
        asr_transforms = {
            'oṁ': ['om', 'Om', 'OM', 'ohm', 'aum', 'Aum', 'AUM'],
            'ṁ': ['m', 'n', 'ng'],
            'ā': ['a', 'aa'],
            'ī': ['i', 'ee'],
            'ū': ['u', 'oo'], 
            'ṛ': ['r', 'ri'],
            'ṅ': ['n', 'ng'],
            'ṇ': ['n'],
            'ś': ['s', 'sh'],
            'ṣ': ['s', 'sh'],
            'ḥ': ['h', ''],
            'kṛṣṇa': ['krishna', 'Krishna', 'krsna'],
            'śānti': ['shanti', 'Shanti', 'santi']
        }
        
        # Apply transforms to enhance recognition
        for prayer_dict in [self.opening_mantras, self.krishna_prayers, self.guru_prayers]:
            for prayer_key, prayer_data in prayer_dict.items():
                enhanced_variations = set(prayer_data.get('asr_variations', []))
                
                # Generate phonetic variations
                for variation in list(enhanced_variations):
                    for original, replacements in asr_transforms.items():
                        for replacement in replacements:
                            new_variation = variation.replace(original, replacement)
                            if new_variation != variation:
                                enhanced_variations.add(new_variation)
                
                prayer_data['asr_variations'] = list(enhanced_variations)
    
    def recognize_prayer(self, text: str) -> Optional[Tuple[str, str, float]]:
        """Recognize complete prayer units in text and return replacement."""
        if not text or len(text.strip()) < 10:
            return None
            
        text_normalized = self._normalize_for_prayer_matching(text)
        
        # Check opening mantras first (highest priority)
        result = self._match_opening_mantras(text_normalized, text)
        if result:
            return result
            
        # Check Krishna prayers
        result = self._match_krishna_prayers(text_normalized, text)
        if result:
            return result
            
        # Check Guru prayers
        result = self._match_guru_prayers(text_normalized, text)
        if result:
            return result
            
        return None
    
    def _normalize_for_prayer_matching(self, text: str) -> str:
        """Normalize text for prayer pattern matching."""
        # Convert to lowercase and normalize whitespace
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Remove common punctuation that interferes with matching
        normalized = re.sub(r'[.,;:!?\'"()]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _match_opening_mantras(self, normalized_text: str, original_text: str) -> Optional[Tuple[str, str, float]]:
        """Match against opening mantras (Upanishad opening)."""
        for mantra_key, mantra_data in self.opening_mantras.items():
            # Check for complete mantra match
            for variation in mantra_data['asr_variations']:
                variation_norm = self._normalize_for_prayer_matching(variation)
                
                # Full match
                if self._calculate_prayer_similarity(normalized_text, variation_norm) > 0.7:
                    logger.info(f"Complete opening mantra recognized: {mantra_data['name']}")
                    return mantra_data['complete_transliteration'], mantra_data['name'], 0.95
                
                # Partial match for segments
                if len(normalized_text.split()) >= 3:
                    for segment in mantra_data['segments']:
                        segment_norm = self._normalize_for_prayer_matching(segment)
                        if self._calculate_prayer_similarity(normalized_text, segment_norm) > 0.8:
                            logger.info(f"Partial opening mantra recognized: {segment}")
                            return segment, f"{mantra_data['name']} (partial)", 0.9
        
        return None
    
    def _match_krishna_prayers(self, normalized_text: str, original_text: str) -> Optional[Tuple[str, str, float]]:
        """Match against Krishna prayers."""
        for prayer_key, prayer_data in self.krishna_prayers.items():
            for variation in prayer_data['asr_variations']:
                variation_norm = self._normalize_for_prayer_matching(variation)
                similarity = self._calculate_prayer_similarity(normalized_text, variation_norm)
                
                if similarity > 0.6:  # Lower threshold for Krishna prayers (often heavily corrupted)
                    logger.info(f"Krishna prayer recognized: {prayer_data['name']} (similarity: {similarity:.2f})")
                    return prayer_data['complete_transliteration'], prayer_data['name'], similarity
        
        return None
    
    def _match_guru_prayers(self, normalized_text: str, original_text: str) -> Optional[Tuple[str, str, float]]:
        """Match against Guru prayers."""  
        for prayer_key, prayer_data in self.guru_prayers.items():
            for variation in prayer_data['asr_variations']:
                variation_norm = self._normalize_for_prayer_matching(variation)
                similarity = self._calculate_prayer_similarity(normalized_text, variation_norm)
                
                if similarity > 0.65:  # Reasonable threshold for Guru prayers
                    logger.info(f"Guru prayer recognized: {prayer_data['name']} (similarity: {similarity:.2f})")
                    return prayer_data['complete_transliteration'], prayer_data['name'], similarity
        
        return None
    
    def _calculate_prayer_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between prayer texts using multiple methods."""
        if not text1 or not text2:
            return 0.0
            
        # Use SequenceMatcher for basic similarity
        from difflib import SequenceMatcher
        seq_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Word-level jaccard similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        if words1 and words2:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            jaccard_similarity = intersection / union if union > 0 else 0
        else:
            jaccard_similarity = 0
            
        # Weighted combination favoring word-level similarity for prayers
        return (seq_similarity * 0.3) + (jaccard_similarity * 0.7)

class ScripturalSegmentProcessor:
    """Processes full segments containing scriptural content."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.prayer_patterns = self._load_prayer_patterns()
        self.verse_patterns = self._load_verse_patterns()
        self.scripture_references = self._load_scripture_references()

        # Initialize verse cache for intelligent content matching
        try:
            self.verse_cache = VerseCache(self.config)
            logger.info(f"Initialized verse cache with {len(self.verse_cache.verses)} verses")
            # Enhance cache with English concept mappings
            self._enhance_verse_cache_with_concepts()
        except Exception as e:
            logger.warning(f"Failed to initialize verse cache: {e}")
            self.verse_cache = None
            
        # TRANSFORMATION: Initialize comprehensive prayer recognition engine
        try:
            from pathlib import Path
            lexicon_dir = Path("lexicons")
            self.prayer_engine = PrayerRecognitionEngine(lexicon_dir, self.config)
            logger.info(f"Initialized PrayerRecognitionEngine with comprehensive prayer database")
        except Exception as e:
            logger.warning(f"Failed to initialize PrayerRecognitionEngine: {e}")
            self.prayer_engine = None

    def _load_prayer_patterns(self) -> Dict[str, str]:
        """Load prayer recognition patterns and their corrections."""
        return {
            # Krishna Prayer - CORRECTED: Use the actual prayer from user feedback
            r'(?i).*vahudevo.*sutam.*devam.*kansa.*chan.*uram.*ardanam.*devaki.*paramahnam.*trishnam.*vande.*jagad.*guru.*':
                'oṁ vāsudeva-sutaṁ devaṁ kaṁsa-cāṇūra-mardanam |\ndevakī-paramānandaṁ kṛṣṇaṁ vande jagad-gurum || oṁ ||',

            # Exact ASR pattern match (full prayer)
            r'(?i)^Om Vahudevo Sutam Devam Kansa Chan Uram Ardanam Devaki Paramahnam Trishnam Vande Jagad Guru.*':
                'oṁ vāsudeva-sutaṁ devaṁ kaṁsa-cāṇūra-mardanam |\ndevakī-paramānandaṁ kṛṣṇaṁ vande jagad-gurum || oṁ ||',

            # Split prayer - First half
            r'(?i)^Om Vahudevo Sutam Devam Kansa Chan Uram Ardanam$':
                'oṁ vāsudeva-sutaṁ devaṁ kaṁsa-cāṇūra-mardanam |',

            r'(?i)^Oṃ Vahudevo Sutam Devam Kansa Chan Uram Ardanam$':
                'oṁ vāsudeva-sutaṁ devaṁ kaṁsa-cāṇūra-mardanam |',

            # Split prayer - Second half
            r'(?i)^Devaki Paramahnam Trishnam Vande Jagad Guru$':
                'devakī-paramānandaṁ kṛṣṇaṁ vande jagad-gurum || oṁ ||',

            # Variations with Om/Oṃ (full prayer)
            r'(?i)^Oṃ Vahudevo Sutam Devam Kansa Chan Uram Ardanam Devaki Paramahnam Trishnam Vande Jagad guru.*':
                'oṁ vāsudeva-sutaṁ devaṁ kaṁsa-cāṇūra-mardanam |\ndevakī-paramānandaṁ kṛṣṇaṁ vande jagad-gurum || oṁ ||',

            r'(?i).*krishnaya.*vasudevaya.*haraye.*paramatmane.*':
                'Oṃ kṛṣṇāya vāsudevāya haraye paramatmane',

            # Guru Prayers
            r'(?i).*brahmanandam.*parama.*sukhadam.*kevalam.*jnana.*murtim.*':
                'brahmānandaṃ paramasukhadaṃ kevalaṃ jñānamūrtiṃ',

            r'(?i).*gurur.*brahma.*gurur.*vishnu.*gurur.*devo.*maheshwara.*':
                'gurur brahmā gurur viṣṇuḥ gurur devo maheśvaraḥ',
        }

    def _load_verse_patterns(self) -> Dict[str, Tuple[str, str]]:
        """Load verse recognition patterns with their corrections and references."""
        return {
            # Bhagavad Gita Chapter 3, Verse 32 - EXACT ASR PATTERNS
            r'(?i)^Yey che dhabhyasu yanto naanuti sthanti me matam sarva jnanavi moor haan sthan mit ji$':
                ('ye tv etad abhyasūyanto nānutiṣṭhanti me matam\nsarva-jñāna-vimūḍhāṁs tān viddhi naṣṭān acetasaḥ', 'Bhagavad Gītā 3.32'),

            # Split across two segments (common pattern)
            r'(?i)^Yey che dhabhyasu yanto naanuti sthanti me matam.*':
                ('ye tv etad abhyasūyanto nānutiṣṭhanti me matam', 'Bhagavad Gītā 3.32a'),

            r'(?i)^.*sarva jnanavi moor haan sthan mit ji.*':
                ('sarva-jñāna-vimūḍhāṁs tān viddhi naṣṭān acetasaḥ', 'Bhagavad Gītā 3.32b'),

            r'(?i)^nashtana che tashaar.*':
                ('sarva-jñāna-vimūḍhāṁs tān viddhi naṣṭān acetasaḥ', 'Bhagavad Gītā 3.32b continuation'),

            # General patterns
            r'(?i).*ye.*tv.*etad.*abhyasuyanto.*nanutishthanti.*me.*matam.*':
                ('ye tv etad abhyasūyanto nānutiṣṭhanti me matam', 'Bhagavad Gītā 3.32a'),

            r'(?i).*sarva.*jnana.*vimudhan.*tan.*viddhi.*nashtan.*acetasah.*':
                ('sarva-jñāna-vimūḍhāṁs tān viddhi naṣṭān acetasaḥ', 'Bhagavad Gītā 3.32b'),

            # Common dharma verses
            r'(?i).*shreyan.*svadharmo.*vigunah.*paradharmat.*swanushthitat.*':
                ('śreyān sva-dharmo viguṇaḥ para-dharmāt sv-anuṣṭhitāt', 'Bhagavad Gītā 3.35'),
        }

    def _load_scripture_references(self) -> Dict[str, str]:
        """Load scripture reference patterns."""
        return {
            r'(?i).*gita.*ch(?:apter)?.*3.*v(?:erse)?.*32.*': 'Bhagavad Gītā 3.32',
            r'(?i).*bhagavad.*gita.*chapter.*3.*verse.*32.*': 'Bhagavad Gītā 3.32',
            r'(?i).*srimad.*bhagavad.*gita.*chapter.*3.*': 'Śrīmad Bhagavad Gītā Chapter 3',
        }

    def _enhance_verse_cache_with_concepts(self):
        """Enhance verse cache with English concept mappings for popular verses."""
        if not self.verse_cache:
            return

        # Popular Gita verses with their English concepts
        verse_concepts = {
            (2, 47): "action duty right work perform fruits results attachment karma dharma obligation",
            (2, 46): "well water reservoir vedas knowledge purpose wisdom understanding utility",
            (2, 56): "mind happiness misery attachment fear anger equanimity steady sage peace",
            (4, 7): "dharma decline righteousness manifestation divine avatar descent incarnation",
            (4, 8): "protection good destruction evil dharma establishment incarnation justice",
            (6, 5): "self elevation mind friend enemy uplift degradation consciousness control",
            (9, 22): "devotion exclusive worship meditation preservation protection yoga surrender",
            (18, 66): "surrender religion dharma sin moksha fear deliverance salvation liberation",
            (3, 35): "dharma duty righteousness path better death fear varna ashrama",
            (3, 32): "knowledge ignorance delusion instruction teaching guidance disobedience",
            (2, 14): "pleasure pain temporary contact senses endurance tolerance patience",
            (2, 20): "soul eternal unborn imperishable consciousness spirit divine nature",
            (15, 7): "living being eternal fragment consciousness soul jiva divine",
        }

        enhanced_count = 0
        for (chapter, verse), concepts in verse_concepts.items():
            cached_verse = self.verse_cache.get_verse(chapter, verse)
            if cached_verse:
                # Add English concepts to existing keywords
                existing_keywords = cached_verse.keywords or ""
                enhanced_keywords = f"{existing_keywords} {concepts}".strip()
                cached_verse.keywords = enhanced_keywords
                enhanced_count += 1

        if enhanced_count > 0:
            logger.info(f"Enhanced {enhanced_count} verses with English concept mappings")

    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """Calculate content similarity between two texts using multiple methods."""
        if not text1 or not text2:
            return 0.0

        # Normalize texts for comparison
        norm1 = self._normalize_for_comparison(text1)
        norm2 = self._normalize_for_comparison(text2)

        # Use SequenceMatcher for overall similarity
        seq_sim = SequenceMatcher(None, norm1, norm2).ratio()

        # Word-level similarity for fuzzy matching
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if words1 and words2:
            word_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        else:
            word_sim = 0.0

        # Phonetic similarity for Sanskrit terms
        phonetic_sim = self._calculate_phonetic_similarity(norm1, norm2)

        # Weighted combination
        return (seq_sim * 0.4) + (word_sim * 0.4) + (phonetic_sim * 0.2)

    def _normalize_for_comparison(self, text: str) -> str:
        """Normalize text for content comparison."""
        # Convert to lowercase
        text = text.lower()

        # Common ASR substitutions for Sanskrit
        asr_substitutions = {
            'ph': 'f', 'th': 't', 'sh': 'ś', 'ch': 'c',
            'krishna': 'kṛṣṇa', 'dharma': 'dharma', 'karma': 'karma',
            'gita': 'gītā', 'yoga': 'yoga', 'arjuna': 'arjuna',
            'vahudevo': 'vāsudeva', 'sutam': 'sutaṁ', 'devam': 'devaṁ',
            'paramahnam': 'paramānandaṁ', 'trishnam': 'kṛṣṇaṁ',
            'brahmanandam': 'brahmānandaṃ', 'jnana': 'jñāna'
        }

        for asr, correct in asr_substitutions.items():
            text = text.replace(asr, correct)

        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _calculate_phonetic_similarity(self, text1: str, text2: str) -> float:
        """Calculate phonetic similarity for Sanskrit terms."""
        # Simple phonetic groupings for Sanskrit
        phonetic_groups = [
            ['k', 'c', 'ch'],
            ['t', 'th', 'd', 'dh'],
            ['p', 'ph', 'b', 'bh'],
            ['s', 'ś', 'ṣ', 'sh'],
            ['n', 'ṇ', 'ñ'],
            ['r', 'ṛ'],
            ['a', 'ā', 'ah'],
            ['i', 'ī'],
            ['u', 'ū'],
            ['e', 'ai'],
            ['o', 'au']
        ]

        # Create phonetic mapping
        phonetic_map = {}
        for i, group in enumerate(phonetic_groups):
            for char in group:
                phonetic_map[char] = i

        def phonetic_encode(text):
            encoded = []
            for char in text:
                encoded.append(str(phonetic_map.get(char, char)))
            return ''.join(encoded)

        enc1 = phonetic_encode(text1)
        enc2 = phonetic_encode(text2)

        return SequenceMatcher(None, enc1, enc2).ratio()

    def find_content_matches(self, text: str, min_similarity: float = 0.6) -> List[Tuple[CachedVerse, float]]:
        """Find verse matches based on content similarity."""
        if not self.verse_cache or not text:
            return []

        matches = []
        normalized_input = self._normalize_for_comparison(text)

        # Skip very short inputs that would match too broadly
        if len(normalized_input.split()) < 3:
            return []

        for verse in self.verse_cache.verses.values():
            # Check against transliteration and keywords
            searchable_content = f"{verse.transliteration} {verse.keywords}".strip()
            if not searchable_content:
                continue

            similarity = self._calculate_content_similarity(normalized_input, searchable_content)

            if similarity >= min_similarity:
                matches.append((verse, similarity))

        # Sort by similarity score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]  # Return top 5 matches

    def detect_verse_by_content(self, text: str) -> Optional[Tuple[str, str, float]]:
        """Detect if text contains a Bhagavad Gita verse by content similarity.
        
        INTELLIGENT TRANSFORMATION: Context-aware thresholds instead of blindly conservative ones.
        Uses dynamic confidence based on content type and Sanskrit density.
        """
        if not text or len(text.strip()) < 10:
            return None
            
        # Analyze content to determine appropriate threshold
        context_info = self._analyze_content_context(text)
        dynamic_threshold = self._calculate_dynamic_threshold(context_info)
        
        matches = self.find_content_matches(text, min_similarity=dynamic_threshold)

        if matches:
            best_verse, confidence = matches[0]
            reference = f"Bhagavad Gītā {best_verse.chapter}.{best_verse.verse}"

            # Context-aware confidence requirements
            min_confidence = self._get_context_confidence_threshold(context_info)
            
            if confidence < min_confidence:
                logger.debug(f"Content-based verse detection below context threshold: {reference} "
                           f"(confidence: {confidence:.2f} < {min_confidence:.2f}, context: {context_info['type']})")
                return None

            # Choose best representation based on content and user preferences
            corrected_text = self._select_best_verse_representation(best_verse, text, context_info)

            # Intelligent semantic appropriateness check
            if not self._is_semantically_appropriate_replacement(text, corrected_text, confidence):
                logger.debug(f"Verse replacement deemed semantically inappropriate: '{text[:30]}...' -> '{corrected_text[:30]}...'")
                return None

            logger.info(f"Intelligent verse detection: {reference} (confidence: {confidence:.2f}, "
                       f"context: {context_info['type']}, threshold: {min_confidence:.2f})")
            return corrected_text, reference, confidence

        return None

    def _analyze_content_context(self, text: str) -> Dict[str, Any]:
        """Analyze content to determine processing context."""
        text_lower = text.lower()
        words = text.split()
        
        # Sanskrit density analysis
        sanskrit_indicators = ['dharma', 'karma', 'yoga', 'krishna', 'arjuna', 'bhagavan', 'atman', 'brahman']
        sanskrit_count = sum(1 for word in words if any(ind in word.lower() for ind in sanskrit_indicators))
        sanskrit_density = sanskrit_count / len(words) if words else 0
        
        # Mantra/prayer indicators
        is_mantra = any(indicator in text_lower for indicator in ['om ', 'aum ', 'purnam', 'shanti'])
        
        # English explanation indicators  
        english_indicators = ['means', 'refers to', 'explains', 'this', 'that', 'chapter', 'verse']
        english_count = sum(1 for word in words if word.lower() in english_indicators)
        english_density = english_count / len(words) if words else 0
        
        # Determine context type
        if is_mantra:
            context_type = 'mantra'
        elif sanskrit_density > 0.6:
            context_type = 'pure_sanskrit' 
        elif sanskrit_density > 0.3:
            context_type = 'mixed_sanskrit'
        elif english_density > 0.3:
            context_type = 'english_explanation'
        else:
            context_type = 'unknown'
            
        return {
            'type': context_type,
            'sanskrit_density': sanskrit_density,
            'english_density': english_density,
            'is_mantra': is_mantra,
            'word_count': len(words)
        }
    
    def _calculate_dynamic_threshold(self, context_info: Dict[str, Any]) -> float:
        """Calculate dynamic similarity threshold based on content context."""
        base_threshold = 0.5  # Much more reasonable than 0.7
        
        # Adjust based on context type
        if context_info['type'] == 'mantra':
            return 0.4  # Lower for mantras (often heavily corrupted by ASR)
        elif context_info['type'] == 'pure_sanskrit':
            return 0.45  # Lower for pure Sanskrit (ASR struggles with Sanskrit)
        elif context_info['type'] == 'mixed_sanskrit':  
            return 0.5  # Standard threshold
        elif context_info['type'] == 'english_explanation':
            return 0.7  # Higher to prevent inappropriate replacements in explanations
        else:
            return base_threshold
            
    def _get_context_confidence_threshold(self, context_info: Dict[str, Any]) -> float:
        """Get confidence threshold based on content context."""
        # Much more reasonable confidence thresholds
        if context_info['type'] == 'mantra':
            return 0.6  # Lower for mantras
        elif context_info['type'] == 'pure_sanskrit':
            return 0.65  # Slightly higher for verses
        elif context_info['type'] == 'mixed_sanskrit':
            return 0.7  # Standard
        elif context_info['type'] == 'english_explanation':
            return 0.85  # Very high to prevent inappropriate replacements
        else:
            return 0.7
            
    def _select_best_verse_representation(self, verse: 'CachedVerse', original_text: str, context_info: Dict[str, Any]) -> str:
        """Select the best verse representation based on context and preferences."""
        # For mantras and pure Sanskrit, prefer transliteration with diacritics
        if context_info['type'] in ['mantra', 'pure_sanskrit']:
            if verse.transliteration and len(verse.transliteration) > 10:
                return verse.transliteration
            elif verse.sanskrit:
                return verse.sanskrit
                
        # For mixed content, prefer readable transliteration
        elif context_info['type'] == 'mixed_sanskrit':
            if verse.transliteration:
                return verse.transliteration
            elif verse.sanskrit:
                return verse.sanskrit
                
        # Fallback to original for English explanations (shouldn't reach here)
        return original_text
        
    def _is_semantically_appropriate_replacement(self, original: str, replacement: str, confidence: float) -> bool:
        """Check if verse replacement is semantically appropriate."""
        # Length sanity check - don't replace very short text with long verses
        if len(original.split()) < 5 and len(replacement.split()) > 15:
            return False
            
        # Don't replace if original contains clear English sentence structure
        english_sentence_patterns = [
            r'\b(the|and|is|are|was|were)\s+\w+',
            r'\b(this|that|these|those)\s+\w+',
            r'\b(means|refers\s+to|explains)\b'
        ]
        
        if any(re.search(pattern, original, re.IGNORECASE) for pattern in english_sentence_patterns):
            # Only replace if confidence is extremely high
            return confidence > 0.9
            
        # Don't replace proper English sentences with verses
        if original.endswith('.') and any(word in original.lower() for word in ['the', 'is', 'means']):
            return confidence > 0.95
            
        return True

    def process_segment(self, text: str) -> Tuple[str, bool, Optional[str]]:
        """
        Process a segment for scriptural content with intelligent phrase-first matching.

        TRANSFORMATION: Prioritizes complete unit recognition over word-by-word processing.
        
        Returns:
            Tuple of (processed_text, was_modified, reference)
        """
        original_text = text

        # CRITICAL: Context-aware protection for mixed content
        # Detect if this is English commentary that should not be replaced
        english_indicators = ['the', 'and', 'is', 'are', 'that', 'which', 'to', 'in', 'of', 'with', 'from', 'at', 'by']
        english_score = sum(1 for indicator in english_indicators if indicator.lower() in text.lower())
        
        # Strong English detection patterns
        mixed_content_patterns = [
            r'\b(Chapter|entitled|Yoga of|in Chapter)\b',  # Commentary patterns
            r'\b(Shrimad|Bhagavad Gita)\b.*\b(Chapter|entitled)\b',  # Title with commentary
            r'\b(The verse number is)\b',  # Verse introduction
            r'\b(following|explained|means)\b',  # Explanatory text
            r'\b(Shankaracharya|personalities)\b.*\b(and|in)\b',  # Names in English context
        ]
        
        has_mixed_patterns = any(re.search(pattern, text, re.IGNORECASE) for pattern in mixed_content_patterns)
        
        # If this looks like English commentary with Sanskrit terms, be very conservative
        if english_score >= 2 or has_mixed_patterns:
            # Check if this contains corrupted Sanskrit that needs surgical editing
            corrupted_patterns = [
                r'evam?\s+pravartitam?\s+chakram?',  # Specific corrupted verse patterns
                r'mokha[mn]?\s+pārtha',
                r'aghāyur?\s+indriya'
            ]
            
            has_corrupted_sanskrit = any(re.search(pattern, text, re.IGNORECASE) for pattern in corrupted_patterns)
            
            if has_corrupted_sanskrit:
                # Allow processing of corrupted Sanskrit within mixed content
                logger.debug(f"Mixed content with corrupted Sanskrit detected, allowing targeted processing: {text[:50]}...")
            else:
                # This is English commentary - do not replace with prayers/verses
                logger.debug(f"English commentary detected, skipping prayer/verse replacement: {text[:50]}...")
                return text, False, None

        # PHASE 1: INTELLIGENT PRAYER RECOGNITION (HIGHEST PRIORITY)
        # This is the key transformation - complete prayer units recognized first
        if self.prayer_engine:
            prayer_result = self.prayer_engine.recognize_prayer(text)
            if prayer_result:
                corrected_text, reference, confidence = prayer_result
                logger.info(f"Complete prayer unit recognized: {reference} (confidence: {confidence:.2f})")
                logger.info(f"Prayer replacement: '{text[:50]}...' -> '{corrected_text[:50]}...'")
                return corrected_text, True, reference

        # Phase 2: Legacy hardcoded prayer patterns (fallback)
        for pattern, correction in self.prayer_patterns.items():
            if re.match(pattern, text):
                logger.info(f"Legacy prayer pattern detected: {text[:50]}... -> {correction[:50]}...")
                return correction, True, "Sanskrit Prayer (legacy)"

        # Phase 3: Hardcoded verse patterns (existing logic)
        for pattern, (correction, reference) in self.verse_patterns.items():
            if re.match(pattern, text):
                logger.info(f"Hardcoded verse detected: {reference} - {text[:50]}... -> {correction[:50]}...")
                return correction, True, reference

        # Phase 4: INTELLIGENT CONTENT-BASED VERSE DETECTION (ENHANCED)
        # This now uses the improved dynamic thresholds
        if self.verse_cache:
            content_result = self.detect_verse_by_content(text)
            if content_result:
                corrected_text, reference, confidence = content_result
                logger.info(f"Intelligent verse detection: {reference} (confidence: {confidence:.2f})")
                return corrected_text, True, reference

        # Phase 5: Scripture references (unchanged)
        for pattern, reference in self.scripture_references.items():
            if re.match(pattern, text):
                logger.info(f"Scripture reference detected: {reference}")
                return text, False, reference

        # Phase 6: Use verse cache for reference detection
        if self.verse_cache:
            detected_refs = self.verse_cache.detect_verse_references(text)
            if detected_refs:
                chapter, verse = detected_refs[0]  # Take first match
                reference = f"Bhagavad Gītā {chapter}.{verse}"
                logger.info(f"Verse reference detected: {reference}")
                return text, False, reference

        return text, False, None

    def detect_scriptural_context(self, segments: List[str], index: int) -> Optional[str]:
        """
        Detect if current segment is in scriptural context based on surrounding segments.

        Args:
            segments: List of all text segments
            index: Current segment index

        Returns:
            Scripture reference if detected, None otherwise
        """
        # Check previous 3 segments for scripture references
        start_index = max(0, index - 3)
        context_segments = segments[start_index:index + 1]

        for segment in context_segments:
            for pattern, reference in self.scripture_references.items():
                if re.match(pattern, segment):
                    return reference

        return None

    def process_with_context(self, segments: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
        """
        Process all segments with contextual awareness.

        Returns:
            List of (processed_text, was_modified, reference) tuples
        """
        results = []
        current_scripture_context = None

        for i, segment in enumerate(segments):
            # Update scripture context
            detected_context = self.detect_scriptural_context(segments, i)
            if detected_context:
                current_scripture_context = detected_context

            # Process segment
            processed_text, was_modified, reference = self.process_segment(segment)

            # If not modified but in scripture context, try harder
            if not was_modified and current_scripture_context:
                # Try more aggressive pattern matching for verses in known context
                processed_text, was_modified, reference = self._process_in_scripture_context(
                    segment, current_scripture_context
                )

            results.append((processed_text, was_modified, reference or current_scripture_context))

        return results

    def _process_in_scripture_context(self, text: str, context: str) -> Tuple[str, bool, Optional[str]]:
        """Process text with known scripture context for more aggressive matching."""

        if "Bhagavad Gītā 3.32" in context:
            # More lenient matching for known verse
            if any(word in text.lower() for word in ['yey', 'che', 'dhabhyasu', 'matam']):
                corrected = 'ye tv etad abhyasūyanto nānutiṣṭhanti me matam'
                logger.info(f"Context-based correction: {text[:30]}... -> {corrected}")
                return corrected, True, "Bhagavad Gītā 3.32 (context-based)"

            if any(word in text.lower() for word in ['sarva', 'jnanavi', 'moor', 'nashtana']):
                corrected = 'sarva-jñāna-vimūḍhāṁs tān viddhi naṣṭān acetasaḥ'
                logger.info(f"Context-based correction: {text[:30]}... -> {corrected}")
                return corrected, True, "Bhagavad Gītā 3.32 (context-based)"

        return text, False, None

def main():
    """Test the scriptural segment processor."""
    processor = ScripturalSegmentProcessor()

    test_segments = [
        "Srimad Bhagavad Gita in chapter 3, the chapter is known as karma yoga",
        "Verse number 32.",
        "Yey che dhabhyasu yanto naanuti sthanti me matam sarva jnanavi moor haan sthan mit ji",
        "nashtana che tashaar.",
        "Om Vahudevo Sutam Devam Kansa Chan Uram Ardanam Devaki Paramahnam Trishnam Vande Jagad Guru"
    ]

    print("Testing Scriptural Segment Processor:")
    print("=" * 50)

    results = processor.process_with_context(test_segments)

    for i, (original, (processed, modified, reference)) in enumerate(zip(test_segments, results)):
        print(f"\\nSegment {i+1}:")
        print(f"Original: {original}")
        if modified:
            print(f"Corrected: {processed}")
            print(f"Reference: {reference}")
        else:
            print("No correction needed")
            if reference:
                print(f"Context: {reference}")

if __name__ == "__main__":
    main()