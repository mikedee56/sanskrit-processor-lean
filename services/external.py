"""
External services integration for Sanskrit Processor - Lean Architecture
Consolidated from multiple service files to maintain lean codebase
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EntityMatch:
    """Simple entity match result."""
    text: str
    start: int
    end: int
    confidence: float = 1.0

class SimpleCache:
    """Ultra-simple in-memory cache for verses and entities."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Any] = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any):
        if len(self._cache) >= self.max_size:
            # Simple LRU - remove first item
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[key] = value
    
    def clear(self):
        self._cache.clear()

class SimpleFallbackNER:
    """Ultra-simple NER fallback using keyword matching."""
    
    def __init__(self, entities_file: Optional[Path] = None):
        self.entities = {}
        self.cache = SimpleCache()
        
        if entities_file and entities_file.exists():
            try:
                self.entities = json.loads(entities_file.read_text())
            except Exception as e:
                logger.warning(f"Could not load entities: {e}")
    
    def extract_entities(self, text: str) -> List[EntityMatch]:
        """Extract entities using simple keyword matching."""
        if not text or not self.entities:
            return []
        
        # Check cache first
        cached = self.cache.get(text)
        if cached:
            return cached
        
        entities = []
        text_lower = text.lower()
        
        for entity_type, entity_list in self.entities.items():
            for entity in entity_list:
                if entity.lower() in text_lower:
                    start = text_lower.find(entity.lower())
                    entities.append(EntityMatch(
                        text=entity,
                        start=start,
                        end=start + len(entity)
                    ))
        
        # Cache result
        self.cache.set(text, entities)
        return entities

# Optional external clients (keep lean - only if truly needed)
class ExternalClients:
    """Container for optional external service clients."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mcp_client = None
        self.api_client = None
        
        # Only initialize if explicitly configured
        if config.get('mcp', {}).get('enabled', False):
            try:
                from .mcp_client import MCPClient
                self.mcp_client = MCPClient(config['mcp'])
            except ImportError:
                logger.info("MCP client not available")
        
        if config.get('api', {}).get('enabled', False):
            try:
                from .api_client import APIClient  
                self.api_client = APIClient(config['api'])
            except ImportError:
                logger.info("API client not available")
    
    def close(self):
        """Close all external connections."""
        if self.mcp_client:
            try:
                self.mcp_client.close()
            except:
                pass
        
        if self.api_client:
            try:
                self.api_client.close()
            except:
                pass

# CONSOLIDATED SERVICE MANAGER - Service Layer Consolidation
class ExternalServiceManager:
    """
    Unified manager for all external service integrations.
    Consolidates MCP and API client functionality with feature flag support.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.use_consolidated = config.get('processing', {}).get('use_consolidated_services', False)
        
        # Initialize components
        self._mcp_config = None
        self._api_config = None
        self._ws = None
        self._session = None
        self._circuit_breakers = {}
        self._verse_cache = None
        
        if self.use_consolidated:
            self._init_consolidated_services()
        else:
            # Legacy fallback - use original ExternalClients
            self._legacy_clients = ExternalClients(config)
    
    def _init_consolidated_services(self):
        """Initialize consolidated MCP and API services."""
        # MCP Configuration
        if self.config.get('services', {}).get('consolidated', {}).get('mcp', {}).get('enabled', True):
            self._init_mcp_service()
        
        # API Configuration  
        if self.config.get('services', {}).get('consolidated', {}).get('api', {}).get('enabled', True):
            self._init_api_service()
    
    def _init_mcp_service(self):
        """Initialize consolidated MCP service."""
        try:
            # Import MCP dependencies
            import websocket
            
            mcp_config = self.config.get('services', {}).get('consolidated', {}).get('mcp', {})
            self._mcp_config = {
                'enabled': True,
                'server_url': mcp_config.get('server_url', 'ws://localhost:8080'),
                'timeout': mcp_config.get('timeout', 30),
                'max_retries': mcp_config.get('max_retries', 3)
            }
            
            logger.info("MCP service initialized in consolidated manager")
            
        except ImportError:
            logger.warning("MCP dependencies not available - MCP features disabled")
            self._mcp_config = None
    
    def _init_api_service(self):
        """Initialize consolidated API service."""
        try:
            import requests
            
            api_config = self.config.get('services', {}).get('consolidated', {}).get('api', {})
            self._api_config = {
                'enabled': True,
                'timeout': api_config.get('timeout', 10),
                'max_retries': api_config.get('max_retries', 2)
            }
            
            # Initialize session
            self._session = requests.Session()
            self._session.headers.update({
                'User-Agent': 'Sanskrit-Processor/1.0 (Academic Research)'
            })
            
            # Initialize circuit breakers
            self._circuit_breakers = {
                "bhagavad_gita": self._create_circuit_breaker(),
                "wisdom_library": self._create_circuit_breaker(),
                "validation": self._create_circuit_breaker()
            }
            
            # Initialize verse cache
            self._init_verse_cache()
            
            logger.info("API service initialized in consolidated manager")
            
        except ImportError:
            logger.warning("Requests library not available - API features disabled")
            self._api_config = None
    
    def _create_circuit_breaker(self):
        """Create a simple circuit breaker for API resilience."""
        class SimpleCircuitBreaker:
            def __init__(self):
                self.failure_count = 0
                self.max_failures = 3
                self.reset_timeout = 60
                self.last_failure = None
            
            def can_execute(self):
                if self.failure_count < self.max_failures:
                    return True
                return False  # Simplified - in production would check timeout
            
            def record_success(self):
                self.failure_count = 0
                self.last_failure = None
            
            def record_failure(self):
                self.failure_count += 1
                import time
                self.last_failure = time.time()
        
        return SimpleCircuitBreaker()
    
    def _init_verse_cache(self):
        """Initialize verse cache for scripture lookup."""
        try:
            # Simple cache implementation
            self._verse_cache = SimpleCache(max_size=5000)
            logger.info("Verse cache initialized")
        except Exception as e:
            logger.warning(f"Verse cache initialization failed: {e}")
            self._verse_cache = None
    
    # MCP CONSOLIDATED METHODS
    def mcp_analyze_batch(self, segments: List[str]) -> List[dict]:
        """Consolidated MCP batch analysis."""
        if not self.use_consolidated:
            # Delegate to legacy client
            if hasattr(self._legacy_clients, 'mcp_client') and self._legacy_clients.mcp_client:
                return self._legacy_clients.mcp_client.batch_analyze(segments)
            return []
        
        if not self._mcp_config or not self._mcp_config.get('enabled'):
            return []
        
        try:
            # Consolidated MCP batch processing
            results = []
            for segment in segments:
                result = self._mcp_send_request({
                    "method": "analyze_batch",
                    "params": {"text": segment}
                })
                if result:
                    results.append(result)
            return results
        except Exception as e:
            logger.error(f"MCP batch analysis failed: {e}")
            return []
    
    def mcp_enhance_segment(self, text: str) -> str:
        """Consolidated MCP segment enhancement."""
        if not self.use_consolidated:
            # Delegate to legacy client
            if hasattr(self._legacy_clients, 'mcp_client') and self._legacy_clients.mcp_client:
                return self._legacy_clients.mcp_client.context_correct(text, {})
            return text
        
        if not self._mcp_config or not self._mcp_config.get('enabled'):
            return text
        
        try:
            result = self._mcp_send_request({
                "method": "context_correct",
                "params": {"text": text, "context": {}}
            })
            return result.get('corrected_text', text) if result else text
        except Exception as e:
            logger.error(f"MCP enhancement failed: {e}")
            return text
    
    def _mcp_send_request(self, request: dict) -> Optional[dict]:
        """Send request to MCP service with consolidated connection handling."""
        if not self._mcp_config:
            return None
        
        try:
            # Simplified MCP request handling
            # In production, would maintain WebSocket connection
            logger.debug(f"MCP request: {request['method']}")
            
            # Mock response for development
            if request['method'] == 'analyze_batch':
                return {"analysis": "enhanced", "confidence": 0.8}
            elif request['method'] == 'context_correct':
                return {"corrected_text": request['params']['text']}
            
            return None
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            return None
    
    # API CONSOLIDATED METHODS  
    def api_lookup_scripture(self, term: str) -> dict:
        """Consolidated scripture lookup."""
        if not self.use_consolidated:
            # Delegate to legacy client
            if hasattr(self._legacy_clients, 'api_client') and self._legacy_clients.api_client:
                return self._legacy_clients.api_client.lookup_scripture(term)
            return {}
        
        if not self._api_config or not self._api_config.get('enabled'):
            return {}
        
        # Check cache first
        if self._verse_cache:
            cached = self._verse_cache.get(f"scripture:{term}")
            if cached:
                return cached
        
        try:
            # Consolidated scripture lookup
            result = {}
            
            # Try Bhagavad Gita API
            if self._circuit_breakers["bhagavad_gita"].can_execute():
                bg_result = self._lookup_bhagavad_gita_consolidated(term)
                if bg_result:
                    result.update(bg_result)
                    self._circuit_breakers["bhagavad_gita"].record_success()
                else:
                    self._circuit_breakers["bhagavad_gita"].record_failure()
            
            # Cache result
            if result and self._verse_cache:
                self._verse_cache.set(f"scripture:{term}", result)
            
            return result
        except Exception as e:
            logger.error(f"Scripture lookup failed: {e}")
            return {}
    
    def api_validate_iast(self, text: str) -> bool:
        """Consolidated IAST validation."""
        if not self.use_consolidated:
            # Delegate to legacy client
            if hasattr(self._legacy_clients, 'api_client') and self._legacy_clients.api_client:
                return self._legacy_clients.api_client.validate_iast(text)
            return True  # Default to valid
        
        if not self._api_config or not self._api_config.get('enabled'):
            return True
        
        try:
            # Simplified IAST validation
            # Check for basic IAST diacritics
            iast_chars = 'āīūṛṝḷḹēōṃḥṅñṭḍṇśṣ'
            has_iast = any(char in text for char in iast_chars)
            return has_iast or text.isascii()  # Valid if has IAST or plain ASCII
        except Exception as e:
            logger.error(f"IAST validation failed: {e}")
            return True
    
    def _lookup_bhagavad_gita_consolidated(self, term: str) -> Optional[dict]:
        """Consolidated Bhagavad Gita lookup."""
        if not self._session:
            return None
        
        try:
            # Simplified API call
            url = "https://bhagavadgita.io/api/v1/search"
            response = self._session.get(
                url,
                params={"query": term},
                timeout=self._api_config.get('timeout', 10)
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "source": "bhagavad_gita",
                    "results": data.get("results", [])
                }
        except Exception as e:
            logger.debug(f"Bhagavad Gita lookup failed: {e}")
        
        return None
    
    # UNIFIED SERVICE MANAGEMENT
    def get_service_status(self) -> dict:
        """Get consolidated service status."""
        if not self.use_consolidated:
            # Delegate to legacy clients
            return {
                "mode": "legacy",
                "mcp_client": "available" if (hasattr(self._legacy_clients, 'mcp_client') and self._legacy_clients.mcp_client) else "disabled",
                "api_client": "available" if (hasattr(self._legacy_clients, 'api_client') and self._legacy_clients.api_client) else "disabled"
            }
        
        return {
            "mode": "consolidated",
            "mcp_service": "enabled" if (self._mcp_config and self._mcp_config.get('enabled')) else "disabled",
            "api_service": "enabled" if (self._api_config and self._api_config.get('enabled')) else "disabled",
            "circuit_breakers": {k: "open" if v.can_execute() else "closed" for k, v in self._circuit_breakers.items()}
        }
    
    def close(self):
        """Close all external connections."""
        if not self.use_consolidated:
            if hasattr(self, '_legacy_clients'):
                self._legacy_clients.close()
            return
        
        # Close consolidated services
        if self._ws:
            try:
                self._ws.close()
            except:
                pass
        
        if self._session:
            try:
                self._session.close()
            except:
                pass
        
        if self._verse_cache:
            self._verse_cache.clear()
