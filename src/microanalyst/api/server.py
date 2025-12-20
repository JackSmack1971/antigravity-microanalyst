from fastapi import FastAPI, HTTPException
from datetime import datetime
import pandas as pd
from pathlib import Path
import os

# === Imports for Metadata ===
try:
    from src.microanalyst.metadata.catalog_generator import CatalogGenerator
    from src.microanalyst.metadata.semantic_search import SemanticCatalogSearch
    from src.microanalyst.metadata.lineage_tracker import LineageTracker
except ImportError:
    pass

# === Imports for Intelligence ===
try:
    from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer
except ImportError:
    pass

app = FastAPI(title="BTC Microanalyst API", version="2.0.0")

# Define paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_CLEAN_DIR = BASE_DIR / "data_clean"
LOG_DIR = BASE_DIR / "logs"

def get_last_modified(path: Path) -> datetime:
    if not path.exists():
        return datetime.min
    return datetime.fromtimestamp(path.stat().st_mtime)

@app.get("/data/etf-flows")
async def get_etf_flows(
    start_date: str = None,
    end_date: str = None,
    ticker: str = None,
    format: str = "json"  # json, csv
):
    """Returns normalized ETF flow data with optional filters"""
    file_path = DATA_CLEAN_DIR / "etf_flows_normalized.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Data file not found")
        
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Apply filters
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
    if ticker:
        df = df[df['ticker'] == ticker.upper()]
    
    # Return format
    if format == "json":
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        return df.to_dict(orient='records')
    elif format == "csv":
        return df.to_csv(index=False)
    
    raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'csv'")

@app.get("/data/price-history")
async def get_price_history(
    start_date: str = None,
    end_date: str = None,
    interval: str = "daily"
):
    """Returns OHLC data"""
    file_path = DATA_CLEAN_DIR / "btc_price_normalized.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Data file not found")
        
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
        
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    return df.to_dict(orient='records')

@app.get("/pipeline/status")
async def pipeline_status():
    """Returns latest execution metrics for monitoring"""
    log_path = LOG_DIR / "retrieval_log.txt"
    last_run_time = get_last_modified(log_path)
    
    etf_file = DATA_CLEAN_DIR / "etf_flows_normalized.csv"
    price_file = DATA_CLEAN_DIR / "btc_price_normalized.csv"
    now = datetime.now()
    
    return {
        "status": "online" if last_run_time != datetime.min else "unknown",
        "last_run": last_run_time.isoformat(),
        "data_freshness_hours": {
            "etf_flows": (now - get_last_modified(etf_file)).total_seconds() / 3600,
            "btc_price": (now - get_last_modified(price_file)).total_seconds() / 3600
        }
    }

# === Metadata Endpoints ===

@app.get("/metadata/catalog")
async def get_full_catalog():
    """Returns complete data catalog with runtime statistics"""
    generator = CatalogGenerator()
    catalog = generator.generate_full_catalog()
    return catalog

@app.get("/metadata/catalog/{dataset_id}")
async def get_dataset_metadata(dataset_id: str):
    """Get detailed metadata for specific dataset"""
    generator = CatalogGenerator()
    catalog = generator.generate_full_catalog()
    
    if dataset_id not in catalog['datasets']:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return catalog['datasets'][dataset_id]

@app.get("/metadata/search")
async def search_catalog(query: str, top_k: int = 5):
    """Semantic search over data catalog"""
    searcher = SemanticCatalogSearch()
    results = searcher.search(query, top_k)
    return {
        "query": query,
        "results": results,
        "total_found": len(results)
    }

@app.get("/metadata/lineage/{dataset_id}")
async def get_lineage(dataset_id: str):
    """Get data lineage for dataset"""
    tracker = LineageTracker()
    lineage = tracker.get_upstream_lineage(dataset_id)
    return {"dataset_id": dataset_id, "lineage": lineage}


# === Intelligence Endpoints ===

@app.get("/intelligence/context")
async def get_market_context(
    lookback_days: int = 30,
    report_type: str = "comprehensive",
    format: str = "markdown",  # markdown, json, structured_json, plain_text
    agent_optimized: bool = True
):
    """
    Get context-aware market intelligence report.
    
    - **regime**: Bull, Bear, Sideways, Volatile
    - **signals**: Technical signals and setups
    - **risks**: Volatility and drawdown risks
    - **narrative**: Human-readable summary
    """
    try:
        synthesizer = ContextSynthesizer()
        context = synthesizer.synthesize_context(lookback_days=lookback_days)
        
        report = synthesizer.generate_report(
            context,
            report_type=report_type,
            output_format=format,
            agent_optimized=agent_optimized
        )
        
        if format in ["json", "structured_json"]:
            import json
            return json.loads(report)
        else:
            return {"report": report, "metadata": context.metadata}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence generation failed: {str(e)}")


# === Confluence Integration ===
from src.microanalyst.intelligence.confluence_calculator import ConfluenceCalculator, ConfluenceVisualizer
from src.microanalyst.data_loader import load_price_history, load_etf_flows, load_etf_flows_enhanced

confluence_calc = ConfluenceCalculator()

@app.get("/intelligence/confluence-zones")
async def get_confluence_zones(
    min_score: float = 0.6,
    max_distance_pct: float = 10.0,
    include_factors: bool = True
):
    """
    Get current confluence zones with filtering options.
    """
    # Load data
    df_price = load_price_history()
    # Prefer enhanced flows
    df_flows = load_etf_flows_enhanced()
    if df_flows.empty:
        df_flows = load_etf_flows()
    
    if df_price.empty:
        raise HTTPException(status_code=404, detail="No price data available")
    
    # Calculate zones
    zones = confluence_calc.calculate_confluence_zones(df_price, df_flows)
    
    # Filter
    current_price = df_price['close'].iloc[-1]
    filtered = [
        z for z in zones
        if z.confluence_score >= min_score and
        abs(z.distance_to_current) <= max_distance_pct
    ]
    
    # Format response
    response = {
        "current_price": float(current_price),
        "timestamp": datetime.now().isoformat(),
        "total_zones": len(filtered),
        "zones": [z.to_dict() for z in filtered]
    }
    
    if not include_factors:
        for zone in response['zones']:
            zone['factors'] = [f['type'] for f in zone['factors']]
    
    return response

@app.get("/intelligence/confluence-zones/near-price")
async def get_nearest_zones(
    count: int = 5,
    direction: str = "both"
):
    """
    Get N nearest confluence zones to current price.
    """
    df_price = load_price_history()
    df_flows = load_etf_flows_enhanced()
    if df_flows.empty: df_flows = load_etf_flows()
    
    if df_price.empty:
        raise HTTPException(status_code=404, detail="No price data available")

    zones = confluence_calc.calculate_confluence_zones(df_price, df_flows)
    current_price = df_price['close'].iloc[-1]
    
    if direction == "above":
        filtered = [z for z in zones if z.price_level > current_price]
    elif direction == "below":
        filtered = [z for z in zones if z.price_level < current_price]
    else:
        filtered = zones
    
    # Sort by distance
    filtered.sort(key=lambda x: abs(x.distance_to_current))
    
    return {
        "current_price": float(current_price),
        "direction": direction,
        "nearest_zones": [z.to_dict() for z in filtered[:count]]
    }

@app.post("/intelligence/confluence-zones/visualize")
async def generate_confluence_visualization():
    """Generate and return confluence zone visualization HTML."""
    df_price = load_price_history()
    df_flows = load_etf_flows_enhanced()
    
    if df_price.empty:
        raise HTTPException(status_code=404, detail="No price data available")

    zones = confluence_calc.calculate_confluence_zones(df_price, df_flows)
    
    visualizer = ConfluenceVisualizer()
    fig = visualizer.plot_zones(df_price, zones)
    
    return {"status": "generated", "html": fig.to_html()}


# === Workflow Engine Integration ===
from src.microanalyst.agents.workflow_engine import WorkflowEngine, ResearchWorkflows

workflow_engine = WorkflowEngine()
research_workflows = ResearchWorkflows(workflow_engine)

@app.post("/workflows/execute")
async def execute_workflow(
    workflow_id: str,
    parameters: Dict[str, Any] = None
):
    """Execute a workflow."""
    try:
        result = await workflow_engine.execute(workflow_id, parameters or {})
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/list")
async def list_workflows():
    """List all registered workflows."""
    return {
        "workflows": [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "version": wf.version,
                "tasks": len(wf.tasks)
            }
            for wf in workflow_engine.workflows.values()
        ]
    }

@app.get("/workflows/{execution_id}/status")
async def get_workflow_status(execution_id: str):
    """Get execution status."""
    status = workflow_engine.get_execution_status(execution_id)
    if not status:
        raise HTTPException(status_code=404, detail="Execution not found")
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
