import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from src.microanalyst.intelligence.feature_engineering import MLFeatureEngineer 
from src.microanalyst.intelligence.ml_model_manager import MLModelManager

logger = logging.getLogger(__name__)

class OracleAnalyzer:
    """The Oracle: Specializes in T+24h directional forecasting.

    This class aggregates technical indicators, sentiment analysis, and
    on-chain data to produce a weighted consensus for short-term price direction.
    It integrates a trained machine learning model to refine predictions
    and calculate confidence scores.

    Attributes:
        weights (Dict[str, float]): Base weights for the signal consensus logic.
        engineer (MLFeatureEngineer): Component for technical feature extraction.
        model_manager (MLModelManager): Lifecycle manager for the ML prediction model.
        model_loaded (bool): Indicates if a trained ML model is currently active.
    """
    
    def __init__(self):
        """Initializes the OracleAnalyzer with default weights and components."""
        self.weights = {
            'tech_rsi': 0.2,
            'tech_sma_dist': 0.2,
            'sent_composite': 0.3,
            'onchain_whale': 0.3
        }
        self.engineer = MLFeatureEngineer()
        self.model_manager = MLModelManager()
        self.model_loaded = False

    def predict_24h(self, df_price: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a directional forecast for a 24-hour horizon.

        Performs feature engineering, calculates a signal consensus score,
        integrates ML model predictions if available, and determines the
        directional bias and price target.

        Args:
            df_price: Historical price data (OHLCV) with >= 50 periods.
            context: Metadata containing sentiment, on-chain, and risk data.

        Returns:
            Dict[str, Any]: Prediction results including direction, confidence,
                price target, and active model information.

        Raises:
            ValueError: If df_price has fewer than 50 periods.
        """
        if df_price.empty or len(df_price) < 50:
            logger.error("Precondition failed: Insufficient price history for Oracle.")
            raise ValueError("Oracle requires at least 50 periods of price history.")

        # 1. Feature Aggregation
        features = self._aggregate_features(df_price, context)
        
        # 2. Consensus Logic (Phase 1)
        # In Phase 2, this will call model.predict()
        prediction_score = sum(
            features.get(k, 0.0) * v 
            for k, v in self.weights.items()
        )

        # 3. ML Model Prediction Integration (Phase 44)
        model_prediction = 0.0
        model_confidence = 0.0
        if self.model_loaded:
            model_prediction, model_confidence = self.model_manager.predict(features)
            # Integrate model prediction with high weight (e.g., 50%)
            prediction_score = (prediction_score * 0.5) + (model_prediction * 0.5)
            logger.info(f"integrated ML model prediction: {model_prediction:.4f} with confidence {model_confidence:.4f}")
        
        # 3. Decision & Bounds Check
        direction = "NEUTRAL"
        if prediction_score > 0.1: direction = "BULLISH"
        elif prediction_score < -0.1: direction = "BEARISH"
        
        # 4. Price Target Calculation (Postcondition check)
        current_price = df_price['close'].iloc[-1]
        
        # Remediation: Use standardized volatility from Engineer
        volatility = features.get('tech_volatility', df_price['close'].pct_change().std())
        
        # Target = Current price + (score * volatility_buffer)
        price_target = current_price * (1 + (prediction_score * volatility * 2))
        
        return {
            'direction': direction,
            'confidence': min(abs(prediction_score) * 2, 1.0),
            'price_target': float(price_target),
            'horizon': '24h',
            'features': features,
            'model_info': {
                'active': self.model_loaded,
                'model_score': model_prediction,
                'model_confidence': model_confidence
            }
        }

    def load_oracle_model(self, version_tag: str):
        """Loads a specific model version from disk.

        Args:
            version_tag: The identifier of the model version to load.
        """
        try:
            self.model_manager.load_model(version_tag)
            self.model_loaded = True
            logger.info(f"Oracle model version {version_tag} loaded.")
        except Exception as e:
            logger.error(f"Failed to load Oracle model: {e}")
            self.model_loaded = False

    def _aggregate_features(self, df_price: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts and merges technical and contextual features for prediction.

        Args:
            df_price: Historical price data for technical analysis.
            context: Nested dictionary of contextual market intelligence.

        Returns:
            Dict[str, Any]: A flat feature vector for the latest period.
        """
        # 1. Technicals
        df_tech = self.engineer.extract_technical_features(df_price)
        latest_tech = df_tech.iloc[-1].to_dict() if not df_tech.empty else {}
        
        # 2. Contextual flattening
        flat_context = self.engineer.flatten_context(context)
        
        # Combine
        return {**latest_tech, **flat_context}
