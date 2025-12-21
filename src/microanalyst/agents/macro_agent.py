from typing import Dict, Any, List
import logging
from src.microanalyst.agents.base import BaseAgent
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer

logger = logging.getLogger(__name__)

class MacroSpecialistAgent(BaseAgent):
    """The MacroSpecialistAgent (The Economist) analyzes BTC/Macro correlations.

    Analyzes the relationship between BTC and traditional macro assets 
    (DXY, SPY, etc.) to identify regime shifts such as decoupling or
    risk-on/risk-off divergences.
    """
    
    def __init__(self):
        super().__init__(name="MacroEconomist")
        self.analyzer = CorrelationAnalyzer()

    def run_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Interprets correlation data to identify the current macro regime.
        
        Analyzes a list of correlation mappings to determine if BTC is 
        trading as a risk-on asset, a safe haven (decoupled), or showing 
        divergent behavior.

        Args:
            context: A dictionary containing 'correlations' (a list of 
                     dictionaries with 'status' and 'interpretation' keys).
            
        Returns:
            Dict: A dictionary containing the identified 'regime' (string),
                  'confidence' (float), and descriptive 'reasoning' (string).
        """
        correlations = context.get('correlations', [])
        
        if not correlations:
            logger.warning("MacroSpecialistAgent: No correlation data found in context.")
            return {
                "regime": "UNKNOWN",
                "confidence": 0.0,
                "reasoning": "Macro signal unavailable due to missing correlation data."
            }

        try:
            # Aggregate status and interpretations
            regimes = [c.get('status', 'normal') for c in correlations]
            interpretations = [c.get('interpretation', '') for c in correlations]
            
            # Simple voting/priority logic for regime
            if any("decoupling" in r for r in regimes):
                primary_regime = "DECOUPLING_BULLISH" if any("bullish" in r for r in regimes) else "DECOUPLING"
            elif any("divergence" in r for r in regimes):
                primary_regime = "DIVERGENCE"
            else:
                primary_regime = "COUPLED"

            reasoning = " | ".join(interpretations)
            
            return {
                "regime": primary_regime,
                "confidence": 0.75, # Consistent structural confidence
                "reasoning": f"Macro Perspective: {reasoning}"
            }
            
        except Exception as e:
            logger.error(f"MacroSpecialistAgent execution failed: {e}")
            return {
                "regime": "ERROR",
                "confidence": 0.0,
                "reasoning": f"Macro analysis error: {e}"
            }
