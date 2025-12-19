import pandas as pd
import numpy as np
import pytest
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.microanalyst.features.engineering import FeatureEngineer

def create_synthetic_ohlc(length=100):
    prices = np.linspace(50000, 60000, length)
    # Add some noise
    prices = prices + np.random.normal(0, 500, length)
    
    df = pd.DataFrame({
        'close': prices,
        'open': prices + np.random.normal(0, 100, length),
        'high': prices + np.random.normal(0, 200, length) + 100,
        'low': prices + np.random.normal(0, 200, length) - 100,
        'volume': np.random.randint(100, 1000, length)
    })
    return df

def test_technical_features():
    df = create_synthetic_ohlc(200)
    fe = FeatureEngineer()
    
    df_feat = fe.generate_technical_features(df)
    
    print("Columns:", df_feat.columns)
    
    # Assert columns exist
    assert 'sma_20' in df_feat.columns
    assert 'sma_50' in df_feat.columns
    assert 'rsi_14' in df_feat.columns
    assert 'macd' in df_feat.columns
    assert 'atr_14' in df_feat.columns
    assert 'vol_mom_5' in df_feat.columns
    
    # Check values exist (not all NaN)
    # Note: First few rows will be NaN due to rolling windows
    assert not df_feat['sma_20'].iloc[-1:].isna().all()
    assert not df_feat['rsi_14'].iloc[-1:].isna().all()

def test_flow_features():
    df = pd.DataFrame({
        'net_flow': np.random.normal(0, 1000, 50)
    })
    fe = FeatureEngineer()
    df_feat = fe.generate_flow_features(df)
    
    assert 'flow_cum_7d' in df_feat.columns
    assert 'flow_mom_5d' in df_feat.columns
    assert 'flow_zscore' in df_feat.columns

def test_derivatives_features():
    df = pd.DataFrame({
        'open_interest': np.linspace(10000, 20000, 50),
        'funding_rate': np.random.normal(0.0001, 0.0001, 50)
    })
    fe = FeatureEngineer()
    df_feat = fe.generate_derivatives_features(df)
    
    assert 'oi_chg_24h' in df_feat.columns
    assert 'funding_zscore' in df_feat.columns

if __name__ == "__main__":
    # Quick manual run
    try:
        test_technical_features()
        print("Technicals Pass ✅")
        test_flow_features()
        print("Flows Pass ✅")
        test_derivatives_features()
        print("Derivatives Pass ✅")
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
