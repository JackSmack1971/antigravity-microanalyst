# src/microanalyst/aggregation/timeframes.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MultiTimeframeAggregator:
    """
    Standardizes data into multiple timeframes (1m, 5m, 1h, 4h, 1d)
    and analyzes fractal alignment (confluence across timeframes).
    """

    def resample_ohlcv(self, df: pd.DataFrame, timeframe_rule: str) -> pd.DataFrame:
        """
        Resample minute-level data to higher timeframes.
        Expects datetime index.
        timeframe_rule: pandas offset alias (e.g. '5T', '1H', '4H', '1D')
        """
        if df.empty:
            return df
            
        # Ensure timestamp is index
        data = df.copy()
        if not isinstance(data.index, pd.DatetimeIndex):
            # Try to find timestamp column
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.set_index('timestamp', inplace=True)
            elif 'date' in data.columns:
                 data['date'] = pd.to_datetime(data['date'])
                 data.set_index('date', inplace=True)
            else:
                 logger.warning("No timestamp index or column found for resampling")
                 return df

        # Aggregation rules
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Only aggregate existing columns
        final_agg = {k: v for k, v in agg_dict.items() if k in data.columns}
        
        try:
            resampled = data.resample(timeframe_rule).agg(final_agg)
            # Remove empty rows (gaps)
            resampled.dropna(inplace=True)
            return resampled
        except Exception as e:
            logger.error(f"Resampling failed: {e}")
            return pd.DataFrame()

    def calculate_alignment(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Check trend alignment across timeframes.
        data_map: {'1h': df1, '4h': df2, '1d': df3}
        Returns: Score (0-100) and Direction.
        """
        scores = []
        directions = []
        
        for tf, df in data_map.items():
            if df.empty or len(df) < 50:
                continue
                
            # Simple Trend Logic: Close > SMA(50)
            # Or EMA(20) > SMA(50)
            close = df['close']
            sma50 = close.rolling(50).mean()
            
            last_close = close.iloc[-1]
            last_sma = sma50.iloc[-1]
            
            if last_close > last_sma:
                scores.append(1) # Bullish
                directions.append("bullish")
            else:
                scores.append(-1) # Bearish
                directions.append("bearish")
        
        if not scores:
            return {"score": 0, "direction": "neutral"}
            
        avg_score = sum(scores) / len(scores)
        
        # Intepretation
        # 1.0 = All Bullish
        # -1.0 = All Bearish
        # 0 = Mixed
        
        alignment_strength = abs(avg_score) * 100
        overall_dir = "neutral"
        if avg_score > 0.3: overall_dir = "bullish"
        if avg_score < -0.3: overall_dir = "bearish"
        
        return {
            "alignment_score": alignment_strength,
            "overall_direction": overall_dir,
            "timeframes_checked": len(scores),
            "is_fractal_aligned": alignment_strength == 100
        }
