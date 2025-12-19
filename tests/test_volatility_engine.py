import asyncio
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.getcwd())

from src.microanalyst.synthetic.volatility import VolatilityEngine

def test_volatility_engine():
    print("Testing Synthetic Volatility Engine...")
    
    engine = VolatilityEngine()
    
    # 1. Create Sample OHLCV Data (Neutral Market)
    print("\n[Scenario 1: Neutral Market Data]")
    dates = pd.date_range(end=pd.Timestamp.now(), periods=60, freq='D')
    close = np.linspace(100, 110, 60) # Slow drift up
    # Add small random noise
    noise = np.random.normal(0, 1, 60) 
    close = close + noise
    
    df = pd.DataFrame({
        'close': close,
        'high': close + 2,
        'low': close - 2,
        'volume': 1000
    }, index=dates)
    
    metrics = engine.calculate_synthetic_iv(df)
    
    if 'error' in metrics:
        print(f"❌ Error: {metrics['error']}")
    else:
        print(f"✅ Synthetic IV: {metrics['value']}")
        print(f"   HV (30d): {metrics['components']['historical_vol_30d']}")
        print(f"   Sentiment Multiplier: {metrics['components']['regime_multiplier']}")
        print(f"   Interpretation: {metrics['interpretation']}")

    # 2. Test Fear & Greed Integration
    print("\n[Scenario 2: Fear & Greed API Check]")
    sentiment = engine._get_fear_greed_index()
    print(f"✅ Current Sentiment: {sentiment.get('value')} ({sentiment.get('value_classification')})")

    print("\nVolatility Engine verification complete!")

if __name__ == "__main__":
    test_volatility_engine()
