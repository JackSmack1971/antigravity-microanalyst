import pandas as pd
import numpy as np
from typing import List
from .base import BaseFactorDetector
from ..schemas import ConfluenceFactor, FactorType, ConfluenceType
from loguru import logger

class OpenInterestDetector(BaseFactorDetector):
    """
    Detects liquidity clusters and 'magnet' levels derived from Open Interest.
    
    Analyzes OI concentration at specific price levels to identify where 
    traders are heavily positioned, which often acts as a target (magnet)
    or significant pivot for price discovery.
    """
    
    def detect(self, df_price: pd.DataFrame, **kwargs) -> List[ConfluenceFactor]:
        """
        Detects Open Interest clusters.
        
        Args:
            df_price: Price DataFrame (to determine current price relative to OI).
            **kwargs: Must contain 'df_oi' (Open Interest DataFrame).
            
        Returns:
            List[ConfluenceFactor]: Detected OI cluster factors.
        """
        df_oi = kwargs.get('df_oi')
        if df_oi is None or df_oi.empty:
            return []
            
        if 'price' not in df_oi.columns or 'open_interest' not in df_oi.columns:
            logger.warning("OI data missing 'price' or 'open_interest' columns")
            return []
            
        factors = []
        current_price = df_price['close'].iloc[-1]
        
        # Aggregate OI by price (binning if necessary, but assuming pre-binned for now)
        # If not binned, we bin it into 0.25% ranges
        if len(df_oi) > 200:
             # Binning logic
             df_oi = df_oi.copy()
             df_oi['price_bin'] = df_oi['price'].round(-1) # Placeholder binning
             df_oi = df_oi.groupby('price_bin')['open_interest'].sum().reset_index()
             df_oi.rename(columns={'price_bin': 'price'}, inplace=True)
             
        # Find peaks in OI
        # We look for levels where OI is > 2 standard deviations above mean
        mean_oi = df_oi['open_interest'].mean()
        std_oi = df_oi['open_interest'].std()
        
        if std_oi == 0:
            return []
            
        threshold = mean_oi + (2 * std_oi)
        clusters = df_oi[df_oi['open_interest'] >= threshold]
        
        for _, cluster in clusters.iterrows():
            price = cluster['price']
            oi_val = cluster['open_interest']
            
            # Strength based on magnitude relative to max
            strength = min(1.0, oi_val / df_oi['open_interest'].max())
            
            # Direction: MAGNET if close to current, otherwise S/R
            dist_pct = abs(price - current_price) / current_price
            
            if dist_pct < 0.01: # Within 1%
                direction = ConfluenceType.MAGNET
            else:
                direction = ConfluenceType.SUPPORT if price < current_price else ConfluenceType.RESISTANCE
                
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.OPEN_INTEREST,
                strength=strength,
                direction=direction,
                metadata={"open_interest": oi_val}
            ))
            
        logger.debug(f"Detected {len(factors)} Open Interest clusters")
        return factors
