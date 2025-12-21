import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    """
    Analyzes correlations between Crypto (BTC) and Macro assets (DXY, SPY).
    Detects 'Decoupling' events which often precede violent moves.
    """
    
    def __init__(self):
        pass
        
    def analyze_correlations(
        self, 
        btc_prices: pd.Series, 
        macro_series: Dict[str, pd.Series]
    ) -> List[Dict[str, Any]]:
        """
        Computes rolling correlation against real macro assets.
        """
        if (isinstance(btc_prices, (pd.Series, pd.DataFrame)) and btc_prices.empty) or btc_prices is None or not isinstance(macro_series, dict) or len(macro_series) == 0:
             return [{"error": "Insufficient data"}]

        results = []
        
        # Ensure alignment of dates
        common_index = btc_prices.index
        
        for asset_name, asset_series in macro_series.items():
            try:
                if asset_series.empty:
                    continue
                    
                # Align data (inner join on dates)
                aligned_df = pd.concat([btc_prices, asset_series], axis=1, join='inner').dropna()
                
                if len(aligned_df) < 30:
                    results.append({
                        "metric": f"BTC_{asset_name.upper()}_Correlation",
                        "status": "insufficient_overlap"
                    })
                    continue
                
                btc_aligned = aligned_df.iloc[:, 0]
                macro_aligned = aligned_df.iloc[:, 1]
                
                # Calculate Rolling Correlation (30 periods)
                rolling_corr = btc_aligned.rolling(30).corr(macro_aligned)
                current_corr = rolling_corr.iloc[-1]
                
                # Logic: Detect Regime Break
                status = "normal"
                interpretation = "Standard macro coupling."
                
                if asset_name == 'dxy':
                    # DXY usually negative. Positive = Risk-On Breakout (Decoupling)
                    if current_corr > 0.2:
                        status = "decoupling_bullish"
                        interpretation = "BTC rising with DXY (Strength) or Falling with DXY (Weakness)."
                    elif current_corr < -0.8:
                        status = "tightly_coupled"
                        interpretation = "BTC purely driven by Dollar flows."
                        
                elif asset_name == 'spy':
                    # SPY usually positive. Negative = Divergence
                    if current_corr < -0.2:
                        status = "divergence_warning"
                        interpretation = "BTC decoupling from Equities risk."
                    elif current_corr > 0.9:
                        status = "high_beta"
                        interpretation = "BTC acting as leveraged Tech Stock."
                
                results.append({
                    "metric": f"BTC_{asset_name.upper()}_Correlation_30d",
                    "value": float(current_corr) if not np.isnan(current_corr) else 0.0,
                    "status": status,
                    "interpretation": interpretation
                })
                
            except Exception as e:
                logger.error(f"Correlation failed for {asset_name}: {e}")
                
        return results
