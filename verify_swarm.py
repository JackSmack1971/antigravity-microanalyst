from src.microanalyst.agents.debate_swarm import run_adversarial_debate

mock_data = {
    "ground_truth": {"regime": "bull_trend"},
    "funding_rate": "0.01%",
    "volatility_score": 65
}

print("--- Starting Swarm Verification ---")
try:
    result = run_adversarial_debate(mock_data)
    print("\n[DECISION]:", result["decision"])
    print("[ALLOCATION]:", result["allocation_pct"])
    print("[REASONING]:", result["reasoning"])
    print("\n--- Perspectives ---")
    print("BULL:", result["bull_case"])
    print("BEAR:", result["bear_case"])
    print("\n[LOGS]:", result["logs"])
    print("\n--- Verification Complete ---")
except Exception as e:
    print(f"\nCRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
