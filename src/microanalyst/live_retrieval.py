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
             # Use the full pipeline to load from captured artifacts and upsert to DB
             normalizer.run_pipeline()
             print("Normalization complete.")
        except Exception as e:
            print(f"Normalization warning: {e}")

        print("\n--- Phase 3: Swarm Intelligence ---")
        
        # Hydrate Context with Real Data
        try:
            from src.microanalyst.core.persistence import DatabaseManager
            from src.microanalyst.intelligence.synthetic_iv import SyntheticVolatilityEngine
            from src.microanalyst.intelligence.chain_watcher import ChainWatcher
            
            db = DatabaseManager()
            vol_engine = SyntheticVolatilityEngine()
            chain_watcher = ChainWatcher()
            
            # Fetch Price History (1D for Volatility)
            price_df = db.get_price_history(limit=365, interval="1d")
            vol_metrics = vol_engine.calculate_metrics(price_df)
            print(f"Volatility Metrics: {vol_metrics}")
            
            # Fetch On-Chain Data
            chain_stats = chain_watcher.fetch_mempool_stats()
            print(f"On-Chain Stats: {chain_stats}")
            
            # Fetch Latest Price (Intraday)
            latest_price = 0
            if not price_df.empty:
                latest_price = price_df.iloc[-1]['close'] # Fallback to daily close
                
            # Better: Get Intraday if available
            intra_df = db.get_price_history(limit=5, interval="15m")
            if not intra_df.empty:
                 latest_price = intra_df.iloc[-1]['close']

            context = {
                "ground_truth": {
                    "regime": "Volatile" if (vol_metrics.get('synthetic_iv_garch') or 0) > 50 else "Stable",
                    "congestion": chain_stats.get("congestion_level")
                },
                "market_data": {
                    "price": latest_price or 95000, 
                    "volatility_score": vol_metrics.get('synthetic_iv_garch', 0),
                    "realized_vol": vol_metrics.get('realized_vol_30d', 0),
                    "open_interest": "Unknown", 
                    "funding_rate": 0.01,
                    "mempool_vbytes": chain_stats.get("mempool_vbytes", 0),
                    "network_fees": chain_stats.get("fastest_fee_sats", 0)
                }
            }
        except Exception as e:
            print(f"Context Hydration Failed: {e}. Using Mock.")
            context = {
                "ground_truth": {"regime": "Bullish Volatility"},
                "market_data": {
                    "price": 95000, 
                    "open_interest": "High",
                    "funding_rate": 0.01,
                    "volatility_score": 65
                }
            }
        
        thesis = run_adversarial_debate(context)
        print(f"Thesis Generated: {thesis.get('decision')} ({thesis.get('confidence')}%)")
        
        # Save for API
        export_path = project_root / "data_exports" / "latest_thesis.json"
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(thesis, f, indent=2)
        print(f"Thesis saved to {export_path}")

        print("\n--- Phase 4: Simulated Execution ---")
        try:
            from src.microanalyst.simulation.paper_exchange import PaperExchange
            from src.microanalyst.simulation.execution_router import ExecutionRouter
            from src.microanalyst.simulation.portfolio_manager import PortfolioManager
            from src.microanalyst.core.persistence import DatabaseManager

            # Initialize Engine
            exchange = PaperExchange()
            router = ExecutionRouter(exchange)
            pm = PortfolioManager(exchange)
            db = DatabaseManager()

            # Execute
            current_price = context["market_data"]["price"]
            user_id = "agent_v5_demo"
            
            # 1. Execute Signal
            order = router.execute_signal(user_id, thesis, current_price)
            
            # 2. Process Fills (Instant fill for simulation at current price)
            exchange.process_fills(current_price)
            
            # 3. Log Performance
            pm.log_state_to_db(db, user_id, current_price)
            if order:
                print(f"Order Executed: {order.side} {order.quantity} BTC")
                # Using Pydantic V2 model_dump() for standardized logging
                order_data = order.model_dump()
                
                trade_record = {
                    "order_id": order_data["order_id"],
                    "user_id": order_data["user_id"],
                    "symbol": order_data["symbol"],
                    "side": order_data["side"],
                    "quantity": order_data["quantity"],
                    "price": order_data["price"] or current_price,
                    "filled_price": order_data["filled_price"],
                    "status": order_data["status"]
                }
                db.log_paper_trade(trade_record)
            else:
               print("No trade executed (HOLD or insufficient confidence).")

        except Exception as e:
             print(f"Execution Phase Error: {e}")
             import traceback
             traceback.print_exc()
            
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
