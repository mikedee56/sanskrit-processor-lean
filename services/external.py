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