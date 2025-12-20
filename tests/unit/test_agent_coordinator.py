import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.agents.agent_coordinator import (
    AgentCoordinator,
    AgentRole,
    AgentTask
)

class TestAgentCoordinator(unittest.TestCase):
    """Comprehensive tests for AgentCoordinator."""
    
    def setUp(self):
        self.coordinator = AgentCoordinator()
        # Mock internal workflow engine to avoid real execution overhead
        self.coordinator.workflow_engine = AsyncMock() 

    def _run_async(self, coroutine):
        return asyncio.run(coroutine)

    # ========== HAPPY PATH TESTS ==========

    @patch('src.microanalyst.agents.agent_coordinator.BinanceSpotProvider')
    def test_delegate_to_module_happy_path_data_collector(self, MockBinance):
        """Test DATA_COLLECTOR role successfully fetches live data."""
        
        # Mock Binance Provider
        mock_provider = MockBinance.return_value
        mock_df = pd.DataFrame({'close': [100, 101, 102]})
        mock_provider.fetch_ohlcv.return_value = mock_df
        
        inputs = {'lookback_days': 10}
        
        result = self._run_async(
            self.coordinator._delegate_to_module(AgentRole.DATA_COLLECTOR, inputs)
        )
        
        self.assertIn('raw_price_history', result)
        self.assertFalse(pd.DataFrame(result['raw_price_history']).empty)

    def test_compute_execution_order_happy_path(self):
        """Test topologial sort of agent tasks."""
        
        # A -> B
        task_a = AgentTask(task_id="A", role=AgentRole.DATA_COLLECTOR, priority=1, inputs={}, expected_outputs=[])
        task_b = AgentTask(task_id="B", role=AgentRole.ANALYST_TECHNICAL, priority=1, inputs={'depends_on': 'A'}, expected_outputs=[])
        
        tasks = [task_b, task_a] # Wrong order
        
        ordered_stages = self.coordinator._compute_execution_order(tasks)
        
        # Expected: [[A], [B]] or similar structure depending on implementation
        # The implementation returns list of lists (stages)
        self.assertEqual(len(ordered_stages), 2)
        self.assertEqual(ordered_stages[0][0].task_id, "A")
        self.assertEqual(ordered_stages[1][0].task_id, "B")

    # ========== EDGE CASE TESTS ==========

    def test_delegate_edge_unknown_role(self):
        """Test delegation to an unknown role returns empty/error."""
        # Using a made-up role if enum allows, or just testing default branch
        with self.assertRaises(Exception): # Or specific behavior
             self._run_async(
                 self.coordinator._delegate_to_module("UNKNOWN_ROLE", {})
             )

    def test_decompose_objective_edge_empty_params(self):
        """Test decomposition with minimal parameters."""
        tasks = self.coordinator._decompose_objective("Analyze BTC", {})
        
        # Check defaults are applied
        self.assertTrue(len(tasks) > 0)
        # Should have at least Data Collector and Decision Maker
        roles = [t.role for t in tasks]
        self.assertIn(AgentRole.DATA_COLLECTOR, roles)
        self.assertIn(AgentRole.DECISION_MAKER, roles)

    # ========== ERROR SCENARIO TESTS ==========

    @patch('src.microanalyst.agents.agent_coordinator.BinanceSpotProvider')
    def test_delegate_error_fallback_simulation(self, MockBinance):
        """
        Test that failure in live fetch triggers fallback (Current Behavior)
        OR raises warning (Desired Behavior).
        """
        # Mock failure
        mock_provider = MockBinance.return_value
        mock_provider.fetch_ohlcv.side_effect = Exception("API Down")
        
        inputs = {'lookback_days': 1}
        
        # Capture logs to verify warning is issued
        with self.assertLogs(level='WARNING') as log:
            result = self._run_async(
                self.coordinator._delegate_to_module(AgentRole.DATA_COLLECTOR, inputs)
            )
            
            # Verify fallback data exists
            self.assertFalse(pd.DataFrame(result['raw_price_history']).empty)
            self.assertIn('Falling back to Simulation', log.output[0])

if __name__ == '__main__':
    unittest.main()
