"""
Sanskrit Prayer Recognition and Formatting Module
Recognizes common Sanskrit prayers and mantras, applies proper formatting and corrections.
"""

import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PrayerMatch:
    """Result of prayer recognition."""
    prayer_name: str
    corrected_text: str
    confidence: float
    translation: Optional[str] = None

class SanskritPrayerRecognizer:
    """Recognizes and corrects common Sanskrit prayers."""
    
    def __init__(self):
        self.prayers = self._load_prayer_database()
    
    def _load_prayer_database(self) -> Dict[str, Dict]:
        """Load database of common Sanskrit prayers with corrections."""
        return {
            "brahmananda_invocation": {
                "patterns": [
                    r"om.*brahm[aā]nand.*param.*sukh",
                    r"brahm[aā]nand.*kevalam.*jn[aā]n",
                    r"dvandv[aā]t[iī]t.*gagan.*sad[rṛ][sś]",
                    r"ekam.*nityam.*vimal.*acal",
                    r"bh[aā]v[aā]t[iī]t.*tri.*gun.*rahit",
                    # Add patterns for ASR corrupted guru stotra without diacritics
                    r"kevalam.*jnanam.*urtim.*dvandvatitam",
                    r"gaganasadrisham.*asyadilakshyam.*ekam",
                    r"sarvdhi.*sahakshibhutam.*bhavatitam",
                    r"trigunarahitam.*sadgurum.*namami"
                ],
                "corrected": """oṁ brahmānandaṁ parama-sukhadaṁ kevalaṁ jñāna-mūrtiṁ
dvandvātītaṁ gagana-sadṛśaṁ tattvam-asyādi-lakṣyam |
ekaṁ nityaṁ vimala-macalaṁ sarvadhī-sākṣibhūtaṁ
bhāvātītaṁ tri-guṇa-rahitaṁ sad-guruṁ taṁ namāmi || oṁ ||""",
                "translation": "Adorations to Sadguru who is Brahman; The Giver of Supreme Bliss; the Embodiment of Pure Consciousness; One without a second; Vast as the ether; Infinite, Eternal; beyond the three gunas and their modifications; the Supreme Preceptor.",
                "confidence_threshold": 0.6
            },
            "purnam_mantra": {
                "patterns": [
                    r"om.*p[uū]rn.*adah.*p[uū]rn.*idam",
                    r"p[uū]rn[aā]t.*p[uū]rn.*udacyate",
                    r"p[uū]rn.*[aā]d[aā]ya.*p[uū]rn.*ava[sś]i[sṣ]yate",
                    r"[sś][aā]nti.*[sś][aā]nti.*[sś][aā]nti",
                    # Add patterns for ASR corruption
                    r"[auo][uṁmṃ].*p[uū][nṇ][aā].*[mṁṃ][aā]?[dḍ][aā]?[hḥ].*p[uū][nṇ][aā]",  # corrupted "puna-madhah puna"
                    r"p[uū][nṇ][aā][sṣ]ya.*p[uū][nṇ][aā].*[mṁṃ][aā]?[dḍ][aā]?[hḥ]",  # "punasya puna-madhah"
                    r"p[uū][nṇ][aā].*m[eē].*v[aā][aāv][aāv].*[sś]i[sṣ][yỵ]ate"  # "puna me vava-sisyate"
                ],
                "corrected": """oṁ pūrṇam-adaḥ pūrṇam-idaṁ pūrṇāt-pūrṇam-udacyate |
pūrṇasya pūrṇam-ādāya pūrṇam-evāvaśiṣyate ||
oṁ śāntiḥ śāntiḥ śāntiḥ ||""",
                "translation": "That is whole, this is whole; from the whole, the whole arises. Taking the whole from the whole, the whole remains. Om Peace, Peace, Peace.",
                "confidence_threshold": 0.5
            },
            "krishna_invocation": {
                "patterns": [
                    r"om.*v[aā]sudeva.*sutam.*devam",
                    r"kams.*c[aā][nṇ][uū]r.*mardan",
                    r"devak[iī].*param[aā]nand",
                    r"k[rṛ][sṣ][nṇ].*vande.*jagad.*guru"
                ],
                "corrected": """oṁ vāsudeva-sutaṁ devaṁ kaṁsa-cāṇūra-mardanam |
devakī-paramānandaṁ kṛṣṇaṁ vande jagad-gurum || oṁ ||""",
                "translation": "Adorations to Lord Krishna; the Preceptor of the Universe; Destroyer of the forces of Darkness and bestower of immortality;",
                "confidence_threshold": 0.7
            },
            "sarve_bhavantu": {
                "patterns": [
                    r"om.*sarve.*bhavantu.*sukhin",
                    r"sarve.*santu.*nir[aā]may",
                    r"sarve.*bhadr[aā][nṇ]i.*pa[sś]yantu",
                    r"m[aā].*ka[sś]cid.*du[hḥ]kh.*bh[aā]g.*bhavet"
                ],
                "corrected": """oṁ sarve bhavantu sukhinaḥ
sarve santu nirāmayāḥ |
sarve bhadrāṇi paśyantu
mā kaścid-duḥkha-bhāg-bhavet ||
oṁ śāntiḥ śāntiḥ śāntiḥ ||""",
                "translation": "May all beings be happy; May all beings be free from illness; May all beings see auspiciousness; May none suffer from sorrow.",
                "confidence_threshold": 0.6
            },
            "asato_ma": {
                "patterns": [
                    r"om.*asato.*m[aā].*sad.*gamaya",
                    r"tamaso.*m[aā].*jyotir.*gamaya",
                    r"m[rṛ]tyor.*m[aā].*am[rṛ]tam.*gamaya"
                ],
                "corrected": """oṁ asato mā sad-gamaya |
tamaso mā jyotir-gamaya |
mṛtyor-mā amṛtaṁ gamaya ||
oṁ śāntiḥ śāntiḥ śāntiḥ ||""",
                "translation": "Lead me from the unreal to the Real; Lead me from darkness to Light; Lead me from death to Immortality.",
                "confidence_threshold": 0.8
            },
            "tryambakam": {
                "patterns": [
                    r"om.*tryambakam.*yaj[aā]mahe",
                    r"sugandhim.*pu[sṣ][tṭ]i.*vardhanam",
                    r"urv[aā]rukam.*iva.*bandhan[aā]n",
                    r"m[rṛ]tyor.*muk[sṣ][iī]ya.*m[aā].*am[rṛ]t[aā]t"
                ],
                "corrected": """oṁ tryambakaṁ yajāmahe
sugandhiṁ puṣṭi-vardhanam |
urvārukam-iva bandhanān
mṛtyor-mukṣīya mā'mṛtāt ||""",
                "translation": "We worship the Three-eyed One (Shiva) who is fragrant and nourishes all; Like a cucumber from its vine, may we be liberated from death, not from immortality.",
                "confidence_threshold": 0.7
            },
            "rama_invocation": {
                "patterns": [
                    r"n[iī]l[aā]mbuj.*[sś]y[aā]mal.*komal[aā]ng",
                    r"s[iī]t[aā].*sam[aā]ropit.*v[aā]m.*bh[aā]g",
                    r"p[aā][nṇ]au.*mah[aā].*s[aā]yak.*c[aā]ru.*c[aā]p",
                    r"nam[aā]mi.*r[aā]mam.*raghuvam[sś].*n[aā]th"
                ],
                "corrected": """nīlāmbuja-śyāmala-komalāṅgaṁ
sītā-samāropita-vāma-bhāgam |
pāṇau mahā-sāyaka-cāru-cāpaṁ
namāmi rāmaṁ raghuvaṁśa-nātham ||""",
                "translation": "Adoration to Lord Rama whose complexion is like a blue lotus. Very tender and delightful in appearance. Sita is seated on His left side and He is carrying a powerful bow and arrow in His hands.",
                "confidence_threshold": 0.6
            }
        }
    
    def recognize_prayer(self, text: str) -> Optional[PrayerMatch]:
        """Recognize if text contains a Sanskrit prayer."""
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        text_clean = ' '.join(text_clean.split())  # Normalize whitespace
        
        for prayer_name, prayer_data in self.prayers.items():
            matches = 0
            total_patterns = len(prayer_data["patterns"])
            
            for pattern in prayer_data["patterns"]:
                if re.search(pattern, text_clean, re.IGNORECASE):
                    matches += 1
            
            confidence = matches / total_patterns
            if confidence >= prayer_data["confidence_threshold"]:
                return PrayerMatch(
                    prayer_name=prayer_name,
                    corrected_text=prayer_data["corrected"],
                    confidence=confidence,
                    translation=prayer_data.get("translation")
                )
        
        return None
    
    def is_likely_prayer_segment(self, text: str) -> bool:
        """Check if text segment is likely part of a Sanskrit prayer."""
        text_lower = text.lower().strip()
        
        # Strong indicators that require explicit Sanskrit context
        strong_indicators = [
            r'\boṁ\b|\bauṁ\b',  # Om symbols (word boundary)
            r'namāmi|vande',  # Sanskrit salutations
            r'śāntiḥ.*śāntiḥ.*śāntiḥ',  # Triple peace mantra
            r'brahmānandaṁ|brahm[aā]nand',  # Brahmananda
            r'pūrṇam.*pūrṇam',  # Fullness mantra pattern
            r'mṛtyor.*mā.*amṛtaṁ',  # Asato ma pattern
            r'tryambakaṁ.*yajāmahe',  # Tryambakam mantra
            r'sarve.*bhavantu.*sukhinaḥ'  # Universal blessing
        ]
        
        # Sanskrit diacritical characters indicate Sanskrit text
        sanskrit_diacriticals = ['ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ḹ', 'ṁ', 'ṃ', 'ḥ', 'ś', 'ṣ', 'ñ', 'ṇ', 'ṭ', 'ḍ']
        has_diacriticals = any(char in text for char in sanskrit_diacriticals)
        
        # Check for strong prayer patterns
        strong_matches = sum(1 for pattern in strong_indicators if re.search(pattern, text_lower))
        
        # Must have either:
        # 1. At least one strong indicator AND Sanskrit diacriticals, OR
        # 2. Multiple strong indicators (2+)
        return (strong_matches >= 1 and has_diacriticals) or strong_matches >= 2
    
    def format_prayer_text(self, text: str) -> Tuple[str, bool]:
        """Format prayer text with proper line breaks and spacing."""
        # First, try to recognize as complete prayer
        prayer_match = self.recognize_prayer(text)
        if prayer_match:
            return prayer_match.corrected_text, True
        
        # If not a complete prayer, apply basic formatting
        if self.is_likely_prayer_segment(text):
            # Apply basic Sanskrit text formatting
            formatted = text.strip()
            
            # Only fix Om spacing if it's already Sanskrit (has diacriticals)
            sanskrit_diacriticals = ['ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ḹ', 'ṁ', 'ṃ', 'ḥ', 'ś', 'ṣ', 'ñ', 'ṇ', 'ṭ', 'ḍ']
            has_diacriticals = any(char in text for char in sanskrit_diacriticals)
            
            if has_diacriticals:
                # Fix common spacing issues around Om (only for Sanskrit text)
                formatted = re.sub(r'\b(om|auṁ|oṁ)\s*', 'oṁ ', formatted, flags=re.IGNORECASE)
            
            # Fix śāntiḥ repetitions (only if already present)
            if 'śāntiḥ' in formatted or 'shanti' in formatted.lower():
                formatted = re.sub(r'(śāntiḥ|shanti[hḥ]?)\s*(śāntiḥ|shanti[hḥ]?)\s*(śāntiḥ|shanti[hḥ]?)', 
                                 'śāntiḥ śāntiḥ śāntiḥ', formatted, flags=re.IGNORECASE)
            
            # Add proper ending if it's a mantra (only if already Sanskrit)
            if has_diacriticals and 'śāntiḥ' in formatted.lower() and not formatted.strip().endswith('||'):
                formatted = formatted.strip() + ' ||'
            
            return formatted, True
        
        return text, False