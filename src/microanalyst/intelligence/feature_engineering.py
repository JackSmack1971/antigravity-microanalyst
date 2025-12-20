import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class MLFeatureEngineer:
    """
    Transforms multi-sourced metrics into flattened, numeric feature vectors for ML.
    Handles technical indicators, sentiment scores, and on-chain metrics.
    """
    
    def __init__(self):
        self.feature_map = {
            'sent_composite': ('sentiment', 'composite_score'),
            'sent_vol': ('sentiment', 'volatility'),
            'onchain_whale': ('onchain', 'whale_score'),
            'onchain_congestion': ('onchain', 'mempool_congestion'),
            'risk_var_95': ('risk', 'var_95'),
            'iv_garch': ('volatility', 'synthetic_iv_garch'),
            'vision_liq_dist': ('vision', 'liq_distance')
        }

    def flatten_context(self, context: Dict[str, Any]) -> Dict[str, float]:
        """
        Extracts and flattens nested metrics into a single numeric dictionary.
        Returns 0.0 for missing data.
        """
        flattened = {}
        for feature_name, (module, key) in self.feature_map.items():
            try:
                val = context.get(module, {}).get(key, 0.0)
                # Ensure it's numeric
                flattened[feature_name] = float(val) if val is not None else 0.0
            except (TypeError, ValueError):
                flattened[feature_name] = 0.0
                
        return flattened

    def extract_technical_features(self, df_price: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates normalized technical indicators for ML.
        """
        if df_price.empty or len(df_price) < 14:
            return pd.DataFrame(index=df_price.index)

        df = df_price.copy()
        
        # 1. RSI (Classic momentum)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Remediation: Fix division by zero
        loss = loss.replace(0, 1e-9)
        rs = gain / loss
        df['tech_rsi'] = 100 - (100 / (1 + rs))
        df['tech_rsi'] = df['tech_rsi'] / 100.0 # Normalize to [0,1]
        
        # 2. Price vs SMA Cross
        df['tech_sma20'] = df['close'].rolling(20).mean()
        df['tech_sma_dist'] = (df['close'] - df['tech_sma20']) / df['tech_sma20']
        
        # 3. Volatility (GARCH-lite: Rolling Std of Log Returns)
        df['log_ret'] = np.log(df['close'] / df['close'].shift(1))
        df['tech_volatility'] = df['log_ret'].rolling(window=14).std()
        
        # Cleanup
        return df[['tech_rsi', 'tech_sma_dist', 'tech_volatility']].fillna(0.0)
