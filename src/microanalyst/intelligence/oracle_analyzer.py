import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from src.microanalyst.intelligence.feature_engineering import MLFeatureEngineer 
from src.microanalyst.intelligence.ml_model_manager import MLModelManager

logger = logging.getLogger(__name__)

class OracleAnalyzer:
    """
    The Oracle: Specializes in T+24h directional forecasting.
    Initial implementation uses weighted signal consensus.
    Ready for XGBoost/LightGBM integration.
    """
    
    def __init__(self):
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
        """
        Main entry point for 24h prediction.
        Precondition: df_price must have >= 50 periods.
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
        """Loads a specific model version into the analyzer."""
        try:
            self.model_manager.load_model(version_tag)
            self.model_loaded = True
            logger.info(f"Oracle model version {version_tag} loaded.")
        except Exception as e:
            logger.error(f"Failed to load Oracle model: {e}")
            self.model_loaded = False

    def _aggregate_features(self, df_price: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Internal feature engineering pipeline using MLFeatureEngineer."""
        # 1. Technicals
        df_tech = self.engineer.extract_technical_features(df_price)
        latest_tech = df_tech.iloc[-1].to_dict() if not df_tech.empty else {}
        
        # 2. Contextual flattening
        flat_context = self.engineer.flatten_context(context)
        
        # Combine
        return {**latest_tech, **flat_context}
