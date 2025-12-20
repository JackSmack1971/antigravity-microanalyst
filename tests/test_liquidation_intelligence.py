import pytest
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.microanalyst.synthetic.liquidation_intelligence import LiquidationClusterAnalyzer

def test_simulation_fallback():
    print("\n--- Testing Simulation Fallback ---")
    analyzer = LiquidationClusterAnalyzer()
    
    current_price = 50500
    magnets = analyzer.detect_magnets([], current_price)
    
    print("Generated Magnets:", magnets)
    
    # Expect round numbers around 50500 -> 51000, 50000
    prices = [m['price'] for m in magnets]
    assert 51000 in prices
    assert 50000 in prices
    print("✅ Fallback successfully generated psychological levels")

def test_cascade_risk_logic():
    print("\n--- Testing Cascade Risk Calculation ---")
    analyzer = LiquidationClusterAnalyzer()
    
    # Scenario 1: Close to magnet
    # Magnet at 50000, Price at 50100 (0.2% away)
    magnets = [{"price": 50000, "intensity": 90}]
    risk_high = analyzer.calculate_cascade_risk(magnets, 50100, volatility=0.02) # Vol 2%
    
    print(f"Close Risk: {risk_high}")
    assert risk_high['risk_level'] == 'HIGH' or risk_high['probability'] >= 0.6
    
    # Scenario 2: Far from magnet
    # Price at 55000 (10% away)
    risk_low = analyzer.calculate_cascade_risk(magnets, 55000, volatility=0.02)
    
    print(f"Far Risk: {risk_low}")
    assert risk_low['risk_level'] == 'LOW'
    print("✅ Risk calculation logic verified")

if __name__ == "__main__":
    try:
        test_simulation_fallback()
        test_cascade_risk_logic()
        print("\nALL LIQUIDATION TESTS PASSED ✅")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
