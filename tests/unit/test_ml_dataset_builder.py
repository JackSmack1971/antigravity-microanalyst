import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adjust path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from src.microanalyst.intelligence.feature_engineering import MLFeatureEngineer
    from src.microanalyst.outputs.agent_ready import AgentDatasetBuilder
except ImportError:
    MLFeatureEngineer = None
    AgentDatasetBuilder = None

class TestMLDatasetBuilder(unittest.TestCase):
    """Blueprinting tests for ML Dataset Generation."""

    def setUp(self):
        if MLFeatureEngineer is None:
            self.skipTest("MLFeatureEngineer not yet implemented")
        self.engineer = MLFeatureEngineer()
        self.builder = AgentDatasetBuilder()

    def test_flatten_feature_vector(self):
        """Verify that nested dictionaries are flattened into a numeric row."""
        context = {
            'sentiment': {'composite_score': 0.8, 'volatility': 0.1},
            'onchain': {'whale_score': 0.5, 'mempool_congestion': 0.2},
            'risk': {'var_95': 0.05}
        }
        
        flat_vector = self.engineer.flatten_context(context)
        
        self.assertIsInstance(flat_vector, dict)
        self.assertEqual(flat_vector['sent_composite'], 0.8)
        self.assertEqual(flat_vector['onchain_whale'], 0.5)
        self.assertEqual(flat_vector['risk_var_95'], 0.05)
        
        # Ensure no nested dicts remain
        for val in flat_vector.values():
            self.assertIsInstance(val, (int, float, np.number))

    def test_build_ml_dataset_parquet_export(self):
        """Verify that build_ml_dataset returns a combined DataFrame."""
        # RSI needs at least 14 samples
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        df_price = pd.DataFrame({
            'close': np.random.randn(30).cumsum() + 50000,
            'volume': np.random.randn(30) * 1000
        }, index=dates)
        
        # Mock component data
        ml_df = self.builder.build_ml_dataset(df_price, sentiment_history={})
        
        self.assertIsInstance(ml_df, pd.DataFrame)
        self.assertFalse(ml_df.empty)
        self.assertEqual(len(ml_df), 30)
        # Should have technical features + price
        self.assertIn('tech_rsi', ml_df.columns)

    def test_handle_missing_data_gracefully(self):
        """Ensure builder doesn't crash if onchain or sentiment is missing."""
        df_price = pd.DataFrame({'close': [50000]*5}, index=pd.date_range('2023-01-01', periods=5))
        
        # Should not crash, should fill with defaults (0.0 or NaNs)
        ml_df = self.builder.build_ml_dataset(df_price, sentiment_history=None)
        self.assertIn('sent_composite', ml_df.columns)

    def test_data_leakage_protection(self):
        """Ensure context is NOT broadcasted when is_inference=False."""
        dates = pd.date_range(start='2023-01-01', periods=30)
        df_price = pd.DataFrame({'close': [50000]*30}, index=dates)
        context = {'sentiment': {'composite_score': 0.9}}
        
        # Training Mode (is_inference=False)
        ml_df = self.builder.build_ml_dataset(df_price, sentiment_history=context['sentiment'], is_inference=False)
        
        # Latest row should have data
        self.assertEqual(ml_df.iloc[-1]['sent_composite'], 0.9)
        # Previous row should be NaN or default (0.0 in my implementation for now)
        # Actually my implementation does: df_ml[feature] = val if is_inference else .loc[-1]
        self.assertTrue(pd.isna(ml_df.iloc[0]['sent_composite']) or ml_df.iloc[0]['sent_composite'] == 0.0)

if __name__ == '__main__':
    unittest.main()
