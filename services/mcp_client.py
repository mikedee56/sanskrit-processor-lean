#!/usr/bin/env python3
"""
MCP Client for Sanskrit Processing
Handles semantic analysis, NER, and context-aware corrections via MCP server.
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

# Try importing mcp client - graceful fallback if not available
try:
    import websocket
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class SemanticAnalysisResult:
    """Result from MCP semantic analysis."""
    enhanced_text: str
    entities_found: List[Dict[str, Any]]
    confidence_score: float
    corrections_applied: List[Dict[str, str]]

@dataclass
class MCPConfig:
    """MCP client configuration."""
    server_url: str = "ws://localhost:3001/mcp"
    timeout: int = 10
    enabled: bool = True

class MCPClient:
    """Simple MCP client for Sanskrit processing enhancements."""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.connected = False
        self.ws = None
        
        if not MCP_AVAILABLE:
            logger.warning("MCP client dependencies not available - running in fallback mode")
            self.config.enabled = False
            return
            
        if self.config.enabled:
            try:
                self._connect()
            except Exception as e:
                logger.warning(f"Failed to connect to MCP server: {e}")
                self.config.enabled = False
    
    def _connect(self):
        """Establish connection to MCP server."""
        if not self.config.enabled or not MCP_AVAILABLE:
            return
            
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(self.config.server_url)
            self.connected = True
            logger.info(f"Connected to MCP server at {self.config.server_url}")
        except Exception as e:
            logger.error(f"MCP connection failed: {e}")
            self.connected = False
            raise
    
    def _send_request(self, method: str, params: Dict) -> Dict:
        """Send request to MCP server."""
        if not self.connected:
            raise ConnectionError("MCP server not connected")
            
        request = {
            "method": method,
            "params": params,
            "id": 1
        }
        
        try:
            self.ws.send(json.dumps(request))
            response = json.loads(self.ws.recv())
            
            if "error" in response:
                raise RuntimeError(f"MCP error: {response['error']}")
                
            return response.get("result", {})
            
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            raise
    
    def analyze_semantics(self, text: str, context: Dict = None) -> SemanticAnalysisResult:
        """Perform semantic analysis on text via MCP."""
        if not self.config.enabled:
            # Fallback: return unchanged text
            return SemanticAnalysisResult(
                enhanced_text=text,
                entities_found=[],
                confidence_score=1.0,
                corrections_applied=[]
            )
        
        try:
            params = {
                "text": text,
                "domain": "yoga_vedanta",
                "features": ["ner", "capitalization", "context_correction"]
            }
            
            if context:
                params["context"] = context
            
            result = self._send_request("analyze_semantics", params)
            
            return SemanticAnalysisResult(
                enhanced_text=result.get("enhanced_text", text),
                entities_found=result.get("entities", []),
                confidence_score=result.get("confidence", 0.8),
                corrections_applied=result.get("corrections", [])
            )
            
        except Exception as e:
            logger.warning(f"MCP semantic analysis failed, using fallback: {e}")
            return SemanticAnalysisResult(
                enhanced_text=text,
                entities_found=[],
                confidence_score=0.5,
                corrections_applied=[]
            )
    
    def enhance_capitalization(self, text: str, domain: str = "spiritual") -> str:
        """Enhance capitalization using MCP NER capabilities."""
        if not self.config.enabled:
            return text
        
        try:
            params = {
                "text": text,
                "operation": "capitalize_entities",
                "domain": domain
            }
            
            result = self._send_request("enhance_text", params)
            return result.get("enhanced_text", text)
            
        except Exception as e:
            logger.warning(f"MCP capitalization enhancement failed: {e}")
            return text
    
    def context_correct(self, text: str, previous_text: str = None, domain: str = "yoga_vedanta") -> str:
        """Apply context-aware corrections via MCP."""
        if not self.config.enabled:
            return text
        
        try:
            params = {
                "text": text,
                "operation": "context_correct",
                "domain": domain
            }
            
            if previous_text:
                params["context"] = {"previous_segment": previous_text}
            
            result = self._send_request("enhance_text", params)
            return result.get("enhanced_text", text)
            
        except Exception as e:
            logger.warning(f"MCP context correction failed: {e}")
            return text
    
    def batch_analyze(self, texts: List[str], context: Dict = None) -> List[SemanticAnalysisResult]:
        """Analyze multiple texts in a single request."""
        if not self.config.enabled:
            return [SemanticAnalysisResult(
                enhanced_text=text,
                entities_found=[],
                confidence_score=1.0,
                corrections_applied=[]
            ) for text in texts]
        
        try:
            params = {
                "texts": texts,
                "domain": "yoga_vedanta",
                "features": ["ner", "capitalization", "context_correction"]
            }
            
            if context:
                params["context"] = context
            
            result = self._send_request("batch_analyze", params)
            
            results = []
            for i, text in enumerate(texts):
                batch_result = result.get("results", [{}])[i] if i < len(result.get("results", [])) else {}
                
                results.append(SemanticAnalysisResult(
                    enhanced_text=batch_result.get("enhanced_text", text),
                    entities_found=batch_result.get("entities", []),
                    confidence_score=batch_result.get("confidence", 0.8),
                    corrections_applied=batch_result.get("corrections", [])
                ))
            
            return results
            
        except Exception as e:
            logger.warning(f"MCP batch analysis failed: {e}")
            return [SemanticAnalysisResult(
                enhanced_text=text,
                entities_found=[],
                confidence_score=0.5,
                corrections_applied=[]
            ) for text in texts]
    
    def close(self):
        """Close MCP connection."""
        if self.ws:
            try:
                self.ws.close()
                self.connected = False
                logger.info("MCP connection closed")
            except Exception as e:
                logger.warning(f"Error closing MCP connection: {e}")

def create_mcp_client(config_path: Path = None) -> MCPClient:
    """Factory function to create MCP client with configuration."""
    config = MCPConfig()
    
    if config_path and config_path.exists():
        try:
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                mcp_settings = config_data.get('mcp', {})
                config.server_url = mcp_settings.get('server_url', config.server_url)
                config.timeout = mcp_settings.get('timeout', config.timeout)
                config.enabled = mcp_settings.get('enabled', config.enabled)
        except Exception as e:
            logger.warning(f"Failed to load MCP config: {e}")
    
    return MCPClient(config)

if __name__ == "__main__":
    # Simple test
    config = MCPConfig(enabled=False)  # Disable for testing
    client = MCPClient(config)
    
    test_text = "welcome to this bhagavad gita lecture on dharma"
    result = client.analyze_semantics(test_text)
    print(f"MCP Test: '{test_text}' -> '{result.enhanced_text}'")