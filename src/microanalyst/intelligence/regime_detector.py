import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MarketRegimeDetector:
    """
    Zero-cost regime classification using technical indicators.
    Provides deterministic 'Ground Truth' for Agents.
    """
    
    REGIMES = {
        "bull_trending": {
            "description": "Strong Upward Momentum",
            "rsi_threshold": 55,
            "adx_threshold": 20
        },
        "bear_trending": {
            "description": "Strong Downward Momentum",
            "rsi_threshold": 45,
            "adx_threshold": 20
        },
        "sideways_compression": {
            "description": "Volatility Squeeze / Range-bound",
            "adx_below": 20,
            "bb_width_below": 0.05
        },
        "high_volatility": {
            "description": "Extended ADR / Panic or Blow-off",
            "atr_percentile": 95
        },
        "distribution": {
            "description": "Topping structure with bear divergence",
            "rsi_divergence": True
        }
    }
    
    def classify(self, ohlcv_at: pd.DataFrame) -> Dict[str, Any]:
        """
        Classifies current market regime.
        """
        if ohlcv_at.empty or len(ohlcv_at) < 50:
            return {"regime": "sideways_compression", "confidence": 0.5, "note": "Insufficient data"}

        try:
            df = ohlcv_at.copy()
            
            # --- Indicators ---
            # 1. Trend: SMA 50
            df['sma50'] = df['close'].rolling(50).mean()
            
            # Use the latest available valid SMA
            valid_sma = df['sma50'].dropna()
            if valid_sma.empty:
                return {"regime": "sideways_compression", "confidence": 0.5, "note": "Insufficient SMA data"}
                
            price_vs_sma = (df['close'].iloc[-1] / valid_sma.iloc[-1]) - 1
            
            # 2. Momentum: RSI 14
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            current_rsi = df['rsi'].iloc[-1]
            
            # 3. Strength: ADX (Proxy)
            # Simple ADX proxy: Absolute change in SMA momentum over time
            df['mom'] = df['close'].pct_change(periods=14).abs()
            adx_proxy = df['mom'].rolling(14).mean().iloc[-1] * 100 
            
            # 4. Volatility: ATR %
            df['tr'] = np.maximum(df['high'] - df['low'], 
                                  np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                             abs(df['low'] - df['close'].shift(1))))
            df['atr_pct'] = (df['tr'].rolling(14).mean() / df['close']) * 100
            current_atr_pct = df['atr_pct'].iloc[-1]
            atr_80th = df['atr_pct'].quantile(0.95)
            
            # --- Logic ---
            regime = "sideways_compression"
            confidence = 0.6
            
            # 1. High Volatility (Emergency state)
            # Add small buffer to prevent false positives when vol is constant
            if current_atr_pct > (atr_80th * 1.05):
                regime = "high_volatility"
                confidence = 0.8
            # 2. Trending Checks
            elif (price_vs_sma > 0.03) and (current_rsi > 52):
                regime = "bull_trending"
                confidence = 0.85 if adx_proxy > 15 else 0.7
            elif (price_vs_sma < -0.03) and (current_rsi < 48):
                regime = "bear_trending"
                confidence = 0.85 if adx_proxy > 15 else 0.7
            # 3. Distribution
            elif current_rsi > 70 and price_vs_sma < 0.02: 
                regime = "distribution"
                confidence = 0.65
            # 4. Sideways (Default)
            else:
                regime = "sideways_compression"
                confidence = 0.75 if adx_proxy < 15 else 0.6

            print(f"DEBUG: Regime={regime}, RSI={current_rsi:.2f}, PriceVsSMA={price_vs_sma:.4f}, ADX={adx_proxy:.2f}")

            return {
                "regime": regime,
                "confidence": float(confidence),
                "metrics": {
                    "price_vs_sma": price_vs_sma,
                    "rsi": current_rsi,
                    "adx_proxy": adx_proxy,
                    "atr_pct": current_atr_pct
                },
                "agent_instructions": self._get_instructions(regime)
            }
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {"regime": "sideways_compression", "confidence": 0.5, "error": str(e)}

    def _get_instructions(self, regime: str) -> Dict[str, str]:
        PROMPT_LIBRARY = {
            "bull_trending": {
                "synthesizer": "Focus on momentum continuation. RSI > 50 is a support zone. Ignore minor bearish divergences.",
                "risk": "Max size 5%. Acceptable drawdown 10%."
            },
            "bear_trending": {
                "synthesizer": "Oversold bounces are exit points. Resistance levels are hard ceilings.",
                "risk": "Max size 2%. Tight stops at 3%."
            },
            "sideways_compression": {
                "synthesizer": "Mean reversion. RSI extremes (30/70) are entry/exit targets. Squeeze play imminent.",
                "risk": "Reduced sizing until breakout."
            },
            "high_volatility": {
                "synthesizer": "Extreme unpredictability. Reduce signal weighting. Wait for volatility to contract.",
                "risk": "Cash preservation mode. 1% max size."
            },
            "distribution": {
                "synthesizer": "Smart money is exiting. Watch for lower highs. Bull trap risk is extreme.",
                "risk": "Hedge positions. Trailing stops tight."
            }
        }
        return PROMPT_LIBRARY.get(regime, {})
