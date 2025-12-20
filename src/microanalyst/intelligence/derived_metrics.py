import pandas as pd
import numpy as np
import time
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class DerivedMetricsEngine:
    """
    Computes 'Institutional' metrics using mathematical proxies from free data.
    """

    @staticmethod
    def derive_funding_rate_proxy(spot: float, perp_mark: float) -> float:
        """
        Proxy for Annualized Funding Rate.
        (Mark - Spot) / Spot * 24h freq * 365 days
        """
        if spot <= 0: return 0.0
        basis = (perp_mark - spot) / spot
        # Freq is usually 8h (3x daily)
        return float(basis * 3 * 365 * 100) # Annualized %

    @staticmethod
    def derive_whale_accumulation_score(addresses_1k_plus: List[int]) -> Dict[str, Any]:
        """
        Input: Time series of 'Whale' address counts.
        Output: Score from -1 to 1 based on Rate of Change.
        """
        if not addresses_1k_plus or len(addresses_1k_plus) < 7:
            return {"score": 0.0, "status": "neutral", "reason": "Insufficient history"}
        
        # Calculate 7-day ROC
        start = float(addresses_1k_plus[0])
        end = float(addresses_1k_plus[-1])
        
        roc = (end - start) / start if start > 0 else 0
        
        # Scale: 1% change over 7 days is huge for whales
        score = np.clip(roc * 10, -1, 1) 
        
        return {
            "score": float(score),
            "status": "bullish" if score > 0.05 else "bearish" if score < -0.05 else "neutral",
            "interpretation": f"Whale counts moved {roc:.2%} over last 7 days."
        }

    @staticmethod
    def derive_order_flow_delta(depth: Dict[str, List[List[Any]]]) -> float:
        """
        Proxy for CVD using Mid-Book Imbalance.
        (BidVol - AskVol) / TotalVol near price
        """
        try:
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])
            
            if not bids or not asks: return 0.0
            
            # Limit to top 20 levels for 'Intelligent' proxy
            bid_vol = sum(float(q) for p, q in bids[:20])
            ask_vol = sum(float(q) for p, q in asks[:20])
            
            total = bid_vol + ask_vol
            if total == 0: return 0.0
            
            return float((bid_vol - ask_vol) / total)
        except Exception as e:
            logger.warning(f"Flow Delta failed: {e}")
            return 0.0
