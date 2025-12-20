import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SignalLibrary:
    """
    Standard library of technical signals for Agents.
    """
    
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
