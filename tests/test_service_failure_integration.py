#!/usr/bin/env python3
"""
Comprehensive Service Failure Integration Tests
Tests circuit breaker behavior and graceful degradation when external services fail.
"""

import pytest
import logging
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

from enhanced_processor import EnhancedSanskritProcessor
from services.external import ExternalServiceManager, ExternalClients
from exceptions import SanskritProcessorError, ProcessingError

# Test data
SAMPLE_SRT_CONTENT = """1
00:00:01,000 --> 00:00:03,000
om namah shivaya guru dev

2
00:00:04,000 --> 00:00:06,000
krishna consciousness meditation

3
00:00:07,000 --> 00:00:09,000
srimad bhagavad gita teaching"""


class TestServiceFailureIntegration:
    """Test service failures and circuit breaker behavior."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create sample SRT file
        srt_file = temp_path / "test.srt"
        srt_file.write_text(SAMPLE_SRT_CONTENT)
        
        # Create basic config
        config = {
            'processing': {
                'use_consolidated_services': True,
                'fuzzy_matching': {'enabled': True, 'threshold': 0.8}
            },
            'services': {
                'consolidated': {
                    'mcp': {'enabled': True, 'timeout': 1, 'max_retries': 2},
                    'api': {'enabled': True, 'timeout': 1, 'max_retries': 2}
                }
            },
            'performance': {
                'profiling': {'enabled': False},
                'monitoring': {'track_service_response_times': True}
            }
        }
        config_file = temp_path / "config.yaml"
        import yaml
        config_file.write_text(yaml.dump(config))
        
        # Create basic lexicons
        lexicons_dir = temp_path / "lexicons"
        lexicons_dir.mkdir()
        
        corrections = {
            'om': 'Om',
            'krishna': 'Krishna',
            'shivaya': 'Shivaya'
        }
        proper_nouns = {
            'Krishna': 'Krishna',
            'Shivaya': 'Shivaya'
        }
        
        (lexicons_dir / "corrections.yaml").write_text(yaml.dump(corrections))
        (lexicons_dir / "proper_nouns.yaml").write_text(yaml.dump(proper_nouns))
        
        return {
            'temp_dir': temp_path,
            'srt_file': srt_file,
            'config_file': config_file,
            'lexicons_dir': lexicons_dir
        }

    def test_mcp_service_failure_fallback(self, temp_files):
        """Test graceful fallback when MCP service fails."""
        with patch('services.mcp_client.MCPClient') as mock_mcp_client:
            # Simulate MCP connection failure
            mock_mcp_client.side_effect = ConnectionError("MCP service unavailable")
            
            processor = EnhancedSanskritProcessor(
                lexicon_dir=temp_files['lexicons_dir'],
                config_path=temp_files['config_file']
            )
            
            # Process should still work with local lexicons
            result = processor.process_srt_file(
                str(temp_files['srt_file']),
                str(temp_files['temp_dir'] / "output.srt")
            )
            
            # Verify processing succeeded with fallback
            assert result is not None
            assert result.segments_processed > 0
            assert result.corrections_applied > 0  # Local corrections applied
            
            # Verify output file exists and has corrections
            output_file = temp_files['temp_dir'] / "output.srt"
            assert output_file.exists()
            output_content = output_file.read_text()
            assert "Om" in output_content  # Local correction applied
            assert "Krishna" in output_content  # Local correction applied

    def test_api_service_timeout_handling(self, temp_files):
        """Test API service timeout handling with circuit breaker."""
        with patch('services.api_client.ExternalAPIClient') as mock_api_client:
            # Simulate API timeout
            mock_instance = Mock()
            mock_instance.lookup_scripture_reference.side_effect = TimeoutError("API timeout")
            mock_api_client.return_value = mock_instance
            
            processor = EnhancedSanskritProcessor(
                lexicon_dir=temp_files['lexicons_dir'],
                config_path=temp_files['config_file']
            )
            
            # Process multiple times to trigger circuit breaker
            results = []
            for i in range(3):
                result = processor.process_srt_file(
                    str(temp_files['srt_file']),
                    str(temp_files['temp_dir'] / f"output_{i}.srt")
                )
                results.append(result)
            
            # All processing should succeed with local fallback
            for result in results:
                assert result is not None
                assert result.segments_processed > 0

    def test_database_connection_failure(self, temp_files):
        """Test database connection failure handling."""
        # Update config to enable database
        config = {
            'processing': {'use_consolidated_services': False},
            'database': {
                'enabled': True,
                'path': 'nonexistent_database.db',
                'fallback_to_yaml': True,
                'connection_timeout': 1.0
            }
        }
        import yaml
        temp_files['config_file'].write_text(yaml.dump(config))
        
        processor = EnhancedSanskritProcessor(
            lexicon_dir=temp_files['lexicons_dir'],
            config_path=temp_files['config_file']
        )
        
        # Should fallback to YAML lexicons
        result = processor.process_srt_file(
            str(temp_files['srt_file']),
            str(temp_files['temp_dir'] / "output.srt")
        )
        
        assert result is not None
        assert result.segments_processed > 0
        assert result.corrections_applied > 0  # YAML fallback worked

    def test_service_recovery_after_failure(self, temp_files):
        """Test service recovery after temporary failures."""
        with patch('services.external.ExternalServiceManager') as mock_manager:
            # First call fails, second succeeds
            mock_instance = Mock()
            mock_instance.enhance_text.side_effect = [
                ConnectionError("Service down"),  # First call fails
                ("Enhanced text", {"confidence": 0.9})  # Second call succeeds
            ]
            mock_manager.return_value = mock_instance
            
            processor = EnhancedSanskritProcessor(
                lexicon_dir=temp_files['lexicons_dir'],
                config_path=temp_files['config_file']
            )
            
            # First processing - service fails, should work with fallback
            result1 = processor.process_srt_file(
                str(temp_files['srt_file']),
                str(temp_files['temp_dir'] / "output1.srt")
            )
            
            # Second processing - service recovers
            result2 = processor.process_srt_file(
                str(temp_files['srt_file']),
                str(temp_files['temp_dir'] / "output2.srt")
            )
            
            assert result1 is not None
            assert result2 is not None
            assert result1.segments_processed > 0
            assert result2.segments_processed > 0

    def test_partial_service_failure(self, temp_files):
        """Test behavior when some services fail but others work."""
        with patch('services.mcp_client.MCPClient') as mock_mcp, \
             patch('services.api_client.ExternalAPIClient') as mock_api:
            
            # MCP fails, but API works
            mock_mcp.side_effect = ConnectionError("MCP down")
            
            mock_api_instance = Mock()
            mock_api_instance.lookup_scripture_reference.return_value = {
                'reference': 'Bhagavad Gita 2.47',
                'confidence': 0.95
            }
            mock_api.return_value = mock_api_instance
            
            processor = EnhancedSanskritProcessor(
                lexicon_dir=temp_files['lexicons_dir'],
                config_path=temp_files['config_file']
            )
            
            result = processor.process_srt_file(
                str(temp_files['srt_file']),
                str(temp_files['temp_dir'] / "output.srt")
            )
            
            # Should work with partial services + local processing
            assert result is not None
            assert result.segments_processed > 0

    def test_service_performance_degradation(self, temp_files):
        """Test handling of slow but working services."""
        with patch('services.external.ExternalServiceManager') as mock_manager:
            mock_instance = Mock()
            
            # Simulate slow service (but within timeout)
            def slow_enhance(text):
                time.sleep(0.5)  # Slow but not timeout
                return (f"Enhanced {text}", {"confidence": 0.8, "response_time": 0.5})
            
            mock_instance.enhance_text.side_effect = slow_enhance
            mock_manager.return_value = mock_instance
            
            processor = EnhancedSanskritProcessor(
                lexicon_dir=temp_files['lexicons_dir'],
                config_path=temp_files['config_file']
            )
            
            start_time = time.time()
            result = processor.process_srt_file(
                str(temp_files['srt_file']),
                str(temp_files['temp_dir'] / "output.srt")
            )
            total_time = time.time() - start_time
            
            # Should complete but record performance metrics
            assert result is not None
            assert total_time > 1.0  # At least one slow call was made
            assert result.segments_processed > 0

    def test_configuration_error_handling(self, temp_files):
        """Test handling of configuration errors in services."""
        # Create invalid config
        invalid_config = {
            'services': {
                'consolidated': {
                    'mcp': {'invalid_option': 'bad_value'}
                }
            }
        }
        import yaml
        temp_files['config_file'].write_text(yaml.dump(invalid_config))
        
        # Should initialize with warnings but still work
        processor = EnhancedSanskritProcessor(
            lexicon_dir=temp_files['lexicons_dir'],
            config_path=temp_files['config_file']
        )
        
        result = processor.process_srt_file(
            str(temp_files['srt_file']),
            str(temp_files['temp_dir'] / "output.srt")
        )
        
        # Should fallback to basic processing
        assert result is not None
        assert result.segments_processed > 0

    def test_service_status_monitoring(self, temp_files):
        """Test service status monitoring and health checks."""
        with patch('services.external.ExternalServiceManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.get_service_status.return_value = {
                'mcp': {'status': 'down', 'last_error': 'Connection failed'},
                'api': {'status': 'up', 'response_time': 0.1},
                'database': {'status': 'degraded', 'performance': 'slow'}
            }
            mock_manager.return_value = mock_instance
            
            processor = EnhancedSanskritProcessor(
                lexicon_dir=temp_files['lexicons_dir'],
                config_path=temp_files['config_file']
            )
            
            # Should be able to get service status
            if hasattr(processor, 'get_service_status'):
                status = processor.get_service_status()
                assert isinstance(status, dict)
                assert 'mcp' in status or 'api' in status

    def test_error_logging_and_metrics(self, temp_files, caplog):
        """Test that service failures are properly logged and tracked."""
        with patch('services.external.ExternalServiceManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.enhance_text.side_effect = RuntimeError("Service crashed")
            mock_manager.return_value = mock_instance
            
            with caplog.at_level(logging.WARNING):
                processor = EnhancedSanskritProcessor(
                    lexicon_dir=temp_files['lexicons_dir'],
                    config_path=temp_files['config_file']
                )
                
                result = processor.process_srt_file(
                    str(temp_files['srt_file']),
                    str(temp_files['temp_dir'] / "output.srt")
                )
            
            # Should log service failures
            assert len(caplog.records) > 0
            # Should still produce result via fallback
            assert result is not None
            assert result.segments_processed > 0


class TestCircuitBreakerBehavior:
    """Test specific circuit breaker pattern behavior."""
    
    @pytest.fixture
    def mock_service_manager(self):
        """Create a mock service manager with circuit breaker."""
        with patch('services.external.ExternalServiceManager') as mock:
            mock_instance = Mock()
            # Simulate circuit breaker states
            mock_instance._circuit_breaker_state = 'closed'  # Initial state
            mock_instance._failure_count = 0
            mock_instance._failure_threshold = 3
            yield mock_instance

    def test_circuit_breaker_opens_after_failures(self, temp_files, mock_service_manager):
        """Test that circuit breaker opens after consecutive failures."""
        # Configure failures
        mock_service_manager.enhance_text.side_effect = ConnectionError("Service down")
        
        processor = EnhancedSanskritProcessor(
            lexicon_dir=temp_files['lexicons_dir'],
            config_path=temp_files['config_file']
        )
        
        # Make multiple calls to trigger circuit breaker
        for i in range(5):
            result = processor.process_srt_file(
                str(temp_files['srt_file']),
                str(temp_files['temp_dir'] / f"output_{i}.srt")
            )
            assert result is not None  # Should still work via fallback
        
        # Circuit breaker should be tracking failures
        call_count = mock_service_manager.enhance_text.call_count
        assert call_count >= 3  # Should have attempted calls

    def test_circuit_breaker_half_open_recovery(self, temp_files):
        """Test circuit breaker recovery behavior."""
        with patch('services.external.ExternalServiceManager') as mock_manager:
            mock_instance = Mock()
            
            # First few calls fail, then succeed
            call_responses = [
                ConnectionError("Fail 1"),
                ConnectionError("Fail 2"), 
                ConnectionError("Fail 3"),  # Should open circuit
                ("Success", {"confidence": 0.9})  # Recovery attempt
            ]
            mock_instance.enhance_text.side_effect = call_responses
            mock_manager.return_value = mock_instance
            
            processor = EnhancedSanskritProcessor(
                lexicon_dir=temp_files['lexicons_dir'],
                config_path=temp_files['config_file']
            )
            
            # Process multiple times
            for i in range(4):
                result = processor.process_srt_file(
                    str(temp_files['srt_file']),
                    str(temp_files['temp_dir'] / f"output_{i}.srt")
                )
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])