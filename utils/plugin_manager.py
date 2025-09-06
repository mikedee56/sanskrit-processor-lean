"""
Simple Plugin Manager for Sanskrit Processor
Lean architecture compliant - function-based plugins with error isolation
"""
import logging
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PluginManager:
    """Minimal plugin system using duck typing and function-based plugins."""
    
    def __init__(self):
        self.plugins: Dict[str, Callable] = {}
        self.enabled = False
        
    def enable(self):
        """Enable plugin system."""
        self.enabled = True
        logger.info("Plugin system enabled")
        
    def disable(self):
        """Disable plugin system."""
        self.enabled = False
        logger.info("Plugin system disabled")
        
    def register(self, name: str, plugin_func: Callable[[str], str]):
        """Register a simple function as a plugin."""
        if not callable(plugin_func):
            raise ValueError(f"Plugin {name} must be callable")
        self.plugins[name] = plugin_func
        logger.info(f"Registered plugin: {name}")
        
    def execute_plugin(self, name: str, text: str) -> str:
        """Execute specific plugin if available and enabled."""
        if not self.enabled or name not in self.plugins:
            return text
        
        # Input validation for security
        if not isinstance(text, str):
            logger.warning(f"Plugin {name}: Invalid input type, converting to string")
            text = str(text) if text is not None else ""
            
        try:
            result = self.plugins[name](text)
            # Validate plugin output
            if not isinstance(result, str):
                logger.warning(f"Plugin {name}: Invalid output type, converting to string")
                result = str(result) if result is not None else text
            logger.debug(f"Plugin {name} processed text")
            return result
        except Exception as e:
            logger.error(f"Plugin {name} failed: {e}")
            return text  # Fail gracefully, return original text
            
    def execute_all(self, text: str) -> str:
        """Execute all registered plugins in sequence."""
        if not self.enabled:
            return text
        
        # Input validation for security
        if not isinstance(text, str):
            logger.warning("Plugin system: Invalid input type, converting to string")
            text = str(text) if text is not None else ""
            
        result = text
        for name, plugin_func in self.plugins.items():
            try:
                plugin_result = plugin_func(result)
                # Validate each plugin's output
                if not isinstance(plugin_result, str):
                    logger.warning(f"Plugin {name}: Invalid output type, skipping")
                    continue
                result = plugin_result
                logger.debug(f"Plugin {name} processed text")
            except Exception as e:
                logger.error(f"Plugin {name} failed: {e}")
                # Continue with other plugins - don't let one failure stop the chain
                
        return result
        
    def list_plugins(self) -> list:
        """Return list of registered plugin names."""
        return list(self.plugins.keys())
        
    def remove_plugin(self, name: str) -> bool:
        """Remove a plugin by name."""
        if name in self.plugins:
            del self.plugins[name]
            logger.info(f"Removed plugin: {name}")
            return True
        return False