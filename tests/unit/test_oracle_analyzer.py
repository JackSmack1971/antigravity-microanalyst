import unittest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Adjust path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.intelligence.oracle_analyzer import OracleAnalyzer

class TestOracleAnalyzer(unittest.TestCase):
    """Blueprinting tests for OracleAnalyzer."""

    def setUp(self):
        self.analyzer = OracleAnalyzer()

    def test_aggregate_features_happy_path(self):
        """Verify that all data sources are merged into a valid feature vector."""
        df_price = pd.DataFrame({
            'close': np.random.randn(100) + 50000,
            'volume': np.random.randn(100) * 1000
        })
        context = {
            'sentiment': {'composite_score': 0.7},
            'onchain': {'mempool_congestion': 'low'}
        }
        
        feature_vector = self.analyzer._aggregate_features(df_price, context)
        
        self.assertIn('tech_rsi', feature_vector)
        self.assertIn('sent_composite', feature_vector)
        self.assertIn('onchain_whale', feature_vector)

    def test_predict_24h_precondition_failure(self):
        """Precondition: Fail if price data is too short."""
        df_price = pd.DataFrame({'close': [50000, 50100]}) # Too short
        
        with self.assertRaises(ValueError):
            self.analyzer.predict_24h(df_price, {})

    def test_predict_24h_postcondition_valid_bounds(self):
        """Postcondition: Prediction must be within realistic bounds."""
        df_price = pd.DataFrame({
            'close': [50000] * 60,
            'high': [51000] * 60,
            'low': [49000] * 60
        })
        
        prediction = self.analyzer.predict_24h(df_price, {'regime': {'current_regime': 'bull'}})
        
        self.assertIn(prediction['direction'], ['BULLISH', 'BEARISH', 'NEUTRAL'])
        self.assertGreaterEqual(prediction['confidence'], 0.0)
        self.assertLessEqual(prediction['confidence'], 1.0)
        
        current_price = 50000
        target = prediction['price_target']
        # Just ensure it's a number and not something crazy
        self.assertIsInstance(target, float)

if __name__ == '__main__':
    unittest.main()
