#!/usr/bin/env python3
"""
Test suite for ASR mode metrics and performance optimizations
"""

import pytest
import tempfile
import os
from pathlib import Path
import time

class TestASRMetrics:
    """Test ASR mode metrics collection and performance optimizations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent.parent
        os.chdir(self.test_dir)
    
    def test_asr_processor_initialization_performance(self):
        """Test that ASR processor initializes within performance bounds."""
        from processors.asr_processor import ASRProcessor
        
        start_time = time.time()
        processor = ASRProcessor(
            lexicon_dir=Path('lexicons'),
            config_path=Path('config.yaml')
        )
        init_time = time.time() - start_time
        
        # Should initialize reasonably quickly (within 2s including full lexicon loading)
        assert init_time < 2.0, f"ASR processor initialization took {init_time:.3f}s, expected <2.0s"
        
        # Should have loaded whitelist terms
        assert len(processor.sanskrit_whitelist) > 30, f"Expected >30 whitelist terms, got {len(processor.sanskrit_whitelist)}"
        
        # Should have compiled patterns
        assert len(processor._compiled_patterns) > 30, f"Expected >30 compiled patterns, got {len(processor._compiled_patterns)}"
    
    def test_asr_metrics_collection(self):
        """Test that ASR mode collects detailed metrics."""
        from processors.asr_processor import ASRProcessor
        
        processor = ASRProcessor(
            lexicon_dir=Path('lexicons'),
            config_path=Path('config.yaml')
        )
        
        test_text = "yogabashi teaches jnana wisdom in the gita"
        context = {}
        
        processed_text, corrections = processor.process_text(test_text, context)
        
        # Verify metrics were collected
        assert 'asr_metrics' in context, "ASR metrics not found in context"
        
        metrics = context['asr_metrics']
        
        # Check core metrics
        assert 'context_detection_time' in metrics
        assert 'context_type' in metrics
        assert 'context_confidence' in metrics
        assert 'whitelist_check_time' in metrics
        assert 'whitelist_matches' in metrics
        assert 'english_protection_bypassed' in metrics
        assert 'processing_path' in metrics
        assert 'total_processing_time' in metrics
        assert 'total_corrections' in metrics
        assert 'correction_rate' in metrics
        
        # Check step breakdown metrics
        assert 'step_breakdown' in metrics
        step_breakdown = metrics['step_breakdown']
        
        assert 'case_corrections' in step_breakdown
        assert 'systematic_corrections' in step_breakdown
        assert 'compound_corrections' in step_breakdown
        assert 'base_corrections' in step_breakdown
        assert 'prayer_corrections' in step_breakdown
        assert 'external_corrections' in step_breakdown
        assert 'step_times' in step_breakdown
        assert 'total_step_time' in step_breakdown
        
        # Verify timing metrics are reasonable
        assert metrics['total_processing_time'] > 0
        assert metrics['context_detection_time'] >= 0
        assert metrics['whitelist_check_time'] >= 0
        
        # Verify corrections were made
        assert corrections > 0, f"Expected corrections but got {corrections}"
        assert metrics['total_corrections'] == corrections
        
        # Verify correction rate is calculated
        assert metrics['correction_rate'] > 0
    
    def test_asr_whitelist_performance(self):
        """Test that whitelist matching performs within acceptable bounds."""
        from processors.asr_processor import ASRProcessor
        
        processor = ASRProcessor(
            lexicon_dir=Path('lexicons'),
            config_path=Path('config.yaml')
        )
        
        # Create test text with multiple Sanskrit terms
        test_text = "yogabashi and shivashistha discuss jnana and dharma while studying the gita"
        context = {}
        
        start_time = time.time()
        processed_text, corrections = processor.process_text(test_text, context)
        processing_time = time.time() - start_time
        
        # Should process reasonably quickly (within 500ms for this short text)
        assert processing_time < 0.5, f"Processing took {processing_time:.3f}s, expected <0.5s"
        
        # Should find whitelist matches
        metrics = context['asr_metrics']
        assert metrics['whitelist_matches'] > 0, "Expected whitelist matches but found none"
        
        # Whitelist check should be fast
        assert metrics['whitelist_check_time'] < 0.05, f"Whitelist check took {metrics['whitelist_check_time']:.3f}s, expected <0.05s"
    
    def test_asr_step_timing_breakdown(self):
        """Test that step timing breakdown provides useful insights."""
        from processors.asr_processor import ASRProcessor
        
        processor = ASRProcessor(
            lexicon_dir=Path('lexicons'),
            config_path=Path('config.yaml')
        )
        
        test_text = "the yogabashi contains jnana about dharma and karma"
        context = {}
        
        processed_text, corrections = processor.process_text(test_text, context)
        
        metrics = context['asr_metrics']
        step_breakdown = metrics['step_breakdown']
        step_times = step_breakdown['step_times']
        
        # Verify all processing steps have timing data
        expected_steps = [
            'case_insensitive_matching',
            'systematic_matching', 
            'compound_matching',
            'base_lexicon',
            'prayer_recognition',
            'external_services'
        ]
        
        for step in expected_steps:
            assert step in step_times, f"Missing timing data for step: {step}"
            assert step_times[step] >= 0, f"Invalid timing for step {step}: {step_times[step]}"
        
        # Total step time should approximately equal sum of individual steps
        total_steps_sum = sum(step_times.values())
        recorded_total = step_breakdown['total_step_time']
        
        assert abs(total_steps_sum - recorded_total) < 0.001, f"Step time sum mismatch: {total_steps_sum:.3f} vs {recorded_total:.3f}"
    
    def test_asr_correction_type_breakdown(self):
        """Test that correction types are properly tracked."""
        from processors.asr_processor import ASRProcessor
        
        processor = ASRProcessor(
            lexicon_dir=Path('lexicons'),
            config_path=Path('config.yaml')
        )
        
        # Text designed to trigger multiple correction types
        test_text = "yogabashi teaches about jnana and DHARMA in the Gita"
        context = {}
        
        processed_text, corrections = processor.process_text(test_text, context)
        
        metrics = context['asr_metrics']
        step_breakdown = metrics['step_breakdown']
        
        # Should have some corrections
        total_step_corrections = (
            step_breakdown['case_corrections'] +
            step_breakdown['systematic_corrections'] +
            step_breakdown['compound_corrections'] +
            step_breakdown['base_corrections'] +
            step_breakdown['prayer_corrections'] +
            step_breakdown['external_corrections']
        )
        
        # Total should match reported corrections
        assert total_step_corrections == corrections, f"Correction count mismatch: {total_step_corrections} vs {corrections}"
        
        # Should have some corrections (may be case, systematic, or base corrections)
        assert corrections > 0, "Expected some corrections to be made"
        
        # Verify at least one correction type was used
        correction_types_used = sum([
            1 for count in [
                step_breakdown['case_corrections'],
                step_breakdown['systematic_corrections'], 
                step_breakdown['compound_corrections'],
                step_breakdown['base_corrections'],
                step_breakdown['prayer_corrections'],
                step_breakdown['external_corrections']
            ] if count > 0
        ])
        assert correction_types_used > 0, "Expected at least one correction type to be used"
    
    def test_asr_context_override_metrics(self):
        """Test that English protection bypass is properly tracked."""
        from processors.asr_processor import ASRProcessor
        
        processor = ASRProcessor(
            lexicon_dir=Path('lexicons'),
            config_path=Path('config.yaml')
        )
        
        # English-dominant text with Sanskrit terms
        test_text = "In English class we study yogabashi philosophy and discuss jnana"
        context = {}
        
        processed_text, corrections = processor.process_text(test_text, context)
        
        metrics = context['asr_metrics']
        
        # Should detect English context initially
        # But override due to Sanskrit whitelist terms
        assert metrics['whitelist_matches'] > 0, "Expected whitelist matches"
        assert metrics['english_protection_bypassed'], "Expected English protection to be bypassed"
        
        # Should process as Sanskrit due to override
        assert metrics['processing_path'] in ['sanskrit_full', 'mixed_aggressive'], f"Unexpected processing path: {metrics['processing_path']}"
        
        # Should make corrections despite English context
        assert corrections > 0, "Expected corrections despite English context"

if __name__ == '__main__':
    pytest.main([__file__])