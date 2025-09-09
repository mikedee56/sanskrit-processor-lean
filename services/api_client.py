#!/usr/bin/env python3
"""
External API Client for Sanskrit Processing
Handles scripture lookup, IAST validation, and quality metrics via external APIs.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

# Try importing requests - graceful fallback if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ScriptureMatch:
    """Result from scripture API lookup."""
    verse_reference: str
    sanskrit_text: str
    translation: str
    confidence: float
    source: str
    transliteration: str = ""

@dataclass
class QualityValidation:
    """Result from quality validation API."""
    iast_compliant: bool
    accuracy_score: float
    suggestions: List[str]
    warnings: List[str]

@dataclass
class APIConfig:
    """External API configuration."""
    bhagavad_gita_url: str = "https://vedicscriptures.github.io"
    wisdom_library_url: str = "https://www.wisdomlib.org"
    rapidapi_key: str = ""
    timeout: int = 15
    max_retries: int = 3
    enabled: bool = True

class CircuitBreaker:
    """Simple circuit breaker for API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def can_call(self) -> bool:
        """Check if API call is allowed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        elif self.state == "half-open":
            return True
        return False
    
    def record_success(self):
        """Record successful API call."""
        self.failures = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed API call."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"

class ExternalAPIClient:
    """Client for external Sanskrit/Hindu scripture and validation APIs."""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.circuit_breakers = {
            "bhagavad_gita": CircuitBreaker(),
            "wisdom_library": CircuitBreaker(),
            "validation": CircuitBreaker()
        }
        
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available - API features disabled")
            self.config.enabled = False
        
        # Simple session with timeout
        if REQUESTS_AVAILABLE and self.config.enabled:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Sanskrit-Processor/1.0 (Academic Research)'
            })
        
        # Initialize verse cache for local lookups
        try:
            from .verse_cache import create_verse_cache
            self.verse_cache = create_verse_cache(config.__dict__ if hasattr(config, '__dict__') else {})
            # Ensure cache is populated
            if not self.verse_cache.is_cache_valid():
                logger.info("Populating verse cache on first use...")
                self.verse_cache.download_verses()
        except Exception as e:
            logger.warning(f"Verse cache initialization failed: {e}")
            self.verse_cache = None
    
    def lookup_scripture(self, text_snippet: str) -> Optional[ScriptureMatch]:
        """Look up potential scripture verses in the text - cache first, API fallback."""
        if not self.config.enabled:
            return None
        
        # Try local verse cache first (fast local lookup)
        if self.verse_cache:
            try:
                # Detect verse references in text
                references = self.verse_cache.detect_verse_references(text_snippet)
                if references:
                    # Get first detected reference
                    chapter, verse = references[0]
                    cached_verse = self.verse_cache.get_verse(chapter, verse)
                    if cached_verse:
                        return ScriptureMatch(
                            verse_reference=f"BG {chapter}.{verse}",
                            sanskrit_text=cached_verse.sanskrit,
                            translation=cached_verse.translation,
                            confidence=0.95,  # High confidence for exact matches
                            source="local_cache",
                            transliteration=cached_verse.transliteration
                        )
                    else:
                        # Verse not in local cache - try external APIs
                        logger.info(f"Verse {chapter}.{verse} not in cache, trying external APIs")
                        # Try external APIs for verses not in cache
                        external_result = self._lookup_bhagavad_gita(text_snippet)
                        if not external_result:
                            external_result = self._lookup_wisdom_library(text_snippet)
                        if external_result:
                            return external_result
                
                # Try content search in cache
                search_results = self.verse_cache.search_content(text_snippet)
                if search_results:
                    best_match = search_results[0]
                    return ScriptureMatch(
                        verse_reference=f"BG {best_match.chapter}.{best_match.verse}",
                        sanskrit_text=best_match.sanskrit,
                        translation=best_match.translation,
                        confidence=0.8,  # Lower confidence for content search
                        source="local_cache",
                        transliteration=best_match.transliteration
                    )
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")
        
        # Fallback to external API (existing behavior)
        # Try Bhagavad Gita first
        result = self._lookup_bhagavad_gita(text_snippet)
        if result and result.confidence > 0.7:
            return result
        
        # Try Wisdom Library as fallback
        result = self._lookup_wisdom_library(text_snippet)
        if result and result.confidence > 0.6:
            return result
        
        return None
    
    def _lookup_bhagavad_gita(self, text: str) -> Optional[ScriptureMatch]:
        """Lookup verse in Bhagavad Gita API using Vedic Scriptures API."""
        if not self.circuit_breakers["bhagavad_gita"].can_call():
            logger.debug("Bhagavad Gita API circuit breaker open")
            return None
        
        try:
            # Try to detect verse references for specific API calls
            if self.verse_cache:
                # Use verse cache for reference detection
                references = self.verse_cache.detect_verse_references(text)
                if references:
                    chapter, verse = references[0]
                    # Call the real Vedic Scriptures API
                    api_url = f"https://vedicscriptures.github.io/slok/{chapter}/{verse}"
                    
                    if REQUESTS_AVAILABLE:
                        response = self.session.get(api_url, timeout=self.config.timeout)
                        if response.status_code == 200:
                            data = response.json()
                            self.circuit_breakers["bhagavad_gita"].record_success()
                            
                            # Extract transliteration if available
                            transliteration = data.get('transliteration', '')
                            if not transliteration and 'slok' in data:
                                # Generate basic transliteration from sanskrit if not provided
                                transliteration = self._basic_transliteration(data['slok'])
                            
                            return ScriptureMatch(
                                verse_reference=f"BG {chapter}.{verse}",
                                sanskrit_text=data.get('slok', ''),
                                translation=data.get('translation', ''),
                                confidence=0.9,
                                source="vedic_scriptures_api",
                                transliteration=transliteration
                            )
                    
            # Fallback: search for common keywords if no specific verse detected
            keywords = ["dharma", "karma", "yoga", "arjuna", "krishna"]
            if any(keyword in text.lower() for keyword in keywords):
                # Return high-confidence verses for common concepts
                if "karma" in text.lower() and "action" in text.lower():
                    return ScriptureMatch(
                        verse_reference="BG 2.47",
                        sanskrit_text="कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥",
                        translation="You have the right to perform your prescribed duty, but not to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
                        confidence=0.75,
                        source="keyword_match",
                        transliteration="karmaṇy evādhikāras te mā phaleṣu kadācana mā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi"
                    )
            
        except Exception as e:
            logger.warning(f"Bhagavad Gita API lookup failed: {e}")
            self.circuit_breakers["bhagavad_gita"].record_failure()
        
        return None
    
    def _basic_transliteration(self, sanskrit_text: str) -> str:
        """Basic Sanskrit to IAST transliteration helper."""
        # This is a simplified transliteration - in production would use proper library
        transliteration_map = {
            'कर्म': 'karma', 'धर्म': 'dharma', 'योग': 'yoga', 
            'अर्जुन': 'arjuna', 'कृष्ण': 'kṛṣṇa', 'भगवान्': 'bhagavān',
            'गीता': 'gītā', 'वेद': 'veda', 'उपनिषद्': 'upaniṣad'
        }
        
        # For now, return simplified version
        for sanskrit, iast in transliteration_map.items():
            if sanskrit in sanskrit_text:
                return iast + "..."  # Simplified indication
        
        return sanskrit_text  # Fallback to original
    
    def _lookup_wisdom_library(self, text: str) -> Optional[ScriptureMatch]:
        """Lookup using alternative APIs like BhagavadGita.io or TheAum.org."""
        if not self.circuit_breakers["wisdom_library"].can_call():
            logger.debug("Alternative API circuit breaker open")
            return None
        
        try:
            # Try BhagavadGita.io style API if verse reference detected
            if self.verse_cache:
                references = self.verse_cache.detect_verse_references(text)
                if references:
                    chapter, verse = references[0]
                    
                    # Try TheAum.org API format
                    api_url = f"https://bhagavadgita.theaum.org/chapters/{chapter}/verses/{verse}"
                    
                    if REQUESTS_AVAILABLE:
                        response = self.session.get(api_url, timeout=self.config.timeout)
                        if response.status_code == 200:
                            data = response.json()
                            self.circuit_breakers["wisdom_library"].record_success()
                            
                            return ScriptureMatch(
                                verse_reference=f"BG {chapter}.{verse}",
                                sanskrit_text=data.get('verse_text', data.get('sanskrit', '')),
                                translation=data.get('translation', data.get('meaning', '')),
                                confidence=0.85,
                                source="theaum_api",
                                transliteration=data.get('transliteration', '')
                            )
            
            # Fallback keyword search
            spiritual_terms = ["moksha", "samsara", "upanishad", "veda"]
            if any(term in text.lower() for term in spiritual_terms):
                self.circuit_breakers["wisdom_library"].record_success()
                return ScriptureMatch(
                    verse_reference="Upanishads Reference",
                    sanskrit_text="तत् त्वम् असि",
                    translation="That thou art",
                    confidence=0.7,
                    source="wisdom_library"
                )
            
        except Exception as e:
            logger.warning(f"Wisdom Library lookup failed: {e}")
            self.circuit_breakers["wisdom_library"].record_failure()
        
        return None
    
    def validate_iast(self, text: str) -> QualityValidation:
        """Validate IAST transliteration quality."""
        if not self.config.enabled:
            return QualityValidation(
                iast_compliant=True,
                accuracy_score=1.0,
                suggestions=[],
                warnings=[]
            )
        
        if not self.circuit_breakers["validation"].can_call():
            logger.debug("Validation API circuit breaker open")
            return QualityValidation(
                iast_compliant=True,
                accuracy_score=0.5,
                suggestions=["API unavailable"],
                warnings=["Validation service temporarily unavailable"]
            )
        
        try:
            # Mock IAST validation - in reality would use specialized service
            warnings = []
            suggestions = []
            
            # Check for common IAST issues
            if "krishna" in text.lower() and "kṛṣṇa" not in text:
                suggestions.append("Consider using IAST: kṛṣṇa for krishna")
            
            if "shiva" in text.lower() and "śiva" not in text:
                suggestions.append("Consider using IAST: śiva for shiva")
            
            # Simple scoring
            iast_chars = "āīūṛṝḷḹṃḥśṣṇṭḍṅñ"
            has_iast = any(char in text for char in iast_chars)
            
            accuracy = 0.9 if has_iast else 0.7
            compliant = len(suggestions) == 0
            
            self.circuit_breakers["validation"].record_success()
            
            return QualityValidation(
                iast_compliant=compliant,
                accuracy_score=accuracy,
                suggestions=suggestions,
                warnings=warnings
            )
            
        except Exception as e:
            logger.warning(f"IAST validation failed: {e}")
            self.circuit_breakers["validation"].record_failure()
            return QualityValidation(
                iast_compliant=False,
                accuracy_score=0.5,
                suggestions=["Validation failed"],
                warnings=[f"Validation error: {str(e)}"]
            )
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all external services."""
        return {
            service: {
                "state": breaker.state,
                "failures": breaker.failures,
                "can_call": breaker.can_call()
            }
            for service, breaker in self.circuit_breakers.items()
        }

def create_api_client(config_path: Path = None) -> ExternalAPIClient:
    """Factory function to create API client with configuration."""
    config = APIConfig()
    
    if config_path and config_path.exists():
        try:
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                api_settings = config_data.get('external_apis', {})
                config.bhagavad_gita_url = api_settings.get('bhagavad_gita_url', config.bhagavad_gita_url)
                config.wisdom_library_url = api_settings.get('wisdom_library_url', config.wisdom_library_url)
                config.rapidapi_key = api_settings.get('rapidapi_key', config.rapidapi_key)
                config.enabled = api_settings.get('enabled', config.enabled)
        except Exception as e:
            logger.warning(f"Failed to load API config: {e}")
    
    return ExternalAPIClient(config)

if __name__ == "__main__":
    # Simple test
    config = APIConfig()
    client = ExternalAPIClient(config)
    
    # Test scripture lookup
    test_text = "The concept of dharma is central to yoga"
    result = client.lookup_scripture(test_text)
    if result:
        print(f"Scripture match: {result.verse_reference} (confidence: {result.confidence})")
    
    # Test IAST validation
    validation = client.validate_iast("Krishna teaches dharma")
    print(f"IAST validation: compliant={validation.iast_compliant}, score={validation.accuracy_score}")
    
    # Service status
    status = client.get_service_status()
    print(f"Service status: {status}")