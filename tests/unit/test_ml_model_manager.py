import unittest
import pandas as pd
import numpy as np
import os
import shutil
from unittest.mock import MagicMock
from src.microanalyst.intelligence.ml_model_manager import MLModelManager

class TestMLModelManager(unittest.TestCase):
    def setUp(self):
        self.model_dir = "test_models"
        self.manager = MLModelManager(model_dir=self.model_dir)
        
        # Create synthetic data for training
        # Target = 2*Feature1 - Feature2 + noise
        n_samples = 100
        self.train_df = pd.DataFrame({
            "tech_rsi": np.random.rand(n_samples),
            "tech_sma_dist": np.random.rand(n_samples),
            "sent_composite": np.random.rand(n_samples),
            "target_return_24h": np.random.randn(n_samples)
        })
        # Inject linear relationship
        self.train_df["target_return_24h"] = (
            2 * self.train_df["tech_rsi"] - 1.5 * self.train_df["sent_composite"] + np.random.normal(0, 0.1, n_samples)
        )

    def tearDown(self):
        if os.path.exists(self.model_dir):
            shutil.rmtree(self.model_dir)

    def test_train_and_predict(self):
        """Test successful training and basic inference."""
        metrics = self.manager.train(self.train_df, target="target_return_24h")
        self.assertIn("rmse", metrics)
        self.assertLess(metrics["rmse"], 1.0) # Should fit reasonably well
        
        # Test prediction
        sample_features = {
            "tech_rsi": 0.8,
            "tech_sma_dist": 0.05,
            "sent_composite": 0.2
        }
        prediction, confidence = self.manager.predict(sample_features)
        
        self.assertIsInstance(prediction, float)
        self.assertIsInstance(confidence, float)
        self.assertTrue(0 <= confidence <= 1.0)
        # Directional pred for linear: 2*0.8 - 1.5*0.2 = 1.6 - 0.3 = 1.3 (Positive)
        self.assertGreater(prediction, 0)

    def test_persistence(self):
        """Test saving and loading the model."""
        self.manager.train(self.train_df, target="target_return_24h")
        model_path = self.manager.save_model("test_v1")
        self.assertTrue(os.path.exists(model_path))
        
        # New manager instance
        new_manager = MLModelManager(model_dir=self.model_dir)
        new_manager.load_model("test_v1")
        
        sample_features = {"tech_rsi": 0.5, "tech_sma_dist": 0.0, "sent_composite": 0.5}
        pred1, _ = self.manager.predict(sample_features)
        pred2, _ = new_manager.predict(sample_features)
        
        self.assertEqual(pred1, pred2)

    def test_missing_features_handling(self):
        """Test how the model handles missing keys during inference."""
        self.manager.train(self.train_df, target="target_return_24h")
        
        # Prediction with missing key
        incomplete_features = {"tech_rsi": 0.5} 
        # Should not crash; should use defaults or handle gracefully
        prediction, _ = self.manager.predict(incomplete_features)
        self.assertIsNotNone(prediction)

    def test_insufficient_data(self):
        """Test training with too few samples."""
        small_df = self.train_df.iloc[:5]
        with self.assertRaises(ValueError):
            self.manager.train(small_df, target="target_return_24h")

if __name__ == "__main__":
    unittest.main()
