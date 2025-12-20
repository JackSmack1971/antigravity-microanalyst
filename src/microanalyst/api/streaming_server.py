from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Any
import asyncio
import json
from datetime import datetime
from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer
from src.microanalyst.intelligence.base import MarketContext
from src.microanalyst.agents.workflow_engine import WorkflowEngine, ResearchWorkflows

app = FastAPI(title="BTC Microanalyst Streaming API")

# Shared synthesizer instance
synthesizer = ContextSynthesizer()

async def get_latest_context() -> Dict[str, Any]:
    """Helper to fetch and format latest context for streaming"""
    try:
        context = synthesizer.synthesize_context(lookback_days=30)
        # Use the JSON report generation logic for consistency
        report_json = synthesizer.generate_report(context, output_format="json", agent_optimized=True)
        return json.loads(report_json)
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/stream/market_updates")
async def stream_market_updates() -> StreamingResponse:
    """
    Stream market updates as they become available
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        print("Client connected to market updates stream")
        try:
            while True:
                # Check for new data
                latest_context = await get_latest_context()
                
                # Format as SSE
                yield f"data: {json.dumps(latest_context, default=str)}\n\n"
                
                await asyncio.sleep(60)  # Update every minute
        except asyncio.CancelledError:
            print("Client disconnected from market updates stream")
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/stream/workflow_execution/{workflow_id}")
async def stream_workflow_execution(workflow_id: str, background_tasks: BackgroundTasks):
    """
    Stream workflow execution progress in real-time
    """
    async def execution_stream() -> AsyncGenerator[str, None]:
        engine = WorkflowEngine()
        execution_id = None
        
        # Start workflow in background 
        # Note: In a real production app, we'd use a more robust task queue
        # For this implementation, we simulate tracking via the engine state
        
        # We need to capture the execution_id before the stream starts
        # or have the engine provide it.
        # Let's assume engine.execute returns the execution_id immediately
        
        # Initialize workflows for the engine
        ResearchWorkflows(engine)
        
        try:
            # Start workflow in background and get ID immediately
            execution_id = await engine.start_execution(workflow_id, {})
            print(f"Streaming execution: {execution_id}")
            
            # Stream progress
            while True:
                status = engine.get_execution_status(execution_id)
                if status:
                    yield f"data: {json.dumps(status, default=str)}\n\n"
                    
                    if status.get('status') in ['completed', 'failed']:
                        break
                
                await asyncio.sleep(1)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except asyncio.CancelledError:
            print(f"Client disconnected from workflow stream: {execution_id}")
            raise
    
    return StreamingResponse(
        execution_stream(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
