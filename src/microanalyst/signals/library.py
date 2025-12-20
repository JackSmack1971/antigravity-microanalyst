import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SignalLibrary:
    """
    Standard library of technical signals for Agents.
    """
    

    def find_support_resistance(self, df: pd.DataFrame, window: int = 14) -> Dict[str, Any]:
        """
        Identify support and resistance levels using local extrema and touch-count heuristics.
        """
        if df.empty or len(df) < window:
            return {}

        current_price = df['close'].iloc[-1]
        
        # 1. Detect Local Extrema
        # Support: Local Lows
        lows = df['low'].rolling(window=window, center=True).min()
        # Resistance: Local Highs
        highs = df['high'].rolling(window=window, center=True).max()
        
        # 2. Extract pivot points (where actual price equals the rolling extrema)
        support_points = df[df['low'] == lows]['low']
        resistance_points = df[df['high'] == highs]['high']
        
        # 3. Cluster and count touches (using rounding to normalize levels)
        # Rounding to nearest $100 for BTC granularity
        s_clusters = support_points.round(-2).value_counts()
        r_clusters = resistance_points.round(-2).value_counts()
        
        # 4. Filter for levels near current price
        # Nearest support (highest cluster below current price)
        nearby_s = s_clusters[s_clusters.index < current_price].sort_index(ascending=False)
        # Nearest resistance (lowest cluster above current price)
        nearby_r = r_clusters[r_clusters.index > current_price].sort_index(ascending=True)
        
        nearest_s = float(nearby_s.index[0]) if not nearby_s.empty else None
        nearest_r = float(nearby_r.index[0]) if not nearby_r.empty else None
        
        # 5. Build zones
        return {
            'nearest_support': nearest_s,
            'nearest_resistance': nearest_r,
            'major_support_zone': {
                'lower': nearest_s * 0.995 if nearest_s else None, 
                'upper': nearest_s * 1.005 if nearest_s else None
            },
            'major_resistance_zone': {
                'lower': nearest_r * 0.995 if nearest_r else None, 
                'upper': nearest_r * 1.005 if nearest_r else None
            },
            'touches': {
                'support': int(nearby_s.iloc[0]) if not nearby_s.empty else 0,
                'resistance': int(nearby_r.iloc[0]) if not nearby_r.empty else 0
            }
        }

    def detect_all_signals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Scan for RSI, Moving Averages, MACD, and Volume signals.
        Expects DF with columns: open, high, low, close, volume.
        Auto-calculates indicators if missing.
        """
        if df.empty or len(df) < 50:
            return []
            
        signals = []
        close = df['close']
        
        # --- 1. RSI (Relative Strength Index) ---
        # Calculate if not present
        if 'rsi_14' not in df.columns:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = df['rsi_14']
            
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            signals.append({
                "type": "MOMENTUM",
                "name": "RSI Oversold",
                "bias": "BULLISH",
                "confidence": 0.7 + (30 - current_rsi)/100, # Higher confidence as it gets lower
                "value": current_rsi
            })
        elif current_rsi > 70:
            signals.append({
                "type": "MOMENTUM",
                "name": "RSI Overbought",
                "bias": "BEARISH",
                "confidence": 0.7 + (current_rsi - 70)/100,
                "value": current_rsi
            })
            
        # --- 2. SMA Crosses (Golden/Death Cross) ---
        # SMA 50 and 200
        sma50 = close.rolling(window=50).mean()
        sma200 = close.rolling(window=200).mean()
        
        if len(close) > 200:
            # Check for recent crossover (last candle)
            curr_50, prev_50 = sma50.iloc[-1], sma50.iloc[-2]
            curr_200, prev_200 = sma200.iloc[-1], sma200.iloc[-2]
            
            if prev_50 < prev_200 and curr_50 > curr_200:
                signals.append({
                    "type": "TREND",
                    "name": "Golden Cross (SMA 50 > 200)",
                    "bias": "BULLISH",
                    "confidence": 0.9,
                    "value": "CROSS_UP"
                })
            elif prev_50 > prev_200 and curr_50 < curr_200:
                signals.append({
                    "type": "TREND",
                    "name": "Death Cross (SMA 50 < 200)",
                    "bias": "BEARISH",
                    "confidence": 0.9,
                    "value": "CROSS_DOWN"
                })

        # --- 3. Close vs Moving Averages ---
        current_price = close.iloc[-1]
        curr_sma50 = sma50.iloc[-1]
        if current_price > curr_sma50:
             signals.append({
                "type": "TREND",
                "name": "Price > SMA 50",
                "bias": "BULLISH",
                "confidence": 0.6,
                "value": current_price
            })
        else:
             signals.append({
                "type": "TREND",
                "name": "Price < SMA 50",
                "bias": "BEARISH",
                "confidence": 0.6,
                "value": current_price
            })

        return signals
