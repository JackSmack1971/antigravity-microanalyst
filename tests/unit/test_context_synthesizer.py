import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.intelligence.context_synthesizer import (
    ContextSynthesizer, 
    MarketContext
)

class TestContextSynthesizer(unittest.TestCase):
    """Comprehensive tests for ContextSynthesizer."""
    
    def setUp(self):
        # Mock dependencies in __init__
        with patch('src.microanalyst.intelligence.context_synthesizer.RegimeAnalyzer') as MockRegime, \
             patch('src.microanalyst.intelligence.context_synthesizer.SignalAnalyzer') as MockSignal, \
             patch('src.microanalyst.intelligence.context_synthesizer.RiskAnalyzer') as MockRisk, \
             patch('src.microanalyst.intelligence.context_synthesizer.OpportunityDetector') as MockOpp, \
             patch('src.microanalyst.intelligence.context_synthesizer.NarrativeGenerator') as MockNarrative, \
             patch('src.microanalyst.intelligence.context_synthesizer.ActionPrioritizer') as MockAction, \
             patch('src.microanalyst.intelligence.context_synthesizer.AgentReasoningAdapter'), \
             patch('src.microanalyst.intelligence.context_synthesizer.MacroDataProvider'), \
             patch('src.microanalyst.intelligence.context_synthesizer.CorrelationAnalyzer'), \
             patch('src.microanalyst.intelligence.context_synthesizer.SignalLibrary'), \
             patch('src.microanalyst.intelligence.context_synthesizer.Environment'): # Jinja env
             
            self.synthesizer = ContextSynthesizer()
            
            # Setup mock instances for use in tests
            self.synthesizer.regime_analyzer = MockRegime.return_value
            self.synthesizer.signal_analyzer = MockSignal.return_value
            self.synthesizer.risk_analyzer = MockRisk.return_value
            self.synthesizer.opportunity_detector = MockOpp.return_value
            self.synthesizer.narrative_generator = MockNarrative.return_value
            self.synthesizer.action_prioritizer = MockAction.return_value
            self.synthesizer.macro_provider = Mock()
            self.synthesizer.correlation_analyzer = Mock()
            self.synthesizer.signal_lib = Mock()
            
            # Mock Data Loading
            self.synthesizer._load_price_data = Mock()
            self.synthesizer._load_flow_data = Mock()

    # ========== HAPPY PATH TESTS ==========

    def test_synthesize_context_happy_path(self):
        """Test full context synthesis with valid mocked data."""
        
        # 1. Arrange Mock Data
        mock_price = pd.DataFrame({
            'date': [datetime.now()], 
            'close': [50000.0],
            'high': [51000.0],
            'low': [49000.0]
        })
        self.synthesizer._load_price_data.return_value = mock_price
        self.synthesizer._load_flow_data.return_value = pd.DataFrame({'date': [datetime.now()], 'flow_usd': [1000]})
        self.synthesizer.signal_lib.find_support_resistance.return_value = {} # Ensure it returns a dict for assignment
        
        # Mock Analyzer Outputs
        self.synthesizer.regime_analyzer.detect_regime.return_value = {
            'current_regime': 'bull', 'regime_confidence': 0.8
        }
        self.synthesizer.signal_analyzer.detect_all_signals.return_value = []
        self.synthesizer.risk_analyzer.assess_risks.return_value = {'overall_risk_score': 0.3}
        self.synthesizer.opportunity_detector.identify_opportunities.return_value = []
        
        # 2. Act
        context = self.synthesizer.synthesize_context(lookback_days=7)
        
        # 3. Assert
        self.assertIsInstance(context, MarketContext)
        self.assertGreater(context.confidence_score, 0.5) 
        self.assertEqual(context.regime['current_regime'], 'bull')

    def test_generate_report_happy_path_markdown(self):
        """Test generating a markdown report using Jinja template."""
        
        # Mock Context
        context = MagicMock(spec=MarketContext)
        context.regime = {'current_regime': 'bull'}
        context.signals = []
        context.risks = []
        context.opportunities = []
        context.key_levels = {}
        context.sentiment_indicators = {}
        context.historical_comparison = {}
        context.confidence_score = 0.8
        context.is_simulation = False
        context.timestamp = datetime.now() # Required for _build_template_context
        
        # Mock Jinja Template
        mock_template = Mock()
        mock_template.render.return_value = "# Report Content"
        self.synthesizer.jinja_env.get_template = Mock(return_value=mock_template)
        
        # Mock Delegates Results (since _build_template_context calls them)
        self.synthesizer.narrative_generator.generate_executive_summary.return_value = "Exec Summary"
        self.synthesizer.action_prioritizer.prioritize_actions.return_value = []
        
        report = self.synthesizer.generate_report(context, output_format="markdown")
        
        self.assertEqual(report, "# Report Content")
        self.synthesizer.jinja_env.get_template.assert_called_with('bull_regime.j2')

        # Verify Delegation in _build_template_context
        self.synthesizer.narrative_generator.generate_executive_summary.assert_called()
        self.synthesizer.action_prioritizer.prioritize_actions.assert_called()

    # ========== EDGE CASE TESTS ==========

    def test_generate_report_regime_coverage(self):
        """Test report generation for multiple regimes to cover template selection."""
        regimes = ['bear', 'accumulation', 'volatile']
        
        for r in regimes:
            context = MagicMock(spec=MarketContext)
            context.regime = {'current_regime': r}
            context.timestamp = datetime.now()
            context.signals = []
            context.risks = []
            context.opportunities = []
            context.key_levels = {}
            context.sentiment_indicators = {}
            context.historical_comparison = {}
            context.confidence_score = 0.5
            
            # Setup mocks
            self.synthesizer.jinja_env.get_template = Mock(return_value=Mock(render=Mock(return_value="Report")))
            self.synthesizer.narrative_generator.generate_executive_summary.return_value = ""
            self.synthesizer.action_prioritizer.prioritize_actions.return_value = []
            
            self.synthesizer.generate_report(context, output_format="markdown")
            
            # Verify get_template called with correct file
            expected_tmpl = 'bear_regime.j2' if r == 'bear' else ('sideways_regime.j2' if r == 'accumulation' else 'volatile_regime.j2')
            self.synthesizer.jinja_env.get_template.assert_called_with(expected_tmpl)

    def test_format_large_number_edge_cases(self):
        """Test formatting utility."""
        self.assertEqual(self.synthesizer._format_large_number(None), "N/A")
        self.assertEqual(self.synthesizer._format_large_number(500), "$500.00")
        self.assertEqual(self.synthesizer._format_large_number(1500), "$1.50K")
        self.assertEqual(self.synthesizer._format_large_number(2_500_000), "$2.50M")

    # ========== ERROR SCENARIO TESTS ==========

    def test_generate_report_fallback_template_missing(self):
        """Test fallback to simple report if Jinja template is missing."""
        context = MagicMock(spec=MarketContext)
        context.regime = {'current_regime': 'bull'}
        
        # Simulate TemplateNotFound
        self.synthesizer.jinja_env.get_template.side_effect = Exception("Template Not Found")
        
        # Mock simple generator
        self.synthesizer._generate_simple_markdown = Mock(return_value="Simple Report")
        
        report = self.synthesizer.generate_report(context)
        
        self.assertEqual(report, "Simple Report")



if __name__ == '__main__':
    unittest.main()
