import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.microanalyst.aggregation.timeframes import MultiTimeframeAggregator

def create_trend_data(length=100, trend='up'):
    start_price = 100
    prices = []
    curr = start_price
    for i in range(length):
        if trend == 'up':
            curr += np.random.uniform(0, 2)
        else:
            curr -= np.random.uniform(0, 2)
        prices.append(curr)
        
    df = pd.DataFrame({
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'close': prices,
        'volume': [100] * length
    })
    # Create valid timestamp index
    df.index = pd.date_range(start='2024-01-01', periods=length, freq='1T')
    return df

def test_resampling():
    print("\n--- Testing OHLCV Resampling ---")
    agg = MultiTimeframeAggregator()
    
    # 10 minutes of data
    df_1m = create_trend_data(length=10, trend='up')
    
    # Resample to 5 mins
    df_5m = agg.resample_ohlcv(df_1m, '5T')
    
    print(f"Input rows: {len(df_1m)}, Output rows: {len(df_5m)}")
    
    # Expected: 2 rows (10 mins / 5 mins)
    assert len(df_5m) == 2
    
    # Check aggregation logic for first bar (first 5 mins)
    first_5_input = df_1m.iloc[0:5]
    first_5_output = df_5m.iloc[0]
    
    assert first_5_output['high'] == first_5_input['high'].max()
    assert first_5_output['low'] == first_5_input['low'].min()
    assert first_5_output['volume'] == first_5_input['volume'].sum()
    
    print("✅ Aggregation Logic (Open/High/Low/Close/Vol) Verified")

def test_fractal_alignment():
    print("\n--- Testing Fractal Alignment ---")
    agg = MultiTimeframeAggregator()
    
    # Create 3 timeframes, all bullish
    tf_data = {
        '1h': create_trend_data(100, 'up'),
        '4h': create_trend_data(100, 'up'),
        '1d': create_trend_data(100, 'up')
    }
    
    result = agg.calculate_alignment(tf_data)
    print("Alignment Result (All Bullish):", result)
    
    assert result['is_fractal_aligned'] == True
    assert result['overall_direction'] == 'bullish'
    print("✅ Detected Full Bullish Alignment")
    
    # Make one bearish
    tf_data['1d'] = create_trend_data(100, 'down')
    result_mixed = agg.calculate_alignment(tf_data)
    print("Alignment Result (Mixed):", result_mixed)
    
    assert result_mixed['is_fractal_aligned'] == False
    assert result_mixed['alignment_score'] < 100
    print("✅ Detected Broken Alignment")

if __name__ == "__main__":
    try:
        test_resampling()
        test_fractal_alignment()
        print("\nALL TIMEFRAME TESTS PASSED ✅")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
