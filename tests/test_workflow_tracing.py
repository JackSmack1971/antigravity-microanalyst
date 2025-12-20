import asyncio
import json
from pathlib import Path
from src.microanalyst.agents.workflow_engine import WorkflowEngine, ResearchWorkflows
import os

# Set PYTHONPATH
os.environ["PYTHONPATH"] = os.getcwd()

async def test_workflow_tracing():
    print("Testing Workflow Engine Tracing...")
    
    # Initialize engine
    engine = WorkflowEngine()
    workflows = ResearchWorkflows(engine)
    
    # Execute a simple workflow
    workflow_id = "sentiment_analysis"
    params = {"lookback_days": 7}
    
    print(f"\n[Scenario: Tracing Workflow {workflow_id}]")
    result = await engine.execute(workflow_id, params)
    
    execution_id = result['execution_id']
    print(f"Execution ID: {execution_id}")
    
    # Verify trace file exists
    trace_files = list(Path("traces").glob(f"{execution_id}_*.json"))
    print(f"Workflow trace file generated: {len(trace_files) > 0}")
    assert len(trace_files) > 0
    
    # Verify trace content
    with open(trace_files[0]) as f:
        data = json.load(f)
        assert data['trace_id'] == execution_id
        assert data['status'] == "completed"
        # 1 start event + potential future step events
        assert len(data['events']) >= 1
        print(f"Events captured in workflow trace: {len(data['events'])}")
        
    print("\nWorkflow Tracing verification passed!")

if __name__ == "__main__":
    # Clean previous traces
    traces_dir = Path("traces")
    if traces_dir.exists():
        for f in traces_dir.glob("*.json"): f.unlink()
        
    asyncio.run(test_workflow_tracing())
