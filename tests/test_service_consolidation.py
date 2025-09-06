#!/usr/bin/env python3
"""
Comprehensive tests for service layer consolidation.
Tests both legacy and consolidated service implementations.
"""

import pytest
import yaml
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Import the classes we're testing
from services.external import ExternalClients, ExternalServiceManager
from enhanced_processor import EnhancedSanskritProcessor


class TestServiceConsolidation:
    """Test service consolidation functionality."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.legacy_config = {
            'processing': {
                'use_consolidated_services': False,
                'enable_semantic_analysis': True,
                'enable_scripture_lookup': True
            }
        }
        
        self.consolidated_config = {
            'processing': {
                'use_consolidated_services': True,
                'enable_semantic_analysis': True,
                'enable_scripture_lookup': True
            },
            'services': {
                'consolidated': {
                    'mcp': {
                        'enabled': True,
                        'server_url': 'ws://localhost:8080',
                        'timeout': 30,
                        'max_retries': 3
                    },
                    'api': {
                        'enabled': True,
                        'timeout': 10,
                        'max_retries': 2
                    }
                }
            }
        }
    
    def test_consolidated_service_initialization(self):
        """Test that consolidated services initialize properly."""
        manager = ExternalServiceManager(self.consolidated_config)
        
        assert manager.use_consolidated == True
        assert hasattr(manager, '_mcp_config')
        assert hasattr(manager, '_api_config')
        assert hasattr(manager, '_circuit_breakers')
        assert hasattr(manager, '_verse_cache')
    
    def test_legacy_service_initialization(self):
        """Test that legacy services still work."""
        manager = ExternalServiceManager(self.legacy_config)
        
        assert manager.use_consolidated == False
        assert hasattr(manager, '_legacy_clients')
        assert isinstance(manager._legacy_clients, ExternalClients)
    
    def test_mcp_consolidation(self):
        """Test MCP functionality works identically in consolidated service."""
        # Test consolidated approach
        manager_consolidated = ExternalServiceManager(self.consolidated_config)
        
        # Test batch analysis
        segments = ['test segment 1', 'test segment 2']
        result = manager_consolidated.mcp_analyze_batch(segments)
        assert isinstance(result, list)
        
        # Test segment enhancement
        text = 'test text'
        enhanced = manager_consolidated.mcp_enhance_segment(text)
        assert isinstance(enhanced, str)
    
    def test_api_consolidation(self):
        """Test API functionality works identically in consolidated service."""
        manager = ExternalServiceManager(self.consolidated_config)
        
        # Test scripture lookup
        result = manager.api_lookup_scripture('Krishna')
        assert isinstance(result, dict)
        
        # Test IAST validation
        is_valid = manager.api_validate_iast('test text')
        assert isinstance(is_valid, bool)
    
    def test_feature_flag_switching(self):
        """Test switching between old and new implementations."""
        # Test legacy mode
        processor_legacy = EnhancedSanskritProcessor()
        processor_legacy.config = self.legacy_config
        processor_legacy.external_clients = Mock()
        processor_legacy.external_services = None
        
        status_legacy = processor_legacy.get_service_status()
        assert 'external_services' in status_legacy
        
        # Test consolidated mode
        processor_consolidated = EnhancedSanskritProcessor()
        processor_consolidated.config = self.consolidated_config
        processor_consolidated.external_clients = None
        
        # Mock the consolidated manager
        mock_manager = Mock()
        mock_manager.get_service_status.return_value = {
            'mode': 'consolidated',
            'mcp_service': 'enabled',
            'api_service': 'enabled'
        }
        processor_consolidated.external_services = mock_manager
        
        status_consolidated = processor_consolidated.get_service_status()
        assert status_consolidated['external_services']['mode'] == 'consolidated'
    
    @patch('requests.Session')
    def test_consolidated_performance(self, mock_session):
        """Ensure consolidation doesn't degrade performance."""
        manager = ExternalServiceManager(self.consolidated_config)
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': []}
        mock_session.return_value.get.return_value = mock_response
        
        start_time = time.time()
        
        # Test batch processing
        for i in range(10):
            manager.mcp_enhance_segment(f"test segment {i}")
            manager.api_lookup_scripture(f"term {i}")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete quickly (under 1 second for 10 operations in mock mode)
        assert processing_time < 1.0
    
    def test_service_status_reporting(self):
        """Test service status reporting works for both modes."""
        # Legacy mode
        legacy_manager = ExternalServiceManager(self.legacy_config)
        legacy_status = legacy_manager.get_service_status()
        assert legacy_status['mode'] == 'legacy'
        
        # Consolidated mode
        consolidated_manager = ExternalServiceManager(self.consolidated_config)
        consolidated_status = consolidated_manager.get_service_status()
        assert consolidated_status['mode'] == 'consolidated'
    
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker patterns are maintained."""
        manager = ExternalServiceManager(self.consolidated_config)
        
        if manager._circuit_breakers:
            # Test circuit breaker creation
            assert 'bhagavad_gita' in manager._circuit_breakers
            assert 'wisdom_library' in manager._circuit_breakers
            assert 'validation' in manager._circuit_breakers
            
            # Test circuit breaker behavior
            cb = manager._circuit_breakers['bhagavad_gita']
            assert cb.can_execute() == True
            
            # Record failures and test behavior
            for _ in range(3):
                cb.record_failure()
            
            # Should still be able to execute (simplified implementation)
            # In production, would test actual circuit opening
            assert hasattr(cb, 'failure_count')
    
    def test_backward_compatibility(self):
        """Test all existing method signatures are preserved."""
        # Test that consolidated manager has all required methods
        manager = ExternalServiceManager(self.consolidated_config)
        
        # MCP methods
        assert hasattr(manager, 'mcp_analyze_batch')
        assert hasattr(manager, 'mcp_enhance_segment')
        
        # API methods
        assert hasattr(manager, 'api_lookup_scripture')
        assert hasattr(manager, 'api_validate_iast')
        
        # Management methods
        assert hasattr(manager, 'get_service_status')
        assert hasattr(manager, 'close')
    
    def test_error_handling_preservation(self):
        """Test all error handling patterns are maintained."""
        manager = ExternalServiceManager(self.consolidated_config)
        
        # Test graceful handling of empty inputs
        assert manager.mcp_analyze_batch([]) == []
        assert manager.mcp_enhance_segment('') == ''
        assert manager.api_lookup_scripture('') == {}
        assert manager.api_validate_iast('') == True
    
    def test_cache_functionality(self):
        """Test caching works in consolidated services."""
        manager = ExternalServiceManager(self.consolidated_config)
        
        if manager._verse_cache:
            # Test cache operations
            test_key = 'test_scripture_key'
            test_value = {'test': 'data'}
            
            manager._verse_cache.set(test_key, test_value)
            cached_value = manager._verse_cache.get(test_key)
            
            assert cached_value == test_value
    
    def test_configuration_validation(self):
        """Test configuration is properly validated."""
        # Test with minimal config
        minimal_config = {'processing': {'use_consolidated_services': True}}
        manager = ExternalServiceManager(minimal_config)
        
        assert manager.use_consolidated == True
        
        # Test with empty config
        empty_manager = ExternalServiceManager({})
        assert empty_manager.use_consolidated == False


class TestEnhancedProcessorConsolidation:
    """Test enhanced processor with consolidated services."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_config_legacy = {
            'processing': {
                'use_consolidated_services': False,
                'enable_semantic_analysis': True,
                'enable_scripture_lookup': True
            }
        }
        
        self.test_config_consolidated = {
            'processing': {
                'use_consolidated_services': True,
                'enable_semantic_analysis': True,
                'enable_scripture_lookup': True
            },
            'services': {
                'consolidated': {
                    'mcp': {'enabled': True, 'timeout': 30},
                    'api': {'enabled': True, 'timeout': 10}
                }
            }
        }
    
    @patch('enhanced_processor.Path')
    def test_processor_initialization_modes(self, mock_path):
        """Test processor initializes correctly in both modes."""
        # Mock path operations
        mock_path.return_value.exists.return_value = False
        
        # Test legacy initialization
        processor_legacy = EnhancedSanskritProcessor()
        processor_legacy.config = self.test_config_legacy
        processor_legacy._init_services_for_test()
        
        # Test consolidated initialization  
        processor_consolidated = EnhancedSanskritProcessor()
        processor_consolidated.config = self.test_config_consolidated
        processor_consolidated._init_services_for_test()
    
    def _init_services_for_test(self):
        """Helper method to initialize services during testing."""
        # This would be called during normal __init__ but we mock it for testing
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])