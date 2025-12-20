import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Adjust path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.agents.agent_coordinator import AgentCoordinator, AgentRole

class TestOracleIntegration(unittest.TestCase):
    """Integration level tests for the Oracle role."""

    def setUp(self):
        self.coordinator = AgentCoordinator()
        self.coordinator.workflow_engine = AsyncMock()

    def _run_async(self, coroutine):
        return asyncio.run(coroutine)

    @patch('src.microanalyst.agents.agent_coordinator.OracleAnalyzer')
    def test_oracle_delegation_logic(self, MockOracle):
        """Verify coordinator correctly delegates to OracleAnalyzer."""
        mock_instance = MockOracle.return_value
        mock_instance.predict_24h.return_value = {
            'direction': 'BULLISH',
            'confidence': 0.85,
            'price_target': 52000.0
        }
        
        # Manually set the analyzer to use our mock
        self.coordinator.oracle_analyzer = mock_instance
        
        inputs = {
            'raw_price_history': {'close': [50000] * 60},
            'context_metadata': {'sentiment': {'composite_score': 0.8}}
        }
        
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.PREDICTION_ORACLE, inputs)
        )
        
        self.assertEqual(result['direction'], 'BULLISH')
        self.assertEqual(result['price_target'], 52000.0)
        mock_instance.predict_24h.assert_called()

    def test_oracle_registration(self):
        """Verify Oracle is registered in the capability map."""
        self.assertIn('prediction_oracle', self.coordinator.agents)
        cap = self.coordinator.agents['prediction_oracle']
        self.assertEqual(cap.role, AgentRole.PREDICTION_ORACLE)
        self.assertIn(AgentRole.ANALYST_SENTIMENT, cap.dependencies)

if __name__ == '__main__':
    unittest.main()
