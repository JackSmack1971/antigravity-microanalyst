import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from src.microanalyst.intelligence.transition_predictor import RegimeTransitionPredictor
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer

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
            correlation = analyzer.analyze_correlations(df_price['close'])
            
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
