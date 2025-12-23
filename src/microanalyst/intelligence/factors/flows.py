import pandas as pd
import numpy as np
from typing import List
from .base import BaseFactorDetector
from ..schemas import ConfluenceFactor, FactorType, ConfluenceType
from loguru import logger

class ETFFlowDetector(BaseFactorDetector):
    """
    Detects significant pivot points in institutional ETF flows.
    
    Identifies 'smart money' movements by detecting statistical outliers 
    (spikes) in net ETF flows and mapping them to the price levels 
    where institutional orders were likely executed.
    """
    
    def detect(self, df_price: pd.DataFrame, **kwargs) -> List[ConfluenceFactor]:
        """
        Detects ETF flow pivots.
        
        Args:
            df_price: Price DataFrame with OHLC data.
            **kwargs: Must contain 'df_flows' (ETF flow DataFrame).
            
        Returns:
            List[ConfluenceFactor]: Detected ETF flow pivot factors.
        """
        df_flows = kwargs.get('df_flows')
        if df_flows is None or df_flows.empty:
            return []
            
        factors = []
        
        # Determine Flow Column Name (standardize)
        flow_col = self._get_flow_column(df_flows)
        if not flow_col:
            return []
            
        # Aggregate daily flows
        daily_flows = df_flows.copy()
        if 'date' not in daily_flows.columns:
            logger.warning("ETF flows missing 'date' column")
            return []
            
        daily_flows = daily_flows.groupby('date')[flow_col].sum().reset_index()
        daily_flows = daily_flows.sort_values('date')
        
        if len(daily_flows) < 2:
            return []
            
        # Statistical Spike Detection (Z-score)
        mean_flow = daily_flows[flow_col].mean()
        std_flow = daily_flows[flow_col].std()
        
        if std_flow == 0:
            return []
            
        daily_flows['z_score'] = (daily_flows[flow_col] - mean_flow) / std_flow
        threshold = 2.0 # 2 sigma spike
        
        spikes = daily_flows[np.abs(daily_flows['z_score']) > threshold]
        
        # Map spikes to price range
        for _, spike in spikes.iterrows():
            # Find matching date in price DF
            # Support both datetime objects and strings
            spike_date = spike['date']
            if isinstance(spike_date, str):
                spike_date = pd.to_datetime(spike_date)
                
            match = df_price[df_price['date'].dt.date == (spike_date.date() if hasattr(spike_date, 'date') else spike_date)]
            
            if not match.empty:
                # Use the day's average price as the pivot level
                price_level = (match['high'].mean() + match['low'].mean()) / 2
                
                # Strength based on Z-score magnitude (normalized)
                # Note: In small datasets (N=10), max Z-score is approx sqrt(N-1) = 3.
                strength = min(1.0, abs(spike['z_score']) / 3.0)
                
                # Direction based on net flow
                direction = ConfluenceType.SUPPORT if spike[flow_col] > 0 else ConfluenceType.RESISTANCE
                
                factors.append(ConfluenceFactor(
                    price=price_level,
                    factor_type=FactorType.ETF_FLOW_PIVOT,
                    strength=strength,
                    direction=direction,
                    metadata={
                        "flow_magnitude": spike[flow_col],
                        "z_score": spike['z_score'],
                        "date": spike['date']
                    }
                ))
                
        logger.debug(f"Detected {len(factors)} ETF flow pivot points")
        return factors
        
    def _get_flow_column(self, df: pd.DataFrame) -> str:
        """Find the appropriate flow column name."""
        candidates = ['flow_usd', 'Net_Flow', 'net_flow', 'flow']
        cols = {c.lower(): c for c in df.columns}
        for cand in candidates:
            if cand.lower() in cols:
                return cols[cand.lower()]
        return ""
