import pandas as pd
import pandas_ta as ta
import numpy as np

def debug_ta():
    df = pd.DataFrame({
        'close': np.random.random(100),
        'high': np.random.random(100),
        'low': np.random.random(100),
        'volume': np.random.random(100)
    })
    
    print("--- Bollinger Bands ---")
    try:
        bb = ta.bbands(df['close'], length=20, std=2)
        print(bb.columns.tolist())
    except Exception as e:
        print(f"BB Error: {e}")

    print("\n--- ATR ---")
    try:
        atr = ta.atr(df['high'], df['low'], df['close'], length=14)
        print(atr.name if hasattr(atr, 'name') else "No Name")
    except Exception as e:
        print(f"ATR Error: {e}")

if __name__ == "__main__":
    debug_ta()
