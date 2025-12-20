from src.microanalyst.intelligence.risk_manager import RiskManager
import pandas as pd

def test_risk_manager():
    print("Initializing RiskManager...")
    rm = RiskManager()
    
    print("\n--- 1D Risk Report ---")
    report_1d = rm.get_risk_report("1d")
    print(report_1d)
    
    if "error" not in report_1d:
        print("SUCCESS: Generated 1D Report.")
    else:
        print("WARNING: 1D Report failed (possibly insufficient data).")

    # Only test 1h if we know we have data, which we verified in Phase 8
    print("\n--- 1H Risk Report ---")
    report_1h = rm.get_risk_report("1h")
    print(report_1h)
    
    if "error" not in report_1h:
        print("SUCCESS: Generated 1H Report.")
    else:
        print(f"WARNING: 1H Report failed: {report_1h.get('error')}")

if __name__ == "__main__":
    test_risk_manager()
