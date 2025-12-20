import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.microanalyst.intelligence.performance_analyzer import OraclePerformanceAnalyzer

class TestOraclePerformanceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = OraclePerformanceAnalyzer()
        
        # Create mock actual price data
        dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
        self.actual_prices = pd.DataFrame({
            'close': [100, 105, 103, 108, 110, 108, 112, 115, 113, 118]
        }, index=dates)

        # Create mock predictions
        # Format: list of dicts with timestamp, direction, and price_target
        self.predictions = [
            {'timestamp': dates[0].isoformat(), 'direction': 'BULLISH', 'price_target': 106.0}, # Correct (Actual 105)
            {'timestamp': dates[1].isoformat(), 'direction': 'BEARISH', 'price_target': 102.0}, # Correct (Actual 103)
            {'timestamp': dates[2].isoformat(), 'direction': 'BULLISH', 'price_target': 110.0}, # Correct (Actual 108)
            {'timestamp': dates[3].isoformat(), 'direction': 'BULLISH', 'price_target': 112.0}, # Correct (Actual 110)
            {'timestamp': dates[4].isoformat(), 'direction': 'BEARISH', 'price_target': 106.0}, # Correct (Actual 108)
            {'timestamp': dates[5].isoformat(), 'direction': 'BULLISH', 'price_target': 115.0}, # Correct (Actual 112)
            {'timestamp': dates[6].isoformat(), 'direction': 'BULLISH', 'price_target': 118.0}, # Correct (Actual 115)
            {'timestamp': dates[7].isoformat(), 'direction': 'BEARISH', 'price_target': 112.0}, # Correct (Actual 113)
            {'timestamp': dates[8].isoformat(), 'direction': 'BULLISH', 'price_target': 120.0}, # Correct (Actual 118)
        ]

    def test_calculate_metrics(self):
        """Test basic accuracy and RMSE calculation."""
        metrics = self.analyzer.evaluate_predictions(self.predictions, self.actual_prices)
        
        self.assertIn('directional_accuracy', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('sample_count', metrics)
        
        # In our mock, all directions are technically correct (BULLISH when price went up next day, BEARISH when down)
        # Dates: 0->1(Up), 1->2(Down), 2->3(Up), 3->4(Up), 4->5(Down), 5->6(Up), 6->7(Up), 7->8(Down), 8->9(Up)
        # Predictions match this perfectly.
        self.assertEqual(metrics['directional_accuracy'], 1.0)
        self.assertGreater(metrics['rmse'], 0)
        self.assertEqual(metrics['sample_count'], 9)

    def test_missing_data_handling(self):
        """Test analyzer behavior with incomplete price history or predictions."""
        # Empty predictions
        metrics = self.analyzer.evaluate_predictions([], self.actual_prices)
        self.assertEqual(metrics['sample_count'], 0)
        self.assertEqual(metrics['directional_accuracy'], 0.0)

        # Mismatched timestamps
        garbage_predictions = [{'timestamp': '2000-01-01', 'direction': 'BULLISH', 'price_target': 1.0}]
        metrics = self.analyzer.evaluate_predictions(garbage_predictions, self.actual_prices)
        self.assertEqual(metrics['sample_count'], 0)

    def test_oracle_edge_calculation(self):
        """Test the 'Oracle Edge' (simulated PnL alpha)."""
        metrics = self.analyzer.evaluate_predictions(self.predictions, self.actual_prices)
        self.assertIn('oracle_edge_pct', metrics)
        # Since all were correct, edge should be positive
        self.assertGreater(metrics['oracle_edge_pct'], 0)

if __name__ == "__main__":
    unittest.main()
