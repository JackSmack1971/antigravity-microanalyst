from src.microanalyst.intelligence.whale_intent import WhaleIntentEngine
import logging

# Configure logger to see internal errors if any
logging.basicConfig(level=logging.INFO)

def test_whale_intent():
    print("Testing WhaleIntentEngine...")
    
    engine = WhaleIntentEngine()
    
    # Mock Market Data indicating a potential "Short Squeeze" setup
    # High OI, Positive Funding, Liquidation Clusters above current price
    context = {
        "price": 95000,
        "trend": "Bullish Consolidation",
        "open_interest": "$25B (High)",
        "funding_rate": 0.015,
        "liquidation_clusters": [
            {"price": 96200, "side": "Short", "intensity": "High"},
            {"price": 93500, "side": "Long", "intensity": "Medium"}
        ]
    }
    
    print("\n--- Input Context ---")
    print(context)
    
    print("\n--- Agent Analysis ---")
    try:
        result = engine.analyze_market_structure(context)
        print(result)
        
        if result.get("intent") and result.get("target_price"):
            print("\nSUCCESS: Received structured Intent analysis.")
        else:
            print("\nFAILURE: Missing key fields in response.")
            
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")

if __name__ == "__main__":
    test_whale_intent()
