import unittest
import sys
import os
import asyncio
import pandas as pd
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.agents.agent_coordinator import (
    AgentCoordinator,
    AgentRole,
    AgentTask
)

class TestAgentRoles(unittest.TestCase):
    """Test suite for specific Agent Role execution logic."""
    
    def setUp(self):
        self.coordinator = AgentCoordinator()
        self.coordinator.workflow_engine = AsyncMock() 
        self.coordinator.results = {}

    def _run_async(self, coroutine):
        return asyncio.run(coroutine)

    @patch('src.microanalyst.agents.agent_coordinator.SignalLibrary')
    def test_role_analyst_technical(self, MockSignalLib):
        """Test ANALYST_TECHNICAL role logic."""
        mock_lib = MockSignalLib.return_value
        mock_lib.detect_all_signals.return_value = [{'signal': 'buy'}]
        
        # Input with price history
        inputs = {'raw_price_history': pd.DataFrame({
            'open': [1, 2, 3],
            'high': [2, 3, 4],
            'low': [0.5, 1.5, 2.5],
            'close': [1, 2, 3],
            'volume': [100, 200, 300]
        })}
        
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.ANALYST_TECHNICAL, inputs)
        )
        
        self.assertIn('technical_signals', result)
        self.assertEqual(result['technical_signals'], [{'signal': 'buy'}])
        self.assertIn('key_levels', result)

    @patch('src.microanalyst.agents.agent_coordinator.FreeSentimentAggregator')
    def test_role_analyst_sentiment(self, MockSentAgg):
        """Test ANALYST_SENTIMENT role logic."""
        mock_agg = MockSentAgg.return_value
        mock_agg.aggregate_sentiment.return_value = {'score': 0.8, 'interpretation': 'Bullish'}
        
        # Test valid inputs (passed from collector)
        inputs = {'sentiment': {'score': 0.5}}
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.ANALYST_SENTIMENT, inputs)
        )
        self.assertEqual(result['sentiment_indicators'], {'score': 0.5})

        # Test empty inputs (fetch fresh)
        inputs = {}
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.ANALYST_SENTIMENT, inputs)
        )
        self.assertEqual(result['sentiment_indicators']['interpretation'], 'Bullish')

    @patch('src.microanalyst.agents.agent_coordinator.RiskManager')
    def test_role_analyst_risk(self, MockRiskMgr):
        """Test ANALYST_RISK role logic."""
        mock_rm = MockRiskMgr.return_value
        mock_rm.optimal_position_sizing.return_value = {'pct_of_equity': 0.05}
        mock_rm.calculate_value_at_risk.return_value = {'var': 100}

        inputs = {'raw_price_history': {'close': [1, 2, 3]}}
        
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.ANALYST_RISK, inputs)
        )
        
        self.assertEqual(result['recommended_sizing_pct'], 0.05)
        self.assertEqual(result['risk_assessment']['var'], 100)

    @patch('src.microanalyst.agents.agent_coordinator.PromptEngine')
    def test_role_synthesizer(self, MockPromptEngine):
        """Test SYNTHESIZER role logic."""
        mock_engine = MockPromptEngine.return_value
        mock_engine.construct_synthesizer_prompt.return_value = "Prompt"
        mock_engine.detect_regime.return_value = "BULL_TREND"
        
        inputs = {'collect_data': {'price': {}}} # Simulate accumulated context
        
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.SYNTHESIZER, inputs)
        )
        
        self.assertIn('market_context', result)
        self.assertEqual(result['market_context']['regime_detected'], "BULL_TREND")
        self.assertEqual(result['market_context']['bias'], "BULLISH")

    @patch('src.microanalyst.agents.agent_coordinator.run_adversarial_debate')
    @patch('src.microanalyst.agents.agent_coordinator.EpisodicMemory')
    def test_role_decision_maker(self, MockMemory, MockDebate):
        """Test DECISION_MAKER role logic."""
        MockDebate.return_value = {'decision': 'BUY'}
        mock_mem = MockMemory.return_value
        mock_mem.store_decision.return_value = "mem_123"
        
        inputs = {'collect_data': {}}
        
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.DECISION_MAKER, inputs)
        )
        
        self.assertEqual(result['decision'], 'BUY')
        self.assertEqual(result['memory_id'], "mem_123")

if __name__ == '__main__':
    unittest.main()
