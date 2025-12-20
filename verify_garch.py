import pandas as pd
import numpy as np
from src.microanalyst.intelligence.synthetic_iv import SyntheticVolatilityEngine

def verify_garch_logic():
    print("--- Starting Synthetic Volatility verification ---")
    
    # Generate Sample Data (Geometric Brownian Motion)
    np.random.seed(42)
    days = 100
    dates = pd.date_range(start="2025-01-01", periods=days, freq="D")
    
    # Drift 0, Vol 2% daily
    returns = np.random.normal(loc=0, scale=0.02, size=days)
    price_start = 50000
    prices = price_start * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({"date": dates, "close": prices})
    
    engine = SyntheticVolatilityEngine()
    metrics = engine.calculate_metrics(df)
    
    print("\n[Metrics Output]")
    print(metrics)
    
    # Assertions
    # 2% daily vol * sqrt(365) ~= 38% annualized
    # GARCH should be somewhat close to this or at least non-zero and valid
    rv = metrics.get('realized_vol_30d')
    garch = metrics.get('synthetic_iv_garch')
    
    assert rv is not None
    assert garch is not None
    
    print(f"Realized Vol (Annualized): {rv:.2f}%")
    print(f"GARCH Forecast (Annualized): {garch:.2f}%")
    
    assert 20 < garch < 80, f"GARCH {garch}% seems out of bounds for 2% daily noise"
    
    print("\n✅ Verification Successful: GARCH model converged and produced valid metrics.")

if __name__ == "__main__":
    verify_garch_logic()
