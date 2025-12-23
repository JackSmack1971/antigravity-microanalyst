
from typing import List
import pandas as pd
from .base import BaseFactorDetector
from ..schemas import ConfluenceFactor, FactorType, ConfluenceType
from loguru import logger

class PriceActionDetector(BaseFactorDetector):
    """
    Detects market factors derived from raw price action, specifically
    historical support/resistance levels and significant swing points.
    """
    def detect(self, df: pd.DataFrame, **kwargs) -> List[ConfluenceFactor]:
        """
        Detects price-action factors.
        
        Args:
            df: DataFrame with OHLC data.
            **kwargs: Unused.
            
        Returns:
            List[ConfluenceFactor]: Detected S/R and Swing points.
        """
        factors = []
        factors.extend(self._detect_historical_sr(df))
        factors.extend(self._detect_swing_points(df))
        return factors

    def _detect_historical_sr(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect historical support/resistance levels using swing points and touch counts.
        
        Analyzes recent swing highs and lows, validates them based on how many
        times price has interacted with those levels, and applies a recency weight.
        
        Args:
            df: Price DataFrame.
            
        Returns:
            List[ConfluenceFactor]: HISTORICAL_SR factors.
        """
        factors = []
        # Find swing highs (resistance candidates)
        df = df.copy()
        df['swing_high'] = (
            (df['high'] > df['high'].shift(1)) &
            (df['high'] > df['high'].shift(2)) &
            (df['high'] > df['high'].shift(-1)) &
            (df['high'] > df['high'].shift(-2))
        )
        
        # Find swing lows (support candidates)
        df['swing_low'] = (
            (df['low'] < df['low'].shift(1)) &
            (df['low'] < df['low'].shift(2)) &
            (df['low'] < df['low'].shift(-1)) &
            (df['low'] < df['low'].shift(-2))
        )
        
        # Process swing highs
        swing_highs = df[df['swing_high']]['high'].values
        for price in swing_highs:
            touches = self._count_touches(df, price, tolerance=0.01)
            recency_weight = self._calculate_recency_weight(
                df[df['high'] == price].index[-1], len(df)
            )
            strength = min(1.0, (touches / 5.0) * recency_weight)
            
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.HISTORICAL_SR,
                strength=strength,
                direction=ConfluenceType.RESISTANCE,
                metadata={"touches": touches}
            ))
            
        # Process swing lows
        swing_lows = df[df['swing_low']]['low'].values
        for price in swing_lows:
            touches = self._count_touches(df, price, tolerance=0.01)
            recency_weight = self._calculate_recency_weight(
                df[df['low'] == price].index[-1], len(df)
            )
            strength = min(1.0, (touches / 5.0) * recency_weight)
            
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.HISTORICAL_SR,
                strength=strength,
                direction=ConfluenceType.SUPPORT,
                metadata={"touches": touches}
            ))
        return factors

    def _detect_swing_points(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect significant multi-day swing high/low points using a rolling window.
        
        Args:
            df: Price DataFrame.
            
        Returns:
            List[ConfluenceFactor]: SWING_POINT factors.
        """
        factors = []
        window = 10
        df_swings = df.copy()
        df_swings['major_swing_high'] = df_swings['high'] == df_swings['high'].rolling(window * 2 + 1, center=True).max()
        df_swings['major_swing_low'] = df_swings['low'] == df_swings['low'].rolling(window * 2 + 1, center=True).min()
        
        swing_highs = df_swings[df_swings['major_swing_high']]['high'].dropna()
        for price in swing_highs:
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.SWING_POINT,
                strength=0.6,
                direction=ConfluenceType.RESISTANCE
            ))
        
        swing_lows = df_swings[df_swings['major_swing_low']]['low'].dropna()
        for price in swing_lows:
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.SWING_POINT,
                strength=0.6,
                direction=ConfluenceType.SUPPORT
            ))
        return factors

    def _count_touches(self, df: pd.DataFrame, price: float, tolerance: float = 0.01) -> int:
        """
        Counts how many times price bars have touched a specific price level.
        """
        within_range = (
            (df['high'] >= price * (1 - tolerance)) &
            (df['high'] <= price * (1 + tolerance))
        ) | (
            (df['low'] >= price * (1 - tolerance)) &
            (df['low'] <= price * (1 + tolerance))
        )
        return within_range.sum()
    
    def _calculate_recency_weight(self, touch_index: int, total_length: int) -> float:
        """
        Calculates a weight based on how recently a level was touched (0.5 to 1.0).
        """
        recency = (touch_index + 1) / total_length
        return 0.5 + (recency * 0.5)
