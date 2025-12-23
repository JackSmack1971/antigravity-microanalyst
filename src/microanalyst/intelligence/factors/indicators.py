
from typing import List
import pandas as pd
import numpy as np
from .base import BaseFactorDetector
from ..schemas import ConfluenceFactor, FactorType, ConfluenceType
from loguru import logger

class VolumeProfileDetector(BaseFactorDetector):
    """
    Detects high-volume nodes (Point of Control) by analyzing volume distribution.
    
    Identifies institutional liquidity clusters by binning price data and 
    detecting peaks in the aggregate volume profile.
    """
    def detect(self, df: pd.DataFrame, **kwargs) -> List[ConfluenceFactor]:
        """
        Detects volume profile peaks.
        
        Args:
            df: Price DataFrame with 'volume' column.
            **kwargs: Unused.
            
        Returns:
            List[ConfluenceFactor]: Detected high-volume nodes (POCs).
        """
        factors = []
        if 'volume' not in df.columns or df['volume'].sum() == 0:
            return factors
        
        # Create price bins (0.5% intervals)
        price_min = df['low'].min()
        price_max = df['high'].max()
        if price_min == price_max: return []
        
        n_bins = int((price_max - price_min) / (price_min * 0.005))
        n_bins = max(10, n_bins) 
        
        bins = np.linspace(price_min, price_max, n_bins)
        
        # Aggregate volume per bin
        volume_profile = np.zeros(len(bins) - 1)
        for _, row in df.iterrows():
            bar_bins = np.digitize([row['low'], row['high']], bins)
            start_idx = max(0, bar_bins[0]-1)
            end_idx = min(len(volume_profile), bar_bins[1])
            for i in range(start_idx, end_idx):
                volume_profile[i] += row['volume']
        
        # Find peaks (local maxima)
        from scipy.signal import find_peaks
        if len(volume_profile) > 0:
             peaks, properties = find_peaks(volume_profile, prominence=np.std(volume_profile))
             for peak_idx in peaks:
                price = (bins[peak_idx] + bins[peak_idx + 1]) / 2
                volume_strength = volume_profile[peak_idx] / volume_profile.max()
                factors.append(ConfluenceFactor(
                    price=price,
                    factor_type=FactorType.VOLUME_PROFILE,
                    strength=volume_strength,
                    direction=ConfluenceType.PIVOT,
                    metadata={"volume": volume_profile[peak_idx]}
                ))
        return factors

class FibonacciDetector(BaseFactorDetector):
    """
    Calculates Fibonacci retracement levels derived from major price swings.
    
    Focuses on standard mathematical levels (0.382, 0.5, 0.618) to identify 
    potential support and resistance zones in a trending market.
    """
    def detect(self, df: pd.DataFrame, **kwargs) -> List[ConfluenceFactor]:
        """
        Detects Fibonacci retracement levels.
        
        Args:
            df: Price DataFrame.
            **kwargs: Unused.
            
        Returns:
            List[ConfluenceFactor]: Fibonacci clusters with weighted importance.
        """
        factors = []
        recent = df.tail(60)
        swing_high = recent['high'].max()
        swing_low = recent['low'].min()
        
        fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        current_price = df['close'].iloc[-1]
        
        for level in fib_levels:
            price = swing_low + (swing_high - swing_low) * (1 - level)
            if level in [0.5, 0.618]:
                strength = 0.9
            elif level in [0.382, 0.786]:
                strength = 0.7
            else:
                strength = 0.5
            
            direction = ConfluenceType.SUPPORT if price < current_price else ConfluenceType.RESISTANCE
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.FIBONACCI,
                strength=strength,
                direction=direction,
                metadata={"fib_level": level}
            ))
        return factors
