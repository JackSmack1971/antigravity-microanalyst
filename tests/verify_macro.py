import pandas as pd
from typing import Dict, Any
from src.microanalyst.providers.macro_data import MacroDataProvider
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer

def verify_macro_pipeline():
    print("🧪 Verifying Macro-Correlation Nexus")
    
    # 1. Test Provider
    print("\n[Step 1] Fetching Macro Data (Live via yfinance)...")
    provider = MacroDataProvider()
    try:
        # We need lookback=60 to get enough data for 30d correlation valid overlap
        macro_data = provider.fetch_macro_series(lookback_days=60)
    except Exception as e:
        print(f"FAILED to fetch data. Ensure yfinance is installed (pip install yfinance). Error: {e}")
        return

    for name, series in macro_data.items():
        if series.empty:
            print(f"⚠️ Warning: No data for {name}")
        else:
            print(f"✅ {name}: {len(series)} points (Last: {series.iloc[-1]:.2f})")
    
    # 2. Test Analyzer
    print("\n[Step 2] Testing Correlation Logic...")
    
    # Construct synthetic BTC data correlated to DXY
    if 'dxy' in macro_data and not macro_data['dxy'].empty:
        dxy = macro_data['dxy']
        
        # Perfect Inverse Correlation Scenario
        btc_inverse = dxy * -1000 + 100000 
        
        analyzer = CorrelationAnalyzer()
        results = analyzer.analyze_correlations(btc_inverse, macro_data)
        
        print("Analysis Results:")
        for res in results:
            print(f" - {res['metric']}: {res.get('value', 'N/A'):.2f} | Status: {res.get('status')}")
            
            if "DXY" in res['metric']:
                # We expect roughly -1.0
                val = res.get('value', 0)
                if val <= -0.9:
                    print("   ✅ Validated Inverse Correlation Logic")
                else:
                    print(f"   ❌ Correlation unexpected: {val}")
    else:
        print("Skipping correlation test: DXY data missing.")

if __name__ == "__main__":
    verify_macro_pipeline()
