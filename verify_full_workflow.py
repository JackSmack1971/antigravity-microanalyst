import asyncio
import json
import logging
import pandas as pd
from datetime import datetime
from src.microanalyst.agents.agent_coordinator import AgentCoordinator
from src.microanalyst.core.persistence import DatabaseManager
from src.microanalyst.intelligence.vision import VisionParser
from src.microanalyst.intelligence.synthetic_iv import SyntheticVolatilityEngine
from src.microanalyst.intelligence.chain_watcher import ChainWatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def assess_workflow():
    logger.info("Starting End-to-End Workflow Assessment...")
    
    coordinator = AgentCoordinator()
    db = DatabaseManager()
    vol_engine = SyntheticVolatilityEngine()
    chain_watcher = ChainWatcher()
    
    # 1. Gather Context
    logger.info("Gathering multi-source context...")
    
    # Price
    df_1h = db.get_price_history(limit=200, interval="1h")
    df_1d = db.get_price_history(limit=365, interval="1d")
    
    # Volatility
    vol_metrics = vol_engine.calculate_metrics(df_1d)
    
    # On-Chain
    chain_stats = chain_watcher.fetch_mempool_stats()
    
    # Vision (Mocking for dev environment, but using real parser structure)
    # In live, we'd pass a path to the latest screenshot
    vision_data = {"liq_distance": 0.05} # 5% distance to magnetic zone
    
    # 2. Build Parameters
    parameters = {
        "lookback_days": 30,
        "sources": ["price", "sentiment", "risk", "synthetic", "derivatives"],
        "df_price": df_1h.to_dict() if not df_1h.empty else {},
        "context_metadata": {
            "volatility": vol_metrics,
            "onchain": chain_stats,
            "vision": vision_data
        }
    }
    
    # 3. Execute Workflow
    logger.info("Executing AgentCoordinator Comprehensive Analysis...")
    result = await coordinator.execute_multi_agent_workflow(
        "comprehensive_analysis",
        parameters
    )
    
    # 4. Assess Data Quality
    logger.info("Assessing Data Quality...")
    final_output = result.get('final_result', {})
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "workflow_summary": {
            "execution_time": result.get('execution_time'),
            "tasks_executed": result.get('tasks_executed')
        },
        "data_quality": {
            "price_history_populated": not df_1h.empty,
            "volatility_available": 'synthetic_iv_garch' in vol_metrics,
            "onchain_available": 'congestion_level' in chain_stats
        },
        "prediction_agent_status": {
            "decision": final_output.get('decision'),
            "confidence": final_output.get('confidence'),
            "reasoning": final_output.get('reasoning')
        }
    }
    
    print("\n--- FINAL WORKFLOW QUALITY REPORT ---")
    print(json.dumps(report, indent=2))
    
    with open("DATA_QUALITY_REPORT.json", "w") as f:
        json.dump(report, f, indent=2)

    # Export for Dashboard
    export_path = "data_exports/latest_thesis.json"
    with open(export_path, "w") as f:
        # Merge coordinator output into the final export
        export_data = result.get('final_result', {})
        export_data['simulation_mode'] = result.get('simulation_mode', False)
        export_data['component_metadata'] = result.get('component_metadata', {})
        export_data['logs'] = result.get('logs', [])
        export_data['execution_time'] = result.get('execution_time', 0.0)
        json.dump(export_data, f, indent=2, default=str)
    logger.info(f"Full intelligence thesis exported to {export_path}")

if __name__ == "__main__":
    asyncio.run(assess_workflow())
