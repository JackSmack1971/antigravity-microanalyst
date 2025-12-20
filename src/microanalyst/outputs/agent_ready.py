import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from src.microanalyst.intelligence.transition_predictor import RegimeTransitionPredictor
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer
from src.microanalyst.intelligence.feature_engineering import MLFeatureEngineer # new

logger = logging.getLogger(__name__)

class AgentDatasetBuilder:
    """
    Transforms dispersed metrics into a unified, agent-consumable JSON structure.
    Integrates: Price, Flows, Derivatives, OnChain, Sentiment, Risk, Intelligence.
    """
    
    def build_feature_dataset(
        self,
        df_price: pd.DataFrame,
        flows_data: Optional[Dict[str, Any]] = None,
        derivatives_data: Optional[Dict[str, Any]] = None,
        sentiment_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        intelligence_data: Optional[Dict[str, Any]] = None,
        derived_metrics_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds the master dataset enriched with Ground Truth and Derived Metrics.
        """
        try:
            if df_price.empty:
                logger.error("Empty price dataframe provided to Builder")
                return {}

            latest_row = df_price.iloc[-1]
            timestamp = latest_row.name if isinstance(latest_row.name, (str, datetime)) else datetime.now().isoformat()
            
            # Ground Truth from Intelligence (Regime Detector)
            intel = intelligence_data or {}
            regime = intel.get('regime', 'unknown')
            confidence = intel.get('confidence', 0.0)
            
            # --- Phase 53: Predictive Intelligence ---
            predictor = RegimeTransitionPredictor()
            prediction = predictor.predict_next_regime(regime)
            
            analyzer = CorrelationAnalyzer()
            correlation = analyzer.analyze_correlations(df_price['close'], df_price['close'])
            
            intel['predictions'] = prediction

            dataset = {
                "timestamp": str(timestamp),
                "ground_truth": {
                    "regime": regime,
                    "regime_confidence": confidence,
                    "instructions": intel.get('agent_instructions', {})
                },
                "price": {
                    "current": float(latest_row.get('close', 0)),
                    "open": float(latest_row.get('open', 0)),
                    "high": float(latest_row.get('high', 0)),
                    "low": float(latest_row.get('low', 0)),
                    "volume": float(latest_row.get('volume', 0)),
                    "features": {k: float(v) for k, v in latest_row.items() if k not in ['open', 'high', 'low', 'close', 'volume']}
                },
                "derived_metrics": derived_metrics_data or {},
                "macro": {
                    "correlation_btc_dxy": correlation
                },
                "flows": flows_data or {},
                "derivatives": derivatives_data or {},
                "sentiment": sentiment_data or {},
                "risk": risk_data or {},
                "intelligence": intel
            }
            
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to build agent dataset: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def build_ml_dataset(
        self,
        df_price: pd.DataFrame,
        sentiment_history: Optional[Dict[str, Any]] = None,
        onchain_history: Optional[Dict[str, Any]] = None,
        risk_history: Optional[Dict[str, Any]] = None,
        vision_history: Optional[Dict[str, Any]] = None,
        volatility_history: Optional[Dict[str, Any]] = None,
        is_inference: bool = True # Security Remediation: Distinguish training vs inference
    ) -> pd.DataFrame:
        """
        Builds a flattened, multi-timeframe feature matrix.
        Security: Only broadcasts point-in-time data if is_inference=True.
        """
        engineer = MLFeatureEngineer()
        
        # 1. Technical Features
        df_ml = engineer.extract_technical_features(df_price)
        df_ml['price_close'] = df_price['close']
        
        # 2. Integrate Point-in-Time Contextual Data
        context = {
            'sentiment': sentiment_history or {},
            'onchain': onchain_history or {},
            'risk': risk_history or {},
            'vision': vision_history or {},
            'volatility': volatility_history or {}
        }
        
        flat_context = engineer.flatten_context(context)
        
        # Security Remediation: Prevent Data Leakage
        if is_inference:
            # Broadcast latest context to all rows (Valid for live inference on latest candle)
            for feature, val in flat_context.items():
                df_ml[feature] = val
        else:
            # For TRAINING, we only populate the LATEST row, or expect historical series
            # This prevents future-leakage in backtests/training.
            for feature, val in flat_context.items():
                df_ml.loc[df_ml.index[-1], feature] = val
                # Rest remain NaN or 0.0 (enforcing data collection per-step)
            
        return df_ml
