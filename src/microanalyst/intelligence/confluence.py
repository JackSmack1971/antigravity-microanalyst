import pandas as pd
import logging
from typing import Dict, Optional, Any
from src.microanalyst.core.persistence import DatabaseManager

logger = logging.getLogger(__name__)

class ConfluenceUtils:
    """
    Utilities for identifying Fractal Alignment across multiple timeframes.
    Timeframes: 15m (Tactical), 1h (Intraday), 1d (Strategic).
    """
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager if db_manager else DatabaseManager()

    def determine_trend(self, prices: pd.Series, period: int = 20) -> str:
        """
        Simple trend determination using SMA.
        Returns: "Bullish", "Bearish", or "Neutral".
        """
        if len(prices) < period:
            return "Neutral"
        
        sma = prices.rolling(window=period).mean().iloc[-1]
        current_price = prices.iloc[-1]
        
        if current_price > sma:
            return "Bullish"
        elif current_price < sma:
            return "Bearish"
        else:
            return "Neutral"

    def check_fractal_alignment(self) -> Dict[str, Any]:
        """
        Checks if 15m, 1h, and 1d trends are aligned.
        """
        timeframes = ["15m", "1h", "1d"]
        trends = {}
        
        try:
            for tf in timeframes:
                # Fetch enough data for SMA
                df = self.db.get_price_history(limit=50, interval=tf)
                if df.empty:
                    trends[tf] = "Unknown"
                    continue
                
                trend = self.determine_trend(df["close"])
                trends[tf] = trend
                
            # Check alignment
            # Filter out Unknowns to avoid false positives? Or treat Unknown as breaking alignment.
            # We need explicit Bullish/Bearish alignment.
            
            is_bullish_aligned = all(t == "Bullish" for t in trends.values())
            is_bearish_aligned = all(t == "Bearish" for t in trends.values())
            
            confluence_type = "None"
            if is_bullish_aligned:
                confluence_type = "Bullish Fractal"
            elif is_bearish_aligned:
                confluence_type = "Bearish Fractal"
                
            return {
                "aligned": is_bullish_aligned or is_bearish_aligned,
                "type": confluence_type,
                "details": trends
            }
            
        except Exception as e:
            logger.error(f"Confluence check failed: {e}")
            return {"aligned": False, "type": "Error", "details": {}}
