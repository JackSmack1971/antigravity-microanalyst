import asyncio
import sys
import json
from pathlib import Path

# Add project root to path for imports to work
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.microanalyst.core.async_retrieval import AsyncRetrievalEngine
from src.microanalyst.normalization import DataNormalizer
from src.microanalyst.agents.debate_swarm import run_adversarial_debate

def main():
    print("Starting BTC Microanalyst [Async Mode]")
    engine = AsyncRetrievalEngine()
    normalizer = DataNormalizer()
    
    # Run the async pipeline
    try:
        print("\n--- Phase 1: Retrieval ---")
        stats = asyncio.run(engine.execute_pipeline())
        
        if stats.get("success", 0) < 5: # Lowered threshold for dev
            print("WARNING: Low success rate.")

        print("\n--- Phase 2: Normalization & Persistence ---")
        # Normalize BTC Price (Intraday & Daily)
        # Note: In a real loop we might process specific files based on stats
        try:
             # Normalize latest files
             normalizer.normalize_price_history()
             # normalizer.normalize_etf_flows() # If available
             print("Normalization complete.")
        except Exception as e:
            print(f"Normalization warning: {e}")

        print("\n--- Phase 3: Swarm Intelligence ---")
        # Construct current context for the debate
        # Ideally this comes from the DB or the latest fetched file
        # For V4 demo, we'll try to fetch latest price from normalized DB or fallback
        
        # Mocking context for now to ensure pipeline completes if DB is empty from just this run
        context = {
            "ground_truth": {"regime": "Bullish Volatility"},
            "market_data": {
                "price": 95000, 
                "open_interest": "High",
                "funding_rate": 0.01,
                "volatility_score": 65 # High vol
            }
        }
        
        thesis = run_adversarial_debate(context)
        print(f"Thesis Generated: {thesis.get('decision')} ({thesis.get('confidence')}%)")
        
        # Save for API
        export_path = project_root / "data_exports" / "latest_thesis.json"
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(thesis, f, indent=2)
        print(f"Thesis saved to {export_path}")
            
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
