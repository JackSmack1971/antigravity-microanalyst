import numpy as np
from typing import Dict, Any, List

class RegimeTransitionPredictor:
    """
    Predicts the probability of the NEXT market regime using a text-book Markov Chain.
    Trained on historical crypto market transitions (hardcoded probability matrix for Tier 3 MVP).
    """
    
    def __init__(self):
        # Transition Matrix (From Row -> To Column)
        # Regimes: [Bull, Bear, Sideways, HighVol, Distribution]
        self.regimes = ["bull_trending", "bear_trending", "sideways_compression", "high_volatility", "distribution"]
        
        # Approximateprobabilities based on historical market cycles
        self.matrix = {
            "bull_trending":        {"bull_trending": 0.60, "distribution": 0.20, "high_volatility": 0.15, "bear_trending": 0.00, "sideways_compression": 0.05},
            "bear_trending":        {"bear_trending": 0.60, "sideways_compression": 0.25, "high_volatility": 0.10, "bull_trending": 0.00, "distribution": 0.05},
            "sideways_compression": {"bull_trending": 0.30, "bear_trending": 0.30, "sideways_compression": 0.30, "high_volatility": 0.10, "distribution": 0.00},
            "high_volatility":      {"sideways_compression": 0.40, "bear_trending": 0.30, "bull_trending": 0.20, "high_volatility": 0.10, "distribution": 0.00},
            "distribution":         {"bear_trending": 0.50, "high_volatility": 0.30, "sideways_compression": 0.10, "distribution": 0.10, "bull_trending": 0.00}
        }

    def predict_next_regime(self, current_regime: str) -> Dict[str, Any]:
        """
        Returns probabilities for the next state given current state.
        """
        if current_regime not in self.matrix:
            # Default fallback if unknown
            return {
                "prediction": "sideways_compression",
                "probabilities": {r: 0.2 for r in self.regimes},
                "confidence": 0.0
            }
            
        probs = self.matrix[current_regime]
        
        # Find most likely next state (excluding self to find *change*)
        candidates = {k: v for k, v in probs.items() if k != current_regime}
        next_prediction = max(candidates, key=candidates.get)
        
        return {
            "current_regime": current_regime,
            "most_likely_next": next_prediction,
            "transition_probability": probs[next_prediction],
            "full_distribution": probs
        }
