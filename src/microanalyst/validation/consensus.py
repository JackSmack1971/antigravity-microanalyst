# src/microanalyst/validation/consensus.py
from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ConsensusEngine:
    """
    Statistical truth resolver for conflicting free data sources.
    Calculates confidence scores based on source reliability and consensus spread.
    """
    
    def __init__(self):
        # Track historical accuracy of each source (0.0 - 1.0)
        # Higher score = more weight in consensus
        self.source_reliability = {
            'binance': 0.98,      # High volume, primary source
            'binance_us': 0.97,   # Good fallback
            'coingecko': 0.95,    # reliable aggregator, slightly lagged
            'kraken': 0.95,       # robust clean data
            'blockchain_info': 0.85, # good for on-chain, sometimes erratic api
            'blockchair': 0.90,
            'synthetic_mvrv': 0.70, # Inherently lower confidence as proxy
            'synthetic_sopr': 0.65
        }
    
    def resolve_price_consensus(self, sources: Dict[str, float]) -> Dict[str, Any]:
        """
        Resolve true price from multiple sources.
        
        Args:
            sources: Dict of {source_name: price_value}
            
        Returns:
            Dict containing consensus_price, confidence, spread, outliers.
        """
        if not sources:
            return {'error': 'No sources provided'}

        # 1. Filter anomalies (negative prices, zero)
        valid_sources = {k: v for k, v in sources.items() if v > 0}
        if not valid_sources:
             return {'error': 'No valid positive prices'}

        # 2. Weighted calculation preparation
        prices = list(valid_sources.values())
        
        # Initial consensus (Median is robust against massive outliers)
        median_price = np.median(prices)
        
        # 3. Detect outliers (>2% deviations from median)
        outliers = []
        clean_sources = {}
        
        for src, price in valid_sources.items():
            deviation = abs(price - median_price) / median_price
            if deviation > 0.02: # 2% threshold
                outliers.append((src, price))
            else:
                clean_sources[src] = price
        
        # If all were outliers (high volatility), fallback to all valid
        if not clean_sources:
            clean_sources = valid_sources
            outliers = [] # Reset outliers since we are using everything

        # 4. Weighted Average on clean set
        weighted_sum = 0.0
        weight_total = 0.0
        
        for src, price in clean_sources.items():
            weight = self.source_reliability.get(src, 0.5) # Default 0.5 for unknown
            weighted_sum += price * weight
            weight_total += weight
            
        if weight_total == 0:
            consensus_price = np.mean(list(clean_sources.values()))
        else:
            consensus_price = weighted_sum / weight_total
            
        # 5. Calculate Confidence
        # Spread penalty
        clean_prices = list(clean_sources.values())
        spread = max(clean_prices) - min(clean_prices)
        spread_pct = (spread / consensus_price) * 100 if consensus_price > 0 else 0
        
        # Base confidence 1.0, penalize for spread
        # 0.1% spread -> 0.99
        # 1.0% spread -> 0.90
        # 5.0% spread -> 0.50
        confidence = max(0.0, 1.0 - (spread_pct / 10.0)) 
        
        # Source count bonus/penalty
        if len(clean_sources) < 2:
            confidence *= 0.8 # Single source penalty
            
        return {
            'consensus_price': float(consensus_price),
            'confidence': float(f"{confidence:.2f}"),
            'spread_pct': float(f"{spread_pct:.4f}"),
            'outliers': outliers,
            'sources_used_count': len(clean_sources),
            'interpretation': self._interpret_confidence(confidence)
        }
    
    def resolve_metric_with_uncertainty(
        self, 
        synthetic_value: float,
        synthetic_confidence: float,
        validation_sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combine synthetic metric with validation data to improve certainty.
        
        Args:
            synthetic_value: The calculated proxy value
            synthetic_confidence: The inherent confidence of the proxy method
            validation_sources: List of dicts [{'source': 'glassnode', 'value': 1.2}, ...]
        """
        if not validation_sources:
            return {
                'final_value': synthetic_value,
                'confidence': synthetic_confidence,
                'method': 'synthetic_only',
                'validation_status': 'unvalidated'
            }
        
        # Calculate consensus from validation sources
        val_values = [s['value'] for s in validation_sources if isinstance(s.get('value'), (int, float))]
        
        if not val_values:
             return {
                'final_value': synthetic_value,
                'confidence': synthetic_confidence,
                'method': 'synthetic_only',
                'validation_status': 'validation_data_invalid'
            }
            
        validation_avg = float(np.mean(val_values))
        
        # Measure agreement
        # Avoid div by zero
        denom = validation_avg if validation_avg != 0 else 1
        deviation = abs(synthetic_value - validation_avg) / abs(denom)
        
        final_confidence = synthetic_confidence
        final_value = synthetic_value
        
        if deviation < 0.05:  # <5% deviation
            # Strong agreement - boost confidence towards max
            boost = (1.0 - synthetic_confidence) * 0.5 
            final_confidence += boost
            # Pull value slightly towards validation
            final_value = (synthetic_value * 0.7) + (validation_avg * 0.3)
            agreement = 'strong'
            
        elif deviation < 0.15:  # 5-15% deviation
            # Moderate agreement - maintain confidence
            agreement = 'moderate'
            # Pull value slightly
            final_value = (synthetic_value * 0.9) + (validation_avg * 0.1)
            
        else:
            # Poor agreement - penalty
            final_confidence *= 0.7
            agreement = 'weak'
            # Keep synthetic value but flag it
        
        return {
            'final_value': float(final_value),
            'confidence': float(f"{final_confidence:.2f}"),
            'synthetic_value': synthetic_value,
            'validation_avg': validation_avg,
            'deviation_pct': float(f"{deviation * 100:.2f}"),
            'agreement': agreement,
            'method': 'synthetic_validated'
        }

    def _interpret_confidence(self, conf):
        if conf >= 0.9: return 'High Confidence'
        if conf >= 0.7: return 'Moderate Confidence'
        if conf >= 0.5: return 'Low Confidence'
        return 'Unreliable'
