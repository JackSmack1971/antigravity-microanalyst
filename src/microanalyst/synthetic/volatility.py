# src/microanalyst/synthetic/volatility.py
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VolatilityEngine:
    """
    Synthesizes 'Implied Volatility' (IV) from free data sources.
    Uses Composite Volatility Model:
    IV ~ (Weighted Realized Vol) * (Sentiment Multiplier)
    """
    
    def __init__(self):
        self.fng_api = "https://api.alternative.me/fng/"
    
    def calculate_synthetic_iv(self, ohlcv_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate Synthetic IV from OHLCV data + Fear Index.
        
        Args:
            ohlcv_df: DataFrame with 'close', 'high', 'low' columns.
        """
        if ohlcv_df.empty or len(ohlcv_df) < 30:
            return {'error': 'Insufficient data for volatility calculation'}
        
        try:
            # 1. Historical Volatility (HV) - 30d Annualized
            # Log returns
            ohlcv_df = ohlcv_df.copy()
            ohlcv_df['returns'] = np.log(ohlcv_df['close'] / ohlcv_df['close'].shift(1))
            
            # 30-day Rolling Std Dev * sqrt(365)
            hv_30d = ohlcv_df['returns'].rolling(window=30).std().iloc[-1] * np.sqrt(365) * 100
            
            # 2. ATR-based Volatility (Intraday volatility)
            # True Range
            high_low = ohlcv_df['high'] - ohlcv_df['low']
            high_close = np.abs(ohlcv_df['high'] - ohlcv_df['close'].shift())
            low_close = np.abs(ohlcv_df['low'] - ohlcv_df['close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            
            atr_14 = true_range.rolling(14).mean()
            # Normalize ATR by price to get % volatility
            atr_pct = (atr_14 / ohlcv_df['close']).iloc[-1] * np.sqrt(365) * 100
            
            # 3. Sentiment Adjustment (Fear & Greed)
            # Thesis: Fear (Low Index) -> High IV. Greed -> Low/Medium IV.
            fng_data = self._get_fear_greed_index()
            fear_index = float(fng_data.get('value', 50))
            
            # 50 is neutral. 
            # If 20 (Extreme Fear) -> Multiplier should be > 1.0 (e.g. 1.15)
            # If 80 (Extreme Greed) -> Multiplier might be < 1.0 or 1.0 (IV crush)
            
            # Formula: 1 + (Neutral - Actual) / Dampener
            # 1 + (50 - 20) / 200 = 1 + 0.15 = 1.15
            regime_multiplier = 1.0 + (50 - fear_index) / 200.0
            
            # 4. Composite Synthesis
            # Weight HV (60%) and ATR (40%)
            raw_vol = (hv_30d * 0.6) + (atr_pct * 0.4)
            synthetic_iv = raw_vol * regime_multiplier
            
            return {
                'timestamp': ohlcv_df.index[-1].isoformat() if hasattr(ohlcv_df.index[-1], 'isoformat') else str(ohlcv_df.index[-1]),
                'metric': 'synthetic_implied_volatility',
                'value': float(f"{synthetic_iv:.2f}"),
                'components': {
                    'historical_vol_30d': float(f"{hv_30d:.2f}"),
                    'atr_volatility': float(f"{atr_pct:.2f}"),
                    'fear_greed_index': fear_index,
                    'regime_multiplier': float(f"{regime_multiplier:.2f}")
                },
                'interpretation': self._interpret_iv(synthetic_iv, hv_30d),
                'confidence': 0.75 # Good proxy, but not market pricing
            }
            
        except Exception as e:
            logger.error(f"Error calculating synthetic IV: {e}")
            return {'error': str(e)}

    def _get_fear_greed_index(self) -> Dict[str, Any]:
        """Fetch Sentiment from Alternative.me Free API"""
        try:
            response = requests.get(self.fng_api, params={'limit': 1}, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get('data'):
                return data['data'][0]
            return {'value': 50} # Default neutral
        except Exception as e:
            logger.warning(f"Fear & Greed API failed: {e}")
            return {'value': 50}

    def _interpret_iv(self, iv, hv):
        if iv > hv * 1.2: return 'High IV (Expect Volatility / Expensive Options)'
        if iv < hv * 0.8: return 'Low IV (Expect Calm / Cheap Options)'
        return 'Neutral Volatility'
