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
    """Simplified MCP client using HTTP instead of WebSocket for basic operations."""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.session = None
        
        if not MCP_AVAILABLE:
            logger.warning("MCP client dependencies not available - running in fallback mode")
            self.config.enabled = False
            return
            
        if self.config.enabled:
            try:
                # Use HTTP session instead of WebSocket for simplicity
                import requests
                self.session = requests.Session()
                self.session.headers.update({
                    'Content-Type': 'application/json',
                    'User-Agent': 'Sanskrit-Processor-MCP/1.0'
                })
                # Convert ws:// URL to http:// for simplified API
                self.api_url = self.config.server_url.replace('ws://', 'http://').replace('wss://', 'https://')
                if not self.api_url.endswith('/'):
                    self.api_url += '/'
                logger.info(f"MCP client configured for HTTP API at {self.api_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize MCP client: {e}")
                self.config.enabled = False
    
    def _send_request(self, endpoint: str, data: Dict) -> Dict:
        """Send HTTP request to MCP server instead of WebSocket."""
        if not self.config.enabled or not self.session:
            return {}
            
        try:
            url = f"{self.api_url}{endpoint}"
            response = self.session.post(
                url, 
                json=data, 
                timeout=self.config.timeout if hasattr(self.config, 'timeout') else 10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"MCP API returned status {response.status_code}")
                return {}
                
        except Exception as e:
            logger.warning(f"MCP HTTP request failed: {e}")
            return {}
    
    def analyze_semantics(self, text: str, context: Dict = None) -> SemanticAnalysisResult:
        """Perform semantic analysis on text via simplified MCP API."""
        if not self.config.enabled:
            # Fallback: return unchanged text
            return SemanticAnalysisResult(
                enhanced_text=text,
                entities_found=[],
                confidence_score=1.0,
                corrections_applied=[]
            )
        
        try:
            data = {
                "text": text,
                "domain": "yoga_vedanta",
                "features": ["ner", "capitalization", "context_correction"]
            }
            
            if context:
                data["context"] = context
            
            result = self._send_request("analyze", data)
            
            if result:
                return SemanticAnalysisResult(
                    enhanced_text=result.get("enhanced_text", text),
                    entities_found=result.get("entities", []),
                    confidence_score=result.get("confidence", 0.8),
                    corrections_applied=result.get("corrections", [])
                )
            else:
                # Fallback on API failure
                return SemanticAnalysisResult(
                    enhanced_text=text,
                    entities_found=[],
                    confidence_score=0.5,
                    corrections_applied=[]
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
        """Enhance capitalization using simplified MCP API."""
        if not self.config.enabled:
            return text
        
        try:
            data = {
                "text": text,
                "operation": "capitalize_entities",
                "domain": domain
            }
            
            result = self._send_request("enhance", data)
            return result.get("enhanced_text", text) if result else text
            
        except Exception as e:
            logger.warning(f"MCP capitalization enhancement failed: {e}")
            return text
    
    def context_correct(self, text: str, previous_text: str = None, domain: str = "yoga_vedanta") -> str:
        """Apply context-aware corrections via simplified MCP API."""
        if not self.config.enabled:
            return text
        
        try:
            data = {
                "text": text,
                "operation": "context_correct",
                "domain": domain
            }
            
            if previous_text:
                data["context"] = {"previous_segment": previous_text}
            
            result = self._send_request("correct", data)
            return result.get("enhanced_text", text) if result else text
            
        except Exception as e:
            logger.warning(f"MCP context correction failed: {e}")
            return text
    
    def batch_analyze(self, texts: List[str], context: Dict = None) -> List[SemanticAnalysisResult]:
        """Analyze multiple texts via simplified batch API."""
        if not self.config.enabled:
            return [SemanticAnalysisResult(
                enhanced_text=text,
                entities_found=[],
                confidence_score=1.0,
                corrections_applied=[]
            ) for text in texts]
        
        try:
            data = {
                "texts": texts,
                "domain": "yoga_vedanta",
                "features": ["ner", "capitalization", "context_correction"]
            }
            
            if context:
                data["context"] = context
            
            result = self._send_request("batch", data)
            
            if result and "results" in result:
                results = []
                for i, text in enumerate(texts):
                    batch_result = result["results"][i] if i < len(result["results"]) else {}
                    
                    results.append(SemanticAnalysisResult(
                        enhanced_text=batch_result.get("enhanced_text", text),
                        entities_found=batch_result.get("entities", []),
                        confidence_score=batch_result.get("confidence", 0.8),
                        corrections_applied=batch_result.get("corrections", [])
                    ))
                
                return results
            else:
                # Fallback on API failure
                return [SemanticAnalysisResult(
                    enhanced_text=text,
                    entities_found=[],
                    confidence_score=0.5,
                    corrections_applied=[]
                ) for text in texts]
            
        except Exception as e:
            logger.warning(f"MCP batch analysis failed: {e}")
            return [SemanticAnalysisResult(
                enhanced_text=text,
                entities_found=[],
                confidence_score=0.5,
                corrections_applied=[]
            ) for text in texts]
    
    def close(self):
        """Close HTTP session."""
        if self.session:
            try:
                self.session.close()
                logger.info("MCP HTTP session closed")
            except Exception as e:
                logger.warning(f"Error closing MCP session: {e}")

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