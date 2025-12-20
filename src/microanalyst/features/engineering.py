# src/microanalyst/features/engineering.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try importing pandas_ta, fallback to manual impl if needed
try:
    import pandas_ta as ta
    TA_LIB_AVAILABLE = True
except ImportError:
    TA_LIB_AVAILABLE = False
    logger.warning("pandas_ta not found. Using internal fallback implementations for indicators.")

class FeatureEngineer:
    """
    Transform raw data -> ML-ready features.
    Standardizes feature generation for Technicals, Flows, and Derivatives.
    """
    
    def __init__(self):
        pass

    def generate_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate standard technical indicators.
        Expects: 'open', 'high', 'low', 'close', 'volume' columns.
        Returns: DataFrame with added feature columns.
        """
        if df.empty:
            return df
            
        # Ensure we work on a copy to avoid SettingWithCopy warnings on input
        df = df.copy()
        
        # Lowercase columns for consistency if needed, but assuming standard names
        # Ensure numeric types
        cols = ['open', 'high', 'low', 'close', 'volume']
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        
        try:
            if TA_LIB_AVAILABLE:
                # Use pandas_ta
                # SMA
                df['sma_20'] = ta.sma(df['close'], length=20)
                df['sma_50'] = ta.sma(df['close'], length=50)
                df['sma_200'] = ta.sma(df['close'], length=200)
                
                # RSI
                df['rsi_14'] = ta.rsi(df['close'], length=14)
                
                # MACD
                macd = ta.macd(df['close'])
                if macd is not None:
                     # pandas_ta returns MACD_12_26_9, MACDh, MACDs
                     df['macd'] = macd['MACD_12_26_9']
                     df['macd_signal'] = macd['MACDs_12_26_9']
                     df['macd_hist'] = macd['MACDh_12_26_9']

                # Bollinger Bands
                bb = ta.bbands(df['close'], length=20, std=2)
                if bb is not None:
                    # Dynamically find columns as names can vary (e.g. BBU_20_2.0)
                    bbu_col = [c for c in bb.columns if c.startswith('BBU')][0]
                    bbl_col = [c for c in bb.columns if c.startswith('BBL')][0]
                    df['bb_upper'] = bb[bbu_col]
                    df['bb_lower'] = bb[bbl_col]
                    
                # ATR
                df['atr_14'] = ta.atr(df['high'], df['low'], df['close'], length=14)
                
            else:
                self._manual_technicals(df)
                
            # Volume Momentum (Simple ROC)
            df['vol_mom_5'] = df['volume'].pct_change(5)
            
            # Price ROC
            df['roc_1'] = df['close'].pct_change(1)
            
        except Exception as e:
            logger.error(f"Error generating technical features: {e}")
            
        return df

    def _manual_technicals(self, df):
        """Fallback implementations using pure pandas/numpy"""
        close = df['close']
        
        # SMA
        df['sma_20'] = close.rolling(window=20).mean()
        df['sma_50'] = close.rolling(window=50).mean()
        df['sma_200'] = close.rolling(window=200).mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD (12, 26, 9)
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands (20, 2)
        sma20 = df['sma_20']
        std20 = close.rolling(window=20).std()
        df['bb_upper'] = sma20 + (std20 * 2)
        df['bb_lower'] = sma20 - (std20 * 2)
        
        # ATR (14) - Simple approx
        # TR = Max(H-L, |H-Cp|, |L-Cp|)
        high = df['high']
        low = df['low']
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(window=14).mean()

    def generate_flow_features(self, df_flows: pd.DataFrame) -> pd.DataFrame:
        """
        Features for ETF/Exchange flows.
        Expects: 'net_flow' column.
        """
        if df_flows.empty or 'net_flow' not in df_flows.columns:
            return df_flows
            
        df = df_flows.copy()
        
        # Cumulative Flows
        df['flow_cum_7d'] = df['net_flow'].rolling(7).sum()
        df['flow_cum_30d'] = df['net_flow'].rolling(30).sum()
        
        # Momentum
        df['flow_mom_5d'] = df['net_flow'].pct_change(5)
        
        # Z-Score (Outlier detection)
        mean_30 = df['net_flow'].rolling(30).mean()
        std_30 = df['net_flow'].rolling(30).std()
        df['flow_zscore'] = (df['net_flow'] - mean_30) / std_30
        
        return df

    def generate_derivatives_features(self, df_derivs: pd.DataFrame) -> pd.DataFrame:
        """
        Features for OI and Funding.
        Expects: 'open_interest', 'funding_rate'
        """
        if df_derivs.empty:
            return df_derivs
            
        df = df_derivs.copy()
        
        if 'open_interest' in df.columns:
            df['oi_chg_24h'] = df['open_interest'].pct_change(1) # Assuming daily rows for daily features
            df['oi_chg_7d'] = df['open_interest'].pct_change(7)
            
        if 'funding_rate' in df.columns:
            # Detect extremes
            # 0.01% per 8h is baseline. >0.03 is high. <0 is short bias.
            # Convert to annualized approx for better reading? Or just Z-score.
            # Rolling mean/std for anomaly
            window = 30
            f_mean = df['funding_rate'].rolling(window).mean()
            f_std = df['funding_rate'].rolling(window).std()
            df['funding_zscore'] = (df['funding_rate'] - f_mean) / f_std
            
        return df
