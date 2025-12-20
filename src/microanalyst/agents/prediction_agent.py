from typing import Dict, Any, Optional
import logging
from src.microanalyst.agents.base import BaseAgent
from src.microanalyst.intelligence.oracle_analyzer import OracleAnalyzer

logger = logging.getLogger(__name__)

class PredictionAgent(BaseAgent):
    """
    The PredictionAgent uses the ML-driven OracleAnalyzer to generate
    deterministic forecasts for the next 24 hours.
    
    It serves as a quantitative anchor, providing 'Ground Truth' forecasts
    that other agents (Retail, Institutional) can debate.
    """
    
    def __init__(self):
        super().__init__(name="PredictionOracle")
        self.oracle = OracleAnalyzer()

    def run_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a 24-hour prediction using price history and context.
        
        Args:
            context: Must include 'df_price' and 'context_metadata'.
            
        Returns:
            Dict: {
                "horizon": "24h",
                "direction": "UP"|"DOWN"|"NEUTRAL",
                "price_target": float,
                "confidence": float,
                "reasoning": str
            }
        """
        df_price = context.get('df_price')
        meta = context.get('context_metadata', {})
        
        if df_price is None or df_price.empty:
            logger.error("PredictionAgent: Missing 'df_price' in context.")
            return {"direction": "NEUTRAL", "confidence": 0.0, "reasoning": "Missing price data."}

        try:
            # OracleAnalyzer returns {direction, confidence, price_target, active_model, ...}
            prediction = self.oracle.predict_24h(df_price, meta)
            
            # Enrich with standardized Agent output
            prediction['horizon'] = "24h"
            prediction['reasoning'] = f"Oracle consensus at {prediction['confidence']:.2f} confidence."
            
            return prediction
            
        except Exception as e:
            logger.error(f"PredictionAgent execution failed: {e}")
            return {
                "horizon": "24h",
                "direction": "NEUTRAL",
                "confidence": 0.0,
                "reasoning": f"Error: {e}"
            }
