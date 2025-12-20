import unittest
import sys
import os
import asyncio
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.agents.workflow_engine import (
    WorkflowEngine,
    ResearchWorkflows,
    WorkflowStatus
)

import tempfile
import shutil

class TestEndToEndWorkflows(unittest.TestCase):
    """
    Integration tests for Research Workflows.
    Executes workflows end-to-end with mocked data providers.
    """
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.engine = WorkflowEngine()
        self.engine.cache_dir = Path(self.test_dir)
        
        # Use an in-memory Redis mock if needed, or just rely on internal dict
        self.engine.redis = AsyncMock()
        self.engine.redis.get.return_value = None
        
        self.research = ResearchWorkflows(self.engine)
        
        # Common Mock Data
        self.mock_price_df = pd.DataFrame({
            'open': np.linspace(100, 200, 100),
            'high': np.linspace(105, 205, 100),
            'low': np.linspace(95, 195, 100),
            'close': np.linspace(102, 202, 100),
            'volume': np.random.rand(100) * 1000
        })

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run_async(self, coroutine):
        return asyncio.run(coroutine)

    @patch('src.microanalyst.data_loader.load_price_history')
    @patch('src.microanalyst.intelligence.confluence_calculator.ConfluenceCalculator')
    def test_price_action_deep_dive_e2e(self, MockConfCalc, MockLoadPrice):
        """Execute Price Action Deep Dive workflow end-to-end."""
        
        # 1. Setup Data Mocks
        MockLoadPrice.return_value = self.mock_price_df
        
        mock_calculator = MockConfCalc.return_value
        # Mocking ConfluenceZone objects is complex, let's mock the return list of objects
        mock_zone = MagicMock()
        mock_zone.to_dict.return_value = {'level': 150, 'score': 0.9}
        mock_calculator.calculate_confluence_zones.return_value = [mock_zone]
        
        # 2. Execute
        results = self._run_async(self.engine.execute("price_action_deep_dive"))
        
        # 3. Verify
        self.assertEqual(results['status'], WorkflowStatus.COMPLETED.value)
        self.assertIn('synthesize_analysis', results['outputs'])
        
        # Check intermediate task results (cached in execution)
        # We can't easily check internal execution state here without peeking, 
        # but success implies tasks ran.
        
        # Verify specific method implementations were called via side effects or coverage
        self.assertTrue(MockLoadPrice.called)
        self.assertTrue(mock_calculator.calculate_confluence_zones.called)

    @patch('src.microanalyst.data_loader.load_etf_flows')
    @patch('src.microanalyst.data_loader.load_price_history')
    def test_sentiment_analysis_e2e(self, MockLoadPrice, MockLoadEtf):
        """Execute Sentiment Analysis workflow end-to-end."""
        
        # 1. Setup
        MockLoadPrice.return_value = self.mock_price_df
        MockLoadEtf.return_value = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=100),
            'net_flow': np.random.randn(100) * 100
        })
        
        # 2. Execute
        results = self._run_async(self.engine.execute("sentiment_analysis"))
        
        # 3. Verify
        self.assertEqual(results['status'], WorkflowStatus.COMPLETED.value)
        self.assertIn('synthesize_sentiment', results['outputs'])
        self.assertTrue(MockLoadEtf.called)

    @patch('src.microanalyst.data_loader.load_price_history')
    def test_risk_assessment_e2e(self, MockLoadPrice):
        """Execute Risk Assessment workflow end-to-end."""
        
        MockLoadPrice.return_value = self.mock_price_df
        
        results = self._run_async(self.engine.execute("risk_assessment"))
        
        self.assertEqual(results['status'], WorkflowStatus.COMPLETED.value)
        self.assertIn('synthesize_risk_assessment', results['outputs'])

if __name__ == '__main__':
    unittest.main()
