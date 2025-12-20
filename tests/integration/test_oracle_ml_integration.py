import unittest
import pandas as pd
import numpy as np
import os
import shutil
from src.microanalyst.intelligence.oracle_analyzer import OracleAnalyzer
from src.microanalyst.intelligence.ml_model_manager import MLModelManager

class TestOracleMLIntegration(unittest.TestCase):
    def setUp(self):
        self.model_dir = "test_models_integration"
        self.oracle = OracleAnalyzer()
        self.oracle.model_manager.model_dir = self.model_dir
        
        # 1. Create synthetic data and train a model
        n_samples = 100
        df = pd.DataFrame({
            "tech_rsi": np.random.rand(n_samples),
            "tech_sma_dist": np.random.rand(n_samples),
            "sent_composite": np.random.rand(n_samples),
            "onchain_whale": np.random.rand(n_samples),
            "target_return_24h": np.random.randn(n_samples)
        })
        # Strongly bias towards tech_rsi for easy verification
        df["target_return_24h"] = 5.0 * df["tech_rsi"]
        
        self.oracle.model_manager.train(df, target="target_return_24h")
        self.oracle.model_manager.save_model("integ_v1")

    def tearDown(self):
        if os.path.exists(self.model_dir):
            shutil.rmtree(self.model_dir)

    def test_integrated_prediction(self):
        """Verify that the loaded model influences the Oracle prediction."""
        # Setup dummy price data
        df_price = pd.DataFrame({
            'close': np.linspace(100, 110, 60),
            'high': np.linspace(101, 111, 60),
            'low': np.linspace(99, 109, 60),
            'open': np.linspace(100, 110, 60),
            'volume': np.random.rand(60) * 1000
        })
        context = {
            'sentiment': {'composite': 0.5},
            'on_chain': {'whale_score': 0.5}
        }
        
        # 1. Prediction WITHOUT model
        self.oracle.model_loaded = False
        res_no_model = self.oracle.predict_24h(df_price, context)
        
        # 2. Prediction WITH model
        self.oracle.load_oracle_model("integ_v1")
        res_with_model = self.oracle.predict_24h(df_price, context)
        
        # Verify model_info output
        self.assertTrue(res_with_model['model_info']['active'])
        self.assertGreater(res_with_model['model_info']['model_confidence'], 0)
        
        # Since the model was trained to follow RSI (which is high in our linsace data),
        # the prediction score should change when the model is active.
        self.assertNotEqual(res_no_model['price_target'], res_with_model['price_target'])
        
        print(f"\nNo Model Target: {res_no_model['price_target']:.2f}")
        print(f"With Model Target: {res_with_model['price_target']:.2f}")

if __name__ == "__main__":
    unittest.main()
