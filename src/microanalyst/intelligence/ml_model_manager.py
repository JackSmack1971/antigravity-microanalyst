import pandas as pd
import numpy as np
import os
import joblib
import logging
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error

logger = logging.getLogger(__name__)

class MLModelManager:
    """
    Manages the lifecycle of Machine Learning models for price prediction.
    Supports training, inference, and persistence.
    """
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        self.model = None
        self.feature_names = []
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def train(self, df: pd.DataFrame, target: str) -> Dict[str, float]:
        """
        Trains a regressor on the provided dataset.
        """
        if len(df) < 10:
            raise ValueError(f"Insufficient data for training. Required: 10, Got: {len(df)}")

        # Separate features and target
        self.feature_names = [c for c in df.columns if c != target]
        X = df[self.feature_names]
        y = df[target]

        # Use RandomForest as a robust default
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X, y)

        # Basic evaluation
        y_pred = self.model.predict(X)
        rmse = root_mean_squared_error(y, y_pred)
        
        logger.info(f"Model trained successfully. RMSE: {rmse:.6f}")
        return {"rmse": float(rmse)}

    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Provides directional prediction and confidence score.
        """
        if self.model is None:
            return 0.0, 0.0

        # Construct input vector with defaults for missing keys
        input_data = []
        for feat in self.feature_names:
            input_data.append(features.get(feat, 0.0))
            
        X_test = np.array(input_data).reshape(1, -1)
        prediction = float(self.model.predict(X_test)[0])
        
        # Simple confidence: standard deviation of trees in the forest
        # (Heuristic: more agreement between trees = higher confidence)
        preds = []
        for estimator in self.model.estimators_:
            preds.append(estimator.predict(X_test)[0])
            
        std_dev = np.std(preds)
        # Normalize confidence to [0, 1] - inverse of relative std
        confidence = 1.0 / (1.0 + std_dev)
        
        return prediction, float(confidence)

    def save_model(self, version_tag: str) -> str:
        """
        Persists the model and feature metadata to disk.
        """
        if self.model is None:
            raise ValueError("No model trained to save.")

        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        path = os.path.join(self.model_dir, f"model_{version_tag}.joblib")
        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names
        }, path)
        
        logger.info(f"Model saved to {path}")
        return path

    def load_model(self, version_tag: str):
        """
        Loads a model and feature metadata from disk.
        """
        path = os.path.join(self.model_dir, f"model_{version_tag}.joblib")
        if not os.path.exists(path):
            raise FileNotFoundError(f"No model found at {path}")

        data = joblib.load(path)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        
        logger.info(f"Model loaded from {path}")
